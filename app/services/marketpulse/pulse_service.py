"""
Market Pulse Service
Main service that orchestrates pulse calculation and storage
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from app.services.marketpulse.polygon_service import MarketPulsePolygonService
from app.services.marketpulse.pulse_calculator import PulseCalculator
from app.services.marketpulse.aws_storage import AWSStorageService

logger = logging.getLogger(__name__)


class MarketPulseService:
    """Main service for Market Pulse calculation and management"""
    
    def __init__(
        self,
        polygon_api_key: str = None,
        s3_bucket: str = None,
        dynamodb_table: str = None
    ):
        self.polygon_service = MarketPulsePolygonService(polygon_api_key)
        self.pulse_calculator = PulseCalculator()
        self.aws_storage = AWSStorageService(s3_bucket, dynamodb_table)
        
        # Tracked tickers for pulse calculation
        self.tracked_tickers = ['SPY', 'QQQ', 'DIA', 'IWM']  # Major indices
    
    async def calculate_current_pulse(self) -> Dict[str, Any]:
        """
        Calculate current market pulse
        Returns pulse event with all indicators
        """
        try:
            # Get market snapshot
            snapshot = await self.polygon_service.get_market_snapshot(self.tracked_tickers)
            
            if not snapshot:
                raise ValueError("No market data available")
            
            # Get historical data for calculations
            ticker_data = {}
            for ticker in self.tracked_tickers:
                if ticker in snapshot:
                    # Get recent aggregates for velocity/volatility
                    aggs = await self.polygon_service.get_aggregates(
                        ticker,
                        multiplier=5,
                        timespan="minute",
                        from_date=datetime.now().date() - timedelta(days=1),
                        to_date=datetime.now().date()
                    )
                    
                    prices = [agg['close'] for agg in aggs]
                    volumes = [agg['volume'] for agg in aggs]
                    
                    ticker_data[ticker] = {
                        'ticker': ticker,
                        'prices': prices,
                        'volumes': volumes,
                        'current_price': snapshot[ticker]['price'],
                        'current_volume': snapshot[ticker]['volume']
                    }
            
            # Calculate breadth (advancing vs declining)
            grouped_daily = await self.polygon_service.get_grouped_daily()
            breadth = self._calculate_market_breadth(grouped_daily)
            
            # Calculate pulse for primary ticker (SPY as market proxy)
            primary_ticker = 'SPY'
            if primary_ticker in ticker_data:
                pulse_event = self.pulse_calculator.calculate_pulse_event(
                    ticker_data[primary_ticker],
                    {'breadth': breadth},
                    datetime.now()
                )
                
                # Store to AWS
                self.aws_storage.store_pulse_event(pulse_event)
                
                return pulse_event
            
            raise ValueError("Primary ticker data not available")
            
        except Exception as e:
            logger.error(f"Error calculating pulse: {e}")
            raise
    
    def _calculate_market_breadth(self, grouped_daily: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate market breadth from grouped daily data"""
        if not grouped_daily.get('results'):
            return {
                'advance_decline_ratio': 0.0,
                'advancing_pct': 0.0,
                'declining_pct': 0.0,
                'breadth': 'neutral'
            }
        
        results = grouped_daily['results']
        if len(results) < 2:
            return {
                'advance_decline_ratio': 0.0,
                'advancing_pct': 50.0,
                'declining_pct': 50.0,
                'breadth': 'neutral'
            }
        
        # Calculate advancing/declining
        # For simplicity, compare current close to previous day's close
        # In production, you'd compare to previous day's data
        advancing = 0
        declining = 0
        
        # Sort by ticker to ensure consistent comparison
        sorted_results = sorted(results, key=lambda x: x.get('ticker', ''))
        
        # Simple approach: count positive vs negative changes
        # In production, compare to actual previous day data
        for result in sorted_results:
            close = result.get('close', 0)
            high = result.get('high', close)
            low = result.get('low', close)
            
            # If high > low significantly, consider it advancing
            if high > low * 1.01:
                advancing += 1
            elif low < high * 0.99:
                declining += 1
        
        return self.pulse_calculator.calculate_breadth(advancing, declining)
    
    async def get_pulse_history(
        self,
        days: int = 7,
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical pulse events"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.aws_storage.get_pulse_events(start_date, end_date, ticker)
    
    async def close(self):
        """Close services"""
        await self.polygon_service.close()

