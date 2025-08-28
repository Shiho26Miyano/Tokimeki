"""
FutureQuant Trader Backtesting Service - Enhanced Engine
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from app.models.trading_models import Symbol, Bar, Feature, Forecast, Strategy, Backtest, Trade
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantBacktestService:
    """Enhanced backtesting engine for distributional futures strategies"""
    
    def __init__(self):
        self.default_configs = {
            "conservative": {
                "initial_capital": 100000,
                "commission_rate": 0.0001,  # 1 bp
                "slippage_bps": 0.5,        # 0.5 bps
                "max_leverage": 1.5,
                "position_limit": 0.20,     # Max 20% in single position
                "daily_loss_limit": 0.02,   # Max 2% daily loss
                "max_drawdown": 0.15,       # Max 15% drawdown
                "risk_free_rate": 0.02,     # 2% annual
                "rebalance_frequency": "daily",
                "cost_model": "realistic",
                "constraints": ["leverage", "position", "drawdown", "daily_loss"]
            },
            "moderate": {
                "initial_capital": 100000,
                "commission_rate": 0.0002,  # 2 bps
                "slippage_bps": 1.0,        # 1 bp
                "max_leverage": 2.0,
                "position_limit": 0.25,     # Max 25% in single position
                "daily_loss_limit": 0.03,   # Max 3% daily loss
                "max_drawdown": 0.20,       # Max 20% drawdown
                "risk_free_rate": 0.02,     # 2% annual
                "rebalance_frequency": "daily",
                "cost_model": "realistic",
                "constraints": ["leverage", "position", "drawdown", "daily_loss"]
            },
            "aggressive": {
                "initial_capital": 100000,
                "commission_rate": 0.0003,  # 3 bps
                "slippage_bps": 2.0,        # 2 bps
                "max_leverage": 3.0,
                "position_limit": 0.30,     # Max 30% in single position
                "daily_loss_limit": 0.05,   # Max 5% daily loss
                "max_drawdown": 0.25,       # Max 25% drawdown
                "risk_free_rate": 0.02,     # 2% annual
                "rebalance_frequency": "daily",
                "cost_model": "realistic",
                "constraints": ["leverage", "position", "drawdown", "daily_loss"]
            }
        }
    
    async def run_backtest(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        config_name: str = "moderate",
        custom_config: Dict[str, Any] = None,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """Run enhanced backtest for a strategy"""
        try:
            # Validate config
            if config_name not in self.default_configs:
                raise ValueError(f"Invalid config. Must be one of: {list(self.default_configs.keys())}")
            
            # Get database session
            db = next(get_db())
            
            # Get strategy
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Merge configs
            config = self.default_configs[config_name].copy()
            if custom_config:
                config.update(custom_config)
            
            # Get backtest data
            backtest_data = await self._get_enhanced_backtest_data(
                db, strategy_id, start_date, end_date, symbols
            )
            
            if not backtest_data.empty:
                backtest_data['timestamp'] = pd.to_datetime(backtest_data['timestamp'])
                backtest_data = backtest_data.set_index('timestamp')
            else:
                raise ValueError("No data found for backtest")
            
            # Execute enhanced backtest
            results = await self._execute_enhanced_backtest(
                db, backtest_data, strategy, config
            )
            
            # Store backtest results
            backtest_id = await self._store_enhanced_backtest_results(
                db, strategy_id, config, results
            )
            
            return {
                "success": True,
                "backtest_id": backtest_id,
                "strategy_name": strategy.name,
                "config_name": config_name,
                "start_date": start_date,
                "end_date": end_date,
                "summary": results["summary"],
                "performance_metrics": results["performance_metrics"],
                "risk_metrics": results["risk_metrics"],
                "trade_analysis": results["trade_analysis"]
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_enhanced_backtest_data(
        self,
        db: Session,
        strategy_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str] = None
    ) -> pd.DataFrame:
        """Get comprehensive data for backtesting"""
        try:
            # Get strategy parameters
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            strategy_params = strategy.params if strategy.params else {}
            
            # Build base query for bars
            bars_query = db.query(Bar).filter(
                Bar.timestamp >= start_date,
                Bar.timestamp <= end_date
            )
            
            # Add symbol filter if specified
            if symbols:
                symbol_objs = db.query(Symbol).filter(Symbol.ticker.in_(symbols)).all()
                symbol_ids = [s.id for s in symbol_objs]
                bars_query = bars_query.filter(Bar.symbol_id.in_(symbol_ids))
            
            # Get bars
            bars = bars_query.order_by(Bar.timestamp).all()
            
            # Convert to DataFrame
            bars_data = []
            for bar in bars:
                symbol = db.query(Symbol).filter(Symbol.id == bar.symbol_id).first()
                bars_data.append({
                    'timestamp': bar.timestamp,
                    'symbol': symbol.ticker,
                    'symbol_id': bar.symbol_id,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                })
            
            bars_df = pd.DataFrame(bars_data)
            
            # Get features
            features_query = db.query(Feature).filter(
                Feature.timestamp >= start_date,
                Feature.timestamp <= end_date
            )
            if symbols:
                features_query = features_query.filter(Feature.symbol_id.in_(symbol_ids))
            
            features = features_query.order_by(Feature.timestamp).all()
            
            # Convert features to DataFrame
            features_data = []
            for feature in features:
                symbol = db.query(Symbol).filter(Symbol.id == feature.symbol_id).first()
                features_data.append({
                    'timestamp': feature.timestamp,
                    'symbol': symbol.ticker,
                    'symbol_id': feature.symbol_id,
                    'features': json.loads(feature.feature_data) if feature.feature_data else {}
                })
            
            features_df = pd.DataFrame(features_data)
            
            # Get forecasts
            forecasts_query = db.query(Forecast).filter(
                Forecast.timestamp >= start_date,
                Forecast.timestamp <= end_date
            )
            if symbols:
                forecasts_query = forecasts_query.filter(Forecast.symbol_id.in_(symbol_ids))
            
            forecasts = forecasts_query.order_by(Forecast.timestamp).all()
            
            # Convert forecasts to DataFrame
            forecasts_data = []
            for forecast in forecasts:
                symbol = db.query(Symbol).filter(Symbol.id == forecast.symbol_id).first()
                forecasts_data.append({
                    'timestamp': forecast.timestamp,
                    'symbol': symbol.ticker,
                    'symbol_id': forecast.symbol_id,
                    'q10': forecast.q10,
                    'q50': forecast.q50,
                    'q90': forecast.q90,
                    'prob_up': forecast.prob_up,
                    'volatility': forecast.volatility,
                    'horizon_minutes': forecast.horizon_minutes
                })
            
            forecasts_df = pd.DataFrame(forecasts_data)
            
            # Merge all data
            if not bars_df.empty and not features_df.empty:
                merged_df = bars_df.merge(
                    features_df, on=['timestamp', 'symbol', 'symbol_id'], how='left'
                )
            else:
                merged_df = bars_df if not bars_df.empty else features_df
            
            if not merged_df.empty and not forecasts_df.empty:
                merged_df = merged_df.merge(
                    forecasts_df, on=['timestamp', 'symbol', 'symbol_id'], how='left'
                )
            
            # Sort by timestamp
            if not merged_df.empty:
                merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
            
            return merged_df
            
        except Exception as e:
            logger.error(f"Error getting backtest data: {str(e)}")
            return pd.DataFrame()
    
    async def _execute_enhanced_backtest(
        self,
        db: Session,
        data: pd.DataFrame,
        strategy: Strategy,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute enhanced backtest with realistic cost modeling and constraints"""
        try:
            # Initialize portfolio
            portfolio = {
                'cash': config['initial_capital'],
                'positions': {},
                'total_value': config['initial_capital'],
                'daily_pnl': [],
                'trades': [],
                'constraints_violated': []
            }
            
            # Get unique dates
            data['date'] = pd.to_datetime(data['timestamp']).dt.date
            unique_dates = sorted(data['date'].unique())
            
            # Daily backtest loop
            for date in unique_dates:
                daily_data = data[data['date'] == date]
                
                # Check constraints before trading
                constraint_check = await self._check_portfolio_constraints(
                    portfolio, config, date
                )
                
                if not constraint_check['valid']:
                    portfolio['constraints_violated'].append({
                        'date': date,
                        'violations': constraint_check['violations']
                    })
                    # Close all positions if critical constraint violated
                    if any(v in ['max_drawdown', 'daily_loss'] for v in constraint_check['violations']):
                        await self._close_all_positions(portfolio, daily_data, config)
                        continue
                
                # Generate daily signals
                signals = await self._generate_daily_distribution_signals(
                    daily_data, strategy, portfolio
                )
                
                # Execute trades
                await self._execute_daily_trades(
                    portfolio, signals, daily_data, config
                )
                
                # Update portfolio
                await self._update_enhanced_portfolio(
                    portfolio, daily_data, config
                )
                
                # Record daily P&L
                portfolio['daily_pnl'].append({
                    'date': date,
                    'total_value': portfolio['total_value'],
                    'cash': portfolio['cash'],
                    'positions_value': sum(pos['value'] for pos in portfolio['positions'].values())
                })
            
            # Calculate comprehensive metrics
            performance_metrics = await self._calculate_enhanced_performance_metrics(
                portfolio, config
            )
            
            risk_metrics = await self._calculate_enhanced_risk_metrics(
                portfolio, config
            )
            
            trade_analysis = await self._analyze_trades(portfolio)
            
            return {
                'portfolio': portfolio,
                'summary': {
                    'initial_capital': config['initial_capital'],
                    'final_value': portfolio['total_value'],
                    'total_return': (portfolio['total_value'] - config['initial_capital']) / config['initial_capital'],
                    'total_trades': len(portfolio['trades']),
                    'constraints_violated': len(portfolio['constraints_violated'])
                },
                'performance_metrics': performance_metrics,
                'risk_metrics': risk_metrics,
                'trade_analysis': trade_analysis
            }
            
        except Exception as e:
            logger.error(f"Error executing backtest: {str(e)}")
            raise
    
    async def _check_portfolio_constraints(
        self,
        portfolio: Dict[str, Any],
        config: Dict[str, Any],
        date: datetime.date
    ) -> Dict[str, Any]:
        """Check portfolio constraints"""
        violations = []
        
        # Calculate current leverage
        positions_value = sum(pos['value'] for pos in portfolio['positions'].values())
        current_leverage = positions_value / portfolio['total_value'] if portfolio['total_value'] > 0 else 0
        
        if current_leverage > config['max_leverage']:
            violations.append('max_leverage')
        
        # Check position limits
        for symbol, position in portfolio['positions'].items():
            position_weight = position['value'] / portfolio['total_value']
            if position_weight > config['position_limit']:
                violations.append('position_limit')
                break
        
        # Check daily loss limit
        if portfolio['daily_pnl']:
            yesterday_pnl = portfolio['daily_pnl'][-1]
            daily_return = (portfolio['total_value'] - yesterday_pnl['total_value']) / yesterday_pnl['total_value']
            if daily_return < -config['daily_loss_limit']:
                violations.append('daily_loss')
        
        # Check max drawdown
        if portfolio['daily_pnl']:
            peak_value = max(pnl['total_value'] for pnl in portfolio['daily_pnl'])
            current_drawdown = (peak_value - portfolio['total_value']) / peak_value
            if current_drawdown > config['max_drawdown']:
                violations.append('max_drawdown')
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    async def _generate_daily_distribution_signals(
        self,
        daily_data: pd.DataFrame,
        strategy: Strategy,
        portfolio: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate daily trading signals using distribution-aware logic"""
        signals = []
        
        for _, row in daily_data.iterrows():
            if pd.isna(row.get('prob_up')) or pd.isna(row.get('q50')):
                continue
            
            # Simple signal generation based on distribution
            prob_up = row['prob_up']
            q50 = row['q50']
            current_price = row['close']
            
            if prob_up > 0.6 and q50 > current_price:
                signals.append({
                    'symbol': row['symbol'],
                    'side': 'long',
                    'entry_price': current_price,
                    'stop_loss': row.get('q10', current_price * 0.95),
                    'take_profit': row.get('q90', current_price * 1.05),
                    'confidence': prob_up,
                    'timestamp': row['timestamp']
                })
            elif prob_up < 0.4 and q50 < current_price:
                signals.append({
                    'symbol': row['symbol'],
                    'side': 'short',
                    'entry_price': current_price,
                    'stop_loss': row.get('q90', current_price * 1.05),
                    'take_profit': row.get('q10', current_price * 0.95),
                    'confidence': 1 - prob_up,
                    'timestamp': row['timestamp']
                })
        
        return signals
    
    async def _execute_daily_trades(
        self,
        portfolio: Dict[str, Any],
        signals: List[Dict[str, Any]],
        daily_data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Execute daily trades with realistic cost modeling"""
        for signal in signals:
            # Check if we already have a position
            if signal['symbol'] in portfolio['positions']:
                continue
            
            # Calculate position size (simplified)
            position_size = 0.1  # 10% of portfolio
            position_value = portfolio['total_value'] * position_size
            
            # Calculate costs
            commission = position_value * config['commission_rate']
            slippage = position_value * (config['slippage_bps'] / 10000)
            total_cost = commission + slippage
            
            # Check if we have enough cash
            if portfolio['cash'] < (position_value + total_cost):
                continue
            
            # Open position
            portfolio['positions'][signal['symbol']] = {
                'side': signal['side'],
                'entry_price': signal['entry_price'],
                'entry_date': signal['timestamp'],
                'quantity': position_value / signal['entry_price'],
                'value': position_value,
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit']
            }
            
            # Update cash
            portfolio['cash'] -= (position_value + total_cost)
            
            # Record trade
            portfolio['trades'].append({
                'timestamp': signal['timestamp'],
                'symbol': signal['symbol'],
                'side': 'buy' if signal['side'] == 'long' else 'sell',
                'price': signal['entry_price'],
                'quantity': position_value / signal['entry_price'],
                'value': position_value,
                'commission': commission,
                'slippage': slippage,
                'total_cost': total_cost
            })
    
    async def _update_enhanced_portfolio(
        self,
        portfolio: Dict[str, Any],
        daily_data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Update portfolio with realistic P&L and position management"""
        # Update position values
        for symbol, position in portfolio['positions'].items():
            symbol_data = daily_data[daily_data['symbol'] == symbol]
            if not symbol_data.empty:
                current_price = symbol_data.iloc[0]['close']
                
                # Update position value
                if position['side'] == 'long':
                    position['value'] = position['quantity'] * current_price
                else:  # short
                    position['value'] = position['quantity'] * (2 * position['entry_price'] - current_price)
                
                # Check stop loss and take profit
                if position['side'] == 'long':
                    if current_price <= position['stop_loss'] or current_price >= position['take_profit']:
                        await self._close_position(portfolio, symbol, current_price, config)
                else:  # short
                    if current_price >= position['stop_loss'] or current_price <= position['take_profit']:
                        await self._close_position(portfolio, symbol, current_price, config)
        
        # Update total portfolio value
        positions_value = sum(pos['value'] for pos in portfolio['positions'].values())
        portfolio['total_value'] = portfolio['cash'] + positions_value
    
    async def _close_position(
        self,
        portfolio: Dict[str, Any],
        symbol: str,
        current_price: float,
        config: Dict[str, Any]
    ) -> None:
        """Close a position with realistic cost modeling"""
        position = portfolio['positions'][symbol]
        
        # Calculate exit value
        if position['side'] == 'long':
            exit_value = position['quantity'] * current_price
        else:  # short
            exit_value = position['quantity'] * (2 * position['entry_price'] - current_price)
        
        # Calculate costs
        commission = exit_value * config['commission_rate']
        slippage = exit_value * (config['slippage_bps'] / 10000)
        total_cost = commission + slippage
        
        # Update cash
        portfolio['cash'] += (exit_value - total_cost)
        
        # Record trade
        portfolio['trades'].append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': 'sell' if position['side'] == 'long' else 'buy',
            'price': current_price,
            'quantity': position['quantity'],
            'value': exit_value,
            'commission': commission,
            'slippage': slippage,
            'total_cost': total_cost
        })
        
        # Remove position
        del portfolio['positions'][symbol]
    
    async def _close_all_positions(
        self,
        portfolio: Dict[str, Any],
        daily_data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Close all positions"""
        symbols_to_close = list(portfolio['positions'].keys())
        for symbol in symbols_to_close:
            symbol_data = daily_data[daily_data['symbol'] == symbol]
            if not symbol_data.empty:
                current_price = symbol_data.iloc[0]['close']
                await self._close_position(portfolio, symbol, current_price, config)
    
    async def _calculate_enhanced_performance_metrics(
        self,
        portfolio: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not portfolio['daily_pnl']:
            return {}
        
        daily_pnl_df = pd.DataFrame(portfolio['daily_pnl'])
        daily_pnl_df['date'] = pd.to_datetime(daily_pnl_df['date'])
        daily_pnl_df = daily_pnl_df.sort_values('date')
        
        # Calculate returns
        daily_pnl_df['daily_return'] = daily_pnl_df['total_value'].pct_change()
        
        # Performance metrics
        total_return = (portfolio['total_value'] - config['initial_capital']) / config['initial_capital']
        annualized_return = total_return * (252 / len(daily_pnl_df)) if len(daily_pnl_df) > 1 else 0
        
        # Risk metrics
        daily_returns = daily_pnl_df['daily_return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0
        
        # Sharpe ratio
        risk_free_rate = config.get('risk_free_rate', 0.02)
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': self._calculate_win_rate(portfolio['trades']),
            'profit_factor': self._calculate_profit_factor(portfolio['trades']),
            'avg_trade': self._calculate_avg_trade(portfolio['trades'])
        }
    
    async def _calculate_enhanced_risk_metrics(
        self,
        portfolio: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        if not portfolio['daily_pnl']:
            return {}
        
        daily_pnl_df = pd.DataFrame(portfolio['daily_pnl'])
        daily_pnl_df['date'] = pd.to_datetime(daily_pnl_df['date'])
        daily_pnl_df = daily_pnl_df.sort_values('date')
        
        # VaR and CVaR
        daily_returns = daily_pnl_df['total_value'].pct_change().dropna()
        
        if len(daily_returns) > 0:
            var_95 = np.percentile(daily_returns, 5)
            var_99 = np.percentile(daily_returns, 1)
            
            cvar_95 = daily_returns[daily_returns <= var_95].mean()
            cvar_99 = daily_returns[daily_returns <= var_99].mean()
        else:
            var_95 = var_99 = cvar_95 = cvar_99 = 0
        
        # Beta (simplified - would need market data for proper calculation)
        beta = 1.0  # Placeholder
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'beta': beta,
            'constraints_violated': len(portfolio['constraints_violated']),
            'max_leverage_used': max(
                (pnl['positions_value'] / pnl['total_value'] for pnl in portfolio['daily_pnl']),
                default=0
            )
        }
    
    async def _analyze_trades(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trade performance"""
        if not portfolio['trades']:
            return {}
        
        trades_df = pd.DataFrame(portfolio['trades'])
        
        # Group trades by symbol
        symbol_analysis = {}
        for symbol in trades_df['symbol'].unique():
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            
            # Calculate P&L for symbol
            buy_trades = symbol_trades[symbol_trades['side'] == 'buy']
            sell_trades = symbol_trades[symbol_trades['side'] == 'sell']
            
            if len(buy_trades) > 0 and len(sell_trades) > 0:
                # Simplified P&L calculation
                avg_buy_price = buy_trades['price'].mean()
                avg_sell_price = sell_trades['price'].mean()
                symbol_pnl = (avg_sell_price - avg_buy_price) / avg_buy_price
            else:
                symbol_pnl = 0
            
            symbol_analysis[symbol] = {
                'total_trades': len(symbol_trades),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'pnl': symbol_pnl,
                'total_commission': symbol_trades['commission'].sum(),
                'total_slippage': symbol_trades['slippage'].sum()
            }
        
        return {
            'total_trades': len(portfolio['trades']),
            'symbol_analysis': symbol_analysis,
            'total_commission': trades_df['commission'].sum(),
            'total_slippage': trades_df['slippage'].sum(),
            'total_costs': trades_df['total_cost'].sum()
        }
    
    def _calculate_win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate win rate from trades"""
        if not trades:
            return 0.0
        
        # This is a simplified calculation - would need proper P&L tracking
        return 0.5  # Placeholder
    
    def _calculate_profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate profit factor from trades"""
        if not trades:
            return 0.0
        
        # This is a simplified calculation - would need proper P&L tracking
        return 1.0  # Placeholder
    
    def _calculate_avg_trade(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate average trade P&L"""
        if not trades:
            return 0.0
        
        # This is a simplified calculation - would need proper P&L tracking
        return 0.0  # Placeholder
    
    async def _store_enhanced_backtest_results(
        self,
        db: Session,
        strategy_id: int,
        config: Dict[str, Any],
        results: Dict[str, Any]
    ) -> int:
        """Store enhanced backtest results"""
        try:
            backtest = Backtest(
                strategy_id=strategy_id,
                start_date=results['summary'].get('start_date'),
                end_date=results['summary'].get('end_date'),
                config=config,
                results=results,
                status="completed"
            )
            
            db.add(backtest)
            db.commit()
            db.refresh(backtest)
            
            logger.info(f"Stored backtest results with ID: {backtest.id}")
            return backtest.id
            
        except Exception as e:
            logger.error(f"Error storing backtest results: {str(e)}")
            db.rollback()
            raise
