from fastapi import Depends
from typing import AsyncGenerator
import httpx
import redis.asyncio as redis
from .config import settings

# Global HTTP client variable
_http_client = None

async def get_http_client() -> httpx.AsyncClient:
    """Dependency for HTTP client with persistent connection pooling and increased timeouts"""
    global _http_client
    
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=50,
                max_connections=200,
                keepalive_expiry=60.0
            ),
            timeout=httpx.Timeout(
                connect=15.0,   # Increased from 10.0 to 15.0 seconds
                read=60.0,      # Increased from 40.0 to 60.0 seconds
                write=15.0,     # Increased from 10.0 to 15.0 seconds
                pool=30.0       # Added pool timeout
            ),
            http2=True,  # Enabled for better performance
            follow_redirects=True
        )
    
    return _http_client

async def cleanup_http_client():
    """Cleanup HTTP client on shutdown"""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None

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

# Stock service dependency
async def get_stock_service(
    cache_service = Depends(get_cache_service)
):
    """Dependency for stock service"""
    from ..services.stock_service import AsyncStockService
    return AsyncStockService(cache_service)

# AI service dependency
async def get_ai_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    cache_service = Depends(get_cache_service),
    stock_service = Depends(get_stock_service)
):
    """Dependency for AI service"""
    from ..services.ai_service import AsyncAIService
    return AsyncAIService(http_client, cache_service, stock_service) 

# Portfolio service dependency
async def get_portfolio_service():
    """Dependency for portfolio service"""
    from ..services.portfolio_service import PortfolioService
    return PortfolioService()

# RAG service singleton dependency
_rag_service_singleton = None

async def get_rag_service(
    ai_service = Depends(get_ai_service)
):
    """Provide a singleton AsyncRAGService so ingested corpora persist across requests."""
    global _rag_service_singleton
    if _rag_service_singleton is None:
        from ..services.rag_service import AsyncRAGService
        _rag_service_singleton = AsyncRAGService(ai_service)
    return _rag_service_singleton