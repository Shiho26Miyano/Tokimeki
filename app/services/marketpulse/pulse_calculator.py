"""
Market Pulse Calculator

Layer 4: API Layer (Fallback Component)
职责: 当 Agent 数据不可用时，提供实时计算能力（fallback）
技术: Python, statistics, numpy (可选)

注意: 这是 fallback 组件，主要计算由 Layer 3 (Lambda Agent) 完成
仅在以下情况使用:
- Agent 数据尚未生成
- 需要实时计算（不等待 Agent）

扩展点:
- 添加更多指标计算
- 优化计算性能
- 支持更多 ticker
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from statistics import mean, stdev

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class PulseCalculator:
    """Calculate Market Pulse indicators with state management for real-time updates"""
    
    def __init__(self):
        # In-memory state: store recent bars per ticker
        # Format: {ticker: [bar1, bar2, ...]} where bar = {timestamp, open, high, low, close, volume}
        self.ticker_bars = {}
        self.max_bars_per_ticker = 500  # Keep last 500 bars (~8 hours of 1-min data)
        
        # Market breadth state (updated periodically)
        self.market_breadth = {
            'advance_decline_ratio': 0.0,
            'advancing_pct': 50.0,
            'declining_pct': 50.0,
            'breadth': 'neutral'
        }
    
    def on_bar(self, ticker: str, bar: Dict[str, Any]):
        """
        Callback for receiving real-time bar data from WebSocket
        Updates internal state for pulse calculation
        
        Args:
            ticker: Ticker symbol (e.g., "SPY")
            bar: Bar data dict with keys: timestamp, open, high, low, close, volume, vwap
        """
        if ticker not in self.ticker_bars:
            self.ticker_bars[ticker] = []
        
        # Add new bar
        self.ticker_bars[ticker].append(bar)
        
        # Keep only recent bars
        if len(self.ticker_bars[ticker]) > self.max_bars_per_ticker:
            self.ticker_bars[ticker] = self.ticker_bars[ticker][-self.max_bars_per_ticker:]
    
    def update_breadth(self, breadth: Dict[str, Any]):
        """Update market breadth data"""
        self.market_breadth = breadth
    
    def compute_pulse(self, primary_ticker: str = "SPY") -> Optional[Dict[str, Any]]:
        """
        Compute current pulse from accumulated state
        Returns pulse event dict or None if insufficient data
        """
        if primary_ticker not in self.ticker_bars:
            return None
        
        bars = self.ticker_bars[primary_ticker]
        if len(bars) < 5:  # Need at least 5 bars
            return None
        
        # Extract prices and volumes
        prices = [bar['close'] for bar in bars]
        volumes = [bar['volume'] for bar in bars]
        
        # Get current values
        current_price = prices[-1] if prices else 0
        current_volume = volumes[-1] if volumes else 0
        avg_volume = mean(volumes[-20:]) if len(volumes) >= 20 else current_volume
        
        # Calculate indicators
        velocity = self.calculate_price_velocity(prices)
        volume_surge = self.calculate_volume_surge(current_volume, avg_volume)
        volatility_burst = self.calculate_volatility_burst(prices)
        
        # Use stored breadth or default
        breadth = self.market_breadth
        
        # Calculate stress
        stress = self.calculate_stress_index(
            volatility_burst.get('volatility', 0),
            volume_surge.get('surge_ratio', 1.0),
            velocity,
            breadth.get('breadth', 'neutral')
        )
        
        return {
            'price': current_price,
            'volume': current_volume,
            'velocity': velocity,
            'volume_surge': volume_surge,
            'volatility_burst': volatility_burst,
            'breadth': breadth,
            'stress': stress.get('stress_score', 0),
            'regime': stress.get('regime', 'calm')
        }
    
    @staticmethod
    def calculate_price_velocity(prices: List[float], window: int = 5) -> float:
        """
        Calculate price velocity (rate of price change)
        Returns percentage change over window
        """
        if len(prices) < window:
            return 0.0
        
        recent = prices[-window:]
        if recent[0] == 0:
            return 0.0
        
        velocity = ((recent[-1] - recent[0]) / recent[0]) * 100
        return round(velocity, 4)
    
    @staticmethod
    def calculate_volume_surge(
        current_volume: float,
        avg_volume: float,
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        Calculate volume surge indicator
        Returns surge ratio and whether it exceeds threshold
        """
        if avg_volume == 0:
            return {
                'surge_ratio': 0.0,
                'is_surge': False,
                'magnitude': 'normal'
            }
        
        surge_ratio = current_volume / avg_volume
        
        if surge_ratio >= threshold * 2:
            magnitude = 'extreme'
        elif surge_ratio >= threshold:
            magnitude = 'high'
        else:
            magnitude = 'normal'
        
        return {
            'surge_ratio': round(surge_ratio, 2),
            'is_surge': surge_ratio >= threshold,
            'magnitude': magnitude
        }
    
    @staticmethod
    def calculate_volatility_burst(
        prices: List[float],
        window: int = 20
    ) -> Dict[str, Any]:
        """
        Calculate volatility burst (sudden increase in volatility)
        Uses standard deviation of returns
        """
        if len(prices) < window + 1:
            return {
                'volatility': 0.0,
                'is_burst': False,
                'magnitude': 'normal'
            }
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        
        if len(returns) < window:
            return {
                'volatility': 0.0,
                'is_burst': False,
                'magnitude': 'normal'
            }
        
        # Calculate rolling volatility
        recent_returns = returns[-window:]
        current_vol = stdev(recent_returns) if len(recent_returns) > 1 else 0.0
        
        # Compare to historical average
        if len(returns) >= window * 2:
            historical_returns = returns[-window*2:-window]
            historical_vol = stdev(historical_returns) if len(historical_returns) > 1 else 0.0
            
            if historical_vol > 0:
                vol_ratio = current_vol / historical_vol
                
                if vol_ratio >= 2.0:
                    magnitude = 'extreme'
                elif vol_ratio >= 1.5:
                    magnitude = 'high'
                else:
                    magnitude = 'normal'
                
                return {
                    'volatility': round(current_vol * 100, 4),
                    'vol_ratio': round(vol_ratio, 2),
                    'is_burst': vol_ratio >= 1.5,
                    'magnitude': magnitude
                }
        
        return {
            'volatility': round(current_vol * 100, 4),
            'is_burst': False,
            'magnitude': 'normal'
        }
    
    @staticmethod
    def calculate_breadth(
        advancing: int,
        declining: int,
        unchanged: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate market breadth
        Returns advance/decline ratio and breadth indicator
        """
        total = advancing + declining + unchanged
        if total == 0:
            return {
                'advance_decline_ratio': 0.0,
                'advancing_pct': 0.0,
                'declining_pct': 0.0,
                'breadth': 'neutral'
            }
        
        advancing_pct = (advancing / total) * 100
        declining_pct = (declining / total) * 100
        
        if declining == 0:
            advance_decline_ratio = float('inf') if advancing > 0 else 0.0
        else:
            advance_decline_ratio = advancing / declining
        
        # Determine breadth strength
        if advancing_pct >= 70:
            breadth = 'very_strong'
        elif advancing_pct >= 60:
            breadth = 'strong'
        elif advancing_pct >= 50:
            breadth = 'positive'
        elif advancing_pct >= 40:
            breadth = 'negative'
        elif advancing_pct >= 30:
            breadth = 'weak'
        else:
            breadth = 'very_weak'
        
        return {
            'advance_decline_ratio': round(advance_decline_ratio, 2),
            'advancing_pct': round(advancing_pct, 2),
            'declining_pct': round(declining_pct, 2),
            'advancing': advancing,
            'declining': declining,
            'unchanged': unchanged,
            'total': total,
            'breadth': breadth
        }
    
    @staticmethod
    def calculate_stress_index(
        volatility: float,
        volume_surge: float,
        price_velocity: float,
        breadth: str
    ) -> Dict[str, Any]:
        """
        Calculate composite stress index
        Combines multiple indicators into a single stress score
        """
        # Normalize inputs (0-1 scale)
        # Volatility: assume max 10% daily volatility
        vol_score = min(volatility / 10.0, 1.0)
        
        # Volume surge: ratio, cap at 5x
        volume_score = min(volume_surge / 5.0, 1.0)
        
        # Price velocity: use absolute value, cap at 10%
        velocity_score = min(abs(price_velocity) / 10.0, 1.0)
        
        # Breadth: convert to score
        breadth_scores = {
            'very_weak': 1.0,
            'weak': 0.8,
            'negative': 0.6,
            'neutral': 0.5,
            'positive': 0.4,
            'strong': 0.2,
            'very_strong': 0.0
        }
        breadth_score = breadth_scores.get(breadth, 0.5)
        
        # Weighted combination
        stress_score = (
            vol_score * 0.3 +
            volume_score * 0.2 +
            velocity_score * 0.2 +
            breadth_score * 0.3
        )
        
        # Classify stress level
        if stress_score >= 0.8:
            regime = 'extreme_stress'
        elif stress_score >= 0.6:
            regime = 'high_stress'
        elif stress_score >= 0.4:
            regime = 'moderate_stress'
        elif stress_score >= 0.2:
            regime = 'low_stress'
        else:
            regime = 'calm'
        
        return {
            'stress_score': round(stress_score, 3),
            'regime': regime,
            'components': {
                'volatility': round(vol_score, 3),
                'volume': round(volume_score, 3),
                'velocity': round(velocity_score, 3),
                'breadth': round(breadth_score, 3)
            }
        }
    
    @staticmethod
    def calculate_pulse_event(
        ticker_data: Dict[str, Any],
        market_data: Dict[str, Any],
        timestamp: datetime = None
    ) -> Dict[str, Any]:
        """
        Calculate complete pulse event from market data
        Returns pulse event with all indicators
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Extract data
        prices = ticker_data.get('prices', [])
        volumes = ticker_data.get('volumes', [])
        current_price = prices[-1] if prices else 0
        current_volume = volumes[-1] if volumes else 0
        avg_volume = mean(volumes[-20:]) if len(volumes) >= 20 else current_volume
        
        # Calculate indicators
        velocity = PulseCalculator.calculate_price_velocity(prices)
        volume_surge = PulseCalculator.calculate_volume_surge(current_volume, avg_volume)
        volatility_burst = PulseCalculator.calculate_volatility_burst(prices)
        breadth = market_data.get('breadth', {})
        stress = PulseCalculator.calculate_stress_index(
            volatility_burst.get('volatility', 0),
            volume_surge.get('surge_ratio', 1.0),
            velocity,
            breadth.get('breadth', 'neutral')
        )
        
        return {
            'timestamp': timestamp.isoformat(),
            'ticker': ticker_data.get('ticker', 'MARKET'),
            'price': current_price,
            'volume': current_volume,
            'velocity': velocity,
            'volume_surge': volume_surge,
            'volatility_burst': volatility_burst,
            'breadth': breadth,
            'stress': stress.get('stress_score', 0),
            'regime': stress.get('regime', 'calm')
        }

