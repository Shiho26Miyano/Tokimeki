"""
FutureQuant Trader Feature Engineering Service - Enhanced Technical Indicators
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from app.models.trading_models import Symbol, Bar, Feature
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantFeatureService:
    """Enhanced feature engineering service for distributional futures trading"""
    
    def __init__(self):
        # Enhanced feature recipes
        self.feature_recipes = {
            "basic": {
                "description": "Basic price and volume features",
                "features": ["returns", "log_returns", "volume_ratio", "price_range"],
                "lookback_periods": [1, 5, 10, 20]
            },
            "momentum": {
                "description": "Momentum and trend indicators",
                "features": ["rsi", "macd", "stoch", "williams_r", "cci", "adx"],
                "lookback_periods": [14, 20, 50]
            },
            "volatility": {
                "description": "Volatility and dispersion measures",
                "features": ["atr", "bbands", "keltner", "donchian", "volatility_ratio"],
                "lookback_periods": [20, 50]
            },
            "volume": {
                "description": "Volume-based indicators",
                "features": ["obv", "vwap", "volume_sma", "volume_ratio", "money_flow"],
                "lookback_periods": [20, 50]
            },
            "support_resistance": {
                "description": "Support and resistance levels",
                "features": ["pivot_points", "fibonacci", "support_resistance"],
                "lookback_periods": [20, 50]
            },
            "distribution": {
                "description": "Distribution-aware features",
                "features": ["quantile_features", "volatility_regime", "tail_risk"],
                "lookback_periods": [20, 50, 100]
            },
            "full": {
                "description": "Complete feature set for advanced models",
                "features": ["returns", "log_returns", "rsi", "macd", "stoch", "williams_r", 
                           "cci", "adx", "atr", "bbands", "keltner", "donchian", "volatility_ratio",
                           "obv", "vwap", "volume_sma", "volume_ratio", "money_flow",
                           "pivot_points", "fibonacci", "support_resistance", "quantile_features",
                           "volatility_regime", "tail_risk"],
                "lookback_periods": [1, 5, 10, 14, 20, 50, 100]
            }
        }
        
        # Feature computation parameters
        self.default_params = {
            "min_data_points": 100,
            "fill_method": "ffill",
            "normalize_features": True,
            "add_interaction_features": True,
            "feature_selection": "correlation"
        }
    
    async def compute_features(
        self,
        symbol_id: int,
        recipe_name: str = "full",
        start_date: str = None,
        end_date: str = None,
        custom_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Compute features for a symbol using specified recipe"""
        try:
            # Validate recipe
            if recipe_name not in self.feature_recipes:
                raise ValueError(f"Invalid recipe. Must be one of: {list(self.feature_recipes.keys())}")
            
            # Get database session
            db = next(get_db())
            
            # Get recipe configuration
            recipe = self.feature_recipes[recipe_name]
            
            # Merge parameters
            params = self.default_params.copy()
            if custom_params:
                params.update(custom_params)
            
            # Get historical data
            bars_data = await self._get_bars_for_feature_computation(
                db, symbol_id, start_date, end_date
            )
            
            if bars_data.empty:
                raise ValueError("No historical data found for feature computation")
            
            # Compute features
            features_df = await self._compute_feature_set(
                bars_data, recipe, params
            )
            
            # Store features
            stored_count = await self._store_features(db, symbol_id, features_df, recipe_name)
            
            return {
                'success': True,
                'symbol_id': symbol_id,
                'recipe_name': recipe_name,
                'features_computed': len(features_df.columns),
                'data_points': len(features_df),
                'stored_count': stored_count,
                'feature_list': list(features_df.columns),
                'computation_params': params
            }
            
        except Exception as e:
            logger.error(f"Feature computation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_bars_for_feature_computation(
        self,
        db: Session,
        symbol_id: int,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """Get historical bars for feature computation"""
        try:
            # Build query
            query = db.query(Bar).filter(Bar.symbol_id == symbol_id)
            
            if start_date:
                query = query.filter(Bar.timestamp >= start_date)
            if end_date:
                query = query.filter(Bar.timestamp <= end_date)
            
            # Get bars
            bars = query.order_by(Bar.timestamp).all()
            
            if not bars:
                return pd.DataFrame()
            
            # Convert to DataFrame
            bars_data = []
            for bar in bars:
                bars_data.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                })
            
            df = pd.DataFrame(bars_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # Ensure minimum data points
            if len(df) < self.default_params['min_data_points']:
                raise ValueError(f"Insufficient data points: {len(df)} < {self.default_params['min_data_points']}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting bars data: {str(e)}")
            return pd.DataFrame()
    
    async def _compute_feature_set(
        self,
        df: pd.DataFrame,
        recipe: Dict[str, Any],
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Compute complete feature set based on recipe"""
        try:
            features_df = df.copy()
            
            # Compute basic features
            for feature_type in recipe['features']:
                if feature_type == "returns":
                    features_df = await self._compute_returns(features_df, recipe['lookback_periods'])
                elif feature_type == "log_returns":
                    features_df = await self._compute_log_returns(features_df, recipe['lookback_periods'])
                elif feature_type == "rsi":
                    features_df = await self._compute_rsi(features_df, recipe['lookback_periods'])
                elif feature_type == "macd":
                    features_df = await self._compute_macd(features_df)
                elif feature_type == "stoch":
                    features_df = await self._compute_stochastic(features_df, recipe['lookback_periods'])
                elif feature_type == "williams_r":
                    features_df = await self._compute_williams_r(features_df, recipe['lookback_periods'])
                elif feature_type == "cci":
                    features_df = await self._compute_cci(features_df, recipe['lookback_periods'])
                elif feature_type == "adx":
                    features_df = await self._compute_adx(features_df, recipe['lookback_periods'])
                elif feature_type == "atr":
                    features_df = await self._compute_atr(features_df, recipe['lookback_periods'])
                elif feature_type == "bbands":
                    features_df = await self._compute_bollinger_bands(features_df, recipe['lookback_periods'])
                elif feature_type == "keltner":
                    features_df = await self._compute_keltner_channels(features_df, recipe['lookback_periods'])
                elif feature_type == "donchian":
                    features_df = await self._compute_donchian_channels(features_df, recipe['lookback_periods'])
                elif feature_type == "volatility_ratio":
                    features_df = await self._compute_volatility_ratio(features_df, recipe['lookback_periods'])
                elif feature_type == "obv":
                    features_df = await self._compute_obv(features_df)
                elif feature_type == "vwap":
                    features_df = await self._compute_vwap(features_df, recipe['lookback_periods'])
                elif feature_type == "volume_sma":
                    features_df = await self._compute_volume_sma(features_df, recipe['lookback_periods'])
                elif feature_type == "volume_ratio":
                    features_df = await self._compute_volume_ratio(features_df, recipe['lookback_periods'])
                elif feature_type == "money_flow":
                    features_df = await self._compute_money_flow(features_df, recipe['lookback_periods'])
                elif feature_type == "pivot_points":
                    features_df = await self._compute_pivot_points(features_df)
                elif feature_type == "fibonacci":
                    features_df = await self._compute_fibonacci_levels(features_df, recipe['lookback_periods'])
                elif feature_type == "support_resistance":
                    features_df = await self._compute_support_resistance(features_df, recipe['lookback_periods'])
                elif feature_type == "quantile_features":
                    features_df = await self._compute_quantile_features(features_df, recipe['lookback_periods'])
                elif feature_type == "volatility_regime":
                    features_df = await self._compute_volatility_regime(features_df, recipe['lookback_periods'])
                elif feature_type == "tail_risk":
                    features_df = await self._compute_tail_risk(features_df, recipe['lookback_periods'])
            
            # Add interaction features
            if params.get('add_interaction_features', True):
                features_df = await self._add_interaction_features(features_df)
            
            # Normalize features
            if params.get('normalize_features', True):
                features_df = await self._normalize_features(features_df)
            
            # Handle missing values
            features_df = features_df.fillna(method=params['fill_method'])
            
            # Remove infinite values
            features_df = features_df.replace([np.inf, -np.inf], np.nan)
            features_df = features_df.fillna(method=params['fill_method'])
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error computing feature set: {str(e)}")
            raise
    
    async def _compute_returns(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute returns for multiple periods"""
        for period in periods:
            df[f'return_{period}d'] = df['close'].pct_change(period)
        return df
    
    async def _compute_log_returns(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute log returns for multiple periods"""
        for period in periods:
            df[f'log_return_{period}d'] = np.log(df['close'] / df['close'].shift(period))
        return df
    
    async def _compute_rsi(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute RSI for multiple periods"""
        for period in periods:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        return df
    
    async def _compute_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute MACD indicators"""
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        return df
    
    async def _compute_stochastic(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Stochastic oscillator for multiple periods"""
        for period in periods:
            low_min = df['low'].rolling(window=period).min()
            high_max = df['high'].rolling(window=period).max()
            df[f'stoch_k_{period}'] = 100 * (df['close'] - low_min) / (high_max - low_min)
            df[f'stoch_d_{period}'] = df[f'stoch_k_{period}'].rolling(window=3).mean()
        return df
    
    async def _compute_williams_r(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Williams %R for multiple periods"""
        for period in periods:
            low_min = df['low'].rolling(window=period).min()
            high_max = df['high'].rolling(window=period).max()
            df[f'williams_r_{period}'] = -100 * (high_max - df['close']) / (high_max - low_min)
        return df
    
    async def _compute_cci(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Commodity Channel Index for multiple periods"""
        for period in periods:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            df[f'cci_{period}'] = (typical_price - sma) / (0.015 * mad)
        return df
    
    async def _compute_adx(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Average Directional Index for multiple periods"""
        for period in periods:
            # True Range
            tr1 = df['high'] - df['low']
            tr2 = abs(df['high'] - df['close'].shift(1))
            tr3 = abs(df['low'] - df['close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Directional Movement
            dm_plus = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                              np.maximum(df['high'] - df['high'].shift(1), 0), 0)
            dm_minus = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                               np.maximum(df['low'].shift(1) - df['low'], 0), 0)
            
            # Smoothed values
            tr_smooth = tr.rolling(window=period).mean()
            dm_plus_smooth = pd.Series(dm_plus).rolling(window=period).mean()
            dm_minus_smooth = pd.Series(dm_minus).rolling(window=period).mean()
            
            # DI values
            di_plus = 100 * dm_plus_smooth / tr_smooth
            di_minus = 100 * dm_minus_smooth / tr_smooth
            
            # DX and ADX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
            df[f'adx_{period}'] = dx.rolling(window=period).mean()
        
        return df
    
    async def _compute_atr(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Average True Range for multiple periods"""
        for period in periods:
            tr1 = df['high'] - df['low']
            tr2 = abs(df['high'] - df['close'].shift(1))
            tr3 = abs(df['low'] - df['close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df[f'atr_{period}'] = tr.rolling(window=period).mean()
        return df
    
    async def _compute_bollinger_bands(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Bollinger Bands for multiple periods"""
        for period in periods:
            sma = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            df[f'bb_upper_{period}'] = sma + (2 * std)
            df[f'bb_lower_{period}'] = sma - (2 * std)
            df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / sma
            df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])
        return df
    
    async def _compute_keltner_channels(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Keltner Channels for multiple periods"""
        for period in periods:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            atr = df[f'atr_{period}'] if f'atr_{period}' in df.columns else df['high'].rolling(window=period).std()
            
            df[f'kc_upper_{period}'] = typical_price + (2 * atr)
            df[f'kc_lower_{period}'] = typical_price - (2 * atr)
            df[f'kc_width_{period}'] = (df[f'kc_upper_{period}'] - df[f'kc_lower_{period}']) / typical_price
        return df
    
    async def _compute_donchian_channels(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Donchian Channels for multiple periods"""
        for period in periods:
            df[f'dc_upper_{period}'] = df['high'].rolling(window=period).max()
            df[f'dc_lower_{period}'] = df['low'].rolling(window=period).min()
            df[f'dc_mid_{period}'] = (df[f'dc_upper_{period}'] + df[f'dc_lower_{period}']) / 2
            df[f'dc_width_{period}'] = (df[f'dc_upper_{period}'] - df[f'dc_lower_{period}']) / df['close']
        return df
    
    async def _compute_volatility_ratio(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute volatility ratio for multiple periods"""
        for period in periods:
            returns = df['close'].pct_change()
            short_vol = returns.rolling(window=period//2).std()
            long_vol = returns.rolling(window=period).std()
            df[f'vol_ratio_{period}'] = short_vol / long_vol
        return df
    
    async def _compute_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute On-Balance Volume"""
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return df
    
    async def _compute_vwap(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Volume Weighted Average Price for multiple periods"""
        for period in periods:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            df[f'vwap_{period}'] = (typical_price * df['volume']).rolling(window=period).sum() / df['volume'].rolling(window=period).sum()
        return df
    
    async def _compute_volume_sma(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute volume simple moving average for multiple periods"""
        for period in periods:
            df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
        return df
    
    async def _compute_volume_ratio(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute volume ratio for multiple periods"""
        for period in periods:
            df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_sma_{period}']
        return df
    
    async def _compute_money_flow(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Money Flow Index for multiple periods"""
        for period in periods:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            money_flow = typical_price * df['volume']
            
            positive_flow = np.where(typical_price > typical_price.shift(1), money_flow, 0)
            negative_flow = np.where(typical_price < typical_price.shift(1), money_flow, 0)
            
            positive_mf = pd.Series(positive_flow).rolling(window=period).sum()
            negative_mf = pd.Series(negative_flow).rolling(window=period).sum()
            
            mfi = 100 - (100 / (1 + positive_mf / negative_mf))
            df[f'mfi_{period}'] = mfi
        return df
    
    async def _compute_pivot_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute pivot points"""
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['r1'] = 2 * df['pivot'] - df['low']
        df['s1'] = 2 * df['pivot'] - df['high']
        df['r2'] = df['pivot'] + (df['high'] - df['low'])
        df['s2'] = df['pivot'] - (df['high'] - df['low'])
        return df
    
    async def _compute_fibonacci_levels(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute Fibonacci retracement levels for multiple periods"""
        for period in periods:
            high = df['high'].rolling(window=period).max()
            low = df['low'].rolling(window=period).min()
            diff = high - low
            
            df[f'fib_236_{period}'] = high - 0.236 * diff
            df[f'fib_382_{period}'] = high - 0.382 * diff
            df[f'fib_500_{period}'] = high - 0.500 * diff
            df[f'fib_618_{period}'] = high - 0.618 * diff
            df[f'fib_786_{period}'] = high - 0.786 * diff
        return df
    
    async def _compute_support_resistance(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute support and resistance levels for multiple periods"""
        for period in periods:
            # Support levels
            df[f'support_1_{period}'] = df['low'].rolling(window=period).min()
            df[f'support_2_{period}'] = df['low'].rolling(window=period*2).min()
            
            # Resistance levels
            df[f'resistance_1_{period}'] = df['high'].rolling(window=period).max()
            df[f'resistance_2_{period}'] = df['high'].rolling(window=period*2).max()
            
            # Distance to support/resistance
            df[f'dist_to_support_{period}'] = (df['close'] - df[f'support_1_{period}']) / df['close']
            df[f'dist_to_resistance_{period}'] = (df[f'resistance_1_{period}'] - df['close']) / df['close']
        return df
    
    async def _compute_quantile_features(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute distribution-aware quantile features for multiple periods"""
        for period in periods:
            returns = df['close'].pct_change()
            
            # Rolling quantiles
            df[f'return_q10_{period}'] = returns.rolling(window=period).quantile(0.10)
            df[f'return_q25_{period}'] = returns.rolling(window=period).quantile(0.25)
            df[f'return_q75_{period}'] = returns.rolling(window=period).quantile(0.75)
            df[f'return_q90_{period}'] = returns.rolling(window=period).quantile(0.90)
            
            # Interquartile range
            df[f'return_iqr_{period}'] = df[f'return_q75_{period}'] - df[f'return_q25_{period}']
            
            # Tail risk measures
            df[f'return_skew_{period}'] = returns.rolling(window=period).skew()
            df[f'return_kurt_{period}'] = returns.rolling(window=period).kurt()
        return df
    
    async def _compute_volatility_regime(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute volatility regime indicators for multiple periods"""
        for period in periods:
            returns = df['close'].pct_change()
            volatility = returns.rolling(window=period).std()
            
            # Volatility regime classification
            vol_mean = volatility.rolling(window=period*2).mean()
            vol_std = volatility.rolling(window=period*2).std()
            
            df[f'vol_regime_{period}'] = np.where(
                volatility > vol_mean + vol_std, 2,  # High volatility
                np.where(volatility < vol_mean - vol_std, 0, 1)  # Low volatility, Normal
            )
            
            # Volatility momentum
            df[f'vol_momentum_{period}'] = volatility.pct_change(period//2)
        return df
    
    async def _compute_tail_risk(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Compute tail risk measures for multiple periods"""
        for period in periods:
            returns = df['close'].pct_change()
            
            # Value at Risk (VaR)
            df[f'var_95_{period}'] = returns.rolling(window=period).quantile(0.05)
            df[f'var_99_{period}'] = returns.rolling(window=period).quantile(0.01)
            
            # Expected Shortfall (CVaR)
            def cvar_95(x):
                return x[x <= x.quantile(0.05)].mean()
            def cvar_99(x):
                return x[x <= x.quantile(0.01)].mean()
            
            df[f'cvar_95_{period}'] = returns.rolling(window=period).apply(cvar_95)
            df[f'cvar_99_{period}'] = returns.rolling(window=period).apply(cvar_99)
            
            # Tail risk ratio
            df[f'tail_risk_ratio_{period}'] = abs(df[f'cvar_95_{period}']) / returns.rolling(window=period).std()
        return df
    
    async def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features between key indicators"""
        try:
            # Price-volume interactions
            if 'volume_ratio_20' in df.columns and 'return_1d' in df.columns:
                df['price_volume_interaction'] = df['volume_ratio_20'] * df['return_1d']
            
            # Momentum-volatility interactions
            if 'rsi_14' in df.columns and 'atr_20' in df.columns:
                df['momentum_vol_interaction'] = df['rsi_14'] * df['atr_20']
            
            # Trend-strength interactions
            if 'adx_14' in df.columns and 'macd' in df.columns:
                df['trend_strength_interaction'] = df['adx_14'] * df['macd']
            
            # Support-resistance interactions
            if 'dist_to_support_20' in df.columns and 'dist_to_resistance_20' in df.columns:
                df['support_resistance_balance'] = df['dist_to_support_20'] / (df['dist_to_resistance_20'] + 1e-8)
            
            logger.info("Added interaction features")
            return df
            
        except Exception as e:
            logger.warning(f"Could not add all interaction features: {str(e)}")
            return df
    
    async def _normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize features using z-score normalization"""
        try:
            # Select only numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # Skip price and volume columns from normalization
            skip_cols = ['open', 'high', 'low', 'close', 'volume']
            normalize_cols = [col for col in numeric_cols if not any(skip in col for skip in skip_cols)]
            
            # Z-score normalization
            for col in normalize_cols:
                mean_val = df[col].mean()
                std_val = df[col].std()
                if std_val > 0:
                    df[f'{col}_normalized'] = (df[col] - mean_val) / std_val
                else:
                    df[f'{col}_normalized'] = 0
            
            logger.info(f"Normalized {len(normalize_cols)} features")
            return df
            
        except Exception as e:
            logger.warning(f"Could not normalize features: {str(e)}")
            return df
    
    async def _store_features(
        self,
        db: Session,
        symbol_id: int,
        features_df: pd.DataFrame,
        recipe_name: str
    ) -> int:
        """Store computed features in database"""
        try:
            stored_count = 0
            
            for timestamp, row in features_df.iterrows():
                # Convert features to JSON
                feature_data = {}
                for col in features_df.columns:
                    if col not in ['open', 'high', 'low', 'close', 'volume']:
                        value = row[col]
                        if pd.isna(value) or np.isinf(value):
                            continue
                        feature_data[col] = float(value)
                
                # Create feature record
                feature = Feature(
                    symbol_id=symbol_id,
                    timestamp=timestamp,
                    recipe_name=recipe_name,
                    feature_data=json.dumps(feature_data),
                    computed_at=datetime.now()
                )
                
                db.add(feature)
                stored_count += 1
            
            db.commit()
            logger.info(f"Stored {stored_count} feature records")
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing features: {str(e)}")
            db.rollback()
            raise
    
    async def get_feature_recipes(self) -> Dict[str, Any]:
        """Get available feature recipes"""
        return {
            'success': True,
            'recipes': self.feature_recipes
        }
    
    async def get_recipe_details(self, recipe_name: str) -> Dict[str, Any]:
        """Get details for a specific recipe"""
        if recipe_name not in self.feature_recipes:
            return {
                'success': False,
                'error': f"Recipe {recipe_name} not found"
            }
        
        return {
            'success': True,
            'recipe': self.feature_recipes[recipe_name]
        }
    
    async def batch_compute_features(
        self,
        symbol_ids: List[int],
        recipe_name: str = "full",
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """Compute features for multiple symbols"""
        try:
            results = []
            
            for symbol_id in symbol_ids:
                result = await self.compute_features(
                    symbol_id, recipe_name, start_date, end_date
                )
                results.append({
                    'symbol_id': symbol_id,
                    'result': result
                })
            
            successful = [r for r in results if r['result']['success']]
            failed = [r for r in results if not r['result']['success']]
            
            return {
                'success': True,
                'total_symbols': len(symbol_ids),
                'successful': len(successful),
                'failed': len(failed),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch feature computation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
