import redis
import json
import hashlib
import time
import os
from functools import wraps
from typing import Optional, Any, Dict

class CacheManager:
    def __init__(self):
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.cache_enabled = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
        self.default_ttl = int(os.environ.get('CACHE_TTL', 300))  # 5 minutes default
        
        if self.cache_enabled:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                print("✅ Redis cache connected successfully")
            except Exception as e:
                print(f"⚠️ Redis cache not available: {e}")
                self.cache_enabled = False
                self.redis_client = None

    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments"""
        # Create a string representation of all arguments
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all cache entries"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

# Global cache instance
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
                print(f"✅ Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Only cache successful responses
            if result and not result.get('error'):
                cache_manager.set(cache_key, result, ttl)
                print(f"💾 Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator 