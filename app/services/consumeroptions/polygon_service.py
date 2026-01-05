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
from concurrent.futures import ThreadPoolExecutor
import httpx
from functools import wraps

try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    RESTClient = None
    POLYGON_AVAILABLE = False

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
        self.client = None  # httpx client for REST API calls
        self.rest_client = None  # Polygon RESTClient for aggregates
        
        # Thread pool executor for running synchronous RESTClient calls
        self.executor = ThreadPoolExecutor(max_workers=5)
        
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
        
        if not POLYGON_AVAILABLE:
            raise ValueError("polygon-api-client package not installed. Install with: pip install polygon-api-client")
        
        # Initialize Polygon RESTClient
        try:
            self.rest_client = RESTClient(self.api_key)
            logger.info("Polygon RESTClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Polygon RESTClient: {str(e)}")
            raise ValueError(f"Failed to initialize Polygon RESTClient: {str(e)}")
    
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
        """Get cached data if not expired - DISABLED for live data"""
        # Disable caching for live/real-time data to ensure freshness
        # For snapshot endpoints, always fetch fresh data
        if 'snapshot' in cache_key.lower():
            return None
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
            
            logger.debug(f"Making API request to: {url} with params: {dict((k, v) for k, v in params.items() if k != 'apikey')}")
            
            response = await client.get(url, params=params)
            
            # Log response status
            logger.debug(f"API response status: {response.status_code}")
            
            # Check for HTTP errors
            if response.status_code == 401:
                error_msg = "Invalid API key. Please check your POLYGON_API_KEY environment variable."
                logger.error(error_msg)
                raise PolygonAPIError(error_msg)
            elif response.status_code == 403:
                error_msg = "API access forbidden. Please check your Polygon API subscription plan."
                logger.error(error_msg)
                raise PolygonAPIError(error_msg)
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded. Please wait before making more requests."
                logger.error(error_msg)
                raise PolygonAPIError(error_msg)
            
            response.raise_for_status()
            
            self.api_calls += 1
            result = response.json()
            
            # Validate response structure
            if not isinstance(result, dict):
                error_msg = f"Invalid API response format: expected dict, got {type(result)}"
                logger.error(f"{error_msg} for {endpoint}")
                raise PolygonAPIError(error_msg)
            
            # Cache successful response
            self._cache_data(cache_key, result)
            
            logger.debug(f"API call successful: {endpoint}")
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error for {endpoint}: {e.response.text[:200]}"
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
        """Get historical pricing data for a specific contract using Polygon RESTClient"""
        try:
            # Run synchronous RESTClient call in thread pool to maintain async interface
            def fetch_aggs():
                aggs = []
                try:
                    for agg in self.rest_client.list_aggs(
                        contract,
                        1,  # multiplier
                        "day",  # timespan
                        start_date,
                        end_date,
                        adjusted="true",
                        sort="asc",
                        limit=1000
                    ):
                        aggs.append(agg)
                    return aggs
                except Exception as e:
                    logger.error(f"Error in RESTClient.list_aggs for {contract}: {str(e)}")
                    raise
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            aggs = await loop.run_in_executor(self.executor, fetch_aggs)
            
            logger.info(f"Retrieved {len(aggs)} aggregates for contract {contract}")
            
            # Process the raw data into the expected format
            processed_data = []
            for agg in aggs:
                try:
                    processed_data.append({
                        "date": datetime.fromtimestamp(agg.timestamp / 1000).strftime('%Y-%m-%d'),
                        "open": agg.open,
                        "high": agg.high,
                        "low": agg.low,
                        "close": agg.close,
                        "volume": agg.volume
                    })
                except Exception as e:
                    logger.warning(f"Error processing agg data: {str(e)}")
                    continue
            
            logger.info(f"Processed {len(processed_data)} data points for contract {contract}")
            return processed_data
            
        except Exception as e:
            logger.warning(f"Error fetching pricing for {contract}: {str(e)}")
            return []
    
    async def _get_latest_agg_for_contract(self, contract_ticker: str) -> Optional[Dict[str, Any]]:
        """Get the latest aggregate data for a contract using RESTClient"""
        try:
            # Get date range - last 30 days to ensure we get recent data
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            def fetch_latest_agg():
                try:
                    # Ensure contract ticker has the "O:" prefix if it's an options contract
                    # Polygon RESTClient expects "O:TICKER..." format for options
                    ticker_to_use = contract_ticker
                    if not ticker_to_use.startswith("O:"):
                        # Check if it looks like an options contract (has expiry/strike info)
                        # If it does, add the "O:" prefix
                        ticker_to_use = f"O:{ticker_to_use}"
                    
                    logger.debug(f"Fetching aggregates for contract: {ticker_to_use} from {start_date} to {end_date}")
                    
                    # Get aggregates for the contract
                    aggs = []
                    for agg in self.rest_client.list_aggs(
                        ticker_to_use,
                        1,  # multiplier
                        "day",  # timespan
                        start_date.isoformat(),
                        end_date.isoformat(),
                        adjusted="true",
                        sort="desc",  # Get most recent first
                        limit=5  # Get last 5 days to find the most recent with data
                    ):
                        aggs.append(agg)
                        # Get the first (most recent) non-zero volume if available
                        if agg.volume > 0:
                            break
                    
                    if aggs:
                        # Use the first aggregate (most recent)
                        agg = aggs[0]
                        logger.debug(f"Found aggregate for {ticker_to_use}: close={agg.close}, volume={agg.volume}, timestamp={agg.timestamp}")
                        return {
                            "close": float(agg.close),
                            "volume": int(agg.volume),
                            "timestamp": agg.timestamp
                        }
                    else:
                        logger.warning(f"No aggregates found for {ticker_to_use}")
                    return None
                except Exception as e:
                    logger.warning(f"Error fetching latest agg for {contract_ticker}: {str(e)}", exc_info=True)
                    return None
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            latest_agg = await loop.run_in_executor(self.executor, fetch_latest_agg)
            return latest_agg
            
        except Exception as e:
            logger.warning(f"Error getting latest agg for {contract_ticker}: {str(e)}", exc_info=True)
            return None
    
    async def get_option_chain_snapshot(self, underlying: str) -> List[OptionContract]:
        """Get LIVE option chain snapshot for underlying ticker using RESTClient.list_snapshot_options_chain - REAL-TIME DATA"""
        try:
            if not self.rest_client:
                logger.error(f"RESTClient not initialized for {underlying}. Check POLYGON_API_KEY.")
                return []
            
            logger.info(f"Fetching LIVE option chain snapshot for {underlying} using RESTClient.list_snapshot_options_chain (real-time data)")
            
            def fetch_options_chain():
                """Fetch options chain using RESTClient (synchronous)"""
                options_chain = []
                try:
                    if not self.rest_client:
                        logger.error("RESTClient is None - cannot fetch options chain")
                        return []
                    
                    # Fetch all contracts - no limit to get all expiry dates
                    logger.info(f"Calling list_snapshot_options_chain for {underlying.upper()}")
                    contract_iterator = self.rest_client.list_snapshot_options_chain(
                        underlying.upper(),
                        params={
                            "order": "asc",
                            "limit": 250,  # Fetch 250 at a time (as per user's example)
                            "sort": "ticker",
                        }
                    )
                    
                    contract_count = 0
                    for contract_data in contract_iterator:
                        options_chain.append(contract_data)
                        contract_count += 1
                        # Safety limit to prevent infinite loops
                        if contract_count >= 10000:
                            logger.warning(f"Reached safety limit of 10,000 contracts for {underlying}")
                            break
                    
                    logger.info(f"Fetched {len(options_chain)} contracts from Polygon API for {underlying}")
                    if len(options_chain) == 0:
                        logger.warning(f"No contracts returned from Polygon API for {underlying}. This may indicate:")
                        logger.warning(f"  1. The ticker has no options available")
                        logger.warning(f"  2. Polygon API subscription doesn't include options data")
                        logger.warning(f"  3. API rate limit or error occurred")
                    return options_chain
                except Exception as e:
                    logger.error(f"Error in RESTClient.list_snapshot_options_chain for {underlying}: {str(e)}", exc_info=True)
                    raise
            
            # Execute in thread pool to maintain async interface
            loop = asyncio.get_event_loop()
            raw_contracts = await loop.run_in_executor(self.executor, fetch_options_chain)
            
            if not raw_contracts:
                logger.warning(f"No contracts returned from Polygon API for {underlying}")
                return []
            
            logger.info(f"Processing {len(raw_contracts)} raw contracts for {underlying}")
            contracts = []
            skipped_count = 0
            
            for contract_data in raw_contracts:
                try:
                    # Extract data from OptionContractSnapshot dataclass
                    if not hasattr(contract_data, 'details') or contract_data.details is None:
                        skipped_count += 1
                        continue
                    
                    details = contract_data.details
                    contract_ticker = getattr(details, 'ticker', None)
                    if not contract_ticker:
                        skipped_count += 1
                        continue
                    
                    # Parse contract type
                    contract_type_raw = getattr(details, 'contract_type', '').lower()
                    if not contract_type_raw:
                        skipped_count += 1
                        continue
                    contract_type = ContractType.CALL if contract_type_raw == "call" else ContractType.PUT
                    
                    # Parse expiry date
                    expiry_str = getattr(details, 'expiration_date', None)
                    if not expiry_str:
                        skipped_count += 1
                        continue
                    try:
                        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    except ValueError:
                        skipped_count += 1
                        continue
                    
                    # Get strike price
                    strike_price = getattr(details, 'strike_price', 0)
                    try:
                        strike = float(strike_price)
                    except (ValueError, TypeError):
                        skipped_count += 1
                        continue
                    
                    # Extract day data (volume, close price)
                    day_data = contract_data.day if hasattr(contract_data, 'day') and contract_data.day else None
                    day_volume = self._extract_number(getattr(day_data, 'volume', None) if day_data else None)
                    day_oi = self._extract_number(getattr(contract_data, 'open_interest', None))
                    
                    # Extract pricing - use day.close as primary, fallback to last_trade/quote
                    last_price = self._extract_price(getattr(day_data, 'close', None) if day_data else None)
                    if not last_price:
                        last_trade = contract_data.last_trade if hasattr(contract_data, 'last_trade') and contract_data.last_trade else None
                        if last_trade:
                            last_price = self._extract_price(getattr(last_trade, 'price', None))
                    bid = None
                    ask = None
                    
                    # Extract Greeks
                    greeks = contract_data.greeks if hasattr(contract_data, 'greeks') and contract_data.greeks else None
                    delta = self._validate_greek(getattr(greeks, 'delta', None) if greeks else None)
                    gamma = self._validate_greek(getattr(greeks, 'gamma', None) if greeks else None)
                    theta = self._validate_greek(getattr(greeks, 'theta', None) if greeks else None)
                    vega = self._validate_greek(getattr(greeks, 'vega', None) if greeks else None)
                    
                    # Implied volatility
                    implied_volatility = self._validate_iv(getattr(contract_data, 'implied_volatility', None))
                    
                    contract = OptionContract(
                        contract=contract_ticker,
                        underlying=underlying.upper(),
                        expiry=expiry,
                        strike=strike,
                        type=contract_type,
                        last_price=last_price,
                        bid=bid,
                        ask=ask,
                        day_volume=day_volume,
                        day_oi=day_oi,
                        implied_volatility=implied_volatility,
                        delta=delta,
                        gamma=gamma,
                        theta=theta,
                        vega=vega
                    )
                    
                    contracts.append(contract)
                    
                except Exception as e:
                    logger.debug(f"Error parsing contract: {str(e)}")
                    skipped_count += 1
                    continue
            
            logger.info(f"Retrieved {len(contracts)} valid contracts for {underlying} (skipped {skipped_count})")
            return contracts
            
        except Exception as e:
            logger.error(f"Error fetching option chain for {underlying}: {str(e)}", exc_info=True)
            return []
    
    async def get_underlying_daily_bars(self, ticker: str, start_date: str, end_date: str) -> List[UnderlyingData]:
        """Get daily bars for underlying stock using Polygon RESTClient"""
        try:
            if not self.rest_client:
                logger.error(f"RESTClient not initialized for {ticker}. Check POLYGON_API_KEY.")
                return []
            
            logger.info(f"Fetching daily bars for {ticker} from {start_date} to {end_date}")
            
            # Run synchronous RESTClient call in thread pool to maintain async interface
            def fetch_aggs():
                aggs = []
                try:
                    if not self.rest_client:
                        logger.error("RESTClient is None - cannot fetch daily bars")
                        return []
                    
                    logger.info(f"Calling list_aggs for {ticker.upper()} from {start_date} to {end_date}")
                    agg_iterator = self.rest_client.list_aggs(
                        ticker.upper(),
                        1,  # multiplier
                        "day",  # timespan
                        start_date,
                        end_date,
                        adjusted="true",
                        sort="asc",
                        limit=5000
                    )
                    
                    agg_count = 0
                    for agg in agg_iterator:
                        aggs.append(agg)
                        agg_count += 1
                        # Safety limit
                        if agg_count >= 5000:
                            logger.warning(f"Reached limit of 5000 aggregates for {ticker}")
                            break
                    
                    logger.info(f"Fetched {len(aggs)} aggregates from Polygon API for {ticker}")
                    if len(aggs) == 0:
                        logger.warning(f"No aggregates returned from Polygon API for {ticker}. This may indicate:")
                        logger.warning(f"  1. The date range is invalid or outside available data")
                        logger.warning(f"  2. Polygon API subscription doesn't include historical stock data")
                        logger.warning(f"  3. Ticker symbol is invalid or delisted")
                    return aggs
                except Exception as e:
                    logger.error(f"Error in RESTClient.list_aggs for {ticker}: {str(e)}", exc_info=True)
                    raise
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            aggs = await loop.run_in_executor(self.executor, fetch_aggs)
            
            if not aggs:
                logger.warning(f"No aggregates returned for {ticker}")
                return []
            
            logger.info(f"Processing {len(aggs)} aggregates for {ticker}")
            bars = []
            skipped_count = 0
            
            for agg in aggs:
                try:
                    # Convert timestamp to date
                    bar_date = datetime.fromtimestamp(agg.timestamp / 1000).date()
                    
                    bar = UnderlyingData(
                        ticker=ticker.upper(),
                        bar_date=bar_date,
                        open=float(agg.open),
                        high=float(agg.high),
                        low=float(agg.low),
                        close=float(agg.close),
                        volume=int(agg.volume)
                    )
                    
                    bars.append(bar)
                    
                except Exception as e:
                    logger.warning(f"Error parsing bar data for {ticker}: {str(e)}")
                    skipped_count += 1
                    continue
            
            logger.info(f"Successfully processed {len(bars)} daily bars for {ticker} (skipped {skipped_count})")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching daily bars for {ticker}: {str(e)}", exc_info=True)
            # Return empty list instead of raising to allow dashboard to render with other data
            return []
    
    async def get_underlying_snapshot(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get LIVE snapshot data for underlying stock (real-time price, volume, etc.)"""
        try:
            logger.info(f"Fetching LIVE snapshot for {ticker} using RESTClient.get_snapshot_ticker")
            
            def fetch_snapshot():
                """Fetch snapshot using RESTClient (synchronous)"""
                try:
                    snapshot = self.rest_client.get_snapshot_ticker(ticker.upper())
                    return snapshot
                except Exception as e:
                    logger.error(f"Error in RESTClient.get_snapshot_ticker for {ticker}: {str(e)}", exc_info=True)
                    raise
            
            # Execute in thread pool to maintain async interface
            loop = asyncio.get_event_loop()
            snapshot = await loop.run_in_executor(self.executor, fetch_snapshot)
            
            if not snapshot:
                logger.warning(f"No snapshot data returned from Polygon API for {ticker}")
                return None
            
            # Extract current price and volume from snapshot
            current_price = None
            current_volume = None
            day_change = None
            day_change_percent = None
            
            # Get day data
            if hasattr(snapshot, 'day') and snapshot.day:
                day_data = snapshot.day
                if hasattr(day_data, 'close') and day_data.close:
                    current_price = float(day_data.close)
                if hasattr(day_data, 'volume') and day_data.volume:
                    current_volume = int(day_data.volume)
                if hasattr(day_data, 'open') and day_data.open and current_price:
                    day_change = current_price - float(day_data.open)
                    day_change_percent = (day_change / float(day_data.open) * 100) if day_data.open > 0 else None
            
            # Get last trade if day data not available
            if not current_price and hasattr(snapshot, 'last_trade') and snapshot.last_trade:
                last_trade = snapshot.last_trade
                if hasattr(last_trade, 'price') and last_trade.price:
                    current_price = float(last_trade.price)
            
            # Get last quote if still no price
            if not current_price and hasattr(snapshot, 'last_quote') and snapshot.last_quote:
                quote = snapshot.last_quote
                if hasattr(quote, 'last_ask_price') and quote.last_ask_price:
                    current_price = float(quote.last_ask_price)
                elif hasattr(quote, 'last_bid_price') and quote.last_bid_price:
                    current_price = float(quote.last_bid_price)
            
            return {
                'ticker': ticker.upper(),
                'current_price': current_price,
                'current_volume': current_volume,
                'day_change': day_change,
                'day_change_percent': day_change_percent,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching snapshot for {ticker}: {str(e)}", exc_info=True)
            return None
    
    async def get_contract_minute_bars(self, contract: str, start_date: str, end_date: str) -> List[ContractBars]:
        """Get 1-minute bars for specific option contract using Polygon RESTClient"""
        try:
            # Run synchronous RESTClient call in thread pool to maintain async interface
            def fetch_aggs():
                aggs = []
                try:
                    for agg in self.rest_client.list_aggs(
                        contract,
                        1,  # multiplier
                        "minute",  # timespan
                        start_date,
                        end_date,
                        adjusted="true",
                        sort="asc",
                        limit=50000
                    ):
                        aggs.append(agg)
                    return aggs
                except Exception as e:
                    logger.error(f"Error in RESTClient.list_aggs for {contract}: {str(e)}")
                    raise
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            aggs = await loop.run_in_executor(self.executor, fetch_aggs)
            
            logger.info(f"Retrieved {len(aggs)} aggregates for contract {contract}")
            
            bars = []
            for agg in aggs:
                try:
                    # Convert timestamp to datetime
                    bar_time = datetime.fromtimestamp(agg.timestamp / 1000)
                    
                    bar = ContractBars(
                        contract=contract,
                        timestamp=bar_time,
                        open=float(agg.open),
                        high=float(agg.high),
                        low=float(agg.low),
                        close=float(agg.close),
                        volume=int(agg.volume)
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
        """Close the HTTP client and executor"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
        if self.executor:
            self.executor.shutdown(wait=True)
    
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