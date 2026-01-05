"""
FastAPI endpoints for AAPL stock vs options analysis dashboard
"""
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ....models.aapl_analysis_models import (
    StockPriceResponse, OptionChainResponse, OptionOHLCResponse,
    StockDCARequest, WeeklyOptionRequest, CombinedBacktestRequest,
    StockDCAResult, WeeklyOptionResult, CombinedBacktestResult,
    BacktestResponse, PolygonConfig, CacheConfig, AppConfig
)
from ....services.aaplanalysis import AAPLAnalysisService, PolygonService
from ....services.aaplanalysis.backtest_service import BacktestEngine

logger = logging.getLogger(__name__)

# Router for AAPL analysis endpoints
router = APIRouter()

# Global service instance (would be better with dependency injection)
_aapl_analysis_service: AAPLAnalysisService = None


def get_aapl_analysis_service() -> AAPLAnalysisService:
    """Dependency to get AAPL Analysis service instance"""
    global _aapl_analysis_service
    if _aapl_analysis_service is None:
        try:
            api_key = os.getenv("POLYGON_API_KEY")
            if not api_key:
                logger.warning("POLYGON_API_KEY not set - using mock data for AAPL analysis")
                # Use a dummy API key for mock data
                api_key = "mock_key"
            config = PolygonConfig(
                api_key=api_key,
                max_retries=3,
                retry_delay=1.0,
                timeout=30.0
            )
            logger.info(f"Initializing AAPLAnalysisService with API key: {'***' if api_key != 'mock_key' else 'mock_key'}")
            _aapl_analysis_service = AAPLAnalysisService(config)
            logger.info("AAPLAnalysisService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AAPLAnalysisService: {e}", exc_info=True)
            raise
    
    if _aapl_analysis_service is None:
        raise ValueError("AAPLAnalysisService failed to initialize")
    
    return _aapl_analysis_service


@router.get("/prices/{ticker}", response_model=StockPriceResponse)
async def get_stock_prices(
    ticker: str,
    start_date: date,
    end_date: date,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get daily OHLC data from Polygon for a stock ticker"""
    try:
        logger.info(f"Getting stock prices for {ticker} from {start_date} to {end_date}")
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        if (end_date - start_date).days > 365 * 10:  # 10 years max
            raise HTTPException(status_code=400, detail="Date range too large (max 10 years)")
        
        # Validate that end_date is not in the future
        today = date.today()
        if end_date > today:
            logger.warning(f"end_date {end_date} is in the future, adjusting to {today}")
            end_date = today
            if start_date >= end_date:
                raise HTTPException(status_code=400, detail="start_date must be before today")
        
        # Ensure service is initialized
        if analysis_service is None:
            logger.error("AAPLAnalysisService is None - service not initialized")
            raise HTTPException(status_code=500, detail="Service not initialized. Please check POLYGON_API_KEY configuration.")
        
        if analysis_service.polygon_service is None:
            logger.error("PolygonService is None - service not initialized")
            raise HTTPException(status_code=500, detail="Polygon service not initialized")
        
        result = await analysis_service.polygon_service.get_stock_prices(ticker, start_date, end_date)
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting stock prices for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stock prices: {str(e)}")


@router.get("/options/contracts/{ticker}", response_model=OptionChainResponse)
async def get_option_contracts(
    ticker: str,
    expiration_date: date,
    underlying_price: float = None,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get option contracts for a specific expiration date"""
    try:
        logger.info(f"Getting option contracts for {ticker} expiring {expiration_date}")
        
        # Validate expiration date
        if expiration_date <= date.today():
            raise HTTPException(status_code=400, detail="Expiration date must be in the future")
        
        result = await analysis_service.polygon_service.get_option_contracts(
            ticker, expiration_date, underlying_price
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting option contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/ohlc/{option_ticker}", response_model=OptionOHLCResponse)
async def get_option_ohlc(
    option_ticker: str,
    start_date: date,
    end_date: date,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get OHLC data for a specific option contract"""
    try:
        logger.info(f"Getting option OHLC for {option_ticker} from {start_date} to {end_date}")
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        result = await analysis_service.polygon_service.get_option_ohlc(option_ticker, start_date, end_date)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting option OHLC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/stock-dca", response_model=BacktestResponse)
async def run_stock_dca_backtest(
    request: StockDCARequest,
    background_tasks: BackgroundTasks,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Simulate buying shares weekly (DCA strategy)"""
    try:
        logger.info(f"Running stock DCA backtest for {request.ticker}")
        
        # Validate request
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        if request.shares_per_week <= 0:
            raise HTTPException(status_code=400, detail="shares_per_week must be positive")
        
        # Run backtest
        result = await analysis_service.run_stock_backtest(request)
        
        # Get diagnostics
        polygon_diagnostics = analysis_service.polygon_service.get_diagnostics()
        backtest_diagnostics = analysis_service.backtest_service.get_diagnostics()
        
        return BacktestResponse(
            success=True,
            message="Stock DCA backtest completed successfully",
            data=result.dict(),
            diagnostics={
                "polygon": polygon_diagnostics.dict(),
                "backtest": backtest_diagnostics.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Error running stock DCA backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/weekly-option", response_model=BacktestResponse)
async def run_weekly_option_backtest(
    request: WeeklyOptionRequest,
    background_tasks: BackgroundTasks,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Simulate buying weekly options strategy"""
    try:
        logger.info(f"Running weekly option backtest for {request.ticker}")
        
        # Validate request
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        if request.contracts_per_week <= 0:
            raise HTTPException(status_code=400, detail="contracts_per_week must be positive")
        
        # Run backtest
        result = await analysis_service.run_option_backtest(request)
        
        # Get diagnostics
        polygon_diagnostics = analysis_service.polygon_service.get_diagnostics()
        backtest_diagnostics = analysis_service.backtest_service.get_diagnostics()
        
        return BacktestResponse(
            success=True,
            message="Weekly option backtest completed successfully",
            data=result.dict(),
            diagnostics={
                "polygon": polygon_diagnostics.dict(),
                "backtest": backtest_diagnostics.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Error running weekly option backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/combined", response_model=BacktestResponse)
async def run_combined_backtest(
    request: CombinedBacktestRequest,
    background_tasks: BackgroundTasks,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Run both stock DCA and weekly option strategies in one response"""
    try:
        logger.info("Running combined backtest")
        
        # Validate requests
        if request.stock_params.start_date >= request.stock_params.end_date:
            raise HTTPException(status_code=400, detail="Stock start_date must be before end_date")
        
        if request.option_params.start_date >= request.option_params.end_date:
            raise HTTPException(status_code=400, detail="Option start_date must be before end_date")
        
        # Run combined backtest
        result = await analysis_service.run_combined_backtest(request)
        
        # Get diagnostics
        polygon_diagnostics = analysis_service.polygon_service.get_diagnostics()
        backtest_diagnostics = analysis_service.backtest_service.get_diagnostics()
        
        return BacktestResponse(
            success=True,
            message="Combined backtest completed successfully",
            data=result.dict(),
            diagnostics={
                "polygon": polygon_diagnostics.dict(),
                "backtest": backtest_diagnostics.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Error running combined backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnostics")
async def get_diagnostics(
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get system diagnostics and performance metrics"""
    try:
        polygon_diagnostics = analysis_service.polygon_service.get_diagnostics()
        backtest_diagnostics = analysis_service.backtest_service.get_diagnostics()
        
        return {
            "success": True,
            "timestamp": datetime.now(),
            "polygon": polygon_diagnostics.dict(),
            "backtest": backtest_diagnostics.dict(),
            "system": {
                "memory_usage": "N/A",  # Could add psutil here
                "cpu_usage": "N/A",
                "uptime": "N/A"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting diagnostics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "aapl-analysis",
        "version": "1.0.0"
    }


@router.get("/config")
async def get_config():
    """Get current configuration (without sensitive data)"""
    return {
        "polygon_configured": bool(os.getenv("POLYGON_API_KEY")),
        "cache_enabled": True,
        "cache_ttl": 3600,
        "max_retries": 3,
        "timeout": 30.0,
        "supported_tickers": ["AAPL"],  # Could be expanded
        "max_backtest_years": 10
    }


# Optimized endpoints for fast data serving

@router.get("/dashboard")
async def get_dashboard_data(
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get optimized dashboard data (cached, fast response)"""
    try:
        return await analysis_service.get_performance_dashboard()
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/cached")
async def get_cached_analysis(
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get cached 3-year analysis data"""
    try:
        result = await analysis_service.get_cached_analysis()
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        return result["data"]
    except Exception as e:
        logger.error(f"Cached analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_analysis_data(
    background_tasks: BackgroundTasks,
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Force refresh of analysis data (background task)"""
    try:
        # Start refresh in background
        background_tasks.add_task(analysis_service.refresh_data)
        return {
            "message": "Data refresh started in background",
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Default backtest parameters endpoint
@router.get("/defaults")
async def get_default_parameters(
    analysis_service: AAPLAnalysisService = Depends(get_aapl_analysis_service)
):
    """Get default parameters for backtests"""
    try:
        return await analysis_service.get_defaults()
    except Exception as e:
        logger.error(f"Defaults error: {e}")
        # Fallback to static defaults
        one_year_ago = date.today() - timedelta(days=365)
        
        return {
            "stock_dca": {
                "ticker": "AAPL",
                "start_date": one_year_ago.isoformat(),
                "end_date": date.today().isoformat(),
                "shares_per_week": 100,
                "buy_weekday": 1,  # Tuesday
                "fee_per_trade": 0.0
            },
            "weekly_option": {
                "ticker": "AAPL",
                "start_date": one_year_ago.isoformat(),
                "end_date": date.today().isoformat(),
                "option_type": "call",
                "moneyness_offset": 0.0,  # ATM
                "min_days_to_expiry": 1,
                "contracts_per_week": 1,
                "buy_weekday": 1,  # Tuesday
                "fee_per_trade": 0.0
            }
        }
