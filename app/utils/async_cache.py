"""
Async cache utilities
"""
import asyncio
import hashlib
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

def async_cache(ttl: int = 300, key_prefix: str = ""):
    """Async cache decorator for function responses"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = str(args) + str(sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Get cache service from kwargs or create default
            cache_service = kwargs.get('cache_service')
            
            if cache_service:
                # Try to get from cache
                cached_result = await cache_service.get(cache_key)
                if cached_result is not None:
                    logger.info(f"Cache hit for {func.__name__}")
                    return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result if cache service available
            if cache_service:
                await cache_service.set(cache_key, result, ttl)
                logger.info(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

class AsyncCacheKey:
    """Helper for generating cache keys"""
    
    @staticmethod
    def generate(*args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    def with_prefix(prefix: str, *args, **kwargs) -> str:
        """Generate a cache key with prefix"""
        return f"{prefix}:{AsyncCacheKey.generate(*args, **kwargs)}"

class AsyncCacheManager:
    """Async cache manager utility"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
    
    async def get_or_set(self, key: str, getter_func: Callable, ttl: int = 300):
        """Get from cache or set using getter function"""
        # Try to get from cache
        cached_value = await self.cache_service.get(key)
        if cached_value is not None:
            return cached_value
        
        # Execute getter function
        value = await getter_func()
        
        # Cache the result
        await self.cache_service.set(key, value, ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if hasattr(self.cache_service, 'redis_client') and self.cache_service.redis_client:
            # This would require Redis SCAN command implementation
            logger.info(f"Invalidating cache pattern: {pattern}")
            # Placeholder for pattern invalidation 