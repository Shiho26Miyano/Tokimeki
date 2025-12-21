"""
Simulation Service for Walk-Forward Paper Trading
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from app.models.simulation_models import (
    PricesDaily, SignalsDaily, Trades, PortfolioDaily, StrategyMetadata
)
from .strategy_service import StrategyPlugin


class SimulationService:
    """Service for running walk-forward trading simulations"""
    
    def __init__(self, db: Session, strategy: StrategyPlugin):
        self.db = db
        self.strategy = strategy
        self.initial_nav = 100000.0  # Starting capital
    
    def get_or_create_portfolio(self, target_date: date) -> PortfolioDaily:
        """Get existing portfolio or create initial portfolio"""
        portfolio = self.db.query(PortfolioDaily).filter(
            and_(
                PortfolioDaily.strategy_id == self.strategy.strategy_id,
                PortfolioDaily.date == target_date
            )
        ).first()
        
        if portfolio:
            return portfolio
        
        # Check for previous day's portfolio
        prev_portfolio = self.db.query(PortfolioDaily).filter(
            and_(
                PortfolioDaily.strategy_id == self.strategy.strategy_id,
                PortfolioDaily.date < target_date
            )
        ).order_by(PortfolioDaily.date.desc()).first()
        
        if prev_portfolio:
            # Carry forward from previous day
            nav = prev_portfolio.nav
            cash = prev_portfolio.cash
            positions = prev_portfolio.positions_json or {}
            cumulative_pnl = prev_portfolio.cumulative_pnl or 0.0
            max_drawdown = prev_portfolio.max_drawdown or 0.0
        else:
            # Initial portfolio
            nav = self.initial_nav
            cash = self.initial_nav
            positions = {}
            cumulative_pnl = 0.0
            max_drawdown = 0.0
        
        portfolio = PortfolioDaily(
            strategy_id=self.strategy.strategy_id,
            date=target_date,
            nav=nav,
            cash=cash,
            positions_json=positions,
            daily_pnl=0.0,
            cumulative_pnl=cumulative_pnl,
            drawdown=0.0,
            max_drawdown=max_drawdown,
            risk_state_json={}
        )
        
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        return portfolio
    
    def mark_to_market(
        self,
        portfolio: PortfolioDaily,
        target_date: date,
        symbols: List[str]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Mark positions to market
        
        Returns:
            (total_position_value, {symbol: value})
        """
        positions = portfolio.positions_json or {}
        position_values = {}
        total_value = 0.0
        
        for symbol in symbols:
            quantity = positions.get(symbol, 0.0)
            if quantity == 0.0:
                continue
            
            # Get current price
            price_data = self.db.query(PricesDaily).filter(
                and_(
                    PricesDaily.symbol == symbol,
                    PricesDaily.date == target_date
                )
            ).first()
            
            if price_data:
                price = price_data.close
                value = quantity * price
                position_values[symbol] = value
                total_value += value
        
        return total_value, position_values
    
    def execute_trade(
        self,
        symbol: str,
        target_date: date,
        signal: SignalsDaily,
        portfolio: PortfolioDaily
    ) -> Optional[Trades]:
        """
        Execute a trade based on signal
        
        Returns:
            Trades instance or None if no trade executed
        """
        if signal.signal == 'FLAT':
            return None
        
        # Get execution price
        price_data = self.db.query(PricesDaily).filter(
            and_(
                PricesDaily.symbol == symbol,
                PricesDaily.date == target_date
            )
        ).first()
        
        if not price_data:
            return None
        
        # Determine execution price based on timing
        execution_timing = self.strategy.params.get('execution_timing', 'MOC')
        
        if execution_timing == 'MOC':
            execution_price = price_data.close
        elif execution_timing == 'NEXT_OPEN':
            # Get next trading day's open
            next_date = target_date + timedelta(days=1)
            next_price = self.db.query(PricesDaily).filter(
                and_(
                    PricesDaily.symbol == symbol,
                    PricesDaily.date == next_date
                )
            ).first()
            if not next_price:
                return None
            execution_price = next_price.open
        else:
            execution_price = price_data.close
        
        # Get current position
        positions = portfolio.positions_json or {}
        current_quantity = positions.get(symbol, 0.0)
        
        # Compute target quantity
        target_position_pct = signal.target_position
        nav = portfolio.nav
        target_value = nav * target_position_pct
        
        if signal.signal == 'LONG':
            target_quantity = target_value / execution_price
        elif signal.signal == 'SHORT':
            target_quantity = -target_value / execution_price
        else:
            target_quantity = 0.0
        
        # Compute trade quantity (difference)
        trade_quantity = target_quantity - current_quantity
        
        # Only execute if meaningful change
        if abs(trade_quantity) < 0.01:  # Less than 0.01 shares
            return None
        
        # Update positions
        new_positions = positions.copy()
        new_positions[symbol] = target_quantity
        portfolio.positions_json = new_positions
        
        # Update cash (simplified - assumes no slippage/commissions for v1)
        cash_change = -trade_quantity * execution_price
        portfolio.cash += cash_change
        
        # Create trade record
        trade = Trades(
            strategy_id=self.strategy.strategy_id,
            symbol=symbol,
            date=target_date,
            side=signal.signal,
            quantity=abs(trade_quantity),
            price=execution_price,
            timing=execution_timing,
            signal_id=signal.id
        )
        
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        
        return trade
    
    def update_portfolio(
        self,
        portfolio: PortfolioDaily,
        target_date: date,
        symbols: List[str]
    ) -> PortfolioDaily:
        """
        Update portfolio with mark-to-market and compute P&L
        
        Returns:
            Updated PortfolioDaily instance
        """
        # Mark to market
        position_value, position_values = self.mark_to_market(
            portfolio, target_date, symbols
        )
        
        # Compute NAV
        nav = portfolio.cash + position_value
        
        # Compute daily P&L
        prev_portfolio = self.db.query(PortfolioDaily).filter(
            and_(
                PortfolioDaily.strategy_id == self.strategy.strategy_id,
                PortfolioDaily.date < target_date
            )
        ).order_by(PortfolioDaily.date.desc()).first()
        
        if prev_portfolio:
            prev_nav = prev_portfolio.nav
            daily_pnl = nav - prev_nav
            cumulative_pnl = (prev_portfolio.cumulative_pnl or 0.0) + daily_pnl
        else:
            daily_pnl = nav - self.initial_nav
            cumulative_pnl = daily_pnl
        
        # Compute drawdown
        peak_nav = self.db.query(func.max(PortfolioDaily.nav)).filter(
            and_(
                PortfolioDaily.strategy_id == self.strategy.strategy_id,
                PortfolioDaily.date <= target_date
            )
        ).scalar() or self.initial_nav
        
        drawdown = (peak_nav - nav) / peak_nav if peak_nav > 0 else 0.0
        
        max_drawdown = portfolio.max_drawdown or 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        
        # Update portfolio
        portfolio.nav = nav
        portfolio.daily_pnl = daily_pnl
        portfolio.cumulative_pnl = cumulative_pnl
        portfolio.drawdown = drawdown
        portfolio.max_drawdown = max_drawdown
        portfolio.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        return portfolio
    
    def simulate_day(
        self,
        symbol: str,
        target_date: date
    ) -> Dict[str, any]:
        """
        Simulate a single day for a symbol
        
        Returns:
            Dictionary with simulation results
        """
        # Get or create portfolio
        portfolio = self.get_or_create_portfolio(target_date)
        
        # Get signal (should already be generated by pipeline)
        signal = self.db.query(SignalsDaily).filter(
            and_(
                SignalsDaily.strategy_id == self.strategy.strategy_id,
                SignalsDaily.symbol == symbol,
                SignalsDaily.date == target_date
            )
        ).first()
        
        if not signal:
            return {
                'success': False,
                'error': 'Signal not found'
            }
        
        # Execute trade
        trade = self.execute_trade(symbol, target_date, signal, portfolio)
        
        # Update portfolio
        portfolio = self.update_portfolio(portfolio, target_date, [symbol])
        
        return {
            'success': True,
            'portfolio': portfolio,
            'trade': trade,
            'signal': signal
        }

