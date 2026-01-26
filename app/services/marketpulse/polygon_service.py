"""
Polygon API Service for Market Pulse
Fetches market data for pulse calculation
"""
import os
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import httpx
from functools import wraps

try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    RESTClient = None
    POLYGON_AVAILABLE = False

logger = logging.getLogger(__name__)


class PolygonAPIError(Exception):
    """Custom exception for Polygon API errors"""
    pass


def retry_with_backoff(max_retries: int = 5, base_delay: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator


class MarketPulsePolygonService:
    """Polygon service for Market Pulse data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        self.client = None
        self.rest_client = None
        
        if not self.api_key:
            logger.warning("POLYGON_API_KEY not set - Market Pulse Polygon service will not be available")
            return
        
        if not POLYGON_AVAILABLE:
            logger.warning("polygon-api-client package not installed")
            return
        
        try:
            self.rest_client = RESTClient(self.api_key)
            logger.info("Market Pulse Polygon RESTClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Polygon RESTClient: {str(e)}")
            self.rest_client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def get_market_snapshot(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Get snapshot data for multiple tickers
        Returns current price, volume, and other market data
        """
        if not self.rest_client:
            raise PolygonAPIError("Polygon RESTClient not initialized")
        
        try:
            # Get snapshot for all tickers
            snapshot_data = {}
            for ticker in tickers:
                try:
                    snapshot = self.rest_client.get_snapshot_ticker(ticker)
                    if snapshot:
                        snapshot_data[ticker] = {
                            'price': snapshot.get('day', {}).get('c'),  # close price
                            'volume': snapshot.get('day', {}).get('v'),  # volume
                            'high': snapshot.get('day', {}).get('h'),
                            'low': snapshot.get('day', {}).get('l'),
                            'open': snapshot.get('day', {}).get('o'),
                            'prev_close': snapshot.get('prevDay', {}).get('c'),
                            'timestamp': datetime.now()
                        }
                except Exception as e:
                    logger.warning(f"Failed to get snapshot for {ticker}: {e}")
                    continue
            
            return snapshot_data
        except Exception as e:
            logger.error(f"Error fetching market snapshot: {e}")
            raise PolygonAPIError(f"Failed to fetch market snapshot: {str(e)}")
    
    async def get_aggregates(
        self,
        ticker: str,
        multiplier: int = 1,
        timespan: str = "minute",
        from_date: date = None,
        to_date: date = None,
        limit: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Get aggregate bars (OHLCV) for a ticker
        Used for calculating velocity and volatility
        """
        if not self.rest_client:
            raise PolygonAPIError("Polygon RESTClient not initialized")
        
        if not from_date:
            from_date = date.today() - timedelta(days=1)
        if not to_date:
            to_date = date.today()
        
        try:
            aggs = self.rest_client.get_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=from_date.isoformat(),
                to=to_date.isoformat(),
                limit=limit
            )
            
            results = []
            if aggs and hasattr(aggs, 'results'):
                for agg in aggs.results:
                    results.append({
                        'timestamp': datetime.fromtimestamp(agg.timestamp / 1000),
                        'open': agg.open,
                        'high': agg.high,
                        'low': agg.low,
                        'close': agg.close,
                        'volume': agg.volume
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching aggregates for {ticker}: {e}")
            raise PolygonAPIError(f"Failed to fetch aggregates: {str(e)}")
    
    async def get_grouped_daily(self, date: date = None) -> Dict[str, Any]:
        """
        Get grouped daily bars for all stocks
        Used for breadth calculation
        """
        if not self.rest_client:
            raise PolygonAPIError("Polygon RESTClient not initialized")
        
        if not date:
            date = date.today()
        
        try:
            grouped = self.rest_client.get_grouped_daily_aggs(
                date=date.isoformat()
            )
            
            return {
                'date': date.isoformat(),
                'results': [
                    {
                        'ticker': r.ticker,
                        'close': r.close,
                        'volume': r.volume,
                        'high': r.high,
                        'low': r.low
                    }
                    for r in (grouped.results if hasattr(grouped, 'results') else [])
                ] if grouped else []
            }
        except Exception as e:
            logger.error(f"Error fetching grouped daily: {e}")
            raise PolygonAPIError(f"Failed to fetch grouped daily: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()

