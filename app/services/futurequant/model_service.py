"""
FutureQuant Trader ML Model Service - Distributional Models
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Protocol
from datetime import datetime, timedelta
import joblib
import os
from sqlalchemy.orm import Session

# PyTorch imports for transformer models
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.models.trading_models import Symbol, Bar, Feature, Forecast, Model
from app.models.database import get_db
from app.services.brpc_service import get_brpc_service

logger = logging.getLogger(__name__)

class DistModel(Protocol):
    """Protocol for distributional models"""
    def fit(self, X: np.ndarray, y: np.ndarray): ...
    def predict_dist(self, X: np.ndarray) -> Dict[str, np.ndarray]: ...

class FutureQuantTransformer(nn.Module):
    """FutureQuant Transformer model for distributional prediction"""
    def __init__(self, input_dim, d_model, n_heads, n_layers, dropout):
        super().__init__()
        self.input_projection = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dropout=dropout, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.quantile_head = nn.Linear(d_model, 3)  # q10, q50, q90
        self.prob_head = nn.Linear(d_model, 1)
        self.vol_head = nn.Linear(d_model, 1)
    
    def forward(self, x):
        # x: (batch, features) -> add seq dim = 1
        x = self.input_projection(x)        # (B, d_model)
        x = x.unsqueeze(1)                  # (B, 1, d_model)
        x = self.transformer(x)             # (B, 1, d_model)
        x = x.squeeze(1)                    # (B, d_model)
        quantiles = self.quantile_head(x)   # (B, 3)
        prob_up = torch.sigmoid(self.prob_head(x))  # (B, 1)
        vol = torch.exp(self.vol_head(x))   # (B, 1), positive
        return quantiles, prob_up, vol


class FutureQuantModelService:
    """Service for training and using distributional ML models for futures prediction"""
    
    def __init__(self):
        self.model_types = {
            "quantile_regression": "Quantile Regression",
            "random_forest": "Random Forest Quantiles", 
            "neural_network": "Neural Network",
            "gradient_boosting": "Gradient Boosting",
            "transformer": "Transformer Encoder (FQT-lite)"
        }
        
        self.horizons = [0.5, 5, 15, 60, 240, 1440]  # 30s (demo), 5m, 15m, 1h, 4h, 1d in minutes
        self.brpc_service = get_brpc_service()
        
    async def generate_test_data(self, symbol: str, days: int = 365) -> Dict[str, Any]:
        """Generate test data for training when no real data exists"""
        try:
            db = next(get_db())
            
            # Check if symbol exists, create if not
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            if not symbol_obj:
                symbol_obj = Symbol(
                    ticker=symbol,
                    name=f"Test {symbol}",
                    exchange="TEST",
                    asset_type="futures",
                    created_at=datetime.utcnow()
                )
                db.add(symbol_obj)
                db.commit()
                db.refresh(symbol_obj)
            
            # Generate synthetic bars data
            import random
            
            base_price = 100.0
            bars_data = []
            features_data = []
            
            start_date = datetime.now() - timedelta(days=days)
            current_date = start_date
            
            for i in range(days):
                # Generate realistic price movement
                price_change = random.gauss(0, 0.02)  # 2% daily volatility
                base_price *= (1 + price_change)
                
                # Create bar data
                bar = Bar(
                    symbol_id=symbol_obj.id,
                    timestamp=current_date,
                    interval="1d",
                    open=base_price * (1 + random.gauss(0, 0.005)),
                    high=base_price * (1 + abs(random.gauss(0, 0.01))),
                    low=base_price * (1 - abs(random.gauss(0, 0.01))),
                    close=base_price,
                    volume=random.randint(1000, 10000),
                    created_at=datetime.utcnow()
                )
                bars_data.append(bar)
                
                # Create feature data
                feature = Feature(
                    symbol_id=symbol_obj.id,
                    timestamp=current_date,
                    payload={
                        "feature_type": "technical_indicators",
                        "sma_20": base_price * (1 + random.gauss(0, 0.01)),
                        "rsi": random.uniform(30, 70),
                        "macd": random.gauss(0, 0.01),
                        "bollinger_upper": base_price * 1.02,
                        "bollinger_lower": base_price * 0.98,
                        "volume_sma": random.randint(5000, 15000),
                        "volatility": abs(price_change),
                        "momentum": random.gauss(0, 0.01)
                    },
                    created_at=datetime.utcnow()
                )
                features_data.append(feature)
                
                current_date += timedelta(days=1)
            
            # Save to database
            db.add_all(bars_data)
            db.add_all(features_data)
            db.commit()
            
            logger.info(f"Generated test data: {len(bars_data)} bars and {len(features_data)} features for {symbol}")
            
            return {
                "success": True,
                "symbol": symbol,
                "bars_count": len(bars_data),
                "features_count": len(features_data),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error generating test data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        
    async def train_model(
        self,
        symbol: str,
        model_type: str = "quantile_regression",
        horizon_minutes: int = 1440,
        start_date: str = None,
        end_date: str = None,
        test_size: float = 0.2,
        hyperparams: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Train a new distributional model for a symbol"""
        try:
            # Validate model type
            if model_type not in self.model_types:
                raise ValueError(f"Invalid model type. Must be one of: {list(self.model_types.keys())}")
            
            # Validate horizon
            try:
                horizon_minutes = float(horizon_minutes)  # may arrive as string
            except (ValueError, TypeError):
                raise ValueError(f"Invalid horizon format. Must be a number, got: {horizon_minutes}")
            
            logger.info(f"Training with horizon: {horizon_minutes} (type: {type(horizon_minutes)})")
            logger.info(f"Available horizons: {self.horizons}")
            if horizon_minutes not in self.horizons:
                raise ValueError(f"Invalid horizon. Must be one of: {self.horizons}")
            
            # Set default dates if not provided
            if not start_date or not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # Get training data
            db = next(get_db())
            
            # Try to get existing data first
            try:
                X_train, y_train, X_test, y_test = await self._prepare_training_data(
                    db, symbol, start_date, end_date, horizon_minutes, test_size
                )
            except ValueError as e:
                if "No bars or features found" in str(e):
                    logger.info(f"No training data found for {symbol}, generating test data...")
                    test_data_result = await self.generate_test_data(symbol, days=365)
                    if not test_data_result["success"]:
                        raise ValueError(f"Failed to generate test data: {test_data_result['error']}")
                    X_train, y_train, X_test, y_test = await self._prepare_training_data(
                        db, symbol, start_date, end_date, horizon_minutes, test_size
                    )
                else:
                    raise
            
            if len(X_train) < 100:
                raise ValueError(f"Insufficient training data. Need at least 100 samples, got {len(X_train)}")
            
            # Set current horizon for demo mode detection
            self._current_horizon = horizon_minutes
            
            # Train model
            model, metrics = await self._train_distributional_model(
                model_type, X_train, y_train, X_test, y_test, hyperparams
            )
            
            # Save model
            model_path = await self._save_model(model, symbol, model_type, horizon_minutes)
            
            # Store model metadata in database with initial "training" status
            model_id = await self._store_model_metadata(
                db, symbol, model_type, model_path, metrics, horizon_minutes, hyperparams, initial_status="training"
            )
            
            # Update status to "completed" after successful training
            await self._update_model_status(db, model_id, "completed")
            
            return {
                "success": True,
                "model_id": model_id,
                "symbol": symbol,
                "model_type": model_type,
                "horizon_minutes": horizon_minutes,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "metrics": metrics,
                "model_path": model_path,
                "hyperparams": hyperparams
            }
        except Exception as e:
            logger.error(f"Training error: {e}")
            # If we have a model_id, update its status to failed
            if 'model_id' in locals():
                try:
                    await self._update_model_status(db, model_id, "failed")
                except:
                    pass  # Don't let status update failure mask the original error
            return {"success": False, "error": str(e)}
    
    async def predict(
        self,
        model_id: int,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Make distributional predictions using a trained model"""
        try:
            db = next(get_db())
            
            # Get model
            model_obj = db.query(Model).filter(Model.id == model_id).first()
            if not model_obj:
                raise ValueError(f"Model {model_id} not found")
            
            # Load model
            model = joblib.load(model_obj.artifact_uri)
            
            # Get features for prediction
            features = await self._get_features_for_prediction(db, symbol, start_date, end_date)
            if not features:
                raise ValueError(f"No features found for {symbol} in date range")
            
            # Make distributional predictions
            predictions = await self._make_distributional_predictions(model, features, model_obj.params)
            
            # Store forecasts
            await self._store_forecasts(db, symbol, predictions, model_id, model_obj.params.get('horizon_minutes', 1440))
            
            return {
                "success": True,
                "model_id": model_id,
                "symbol": symbol,
                "predictions_count": len(predictions),
                "start_date": start_date,
                "end_date": end_date,
                "forecast_type": "distributional"
            }
            
        except Exception as e:
            logger.error(f"Prediction error for model {model_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _prepare_training_data(
        self,
        db: Session,
        symbol: str,
        start_date: str,
        end_date: str,
        horizon_minutes: float,
        test_size: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training and test data with strict time-based split"""
        # Get symbol
        symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
        if not symbol_obj:
            raise ValueError(f"Symbol {symbol} not found")
        
        # Get bars and features
        bars = db.query(Bar).filter(
            Bar.symbol_id == symbol_obj.id,
            Bar.interval == "1d",
            Bar.timestamp >= start_date,
            Bar.timestamp <= end_date
        ).order_by(Bar.timestamp).all()
        
        features = db.query(Feature).filter(
            Feature.symbol_id == symbol_obj.id,
            Feature.timestamp >= start_date,
            Feature.timestamp <= end_date
        ).order_by(Feature.timestamp).all()
        
        if not bars or not features:
            raise ValueError("No bars or features found for training")
        
        data = []
        
        # Convert horizon to appropriate index offset
        if horizon_minutes == 0.5:  # 30 seconds demo
            horizon_index = 1  # 1 day minimum for daily bars
            logger.info("30-second demo mode: using 1 day offset for daily data")
        elif horizon_minutes < 1:
            horizon_index = 1
        else:
            horizon_index = int(horizon_minutes)
        
        for i, bar in enumerate(bars):
            if i + horizon_index >= len(bars):
                break
            
            # Get current features
            feature = next((f for f in features if f.timestamp == bar.timestamp), None)
            if not feature:
                continue
            
            # Target
            future_bar = bars[i + horizon_index]
            future_return = (future_bar.close - bar.close) / bar.close
            
            row = feature.payload.copy()
            row['future_return'] = future_return
            row['timestamp'] = bar.timestamp
            data.append(row)
        
        if not data:
            raise ValueError("No valid training data found")
        
        df = pd.DataFrame(data).dropna()
        if len(df) < 100:
            raise ValueError(f"Insufficient data after preprocessing. Got {len(df)} samples")
        
        df = self._fix_feature_data_types(df)
        
        feature_cols = [c for c in df.columns if c not in ['future_return', 'timestamp']]
        X = df[feature_cols].values
        y = df['future_return'].values
        
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        return X_train, y_train, X_test, y_test

    def _fix_feature_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix data types for features to ensure they are numeric"""
        try:
            logger.info(f"Fixing data types for {len(df.columns)} columns")
            for col in df.columns:
                if col in ['future_return', 'timestamp']:
                    continue
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if df[col].isna().any():
                    df[col] = df[col].ffill().bfill().fillna(0)
                if df[col].dtype in ['object', 'string', 'int64', 'int32', 'int16', 'int8', 'float32', 'float16']:
                    df[col] = df[col].astype('float64')
            object_columns = df.select_dtypes(include=['object']).columns.tolist()
            if object_columns:
                logger.warning(f"Found remaining object columns: {object_columns}")
                for col in object_columns:
                    if col not in ['future_return', 'timestamp']:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('float64')
            feature_cols = [c for c in df.columns if c not in ['future_return', 'timestamp']]
            for col in feature_cols:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    logger.error(f"Column {col} is still not numeric: {df[col].dtype}")
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('float64')
            logger.info(f"Data type fix complete. Final dtypes: {df.dtypes.unique()}")
            return df
        except Exception as e:
            logger.error(f"Error fixing feature data types: {str(e)}")
            return df
    
    async def _train_distributional_model(
        self,
        model_type: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        hyperparams: Dict[str, Any] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """Train a distributional model"""
        try:
            if model_type == "quantile_regression":
                return await self._train_quantile_regression(X_train, y_train, X_test, y_test, hyperparams)
            elif model_type == "random_forest":
                return await self._train_random_forest(X_train, y_train, X_test, y_test, hyperparams)
            elif model_type == "neural_network":
                return await self._train_neural_network(X_train, y_train, X_test, y_test, hyperparams)
            elif model_type == "gradient_boosting":
                return await self._train_gradient_boosting(X_train, y_train, X_test, y_test, hyperparams)
            elif model_type == "transformer":
                # For demo mode, try transformer first, fallback to quantile regression if it's too slow
                if hasattr(self, '_current_horizon') and self._current_horizon == 0.5:
                    try:
                        logger.info("Attempting transformer training for demo mode...")
                        return await self._train_transformer(X_train, y_train, X_test, y_test, hyperparams)
                    except Exception as e:
                        logger.warning(f"Transformer training failed for demo mode: {str(e)}")
                        logger.info("Falling back to quantile regression for faster training...")
                        return await self._train_quantile_regression(X_train, y_train, X_test, y_test, hyperparams)
                else:
                    return await self._train_transformer(X_train, y_train, X_test, y_test, hyperparams)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
        except Exception as e:
            logger.error(f"Error training {model_type} model: {str(e)}")
            # For demo mode, always fallback to quantile regression
            if hasattr(self, '_current_horizon') and self._current_horizon == 0.5:
                logger.info("Falling back to quantile regression due to training error...")
                return await self._train_quantile_regression(X_train, y_train, X_test, y_test, hyperparams)
            else:
                raise e
    
    async def _train_quantile_regression(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        hyperparams: Dict[str, Any] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """Train quantile regression model for distributional forecasting"""
        from sklearn.linear_model import QuantileRegressor
        
        default_params = {"alpha": 0.1, "solver": "highs"}
        if hyperparams:
            default_params.update(hyperparams)
        
        models = {}
        quantiles = [0.1, 0.5, 0.9]
        for q in quantiles:
            model = QuantileRegressor(quantile=q, **default_params)
            model.fit(X_train, y_train)
            models[q] = model
        
        ensemble_model = {
            'type': 'quantile_regression',
            'models': models,
            'quantiles': quantiles,
            'hyperparams': default_params
        }
        metrics = await self._evaluate_distributional_model(ensemble_model, X_test, y_test)
        return ensemble_model, metrics
    
    async def _train_transformer(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        hyperparams: Dict[str, Any] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """Train transformer encoder model (FQT-lite)"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for transformer models")
        
        import torch.optim as optim
        
        default_params = {
            "d_model": 64,
            "n_heads": 4,
            "n_layers": 2,
            "dropout": 0.1,
            "lr": 0.001,
            "epochs": 100,
            "batch_size": 32
        }
        if hasattr(self, '_current_horizon') and self._current_horizon == 0.5:
            logger.info("30-second demo mode: using ultra-fast training parameters")
            # For demo mode, use simpler parameters to ensure fast training
            default_params.update({
                "epochs": 2,  # Very few epochs for demo
                "batch_size": 256,  # Larger batch for speed
                "lr": 0.1,  # Higher learning rate for faster convergence
                "d_model": 16,  # Smaller model for speed
                "n_heads": 2,  # Fewer attention heads
                "n_layers": 1  # Single layer for speed
            })
        if hyperparams:
            default_params.update(hyperparams)
        
        # Use the module-level FutureQuantTransformer class
        
        model = FutureQuantTransformer(
            input_dim=X_train.shape[1],
            d_model=default_params["d_model"],
            n_heads=default_params["n_heads"],
            n_layers=default_params["n_layers"],
            dropout=default_params["dropout"]
        )
        
        optimizer = optim.Adam(model.parameters(), lr=default_params["lr"])
        # Pinball-like plus volatility penalty is implemented explicitly below
        
        X_train_tensor = torch.as_tensor(X_train, dtype=torch.float32)
        y_train_tensor = torch.as_tensor(y_train, dtype=torch.float32)
        
        model.train()
        logger.info(f"Starting training with {default_params['epochs']} epochs")
        
        # Add timeout for demo mode
        import time
        start_time = time.time()
        max_training_time = 15  # 15 seconds max for demo mode
        
        for epoch in range(default_params["epochs"]):
            # Check timeout
            if hasattr(self, '_current_horizon') and self._current_horizon == 0.5:
                if time.time() - start_time > max_training_time:
                    logger.warning(f"Training timeout after {max_training_time}s, stopping early at epoch {epoch+1}")
                    break
            try:
                optimizer.zero_grad()
                quantiles, prob_up, vol = model(X_train_tensor)  # (B,3), (B,1), (B,1)
                q10, q50, q90 = quantiles[:, 0], quantiles[:, 1], quantiles[:, 2]
                y = y_train_tensor
                
                # Pinball losses
                def pinball_loss(y_true, y_pred, q):
                    e = y_true - y_pred
                    return torch.mean(torch.maximum((q - 1) * e, q * e))
                q10_loss = pinball_loss(y, q10, 0.1)
                q50_loss = pinball_loss(y, q50, 0.5)
                q90_loss = pinball_loss(y, q90, 0.9)
                
                vol_loss = torch.mean(torch.abs(vol.squeeze(1) - torch.std(y)))
                total_loss = q10_loss + q50_loss + q90_loss + 0.1 * vol_loss
                total_loss.backward()
                optimizer.step()
                
                # Log progress every few epochs
                if epoch % max(1, default_params["epochs"] // 5) == 0:
                    logger.info(f"Epoch {epoch+1}/{default_params['epochs']}, Loss: {total_loss.item():.6f}")
                    
            except Exception as e:
                logger.error(f"Error during epoch {epoch+1}: {str(e)}")
                raise e
        
        logger.info("Training completed successfully")
        
        transformer_model = {
            'type': 'transformer',
            'model': model,
            'hyperparams': default_params,
            'input_dim': X_train.shape[1]
        }
        metrics = await self._evaluate_distributional_model(transformer_model, X_test, y_test)
        return transformer_model, metrics
    
    async def _train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        hyperparams: Dict[str, Any] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """Train random forest model"""
        from sklearn.ensemble import RandomForestRegressor
        default_params = {"n_estimators": 100, "max_depth": 10, "random_state": 42}
        if hyperparams:
            default_params.update(hyperparams)
        model = RandomForestRegressor(**default_params)
        model.fit(X_train, y_train)
        metrics = await self._evaluate_distributional_model(model, X_test, y_test)
        return model, metrics
    
    async def _train_neural_network(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        hyperparams: Dict[str, Any] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """Train neural network model"""
        from sklearn.neural_network import MLPRegressor
        default_params = {"hidden_layer_sizes": (100, 50), "max_iter": 500, "random_state": 42}
        if hyperparams:
            default_params.update(hyperparams)
        model = MLPRegressor(**default_params)
        model.fit(X_train, y_train)
        metrics = await self._evaluate_distributional_model(model, X_test, y_test)
        return model, metrics
    
    async def _train_gradient_boosting(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        hyperparams: Dict[str, Any] = None
    ) -> Tuple[Any, Dict[str, float]]:
        """Train gradient boosting model"""
        from sklearn.ensemble import GradientBoostingRegressor
        default_params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
        if hyperparams:
            default_params.update(hyperparams)
        model = GradientBoostingRegressor(**default_params)
        model.fit(X_train, y_train)
        metrics = await self._evaluate_distributional_model(model, X_test, y_test)
        return model, metrics
    
    async def _evaluate_distributional_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate distributional model performance"""
        try:
            if isinstance(model, dict) and model.get('type') == 'quantile_regression':
                predictions = []
                for q in model['quantiles']:
                    pred = model['models'][q].predict(X_test)
                    predictions.append(pred)
                y_pred = predictions[1]  # median
                q10_pred, q50_pred, q90_pred = predictions[0], predictions[1], predictions[2]
                coverage_10 = np.mean((y_test >= q10_pred) & (y_test <= q90_pred))
                coverage_50 = np.mean((y_test >= q10_pred) & (y_test <= q50_pred))
            elif isinstance(model, dict) and model.get('type') == 'transformer':
                # Lazy import torch here to avoid NameError if sklearn path is used
                import torch
                model['model'].eval()
                with torch.no_grad():
                    X_test_tensor = torch.as_tensor(X_test, dtype=torch.float32)
                    quantiles, prob_up, vol = model['model'](X_test_tensor)
                    q10_pred = quantiles[:, 0].detach().cpu().numpy()
                    q50_pred = quantiles[:, 1].detach().cpu().numpy()
                    q90_pred = quantiles[:, 2].detach().cpu().numpy()
                    y_pred = q50_pred
                    coverage_10 = np.mean((y_test >= q10_pred) & (y_test <= q90_pred))
                    coverage_50 = np.mean((y_test >= q10_pred) & (y_test <= q50_pred))
            else:
                y_pred = model.predict(X_test)
                coverage_10 = coverage_50 = 0.0  # not available
            mse = float(np.mean((y_test - y_pred) ** 2))
            mae = float(np.mean(np.abs(y_test - y_pred)))
            denom = np.sum((y_test - np.mean(y_test)) ** 2)
            r2 = float(1 - (np.sum((y_test - y_pred) ** 2) / denom)) if denom != 0 else 0.0
            return {
                "mse": mse,
                "mae": mae,
                "r2": r2,
                "coverage_10_90": float(coverage_10),
                "coverage_10_50": float(coverage_50)
            }
        except Exception as e:
            logger.error(f"Model evaluation error: {str(e)}")
            return {
                "mse": float('inf'),
                "mae": float('inf'),
                "r2": 0.0,
                "coverage_10_90": 0.0,
                "coverage_10_50": 0.0
            }
    
    async def _save_model(
        self,
        model: Any,
        symbol: str,
        model_type: str,
        horizon_minutes: float
    ) -> str:
        """Save trained model to disk"""
        models_dir = "models"
        os.makedirs(models_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{model_type}_{horizon_minutes}m_{timestamp}.joblib"
        filepath = os.path.join(models_dir, filename)
        joblib.dump(model, filepath)
        return filepath
    
    async def _store_model_metadata(
        self,
        db: Session,
        symbol: str,
        model_type: str,
        model_path: str,
        metrics: Dict[str, float],
        horizon_minutes: float,
        hyperparams: Dict[str, Any] = None,
        initial_status: str = "active"
    ) -> int:
        """Store model metadata in database"""
        symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
        if not symbol_obj:
            raise ValueError(f"Symbol {symbol} not found")
        
        model = Model(
            name=f"{symbol}_{model_type}_{horizon_minutes}m",
            description=f"{self.model_types[model_type]} for {symbol} with {horizon_minutes}m horizon",
            artifact_uri=model_path,
            params={
                "symbol": symbol,
                "model_type": model_type,
                "horizon_minutes": horizon_minutes,
                "training_date": datetime.now().isoformat(),
                "hyperparams": hyperparams or {}
            },
            metrics=metrics,
            status=initial_status
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model.id
    
    async def _update_model_status(self, db: Session, model_id: int, status: str):
        """Update model status in database"""
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if model:
                model.status = status
                model.updated_at = datetime.now()
                db.commit()
                logger.info(f"Updated model {model_id} status to: {status}")
                
                # Auto-cleanup old models if this one completed successfully
                if status == 'completed':
                    await self._cleanup_old_models(db, model.symbol, model.timeframe)
            else:
                logger.warning(f"Model {model_id} not found for status update")
        except Exception as e:
            logger.error(f"Error updating model {model_id} status: {str(e)}")
            db.rollback()
    
    async def _cleanup_old_models(self, db: Session, symbol: str, timeframe: str, keep_count: int = 3):
        """Automatically cleanup old models, keeping only the most recent ones"""
        try:
            # Get all completed models for this symbol/timeframe combination
            models = db.query(Model).filter(
                Model.symbol == symbol,
                Model.timeframe == timeframe,
                Model.status == 'completed'
            ).order_by(Model.updated_at.desc()).all()
            
            if len(models) > keep_count:
                # Keep only the most recent models
                models_to_delete = models[keep_count:]
                
                for model in models_to_delete:
                    # Delete the model file
                    model_path = f"models/{model.filename}"
                    if os.path.exists(model_path):
                        os.remove(model_path)
                        logger.info(f"Deleted old model file: {model_path}")
                    
                    # Delete from database
                    db.delete(model)
                
                db.commit()
                logger.info(f"Cleaned up {len(models_to_delete)} old models for {symbol}_{timeframe}")
                
        except Exception as e:
            logger.error(f"Error during model cleanup: {str(e)}")
            db.rollback()
    
    async def _get_features_for_prediction(
        self,
        db: Session,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get features for making predictions"""
        symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
        if not symbol_obj:
            raise ValueError(f"Symbol {symbol} not found")
        features = db.query(Feature).filter(
            Feature.symbol_id == symbol_obj.id,
            Feature.timestamp >= start_date,
            Feature.timestamp <= end_date
        ).order_by(Feature.timestamp).all()
        result = []
        for feature in features:
            feature_dict = feature.payload.copy()
            feature_dict['timestamp'] = feature.timestamp
            result.append(feature_dict)
        return result
    
    async def _make_distributional_predictions(
        self,
        model: Any,
        features: List[Dict[str, Any]],
        model_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Make distributional predictions using trained model"""
        predictions = []
        for feature in features:
            try:
                feature_values = {k: v for k, v in feature.items() if k != 'timestamp'}
                X = np.array([list(feature_values.values())])
                
                if isinstance(model, dict) and model.get('type') == 'quantile_regression':
                    q10_pred = model['models'][0.1].predict(X)[0]
                    q50_pred = model['models'][0.5].predict(X)[0]
                    q90_pred = model['models'][0.9].predict(X)[0]
                    prob_up = 0.5 + (q50_pred / (abs(q10_pred) + abs(q90_pred) + 1e-8)) * 0.5
                    prob_up = max(0.0, min(1.0, prob_up))
                    volatility = abs(q90_pred - q10_pred) / 2
                elif isinstance(model, dict) and model.get('type') == 'transformer':
                    import torch
                    model['model'].eval()
                    with torch.no_grad():
                        X_tensor = torch.as_tensor(X, dtype=torch.float32)
                        quantiles, prob_up_t, vol_t = model['model'](X_tensor)
                        q10_pred = float(quantiles[0, 0].item())
                        q50_pred = float(quantiles[0, 1].item())
                        q90_pred = float(quantiles[0, 2].item())
                        prob_up = float(prob_up_t[0, 0].item())
                        volatility = float(vol_t[0, 0].item())
                else:
                    pred = float(model.predict(X)[0])
                    q10_pred = pred * 0.9
                    q50_pred = pred
                    q90_pred = pred * 1.1
                    prob_up = 0.5 + (pred / (abs(pred) + 0.01)) * 0.5
                    prob_up = max(0.0, min(1.0, prob_up))
                    volatility = abs(pred) * 0.1
                
                predictions.append({
                    "timestamp": feature['timestamp'],
                    "q10": float(q10_pred),
                    "q50": float(q50_pred),
                    "q90": float(q90_pred),
                    "prob_up": float(prob_up),
                    "volatility": float(volatility)
                })
            except Exception as e:
                logger.error(f"Prediction error for feature: {str(e)}")
                continue
        return predictions
    
    async def _store_forecasts(
        self,
        db: Session,
        symbol: str,
        predictions: List[Dict[str, Any]],
        model_id: int,
        horizon_minutes: float
    ):
        """Store forecasts in database"""
        try:
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            if not symbol_obj:
                raise ValueError(f"Symbol {symbol} not found")
            forecasts = []
            for pred in predictions:
                forecast = Forecast(
                    symbol_id=symbol_obj.id,
                    timestamp=pred['timestamp'],
                    horizon_minutes=horizon_minutes,
                    q10=pred['q10'],
                    q50=pred['q50'],
                    q90=pred['q90'],
                    prob_up=pred['prob_up'],
                    volatility=pred['volatility'],
                    model_id=model_id
                )
                forecasts.append(forecast)
            db.bulk_save_objects(forecasts)
            db.commit()
            logger.info(f"Stored {len(forecasts)} forecasts for {symbol}")
        except Exception as e:
            db.rollback()
            raise e
    
    async def train_model_brpc(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Train model using BRPC for high performance"""
        try:
            request_data = {
                "model_type": model_config.get("model_type", "Neural Network"),
                "training_data": model_config.get("training_data", {}),
                "hyperparameters": model_config.get("hyperparameters", {}),
                "strategy_id": model_config.get("strategy_id", 1),
                "symbol": model_config.get("symbol", "ES"),
                "timeframe": model_config.get("timeframe", "1d")
            }
            response = await self.brpc_service.call_method(
                method_name="train_model",
                request_data=request_data
            )
            if response and "error" not in response:
                return {
                    "success": True,
                    "model_id": response.get("model_id"),
                    "training_status": response.get("status"),
                    "message": response.get("message"),
                    "estimated_completion": response.get("estimated_completion"),
                    "brpc_mode": self.brpc_service.is_available()
                }
            else:
                return {
                    "success": False, 
                    "error": (response or {}).get("error", "BRPC call failed"),
                    "brpc_mode": False
                }
        except Exception as e:
            logger.error(f"Model training via BRPC failed: {e}")
            return {"success": False, "error": str(e), "brpc_mode": False}
    
    async def predict_brpc(self, model_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions using BRPC"""
        try:
            request_data = {"model_id": model_id, "input_data": input_data}
            response = await self.brpc_service.call_method(
                method_name="predict",
                request_data=request_data
            )
            if response and "error" not in response:
                return {
                    "success": True,
                    "prediction": response.get("prediction"),
                    "confidence": response.get("confidence"),
                    "model_id": response.get("model_id"),
                    "timestamp": response.get("timestamp"),
                    "brpc_mode": self.brpc_service.is_available()
                }
            else:
                return {"success": False, "error": (response or {}).get("error", "Prediction failed")}
        except Exception as e:
            logger.error(f"Prediction via BRPC failed: {e}")
            return {"success": False, "error": str(e)}
