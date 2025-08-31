"""
FutureQuant Trader VectorBT Integration Service
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import vectorbt as vbt
from sqlalchemy.orm import Session

from app.models.trading_models import Symbol, Bar, Strategy, Backtest, Trade
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantVectorBTService:
    """VectorBT integration service for advanced backtesting and analysis"""
    
    def __init__(self):
        self.vbt_config = {
            "fees": 0.001,  # 0.1% commission
            "slippage": 0.0005,  # 0.05% slippage
            "freq": "1D",  # Daily frequency
            "init_cash": 100000,  # Initial capital
            "size": 0.1,  # Position size as fraction of portfolio
            "accumulate": False,  # Don't accumulate positions
            "upon_long_conflict": "ignore",  # Ignore conflicting signals
            "upon_short_conflict": "ignore"
        }
    
    async def run_vectorbt_backtest(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str],
        strategy_type: str = "momentum",
        custom_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run VectorBT backtest for a strategy"""
        try:
            # Get database session
            db = next(get_db())
            
            # Get strategy
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Get historical data
            price_data = await self._get_price_data(db, symbols, start_date, end_date)
            
            if price_data.empty:
                raise ValueError("No price data found for backtest")
            
            # Run VectorBT backtest based on strategy type
            if strategy_type == "momentum":
                results = await self._run_momentum_strategy(price_data, custom_params)
            elif strategy_type == "mean_reversion":
                results = await self._run_mean_reversion_strategy(price_data, custom_params)
            elif strategy_type == "trend_following":
                results = await self._run_trend_following_strategy(price_data, custom_params)
            elif strategy_type == "statistical_arbitrage":
                results = await self._run_statistical_arbitrage_strategy(price_data, custom_params)
            else:
                raise ValueError(f"Unsupported strategy type: {strategy_type}")
            
            # Store results in database
            backtest_id = await self._store_backtest_results(db, strategy_id, results, start_date, end_date)
            
            return {
                "success": True,
                "backtest_id": backtest_id,
                "results": results,
                "strategy_type": strategy_type,
                "symbols": symbols
            }
            
        except Exception as e:
            logger.error(f"VectorBT backtest error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_price_data(self, db: Session, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Get price data for symbols"""
        try:
            # Get symbol IDs
            symbol_objs = db.query(Symbol).filter(Symbol.ticker.in_(symbols)).all()
            symbol_ids = [s.id for s in symbol_objs]
            
            # Get bars data
            bars = db.query(Bar).filter(
                Bar.symbol_id.in_(symbol_ids),
                Bar.timestamp >= start_date,
                Bar.timestamp <= end_date
            ).order_by(Bar.timestamp).all()
            
            # Convert to DataFrame
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
            
            # Pivot to get OHLCV data
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
    
    async def _run_momentum_strategy(self, price_data: pd.DataFrame, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run momentum strategy using VectorBT"""
        try:
            # Default parameters
            params = {
                "window": 20,
                "threshold": 0.02,
                "stop_loss": 0.05,
                "take_profit": 0.10
            }
            if custom_params:
                params.update(custom_params)
            
            # Calculate momentum indicators
            close_prices = price_data.xs('close', level=1, axis=1)
            
            # Simple momentum: price change over window
            momentum = close_prices.pct_change(params['window'])
            
            # Generate signals
            long_signal = momentum > params['threshold']
            short_signal = momentum < -params['threshold']
            
            # Run VectorBT backtest
            portfolio = vbt.Portfolio.from_signals(
                close_prices,
                long_signal,
                short_signal,
                **self.vbt_config
            )
            
            # Calculate performance metrics
            stats = portfolio.stats()
            
            return {
                "strategy_type": "momentum",
                "parameters": params,
                "total_return": float(stats['Total Return [%]']),
                "sharpe_ratio": float(stats['Sharpe Ratio']),
                "max_drawdown": float(stats['Max Drawdown [%]']),
                "win_rate": float(stats['Win Rate [%]']),
                "profit_factor": float(stats['Profit Factor']),
                "trades_count": int(stats['Total Trades']),
                "portfolio_value": portfolio.value().iloc[-1],
                "equity_curve": portfolio.value().tolist(),
                "drawdown_curve": portfolio.drawdown().iloc[-1].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error running momentum strategy: {str(e)}")
            raise e
    
    async def _run_mean_reversion_strategy(self, price_data: pd.DataFrame, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run mean reversion strategy using VectorBT"""
        try:
            # Default parameters
            params = {
                "window": 50,
                "std_threshold": 2.0,
                "position_size": 0.1
            }
            if custom_params:
                params.update(custom_params)
            
            close_prices = price_data.xs('close', level=1, axis=1)
            
            # Calculate Bollinger Bands
            rolling_mean = close_prices.rolling(params['window']).mean()
            rolling_std = close_prices.rolling(params['window']).std()
            
            upper_band = rolling_mean + (rolling_std * params['std_threshold'])
            lower_band = rolling_mean - (rolling_std * params['std_threshold'])
            
            # Generate signals
            long_signal = close_prices < lower_band
            short_signal = close_prices > upper_band
            exit_signal = (close_prices >= rolling_mean) & (close_prices <= rolling_mean)
            
            # Run VectorBT backtest
            portfolio = vbt.Portfolio.from_signals(
                close_prices,
                long_signal,
                short_signal,
                exit_signal,
                **self.vbt_config
            )
            
            # Calculate performance metrics
            stats = portfolio.stats()
            
            return {
                "strategy_type": "mean_reversion",
                "parameters": params,
                "total_return": float(stats['Total Return [%]']),
                "sharpe_ratio": float(stats['Sharpe Ratio']),
                "max_drawdown": float(stats['Max Drawdown [%]']),
                "win_rate": float(stats['Win Rate [%]']),
                "profit_factor": float(stats['Profit Factor']),
                "trades_count": int(stats['Total Trades']),
                "portfolio_value": portfolio.value().iloc[-1],
                "equity_curve": portfolio.value().tolist(),
                "drawdown_curve": portfolio.drawdown().iloc[-1].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error running mean reversion strategy: {str(e)}")
            raise e
    
    async def _run_trend_following_strategy(self, price_data: pd.DataFrame, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run trend following strategy using VectorBT"""
        try:
            # Default parameters
            params = {
                "fast_window": 10,
                "slow_window": 30,
                "atr_window": 14,
                "atr_multiplier": 2.0
            }
            if custom_params:
                params.update(custom_params)
            
            close_prices = price_data.xs('close', level=1, axis=1)
            high_prices = price_data.xs('high', level=1, axis=1)
            low_prices = price_data.xs('low', level=1, axis=1)
            
            # Calculate moving averages
            fast_ma = close_prices.rolling(params['fast_window']).mean()
            slow_ma = close_prices.rolling(params['slow_window']).mean()
            
            # Calculate ATR (Average True Range)
            tr1 = high_prices - low_prices
            tr2 = abs(high_prices - close_prices.shift(1))
            tr3 = abs(low_prices - close_prices.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(params['atr_window']).mean()
            
            # Generate signals
            long_signal = fast_ma > slow_ma
            short_signal = fast_ma < slow_ma
            
            # Add ATR-based position sizing
            position_size = self.vbt_config['size'] * (close_prices / atr)
            
            # Run VectorBT backtest
            portfolio = vbt.Portfolio.from_signals(
                close_prices,
                long_signal,
                short_signal,
                size=position_size,
                **self.vbt_config
            )
            
            # Calculate performance metrics
            stats = portfolio.stats()
            
            return {
                "strategy_type": "trend_following",
                "parameters": params,
                "total_return": float(stats['Total Return [%]']),
                "sharpe_ratio": float(stats['Sharpe Ratio']),
                "max_drawdown": float(stats['Max Drawdown [%]']),
                "win_rate": float(stats['Win Rate [%]']),
                "profit_factor": float(stats['Profit Factor']),
                "trades_count": int(stats['Total Trades']),
                "portfolio_value": portfolio.value().iloc[-1],
                "equity_curve": portfolio.value().tolist(),
                "drawdown_curve": portfolio.drawdown().iloc[-1].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error running trend following strategy: {str(e)}")
            raise e
    
    async def _run_statistical_arbitrage_strategy(self, price_data: pd.DataFrame, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run statistical arbitrage strategy using VectorBT"""
        try:
            # Default parameters
            params = {
                "lookback": 60,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "max_holding_period": 20
            }
            if custom_params:
                params.update(custom_params)
            
            close_prices = price_data.xs('close', level=1, axis=1)
            
            # Calculate z-score for each symbol
            rolling_mean = close_prices.rolling(params['lookback']).mean()
            rolling_std = close_prices.rolling(params['lookback']).std()
            z_score = (close_prices - rolling_mean) / rolling_std
            
            # Generate signals based on z-score
            long_signal = z_score < -params['entry_threshold']
            short_signal = z_score > params['entry_threshold']
            exit_signal = abs(z_score) < params['exit_threshold']
            
            # Run VectorBT backtest
            portfolio = vbt.Portfolio.from_signals(
                close_prices,
                long_signal,
                short_signal,
                exit_signal,
                **self.vbt_config
            )
            
            # Calculate performance metrics
            stats = portfolio.stats()
            
            return {
                "strategy_type": "statistical_arbitrage",
                "parameters": params,
                "total_return": float(stats['Total Return [%]']),
                "sharpe_ratio": float(stats['Sharpe Ratio']),
                "max_drawdown": float(stats['Max Drawdown [%]']),
                "win_rate": float(stats['Win Rate [%]']),
                "profit_factor": float(stats['Profit Factor']),
                "trades_count": int(stats['Total Trades']),
                "portfolio_value": portfolio.value().iloc[-1],
                "equity_curve": portfolio.value().tolist(),
                "drawdown_curve": portfolio.drawdown().iloc[-1].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error running statistical arbitrage strategy: {str(e)}")
            raise e
    
    async def _store_backtest_results(self, db: Session, strategy_id: int, results: Dict[str, Any], start_date: str, end_date: str) -> int:
        """Store backtest results in database"""
        try:
            backtest = Backtest(
                strategy_id=strategy_id,
                start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date, "%Y-%m-%d"),
                initial_capital=100000,
                final_capital=results.get('portfolio_value', 100000),
                total_return=results.get('total_return', 0),
                sharpe_ratio=results.get('sharpe_ratio', 0),
                max_drawdown=results.get('max_drawdown', 0),
                win_rate=results.get('win_rate', 0),
                profit_factor=results.get('profit_factor', 0),
                trades_count=results.get('trades_count', 0),
                parameters=results.get('parameters', {}),
                results=results,
                status="completed",
                created_at=datetime.utcnow()
            )
            
            db.add(backtest)
            db.commit()
            db.refresh(backtest)
            
            logger.info(f"Stored VectorBT backtest results with ID: {backtest.id}")
            return backtest.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing backtest results: {str(e)}")
            raise e
    
    async def get_portfolio_analysis(self, backtest_id: int) -> Dict[str, Any]:
        """Get detailed portfolio analysis for a backtest"""
        try:
            db = next(get_db())
            
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise ValueError(f"Backtest {backtest_id} not found")
            
            results = backtest.results
            
            # Additional analysis
            analysis = {
                "backtest_id": backtest_id,
                "strategy_type": results.get('strategy_type'),
                "parameters": results.get('parameters'),
                "performance_metrics": {
                    "total_return": results.get('total_return'),
                    "sharpe_ratio": results.get('sharpe_ratio'),
                    "max_drawdown": results.get('max_drawdown'),
                    "win_rate": results.get('win_rate'),
                    "profit_factor": results.get('profit_factor'),
                    "trades_count": results.get('trades_count')
                },
                "equity_curve": results.get('equity_curve'),
                "drawdown_curve": results.get('drawdown_curve'),
                "risk_metrics": {
                    "volatility": self._calculate_volatility(results.get('equity_curve', [])),
                    "var_95": self._calculate_var(results.get('equity_curve', []), 0.95),
                    "cvar_95": self._calculate_cvar(results.get('equity_curve', []), 0.95)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting portfolio analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_volatility(self, equity_curve: List[float]) -> float:
        """Calculate portfolio volatility"""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        return float(returns.std() * np.sqrt(252))  # Annualized
    
    def _calculate_var(self, equity_curve: List[float], confidence_level: float) -> float:
        """Calculate Value at Risk"""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        return float(np.percentile(returns, (1 - confidence_level) * 100))
    
    def _calculate_cvar(self, equity_curve: List[float], confidence_level: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return float(returns[returns <= var].mean())
