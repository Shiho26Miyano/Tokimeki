"""
Polygon API Service for Market Pulse

Layer 1: Data Collection Layer
职责: WebSocket 连接管理，接收实时市场数据
技术: websocket-client, Polygon.io WebSocket API, threading

扩展点:
- 支持其他数据源（Alpha Vantage, Yahoo Finance 等）
- 支持不同的 WebSocket 协议
- 添加连接重试和错误恢复机制
"""
import os
import logging
import asyncio
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional, Any
import httpx
from functools import wraps

try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    RESTClient = None
    POLYGON_AVAILABLE = False

try:
    import websocket
    import json
    import threading
    import ssl
    WEBSOCKET_AVAILABLE = True
except ImportError:
    websocket = None
    ssl = None
    WEBSOCKET_AVAILABLE = False

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
    """Polygon service for Market Pulse data with WebSocket support"""
    
    def __init__(self, api_key: str = None, use_delayed: bool = None):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        
        # Determine WebSocket URL based on plan access
        # If use_delayed is None, check environment variable, default to False (real-time)
        if use_delayed is None:
            use_delayed = os.getenv("POLYGON_USE_DELAYED_WS", "false").lower() == "true"
        
        if use_delayed:
            self.ws_url = "wss://delayed.polygon.io/stocks"  # 15-min delayed data
            logger.warning("⚠️  Using DELAYED WebSocket (15-minute delay) - set POLYGON_USE_DELAYED_WS=false for real-time")
        else:
            self.ws_url = "wss://socket.polygon.io/stocks"  # Real-time data (requires plan)
            logger.info("✅ Using REAL-TIME WebSocket")
        
        self.client = None
        self.rest_client = None
        
        # WebSocket state
        self.ws = None
        self.ws_thread = None
        self.ws_connected = False
        self.on_bar_callback = None
        self.subscribed_tickers = []
        self.realtime_access_denied = False  # Track if real-time access was denied
        
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
    
    def start_ws_aggregates(
        self,
        tickers: List[str],
        on_bar: callable = None
    ):
        """
        Start WebSocket connection for real-time aggregates (1-minute bars)
        
        Args:
            tickers: List of ticker symbols to subscribe to (e.g., ["SPY", "QQQ"])
            on_bar: Callback function that receives bar data: on_bar(ticker, bar_dict)
        """
        if not WEBSOCKET_AVAILABLE:
            logger.error("websocket-client package not installed. Install with: pip install websocket-client")
            return False
        
        if not self.api_key:
            logger.error("POLYGON_API_KEY not set - cannot start WebSocket")
            return False
        
        if self.ws_connected:
            logger.warning("WebSocket already connected")
            return True
        
        self.on_bar_callback = on_bar
        self.subscribed_tickers = tickers
        
        try:
            # Start WebSocket in background thread
            self.ws_thread = threading.Thread(target=self._ws_thread, daemon=True)
            self.ws_thread.start()
            logger.info(f"WebSocket thread started for tickers: {tickers}")
            return True
        except Exception as e:
            logger.error(f"Failed to start WebSocket: {e}")
            return False
    
    def _ws_thread(self):
        """WebSocket thread function"""
        try:
            # Create WebSocket connection
            # Note: SSL certificate verification may fail on macOS
            # We'll handle this by using sslopt parameter
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close
            )
            
            # Run WebSocket with SSL options
            # On macOS, SSL certificate verification may fail due to certificate chain issues
            # We'll try with verification first, then fall back if needed
            ssl_options = {}
            
            try:
                # Try to use default SSL context (preferred)
                ssl_context = ssl.create_default_context()
                ssl_options = {"context": ssl_context}
                logger.debug("Using default SSL context for WebSocket")
            except Exception as ssl_error:
                logger.warning(f"Could not create default SSL context: {ssl_error}")
                # Fallback: disable certificate verification (for development)
                # WARNING: This reduces security but allows connection on systems with cert issues
                logger.warning("⚠️  Using unverified SSL (cert_reqs=CERT_NONE) - for development only")
                ssl_options = {"cert_reqs": ssl.CERT_NONE}
            
            # Run forever (blocks until connection closes)
            self.ws.run_forever(sslopt=ssl_options)
                
        except Exception as e:
            logger.error(f"❌ WebSocket thread error: {e}", exc_info=True)
            self.ws_connected = False
    
    def _on_ws_open(self, ws):
        """Handle WebSocket open event"""
        logger.info("🔌 WebSocket connection opened, authenticating...")
        try:
            # Authenticate with Polygon.io
            auth_msg = {
                "action": "auth",
                "params": self.api_key
            }
            ws.send(json.dumps(auth_msg))
            logger.debug(f"Authentication message sent: {auth_msg['action']}")
        except Exception as e:
            logger.error(f"Error sending authentication: {e}")
            self.ws_connected = False
    
    def _on_ws_message(self, ws, message):
        """Handle WebSocket message"""
        try:
            data = json.loads(message)
            logger.debug(f"📨 WebSocket message received: {type(data)}")
            
            # Handle authentication response
            if isinstance(data, list):
                for event in data:
                    ev_type = event.get("ev")
                    status = event.get("status")
                    
                    if ev_type == "status":
                        if status == "auth_success":
                            logger.info("✅ WebSocket authenticated successfully")
                            self.ws_connected = True
                            # Subscribe to aggregates after successful auth
                            self._subscribe_aggregates()
                        elif status == "auth_failed":
                            logger.error("❌ WebSocket authentication failed")
                            logger.error(f"   Response: {event}")
                            self.ws_connected = False
                        elif status == "sub_success":
                            logger.info(f"✅ Subscription successful: {event.get('message', '')}")
                        elif status == "sub_failed":
                            logger.error(f"❌ Subscription failed: {event.get('message', '')}")
                        elif status == "error":
                            error_msg = event.get('message', '')
                            logger.error(f"❌ WebSocket error: {error_msg}")
                            # Check if it's a real-time data access error
                            if "real-time data" in error_msg.lower() or "don't have access" in error_msg.lower():
                                self.realtime_access_denied = True
                                logger.error("❌ Real-time data access denied!")
                                logger.warning("⚠️  Your API key doesn't have real-time data access.")
                                logger.info("💡 Solutions:")
                                logger.info("   1. Visit https://polygon.io/dashboard to sign agreements (if you have a plan)")
                                logger.info("   2. Set POLYGON_USE_DELAYED_WS=true to use 15-min delayed data (free)")
                                logger.info("   3. Upgrade your plan at https://polygon.io/pricing")
                        else:
                            logger.debug(f"Status event: {status} - {event}")
                    elif ev_type == "AM":  # Per-minute aggregate (bar) event
                        logger.debug(f"📊 AM aggregate received: {event.get('sym', 'unknown')}")
                        self._handle_aggregate(event)
                    elif ev_type == "A":  # Per-second aggregate (also handle for compatibility)
                        logger.debug(f"📊 A aggregate received: {event.get('sym', 'unknown')}")
                        self._handle_aggregate(event)
                    else:
                        logger.debug(f"Unknown event type: {ev_type}")
            elif isinstance(data, dict):
                ev_type = data.get("ev")
                status = data.get("status")
                
                if ev_type == "status":
                    if status == "auth_success":
                        logger.info("✅ WebSocket authenticated successfully")
                        self.ws_connected = True
                        self._subscribe_aggregates()
                    elif status == "auth_failed":
                        logger.error("❌ WebSocket authentication failed")
                        logger.error(f"   Response: {data}")
                        self.ws_connected = False
                    elif status == "sub_success":
                        logger.info(f"✅ Subscription successful: {data.get('message', '')}")
                    elif status == "sub_failed":
                        logger.error(f"❌ Subscription failed: {data.get('message', '')}")
                    elif status == "error":
                        error_msg = data.get('message', '')
                        logger.error(f"❌ WebSocket error: {error_msg}")
                        # Check if it's a real-time data access error
                        if "real-time data" in error_msg.lower() or "don't have access" in error_msg.lower():
                            self.realtime_access_denied = True
                            logger.error("❌ Real-time data access denied!")
                            logger.warning("⚠️  Your API key doesn't have real-time data access.")
                            logger.info("💡 Solutions:")
                            logger.info("   1. Visit https://polygon.io/dashboard to sign agreements (if you have a plan)")
                            logger.info("   2. Set POLYGON_USE_DELAYED_WS=true to use 15-min delayed data (free)")
                            logger.info("   3. Upgrade your plan at https://polygon.io/pricing")
                    else:
                        logger.debug(f"Status: {status} - {data}")
                elif ev_type == "AM":  # Per-minute aggregate event
                    logger.debug(f"📊 AM aggregate received: {data.get('sym', 'unknown')}")
                    self._handle_aggregate(data)
                elif ev_type == "A":  # Per-second aggregate (also handle for compatibility)
                    logger.debug(f"📊 A aggregate received: {data.get('sym', 'unknown')}")
                    self._handle_aggregate(data)
                else:
                    logger.debug(f"Unknown event type: {ev_type} - {data}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse WebSocket message: {e}")
            logger.error(f"   Raw message: {message[:200]}")
        except Exception as e:
            logger.error(f"❌ Error processing WebSocket message: {e}", exc_info=True)
    
    def _subscribe_aggregates(self):
        """Subscribe to aggregate bars for tickers"""
        if not self.ws:
            logger.error("❌ Cannot subscribe: WebSocket not initialized")
            return
        
        if not self.subscribed_tickers:
            logger.warning("⚠️  No tickers to subscribe to")
            return
        
        try:
            # Subscribe to 1-minute aggregates
            # Format: AM.{ticker} for per-minute aggregates (A is per-second)
            subscriptions = [f"AM.{ticker}" for ticker in self.subscribed_tickers]
            
            subscribe_msg = {
                "action": "subscribe",
                "params": ",".join(subscriptions)
            }
            
            self.ws.send(json.dumps(subscribe_msg))
            logger.info(f"📡 Subscription message sent: {subscriptions}")
            logger.debug(f"   Full message: {subscribe_msg}")
        except Exception as e:
            logger.error(f"❌ Error subscribing to aggregates: {e}", exc_info=True)
    
    def _handle_aggregate(self, event: Dict[str, Any]):
        """Handle aggregate bar event"""
        try:
            # Parse aggregate event
            # Format: {"ev":"A","sym":"SPY","v":12345,"av":123456,"op":450.0,"vw":450.5,"o":450.1,"c":450.2,"h":450.3,"l":450.0,"a":450.15,"z":1,"s":1234567890000,"e":12345678960000}
            ticker = event.get("sym", "")
            start_time_ms = event.get("s", 0)
            
            # Convert timestamp to datetime and then to ISO string
            if start_time_ms > 0:
                dt = datetime.fromtimestamp(start_time_ms / 1000, tz=timezone.utc)
                timestamp_str = dt.isoformat().replace('+00:00', 'Z')
            else:
                timestamp_str = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            bar = {
                "ticker": ticker,
                "timestamp": timestamp_str,  # ISO format string
                "open": event.get("o", 0),
                "high": event.get("h", 0),
                "low": event.get("l", 0),
                "close": event.get("c", 0),
                "volume": event.get("v", 0),
                "vwap": event.get("vw", 0)
            }
            
            logger.debug(f"📊 Processing bar: {ticker} at {timestamp_str}")
            
            # Call callback if provided
            if self.on_bar_callback:
                try:
                    self.on_bar_callback(ticker, bar)
                except Exception as e:
                    logger.error(f"❌ Error in on_bar callback: {e}", exc_info=True)
            else:
                logger.warning("⚠️  No callback registered for bar data")
            
        except Exception as e:
            logger.error(f"❌ Error handling aggregate event: {e}", exc_info=True)
            logger.error(f"   Event data: {event}")
    
    def _on_ws_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")
        self.ws_connected = False
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.ws_connected = False
    
    def stop_ws(self):
        """Stop WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.ws_connected = False
            logger.info("WebSocket connection closed")
    
    async def close(self):
        """Close HTTP client and WebSocket"""
        self.stop_ws()
        if self.client and not self.client.is_closed:
            await self.client.aclose()

