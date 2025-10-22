"""
Polygon API service with caching, retries, and diagnostics
"""
import asyncio
import json
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import httpx
import logging
from functools import wraps

from ...models.aapl_analysis_models import (
    OHLCData, StockPriceResponse, OptionContract, OptionChainResponse,
    OptionOHLCResponse, OptionType, DataDiagnostics, PolygonConfig
)

logger = logging.getLogger(__name__)


class PolygonAPIError(Exception):
    """Custom exception for Polygon API errors"""
    pass


class CacheManager:
    """In-memory cache manager with TTL support"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        return time.time() > entry['expires_at']
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_oldest(self):
        """Evict oldest entries if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove 10% of oldest entries
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['created_at']
            )
            to_remove = len(sorted_items) // 10 + 1
            for key, _ in sorted_items[:to_remove]:
                del self.cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self._cleanup_expired()
        
        if key in self.cache and not self._is_expired(self.cache[key]):
            self.hits += 1
            return self.cache[key]['data']
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        self._evict_oldest()
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'data': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'size': len(self.cache)
        }


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
            
            raise PolygonAPIError(f"API call failed after {max_retries + 1} attempts: {last_exception}")
        
        return wrapper
    return decorator


class PolygonService:
    """Service for interacting with Polygon API"""
    
    def __init__(self, config: PolygonConfig):
        self.config = config
        self.cache = CacheManager()
        self.client = None
        self.api_calls = 0
        self.total_latency = 0.0
        self.errors: List[str] = []
    
    async def _ensure_client(self):
        """Ensure HTTP client is available and not closed"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    async def __aenter__(self):
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    async def close(self):
        """Explicitly close the HTTP client"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"
    
    @retry_with_backoff()
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Polygon API"""
        start_time = time.time()
        
        try:
            # Ensure client is available
            await self._ensure_client()
            
            params['apikey'] = self.config.api_key
            url = f"{self.config.base_url}{endpoint}"
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            self.api_calls += 1
            self.total_latency += latency
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            self.errors.append(error_msg)
            raise PolygonAPIError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            self.errors.append(error_msg)
            raise PolygonAPIError(error_msg)
    
    async def get_stock_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        multiplier: int = 1,
        timespan: str = "day"
    ) -> StockPriceResponse:
        """Get stock OHLC data from Polygon"""
        # Check if using mock data
        if self.config.api_key == "mock_key":
            return self._generate_mock_stock_data(ticker, start_date, end_date)
        
        cache_key = self._get_cache_key(
            f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}",
            {
                'from': start_date.isoformat(),
                'to': end_date.isoformat(),
                'adjusted': 'true',
                'sort': 'asc'
            }
        )
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return StockPriceResponse(**cached_data)
        
        # Make API request
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        response_data = await self._make_request(endpoint, params)
        
        if response_data.get('status') not in ['OK', 'DELAYED']:
            raise PolygonAPIError(f"API returned status: {response_data.get('status')}")
        
        # Parse response
        ohlc_data = []
        for result in response_data.get('results', []):
            ohlc_data.append(OHLCData(
                timestamp=datetime.fromtimestamp(result['t'] / 1000),
                open=result['o'],
                high=result['h'],
                low=result['l'],
                close=result['c'],
                volume=result['v']
            ))
        
        stock_response = StockPriceResponse(
            ticker=ticker,
            data=ohlc_data,
            count=len(ohlc_data),
            from_date=start_date,
            to_date=end_date
        )
        
        # Cache the response
        self.cache.set(cache_key, stock_response.dict())
        
        return stock_response
    
    async def get_option_contracts(
        self,
        ticker: str,
        expiration_date: date,
        underlying_price: Optional[float] = None
    ) -> OptionChainResponse:
        """Get option contracts for a specific expiration date"""
        cache_key = self._get_cache_key(
            f"/v3/reference/options/contracts",
            {
                'underlying_ticker': ticker,
                'expiration_date': expiration_date.isoformat(),
                'limit': 1000
            }
        )
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return OptionChainResponse(**cached_data)
        
        # Make API request
        endpoint = "/v3/reference/options/contracts"
        params = {
            'underlying_ticker': ticker,
            'expiration_date': expiration_date.isoformat(),
            'limit': 1000,
            'sort': 'strike_price'
        }
        
        response_data = await self._make_request(endpoint, params)
        
        if response_data.get('status') not in ['OK', 'DELAYED']:
            raise PolygonAPIError(f"API returned status: {response_data.get('status')}")
        
        # Parse contracts
        calls = []
        puts = []
        
        for contract in response_data.get('results', []):
            days_to_expiry = (expiration_date - date.today()).days
            
            option_contract = OptionContract(
                ticker=contract['ticker'],
                underlying_ticker=contract['underlying_ticker'],
                option_type=OptionType.CALL if contract['contract_type'] == 'call' else OptionType.PUT,
                strike_price=contract['strike_price'],
                expiration_date=datetime.strptime(contract['expiration_date'], '%Y-%m-%d').date(),
                days_to_expiry=days_to_expiry
            )
            
            if option_contract.option_type == OptionType.CALL:
                calls.append(option_contract)
            else:
                puts.append(option_contract)
        
        # Get current underlying price if not provided
        if underlying_price is None:
            try:
                today = date.today()
                yesterday = today - timedelta(days=1)
                price_data = await self.get_stock_prices(ticker, yesterday, today)
                if price_data.data:
                    underlying_price = price_data.data[-1].close
                else:
                    underlying_price = 0.0
            except Exception:
                underlying_price = 0.0
        
        option_chain = OptionChainResponse(
            underlying_ticker=ticker,
            expiration_date=expiration_date,
            underlying_price=underlying_price,
            calls=calls,
            puts=puts,
            count=len(calls) + len(puts)
        )
        
        # Cache the response
        self.cache.set(cache_key, option_chain.dict())
        
        return option_chain
    
    async def get_option_ohlc(
        self,
        option_ticker: str,
        start_date: date,
        end_date: date
    ) -> OptionOHLCResponse:
        """Get OHLC data for a specific option contract"""
        cache_key = self._get_cache_key(
            f"/v2/aggs/ticker/{option_ticker}/range/1/day",
            {
                'from': start_date.isoformat(),
                'to': end_date.isoformat()
            }
        )
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return OptionOHLCResponse(**cached_data)
        
        # Make API request
        endpoint = f"/v2/aggs/ticker/{option_ticker}/range/1/day/{start_date}/{end_date}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        response_data = await self._make_request(endpoint, params)
        
        if response_data.get('status') not in ['OK', 'DELAYED']:
            raise PolygonAPIError(f"API returned status: {response_data.get('status')}")
        
        # Parse OHLC data
        ohlc_data = []
        for result in response_data.get('results', []):
            ohlc_data.append(OHLCData(
                timestamp=datetime.fromtimestamp(result['t'] / 1000),
                open=result['o'],
                high=result['h'],
                low=result['l'],
                close=result['c'],
                volume=result['v']
            ))
        
        # Create a dummy contract details (would need separate API call for full details)
        contract_details = OptionContract(
            ticker=option_ticker,
            underlying_ticker="AAPL",  # Hardcoded for now
            option_type=OptionType.CALL if 'C' in option_ticker else OptionType.PUT,
            strike_price=0.0,  # Would need to parse from ticker
            expiration_date=date.today(),  # Would need to parse from ticker
            days_to_expiry=0
        )
        
        option_ohlc = OptionOHLCResponse(
            option_ticker=option_ticker,
            underlying_ticker="AAPL",
            data=ohlc_data,
            count=len(ohlc_data),
            contract_details=contract_details
        )
        
        # Cache the response
        self.cache.set(cache_key, option_ohlc.dict())
        
        return option_ohlc
    
    def get_diagnostics(self) -> DataDiagnostics:
        """Get diagnostics information"""
        cache_stats = self.cache.get_stats()
        avg_latency = self.total_latency / max(self.api_calls, 1)
        
        return DataDiagnostics(
            polygon_api_calls=self.api_calls,
            polygon_avg_latency_ms=avg_latency,
            cache_hits=cache_stats['hits'],
            cache_misses=cache_stats['misses'],
            missing_stock_data_days=0,  # Would be calculated during backtest
            missing_option_contracts=0,  # Would be calculated during backtest
            missing_option_exit_data=0,  # Would be calculated during backtest
            partial_data_warnings=[],
            api_errors=self.errors.copy()
        )
    
    def _generate_mock_stock_data(self, ticker: str, start_date: date, end_date: date) -> StockPriceResponse:
        """Generate mock stock data for demonstration purposes"""
        import random
        from datetime import timedelta
        
        # Set seed for consistent mock data
        random.seed(42)
        
        # Generate realistic AAPL-like data
        base_price = 150.0 if ticker.upper() == "AAPL" else 100.0
        current_price = base_price
        ohlc_data = []
        
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                # Generate realistic price movement
                daily_change = random.uniform(-0.05, 0.05)  # ±5% daily change
                current_price *= (1 + daily_change)
                
                # Generate OHLC data
                open_price = current_price * random.uniform(0.98, 1.02)
                high_price = max(open_price, current_price) * random.uniform(1.0, 1.03)
                low_price = min(open_price, current_price) * random.uniform(0.97, 1.0)
                close_price = current_price
                volume = random.randint(1000000, 10000000)
                
                ohlc_data.append(OHLCData(
                    timestamp=datetime.combine(current_date, datetime.min.time()),
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=volume
                ))
            
            current_date += timedelta(days=1)
        
        return StockPriceResponse(
            ticker=ticker,
            data=ohlc_data,
            count=len(ohlc_data),
            from_date=start_date,
            to_date=end_date
        )
