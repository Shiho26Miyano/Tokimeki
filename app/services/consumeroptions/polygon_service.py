"""
Unified Consumer Options Polygon API Service
Streamlined service for fetching options data from Polygon.io
"""
import os
import time
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import httpx
from functools import wraps

from app.models.options_models import (
    OptionContract, UnderlyingData, ContractBars, ContractType
)

logger = logging.getLogger(__name__)


class PolygonAPIError(Exception):
    """Custom exception for Polygon API errors"""
    pass


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
            
            raise last_exception
        
        return wrapper
    return decorator


class ConsumerOptionsPolygonService:
    """Unified Polygon service for Consumer Options data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        self.client = None
        
        # Simple in-memory cache
        self.cache: Dict[str, tuple[float, Any]] = {}
        self.cache_ttl = 300  # 5 minutes default
        
        # Statistics
        self.api_calls = 0
        self.errors: List[str] = []
        
        if not self.api_key:
            logger.warning("POLYGON_API_KEY not set - will use mock data")
    
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
        """Make HTTP request to Polygon API with caching and error handling"""
        if params is None:
            params = {}
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {endpoint}")
            return cached_data
        
        # If no API key, return mock data
        if not self.api_key:
            logger.info(f"No API key - generating mock data for {endpoint}")
            mock_data = self._generate_mock_response(endpoint, params)
            self._cache_data(cache_key, mock_data)
            return mock_data
        
        try:
            client = await self._get_client()
            params['apikey'] = self.api_key
            url = f"{self.base_url}{endpoint}"
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            self.api_calls += 1
            result = response.json()
            
            # Cache successful response
            self._cache_data(cache_key, result)
            
            logger.debug(f"API call successful: {endpoint}")
            return result
            
        except Exception as e:
            error_msg = f"API error for {endpoint}: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            
            # Return mock data on error
            mock_data = self._generate_mock_response(endpoint, params)
            self._cache_data(cache_key, mock_data)
            return mock_data
    
    def _generate_mock_response(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response based on endpoint"""
        if "/v3/snapshot/options/" in endpoint:
            underlying = endpoint.split("/")[-1].upper()
            return self._mock_option_chain_response(underlying)
        elif "/v2/aggs/ticker/" in endpoint and "/day/" in endpoint:
            ticker = endpoint.split("/")[4].upper()
            return self._mock_daily_bars_response(ticker, params)
        elif "/v2/aggs/t/" in endpoint and "/minute/" in endpoint:
            return self._mock_minute_bars_response()
        elif "/v1/indicators/rsi/" in endpoint:
            return {"results": {"values": [{"value": 45.5}]}}
        else:
            return {"results": []}
    
    def _mock_option_chain_response(self, underlying: str) -> Dict[str, Any]:
        """Generate realistic mock option chain data"""
        import random
        
        base_price = {"COST": 900, "WMT": 180, "TGT": 150, "AMZN": 180, "AAPL": 220}.get(underlying, 200)
        contracts = []
        
        # Generate contracts for next 8 expiries (more realistic options chain)
        for weeks_out in [1, 2, 3, 4, 6, 8, 12, 16]:
            expiry = date.today() + timedelta(weeks=weeks_out)
            expiry_str = expiry.strftime("%Y-%m-%d")
            
            # Generate strikes around current price (more strikes for better heatmap)
            for i in range(-8, 9):
                strike = base_price + (i * 10)
                
                for contract_type in ["call", "put"]:
                    # Generate realistic Greeks
                    moneyness = strike / base_price
                    time_factor = weeks_out / 4.0
                    
                    if contract_type == "call":
                        delta = max(0.05, min(0.95, 0.5 + (base_price - strike) / base_price * 2))
                        contract_symbol = f"O:{underlying}{expiry.strftime('%y%m%d')}C{int(strike * 1000):08d}"
                    else:
                        delta = max(-0.95, min(-0.05, -0.5 + (strike - base_price) / base_price * 2))
                        contract_symbol = f"O:{underlying}{expiry.strftime('%y%m%d')}P{int(strike * 1000):08d}"
                    
                    iv = 0.20 + random.uniform(-0.05, 0.10) + (abs(moneyness - 1) * 0.1)
                    gamma = 0.02 * (1 - abs(moneyness - 1)) * time_factor
                    theta = -0.05 * time_factor
                    vega = 0.15 * time_factor
                    
                    volume = random.randint(50, 2000) if random.random() > 0.3 else 0
                    oi = random.randint(100, 5000) if random.random() > 0.2 else 0
                    last_price = max(0.01, abs(delta) * base_price * 0.1 + random.uniform(-5, 5))
                    
                    contract_data = {
                        "contract": contract_symbol,
                        "details": {
                            "contract_type": contract_type,
                            "strike_price": strike,
                            "expiration_date": expiry_str
                        },
                        "day": {
                            "volume": volume,
                            "open_interest": oi
                        },
                        "last_quote": {
                            "p": round(last_price, 2),
                            "b": round(last_price * 0.98, 2),
                            "a": round(last_price * 1.02, 2)
                        },
                        "implied_volatility": round(iv, 4),
                        "greeks": {
                            "delta": round(delta, 4),
                            "gamma": round(gamma, 4),
                            "theta": round(theta, 4),
                            "vega": round(vega, 4)
                        }
                    }
                    contracts.append(contract_data)
        
        return {"results": contracts}
    
    def _mock_daily_bars_response(self, ticker: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock daily bars data"""
        import random
        
        # Generate 60 days of data
        bars = []
        base_price = {"COST": 900, "WMT": 180, "TGT": 150, "AMZN": 180, "AAPL": 220}.get(ticker, 200)
        current_price = base_price
        
        for i in range(60):
            bar_date = date.today() - timedelta(days=60-i)
            
            # Skip weekends
            if bar_date.weekday() < 5:
                # Generate realistic price movement
                change_pct = random.uniform(-0.03, 0.03)
                current_price *= (1 + change_pct)
                
                daily_range = current_price * 0.02
                open_price = current_price + random.uniform(-daily_range/2, daily_range/2)
                close_price = current_price + random.uniform(-daily_range/2, daily_range/2)
                high_price = max(open_price, close_price) + random.uniform(0, daily_range/2)
                low_price = min(open_price, close_price) - random.uniform(0, daily_range/2)
                
                volume = random.randint(1000000, 5000000)
                timestamp = int(bar_date.strftime("%s")) * 1000
                
                bar_data = {
                    "t": timestamp,
                    "o": round(open_price, 2),
                    "h": round(high_price, 2),
                    "l": round(low_price, 2),
                    "c": round(close_price, 2),
                    "v": volume
                }
                bars.append(bar_data)
        
        return {"results": bars}
    
    def _mock_minute_bars_response(self) -> Dict[str, Any]:
        """Generate mock minute bars data"""
        import random
        
        bars = []
        base_price = 10.0
        
        for i in range(100):
            timestamp = int((datetime.now() - timedelta(minutes=100-i)).timestamp() * 1000)
            change = random.uniform(-0.1, 0.1)
            base_price *= (1 + change)
            
            bar_data = {
                "t": timestamp,
                "o": round(base_price, 2),
                "h": round(base_price * 1.02, 2),
                "l": round(base_price * 0.98, 2),
                "c": round(base_price, 2),
                "v": random.randint(100, 1000)
            }
            bars.append(bar_data)
        
        return {"results": bars}
    
    async def get_option_chain_snapshot(self, underlying: str) -> List[OptionContract]:
        """Get option chain snapshot for underlying ticker"""
        endpoint = f"/v3/snapshot/options/{underlying.upper()}"
        
        try:
            data = await self._make_request(endpoint)
            contracts = []
            
            for contract_data in data.get("results", []):
                try:
                    # Extract contract details
                    details = contract_data.get("details", {})
                    day_data = contract_data.get("day", {}) or {}
                    greeks = contract_data.get("greeks", {}) or {}
                    last_quote = contract_data.get("last_quote", {}) or {}
                    
                    # Parse contract type
                    contract_type_raw = details.get("contract_type", "").lower()
                    contract_type = ContractType.CALL if contract_type_raw == "call" else ContractType.PUT
                    
                    # Parse expiry date
                    expiry_str = details.get("expiration_date")
                    expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date() if expiry_str else None
                    
                    if not expiry:
                        continue  # Skip contracts without valid expiry
                    
                    contract = OptionContract(
                        contract=contract_data.get("contract", ""),
                        underlying=underlying.upper(),
                        expiry=expiry,
                        strike=float(details.get("strike_price", 0)),
                        type=contract_type,
                        
                        # Market data
                        last_price=last_quote.get("p"),
                        bid=last_quote.get("b"),
                        ask=last_quote.get("a"),
                        
                        # Volume and OI
                        day_volume=day_data.get("volume"),
                        day_oi=day_data.get("open_interest"),
                        
                        # Greeks and IV - check multiple possible locations
                        implied_volatility=(
                            contract_data.get("implied_volatility") or 
                            greeks.get("implied_volatility") or
                            contract_data.get("iv")
                        ),
                        delta=greeks.get("delta"),
                        gamma=greeks.get("gamma"),
                        theta=greeks.get("theta"),
                        vega=greeks.get("vega")
                    )
                    
                    contracts.append(contract)
                    
                except Exception as e:
                    logger.warning(f"Error parsing contract data: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(contracts)} contracts for {underlying}")
            return contracts
            
        except Exception as e:
            logger.error(f"Error fetching option chain for {underlying}: {str(e)}")
            raise PolygonAPIError(f"Failed to fetch option chain: {str(e)}")
    
    async def get_underlying_daily_bars(self, ticker: str, start_date: str, end_date: str) -> List[UnderlyingData]:
        """Get daily bars for underlying stock"""
        endpoint = f"/v2/aggs/ticker/{ticker.upper()}/range/1/day/{start_date}/{end_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 5000
        }
        
        try:
            data = await self._make_request(endpoint, params)
            bars = []
            
            for bar_data in data.get("results", []):
                try:
                    # Convert timestamp to date
                    timestamp = bar_data.get("t", 0)
                    bar_date = datetime.fromtimestamp(timestamp / 1000).date()
                    
                    bar = UnderlyingData(
                        ticker=ticker.upper(),
                        bar_date=bar_date,
                        open=float(bar_data.get("o", 0)),
                        high=float(bar_data.get("h", 0)),
                        low=float(bar_data.get("l", 0)),
                        close=float(bar_data.get("c", 0)),
                        volume=int(bar_data.get("v", 0))
                    )
                    
                    bars.append(bar)
                    
                except Exception as e:
                    logger.warning(f"Error parsing bar data: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(bars)} daily bars for {ticker}")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching daily bars for {ticker}: {str(e)}")
            raise PolygonAPIError(f"Failed to fetch daily bars: {str(e)}")
    
    async def get_contract_minute_bars(self, contract: str, start_date: str, end_date: str) -> List[ContractBars]:
        """Get 1-minute bars for specific option contract"""
        endpoint = f"/v2/aggs/t/{contract}/range/1/minute/{start_date}/{end_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000
        }
        
        try:
            data = await self._make_request(endpoint, params)
            bars = []
            
            for bar_data in data.get("results", []):
                try:
                    # Convert timestamp to datetime
                    timestamp = bar_data.get("t", 0)
                    bar_time = datetime.fromtimestamp(timestamp / 1000)
                    
                    bar = ContractBars(
                        contract=contract,
                        timestamp=bar_time,
                        open=float(bar_data.get("o", 0)),
                        high=float(bar_data.get("h", 0)),
                        low=float(bar_data.get("l", 0)),
                        close=float(bar_data.get("c", 0)),
                        volume=int(bar_data.get("v", 0))
                    )
                    
                    bars.append(bar)
                    
                except Exception as e:
                    logger.warning(f"Error parsing contract bar data: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(bars)} minute bars for {contract}")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching minute bars for {contract}: {str(e)}")
            raise PolygonAPIError(f"Failed to fetch minute bars: {str(e)}")
    
    async def get_underlying_rsi(self, ticker: str, window: int = 14) -> Optional[float]:
        """Get RSI indicator for underlying stock"""
        endpoint = f"/v1/indicators/rsi/{ticker.upper()}"
        params = {
            "timespan": "day",
            "window": window
        }
        
        try:
            data = await self._make_request(endpoint, params)
            
            # Get the latest RSI value
            results = data.get("results", {})
            values = results.get("values", [])
            
            if values:
                latest = values[-1]
                return latest.get("value")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching RSI for {ticker}: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get service diagnostics"""
        return {
            "api_calls": self.api_calls,
            "errors": self.errors[-10:],  # Last 10 errors
            "cache_size": len(self.cache),
            "has_api_key": bool(self.api_key)
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()