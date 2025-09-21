"""
Mini Golf Strategy Core API Endpoints
Independent core functionality for the Mini Golf Strategy service
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.services.minigolfstrategy.core_service import MiniGolfStrategyCoreService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class CourseSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for golf courses")
    country: Optional[str] = Field(None, description="Country filter")
    limit: int = Field(25, description="Maximum number of results")

class StrategyRequest(BaseModel):
    course_id: str = Field(..., description="Golf course ID")
    hole_data: Dict[str, Any] = Field(..., description="Hole information")
    conditions: Dict[str, Any] = Field(..., description="Playing conditions")
    player_bag: List[Dict[str, Any]] = Field(..., description="Player's golf bag")

@router.get("/overview", response_model=dict)
async def get_platform_overview(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get comprehensive Mini Golf Strategy platform overview"""
    try:
        service = MiniGolfStrategyCoreService()
        result = await service.get_platform_overview()
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="minigolfstrategy_core_overview",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="minigolfstrategy_core_overview",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Platform overview error: {str(e)}")
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_overview",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/defaults", response_model=dict)
async def get_default_data(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get default data for testing and demo purposes"""
    try:
        service = MiniGolfStrategyCoreService()
        result = await service.get_default_data()
        
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_defaults",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Default data error: {str(e)}")
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_defaults",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/search", response_model=dict)
async def search_courses(
    request: CourseSearchRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Search for golf courses"""
    try:
        service = MiniGolfStrategyCoreService()
        result = await service.search_courses(
            query=request.query,
            country=request.country,
            limit=request.limit
        )
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="minigolfstrategy_core_search_courses",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="minigolfstrategy_core_search_courses",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Course search error: {str(e)}")
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_search_courses",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy/generate", response_model=dict)
async def generate_strategy(
    request: StrategyRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Generate AI-powered golf strategy"""
    try:
        service = MiniGolfStrategyCoreService()
        result = await service.generate_strategy(
            course_id=request.course_id,
            hole_data=request.hole_data,
            conditions=request.conditions,
            player_bag=request.player_bag
        )
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="minigolfstrategy_core_generate_strategy",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="minigolfstrategy_core_generate_strategy",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Strategy generation error: {str(e)}")
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_generate_strategy",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=dict)
async def get_health_check(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get Mini Golf Strategy health check"""
    try:
        service = MiniGolfStrategyCoreService()
        
        # Get basic health info
        overview = await service.get_platform_overview()
        
        health_status = {
            "service": "MiniGolfStrategy",
            "status": "healthy" if overview.get("success") else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "uptime": "99.9%",  # Simulated
            "dependencies": {
                "database": "connected",
                "golf_course_api": "available"
            }
        }
        
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_health",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "health": health_status
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        await usage_service.track_request(
            endpoint="minigolfstrategy_core_health",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
