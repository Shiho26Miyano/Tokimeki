import json
import hashlib
import logging
from typing import Optional, Any
from functools import wraps
import redis.asyncio as redis
from ..core.config import settings

logger = logging.getLogger(__name__)

class AsyncCacheService:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.cache_enabled = settings.cache_enabled and redis_client is not None
        self.default_ttl = settings.cache_ttl
        
        if self.cache_enabled:
            logger.info("Async cache service initialized with Redis")
        else:
            logger.warning("Async cache service initialized without Redis")
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache asynchronously"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache asynchronously"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache asynchronously"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache asynchronously"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache asynchronously"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key)
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False
    
    async def is_redis_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection check failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Redis connection with a simple operation"""
        if not self.redis_client:
            return False
        
        try:
            # Test with a simple set/get operation
            test_key = "test_connection"
            test_value = "test"
            await self.redis_client.setex(test_key, 10, test_value)
            result = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            return result == test_value.encode()
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False

def async_cached_response(ttl: int = None, key_prefix: str = ""):
    """Async cache decorator for function responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(str(args) + str(kwargs).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await wrapper.cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await wrapper.cache_service.set(cache_key, result, ttl or wrapper.cache_service.default_ttl)
            
            return result
        
        # Add cache service attribute
        wrapper.cache_service = None
        return wrapper
    return decorator 