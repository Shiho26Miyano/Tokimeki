"""
FutureExploratorium Core Service
Independent orchestration service that interfaces with FutureQuant services
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

# Import FutureQuant services as external dependencies
from app.services.futurequant.data_service import FutureQuantDataService
from app.services.futurequant.feature_service import FutureQuantFeatureService
from app.services.futurequant.model_service import FutureQuantModelService
from app.services.futurequant.signal_service import FutureQuantSignalService
from app.services.futurequant.backtest_service import FutureQuantBacktestService
from app.services.futurequant.paper_broker_service import FutureQuantPaperBrokerService
from app.services.futurequant.unified_quant_service import FutureQuantUnifiedService
from app.services.futurequant.market_data_service import market_data_service

logger = logging.getLogger(__name__)

class FutureExploratoriumCoreService:
    """Core FutureExploratorium service - independent orchestration layer"""
    
    def __init__(self):
        # Initialize FutureQuant services as external dependencies
        self.futurequant_data = FutureQuantDataService()
        self.futurequant_features = FutureQuantFeatureService()
        self.futurequant_models = FutureQuantModelService()
        self.futurequant_signals = FutureQuantSignalService()
        self.futurequant_backtests = FutureQuantBacktestService()
        self.futurequant_paper_trading = FutureQuantPaperBrokerService()
        self.futurequant_unified = FutureQuantUnifiedService()
        self.futurequant_market_data = market_data_service
        
        # FutureExploratorium specific configuration
        self.platform_config = {
            "name": "FutureExploratorium",
            "version": "1.0.0",
            "description": "Advanced Futures Trading Platform",
            "supported_asset_classes": ["Energy", "Metals", "Equity", "Grains", "Currency"],
            "supported_venues": ["CME", "ICE", "NYMEX", "COMEX"],
            "max_concurrent_strategies": 10,
            "max_concurrent_models": 5,
            "max_concurrent_backtests": 3,
            "service_type": "standalone",
            "dependencies": []
        }
    
    async def get_platform_overview(self) -> Dict[str, Any]:
        """Get comprehensive platform overview"""
        try:
            db = next(get_db())
            
            # Get platform statistics
            stats = {
                "symbols": db.query(Symbol).count(),
                "active_strategies": db.query(Strategy).filter(Strategy.is_active == True).count(),
                "trained_models": db.query(Model).filter(Model.status == "active").count(),
                "completed_backtests": db.query(Backtest).filter(Backtest.status == "completed").count(),
                "total_trades": db.query(Trade).count()
            }
            
            # Get recent activity
            recent_activity = await self._get_recent_activity(db)
            
            # Get system health
            system_health = await self._get_system_health()
            
            # Get market overview
            market_overview = await self._get_market_overview()
            
            return {
                "success": True,
                "platform": self.platform_config,
                "statistics": stats,
                "recent_activity": recent_activity,
                "system_health": system_health,
                "market_overview": market_overview,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting platform overview: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_recent_activity(self, db: Session) -> List[Dict[str, Any]]:
        """Get recent platform activity"""
        try:
            activities = []
            
            # Recent models
            recent_models = db.query(Model).order_by(Model.updated_at.desc()).limit(3).all()
            for model in recent_models:
                activities.append({
                    "type": "model",
                    "action": f"Model '{model.name}' {model.status}",
                    "timestamp": model.updated_at.isoformat() if model.updated_at else model.registered_at.isoformat(),
                    "status": model.status,
                    "service": "FutureQuant"
                })
            
            # Recent backtests
            recent_backtests = db.query(Backtest).order_by(Backtest.created_at.desc()).limit(3).all()
            for backtest in recent_backtests:
                activities.append({
                    "type": "backtest",
                    "action": f"Backtest {backtest.status}",
                    "timestamp": backtest.created_at.isoformat(),
                    "status": backtest.status,
                    "service": "FutureQuant"
                })
            
            # Recent trades
            recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(3).all()
            for trade in recent_trades:
                activities.append({
                    "type": "trade",
                    "action": f"Trade {trade.side} {trade.quantity} {trade.symbol.ticker}",
                    "timestamp": trade.created_at.isoformat(),
                    "status": "completed",
                    "service": "FutureQuant"
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:10]
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            health = {
                "status": "healthy",
                "components": {},
                "overall_score": 0.0,
                "service_dependencies": {}
            }
            
            # Check FutureQuant data service
            try:
                data_status = await self.futurequant_data.get_data_status()
                health["components"]["futurequant_data"] = {
                    "status": "healthy",
                    "symbols_available": data_status.get("total_symbols", 0),
                    "last_updated": data_status.get("last_updated", "unknown")
                }
                health["service_dependencies"]["futurequant_data"] = "operational"
            except Exception as e:
                health["components"]["futurequant_data"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health["service_dependencies"]["futurequant_data"] = "error"
            
            # Check FutureQuant model service
            try:
                model_status = await self.futurequant_models.get_model_status()
                health["components"]["futurequant_models"] = {
                    "status": "healthy",
                    "available_models": len(model_status.get("available_model_types", [])),
                    "training_capability": "active"
                }
                health["service_dependencies"]["futurequant_models"] = "operational"
            except Exception as e:
                health["components"]["futurequant_models"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health["service_dependencies"]["futurequant_models"] = "error"
            
            # Check FutureQuant paper trading service
            try:
                paper_status = await self.futurequant_paper_trading.get_paper_trading_status()
                health["components"]["futurequant_paper_trading"] = {
                    "status": "healthy",
                    "active_sessions": len(paper_status.get("active_sessions", [])),
                    "system_status": paper_status.get("system_status", "unknown")
                }
                health["service_dependencies"]["futurequant_paper_trading"] = "operational"
            except Exception as e:
                health["components"]["futurequant_paper_trading"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health["service_dependencies"]["futurequant_paper_trading"] = "error"
            
            # Calculate overall health score
            healthy_components = sum(1 for comp in health["components"].values() if comp["status"] == "healthy")
            total_components = len(health["components"])
            health["overall_score"] = healthy_components / total_components if total_components > 0 else 0.0
            
            if health["overall_score"] < 0.5:
                health["status"] = "unhealthy"
            elif health["overall_score"] < 0.8:
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {"status": "unknown", "error": str(e)}
    
    async def _get_market_overview(self) -> Dict[str, Any]:
        """Get current market overview"""
        try:
            # Get current prices for major futures
            major_symbols = ["ES=F", "NQ=F", "YM=F", "RTY=F", "CL=F", "GC=F", "SI=F"]
            market_data = {}
            
            for symbol in major_symbols:
                try:
                    current_price = await self.futurequant_market_data.get_current_price(symbol)
                    if current_price:
                        market_data[symbol] = {
                            "price": current_price,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                except Exception as e:
                    logger.warning(f"Could not get price for {symbol}: {str(e)}")
            
            return {
                "major_futures": market_data,
                "market_status": "open",  # Simplified
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "FutureQuant Market Data Service"
            }
            
        except Exception as e:
            logger.error(f"Error getting market overview: {str(e)}")
            return {"error": str(e)}
    
    async def run_comprehensive_analysis(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """Run comprehensive analysis using FutureQuant services"""
        try:
            if analysis_types is None:
                analysis_types = [
                    "data_ingestion",
                    "feature_engineering", 
                    "model_training",
                    "signal_generation",
                    "backtesting",
                    "risk_analysis"
                ]
            
            results = {}
            
            # Data ingestion via FutureQuant
            if "data_ingestion" in analysis_types:
                data_result = await self.futurequant_data.ingest_data(
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    interval="1d"
                )
                results["data_ingestion"] = {
                    "service": "FutureQuant",
                    "result": data_result
                }
            
            # Feature engineering via FutureQuant
            if "feature_engineering" in analysis_types:
                feature_results = {}
                for symbol in symbols:
                    feature_result = await self.futurequant_features.compute_features(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        recipe="full"
                    )
                    feature_results[symbol] = {
                        "service": "FutureQuant",
                        "result": feature_result
                    }
                results["feature_engineering"] = feature_results
            
            # Model training via FutureQuant
            if "model_training" in analysis_types:
                model_results = {}
                for symbol in symbols:
                    model_result = await self.futurequant_models.train_model(
                        symbol=symbol,
                        model_type="quantile_regression",
                        horizon_minutes=1440,
                        start_date=start_date,
                        end_date=end_date
                    )
                    model_results[symbol] = {
                        "service": "FutureQuant",
                        "result": model_result
                    }
                results["model_training"] = model_results
            
            # Signal generation via FutureQuant
            if "signal_generation" in analysis_types:
                signal_results = {}
                for symbol in symbols:
                    # Get latest model for symbol
                    db = next(get_db())
                    latest_model = db.query(Model).filter(
                        Model.name.contains(symbol)
                    ).order_by(Model.updated_at.desc()).first()
                    
                    if latest_model:
                        signal_result = await self.futurequant_signals.generate_signals(
                            model_id=latest_model.id,
                            strategy_name="moderate",
                            start_date=start_date,
                            end_date=end_date,
                            symbols=[symbol]
                        )
                        signal_results[symbol] = {
                            "service": "FutureQuant",
                            "result": signal_result
                        }
                results["signal_generation"] = signal_results
            
            # Backtesting via FutureQuant
            if "backtesting" in analysis_types:
                backtest_results = {}
                for symbol in symbols:
                    # Create a simple strategy for backtesting
                    strategy = Strategy(
                        name=f"FutureExploratorium Strategy for {symbol}",
                        description=f"Automated strategy for {symbol} via FutureExploratorium",
                        params={"symbol": symbol, "risk_level": "moderate", "service": "FutureExploratorium"}
                    )
                    db = next(get_db())
                    db.add(strategy)
                    db.commit()
                    db.refresh(strategy)
                    
                    backtest_result = await self.futurequant_backtests.run_backtest(
                        strategy_id=strategy.id,
                        start_date=start_date,
                        end_date=end_date,
                        symbols=[symbol],
                        initial_capital=100000
                    )
                    backtest_results[symbol] = {
                        "service": "FutureQuant",
                        "result": backtest_result
                    }
                results["backtesting"] = backtest_results
            
            # Risk analysis via FutureQuant
            if "risk_analysis" in analysis_types:
                risk_result = await self.futurequant_unified.run_comprehensive_analysis(
                    strategy_id=1,  # Placeholder
                    start_date=start_date,
                    end_date=end_date,
                    symbols=symbols,
                    analysis_types=["risk_metrics", "factor_analysis"]
                )
                results["risk_analysis"] = {
                    "service": "FutureQuant",
                    "result": risk_result
                }
            
            return {
                "success": True,
                "analysis_types": analysis_types,
                "symbols": symbols,
                "date_range": {"start": start_date, "end": end_date},
                "results": results,
                "orchestrated_by": "FutureExploratorium",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all strategy performance"""
        try:
            db = next(get_db())
            
            # Get all completed backtests
            backtests = db.query(Backtest).filter(
                Backtest.status == "completed"
            ).all()
            
            performance_summary = {
                "total_strategies": len(backtests),
                "performance_metrics": [],
                "best_performers": [],
                "worst_performers": [],
                "service_breakdown": {
                    "futurequant_strategies": 0,
                    "futureexploratorium_strategies": 0
                }
            }
            
            for backtest in backtests:
                if backtest.metrics:
                    metrics = backtest.metrics
                    strategy_name = backtest.strategy.name if backtest.strategy else "Unknown"
                    
                    # Determine service based on strategy name or params
                    service = "FutureQuant"
                    if "FutureExploratorium" in strategy_name:
                        service = "FutureExploratorium"
                    elif backtest.strategy and backtest.strategy.params:
                        if backtest.strategy.params.get("service") == "FutureExploratorium":
                            service = "FutureExploratorium"
                    
                    performance_summary["service_breakdown"][f"{service.lower()}_strategies"] += 1
                    
                    performance_summary["performance_metrics"].append({
                        "strategy_id": backtest.strategy_id,
                        "strategy_name": strategy_name,
                        "service": service,
                        "total_return": metrics.get("total_return", 0),
                        "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                        "max_drawdown": metrics.get("max_drawdown", 0),
                        "win_rate": metrics.get("win_rate", 0),
                        "start_date": backtest.start_date.isoformat(),
                        "end_date": backtest.end_date.isoformat()
                    })
            
            # Sort by total return
            performance_summary["performance_metrics"].sort(
                key=lambda x: x["total_return"], reverse=True
            )
            
            # Get best and worst performers
            if performance_summary["performance_metrics"]:
                performance_summary["best_performers"] = performance_summary["performance_metrics"][:3]
                performance_summary["worst_performers"] = performance_summary["performance_metrics"][-3:]
            
            return {
                "success": True,
                "summary": performance_summary,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy performance summary: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data for the platform"""
        try:
            # Get active paper trading sessions from FutureQuant
            active_sessions = await self.futurequant_paper_trading.get_active_sessions()
            
            # Get current market data
            market_data = await self._get_market_overview()
            
            # Get system health
            system_health = await self._get_system_health()
            
            # Get recent activity
            db = next(get_db())
            recent_activity = await self._get_recent_activity(db)
            
            return {
                "success": True,
                "active_sessions": active_sessions,
                "market_data": market_data,
                "system_health": system_health,
                "recent_activity": recent_activity,
                "service_status": {
                    "futureexploratorium": "active",
                    "futurequant": "operational"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time dashboard data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        try:
            status = {
                "futureexploratorium": {
                    "status": "active",
                    "version": self.platform_config["version"],
                    "description": self.platform_config["description"],
                    "capabilities": [
                        "data_ingestion",
                        "feature_engineering", 
                        "model_training",
                        "signal_generation",
                        "backtesting",
                        "paper_trading",
                        "risk_analysis",
                        "strategy_optimization",
                        "real_time_monitoring"
                    ]
                },
                "dependencies": {
                    "database": "connected",
                    "mlflow": "available",
                    "redis": "available",
                    "yfinance": "available"
                }
            }
            
            return {
                "success": True,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {str(e)}")
            return {"success": False, "error": str(e)}
