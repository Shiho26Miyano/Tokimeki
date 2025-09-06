"""
FutureExploratorium Dashboard Service
Real-time monitoring and control for the futures trading platform
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.trading_models import Symbol, Bar, Strategy, Backtest, Model, Trade
from app.models.database import get_db
from .futureexploratorium_service import FutureExploratoriumService

logger = logging.getLogger(__name__)

class FutureExploratoriumDashboardService:
    """Dashboard service for real-time monitoring and control"""
    
    def __init__(self):
        self.futureexploratorium_service = FutureExploratoriumService()
        self.dashboard_config = {
            "refresh_interval": 5,  # seconds
            "max_data_points": 1000,
            "chart_timeframes": ["1m", "5m", "15m", "1h", "1d"],
            "supported_indicators": [
                "SMA", "EMA", "RSI", "MACD", "Bollinger Bands", 
                "Stochastic", "ATR", "Volume Profile"
            ]
        }
    
    async def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get all dashboard components in parallel
            tasks = [
                self._get_market_overview(),
                self._get_strategy_performance(),
                self._get_risk_metrics(),
                self._get_active_sessions(),
                self._get_system_status(),
                self._get_recent_activity(),
                self._get_alerts_and_notifications()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            dashboard_data = {
                "market_overview": results[0] if not isinstance(results[0], Exception) else {},
                "strategy_performance": results[1] if not isinstance(results[1], Exception) else {},
                "risk_metrics": results[2] if not isinstance(results[2], Exception) else {},
                "active_sessions": results[3] if not isinstance(results[3], Exception) else {},
                "system_status": results[4] if not isinstance(results[4], Exception) else {},
                "recent_activity": results[5] if not isinstance(results[5], Exception) else [],
                "alerts": results[6] if not isinstance(results[6], Exception) else [],
                "timestamp": datetime.utcnow().isoformat(),
                "refresh_interval": self.dashboard_config["refresh_interval"]
            }
            
            return {
                "success": True,
                "dashboard": dashboard_data
            }
            
        except Exception as e:
            logger.error(f"Dashboard data error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_market_overview(self) -> Dict[str, Any]:
        """Get market overview data"""
        try:
            # Get major futures data
            major_symbols = ["ES=F", "NQ=F", "YM=F", "RTY=F", "CL=F", "GC=F", "SI=F", "ZC=F"]
            market_data = {}
            
            for symbol in major_symbols:
                try:
                    # Get current price and basic metrics
                    current_price = await self.futureexploratorium_service.market_data_service.get_current_price(symbol)
                    if current_price:
                        # Simulate additional metrics
                        market_data[symbol] = {
                            "price": current_price,
                            "change": np.random.uniform(-2, 2),  # Simulated change
                            "change_percent": np.random.uniform(-1, 1),  # Simulated change %
                            "volume": np.random.randint(1000, 10000),  # Simulated volume
                            "high": current_price * (1 + abs(np.random.uniform(0, 0.02))),
                            "low": current_price * (1 - abs(np.random.uniform(0, 0.02))),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                except Exception as e:
                    logger.warning(f"Could not get data for {symbol}: {str(e)}")
            
            return {
                "major_futures": market_data,
                "market_status": "open",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market overview error: {str(e)}")
            return {}
    
    async def _get_strategy_performance(self) -> Dict[str, Any]:
        """Get strategy performance data"""
        try:
            # Get performance summary
            performance_summary = await self.futureexploratorium_service.get_strategy_performance_summary()
            
            if not performance_summary.get("success"):
                return {}
            
            summary = performance_summary.get("summary", {})
            
            # Calculate additional metrics
            total_strategies = summary.get("total_strategies", 0)
            performance_metrics = summary.get("performance_metrics", [])
            
            if performance_metrics:
                avg_return = np.mean([m["total_return"] for m in performance_metrics])
                avg_sharpe = np.mean([m["sharpe_ratio"] for m in performance_metrics])
                avg_drawdown = np.mean([m["max_drawdown"] for m in performance_metrics])
                
                # Performance distribution
                performance_distribution = {
                    "excellent": len([m for m in performance_metrics if m["total_return"] > 0.2]),
                    "good": len([m for m in performance_metrics if 0.1 < m["total_return"] <= 0.2]),
                    "average": len([m for m in performance_metrics if 0.0 < m["total_return"] <= 0.1]),
                    "poor": len([m for m in performance_metrics if m["total_return"] <= 0.0])
                }
            else:
                avg_return = 0
                avg_sharpe = 0
                avg_drawdown = 0
                performance_distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}
            
            return {
                "total_strategies": total_strategies,
                "average_return": avg_return,
                "average_sharpe": avg_sharpe,
                "average_drawdown": avg_drawdown,
                "performance_distribution": performance_distribution,
                "best_performers": summary.get("best_performers", [])[:5],
                "worst_performers": summary.get("worst_performers", [])[:5]
            }
            
        except Exception as e:
            logger.error(f"Strategy performance error: {str(e)}")
            return {}
    
    async def _get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics data"""
        try:
            # Simulate risk metrics
            risk_metrics = {
                "portfolio_var_95": np.random.uniform(0.01, 0.05),  # 1-5% VaR
                "portfolio_var_99": np.random.uniform(0.02, 0.08),  # 2-8% VaR
                "max_drawdown": np.random.uniform(0.05, 0.15),  # 5-15% max drawdown
                "volatility": np.random.uniform(0.10, 0.25),  # 10-25% volatility
                "sharpe_ratio": np.random.uniform(0.5, 2.0),  # 0.5-2.0 Sharpe
                "sortino_ratio": np.random.uniform(0.7, 2.5),  # 0.7-2.5 Sortino
                "calmar_ratio": np.random.uniform(0.3, 1.5),  # 0.3-1.5 Calmar
                "beta": np.random.uniform(0.8, 1.3),  # 0.8-1.3 Beta
                "correlation_to_market": np.random.uniform(0.6, 0.9),  # 0.6-0.9 correlation
                "risk_score": np.random.uniform(3, 8)  # 3-8 risk score (1-10 scale)
            }
            
            # Risk alerts
            risk_alerts = []
            if risk_metrics["portfolio_var_95"] > 0.04:
                risk_alerts.append("High VaR detected - consider reducing position sizes")
            if risk_metrics["max_drawdown"] > 0.10:
                risk_alerts.append("Maximum drawdown exceeded - review risk management")
            if risk_metrics["volatility"] > 0.20:
                risk_alerts.append("High volatility detected - consider hedging strategies")
            
            return {
                "metrics": risk_metrics,
                "alerts": risk_alerts,
                "risk_level": "medium" if risk_metrics["risk_score"] < 6 else "high"
            }
            
        except Exception as e:
            logger.error(f"Risk metrics error: {str(e)}")
            return {}
    
    async def _get_active_sessions(self) -> Dict[str, Any]:
        """Get active trading sessions data"""
        try:
            # Get active sessions from paper broker service
            active_sessions = await self.futureexploratorium_service.paper_broker_service.get_active_sessions()
            
            # Calculate session statistics
            total_sessions = len(active_sessions)
            total_capital = sum(session.get("initial_capital", 0) for session in active_sessions)
            total_pnl = sum(session.get("current_capital", 0) - session.get("initial_capital", 0) for session in active_sessions)
            
            # Session performance
            session_performance = []
            for session in active_sessions:
                initial_capital = session.get("initial_capital", 0)
                current_capital = session.get("current_capital", initial_capital)
                pnl = current_capital - initial_capital
                pnl_percent = (pnl / initial_capital * 100) if initial_capital > 0 else 0
                
                session_performance.append({
                    "session_id": session.get("session_id", "unknown"),
                    "strategy_name": session.get("strategy_name", "Unknown"),
                    "initial_capital": initial_capital,
                    "current_capital": current_capital,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "status": session.get("status", "unknown"),
                    "start_time": session.get("start_time", "").isoformat() if session.get("start_time") else ""
                })
            
            return {
                "total_sessions": total_sessions,
                "total_capital": total_capital,
                "total_pnl": total_pnl,
                "average_pnl_percent": (total_pnl / total_capital * 100) if total_capital > 0 else 0,
                "sessions": session_performance
            }
            
        except Exception as e:
            logger.error(f"Active sessions error: {str(e)}")
            return {}
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get system status data"""
        try:
            # Get system health
            system_health = await self.futureexploratorium_service._get_system_health()
            
            # Get additional system metrics
            db = next(get_db())
            system_metrics = {
                "total_symbols": db.query(Symbol).count(),
                "total_models": db.query(Model).count(),
                "active_models": db.query(Model).filter(Model.status == "active").count(),
                "total_strategies": db.query(Strategy).count(),
                "active_strategies": db.query(Strategy).filter(Strategy.is_active == True).count(),
                "total_backtests": db.query(Backtest).count(),
                "completed_backtests": db.query(Backtest).filter(Backtest.status == "completed").count(),
                "total_trades": db.query(Trade).count()
            }
            
            return {
                "health": system_health,
                "metrics": system_metrics,
                "uptime": "99.9%",  # Simulated
                "last_restart": (datetime.utcnow() - timedelta(days=7)).isoformat(),  # Simulated
                "memory_usage": np.random.uniform(60, 85),  # Simulated
                "cpu_usage": np.random.uniform(20, 60)  # Simulated
            }
            
        except Exception as e:
            logger.error(f"System status error: {str(e)}")
            return {}
    
    async def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity data"""
        try:
            db = next(get_db())
            activities = []
            
            # Recent models
            recent_models = db.query(Model).order_by(Model.updated_at.desc()).limit(5).all()
            for model in recent_models:
                activities.append({
                    "type": "model",
                    "action": f"Model '{model.name}' {model.status}",
                    "timestamp": model.updated_at.isoformat() if model.updated_at else model.registered_at.isoformat(),
                    "status": model.status,
                    "priority": "medium"
                })
            
            # Recent backtests
            recent_backtests = db.query(Backtest).order_by(Backtest.created_at.desc()).limit(5).all()
            for backtest in recent_backtests:
                activities.append({
                    "type": "backtest",
                    "action": f"Backtest {backtest.status}",
                    "timestamp": backtest.created_at.isoformat(),
                    "status": backtest.status,
                    "priority": "low"
                })
            
            # Recent trades
            recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(5).all()
            for trade in recent_trades:
                activities.append({
                    "type": "trade",
                    "action": f"Trade {trade.side} {trade.quantity} {trade.symbol.ticker}",
                    "timestamp": trade.created_at.isoformat(),
                    "status": "completed",
                    "priority": "high"
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:20]
            
        except Exception as e:
            logger.error(f"Recent activity error: {str(e)}")
            return []
    
    async def _get_alerts_and_notifications(self) -> List[Dict[str, Any]]:
        """Get alerts and notifications"""
        try:
            alerts = []
            
            # System alerts
            alerts.append({
                "type": "system",
                "level": "info",
                "message": "System running normally",
                "timestamp": datetime.utcnow().isoformat(),
                "dismissed": False
            })
            
            # Risk alerts
            alerts.append({
                "type": "risk",
                "level": "warning",
                "message": "High volatility detected in ES=F",
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "dismissed": False
            })
            
            # Performance alerts
            alerts.append({
                "type": "performance",
                "level": "success",
                "message": "Strategy 'Momentum ES' achieved 15% return",
                "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "dismissed": False
            })
            
            # Model alerts
            alerts.append({
                "type": "model",
                "level": "info",
                "message": "Model training completed for NQ=F",
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "dismissed": False
            })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Alerts error: {str(e)}")
            return []
    
    async def get_chart_data(
        self, 
        symbol: str, 
        timeframe: str = "1d", 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get chart data for a specific symbol"""
        try:
            # Get historical data
            db = next(get_db())
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            
            if not symbol_obj:
                return {"success": False, "error": f"Symbol {symbol} not found"}
            
            # Get bars
            bars = db.query(Bar).filter(
                Bar.symbol_id == symbol_obj.id
            ).order_by(Bar.timestamp.desc()).limit(limit).all()
            
            if not bars:
                return {"success": False, "error": f"No data found for {symbol}"}
            
            # Convert to chart format
            chart_data = []
            for bar in reversed(bars):  # Reverse to get chronological order
                chart_data.append({
                    "timestamp": bar.timestamp.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume
                })
            
            # Calculate technical indicators
            if len(chart_data) >= 20:
                df = pd.DataFrame(chart_data)
                df['close'] = pd.to_numeric(df['close'])
                
                # Simple Moving Average
                df['sma_20'] = df['close'].rolling(window=20).mean()
                df['sma_50'] = df['close'].rolling(window=min(50, len(df))).mean()
                
                # RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
                
                # Add indicators to chart data
                for i, row in df.iterrows():
                    if i < len(chart_data):
                        chart_data[i]['sma_20'] = float(row['sma_20']) if not pd.isna(row['sma_20']) else None
                        chart_data[i]['sma_50'] = float(row['sma_50']) if not pd.isna(row['sma_50']) else None
                        chart_data[i]['rsi'] = float(row['rsi']) if not pd.isna(row['rsi']) else None
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": chart_data,
                "count": len(chart_data)
            }
            
        except Exception as e:
            logger.error(f"Chart data error for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_strategy_analytics(self, strategy_id: int) -> Dict[str, Any]:
        """Get detailed analytics for a specific strategy"""
        try:
            db = next(get_db())
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            
            if not strategy:
                return {"success": False, "error": "Strategy not found"}
            
            # Get backtests for this strategy
            backtests = db.query(Backtest).filter(
                Backtest.strategy_id == strategy_id
            ).order_by(Backtest.created_at.desc()).all()
            
            # Calculate analytics
            analytics = {
                "strategy_info": {
                    "id": strategy.id,
                    "name": strategy.name,
                    "description": strategy.description,
                    "is_active": strategy.is_active,
                    "created_at": strategy.created_at.isoformat()
                },
                "backtest_summary": {
                    "total_backtests": len(backtests),
                    "completed_backtests": len([b for b in backtests if b.status == "completed"]),
                    "failed_backtests": len([b for b in backtests if b.status == "failed"])
                },
                "performance_metrics": [],
                "risk_metrics": {},
                "recommendations": []
            }
            
            # Process completed backtests
            completed_backtests = [b for b in backtests if b.status == "completed" and b.metrics]
            if completed_backtests:
                returns = [b.metrics.get("total_return", 0) for b in completed_backtests]
                sharpe_ratios = [b.metrics.get("sharpe_ratio", 0) for b in completed_backtests]
                max_drawdowns = [b.metrics.get("max_drawdown", 0) for b in completed_backtests]
                
                analytics["performance_metrics"] = {
                    "average_return": np.mean(returns),
                    "best_return": max(returns),
                    "worst_return": min(returns),
                    "average_sharpe": np.mean(sharpe_ratios),
                    "average_drawdown": np.mean(max_drawdowns),
                    "consistency": 1 - np.std(returns) / (np.mean(returns) + 1e-8)
                }
                
                # Risk metrics
                analytics["risk_metrics"] = {
                    "volatility": np.std(returns),
                    "var_95": np.percentile(returns, 5),
                    "max_drawdown": max(max_drawdowns),
                    "win_rate": len([r for r in returns if r > 0]) / len(returns)
                }
                
                # Recommendations
                if analytics["performance_metrics"]["average_return"] > 0.1:
                    analytics["recommendations"].append("Strategy shows strong performance - consider increasing allocation")
                if analytics["risk_metrics"]["max_drawdown"] > 0.15:
                    analytics["recommendations"].append("High drawdown detected - review risk management parameters")
                if analytics["performance_metrics"]["consistency"] < 0.5:
                    analytics["recommendations"].append("Inconsistent performance - consider parameter optimization")
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Strategy analytics error: {str(e)}")
            return {"success": False, "error": str(e)}
