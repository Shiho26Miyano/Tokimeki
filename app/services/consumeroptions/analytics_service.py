"""
Consumer Options Analytics Service
Handles call/put ratios, IV analysis, unusual activity detection, and technical analysis
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from statistics import median
import asyncio

from app.models.options_models import (
    OptionContract, CallPutRatios, IVTermPoint, UnusualActivity, 
    UnderlyingData, ContractType
)

logger = logging.getLogger(__name__)

class ConsumerOptionsAnalyticsService:
    """Service for options analytics and sentiment analysis"""
    
    def __init__(self):
        # Historical data cache for unusual activity detection
        self.historical_cache = {}
        
        # Thresholds for unusual activity
        self.unusual_thresholds = {
            "volume_multiplier": 3.0,      # 3x average volume
            "oi_multiplier": 2.0,          # 2x average OI change
            "iv_percentile": 95,           # 95th percentile IV
            "min_volume": 50,              # Minimum volume to consider
            "min_oi": 100,                 # Minimum OI to consider
            "lookback_days": 20            # Days for historical average
        }
    
    def calculate_call_put_ratios(self, contracts: List[OptionContract], ticker: str) -> CallPutRatios:
        """
        Calculate call/put volume and open interest ratios
        
        Args:
            contracts: List of option contracts
            ticker: Underlying ticker
            
        Returns:
            CallPutRatios object with analysis
        """
        try:
            # Separate calls and puts
            calls = [c for c in contracts if c.type == ContractType.CALL]
            puts = [c for c in contracts if c.type == ContractType.PUT]
            
            logger.info(f"Calculating ratios for {ticker}: {len(calls)} calls, {len(puts)} puts")
            
            # Calculate totals with better error handling
            call_volume = sum(c.day_volume or 0 for c in calls)
            put_volume = sum(c.day_volume or 0 for c in puts)
            call_oi = sum(c.day_oi or 0 for c in calls)
            put_oi = sum(c.day_oi or 0 for c in puts)
            
            logger.info(f"Volume totals - Calls: {call_volume}, Puts: {put_volume}")
            logger.info(f"OI totals - Calls: {call_oi}, Puts: {put_oi}")
            
            # Calculate ratios with proper handling of zero denominators
            volume_ratio = None
            if put_volume > 0:
                volume_ratio = round(call_volume / put_volume, 3)
            elif call_volume > 0:
                volume_ratio = float('inf')  # All calls, no puts
            
            oi_ratio = None
            if put_oi > 0:
                oi_ratio = round(call_oi / put_oi, 3)
            elif call_oi > 0:
                oi_ratio = float('inf')  # All calls, no puts
            
            # Determine sentiment with better logic
            sentiment = "Neutral"
            confidence = 0.5
            
            if volume_ratio is not None and volume_ratio != float('inf'):
                if volume_ratio > 1.5:
                    sentiment = "Bullish"
                    confidence = min(0.95, 0.6 + (volume_ratio - 1.0) * 0.15)
                elif volume_ratio > 1.2:
                    sentiment = "Bullish"
                    confidence = min(0.8, 0.5 + (volume_ratio - 1.0) * 0.2)
                elif volume_ratio < 0.6:
                    sentiment = "Bearish"
                    confidence = min(0.95, 0.6 + (1.0 - volume_ratio) * 0.2)
                elif volume_ratio < 0.8:
                    sentiment = "Bearish"
                    confidence = min(0.8, 0.5 + (1.0 - volume_ratio) * 0.15)
            elif volume_ratio == float('inf'):
                sentiment = "Bullish"
                confidence = 0.9
            
            # Also consider OI ratio for sentiment
            if oi_ratio is not None and oi_ratio != float('inf'):
                if oi_ratio > 1.5 and sentiment != "Bearish":
                    sentiment = "Bullish"
                    confidence = min(0.95, confidence + 0.1)
                elif oi_ratio < 0.6 and sentiment != "Bullish":
                    sentiment = "Bearish"
                    confidence = min(0.95, confidence + 0.1)
            
            # Calculate median IV across all contracts with better validation
            all_iv_values = []
            for c in contracts:
                iv = c.implied_volatility
                if iv is not None and isinstance(iv, (int, float)) and 0.01 <= iv <= 5.0:
                    all_iv_values.append(iv)
            
            median_iv = median(all_iv_values) if len(all_iv_values) > 0 else None
            
            logger.info(f"Calculated median IV: {median_iv:.2%} from {len(all_iv_values)} valid contracts out of {len(contracts)} total" if median_iv else f"No valid IV data found from {len(contracts)} contracts")
            
            return CallPutRatios(
                ticker=ticker,
                analysis_date=date.today(),
                call_volume=call_volume,
                put_volume=put_volume,
                volume_ratio=volume_ratio if volume_ratio != float('inf') else None,
                call_oi=call_oi,
                put_oi=put_oi,
                oi_ratio=oi_ratio if oi_ratio != float('inf') else None,
                sentiment=sentiment,
                confidence=round(confidence, 3),
                median_iv=round(median_iv, 4) if median_iv else None
            )
            
        except Exception as e:
            logger.error(f"Error calculating call/put ratios for {ticker}: {str(e)}")
            raise
    
    def calculate_iv_term_structure(self, contracts: List[OptionContract]) -> List[IVTermPoint]:
        """
        Calculate implied volatility term structure
        
        Args:
            contracts: List of option contracts
            
        Returns:
            List of IVTermPoint objects sorted by expiry
        """
        try:
            logger.info(f"Calculating IV term structure from {len(contracts)} contracts")
            
            # Group contracts by expiry and collect IV values
            expiry_groups = {}
            total_iv_contracts = 0
            
            for contract in contracts:
                iv = contract.implied_volatility
                if iv is not None and isinstance(iv, (int, float)) and 0.01 <= iv <= 5.0:  # Filter out unrealistic IV values
                    expiry = contract.expiry
                    if expiry not in expiry_groups:
                        expiry_groups[expiry] = []
                    expiry_groups[expiry].append(iv)
                    total_iv_contracts += 1
            
            logger.info(f"Found {total_iv_contracts} contracts with valid IV across {len(expiry_groups)} expiries")
            
            # Calculate median IV for each expiry
            iv_points = []
            today = date.today()
            
            for expiry, iv_values in expiry_groups.items():
                if len(iv_values) >= 1:  # Reduced requirement to at least 1 contract
                    days_to_expiry = (expiry - today).days
                    
                    # Only include future expiries
                    if days_to_expiry > 0:
                        median_iv = median(iv_values) if len(iv_values) > 1 else iv_values[0]
                        
                        iv_point = IVTermPoint(
                            expiry=expiry,
                            days_to_expiry=days_to_expiry,
                            median_iv=round(median_iv, 4),
                            contract_count=len(iv_values)
                        )
                        iv_points.append(iv_point)
                        
                        logger.debug(f"IV point: {expiry} ({days_to_expiry}d) - {median_iv:.2%} from {len(iv_values)} contracts")
            
            # Sort by expiry
            iv_points.sort(key=lambda x: x.expiry)
            
            logger.info(f"Calculated IV term structure with {len(iv_points)} points")
            
            # If no IV data available, create a placeholder
            if not iv_points:
                logger.warning("No valid IV data found, creating placeholder")
                # Create a single point with estimated IV
                future_expiry = today + timedelta(days=30)
                iv_points.append(IVTermPoint(
                    expiry=future_expiry,
                    days_to_expiry=30,
                    median_iv=0.25,  # Default 25% IV
                    contract_count=0
                ))
            
            return iv_points
            
        except Exception as e:
            logger.error(f"Error calculating IV term structure: {str(e)}")
            # Return empty list instead of raising to prevent dashboard failure
            return []
    
    def detect_unusual_activity(self, contracts: List[OptionContract], ticker: str) -> List[UnusualActivity]:
        """
        Detect unusual activity in option contracts
        
        Args:
            contracts: List of option contracts
            ticker: Underlying ticker
            
        Returns:
            List of UnusualActivity objects
        """
        try:
            unusual_contracts = []
            
            for contract in contracts:
                # Check volume threshold
                if (contract.day_volume and 
                    contract.day_volume >= self.unusual_thresholds["min_volume"]):
                    
                    # For demo purposes, use simple heuristics
                    # In production, this would use historical data
                    avg_volume = contract.day_volume * 0.3  # Assume current is 3x average
                    z_score = 3.0  # Simplified z-score
                    
                    if contract.day_volume >= avg_volume * self.unusual_thresholds["volume_multiplier"]:
                        unusual = UnusualActivity(
                            contract=contract.contract,
                            trigger_type="Volume",
                            current_value=float(contract.day_volume),
                            average_value=avg_volume,
                            z_score=z_score,
                            threshold=self.unusual_thresholds["volume_multiplier"],
                            timestamp=datetime.now()
                        )
                        unusual_contracts.append(unusual)
                
                # Check OI threshold
                if (contract.day_oi and 
                    contract.day_oi >= self.unusual_thresholds["min_oi"]):
                    
                    avg_oi = contract.day_oi * 0.5  # Assume current is 2x average
                    z_score = 2.0
                    
                    if contract.day_oi >= avg_oi * self.unusual_thresholds["oi_multiplier"]:
                        unusual = UnusualActivity(
                            contract=contract.contract,
                            trigger_type="Open Interest",
                            current_value=float(contract.day_oi),
                            average_value=avg_oi,
                            z_score=z_score,
                            threshold=self.unusual_thresholds["oi_multiplier"],
                            timestamp=datetime.now()
                        )
                        unusual_contracts.append(unusual)
                
                # Check IV threshold (high IV percentile)
                if (contract.implied_volatility and 
                    contract.implied_volatility > 0.4):  # Simple high IV threshold
                    
                    unusual = UnusualActivity(
                        contract=contract.contract,
                        trigger_type="Implied Volatility",
                        current_value=contract.implied_volatility,
                        average_value=0.25,  # Assumed average IV
                        z_score=2.5,
                        threshold=0.4,
                        timestamp=datetime.now()
                    )
                    unusual_contracts.append(unusual)
            
            # Sort by z-score (highest first)
            unusual_contracts.sort(key=lambda x: x.z_score, reverse=True)
            
            logger.info(f"Detected {len(unusual_contracts)} unusual activities for {ticker}")
            return unusual_contracts
            
        except Exception as e:
            logger.error(f"Error detecting unusual activity for {ticker}: {str(e)}")
            raise
    
    def calculate_technical_indicators(self, bars: List[UnderlyingData]) -> List[UnderlyingData]:
        """
        Calculate technical indicators for underlying data
        
        Args:
            bars: List of UnderlyingData objects
            
        Returns:
            List of UnderlyingData with technical indicators added
        """
        try:
            if len(bars) < 50:
                logger.warning("Insufficient data for technical indicators")
                return bars
            
            # Convert to DataFrame for easier calculation
            df = pd.DataFrame([{
                'date': bar.bar_date,
                'close': bar.close,
                'high': bar.high,
                'low': bar.low,
                'volume': bar.volume
            } for bar in bars])
            
            df = df.sort_values('date')
            
            # Calculate SMAs
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # Calculate RSI
            df['rsi_14'] = self._calculate_rsi(df['close'], 14)
            
            # Update bars with indicators
            updated_bars = []
            for i, bar in enumerate(bars):
                if i < len(df):
                    row = df.iloc[i]
                    bar.sma_20 = row.get('sma_20')
                    bar.sma_50 = row.get('sma_50')
                    bar.rsi_14 = row.get('rsi_14')
                
                updated_bars.append(bar)
            
            logger.info(f"Calculated technical indicators for {len(updated_bars)} bars")
            return updated_bars
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return bars  # Return original bars on error
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            prices: Series of closing prices
            window: RSI window (default 14)
            
        Returns:
            Series of RSI values
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([None] * len(prices))
    
    def get_market_sentiment_summary(self, all_ratios: Dict[str, CallPutRatios]) -> Dict[str, Any]:
        """
        Generate overall market sentiment summary
        
        Args:
            all_ratios: Dictionary of CallPutRatios by ticker
            
        Returns:
            Market sentiment summary
        """
        try:
            sentiments = [ratio.sentiment for ratio in all_ratios.values()]
            confidences = [ratio.confidence for ratio in all_ratios.values()]
            
            # Count sentiments
            bullish_count = sentiments.count("Bullish")
            bearish_count = sentiments.count("Bearish")
            neutral_count = sentiments.count("Neutral")
            
            # Overall sentiment
            if bullish_count > bearish_count:
                overall_sentiment = "Bullish"
            elif bearish_count > bullish_count:
                overall_sentiment = "Bearish"
            else:
                overall_sentiment = "Neutral"
            
            # Average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            return {
                "overall_sentiment": overall_sentiment,
                "confidence": avg_confidence,
                "bullish_tickers": bullish_count,
                "bearish_tickers": bearish_count,
                "neutral_tickers": neutral_count,
                "total_tickers": len(all_ratios)
            }
            
        except Exception as e:
            logger.error(f"Error generating market sentiment summary: {str(e)}")
            return {
                "overall_sentiment": "Unknown",
                "confidence": 0.0,
                "bullish_tickers": 0,
                "bearish_tickers": 0,
                "neutral_tickers": 0,
                "total_tickers": 0
            }
    
    def calculate_oi_change_heatmap_data(self, contracts: List[OptionContract]) -> Dict[str, Any]:
        """
        Calculate Open Interest Change heatmap data
        
        Args:
            contracts: List of option contracts
            
        Returns:
            Dictionary with heatmap data for frontend
        """
        try:
            if not contracts:
                logger.warning("No contracts provided for OI heatmap calculation")
                return {"expiries": [], "strikes": [], "delta_oi": []}
            
            logger.info(f"Calculating OI heatmap for {len(contracts)} contracts")
            
            # Create DataFrame for easier manipulation
            df = pd.DataFrame([{
                'expiry': pd.to_datetime(c.expiry) if isinstance(c.expiry, str) else c.expiry,
                'strike': c.strike,
                'type': c.type.value,
                'oi_today': c.day_oi or 0,
                'delta': c.delta or 0,
                'volume': c.day_volume or 0
            } for c in contracts])
            
            logger.info(f"Created DataFrame with {len(df)} rows")
            
            # Get unique expiries and strikes
            expiries = sorted(df["expiry"].unique())
            strikes = sorted(df["strike"].unique())
            
            logger.info(f"Found {len(expiries)} expiries and {len(strikes)} strikes")
            
            if len(expiries) == 0 or len(strikes) == 0:
                logger.warning("No valid expiries or strikes found")
                return {"expiries": [], "strikes": [], "delta_oi": []}
            
            # Create pivot tables for today's OI
            try:
                grid_today = df.pivot_table(
                    index="expiry", columns="strike",
                    values="oi_today", aggfunc="sum"
                ).reindex(index=expiries, columns=strikes).fillna(0)
                
                logger.info(f"Created grid_today with shape: {grid_today.shape}")
            except Exception as e:
                logger.error(f"Error creating pivot table: {str(e)}")
                return {"expiries": [], "strikes": [], "delta_oi": []}
            
            # For demo purposes, simulate yesterday's OI with some variation
            # In production, this would come from historical data
            np.random.seed(42)  # For consistent demo data
            variation_factor = np.random.uniform(0.7, 1.3, grid_today.shape)
            grid_yesterday = (grid_today * variation_factor).round().astype(int)
            
            # Calculate delta OI
            delta_oi = grid_today - grid_yesterday
            
            # Convert to list format for frontend
            heatmap_data = {
                "expiries": [expiry.strftime('%m-%d') for expiry in expiries],
                "strikes": list(strikes),
                "delta_oi": delta_oi.values.tolist(),
                "min_delta": float(delta_oi.min().min()),
                "max_delta": float(delta_oi.max().max())
            }
            
            logger.info(f"Calculated OI change heatmap with {len(expiries)} expiries and {len(strikes)} strikes")
            logger.info(f"Heatmap data keys: {list(heatmap_data.keys())}")
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Error calculating OI change heatmap: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"expiries": [], "strikes": [], "delta_oi": []}
    
    def calculate_delta_distribution_data(self, contracts: List[OptionContract]) -> Dict[str, Any]:
        """
        Calculate Delta Distribution histogram data
        
        Args:
            contracts: List of option contracts
            
        Returns:
            Dictionary with histogram data for frontend
        """
        try:
            if not contracts:
                return {"bins": [], "counts": [], "bin_centers": []}
            
            # Create DataFrame for easier manipulation
            df = pd.DataFrame([{
                'delta': c.delta or 0,
                'volume': c.day_volume or 1  # Use volume as weight, default to 1
            } for c in contracts])
            
            # Filter valid deltas and clip to [-1, 1] range
            valid_deltas = df[df['delta'].notna() & (df['delta'] >= -1) & (df['delta'] <= 1)]
            
            if len(valid_deltas) == 0:
                return {"bins": [], "counts": [], "bin_centers": []}
            
            # Create histogram with 21 bins from -1 to 1
            bins = np.linspace(-1, 1, 21)
            counts, bin_edges = np.histogram(
                valid_deltas['delta'], 
                bins=bins, 
                weights=valid_deltas['volume']
            )
            
            # Calculate bin centers for x-axis labels
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            histogram_data = {
                "bins": bins.tolist(),
                "counts": counts.tolist(),
                "bin_centers": bin_centers.tolist(),
                "max_count": int(counts.max()) if len(counts) > 0 else 0
            }
            
            logger.info(f"Calculated delta distribution with {len(counts)} bins, max count: {histogram_data['max_count']}")
            return histogram_data
            
        except Exception as e:
            logger.error(f"Error calculating delta distribution: {str(e)}")
            return {"bins": [], "counts": [], "bin_centers": []}

    def filter_contracts_by_criteria(self, contracts: List[OptionContract], 
                                   criteria: Dict[str, Any]) -> List[OptionContract]:
        """
        Filter contracts based on various criteria
        
        Args:
            contracts: List of option contracts
            criteria: Filtering criteria
            
        Returns:
            Filtered list of contracts
        """
        try:
            filtered = contracts.copy()
            
            # Filter by expiry range
            if "expiry_start" in criteria and "expiry_end" in criteria:
                start_date = datetime.strptime(criteria["expiry_start"], "%Y-%m-%d").date()
                end_date = datetime.strptime(criteria["expiry_end"], "%Y-%m-%d").date()
                filtered = [c for c in filtered if start_date <= c.expiry <= end_date]
            
            # Filter by strike range
            if "strike_min" in criteria and "strike_max" in criteria:
                strike_min = float(criteria["strike_min"])
                strike_max = float(criteria["strike_max"])
                filtered = [c for c in filtered if strike_min <= c.strike <= strike_max]
            
            # Filter by contract type
            if "contract_type" in criteria:
                contract_type = ContractType(criteria["contract_type"])
                filtered = [c for c in filtered if c.type == contract_type]
            
            # Filter by minimum volume
            if "min_volume" in criteria:
                min_vol = int(criteria["min_volume"])
                filtered = [c for c in filtered if (c.day_volume or 0) >= min_vol]
            
            # Filter by minimum OI
            if "min_oi" in criteria:
                min_oi = int(criteria["min_oi"])
                filtered = [c for c in filtered if (c.day_oi or 0) >= min_oi]
            
            # Filter unusual only
            if criteria.get("unusual_only", False):
                filtered = [c for c in filtered if c.is_unusual]
            
            logger.info(f"Filtered {len(contracts)} contracts to {len(filtered)} based on criteria")
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering contracts: {str(e)}")
            return contracts  # Return original on error
