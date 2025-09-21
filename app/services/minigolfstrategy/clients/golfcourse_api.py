"""
Golf Course API Client
External API integration for golf course data
"""
import httpx
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class GolfCourseAPIClient:
    """Client for external golf course API"""
    
    def __init__(self):
        self.base_url = settings.golfcourse_api_base
        self.api_key = settings.golfcourse_api_key or ''
        self.timeout = 30.0  # Increased timeout for better reliability
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour cache TTL
    
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Create a hash of the endpoint and parameters
        cache_string = f"{endpoint}:{sorted(params.items())}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if not expired"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"Cache hit for key: {cache_key[:8]}...")
                return data
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                logger.info(f"Cache expired for key: {cache_key[:8]}...")
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store data in cache"""
        self.cache[cache_key] = (data, time.time())
        logger.info(f"Cached data for key: {cache_key[:8]}...")
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make API request with retry logic for rate limiting"""
        import asyncio
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, **kwargs)
                    else:
                        response = await client.request(method, url, **kwargs)
                    
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.HTTPError as e:
                if e.response and e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        # Exponential backoff for rate limiting
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        return {
                            "error": "GolfCourse API rate limit exceeded. Please try again in a few minutes.",
                            "retry_after": 300,  # 5 minutes
                            "status_code": 429
                        }
                else:
                    logger.error(f"HTTP error: {str(e)}")
                    return {"error": f"API request failed: {str(e)}"}
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return {"error": f"Unexpected error: {str(e)}"}
        
        return {"error": "Max retries exceeded"}
    
    async def search_courses(
        self, 
        query: str, 
        country: Optional[str] = None, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Search for golf courses"""
        try:
            params = {"search_query": query}
            if country:
                params["country"] = country
            
            # Check cache first
            cache_key = self._get_cache_key("search", params)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            headers = {}
            # Use Key authentication scheme
            if self.api_key:
                headers["Authorization"] = f"Key {self.api_key}"
            
            result = await self._make_request(
                "GET",
                f"{self.base_url}/v1/search",
                headers=headers,
                params=params
            )
            
            # Handle authentication errors specifically
            if "error" in result:
                if "401" in result["error"] or "authentication" in result["error"].lower():
                    return {"error": "GolfCourseAPI authentication failed. Please check your API key or register at https://www.golfcourseapi.com/sign-in"}
            
            # Cache successful results
            if "error" not in result:
                self._set_cache(cache_key, result)
            
            return result
                
        except Exception as e:
            logger.error(f"Error searching courses: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    
    async def get_course_details(self, course_id: str) -> Dict[str, Any]:
        """Get detailed course information"""
        try:
            headers = {}
            params = {}
            
            # Use Key authentication scheme
            if self.api_key:
                headers["Authorization"] = f"Key {self.api_key}"
            
            result = await self._make_request(
                "GET",
                f"{self.base_url}/v1/courses/{course_id}",
                headers=headers,
                params=params
            )
            
            # Handle authentication errors specifically
            if "error" in result:
                if "401" in result["error"] or "authentication" in result["error"].lower():
                    return {"error": "GolfCourseAPI authentication failed. Please check your API key or register at https://www.golfcourseapi.com/sign-in"}
            
            return result
                
        except Exception as e:
            logger.error(f"Error getting course details: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def get_courses_by_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 50
    ) -> Dict[str, Any]:
        """Get courses near a location"""
        try:
            headers = {"Authorization": f"Key {self.api_key}"} if self.api_key else {}
            params = {
                "lat": latitude,
                "lng": longitude,
                "radius": radius
            }
            
            result = await self._make_request(
                "GET",
                f"{self.base_url}/v1/courses/nearby",
                headers=headers,
                params=params
            )
            
            # Handle authentication errors specifically
            if "error" in result:
                if "401" in result["error"] or "authentication" in result["error"].lower():
                    return {"error": "GolfCourseAPI authentication failed. Please check your API key or register at https://www.golfcourseapi.com/sign-in"}
            
            return result
                
        except Exception as e:
            logger.error(f"Error getting nearby courses: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl
        }

# Global client instance
golf_course_client = GolfCourseAPIClient()
