"""
FutureQuant Trader QF-Lib Integration Service
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.trading_models import Symbol, Bar, Strategy, Backtest
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantQFLibService:
    """QF-Lib integration service for quantitative finance analysis"""
    
    def __init__(self):
        self.qf_config = {
            "risk_free_rate": 0.02,
            "benchmark": "SPY",
            "confidence_level": 0.95,
            "lookback_period": 252
        }
    
    async def run_qflib_analysis(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str],
        analysis_type: str = "risk_metrics"
    ) -> Dict[str, Any]:
        """Run QF-Lib analysis for a strategy"""
        try:
            db = next(get_db())
            
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            price_data = await self._get_price_data(db, symbols, start_date, end_date)
            
            if price_data.empty:
                raise ValueError("No price data found for analysis")
            
            if analysis_type == "risk_metrics":
                results = await self._calculate_risk_metrics(price_data)
            elif analysis_type == "factor_analysis":
                results = await self._run_factor_analysis(price_data)
            elif analysis_type == "portfolio_optimization":
                results = await self._run_portfolio_optimization(price_data)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "results": results,
                "symbols": symbols
            }
            
        except Exception as e:
            logger.error(f"QF-Lib analysis error: {str(e)}")
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
                    'close': bar.close
                })
            
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index(['timestamp', 'symbol'])
            
            # Pivot to get close prices
            close_prices = df['close'].unstack()
            return close_prices
            
        except Exception as e:
            logger.error(f"Error getting price data: {str(e)}")
            return pd.DataFrame()
    
    async def _calculate_risk_metrics(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics using QF-Lib principles"""
        try:
            returns = price_data.pct_change().dropna()
            
            # Basic statistics
            mean_returns = returns.mean()
            std_returns = returns.std()
            annualized_return = mean_returns * 252
            annualized_volatility = std_returns * np.sqrt(252)
            
            # Risk metrics
            sharpe_ratio = (annualized_return - self.qf_config["risk_free_rate"]) / annualized_volatility
            var_95 = returns.quantile(0.05)
            cvar_95 = returns[returns <= var_95].mean()
            
            # Maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Correlation matrix
            correlation_matrix = returns.corr()
            
            # Beta calculation (assuming first symbol as benchmark)
            if len(returns.columns) > 1:
                benchmark_returns = returns.iloc[:, 0]
                betas = {}
                for col in returns.columns[1:]:
                    covariance = returns[col].cov(benchmark_returns)
                    benchmark_variance = benchmark_returns.var()
                    betas[col] = covariance / benchmark_variance if benchmark_variance != 0 else 0
            else:
                betas = {}
            
            return {
                "returns_analysis": {
                    "annualized_return": annualized_return.to_dict(),
                    "annualized_volatility": annualized_volatility.to_dict(),
                    "sharpe_ratio": sharpe_ratio.to_dict()
                },
                "risk_metrics": {
                    "var_95": var_95.to_dict(),
                    "cvar_95": cvar_95.to_dict(),
                    "max_drawdown": max_drawdown.to_dict()
                },
                "correlation_matrix": correlation_matrix.to_dict(),
                "betas": betas
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            raise e
    
    async def _run_factor_analysis(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Run factor analysis using QF-Lib principles"""
        try:
            returns = price_data.pct_change().dropna()
            
            # Calculate common factors
            market_factor = returns.mean(axis=1)  # Market factor
            size_factor = returns.std(axis=1)     # Volatility factor
            
            # Factor loadings
            factor_loadings = {}
            for symbol in returns.columns:
                # Market factor loading
                market_corr = returns[symbol].corr(market_factor)
                # Size factor loading
                size_corr = returns[symbol].corr(size_factor)
                
                factor_loadings[symbol] = {
                    "market_factor": market_corr,
                    "size_factor": size_corr
                }
            
            # Factor returns
            factor_returns = pd.DataFrame({
                "market_factor": market_factor,
                "size_factor": size_factor
            })
            
            return {
                "factor_loadings": factor_loadings,
                "factor_returns": factor_returns.to_dict(),
                "factor_correlation": factor_returns.corr().to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error running factor analysis: {str(e)}")
            raise e
    
    async def _run_portfolio_optimization(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Run portfolio optimization using QF-Lib principles"""
        try:
            returns = price_data.pct_change().dropna()
            
            # Calculate expected returns and covariance
            expected_returns = returns.mean() * 252
            covariance_matrix = returns.cov() * 252
            
            # Minimum variance portfolio
            inv_cov = np.linalg.inv(covariance_matrix.values)
            ones = np.ones(len(expected_returns))
            min_var_weights = (inv_cov @ ones) / (ones.T @ inv_cov @ ones)
            
            # Maximum Sharpe ratio portfolio
            risk_free_rate = self.qf_config["risk_free_rate"]
            excess_returns = expected_returns - risk_free_rate
            max_sharpe_weights = (inv_cov @ excess_returns) / (excess_returns.T @ inv_cov @ excess_returns)
            
            # Equal weight portfolio
            equal_weights = np.ones(len(expected_returns)) / len(expected_returns)
            
            portfolios = {
                "min_variance": {
                    "weights": dict(zip(expected_returns.index, min_var_weights)),
                    "expected_return": float(expected_returns @ min_var_weights),
                    "volatility": float(np.sqrt(min_var_weights.T @ covariance_matrix.values @ min_var_weights))
                },
                "max_sharpe": {
                    "weights": dict(zip(expected_returns.index, max_sharpe_weights)),
                    "expected_return": float(expected_returns @ max_sharpe_weights),
                    "volatility": float(np.sqrt(max_sharpe_weights.T @ covariance_matrix.values @ max_sharpe_weights))
                },
                "equal_weight": {
                    "weights": dict(zip(expected_returns.index, equal_weights)),
                    "expected_return": float(expected_returns @ equal_weights),
                    "volatility": float(np.sqrt(equal_weights.T @ covariance_matrix.values @ equal_weights))
                }
            }
            
            return {
                "portfolios": portfolios,
                "expected_returns": expected_returns.to_dict(),
                "covariance_matrix": covariance_matrix.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error running portfolio optimization: {str(e)}")
            raise e
