"""
FutureQuant Trader Lean (QuantConnect) Integration Service
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import asyncio

from app.models.trading_models import Symbol, Bar, Strategy, Backtest, Trade
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantLeanService:
    """Lean (QuantConnect) integration service for algorithmic trading"""
    
    def __init__(self):
        self.lean_config = {
            "initial_capital": 100000,
            "benchmark": "SPY",
            "risk_free_rate": 0.02,
            "brokerage_model": "InteractiveBrokersBrokerageModel",
            "data_feed": "InteractiveBrokers",
            "resolution": "Minute",
            "warmup_period": 30
        }
    
    async def run_lean_backtest(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str],
        strategy_code: str,
        custom_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run Lean backtest for a strategy"""
        try:
            db = next(get_db())
            
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Merge configs
            config = self.lean_config.copy()
            if custom_config:
                config.update(custom_config)
            
            # Get historical data
            price_data = await self._get_price_data(db, symbols, start_date, end_date)
            
            if price_data.empty:
                raise ValueError("No price data found for backtest")
            
            # Run Lean backtest simulation
            results = await self._simulate_lean_backtest(price_data, strategy_code, config)
            
            # Store results
            backtest_id = await self._store_lean_results(db, strategy_id, results, start_date, end_date)
            
            return {
                "success": True,
                "backtest_id": backtest_id,
                "results": results,
                "strategy_code": strategy_code,
                "symbols": symbols
            }
            
        except Exception as e:
            logger.error(f"Lean backtest error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_price_data(self, db: Session, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Get price data for symbols"""
        try:
            symbol_objs = db.query(Symbol).filter(Symbol.ticker.in_(symbols)).all()
            symbol_ids = [s.id for s in symbol_objs]
            
            bars = db.query(Bar).filter(
                Bar.symbol_id.in_(symbol_ids),
                Bar.timestamp >= start_date,
                Bar.timestamp <= end_date
            ).order_by(Bar.timestamp).all()
            
            data = []
            for bar in bars:
                symbol_ticker = next(s.ticker for s in symbol_objs if s.id == bar.symbol_id)
                data.append({
                    'timestamp': bar.timestamp,
                    'symbol': symbol_ticker,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                })
            
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index(['timestamp', 'symbol'])
            
            # Create OHLCV structure
            ohlcv = {}
            for symbol in symbols:
                symbol_data = df.xs(symbol, level=1)
                ohlcv[symbol] = symbol_data[['open', 'high', 'low', 'close', 'volume']]
            
            return pd.concat(ohlcv, axis=1)
            
        except Exception as e:
            logger.error(f"Error getting price data: {str(e)}")
            return pd.DataFrame()
    
    async def _simulate_lean_backtest(self, price_data: pd.DataFrame, strategy_code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Lean backtest execution"""
        try:
            # Parse strategy code to extract parameters
            strategy_params = self._parse_strategy_code(strategy_code)
            
            # Initialize portfolio
            initial_capital = config["initial_capital"]
            current_capital = initial_capital
            positions = {symbol: 0 for symbol in price_data.columns.get_level_values(1).unique()}
            
            # Get close prices
            close_prices = price_data.xs('close', level=1, axis=1)
            timestamps = close_prices.index
            
            # Initialize tracking variables
            portfolio_values = []
            trades = []
            current_positions = {}
            
            # Warmup period
            warmup_start = config["warmup_period"]
            
            for i in range(warmup_start, len(timestamps)):
                current_time = timestamps[i]
                current_prices = close_prices.iloc[i]
                
                # Generate signals based on strategy
                signals = self._generate_signals(close_prices.iloc[:i+1], strategy_params)
                
                # Execute trades
                for symbol in current_prices.index:
                    signal = signals.get(symbol, 0)
                    current_price = current_prices[symbol]
                    
                    if signal != 0 and symbol in positions:
                        # Calculate position size
                        position_size = self._calculate_position_size(
                            signal, current_capital, current_price, strategy_params
                        )
                        
                        # Execute trade
                        if position_size != positions[symbol]:
                            trade_size = position_size - positions[symbol]
                            trade_cost = abs(trade_size) * current_price * (1 + config.get("commission_rate", 0.001))
                            
                            if trade_cost <= current_capital:
                                # Update positions and capital
                                old_position = positions[symbol]
                                positions[symbol] = position_size
                                current_capital -= trade_cost
                                
                                # Record trade
                                if trade_size != 0:
                                    trades.append({
                                        "timestamp": current_time,
                                        "symbol": symbol,
                                        "side": "buy" if trade_size > 0 else "sell",
                                        "quantity": abs(trade_size),
                                        "price": current_price,
                                        "cost": trade_cost
                                    })
                
                # Calculate current portfolio value
                portfolio_value = current_capital
                for symbol, position in positions.items():
                    if symbol in current_prices.index:
                        portfolio_value += position * current_prices[symbol]
                
                portfolio_values.append(portfolio_value)
                current_positions[current_time] = positions.copy()
            
            # Calculate performance metrics
            returns = pd.Series(portfolio_values).pct_change().dropna()
            
            results = {
                "strategy_params": strategy_params,
                "initial_capital": initial_capital,
                "final_capital": portfolio_values[-1],
                "total_return": (portfolio_values[-1] - initial_capital) / initial_capital,
                "sharpe_ratio": self._calculate_sharpe_ratio(returns, config["risk_free_rate"]),
                "max_drawdown": self._calculate_max_drawdown(portfolio_values),
                "trades": trades,
                "portfolio_values": portfolio_values,
                "positions_history": current_positions,
                "final_positions": positions
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error simulating Lean backtest: {str(e)}")
            raise e
    
    def _parse_strategy_code(self, strategy_code: str) -> Dict[str, Any]:
        """Parse strategy code to extract parameters"""
        try:
            # Simple parameter extraction - in real implementation, this would parse C# code
            params = {
                "lookback_period": 20,
                "momentum_threshold": 0.02,
                "position_size": 0.1,
                "stop_loss": 0.05,
                "take_profit": 0.10
            }
            
            # Extract parameters from code if possible
            if "lookback" in strategy_code.lower():
                # Extract lookback period
                pass
            
            return params
            
        except Exception as e:
            logger.warning(f"Could not parse strategy code, using defaults: {str(e)}")
            return {
                "lookback_period": 20,
                "momentum_threshold": 0.02,
                "position_size": 0.1,
                "stop_loss": 0.05,
                "take_profit": 0.10
            }
    
    def _generate_signals(self, price_data: pd.DataFrame, strategy_params: Dict[str, Any]) -> Dict[str, int]:
        """Generate trading signals based on strategy parameters"""
        try:
            signals = {}
            
            for symbol in price_data.columns:
                prices = price_data[symbol].dropna()
                
                if len(prices) < strategy_params["lookback_period"]:
                    continue
                
                # Simple momentum strategy
                lookback = strategy_params["lookback_period"]
                momentum = (prices.iloc[-1] - prices.iloc[-lookback]) / prices.iloc[-lookback]
                threshold = strategy_params["momentum_threshold"]
                
                if momentum > threshold:
                    signals[symbol] = 1  # Long signal
                elif momentum < -threshold:
                    signals[symbol] = -1  # Short signal
                else:
                    signals[symbol] = 0  # No signal
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return {}
    
    def _calculate_position_size(self, signal: int, capital: float, price: float, params: Dict[str, Any]) -> float:
        """Calculate position size based on signal and capital"""
        try:
            if signal == 0:
                return 0
            
            position_value = capital * params["position_size"]
            quantity = position_value / price
            
            # Round to reasonable precision
            return round(quantity, 2)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(returns) == 0:
                return 0.0
            
            excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
            if excess_returns.std() == 0:
                return 0.0
            
            return float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            return 0.0
    
    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""
        try:
            if len(portfolio_values) < 2:
                return 0.0
            
            peak = portfolio_values[0]
            max_dd = 0.0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            
            return float(max_dd)
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {str(e)}")
            return 0.0
    
    async def _store_lean_results(self, db: Session, strategy_id: int, results: Dict[str, Any], start_date: str, end_date: str) -> int:
        """Store Lean backtest results in database"""
        try:
            backtest = Backtest(
                strategy_id=strategy_id,
                start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date, "%Y-%m-%d"),
                initial_capital=results.get('initial_capital', 100000),
                final_capital=results.get('final_capital', 100000),
                total_return=results.get('total_return', 0),
                sharpe_ratio=results.get('sharpe_ratio', 0),
                max_drawdown=results.get('max_drawdown', 0),
                win_rate=0,  # Calculate from trades if needed
                profit_factor=0,  # Calculate from trades if needed
                trades_count=len(results.get('trades', [])),
                parameters=results.get('strategy_params', {}),
                results=results,
                status="completed",
                created_at=datetime.utcnow()
            )
            
            db.add(backtest)
            db.commit()
            db.refresh(backtest)
            
            logger.info(f"Stored Lean backtest results with ID: {backtest.id}")
            return backtest.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing Lean backtest results: {str(e)}")
            raise e
    
    async def get_lean_analysis(self, backtest_id: int) -> Dict[str, Any]:
        """Get detailed Lean analysis for a backtest"""
        try:
            db = next(get_db())
            
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise ValueError(f"Backtest {backtest_id} not found")
            
            results = backtest.results
            
            analysis = {
                "backtest_id": backtest_id,
                "strategy_params": results.get('strategy_params'),
                "performance_metrics": {
                    "total_return": results.get('total_return'),
                    "sharpe_ratio": results.get('sharpe_ratio'),
                    "max_drawdown": results.get('max_drawdown'),
                    "trades_count": results.get('trades_count')
                },
                "portfolio_values": results.get('portfolio_values'),
                "trades": results.get('trades'),
                "final_positions": results.get('final_positions')
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting Lean analysis: {str(e)}")
            return {"error": str(e)}
