"""
ETF Dashboard API Endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.etf.dashboard_service import ETFDashboardService
from app.services.etf.search_service import ETFSearchService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service
from app.models.etf_models import (
    ETFDashboardResponse, ETFComparison
)

logger = logging.getLogger(__name__)

router = APIRouter()


class DashboardDataRequest(BaseModel):
    """Request for dashboard data"""
    symbol: str = Field(..., description="ETF ticker symbol")
    date_range_days: int = Field(default=365, description="Days of historical data")


class ComparisonRequest(BaseModel):
    """Request for ETF comparison"""
    symbols: List[str] = Field(..., min_items=1, max_items=10, description="List of ETF symbols to compare")


@router.post("/dashboard/data", response_model=ETFDashboardResponse)
async def get_dashboard_data(
    request: DashboardDataRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get complete dashboard data for specified ETF"""
    try:
        dashboard_service = ETFDashboardService()
        
        result = await dashboard_service.get_dashboard_data(
            symbol=request.symbol.upper(),
            date_range_days=request.date_range_days
        )
        
        await usage_service.track_request(
            endpoint="etf_dashboard_data",
            response_time=0.0,
            success=True
        )
        
        # Convert Pydantic model to dict for JSON serialization
        if hasattr(result, 'model_dump'):
            return result.model_dump()
        elif hasattr(result, 'dict'):
            return result.dict()
        return result
        
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_dashboard_data",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{symbol}")
async def get_etf_info(
    symbol: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get ETF basic information"""
    try:
        dashboard_service = ETFDashboardService()
        basic_info = await dashboard_service._get_basic_info(symbol.upper())
        
        if not basic_info:
            raise HTTPException(status_code=404, detail=f"ETF {symbol} not found")
        
        await usage_service.track_request(
            endpoint="etf_info",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "data": basic_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ETF info error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_info",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings/{symbol}")
async def get_etf_holdings(
    symbol: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get ETF holdings information"""
    try:
        dashboard_service = ETFDashboardService()
        holdings = await dashboard_service._get_holdings(symbol.upper())
        
        await usage_service.track_request(
            endpoint="etf_holdings",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "holdings": holdings,
            "total_count": len(holdings)
        }
        
    except Exception as e:
        logger.error(f"ETF holdings error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_holdings",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparison", response_model=List[ETFComparison])
async def get_etf_comparison(
    request: ComparisonRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get comparison data for multiple ETFs"""
    try:
        dashboard_service = ETFDashboardService()
        
        symbols = [s.upper() for s in request.symbols]
        comparisons = await dashboard_service.get_etf_comparison(symbols)
        
        await usage_service.track_request(
            endpoint="etf_comparison",
            response_time=0.0,
            success=True
        )
        
        return comparisons
        
    except Exception as e:
        logger.error(f"ETF comparison error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_comparison",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-metrics/{symbol}")
async def get_risk_metrics(
    symbol: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get risk metrics for ETF"""
    try:
        dashboard_service = ETFDashboardService()
        
        # Get price data first
        end_date = datetime.now().date()
        start_date = end_date.replace(year=end_date.year - 1)  # 1 year
        
        price_data = await dashboard_service._get_price_data(
            symbol.upper(),
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if not price_data or len(price_data) < 30:
            raise HTTPException(
                status_code=400,
                detail="Insufficient price data for risk metrics calculation"
            )
        
        # Calculate risk metrics
        prices = [bar.close for bar in price_data]
        risk_metrics = dashboard_service.analytics_service.calculate_risk_metrics(
            symbol=symbol.upper(),
            prices=prices
        )
        
        await usage_service.track_request(
            endpoint="etf_risk_metrics",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "risk_metrics": risk_metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk metrics error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_risk_metrics",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical-indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get technical indicators for ETF"""
    try:
        dashboard_service = ETFDashboardService()
        
        # Get price data
        end_date = datetime.now().date()
        start_date = end_date.replace(year=end_date.year - 1)  # 1 year
        
        price_data = await dashboard_service._get_price_data(
            symbol.upper(),
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if not price_data or len(price_data) < 20:
            raise HTTPException(
                status_code=400,
                detail="Insufficient price data for technical indicators calculation"
            )
        
        # Calculate technical indicators
        dates = [bar.date for bar in price_data]
        prices = [bar.close for bar in price_data]
        highs = [bar.high for bar in price_data]
        lows = [bar.low for bar in price_data]
        closes = [bar.close for bar in price_data]
        
        indicators = dashboard_service.analytics_service.calculate_technical_indicators(
            symbol=symbol.upper(),
            dates=dates,
            prices=prices,
            highs=highs,
            lows=lows,
            closes=closes
        )
        
        await usage_service.track_request(
            endpoint="etf_technical_indicators",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "indicators": indicators
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Technical indicators error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_technical_indicators",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings-analysis/{symbol}")
async def get_holdings_analysis(
    symbol: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get detailed holdings analysis"""
    try:
        dashboard_service = ETFDashboardService()
        analysis = await dashboard_service.get_etf_holdings_analysis(symbol.upper())
        
        await usage_service.track_request(
            endpoint="etf_holdings_analysis",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            **analysis
        }
        
    except Exception as e:
        logger.error(f"Holdings analysis error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_holdings_analysis",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_etfs(
    query: str = Query(default="", description="Search query for ETF name or ticker"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of results"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Search for ETFs by name or ticker"""
    try:
        search_service = ETFSearchService()
        results = await search_service.search_etfs(query=query, limit=limit)
        
        await usage_service.track_request(
            endpoint="etf_search",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"ETF search error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_search",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
async def get_popular_etfs(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get list of popular ETFs"""
    try:
        search_service = ETFSearchService()
        results = await search_service.get_popular_etfs(limit=limit)
        
        await usage_service.track_request(
            endpoint="etf_popular",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Get popular ETFs error: {str(e)}")
        await usage_service.track_request(
            endpoint="etf_popular",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

