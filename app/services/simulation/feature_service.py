"""
Feature Engineering Service for Trading Simulation
Computes required metrics: rv20, rv60, atr14, iv metrics, percentiles
"""
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.simulation_models import (
    PricesDaily, OptionsSnapshotDaily, FeaturesDaily
)


class SimulationFeatureService:
    """Service for computing daily features for trading strategies"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ROLLING_WINDOW_DAYS = 504  # ~2 years of trading days
    
    def compute_realized_volatility(self, prices_df: pd.DataFrame, window: int) -> float:
        """
        Compute annualized realized volatility from log returns
        
        Args:
            prices_df: DataFrame with 'close' column, sorted by date
            window: Number of days for rolling window
            
        Returns:
            Annualized realized volatility
        """
        if len(prices_df) < window + 1:
            return None
        
        # Get close prices for the window
        closes = prices_df['close'].values[-window-1:]
        
        # Compute log returns
        log_returns = np.log(closes[1:] / closes[:-1])
        
        # Annualized standard deviation
        rv = np.sqrt(252) * np.std(log_returns)
        
        return float(rv)
    
    def compute_atr14(self, prices_df: pd.DataFrame) -> float:
        """
        Compute 14-day ATR (Average True Range) using Wilder's method
        
        Args:
            prices_df: DataFrame with 'high', 'low', 'close' columns
            
        Returns:
            14-day ATR
        """
        if len(prices_df) < 15:  # Need at least 15 days (14 + 1 for prev close)
            return None
        
        # Get last 15 rows
        df = prices_df[['high', 'low', 'close']].tail(15).copy()
        
        # True Range
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Wilder's ATR (exponential smoothing with alpha = 1/14)
        atr_values = df['tr'].tail(14).values
        atr = atr_values[0]  # First value
        
        alpha = 1.0 / 14.0
        for tr in atr_values[1:]:
            atr = (1 - alpha) * atr + alpha * tr
        
        return float(atr)
    
    def compute_percentile(self, value: float, historical_values: np.ndarray) -> float:
        """
        Compute percentile rank of a value against historical values
        
        Args:
            value: Current value
            historical_values: Array of historical values (no lookahead)
            
        Returns:
            Percentile rank (0-100)
        """
        if value is None or len(historical_values) == 0:
            return None
        
        # Remove NaN values
        historical_values = historical_values[~np.isnan(historical_values)]
        
        if len(historical_values) == 0:
            return None
        
        # Percentile rank
        pct = (np.sum(historical_values <= value) / len(historical_values)) * 100.0
        
        return float(pct)
    
    def compute_features_for_date(
        self, 
        symbol: str, 
        target_date: date,
        use_adjusted: bool = True
    ) -> Optional[Dict]:
        """
        Compute all features for a given symbol and date
        
        Args:
            symbol: Stock symbol
            target_date: Date to compute features for
            use_adjusted: Whether to use adjusted_close if available
            
        Returns:
            Dictionary of feature values or None if insufficient data
        """
        # Get all prices up to and including target_date (no lookahead)
        prices_query = self.db.query(PricesDaily).filter(
            and_(
                PricesDaily.symbol == symbol,
                PricesDaily.date <= target_date
            )
        ).order_by(PricesDaily.date)
        
        prices_list = prices_query.all()
        
        if len(prices_list) < 61:  # Need at least 61 days for rv60
            return None
        
        # Convert to DataFrame
        prices_data = []
        for p in prices_list:
            close_price = p.adjusted_close if (use_adjusted and p.adjusted_close) else p.close
            prices_data.append({
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': close_price,
                'volume': p.volume
            })
        
        prices_df = pd.DataFrame(prices_data)
        prices_df = prices_df.sort_values('date')
        
        # Get target date row
        target_row = prices_df[prices_df['date'] == target_date]
        if len(target_row) == 0:
            return None
        
        # Compute realized volatility
        rv20 = self.compute_realized_volatility(prices_df, 20)
        rv60 = self.compute_realized_volatility(prices_df, 60)
        
        # Compute ATR14
        atr14 = self.compute_atr14(prices_df)
        
        # Get options data for target date
        options_snapshot = self.db.query(OptionsSnapshotDaily).filter(
            and_(
                OptionsSnapshotDaily.symbol == symbol,
                OptionsSnapshotDaily.date == target_date
            )
        ).first()
        
        iv_median = options_snapshot.iv_median if options_snapshot else None
        iv_slope = options_snapshot.iv_slope if options_snapshot else None
        cp_vol_ratio = None
        cp_oi_ratio = None
        unusual_count = 0
        
        if options_snapshot:
            # Compute call/put ratios
            total_call_vol = options_snapshot.total_call_volume or 0
            total_put_vol = options_snapshot.total_put_volume or 0
            total_call_oi = options_snapshot.total_call_oi or 0
            total_put_oi = options_snapshot.total_put_oi or 0
            
            eps = 1e-9
            cp_vol_ratio = total_call_vol / max(total_put_vol, eps)
            cp_oi_ratio = total_call_oi / max(total_put_oi, eps)
            unusual_count = options_snapshot.unusual_count or 0
        
        # Compute percentiles (using historical data up to target_date)
        # Get historical features for percentile computation
        historical_features = self.db.query(FeaturesDaily).filter(
            and_(
                FeaturesDaily.symbol == symbol,
                FeaturesDaily.date < target_date
            )
        ).order_by(FeaturesDaily.date).limit(self.ROLLING_WINDOW_DAYS).all()
        
        # Compute percentiles
        rv20_pct = None
        atr14_pct = None
        iv_median_pct = None
        percentile_quality = "sufficient"
        
        if rv20 is not None:
            rv20_history = np.array([f.rv20 for f in historical_features if f.rv20 is not None])
            if len(rv20_history) >= 252:  # At least 1 year
                rv20_pct = self.compute_percentile(rv20, rv20_history)
            else:
                percentile_quality = "insufficient"
        
        if atr14 is not None:
            atr14_history = np.array([f.atr14 for f in historical_features if f.atr14 is not None])
            if len(atr14_history) >= 252:
                atr14_pct = self.compute_percentile(atr14, atr14_history)
            else:
                percentile_quality = "insufficient"
        
        if iv_median is not None:
            iv_history = np.array([f.iv_median for f in historical_features if f.iv_median is not None])
            if len(iv_history) >= 252:
                iv_median_pct = self.compute_percentile(iv_median, iv_history)
            else:
                percentile_quality = "insufficient"
        
        features = {
            'symbol': symbol,
            'date': target_date,
            'rv20': rv20,
            'rv60': rv60,
            'atr14': atr14,
            'iv_median': iv_median,
            'iv_slope': iv_slope,
            'cp_vol_ratio': cp_vol_ratio,
            'cp_oi_ratio': cp_oi_ratio,
            'unusual_count': unusual_count,
            'rv20_pct': rv20_pct,
            'atr14_pct': atr14_pct,
            'iv_median_pct': iv_median_pct,
            'percentile_quality': percentile_quality
        }
        
        return features
    
    def persist_features(self, features: Dict) -> FeaturesDaily:
        """
        Persist computed features to database
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            FeaturesDaily instance
        """
        # Check if exists
        existing = self.db.query(FeaturesDaily).filter(
            and_(
                FeaturesDaily.symbol == features['symbol'],
                FeaturesDaily.date == features['date']
            )
        ).first()
        
        if existing:
            # Update existing
            for key, value in features.items():
                if key not in ['symbol', 'date']:
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Create new
            feature_row = FeaturesDaily(**features)
            self.db.add(feature_row)
            self.db.commit()
            self.db.refresh(feature_row)
            return feature_row

