"""
Market Pulse Data Collector

Layer 1: Data Collection Layer
职责: 从 Polygon/Massive WebSocket 采集原始数据并存储到 S3
技术: websocket-client, Polygon.io API, boto3

扩展点:
- 支持多个数据源（不只是 Polygon）
- 支持不同的数据格式
- 添加数据验证和清洗
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import json

from app.services.marketpulse.polygon_service import MarketPulsePolygonService
from app.services.marketpulse.aws_storage import AWSStorageService

logger = logging.getLogger(__name__)


class MarketPulseDataCollector:
    """
    Data Collector for Market Pulse
    
    Architecture:
    1. WebSocket: Receives raw bar data from Polygon/Massive
    2. Store: Raw bars stored directly to S3 (raw-data/YYYY-MM-DD/ticker-timestamp.json)
    3. Agent: AWS Lambda reads raw data, computes pulse, learns, stores results
    4. Dashboard: Reads agent-processed results from S3
    """
    
    def __init__(
        self,
        polygon_api_key: str = None,
        s3_bucket: str = None,
        tickers: list = None,
        use_delayed_ws: bool = None
    ):
        self.polygon_service = MarketPulsePolygonService(
            api_key=polygon_api_key,
            use_delayed=use_delayed_ws
        )
        self.aws_storage = AWSStorageService(s3_bucket=s3_bucket)
        # Default to 10 supported tickers for dual signal architecture
        self.tickers = tickers or ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'GOOGL', 'JPM', 'XOM', 'SPY']
        self.started = False
        # Aggregate raw 1m bars into 5m bars before writing to S3
        self.bar_interval_minutes = 5
        # Per‑ticker in‑memory aggregation state for current 5m window
        # ticker -> state dict
        self._agg_state: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.bars_collected = 0
        self.last_bar_time = None
    
    def start(self):
        """Start collecting raw market data"""
        if self.started:
            logger.warning("DataCollector already started")
            return
        
        logger.info(f"Starting Market Pulse Data Collector for tickers: {self.tickers}")
        
        # Start WebSocket to receive raw bars
        ws_started = self.polygon_service.start_ws_aggregates(
            tickers=self.tickers,
            on_bar=self._on_raw_bar_received
        )
        
        if ws_started:
            self.started = True
            logger.info("✅ Market Pulse Data Collector started - collecting raw data to S3")
        else:
            logger.error("❌ Failed to start WebSocket - data collection disabled")
    
    def stop(self):
        """Stop data collection"""
        if not self.started:
            return
        
        # Flush any in‑memory aggregation state before stopping
        try:
            self._flush_all_aggregated_bars()
        except Exception as e:
            logger.warning(f"Error flushing aggregated bars on stop: {e}", exc_info=True)
        
        self.polygon_service.stop_ws()
        self.started = False
        logger.info(f"Data Collector stopped. Total bars collected: {self.bars_collected}")
    
    def _on_raw_bar_received(self, ticker: str, bar: Dict[str, Any]):
        """
        Callback when raw bar data is received from WebSocket
        Aggregates incoming 1m bars into 5m bars and stores only
        the aggregated 5m bars to S3 to reduce object count.
        """
        try:
            success = self._aggregate_and_store_5m_bar(ticker, bar)
            
            if success:
                self.bars_collected += 1
                self.last_bar_time = datetime.now(timezone.utc)
                
                if self.bars_collected % 10 == 0:  # Log every 10 bars
                    logger.debug(f"Collected {self.bars_collected} bars (latest: {ticker} at {bar.get('timestamp')})")
            else:
                logger.warning(f"Failed to store raw bar for {ticker}")
                
        except Exception as e:
            logger.error(f"Error processing raw bar: {e}", exc_info=True)
    
    def _get_bucket_start(self, dt: datetime) -> datetime:
        """
        Floor a datetime to the start of its 5‑minute bucket.
        """
        minute_bucket = (dt.minute // self.bar_interval_minutes) * self.bar_interval_minutes
        return dt.replace(minute=minute_bucket, second=0, microsecond=0)
    
    def _aggregate_and_store_5m_bar(self, ticker: str, bar: Dict[str, Any]) -> bool:
        """
        Aggregate incoming 1m bar into a 5m bar.
        We keep one in‑memory bucket per ticker and flush it to S3
        when we see a bar from the next 5‑minute window.
        """
        # Parse timestamp from bar
        timestamp = bar.get("timestamp")
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif hasattr(timestamp, "isoformat"):
            dt = timestamp
        else:
            dt = datetime.now(timezone.utc)
        
        bucket_start = self._get_bucket_start(dt)
        state = self._agg_state.get(ticker)
        
        # If we have an existing bucket and the new bar belongs to a later bucket,
        # flush the previous 5m bar to S3.
        if state and state.get("bucket_start") != bucket_start:
            self._flush_aggregated_bar(ticker, state)
            state = None
        
        # Initialize state for this ticker if needed
        if not state:
            state = {
                "bucket_start": bucket_start,
                "open": bar.get("open", 0),
                "high": bar.get("high", 0),
                "low": bar.get("low", 0),
                "close": bar.get("close", 0),
                "volume": bar.get("volume", 0) or 0,
                # For VWAP we keep numerator and denominator separately
                "vwap_numerator": (bar.get("vwap", 0) or 0) * (bar.get("volume", 0) or 0),
                "vwap_denominator": bar.get("volume", 0) or 0,
                "last_timestamp": dt,
            }
            self._agg_state[ticker] = state
        else:
            # Update existing 5m bucket with this new 1m bar
            high = bar.get("high", 0)
            low = bar.get("low", 0)
            close = bar.get("close", 0)
            volume = bar.get("volume", 0) or 0
            vwap = bar.get("vwap", 0) or 0
            
            state["high"] = max(state.get("high", high), high)
            # If low 尚未初始化，使用当前 low
            if state.get("low") is None:
                state["low"] = low
            else:
                state["low"] = min(state.get("low", low), low)
            state["close"] = close
            state["volume"] = (state.get("volume", 0) or 0) + volume
            state["vwap_numerator"] = state.get("vwap_numerator", 0) + vwap * volume
            state["vwap_denominator"] = state.get("vwap_denominator", 0) + volume
            state["last_timestamp"] = dt
        
        return True
    
    def _flush_aggregated_bar(self, ticker: str, state: Dict[str, Any]) -> None:
        """
        Flush a completed 5m aggregated bar to S3 using the same raw‑data schema.
        """
        if not state:
            return
        
        total_volume = state.get("volume", 0) or 0
        vwap_den = state.get("vwap_denominator", 0) or 0
        if vwap_den > 0:
            vwap_value = state.get("vwap_numerator", 0) / vwap_den
        else:
            vwap_value = 0
        
        # Use the end of the 5m window as the timestamp for the stored bar
        bucket_start: datetime = state.get("bucket_start")
        end_dt = bucket_start + timedelta(minutes=self.bar_interval_minutes)
        timestamp_str = end_dt.isoformat().replace("+00:00", "Z")
        
        raw_data = {
            "source": "polygon_websocket_5m_agg",
            "ticker": ticker,
            "timestamp": timestamp_str,
            "bar_data": {
                "open": state.get("open"),
                "high": state.get("high"),
                "low": state.get("low"),
                "close": state.get("close"),
                "volume": total_volume,
                "vwap": vwap_value,
            },
            "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        
        self._store_raw_bar(raw_data)
    
    def _flush_all_aggregated_bars(self) -> None:
        """
        Flush all in‑memory 5m bars (called on shutdown).
        """
        for ticker, state in list(self._agg_state.items()):
            try:
                self._flush_aggregated_bar(ticker, state)
            except Exception as e:
                logger.warning(f"Error flushing aggregated bar for {ticker}: {e}", exc_info=True)
        self._agg_state.clear()
    
    def _store_raw_bar(self, raw_data: Dict[str, Any]) -> bool:
        """
        Store raw bar data to S3
        Path: raw-data/YYYY-MM-DD/ticker/timestamp.json
        """
        try:
            # Parse timestamp
            timestamp = raw_data.get('timestamp')
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif hasattr(timestamp, 'isoformat'):
                dt = timestamp
            else:
                dt = datetime.now(timezone.utc)
            
            date_str = dt.strftime("%Y-%m-%d")
            ticker = raw_data.get('ticker', 'UNKNOWN')
            
            # Create S3 key: raw-data/YYYY-MM-DD/ticker/timestamp.json
            timestamp_key = dt.isoformat().replace(':', '-').replace('.', '-').replace('+00:00', 'Z')
            s3_key = f"raw-data/{date_str}/{ticker}/{timestamp_key}.json"
            
            # Store to S3
            if self.aws_storage.s3_client and self.aws_storage.s3_bucket:
                self.aws_storage.s3_client.put_object(
                    Bucket=self.aws_storage.s3_bucket,
                    Key=s3_key,
                    Body=json.dumps(raw_data, default=str, ensure_ascii=False),
                    ContentType='application/json'
                )
                return True
            else:
                logger.warning("S3 client not initialized - raw data not stored")
                return False
                
        except Exception as e:
            logger.error(f"Error storing raw bar to S3: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            "started": self.started,
            "bars_collected": self.bars_collected,
            "last_bar_time": self.last_bar_time.isoformat() if self.last_bar_time else None,
            "tickers": self.tickers,
            "websocket_connected": self.polygon_service.ws_connected if self.polygon_service else False
        }
