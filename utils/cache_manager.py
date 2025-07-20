import redis
import os
import json
import logging
import hashlib
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = False
        self.default_ttl = 300  # 5 minutes default
        
        # Try to initialize Redis
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
                self.cache_enabled = True
                logger.info("Redis cache initialized successfully")
            else:
                logger.warning("REDIS_URL not set, cache disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
            self.cache_enabled = False
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments"""
        # Create a string representation of all arguments
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False

# Global cache manager instance
cache_manager = CacheManager()

def cached_response(ttl: int = None, key_prefix: str = ""):
    """Decorator to cache API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{cache_manager.generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Only cache successful responses
            if result and not result.get('error'):
                cache_manager.set(cache_key, result, ttl)
                logger.info(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator 