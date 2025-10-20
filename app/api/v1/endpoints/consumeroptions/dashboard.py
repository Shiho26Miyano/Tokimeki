"""
Consumer Options Dashboard API Endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.consumeroptions.dashboard_service import ConsumerOptionsDashboardService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service
from app.models.options_models import (
    DashboardRequest, DashboardResponse, ContractDrilldownRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for requests
class DashboardDataRequest(BaseModel):
    focus_ticker: str = Field(..., description="Primary ticker for detailed analysis")
    tickers: Optional[List[str]] = Field(None, description="List of all tickers to analyze")
    date_range_days: int = Field(default=60, description="Days of historical data")

class TopMoversRequest(BaseModel):
    tickers: Optional[List[str]] = Field(None, description="List of tickers to analyze")

@router.post("/data", response_model=DashboardResponse)
async def get_dashboard_data(
    request: DashboardDataRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get complete dashboard data for specified ticker"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        result = await dashboard_service.get_dashboard_data(
            focus_ticker=request.focus_ticker.upper(),
            tickers=[t.upper() for t in request.tickers] if request.tickers else None,
            date_range_days=request.date_range_days
        )
        
        await usage_service.track_request(
            endpoint="consumeroptions_dashboard_data",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_dashboard_data",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.get("/data/{ticker}", response_model=DashboardResponse)
async def get_dashboard_data_simple(
    ticker: str,
    days: int = Query(default=60, description="Days of historical data"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get dashboard data for single ticker (simplified endpoint)"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        result = await dashboard_service.get_dashboard_data(
            focus_ticker=ticker.upper(),
            date_range_days=days
        )
        
        await usage_service.track_request(
            endpoint="consumeroptions_dashboard_data_simple",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Dashboard data error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_dashboard_data_simple",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.post("/multi-ticker-analytics")
async def get_multi_ticker_analytics(
    tickers: List[str] = Query(..., description="List of ticker symbols"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get analytics data for multiple tickers"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        ticker_list = [t.upper() for t in tickers]
        result = await dashboard_service.get_multi_ticker_analytics(ticker_list)
        
        await usage_service.track_request(
            endpoint="consumeroptions_multi_ticker_analytics",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Multi-ticker analytics error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_multi_ticker_analytics",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.get("/contract-drilldown/{contract}")
async def get_contract_drilldown(
    contract: str,
    days: int = Query(default=5, description="Days of historical data"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get detailed drilldown data for specific contract"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        result = await dashboard_service.get_contract_drilldown(contract, days)
        
        await usage_service.track_request(
            endpoint="consumeroptions_contract_drilldown",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Contract drilldown error for {contract}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_contract_drilldown",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.post("/top-movers")
async def get_top_movers(
    request: TopMoversRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get top moving options across all tickers"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        tickers = [t.upper() for t in request.tickers] if request.tickers else None
        result = await dashboard_service.get_top_movers(tickers)
        
        await usage_service.track_request(
            endpoint="consumeroptions_top_movers",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Top movers error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_top_movers",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.get("/top-movers")
async def get_top_movers_simple(
    tickers: str = Query(default="COST,WMT,TGT,AMZN,AAPL", description="Comma-separated ticker symbols"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get top movers (simplified endpoint)"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        result = await dashboard_service.get_top_movers(ticker_list)
        
        await usage_service.track_request(
            endpoint="consumeroptions_top_movers_simple",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Top movers simple error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_top_movers_simple",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.get("/summary")
async def get_dashboard_summary(
    tickers: str = Query(default="COST,WMT,TGT,AMZN,AAPL", description="Comma-separated ticker symbols"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get dashboard summary with key metrics"""
    try:
        dashboard_service = ConsumerOptionsDashboardService()
        
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        # Get analytics for all tickers
        analytics_result = await dashboard_service.get_multi_ticker_analytics(ticker_list)
        
        # Get top movers
        top_movers = await dashboard_service.get_top_movers(ticker_list)
        
        # Compile summary
        summary = {
            "market_summary": analytics_result.get("market_summary"),
            "ticker_count": len(ticker_list),
            "tickers": ticker_list,
            "top_volume_contracts": top_movers.get("top_volume", [])[:5],
            "top_unusual_activity": top_movers.get("unusual_activity", [])[:5],
            "timestamp": analytics_result.get("timestamp")
        }
        
        await usage_service.track_request(
            endpoint="consumeroptions_dashboard_summary",
            response_time=0.0,
            success=True
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_dashboard_summary",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await dashboard_service.close()

@router.get("/health")
async def health_check(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Health check endpoint for the dashboard service"""
    try:
        # Basic health check - just verify we can create services
        dashboard_service = ConsumerOptionsDashboardService()
        
        await usage_service.track_request(
            endpoint="consumeroptions_health_check",
            response_time=0.0,
            success=True
        )
        
        return {
            "status": "healthy",
            "service": "Consumer Options Sentiment Dashboard",
            "version": "1.0.0",
            "default_tickers": dashboard_service.default_tickers
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_health_check",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
