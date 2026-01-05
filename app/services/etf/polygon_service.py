"""
ETF Polygon.io API Service
Service for fetching ETF data from Polygon.io
"""
import os
import time
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import httpx
from functools import wraps

try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    RESTClient = None
    POLYGON_AVAILABLE = False

from app.models.etf_models import (
    ETFBasicInfo, ETFPriceData
)

logger = logging.getLogger(__name__)


class PolygonAPIError(Exception):
    """Custom exception for Polygon API errors"""
    pass


def retry_with_backoff(max_retries: int = 5, base_delay: float = 2.0):
    """Decorator for retrying API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e
                    
                    if e.response.status_code == 429:
                        if attempt == max_retries:
                            break
                        delay = base_delay * (2 ** attempt) + 3
                        logger.warning(f"Rate limited (429) - attempt {attempt + 1}, waiting {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    
                    if attempt == max_retries:
                        break
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"HTTP error {e.response.status_code} (attempt {attempt + 1}), retrying in {delay}s")
                    await asyncio.sleep(delay)
                    
                except httpx.RequestError as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Request error (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class ETFPolygonService:
    """Polygon service for ETF data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        self.client = None
        self.rest_client = None
        
        # Thread pool executor for running synchronous RESTClient calls
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Simple in-memory cache
        self.cache: Dict[str, tuple[float, Any]] = {}
        self.cache_ttl = 1800  # 30 minutes
        
        # Statistics
        self.api_calls = 0
        self.errors: List[str] = []
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum 100ms between requests
        
        if not self.api_key:
            logger.warning("POLYGON_API_KEY not set - Polygon service will not be available")
            return
        
        if not POLYGON_AVAILABLE:
            logger.warning("polygon-api-client package not installed - Polygon service will not be available")
            logger.warning("Install with: pip install polygon-api-client")
            return
        
        # Initialize Polygon RESTClient
        try:
            self.rest_client = RESTClient(self.api_key)
            logger.info("Polygon RESTClient initialized successfully for ETF service")
        except Exception as e:
            logger.error(f"Failed to initialize Polygon RESTClient: {str(e)}")
            self.rest_client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if k != "apikey")
        return f"{endpoint}?{param_str}"
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        if cache_key in self.cache:
            timestamp, data = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_data(self, cache_key: str, data: Any):
        """Cache data with current timestamp"""
        self.cache[cache_key] = (time.time(), data)
    
    @retry_with_backoff()
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to Polygon API with caching and rate limiting"""
        if not self.api_key:
            raise PolygonAPIError("POLYGON_API_KEY is required but not set")
        
        if params is None:
            params = {}
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {endpoint}")
            return cached_data
        
        try:
            client = await self._get_client()
            params['apikey'] = self.api_key
            url = f"{self.base_url}{endpoint}"
            
            logger.debug(f"Making API request to: {endpoint}")
            
            response = await client.get(url, params=params)
            
            if response.status_code == 401:
                raise PolygonAPIError("Invalid API key")
            elif response.status_code == 403:
                raise PolygonAPIError("API access forbidden")
            elif response.status_code == 429:
                raise PolygonAPIError("Rate limit exceeded")
            
            response.raise_for_status()
            
            self.api_calls += 1
            result = response.json()
            
            # Cache successful response
            self._cache_data(cache_key, result)
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error for {endpoint}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            raise PolygonAPIError(error_msg) from e
        except httpx.RequestError as e:
            error_msg = f"Request error for {endpoint}: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            raise PolygonAPIError(error_msg) from e
        except Exception as e:
            error_msg = f"API error for {endpoint}: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            raise
    
    async def get_etf_basic_info(self, symbol: str) -> Optional[ETFBasicInfo]:
        """Get basic ETF information"""
        if not self.rest_client:
            return None
        
        try:
            def fetch_ticker_details():
                try:
                    return self.rest_client.get_ticker_details(symbol.upper())
                except Exception as e:
                    logger.error(f"Error fetching ticker details: {str(e)}")
                    return None
            
            loop = asyncio.get_event_loop()
            ticker_details = await loop.run_in_executor(self.executor, fetch_ticker_details)
            
            if not ticker_details:
                return None
            
            # Get snapshot for current price (real-time data)
            def fetch_snapshot():
                try:
                    snapshot = self.rest_client.get_snapshot_ticker(symbol.upper())
                    return snapshot
                except Exception as e:
                    logger.debug(f"Could not fetch snapshot: {str(e)}")
                    return None
            
            snapshot = await loop.run_in_executor(self.executor, fetch_snapshot)
            
            # Extract data from ticker_details
            details = ticker_details.results if hasattr(ticker_details, 'results') else ticker_details
            
            current_price = None
            previous_close = None
            day_change = None
            day_change_percent = None
            volume = None
            
            # Get real-time data from snapshot
            if snapshot:
                # Try to get latest quote (real-time)
                if hasattr(snapshot, 'last_quote'):
                    quote = snapshot.last_quote
                    if quote:
                        current_price = float(quote.last_ask_price) if hasattr(quote, 'last_ask_price') and quote.last_ask_price else None
                        if not current_price:
                            current_price = float(quote.last_bid_price) if hasattr(quote, 'last_bid_price') and quote.last_bid_price else None
                
                # Get day data for previous close and volume
                if hasattr(snapshot, 'day'):
                    day_data = snapshot.day
                    if day_data:
                        if not current_price:
                            current_price = float(day_data.close) if hasattr(day_data, 'close') and day_data.close else None
                        previous_close = float(day_data.open) if hasattr(day_data, 'open') and day_data.open else None
                        volume = int(day_data.volume) if hasattr(day_data, 'volume') and day_data.volume else None
                        
                        # If we have previous close but not current price, use close as current
                        if previous_close and not current_price:
                            current_price = float(day_data.close) if hasattr(day_data, 'close') and day_data.close else previous_close
                        
                        if current_price and previous_close:
                            day_change = current_price - previous_close
                            day_change_percent = (day_change / previous_close * 100) if previous_close > 0 else None
                
                # Also try previous_day for previous close
                if not previous_close and hasattr(snapshot, 'prev_day'):
                    prev_day = snapshot.prev_day
                    if prev_day and hasattr(prev_day, 'close'):
                        previous_close = float(prev_day.close)
                        if current_price and previous_close:
                            day_change = current_price - previous_close
                            day_change_percent = (day_change / previous_close * 100) if previous_close > 0 else None
            
            # Extract basic info
            name = getattr(details, 'name', None) or getattr(details, 'title', None) or symbol
            description = getattr(details, 'description', None)
            
            return ETFBasicInfo(
                symbol=symbol.upper(),
                name=name,
                description=description,
                current_price=current_price,
                previous_close=previous_close,
                day_change=day_change,
                day_change_percent=day_change_percent,
                volume=volume,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting ETF basic info for {symbol}: {str(e)}")
            return None
    
    async def get_etf_daily_bars(self, symbol: str, start_date: str, end_date: str) -> List[ETFPriceData]:
        """Get daily bars for ETF using Polygon RESTClient"""
        if not self.rest_client:
            return []
        
        try:
            def fetch_aggs():
                aggs = []
                try:
                    for agg in self.rest_client.list_aggs(
                        symbol.upper(),
                        1,  # multiplier
                        "day",  # timespan
                        start_date,
                        end_date,
                        adjusted="true",
                        sort="asc",
                        limit=5000
                    ):
                        aggs.append(agg)
                    return aggs
                except Exception as e:
                    logger.error(f"Error in RESTClient.list_aggs for {symbol}: {str(e)}")
                    return []
            
            loop = asyncio.get_event_loop()
            aggs = await loop.run_in_executor(self.executor, fetch_aggs)
            
            logger.info(f"Retrieved {len(aggs)} aggregates for {symbol}")
            
            bars = []
            for agg in aggs:
                try:
                    bar_date = datetime.fromtimestamp(agg.timestamp / 1000).date()
                    
                    # Extract and validate price data
                    open_price = float(agg.open) if hasattr(agg, 'open') and agg.open else None
                    high_price = float(agg.high) if hasattr(agg, 'high') and agg.high else None
                    low_price = float(agg.low) if hasattr(agg, 'low') and agg.low else None
                    close_price = float(agg.close) if hasattr(agg, 'close') and agg.close else None
                    
                    # Validate and clean data
                    if not all([open_price, high_price, low_price, close_price]):
                        logger.debug(f"Skipping bar for {symbol} on {bar_date}: missing price data")
                        continue
                    
                    # Ensure high >= low, and both are within reasonable range of open/close
                    if high_price < low_price:
                        logger.warning(f"Invalid high/low for {symbol} on {bar_date}: high={high_price}, low={low_price}, swapping")
                        high_price, low_price = low_price, high_price
                    
                    # Ensure high >= max(open, close) and low <= min(open, close)
                    max_price = max(open_price, close_price)
                    min_price = min(open_price, close_price)
                    
                    if high_price < max_price:
                        logger.debug(f"Adjusting high for {symbol} on {bar_date}: {high_price} -> {max_price}")
                        high_price = max_price
                    
                    if low_price > min_price:
                        logger.debug(f"Adjusting low for {symbol} on {bar_date}: {low_price} -> {min_price}")
                        low_price = min_price
                    
                    # Check for unreasonable spreads (more than 20% daily range is suspicious)
                    price_range = high_price - low_price
                    avg_price = (open_price + close_price) / 2
                    spread_pct = (price_range / avg_price * 100) if avg_price > 0 else 0
                    
                    if spread_pct > 20:
                        logger.warning(f"Unusually large spread for {symbol} on {bar_date}: {spread_pct:.2f}% (high={high_price}, low={low_price})")
                        # Cap the spread to reasonable values
                        max_spread = avg_price * 0.10  # Max 10% spread
                        if price_range > max_spread:
                            center = (high_price + low_price) / 2
                            high_price = center + max_spread / 2
                            low_price = center - max_spread / 2
                            logger.info(f"Capped spread for {symbol} on {bar_date} to 10%")
                    
                    bar = ETFPriceData(
                        date=bar_date,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=int(agg.volume) if hasattr(agg, 'volume') and agg.volume else 0,
                        adjusted_close=close_price  # Adjusted close same as close for adjusted=true
                    )
                    
                    bars.append(bar)
                    
                except Exception as e:
                    logger.warning(f"Error parsing bar data: {str(e)}")
                    continue
            
            logger.info(f"Processed {len(bars)} daily bars for {symbol}")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching daily bars for {symbol}: {str(e)}")
            return []
    
    async def get_etf_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed ticker information"""
        if not self.rest_client:
            return None
        
        try:
            def fetch_details():
                try:
                    return self.rest_client.get_ticker_details(symbol.upper())
                except Exception as e:
                    logger.error(f"Error fetching ticker details: {str(e)}")
                    return None
            
            loop = asyncio.get_event_loop()
            details = await loop.run_in_executor(self.executor, fetch_details)
            
            if not details:
                return None
            
            # Convert to dict
            result = details.results if hasattr(details, 'results') else details
            
            return {
                'symbol': symbol.upper(),
                'name': getattr(result, 'name', None) or getattr(result, 'title', None),
                'description': getattr(result, 'description', None),
                'homepage_url': getattr(result, 'homepage_url', None),
                'total_employees': getattr(result, 'total_employees', None),
                'list_date': getattr(result, 'list_date', None),
                'market': getattr(result, 'market', None),
                'primary_exchange': getattr(result, 'primary_exchange', None),
            }
            
        except Exception as e:
            logger.error(f"Error getting ticker details for {symbol}: {str(e)}")
            return None
    
    async def get_etf_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time snapshot data"""
        if not self.rest_client:
            return None
        
        try:
            def fetch_snapshot():
                try:
                    return self.rest_client.get_snapshot_ticker(symbol.upper())
                except Exception as e:
                    logger.error(f"Error fetching snapshot: {str(e)}")
                    return None
            
            loop = asyncio.get_event_loop()
            snapshot = await loop.run_in_executor(self.executor, fetch_snapshot)
            
            if not snapshot:
                return None
            
            result = {}
            
            if hasattr(snapshot, 'day'):
                day_data = snapshot.day
                if day_data:
                    result['current_price'] = float(day_data.close) if hasattr(day_data, 'close') else None
                    result['open'] = float(day_data.open) if hasattr(day_data, 'open') else None
                    result['high'] = float(day_data.high) if hasattr(day_data, 'high') else None
                    result['low'] = float(day_data.low) if hasattr(day_data, 'low') else None
                    result['volume'] = int(day_data.volume) if hasattr(day_data, 'volume') else None
                    result['vwap'] = float(day_data.vwap) if hasattr(day_data, 'vwap') else None
            
            if hasattr(snapshot, 'prev_day'):
                prev_day = snapshot.prev_day
                if prev_day:
                    result['previous_close'] = float(prev_day.close) if hasattr(prev_day, 'close') else None
            
            if hasattr(snapshot, 'min'):
                min_data = snapshot.min
                if min_data:
                    result['min_open'] = float(min_data.open) if hasattr(min_data, 'open') else None
                    result['min_close'] = float(min_data.close) if hasattr(min_data, 'close') else None
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting snapshot for {symbol}: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client and executor"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
        if self.executor:
            self.executor.shutdown(wait=True)
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get service diagnostics"""
        return {
            "api_calls": self.api_calls,
            "errors": self.errors[-10:],
            "cache_size": len(self.cache),
            "has_api_key": bool(self.api_key),
            "rest_client_available": self.rest_client is not None
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()

