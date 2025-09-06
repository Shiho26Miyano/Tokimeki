"""
FutureExploratorium Strategy Service
Advanced strategy management and execution for futures trading
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class FutureExploratoriumStrategyService:
    """Strategy Service for FutureExploratorium"""
    
    def __init__(self):
        self.service_name = "FutureExploratoriumStrategyService"
        self.version = "1.0.0"
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache for historical data
    
    async def _fetch_market_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch real market data from Yahoo Finance"""
        try:
            cache_key = f"market_data_{symbol}_{start_date}_{end_date}"
            
            # Check cache first
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_ttl:
                    return cached_data['data']
            
            # Fetch from Yahoo Finance
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            
            data = await loop.run_in_executor(
                self.executor,
                lambda: ticker.history(start=start_date, end=end_date)
            )
            
            if not data.empty:
                # Cache the data
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now().timestamp()
                }
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {str(e)}")
            return None
    
    async def _calculate_strategy_metrics(self, data: pd.DataFrame, strategy_type: str = "momentum") -> Dict[str, Any]:
        """Calculate real strategy performance metrics from market data"""
        try:
            if data.empty or len(data) < 2:
                return {}
            
            # Calculate returns
            data['Returns'] = data['Close'].pct_change().dropna()
            
            # Calculate strategy-specific metrics
            if strategy_type == "momentum":
                # Simple momentum strategy: buy when price > 20-day MA
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['Close'] > data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            elif strategy_type == "mean_reversion":
                # Mean reversion strategy: buy when price < 20-day MA
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['Close'] < data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            else:  # trend_following
                # Trend following: buy when 10-day MA > 20-day MA
                data['MA_10'] = data['Close'].rolling(window=10).mean()
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['MA_10'] > data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            
            # Calculate performance metrics
            strategy_returns = data['Strategy_Returns'].dropna()
            market_returns = data['Returns'].dropna()
            
            if len(strategy_returns) == 0:
                return {}
            
            # Basic metrics
            total_return = (1 + strategy_returns).prod() - 1
            annualized_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
            volatility = strategy_returns.std() * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
            
            # Drawdown calculation
            cumulative_returns = (1 + strategy_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Win rate
            winning_trades = (strategy_returns > 0).sum()
            total_trades = len(strategy_returns)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Profit factor
            gross_profit = strategy_returns[strategy_returns > 0].sum()
            gross_loss = abs(strategy_returns[strategy_returns < 0].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Calmar ratio
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            return {
                "total_return": float(total_return),
                "annualized_return": float(annualized_return),
                "volatility": float(volatility),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "win_rate": float(win_rate),
                "profit_factor": float(profit_factor),
                "calmar_ratio": float(calmar_ratio),
                "total_trades": int(total_trades),
                "winning_trades": int(winning_trades),
                "losing_trades": int(total_trades - winning_trades)
            }
            
        except Exception as e:
            logger.error(f"Error calculating strategy metrics: {str(e)}")
            return {}
    
    async def get_strategy_list(self) -> Dict[str, Any]:
        """Get list of available strategies"""
        try:
            # Mock strategy list
            strategies = [
                {
                    "id": "strategy_001",
                    "name": "Momentum Breakout",
                    "description": "Trades breakouts with momentum confirmation",
                    "status": "active",
                    "performance": {
                        "total_return": 0.125,
                        "sharpe_ratio": 1.85,
                        "max_drawdown": -0.08,
                        "win_rate": 0.68
                    },
                    "created_at": "2024-01-15T10:00:00Z",
                    "last_updated": "2024-01-17T15:30:00Z"
                },
                {
                    "id": "strategy_002",
                    "name": "Mean Reversion",
                    "description": "Trades mean reversion with statistical confirmation",
                    "status": "active",
                    "performance": {
                        "total_return": 0.095,
                        "sharpe_ratio": 1.45,
                        "max_drawdown": -0.12,
                        "win_rate": 0.62
                    },
                    "created_at": "2024-01-10T14:00:00Z",
                    "last_updated": "2024-01-17T12:15:00Z"
                },
                {
                    "id": "strategy_003",
                    "name": "Trend Following",
                    "description": "Follows trends with multiple timeframe confirmation",
                    "status": "paused",
                    "performance": {
                        "total_return": 0.08,
                        "sharpe_ratio": 1.25,
                        "max_drawdown": -0.15,
                        "win_rate": 0.55
                    },
                    "created_at": "2024-01-05T09:00:00Z",
                    "last_updated": "2024-01-16T18:45:00Z"
                }
            ]
            
            return {
                "success": True,
                "strategies": strategies,
                "total_count": len(strategies),
                "message": "Strategy list retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Strategy list error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "strategies": None
            }
    
    async def get_strategy_details(self, strategy_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific strategy"""
        try:
            # Mock strategy details
            strategy_details = {
                "id": strategy_id,
                "name": "Momentum Breakout",
                "description": "Trades breakouts with momentum confirmation",
                "status": "active",
                "parameters": {
                    "lookback_period": 20,
                    "breakout_threshold": 0.02,
                    "momentum_period": 14,
                    "stop_loss": 0.015,
                    "take_profit": 0.03,
                    "position_size": 0.1
                },
                "performance": {
                    "total_return": 0.125,
                    "annualized_return": 0.15,
                    "volatility": 0.18,
                    "sharpe_ratio": 1.85,
                    "max_drawdown": -0.08,
                    "win_rate": 0.68,
                    "profit_factor": 1.45,
                    "calmar_ratio": 1.88
                },
                "risk_metrics": {
                    "var_95": 0.025,
                    "var_99": 0.035,
                    "expected_shortfall": 0.05,
                    "beta": 0.85,
                    "alpha": 0.03
                },
                "trade_statistics": {
                    "total_trades": 156,
                    "winning_trades": 106,
                    "losing_trades": 50,
                    "avg_win": 0.025,
                    "avg_loss": -0.015,
                    "largest_win": 0.08,
                    "largest_loss": -0.05,
                    "avg_trade_duration": "2.5 days"
                },
                "created_at": "2024-01-15T10:00:00Z",
                    "last_updated": "2024-01-17T15:30:00Z"
            }
            
            return {
                "success": True,
                "strategy": strategy_details,
                "message": f"Strategy details for {strategy_id} retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Strategy details error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "strategy": None
            }
    
    async def create_strategy(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new trading strategy"""
        try:
            # Mock strategy creation
            new_strategy = {
                "id": f"strategy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "name": strategy_data.get("name", "New Strategy"),
                "description": strategy_data.get("description", ""),
                "status": "created",
                "parameters": strategy_data.get("parameters", {}),
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "strategy": new_strategy,
                "message": "Strategy created successfully"
            }
            
        except Exception as e:
            logger.error(f"Strategy creation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "strategy": None
            }
    
    async def update_strategy(self, strategy_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing strategy"""
        try:
            # Mock strategy update
            updated_strategy = {
                "id": strategy_id,
                "name": update_data.get("name", "Updated Strategy"),
                "description": update_data.get("description", ""),
                "status": update_data.get("status", "active"),
                "parameters": update_data.get("parameters", {}),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "strategy": updated_strategy,
                "message": f"Strategy {strategy_id} updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Strategy update error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "strategy": None
            }
    
    async def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Delete a strategy"""
        try:
            # Mock strategy deletion
            return {
                "success": True,
                "message": f"Strategy {strategy_id} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Strategy deletion error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_backtest(self, strategy_id: str, backtest_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run backtest for a strategy using real market data"""
        try:
            # Extract parameters
            symbol = backtest_params.get("symbol", "ES=F")  # Default to E-mini S&P 500
            start_date = backtest_params.get("start_date", "2023-01-01")
            end_date = backtest_params.get("end_date", "2024-01-01")
            strategy_type = backtest_params.get("strategy_type", "momentum")
            
            # Fetch real market data
            logger.info(f"Fetching market data for {symbol} from {start_date} to {end_date}")
            data = await self._fetch_market_data(symbol, start_date, end_date)
            
            if data is None or data.empty:
                return {
                    "success": False,
                    "error": f"No data available for {symbol} in the specified date range",
                    "backtest": None
                }
            
            # Calculate strategy metrics
            metrics = await self._calculate_strategy_metrics(data, strategy_type)
            
            if not metrics:
                return {
                    "success": False,
                    "error": "Failed to calculate strategy metrics",
                    "backtest": None
                }
            
            # Generate equity curve
            data['Returns'] = data['Close'].pct_change().dropna()
            if strategy_type == "momentum":
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['Close'] > data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            elif strategy_type == "mean_reversion":
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['Close'] < data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            else:  # trend_following
                data['MA_10'] = data['Close'].rolling(window=10).mean()
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['MA_10'] > data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            
            # Calculate equity curve
            initial_capital = 100000
            cumulative_returns = (1 + data['Strategy_Returns'].fillna(0)).cumprod()
            equity_curve = []
            
            for date, value in cumulative_returns.items():
                equity_curve.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "value": float(initial_capital * value)
                })
            
            # Calculate trade statistics
            strategy_returns = data['Strategy_Returns'].dropna()
            winning_trades = strategy_returns[strategy_returns > 0]
            losing_trades = strategy_returns[strategy_returns < 0]
            
            backtest_results = {
                "strategy_id": strategy_id,
                "backtest_id": f"backtest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "parameters": backtest_params,
                "symbol": symbol,
                "results": {
                    "total_return": metrics.get("total_return", 0),
                    "annualized_return": metrics.get("annualized_return", 0),
                    "volatility": metrics.get("volatility", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                    "calmar_ratio": metrics.get("calmar_ratio", 0)
                },
                "trade_summary": {
                    "total_trades": metrics.get("total_trades", 0),
                    "winning_trades": metrics.get("winning_trades", 0),
                    "losing_trades": metrics.get("losing_trades", 0),
                    "avg_win": float(winning_trades.mean()) if len(winning_trades) > 0 else 0,
                    "avg_loss": float(losing_trades.mean()) if len(losing_trades) > 0 else 0
                },
                "equity_curve": equity_curve,
                "start_date": start_date,
                "end_date": end_date,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "backtest": backtest_results,
                "message": f"Backtest for strategy {strategy_id} completed successfully using real {symbol} data"
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "backtest": None
            }
    
    async def get_strategy_performance(self, strategy_id: str, symbol: str = "ES=F", period: str = "1y") -> Dict[str, Any]:
        """Get performance metrics for a strategy using real market data"""
        try:
            # Calculate date range based on period
            end_date = datetime.now()
            if period == "3mo":
                start_date = end_date - timedelta(days=90)
            elif period == "6mo":
                start_date = end_date - timedelta(days=180)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "2y":
                start_date = end_date - timedelta(days=730)
            else:
                start_date = end_date - timedelta(days=365)
            
            # Fetch real market data
            data = await self._fetch_market_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if data is None or data.empty:
                return {
                    "success": False,
                    "error": f"No data available for {symbol}",
                    "performance": None
                }
            
            # Determine strategy type based on strategy_id
            strategy_type = "momentum"  # Default
            if "mean" in strategy_id.lower() or "reversion" in strategy_id.lower():
                strategy_type = "mean_reversion"
            elif "trend" in strategy_id.lower():
                strategy_type = "trend_following"
            
            # Calculate real performance metrics
            metrics = await self._calculate_strategy_metrics(data, strategy_type)
            
            if not metrics:
                return {
                    "success": False,
                    "error": "Failed to calculate performance metrics",
                    "performance": None
                }
            
            # Calculate additional risk metrics
            data['Returns'] = data['Close'].pct_change().dropna()
            if strategy_type == "momentum":
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['Close'] > data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            elif strategy_type == "mean_reversion":
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['Close'] < data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            else:  # trend_following
                data['MA_10'] = data['Close'].rolling(window=10).mean()
                data['MA_20'] = data['Close'].rolling(window=20).mean()
                data['Signal'] = (data['MA_10'] > data['MA_20']).astype(int)
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            
            strategy_returns = data['Strategy_Returns'].dropna()
            market_returns = data['Returns'].dropna()
            
            # Calculate VaR and other risk metrics
            var_95 = float(strategy_returns.quantile(0.05)) if len(strategy_returns) > 0 else 0
            var_99 = float(strategy_returns.quantile(0.01)) if len(strategy_returns) > 0 else 0
            expected_shortfall = float(strategy_returns[strategy_returns <= var_95].mean()) if len(strategy_returns) > 0 else 0
            
            # Calculate beta and alpha (simplified)
            if len(strategy_returns) > 1 and len(market_returns) > 1:
                covariance = np.cov(strategy_returns, market_returns)[0, 1]
                market_variance = np.var(market_returns)
                beta = covariance / market_variance if market_variance > 0 else 0
                alpha = metrics.get("annualized_return", 0) - beta * market_returns.mean() * 252
            else:
                beta = 0
                alpha = 0
            
            performance_data = {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "period": period,
                "performance_metrics": {
                    "total_return": metrics.get("total_return", 0),
                    "annualized_return": metrics.get("annualized_return", 0),
                    "volatility": metrics.get("volatility", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                    "calmar_ratio": metrics.get("calmar_ratio", 0)
                },
                "risk_metrics": {
                    "var_95": var_95,
                    "var_99": var_99,
                    "expected_shortfall": expected_shortfall,
                    "beta": beta,
                    "alpha": alpha
                },
                "trade_statistics": {
                    "total_trades": metrics.get("total_trades", 0),
                    "winning_trades": metrics.get("winning_trades", 0),
                    "losing_trades": metrics.get("losing_trades", 0),
                    "avg_win": float(strategy_returns[strategy_returns > 0].mean()) if len(strategy_returns) > 0 else 0,
                    "avg_loss": float(strategy_returns[strategy_returns < 0].mean()) if len(strategy_returns) > 0 else 0,
                    "largest_win": float(strategy_returns.max()) if len(strategy_returns) > 0 else 0,
                    "largest_loss": float(strategy_returns.min()) if len(strategy_returns) > 0 else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "performance": performance_data,
                "message": f"Performance data for strategy {strategy_id} retrieved successfully using real {symbol} data"
            }
            
        except Exception as e:
            logger.error(f"Strategy performance error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "performance": None
            }
