"""
Market Pulse Service (v3 - Minimal Design)

Layer 3: API + Service Layer
职责: 数据采集协调 + 读取处理结果
技术: Python Services

组件:
- DataCollector (Layer 1): 数据采集
- AWSStorageService (Layer 2): S3 存储

数据流:
1. Data Collector: WebSocket → Raw bars → S3 (raw-data/)
2. AWS Agent: Reads raw-data/ → Computes pulse → Stores to processed-data/
3. Service: Reads processed-data/ → Returns to dashboard

设计原则: 删除所有不必要的部分，只保留核心功能
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

try:
    from botocore.exceptions import ClientError
except ImportError:
    ClientError = None

from app.services.marketpulse.data_collector import MarketPulseDataCollector
from app.services.marketpulse.aws_storage import AWSStorageService

logger = logging.getLogger(__name__)


class MarketPulseService:
    """
    Market Pulse Service (v3 - Minimal)
    
    Core responsibilities:
    - ✅ Collect raw market data → S3
    - ✅ Read agent-processed results from S3
    
    Deleted (v3):
    - ❌ Fallback calculator (Agent always available)
    - ❌ Historical data query
    - ❌ Daily summary
    - ❌ Insights
    - ❌ Collection stats
    """
    
    def __init__(
        self,
        polygon_api_key: str = None,
        s3_bucket: str = None,
        tickers: List[str] = None,
        use_delayed_ws: bool = None
    ):
        # Data collector: collects raw data
        # Default to 10 supported tickers for dual signal architecture
        self.data_collector = MarketPulseDataCollector(
            polygon_api_key=polygon_api_key,
            s3_bucket=s3_bucket,
            tickers=tickers or ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'GOOGL', 'JPM', 'XOM', 'SPY'],
            use_delayed_ws=use_delayed_ws
        )
        
        # Storage service: for reading processed data
        self.aws_storage = AWSStorageService(s3_bucket=s3_bucket)
        
        self.started = False
    
    def start(self):
        """
        Start the data collection service
        Only collects raw data - computation is done by AWS Agent
        """
        if self.started:
            logger.warning("PulseService already started")
            return
        
        # Start data collector (WebSocket → S3)
        self.data_collector.start()
        self.started = True
        
        logger.info("✅ Market Pulse Service started - collecting raw data to S3")
        logger.info("   → AWS Agent will process raw data and compute pulse")
    
    def stop(self):
        """Stop data collection"""
        if not self.started:
            return
        
        self.data_collector.stop()
        self.started = False
        logger.info("Market Pulse Service stopped")
    
    async def calculate_current_pulse(self, ticker: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current pulse (from agent-processed data)
        Returns latest event or empty pulse if no data available
        
        Args:
            ticker: Optional ticker symbol to filter by (e.g., 'SPY', 'QQQ')
        """
        try:
            events = self._get_today_pulse_events(ticker=ticker)
            
            if events:
                latest = events[-1]
                logger.debug(f"Using agent-processed pulse: {latest.get('timestamp')} for ticker: {ticker or 'ALL'}")
                return latest
            
            # No data available - return empty pulse
            return {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "ticker": ticker or "MARKET",
                "stress": 0.0,
                "regime": "unknown",
                "velocity": 0.0,
                "volume_surge": {"surge_ratio": 1.0, "is_surge": False, "magnitude": "normal"},
                "volatility_burst": {"volatility": 0.0, "is_burst": False, "magnitude": "normal"},
                "breadth": {"breadth": "neutral"}
            }
            
        except Exception as e:
            logger.error(f"Error getting current pulse: {e}")
            raise
    
    def get_today_events(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get today's pulse events (from agent-processed data)
        Reads from: processed-data/YYYY-MM-DD/pulse-events.json
        """
        return self._get_today_pulse_events(ticker=ticker)
    
    def _get_today_pulse_events(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Internal method: Read today's pulse events from S3
        Merged from AgentReader (v3 simplification)
        """
        try:
            today = datetime.now(timezone.utc).date()
            date_str = today.isoformat()
            s3_key = f"processed-data/{date_str}/pulse-events.json"
            
            if not self.aws_storage.s3_client or not self.aws_storage.s3_bucket:
                logger.warning("S3 client not initialized")
                return []
            
            try:
                response = self.aws_storage.s3_client.get_object(
                    Bucket=self.aws_storage.s3_bucket,
                    Key=s3_key
                )
                
                content = response['Body'].read().decode('utf-8')
                data = json.loads(content)
                
                events = data.get('events', [])
                
                # Filter by ticker if specified
                if ticker:
                    events = [e for e in events if e.get('ticker') == ticker]
                
                # Sort by timestamp
                events.sort(key=lambda x: x.get('timestamp', ''))
                
                logger.debug(f"Retrieved {len(events)} pulse events")
                return events
                
            except Exception as e:
                if ClientError and isinstance(e, ClientError):
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code == 'NoSuchKey':
                        logger.debug(f"No agent-processed data found for {date_str}")
                        return []
                logger.error(f"Error reading pulse events: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting today's pulse events: {e}")
            return []
    
    async def close(self):
        """Close services"""
        self.stop()
