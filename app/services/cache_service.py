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
        try:
            key_payload = {
                "args": [repr(arg) for arg in args],
                "kwargs": {key: repr(kwargs[key]) for key in sorted(kwargs.keys())}
            }
            serialized = json.dumps(key_payload, sort_keys=True, separators=(",", ":"))
        except Exception:
            # Fallback to non-JSON deterministic representation
            serialized = repr((tuple(repr(a) for a in args), tuple(sorted((k, repr(v)) for k, v in kwargs.items()))))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    
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
            # Determine cache service if present
            cache_service = getattr(wrapper, "cache_service", None)

            # Build deterministic cache key
            try:
                key_payload = {
                    "args": [repr(arg) for arg in args],
                    "kwargs": {key: repr(kwargs[key]) for key in sorted(kwargs.keys())}
                }
                serialized = json.dumps(key_payload, sort_keys=True, separators=(",", ":"))
            except Exception:
                serialized = repr((tuple(repr(a) for a in args), tuple(sorted((k, repr(v)) for k, v in kwargs.items()))))
            cache_key_suffix = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            cache_key = f"{key_prefix}:{func.__name__}:{cache_key_suffix}"

            # If no cache service configured, just execute function
            if not cache_service:
                return await func(*args, **kwargs)

            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and store in cache
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl or cache_service.default_ttl)
            return result
        
        # Add cache service attribute
        wrapper.cache_service = None
        return wrapper
    return decorator 