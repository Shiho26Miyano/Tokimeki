"""
FutureExploratorium Dashboard API Endpoints
Independent dashboard functionality for the FutureExploratorium service
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.services.futureexploratorium.dashboard_service import FutureExploratoriumDashboardService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/comprehensive", response_model=dict)
async def get_comprehensive_dashboard(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get comprehensive dashboard data"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service.get_comprehensive_dashboard_data()
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_dashboard_comprehensive",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_dashboard_comprehensive",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Comprehensive dashboard error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_comprehensive",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart", response_model=dict)
async def get_chart_data(
    symbol: str = Query(default="ES=F", description="Symbol to chart"),
    timeframe: str = Query(default="1d", description="Chart timeframe"),
    limit: int = Query(default=100, ge=10, le=1000, description="Number of data points"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get chart data for dashboard"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service.get_chart_data(symbol, timeframe, limit)
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_dashboard_chart",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_dashboard_chart",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Chart data error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_chart",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/{strategy_id}/analytics", response_model=dict)
async def get_strategy_analytics(
    strategy_id: int = Path(..., description="Strategy ID"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get detailed analytics for a specific strategy"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service.get_strategy_analytics(strategy_id)
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_dashboard_strategy_analytics",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_dashboard_strategy_analytics",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Strategy analytics error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_strategy_analytics",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/overview", response_model=dict)
async def get_market_overview(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get market overview data"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_market_overview()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_market_overview",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "market_overview": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Market overview error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_market_overview",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=dict)
async def get_performance_metrics(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get performance metrics"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_strategy_performance()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_performance",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "performance": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_performance",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk", response_model=dict)
async def get_risk_metrics(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get risk metrics"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_risk_metrics()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_risk",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "risk_metrics": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Risk metrics error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_risk",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=dict)
async def get_active_sessions(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get active trading sessions"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_active_sessions()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_sessions",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "sessions": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Active sessions error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_sessions",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system", response_model=dict)
async def get_system_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get system status"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_system_status()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_system",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "system_status": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System status error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_system",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity", response_model=dict)
async def get_recent_activity(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get recent activity"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_recent_activity()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_activity",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "activity": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Recent activity error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_activity",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=dict)
async def get_alerts(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get alerts and notifications"""
    try:
        dashboard_service = FutureExploratoriumDashboardService()
        result = await dashboard_service._get_alerts_and_notifications()
        
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_alerts",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "alerts": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alerts error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_dashboard_alerts",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
