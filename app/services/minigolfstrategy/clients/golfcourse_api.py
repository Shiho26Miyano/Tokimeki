"""
Golf Course API Client
External API integration for golf course data
"""
import httpx
import logging
import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class GolfCourseAPIClient:
    """Client for external golf course API with rate limiting and retry logic"""
    
    def __init__(self):
        self.base_url = settings.golfcourse_api_base
        self.api_key = settings.golfcourse_api_key or ''
        self.timeout = 20.0
        self.rate_limit_delay = 2.0  # 2 seconds between requests (conservative)
        self.max_retries = 5  # More retries for rate limits
        self.retry_delay = 10.0  # 10 seconds between retries
        self.last_request_time = 0
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.request_count = 0  # Track requests made
        self.daily_reset_time = time.time()  # Track when to reset daily count
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        
        # Reset daily counter if it's been more than 24 hours
        if current_time - self.daily_reset_time > 86400:  # 24 hours
            self.request_count = 0
            self.daily_reset_time = current_time
            logger.info("Daily request counter reset")
        
        # Check if we're approaching daily limit (conservative: 8000 out of 10000)
        if self.request_count >= 8000:
            logger.warning(f"Approaching daily limit: {self.request_count}/10000 requests used")
            # Wait until next day
            wait_time = 86400 - (current_time - self.daily_reset_time)
            if wait_time > 0:
                logger.warning(f"Daily limit reached. Waiting {wait_time/3600:.1f} hours until reset")
                await asyncio.sleep(min(wait_time, 3600))  # Max 1 hour wait
                return
        
        # Standard rate limiting between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
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
    
    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make API request with retry logic for rate limiting"""
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                await self._rate_limit()
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, **kwargs)
                    else:
                        response = await client.request(method, url, **kwargs)
                    
                    # Handle rate limiting specifically
                    if response.status_code == 429:
                        if attempt < self.max_retries:
                            # Progressive backoff: 10s, 30s, 60s, 120s, 300s
                            wait_time = min(self.retry_delay * (3 ** attempt), 300)
                            logger.warning(f"Rate limited (429). Retrying in {wait_time} seconds... (attempt {attempt + 1}/{self.max_retries + 1})")
                            logger.warning(f"Daily usage: {self.request_count}/10000 requests")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return {"error": "Rate limit exceeded after multiple retries. Please wait before making more requests."}
                    
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.HTTPError as e:
                if e.response and e.response.status_code == 429:
                    if attempt < self.max_retries:
                        wait_time = min(self.retry_delay * (3 ** attempt), 300)
                        logger.warning(f"Rate limited (429). Retrying in {wait_time} seconds... (attempt {attempt + 1}/{self.max_retries + 1})")
                        logger.warning(f"Daily usage: {self.request_count}/10000 requests")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return {"error": "Rate limit exceeded after multiple retries. Please wait before making more requests."}
                else:
                    logger.error(f"HTTP error: {str(e)}")
                    if attempt == self.max_retries:
                        return {"error": f"API request failed after {self.max_retries + 1} attempts: {str(e)}"}
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if attempt == self.max_retries:
                    return {"error": f"Unexpected error after {self.max_retries + 1} attempts: {str(e)}"}
                await asyncio.sleep(self.retry_delay)
        
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
            
            result = await self._make_request_with_retry(
                "GET",
                f"{self.base_url}/v1/search",
                headers=headers,
                params=params
            )
            
            # Handle authentication errors specifically
            if "error" in result and "Rate limit exceeded" not in result["error"]:
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
            
            result = await self._make_request_with_retry(
                "GET",
                f"{self.base_url}/v1/courses/{course_id}",
                headers=headers,
                params=params
            )
            
            # Handle authentication errors specifically
            if "error" in result and "Rate limit exceeded" not in result["error"]:
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
            
            result = await self._make_request_with_retry(
                "GET",
                f"{self.base_url}/v1/courses/nearby",
                headers=headers,
                params=params
            )
            
            # Handle authentication errors specifically
            if "error" in result and "Rate limit exceeded" not in result["error"]:
                if "401" in result["error"] or "authentication" in result["error"].lower():
                    return {"error": "GolfCourseAPI authentication failed. Please check your API key or register at https://www.golfcourseapi.com/sign-in"}
            
            return result
                
        except Exception as e:
            logger.error(f"Error getting nearby courses: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        current_time = time.time()
        time_since_reset = current_time - self.daily_reset_time
        hours_until_reset = max(0, (86400 - time_since_reset) / 3600)
        
        return {
            "requests_made": self.request_count,
            "daily_limit": 10000,
            "usage_percentage": (self.request_count / 10000) * 100,
            "hours_until_reset": hours_until_reset,
            "last_request_time": self.last_request_time,
            "cache_size": len(self.cache)
        }
    
    async def wait_for_rate_limit_reset(self) -> None:
        """Wait for rate limit to reset (useful for testing)"""
        logger.info("Waiting for rate limit to reset...")
        # Wait 1 hour to be safe
        await asyncio.sleep(3600)
        logger.info("Rate limit reset wait completed")

# Global client instance
golf_course_client = GolfCourseAPIClient()
