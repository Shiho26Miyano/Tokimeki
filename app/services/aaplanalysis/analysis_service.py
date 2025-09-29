"""
AAPL Analysis Service - Main coordinator for AAPL stock and options analysis
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date

from .backtest_service import BacktestEngine
from .polygon_service import PolygonService
from .data_pipeline_service import AAPLDataPipeline
from ...models.aapl_analysis_models import (
    StockDCARequest, WeeklyOptionRequest, StockDCAResult, WeeklyOptionResult,
    CombinedBacktestResult, PolygonConfig
)

logger = logging.getLogger(__name__)


class AAPLAnalysisService:
    """Main service for coordinating AAPL analysis operations"""
    
    def __init__(self, polygon_config: PolygonConfig):
        self.polygon_service = PolygonService(polygon_config)
        self.backtest_service = BacktestEngine(self.polygon_service)
        self.data_pipeline = AAPLDataPipeline(polygon_config)
        
        # Background tasks will be started when first needed
        self._background_tasks_started = False
        
    async def _ensure_background_tasks_started(self):
        """Ensure background tasks are started"""
        if not self._background_tasks_started:
            try:
                asyncio.create_task(self._start_background_tasks())
                self._background_tasks_started = True
            except Exception as e:
                logger.warning(f"Failed to start background tasks: {e}")
    
    async def get_defaults(self) -> Dict[str, Any]:
        """Get default parameters for AAPL analysis"""
        await self._ensure_background_tasks_started()
        end_date = datetime.now().date()
        start_date = date(end_date.year - 1, end_date.month, end_date.day)
        
        return {
            "stock_dca": {
                "ticker": "AAPL",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "shares_per_week": 100,
                "buy_weekday": 1,  # Tuesday
                "fee_per_trade": 0.0
            },
            "weekly_option": {
                "ticker": "AAPL",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "option_type": "call",
                "moneyness_offset": 0.0,
                "min_days_to_expiry": 1,
                "contracts_per_week": 1,
                "buy_weekday": 1,  # Tuesday
                "fee_per_trade": 0.0
            }
        }
    
    async def run_stock_backtest(self, params: StockDCARequest) -> StockDCAResult:
        """Run stock DCA backtest"""
        return await self.backtest_service.run_stock_dca_backtest(params)
    
    async def run_option_backtest(self, params: WeeklyOptionRequest) -> WeeklyOptionResult:
        """Run weekly options backtest"""
        return await self.backtest_service.run_weekly_option_backtest(params)
    
    async def run_combined_backtest(
        self, 
        stock_params: StockDCARequest, 
        option_params: WeeklyOptionRequest
    ) -> CombinedBacktestResult:
        """Run combined stock DCA vs weekly options backtest"""
        from ...models.aapl_analysis_models import CombinedBacktestRequest
        combined_request = CombinedBacktestRequest(
            stock_params=stock_params,
            option_params=option_params
        )
        return await self.backtest_service.run_combined_backtest(combined_request)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all AAPL analysis services"""
        try:
            # Test polygon service
            polygon_status = await self.polygon_service.health_check()
            
            return {
                "status": "healthy",
                "services": {
                    "polygon": polygon_status,
                    "backtest": {"status": "healthy"},
                    "analysis": {"status": "healthy"}
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _start_background_tasks(self):
        """Start background tasks for cache management"""
        try:
            # Start background cache refresh
            asyncio.create_task(self.data_pipeline.refresh_cache_background())
            
            # Clean up old snapshots daily
            while True:
                await asyncio.sleep(24 * 3600)  # 24 hours
                await self.data_pipeline.cleanup_old_snapshots()
        except Exception as e:
            logger.error(f"Background task error: {e}")
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get optimized performance data for dashboard"""
        try:
            return await self.data_pipeline.get_performance_summary()
        except Exception as e:
            logger.error(f"Error getting performance dashboard: {e}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
                "status": "error"
            }
    
    async def get_cached_analysis(self) -> Dict[str, Any]:
        """Get cached 3-year analysis data"""
        try:
            snapshot = await self.data_pipeline.get_cached_data_or_generate()
            return {
                "success": True,
                "data": {
                    "timestamp": snapshot.timestamp,
                    "period": {
                        "start": snapshot.period_start,
                        "end": snapshot.period_end
                    },
                    "stock_performance": snapshot.stock_performance,
                    "option_performance": snapshot.option_performance,
                    "comparison_metrics": snapshot.comparison_metrics,
                    "market_summary": snapshot.market_data_summary
                }
            }
        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_data(self) -> Dict[str, Any]:
        """Force refresh of analysis data"""
        try:
            logger.info("Force refreshing AAPL analysis data...")
            snapshot = await self.data_pipeline.generate_3year_snapshot()
            return {
                "success": True,
                "message": "Data refreshed successfully",
                "timestamp": snapshot.timestamp
            }
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self.polygon_service, 'cleanup'):
            await self.polygon_service.cleanup()
