"""
Monitoring endpoints
"""
import time
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ....core.dependencies import get_cache_service, get_usage_service
from ....services.cache_service import AsyncCacheService
from ....services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class CacheClearRequest(BaseModel):
    confirm: bool = True

@router.get("/usage-stats")
async def get_usage_stats(
    period: str = "today",
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get current usage statistics"""
    try:
        stats = await usage_service.get_usage_stats(period)
        return stats
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage-limits")
async def get_usage_limits(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Check if usage limits are exceeded"""
    try:
        limits = await usage_service.check_limits()
        return limits
    except Exception as e:
        logger.error(f"Error checking usage limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache-status")
async def get_cache_status(
    cache_service: AsyncCacheService = Depends(get_cache_service)
):
    """Get cache status and statistics"""
    try:
        # Test cache connection
        cache_test = False
        if cache_service.redis_client:
            try:
                await cache_service.redis_client.ping()
                cache_test = True
            except Exception:
                cache_test = False
        
        return {
            "cache_enabled": cache_service.cache_enabled,
            "redis_connected": cache_service.redis_client is not None,
            "redis_test": cache_test,
            "default_ttl": cache_service.default_ttl
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache-clear")
async def clear_cache(
    background_tasks: BackgroundTasks,
    cache_service: AsyncCacheService = Depends(get_cache_service)
):
    """Clear all cached data in background"""
    try:
        # Add background task
        background_tasks.add_task(cache_service.clear_all)
        
        return {
            "success": True,
            "message": "Cache clearing started in background"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-stats")
async def reset_usage_stats(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Reset usage statistics"""
    try:
        await usage_service.reset_stats()
        return {
            "success": True,
            "message": "Usage statistics reset successfully"
        }
    except Exception as e:
        logger.error(f"Error resetting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-redis")
async def test_redis(
    cache_service: AsyncCacheService = Depends(get_cache_service)
):
    """Test Redis connection and basic operations"""
    try:
        if not cache_service.redis_client:
            return {
                "success": False,
                "error": "Redis client not initialized",
                "cache_enabled": cache_service.cache_enabled
            }
        
        # Test basic Redis operations
        test_key = "test_connection"
        test_value = {"timestamp": time.time(), "message": "Redis test"}
        
        # Set a test value
        await cache_service.redis_client.setex(test_key, 60, str(test_value))
        
        # Get the test value
        retrieved = await cache_service.redis_client.get(test_key)
        
        # Delete the test value
        await cache_service.redis_client.delete(test_key)
        
        return {
            "success": True,
            "message": "Redis connection and operations working",
            "test_key": test_key,
            "test_value": test_value,
            "retrieved": retrieved,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Redis test error: {e}")
        return {
            "success": False,
            "error": str(e),
            "cache_enabled": cache_service.cache_enabled
        }

@router.get("/health")
async def health_check():
    """Health check for monitoring service"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": time.time()
    } 