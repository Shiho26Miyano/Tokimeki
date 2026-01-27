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
from datetime import datetime, timezone
from typing import Dict, Any, Optional
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
        
        self.polygon_service.stop_ws()
        self.started = False
        logger.info(f"Data Collector stopped. Total bars collected: {self.bars_collected}")
    
    def _on_raw_bar_received(self, ticker: str, bar: Dict[str, Any]):
        """
        Callback when raw bar data is received from WebSocket
        Stores raw data directly to S3 - NO computation here
        """
        try:
            # Prepare raw data document
            raw_data = {
                "source": "polygon_websocket",
                "ticker": ticker,
                "timestamp": bar.get('timestamp'),
                "bar_data": {
                    "open": bar.get('open'),
                    "high": bar.get('high'),
                    "low": bar.get('low'),
                    "close": bar.get('close'),
                    "volume": bar.get('volume'),
                    "vwap": bar.get('vwap', 0)
                },
                "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
            
            # Store raw bar to S3
            success = self._store_raw_bar(raw_data)
            
            if success:
                self.bars_collected += 1
                self.last_bar_time = datetime.now(timezone.utc)
                
                if self.bars_collected % 10 == 0:  # Log every 10 bars
                    logger.debug(f"Collected {self.bars_collected} bars (latest: {ticker} at {bar.get('timestamp')})")
            else:
                logger.warning(f"Failed to store raw bar for {ticker}")
                
        except Exception as e:
            logger.error(f"Error processing raw bar: {e}", exc_info=True)
    
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
