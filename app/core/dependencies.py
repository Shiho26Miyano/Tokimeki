from fastapi import Depends
from typing import AsyncGenerator
import httpx
import redis.asyncio as redis
from .config import settings

# HTTP Client dependency with connection pooling
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Dependency for HTTP client with connection pooling"""
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        timeout=httpx.Timeout(30.0)
    ) as client:
        yield client

# Redis client dependency
async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Dependency for Redis client"""
    if settings.redis_url:
        redis_client = redis.from_url(settings.redis_url)
        try:
            await redis_client.ping()
            yield redis_client
        finally:
            await redis_client.close()
    else:
        yield None

# Cache service dependency
async def get_cache_service(redis_client: redis.Redis = Depends(get_redis_client)):
    """Dependency for cache service"""
    from ..services.cache_service import AsyncCacheService
    return AsyncCacheService(redis_client)

# Usage tracking service dependency
async def get_usage_service():
    """Dependency for usage tracking service"""
    from ..services.usage_service import AsyncUsageService
    return AsyncUsageService()

# AI service dependency
async def get_ai_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    cache_service = Depends(get_cache_service)
):
    """Dependency for AI service"""
    from ..services.ai_service import AsyncAIService
    return AsyncAIService(http_client, cache_service)

# Stock service dependency
async def get_stock_service(
    cache_service = Depends(get_cache_service)
):
    """Dependency for stock service"""
    from ..services.stock_service import AsyncStockService
    return AsyncStockService(cache_service) 