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


def retry_with_backoff(max_retries: int = 5, base_delay: float = 2.0):
    """Decorator for retrying API calls with exponential backoff, handling rate limits"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e
                    
                    # Handle rate limiting (429) with longer delays
                    if e.response.status_code == 429:
                        if attempt == max_retries:
                            break
                        
                        # Longer delay for rate limits: 5s, 10s, 20s, 40s, 80s
                        delay = base_delay * (2 ** attempt) + 3  # Extra 3 seconds for rate limits
                        logger.warning(f"Rate limited (429) - attempt {attempt + 1}, waiting {delay}s before retry")
                        await asyncio.sleep(delay)
                        continue
                    
                    # Handle other HTTP errors
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


class ConsumerOptionsPolygonService:
    """Unified Polygon service for Consumer Options data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        self.client = None
        
        # Simple in-memory cache with longer TTL to reduce API calls
        self.cache: Dict[str, tuple[float, Any]] = {}
        self.cache_ttl = 1800  # 30 minutes default (increased from 5 minutes)
        
        # Statistics
        self.api_calls = 0
        self.errors: List[str] = []
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum 100ms between requests
        
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY is required but not set")
        
        # Ensure we're not using mock data
        if self.api_key == "mock_key" or self.api_key.startswith("mock"):
            raise ValueError("Mock data is not allowed for Consumer Options. Please set a valid POLYGON_API_KEY")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if k != "apikey")
        return f"{endpoint}?{param_str}"
    
    def _validate_iv(self, iv_value) -> Optional[float]:
        """Validate and normalize implied volatility values"""
        if iv_value is None:
            return None
        
        try:
            iv_float = float(iv_value)
            # If IV is > 1, it's likely already a percentage, convert to decimal
            if iv_float > 1.0:
                iv_float = iv_float / 100.0
            
            # Validate reasonable range (0.01% to 500%)
            if 0.0001 <= iv_float <= 5.0:
                return round(iv_float, 4)
            else:
                logger.warning(f"IV value {iv_float} outside reasonable range, setting to None")
                return None
        except (ValueError, TypeError):
            return None
    
    def _validate_greek(self, greek_value) -> Optional[float]:
        """Validate and normalize Greek values"""
        if greek_value is None:
            return None
        
        try:
            greek_float = float(greek_value)
            # Round to reasonable precision
            return round(greek_float, 6)
        except (ValueError, TypeError):
            return None
    
    def _extract_price(self, price_value) -> Optional[float]:
        """Extract and validate price values"""
        if price_value is None:
            return None
        
        try:
            price_float = float(price_value)
            # Validate reasonable price range (0.01 to 10000)
            if 0.01 <= price_float <= 10000:
                return round(price_float, 2)
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def _extract_number(self, number_value) -> Optional[int]:
        """Extract and validate integer values (volume, OI)"""
        if number_value is None:
            return None
        
        try:
            number_int = int(float(number_value))
            # Validate reasonable range
            if 0 <= number_int <= 10000000:
                return number_int
            else:
                return None
        except (ValueError, TypeError):
            return None
    
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
        """Make HTTP request to Polygon API with caching, rate limiting, and error handling"""
        if params is None:
            params = {}
        
        # Rate limiting - ensure minimum interval between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {endpoint}")
            return cached_data
        
        # Require API key for all requests
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY is required but not set")
        
        # Ensure we're using real API data, not mock data
        if self.api_key == "mock_key" or self.api_key.startswith("mock"):
            raise PolygonAPIError("Cannot make API request: Invalid or mock API key detected")
        
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
            
            # Re-raise the exception instead of returning mock data
            raise
    
    
    async def get_historical_options_contracts(self, underlying: str, start_date: str, end_date: str) -> List[OptionContract]:
        """Get historical options contracts for underlying ticker over date range with pagination"""
        all_contracts = []
        offset = 0
        limit = 1000  # Polygon's max limit per request
        
        while True:
            endpoint = f"/v3/reference/options/contracts"
            params = {
                "underlying_ticker": underlying.upper(),
                "expiration_date.gte": start_date,
                "expiration_date.lte": end_date,
                "limit": limit,
                "offset": offset,
                "sort": "expiration_date"
            }
            
            try:
                logger.info(f"Fetching contracts for {underlying} with offset {offset}")
                data = await self._make_request(endpoint, params)
                contracts_batch = data.get("results", [])
                
                if not contracts_batch:
                    logger.info(f"No more contracts found at offset {offset}")
                    break
                
                # Parse contracts
                for contract_data in contracts_batch:
                    try:
                        # Parse contract details
                        contract_type_raw = contract_data.get("contract_type", "").lower()
                        contract_type = ContractType.CALL if contract_type_raw == "call" else ContractType.PUT
                        
                        # Parse expiry date
                        expiry_str = contract_data.get("expiration_date")
                        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date() if expiry_str else None
                        
                        if not expiry:
                            continue  # Skip contracts without valid expiry
                        
                        contract = OptionContract(
                            contract=contract_data.get("ticker", ""),
                            underlying=underlying.upper(),
                            expiry=expiry,
                            strike=float(contract_data.get("strike_price", 0)),
                            type=contract_type,
                            
                            # Historical contracts may not have current market data
                            last_price=None,
                            bid=None,
                            ask=None,
                            day_volume=None,
                            day_oi=None,
                            implied_volatility=None,
                            delta=None,
                            gamma=None,
                            theta=None,
                            vega=None
                        )
                        
                        all_contracts.append(contract)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing historical contract data: {str(e)}")
                        continue
                
                logger.info(f"Retrieved {len(contracts_batch)} contracts in this batch (total so far: {len(all_contracts)})")
                
                # If we got fewer contracts than the limit, we've reached the end
                if len(contracts_batch) < limit:
                    logger.info(f"Reached end of data (got {len(contracts_batch)} < {limit})")
                    break
                
                # Move to next page
                offset += limit
                
                # Safety limit to prevent infinite loops
                if offset > 10000:  # Max 10,000 contracts
                    logger.warning(f"Reached safety limit of 10,000 contracts for {underlying}")
                    break
                
            except Exception as e:
                logger.error(f"Error fetching contracts batch at offset {offset}: {str(e)}")
                break
        
        logger.info(f"Retrieved {len(all_contracts)} total historical contracts for {underlying} from {start_date} to {end_date}")
        return all_contracts
    
    async def get_options_with_full_history(self, underlying: str, limit_contracts: int = 50) -> List[Dict[str, Any]]:
        """Get options contracts with all available historical pricing data"""
        try:
            # Get contracts from a wider range to ensure we have contracts with sufficient history
            end_date = date.today()
            start_date = end_date - timedelta(days=60)  # Look back 60 days for contracts
            
            logger.info(f"Getting options with full history for {underlying}")
            
            # Get contracts
            contracts = await self.get_historical_options_contracts(
                underlying, start_date.isoformat(), end_date.isoformat()
            )
            
            # Limit to most recent contracts to avoid rate limits
            recent_contracts = contracts[:limit_contracts]
            
            # Get full historical data for each contract
            contracts_with_history = []
            for contract in recent_contracts:
                try:
                    # Calculate full historical range - get as much data as possible
                    history_end = date.today()
                    history_start = history_end - timedelta(days=365)  # Go back 1 year to get maximum data
                    
                    # Get historical pricing data
                    logger.info(f"Getting full history for contract {contract.contract} from {history_start} to {history_end}")
                    historical_data = await self.get_contract_historical_pricing(
                        contract.contract, 
                        history_start.isoformat(), 
                        history_end.isoformat()
                    )
                    logger.info(f"Retrieved {len(historical_data)} days of data for contract {contract.contract}")
                    
                    # Keep all available historical data - no limiting
                    
                    # Create contract data with history
                    contract_data = {
                        "contract": contract.contract,
                        "underlying": contract.underlying,
                        "expiry": contract.expiry.isoformat() if contract.expiry else None,
                        "strike": contract.strike,
                        "type": contract.type.value if contract.type else None,
                        "historical_data": historical_data,
                        "days_of_data": len(historical_data),
                        "latest_price": historical_data[-1].get('close') if historical_data else None,
                        "latest_volume": historical_data[-1].get('volume') if historical_data else None
                    }
                    
                    contracts_with_history.append(contract_data)
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Error getting history for contract {contract.contract}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(contracts_with_history)} contracts with full history for {underlying}")
            return contracts_with_history
            
        except Exception as e:
            logger.error(f"Error getting options with full history for {underlying}: {str(e)}")
            raise PolygonAPIError(f"Failed to get options with full history: {str(e)}")
    
    async def get_historical_options_data(self, underlying: str, start_date: str, end_date: str) -> List[OptionContract]:
        """Get historical options data with prices and Greeks for underlying ticker over date range"""
        try:
            # First get historical contracts
            contracts = await self.get_historical_options_contracts(underlying, start_date, end_date)
            
            # For each contract, get historical pricing data
            enriched_contracts = []
            for contract in contracts[:50]:  # Limit to first 50 to avoid rate limits
                try:
                    # Get historical pricing for this contract
                    pricing_data = await self.get_contract_historical_pricing(
                        contract.contract, start_date, end_date
                    )
                    
                    if pricing_data:
                        # Update contract with latest pricing data
                        latest_data = pricing_data[-1] if pricing_data else None
                        if latest_data:
                            contract.last_price = latest_data.get('close')
                            contract.day_volume = latest_data.get('volume')
                            # Note: Historical data may not have Greeks
                    
                    enriched_contracts.append(contract)
                    
                except Exception as e:
                    logger.warning(f"Error enriching contract {contract.contract}: {str(e)}")
                    enriched_contracts.append(contract)  # Add without enrichment
            
            logger.info(f"Retrieved {len(enriched_contracts)} enriched historical contracts for {underlying}")
            return enriched_contracts
            
        except Exception as e:
            logger.error(f"Error fetching historical options data for {underlying}: {str(e)}")
            raise PolygonAPIError(f"Failed to fetch historical options data: {str(e)}")
    
    async def get_contract_historical_pricing(self, contract: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical pricing data for a specific contract"""
        endpoint = f"/v2/aggs/ticker/{contract}/range/1/day/{start_date}/{end_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 1000
        }
        
        try:
            data = await self._make_request(endpoint, params)
            results = data.get("results", [])
            
            logger.info(f"API response for {contract}: status={data.get('status')}, results_count={len(results)}")
            
            # Process the raw data into the expected format
            processed_data = []
            for result in results:
                processed_data.append({
                    "date": datetime.fromtimestamp(result['t'] / 1000).strftime('%Y-%m-%d'),
                    "open": result.get('o'),
                    "high": result.get('h'),
                    "low": result.get('l'),
                    "close": result.get('c'),
                    "volume": result.get('v')
                })
            
            logger.info(f"Processed {len(processed_data)} data points for contract {contract}")
            return processed_data
            
        except Exception as e:
            logger.warning(f"Error fetching pricing for {contract}: {str(e)}")
            return []
    
    async def get_option_chain_snapshot(self, underlying: str) -> List[OptionContract]:
        """Get option chain snapshot for underlying ticker"""
        endpoint = f"/v3/snapshot/options/{underlying.upper()}"
        
        try:
            data = await self._make_request(endpoint)
            logger.info(f"Retrieved option chain data for {underlying}")
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
                        
                        # Market data - try multiple sources
                        last_price=self._extract_price(last_quote.get("p") or contract_data.get("last_quote", {}).get("p")),
                        bid=self._extract_price(last_quote.get("b") or contract_data.get("last_quote", {}).get("b")),
                        ask=self._extract_price(last_quote.get("a") or contract_data.get("last_quote", {}).get("a")),
                        
                        # Volume and OI - try multiple sources
                        day_volume=self._extract_number(day_data.get("volume") or contract_data.get("day", {}).get("volume")),
                        day_oi=self._extract_number(day_data.get("open_interest") or contract_data.get("day", {}).get("open_interest")),
                        
                        # Greeks and IV - check multiple possible locations and validate
                        implied_volatility=self._validate_iv(
                            contract_data.get("implied_volatility") or 
                            greeks.get("implied_volatility") or
                            contract_data.get("iv")
                        ),
                        delta=self._validate_greek(greeks.get("delta")),
                        gamma=self._validate_greek(greeks.get("gamma")),
                        theta=self._validate_greek(greeks.get("theta")),
                        vega=self._validate_greek(greeks.get("vega"))
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