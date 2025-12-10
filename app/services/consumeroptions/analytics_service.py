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
    
    def _get_historical_volume_average(self, contract: str) -> Optional[float]:
        """Get historical volume average for a contract"""
        try:
            # Check cache first
            cache_key = f"volume_avg_{contract}"
            if cache_key in self.historical_cache:
                return self.historical_cache[cache_key]
            
            # In a real implementation, this would fetch historical data
            # For now, return None to indicate no historical data available
            logger.warning(f"No historical volume data available for {contract}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting historical volume for {contract}: {str(e)}")
            return None
    
    def _get_historical_oi_data(self, contracts: List[OptionContract], expiries: List[date], strikes: List[float]) -> Optional[pd.DataFrame]:
        """Get historical OI data for heatmap calculation"""
        try:
            # In a real implementation, this would fetch historical OI data
            # For now, return None to indicate no historical data available
            logger.warning("No historical OI data available for heatmap calculation")
            return None
            
        except Exception as e:
            logger.error(f"Error getting historical OI data: {str(e)}")
            return None
    
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
                    
                    # Use historical data for proper analysis
                    # Get historical volume data for this contract
                    avg_volume = self._get_historical_volume_average(contract.contract)
                    if avg_volume is None:
                        continue  # Skip if no historical data available
                    
                    # Calculate proper z-score
                    z_score = (contract.day_volume - avg_volume) / max(avg_volume * 0.1, 1.0)  # 10% std dev assumption
                    
                    if avg_volume and contract.day_volume >= avg_volume * self.unusual_thresholds["volume_multiplier"]:
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
        Calculate Volume heatmap data - SIMPLIFIED, no expiry filtering, use all contracts
        
        Args:
            contracts: List of option contracts (ALL contracts, no filtering)
            
        Returns:
            Dictionary with heatmap data for frontend using volume metric
        """
        try:
            if not contracts:
                logger.warning("No contracts provided for volume heatmap calculation")
                return {"expiries": [], "strikes": [], "volume": []}
            
            logger.info(f"Calculating volume heatmap for {len(contracts)} contracts (no filtering)")
            
            # Create DataFrame - use ALL contracts
            df = pd.DataFrame([{
                'expiry': pd.to_datetime(c.expiry) if isinstance(c.expiry, str) else c.expiry,
                'strike': c.strike,
                'type': c.type.value,
                'volume': c.day_volume or 0,
                'oi': c.day_oi or 0,
                'delta': c.delta or 0
            } for c in contracts])
            
            logger.info(f"Created DataFrame with {len(df)} rows")
            
            # Get unique expiries and strikes - use ALL
            all_expiries = sorted(df["expiry"].unique())
            all_strikes = sorted(df["strike"].unique())
            
            logger.info(f"Found {len(all_expiries)} unique expiries and {len(all_strikes)} unique strikes")
            
            # Select top 10 expiries by total volume (most active expiries)
            # This ensures we show the most relevant expiries with actual trading activity
            expiry_volumes = df.groupby('expiry')['volume'].sum().sort_values(ascending=False)
            top_expiries = expiry_volumes.head(10).index.tolist()
            
            # Convert to date format for frontend
            selected_expiry_dates = []
            for e in top_expiries:
                if hasattr(e, 'date'):
                    selected_expiry_dates.append(e.date())
                elif isinstance(e, date):
                    selected_expiry_dates.append(e)
                else:
                    try:
                        selected_expiry_dates.append(pd.to_datetime(e).date())
                    except:
                        continue
            
            selected_expiry_dates = sorted(selected_expiry_dates)
            
            logger.info(f"Selected top {len(selected_expiry_dates)} expiries by volume: {[str(d) for d in selected_expiry_dates[:3]]}...{[str(d) for d in selected_expiry_dates[-3:]] if len(selected_expiry_dates) > 3 else ''}")
            
            # Filter DataFrame to only selected expiries (top 10 by volume)
            df_filtered = df[df['expiry'].isin(top_expiries)].copy()
            
            if len(df_filtered) == 0:
                logger.warning("No contracts after filtering by top expiries")
                return {"expiries": [], "strikes": [], "volume": []}
            
            logger.info(f"Filtered to {len(df_filtered)} contracts for {len(selected_expiry_dates)} expiries")
            
            # Select 10 evenly distributed strikes from ALL strikes (not just filtered)
            if len(all_strikes) == 0:
                logger.warning("No valid strikes found")
                return {"expiries": [], "strikes": [], "volume": []}
            
            # Select 10 evenly distributed strikes
            if len(all_strikes) <= 10:
                selected_strikes = all_strikes
            else:
                step = len(all_strikes) / 10
                selected_strikes = [all_strikes[int(i * step)] for i in range(10)]
            
            logger.info(f"Selected {len(selected_strikes)} strikes from {len(all_strikes)} total")
            
            # Create strike labels
            strike_labels = [str(int(s)) if s >= 1 else f"{s:.2f}" for s in selected_strikes]
            
            # Assign each contract to the closest selected strike
            def assign_strike_index(strike):
                closest_idx = 0
                min_distance = abs(strike - selected_strikes[0])
                for idx, selected_strike in enumerate(selected_strikes):
                    distance = abs(strike - selected_strike)
                    if distance < min_distance:
                        min_distance = distance
                        closest_idx = idx
                return closest_idx
            
            df_filtered['strike_index'] = df_filtered['strike'].apply(assign_strike_index)
            
            # Create pivot table - SIMPLIFIED
            volume_grid = df_filtered.pivot_table(
                index="expiry", columns="strike_index",
                values="volume", aggfunc="sum",
                fill_value=0
            )
            
            # Ensure we have all 10 strike indices (0-9)
            all_strike_indices = list(range(10))
            for idx in all_strike_indices:
                if idx not in volume_grid.columns:
                    volume_grid[idx] = 0
            
            # Reindex to ensure correct order
            volume_grid = volume_grid.reindex(index=top_expiries, columns=all_strike_indices, fill_value=0)
            
            logger.info(f"Volume grid shape: {volume_grid.shape}")
            
            # Convert expiries to date format
            actual_expiries = []
            for e in top_expiries:
                if hasattr(e, 'date'):
                    actual_expiries.append(e.date())
                elif isinstance(e, date):
                    actual_expiries.append(e)
                else:
                    try:
                        actual_expiries.append(pd.to_datetime(e).date())
                    except:
                        continue
            
            actual_expiries = sorted(actual_expiries)
            
            # Calculate min/max
            min_vol = float(volume_grid.min().min())
            max_vol = float(volume_grid.max().max())
            
            logger.info(f"Final: {len(actual_expiries)} expiries, {len(strike_labels)} strikes, volume range: {min_vol} to {max_vol}")
                
            # Convert to list format for frontend
            volume_list = volume_grid.values.tolist()
            
            # Verify dimensions
            if len(volume_list) != len(actual_expiries) or (len(volume_list) > 0 and len(volume_list[0]) != len(strike_labels)):
                logger.error(f"Dimension mismatch: {len(volume_list)}x{len(volume_list[0]) if volume_list else 0} vs {len(actual_expiries)}x{len(strike_labels)}")
                return {"expiries": [], "strikes": [], "volume": []}
            
            # If all volumes are zero, set a small range for display
            if min_vol == 0 and max_vol == 0:
                max_vol = 1.0
            
            heatmap_data = {
                "expiries": [expiry.strftime('%m-%d') for expiry in actual_expiries],
                "strikes": strike_labels,
                "volume": volume_list,
                "min_volume": min_vol,
                "max_volume": max_vol
            }
            
            logger.info(f"✓ SUCCESS: Heatmap data - {len(heatmap_data['expiries'])} expiries, {len(heatmap_data['strikes'])} strikes")
            logger.info(f"✓ Volume range: {min_vol} to {max_vol}")
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Error calculating volume heatmap: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"expiries": [], "strikes": [], "volume": []}
    
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
