"""
FutureQuant Trader Signal Generation Service - Distribution-Aware Strategy
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.trading_models import Symbol, Bar, Feature, Forecast, Strategy
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantSignalService:
    """Service for generating trading signals from distributional model forecasts"""
    
    def __init__(self):
        self.default_strategies = {
            "conservative": {
                "min_prob": 0.65,
                "max_dd_per_trade": 0.02,
                "risk_budget": 0.02,
                "position_sizing": "kelly",
                "stop_loss": "quantile",
                "take_profit": "quantile",
                "trailing_stop": True,
                "max_leverage": 1.5,
                "cooldown_after_stop": 3,  # days
                "max_trades_per_day": 2
            },
            "moderate": {
                "min_prob": 0.60,
                "max_dd_per_trade": 0.03,
                "risk_budget": 0.03,
                "position_sizing": "kelly",
                "stop_loss": "quantile",
                "take_profit": "quantile",
                "trailing_stop": True,
                "max_leverage": 2.0,
                "cooldown_after_stop": 2,  # days
                "max_trades_per_day": 3
            },
            "aggressive": {
                "min_prob": 0.55,
                "max_dd_per_trade": 0.05,
                "risk_budget": 0.05,
                "position_sizing": "kelly",
                "stop_loss": "quantile",
                "take_profit": "quantile",
                "trailing_stop": False,
                "max_leverage": 3.0,
                "cooldown_after_stop": 1,  # day
                "max_trades_per_day": 5
            }
        }
    
    async def generate_signals(
        self,
        model_id: int,
        strategy_name: str = "moderate",
        start_date: str = None,
        end_date: str = None,
        symbols: List[str] = None,
        custom_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate trading signals based on distributional model forecasts"""
        try:
            # Validate strategy
            if strategy_name not in self.default_strategies:
                raise ValueError(f"Invalid strategy. Must be one of: {list(self.default_strategies.keys())}")
            
            # Set default dates if not provided
            if not start_date or not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Get strategy parameters
            strategy_params = self.default_strategies[strategy_name].copy()
            if custom_params:
                strategy_params.update(custom_params)
            
            # Get database session
            db = next(get_db())
            
            # Get forecasts
            forecasts = await self._get_forecasts(db, model_id, start_date, end_date, symbols)
            
            if not forecasts:
                raise ValueError("No forecasts found for the specified parameters")
            
            # Generate signals using distribution-aware strategy
            signals = await self._generate_distribution_aware_signals(
                db, forecasts, strategy_params
            )
            
            # Store strategy if it doesn't exist
            strategy_id = await self._ensure_strategy_exists(db, strategy_name, strategy_params)
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "signals_count": len(signals),
                "start_date": start_date,
                "end_date": end_date,
                "symbols": symbols or [],
                "signals": signals[:10],  # Return first 10 signals as preview
                "strategy_type": "distribution_aware"
            }
            
        except Exception as e:
            logger.error(f"Signal generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_forecasts(
        self,
        db: Session,
        model_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get distributional forecasts from database"""
        # Build query
        query = db.query(Forecast).filter(
            Forecast.model_id == model_id,
            Forecast.timestamp >= start_date,
            Forecast.timestamp <= end_date
        )
        
        # Add symbol filter if specified
        if symbols:
            symbol_objs = db.query(Symbol).filter(Symbol.ticker.in_(symbols)).all()
            symbol_ids = [s.id for s in symbol_objs]
            query = query.filter(Forecast.symbol_id.in_(symbol_ids))
        
        # Execute query
        forecasts = query.order_by(Forecast.timestamp).all()
        
        # Convert to list of dicts
        result = []
        for forecast in forecasts:
            # Get symbol info
            symbol = db.query(Symbol).filter(Symbol.id == forecast.symbol_id).first()
            
            result.append({
                "id": forecast.id,
                "symbol": symbol.ticker,
                "symbol_id": forecast.symbol_id,
                "timestamp": forecast.timestamp,
                "q10": forecast.q10,
                "q50": forecast.q50,
                "q90": forecast.q90,
                "prob_up": forecast.prob_up,
                "volatility": forecast.volatility,
                "horizon_minutes": forecast.horizon_minutes
            })
        
        return result
    
    async def _generate_distribution_aware_signals(
        self,
        db: Session,
        forecasts: List[Dict[str, Any]],
        strategy_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate signals using distribution-aware strategy"""
        signals = []
        
        for forecast in forecasts:
            try:
                # Get current price
                current_price = await self._get_current_price(db, forecast['symbol_id'])
                if not current_price:
                    continue
                
                # Generate signal using distribution-aware logic
                signal = await self._generate_single_distribution_signal(
                    forecast, current_price, strategy_params
                )
                
                if signal:
                    signal['symbol'] = forecast['symbol']
                    signal['timestamp'] = forecast['timestamp']
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error generating signal for forecast {forecast['id']}: {str(e)}")
                continue
        
        return signals
    
    async def _generate_single_distribution_signal(
        self,
        forecast: Dict[str, Any],
        current_price: float,
        strategy_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a single signal using distribution-aware strategy"""
        try:
            prob_up = forecast['prob_up']
            q10 = forecast['q10']
            q50 = forecast['q50']
            q90 = forecast['q90']
            volatility = forecast['volatility']
            
            min_prob = strategy_params.get('min_prob', 0.60)
            max_dd_per_trade = strategy_params.get('max_dd_per_trade', 0.03)
            
            # Distribution-aware entry conditions
            if prob_up >= min_prob and q50 > current_price:
                # Long signal
                side = "long"
                entry_price = current_price
                stop_loss = q10
                take_profit = q90
                
                # Check drawdown constraint
                drawdown = (entry_price - stop_loss) / entry_price
                if drawdown > max_dd_per_trade:
                    return None
                
            elif (1 - prob_up) >= min_prob and q50 < current_price:
                # Short signal
                side = "short"
                entry_price = current_price
                stop_loss = q90
                take_profit = q10
                
                # Check drawdown constraint
                drawdown = (stop_loss - entry_price) / entry_price
                if drawdown > max_dd_per_trade:
                    return None
                
            else:
                # No signal
                return None
            
            # Calculate position size using Kelly criterion
            position_size = await self._calculate_kelly_position_size(
                forecast, strategy_params, current_price
            )
            
            if position_size <= 0:
                return None
            
            # Create signal
            signal = {
                "side": side,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "position_size": position_size,
                "confidence": prob_up if side == "long" else (1 - prob_up),
                "volatility": volatility,
                "drawdown": drawdown,
                "quantile_forecast": {
                    "q10": q10,
                    "q50": q50,
                    "q90": q90
                },
                "strategy_params": strategy_params
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in single signal generation: {str(e)}")
            return None
    
    async def _calculate_kelly_position_size(
        self,
        forecast: Dict[str, Any],
        strategy_params: Dict[str, Any],
        current_price: float
    ) -> float:
        """Calculate position size using Kelly criterion"""
        sizing_method = strategy_params.get('position_sizing', 'kelly')
        risk_budget = strategy_params.get('risk_budget', 0.03)
        
        if sizing_method == 'kelly':
            # Kelly criterion: f = (bp - q) / b
            # where b = odds received, p = probability of win, q = probability of loss
            
            prob_up = forecast['prob_up']
            q10 = forecast['q10']
            q50 = forecast['q50']
            q90 = forecast['q90']
            
            # Calculate win probability and odds
            if q50 > current_price:  # Long position
                p = prob_up
                q = 1 - prob_up
                # Odds = (take_profit - entry) / (entry - stop_loss)
                odds = (q90 - current_price) / (current_price - q10) if current_price > q10 else 1.0
            else:  # Short position
                p = 1 - prob_up
                q = prob_up
                # Odds = (entry - take_profit) / (stop_loss - entry)
                odds = (current_price - q10) / (q90 - current_price) if q90 > current_price else 1.0
            
            # Kelly fraction
            if p > 0.5 and odds > 1.0:
                kelly_fraction = (odds * p - q) / odds
                # Clamp between 0 and 0.25 (max 25% per trade)
                kelly_fraction = max(0.0, min(kelly_fraction, 0.25))
            else:
                kelly_fraction = 0.0
            
            # Normalize by volatility and risk budget
            volatility = forecast['volatility']
            if volatility > 0:
                # Volatility adjustment
                vol_factor = 1.0 / (1.0 + volatility)
                kelly_fraction *= vol_factor
            
            # Apply risk budget
            position_size = kelly_fraction * risk_budget
            
        else:
            # Fixed sizing
            position_size = risk_budget
        
        # Ensure position size is within bounds
        position_size = max(0.01, min(position_size, 0.10))  # Between 1% and 10%
        
        return position_size
    
    async def _get_current_price(self, db: Session, symbol_id: int) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Get latest bar
            latest_bar = db.query(Bar).filter(
                Bar.symbol_id == symbol_id
            ).order_by(Bar.timestamp.desc()).first()
            
            if latest_bar:
                return latest_bar.close
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            return None
    
    async def _ensure_strategy_exists(
        self,
        db: Session,
        strategy_name: str,
        strategy_params: Dict[str, Any]
    ) -> int:
        """Ensure strategy exists in database, create if not"""
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
        
        if not strategy:
            # Create new strategy
            strategy = Strategy(
                name=strategy_name,
                description=f"Distribution-aware {strategy_name} strategy",
                params=strategy_params,
                is_active=True
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
            logger.info(f"Created strategy: {strategy_name}")
        
        return strategy.id
    
    async def get_signal_summary(
        self,
        strategy_id: int,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """Get summary of signals for a strategy"""
        try:
            # Set default dates if not provided
            if not start_date or not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Get database session
            db = next(get_db())
            
            # Get strategy
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Get signals (this would need to be implemented based on how signals are stored)
            # For now, return basic summary
            summary = {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "start_date": start_date,
                "end_date": end_date,
                "total_signals": 0,  # Placeholder
                "long_signals": 0,   # Placeholder
                "short_signals": 0,  # Placeholder
                "avg_confidence": 0.0,  # Placeholder
                "avg_position_size": 0.0,  # Placeholder
                "strategy_type": "distribution_aware"
            }
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting signal summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_signal(
        self,
        signal: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a signal against portfolio constraints"""
        try:
            validation_result = {
                "valid": True,
                "constraints_passed": [],
                "constraints_failed": [],
                "warnings": []
            }
            
            # Check leverage constraints
            current_leverage = portfolio_state.get("current_leverage", 0.0)
            max_leverage = signal.get("strategy_params", {}).get("max_leverage", 2.0)
            
            if current_leverage >= max_leverage:
                validation_result["valid"] = False
                validation_result["constraints_failed"].append("max_leverage")
            else:
                validation_result["constraints_passed"].append("max_leverage")
            
            # Check daily trade limit
            daily_trades = portfolio_state.get("daily_trades", 0)
            max_daily_trades = signal.get("strategy_params", {}).get("max_trades_per_day", 3)
            
            if daily_trades >= max_daily_trades:
                validation_result["valid"] = False
                validation_result["constraints_failed"].append("max_daily_trades")
            else:
                validation_result["constraints_passed"].append("max_daily_trades")
            
            # Check cooldown after stop loss
            last_stop_loss = portfolio_state.get("last_stop_loss_date")
            cooldown_days = signal.get("strategy_params", {}).get("cooldown_after_stop", 2)
            
            if last_stop_loss:
                days_since_stop = (datetime.now() - last_stop_loss).days
                if days_since_stop < cooldown_days:
                    validation_result["valid"] = False
                    validation_result["constraints_failed"].append("cooldown_after_stop")
                else:
                    validation_result["constraints_passed"].append("cooldown_after_stop")
            else:
                validation_result["constraints_passed"].append("cooldown_after_stop")
            
            # Check position size limits
            position_size = signal.get("position_size", 0.0)
            if position_size > 0.10:  # Max 10% per trade
                validation_result["warnings"].append("position_size_large")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
