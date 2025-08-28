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

from app.models.trading_models import Symbol, Bar, Feature, Forecast, Model
from app.models.database import get_db

logger = logging.getLogger(__name__)

class DistModel(Protocol):
    """Protocol for distributional models"""
    def fit(self, X: np.ndarray, y: np.ndarray): ...
    def predict_dist(self, X: np.ndarray) -> Dict[str, np.ndarray]: ...

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
        
        self.horizons = [60, 240, 1440]  # 1h, 4h, 1d in minutes
        
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
            if horizon_minutes not in self.horizons:
                raise ValueError(f"Invalid horizon. Must be one of: {self.horizons}")
            
            # Set default dates if not provided
            if not start_date or not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # Get training data
            db = next(get_db())
            X_train, y_train, X_test, y_test = await self._prepare_training_data(
                db, symbol, start_date, end_date, horizon_minutes, test_size
            )
            
            if len(X_train) < 100:
                raise ValueError(f"Insufficient training data. Need at least 100 samples, got {len(X_train)}")
            
            # Train model
            model, metrics = await self._train_distributional_model(
                model_type, X_train, y_train, X_test, y_test, hyperparams
            )
            
            # Save model
            model_path = await self._save_model(model, symbol, model_type, horizon_minutes)
            
            # Store model metadata in database
            model_id = await self._store_model_metadata(
                db, symbol, model_type, model_path, metrics, horizon_minutes, hyperparams
            )
            
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
            logger.error(f"Model training error for {symbol}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
        horizon_minutes: int,
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
        
        # Create DataFrame
        data = []
        for i, bar in enumerate(bars):
            if i + horizon_minutes >= len(bars):
                break
            
            # Get current features
            feature = next((f for f in features if f.timestamp == bar.timestamp), None)
            if not feature:
                continue
            
            # Get future price (target) - STRICT TIME-BASED SPLIT
            future_bar = bars[i + horizon_minutes]
            future_return = (future_bar.close - bar.close) / bar.close
            
            # Combine features
            row = feature.payload.copy()
            row['future_return'] = future_return
            row['timestamp'] = bar.timestamp
            data.append(row)
        
        if not data:
            raise ValueError("No valid training data found")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df = df.dropna()
        
        if len(df) < 100:
            raise ValueError(f"Insufficient data after preprocessing. Got {len(df)} samples")
        
        # Prepare features and target
        feature_cols = [col for col in df.columns if col not in ['future_return', 'timestamp']]
        X = df[feature_cols].values
        y = df['future_return'].values
        
        # STRICT TIME-BASED SPLIT (no shuffling)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        return X_train, y_train, X_test, y_test
    
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
        if model_type == "quantile_regression":
            return await self._train_quantile_regression(X_train, y_train, X_test, y_test, hyperparams)
        elif model_type == "random_forest":
            return await self._train_random_forest(X_train, y_train, X_test, y_test, hyperparams)
        elif model_type == "neural_network":
            return await self._train_neural_network(X_train, y_train, X_test, y_test, hyperparams)
        elif model_type == "gradient_boosting":
            return await self._train_gradient_boosting(X_train, y_train, X_test, y_test, hyperparams)
        elif model_type == "transformer":
            return await self._train_transformer(X_train, y_train, X_test, y_test, hyperparams)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
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
        
        # Default hyperparameters
        default_params = {"alpha": 0.1, "solver": "highs"}
        if hyperparams:
            default_params.update(hyperparams)
        
        # Train models for different quantiles
        models = {}
        quantiles = [0.1, 0.5, 0.9]
        
        for q in quantiles:
            model = QuantileRegressor(quantile=q, **default_params)
            model.fit(X_train, y_train)
            models[q] = model
        
        # Create ensemble model
        ensemble_model = {
            'type': 'quantile_regression',
            'models': models,
            'quantiles': quantiles,
            'hyperparams': default_params
        }
        
        # Evaluate
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
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError("PyTorch required for transformer models")
        
        # Default hyperparameters
        default_params = {
            "d_model": 64,
            "n_heads": 4,
            "n_layers": 2,
            "dropout": 0.1,
            "lr": 0.001,
            "epochs": 100,
            "batch_size": 32
        }
        if hyperparams:
            default_params.update(hyperparams)
        
        # Create transformer model
        class FutureQuantTransformer(nn.Module):
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
                x = self.input_projection(x)
                x = self.transformer(x)
                quantiles = self.quantile_head(x)
                prob_up = torch.sigmoid(self.prob_head(x))
                vol = torch.exp(self.vol_head(x))  # Ensure positive volatility
                return quantiles, prob_up, vol
        
        # Initialize model
        model = FutureQuantTransformer(
            input_dim=X_train.shape[1],
            d_model=default_params["d_model"],
            n_heads=default_params["n_heads"],
            n_layers=default_params["n_layers"],
            dropout=default_params["dropout"]
        )
        
        # Training setup
        optimizer = optim.Adam(model.parameters(), lr=default_params["lr"])
        criterion = nn.MSELoss()
        
        # Convert to PyTorch tensors
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.FloatTensor(y_train)
        
        # Training loop
        model.train()
        for epoch in range(default_params["epochs"]):
            optimizer.zero_grad()
            
            # Forward pass
            quantiles, prob_up, vol = model(X_train_tensor)
            
            # Distributional loss (pinball loss for quantiles + volatility penalty)
            q10, q50, q90 = quantiles[:, 0], quantiles[:, 1], quantiles[:, 2]
            
            # Pinball loss for quantiles
            q10_loss = torch.mean(torch.max((0.1 - 1) * (y_train_tensor - q10), 0.1 * (y_train_tensor - q10)))
            q50_loss = torch.mean(torch.max((0.5 - 1) * (y_train_tensor - q50), 0.5 * (y_train_tensor - q50)))
            q90_loss = torch.mean(torch.max((0.9 - 1) * (y_train_tensor - q90), 0.9 * (y_train_tensor - q90)))
            
            # Volatility penalty
            vol_loss = torch.mean(torch.abs(vol - torch.std(y_train_tensor)))
            
            # Total loss
            total_loss = q10_loss + q50_loss + q90_loss + 0.1 * vol_loss
            
            # Backward pass
            total_loss.backward()
            optimizer.step()
        
        # Create model wrapper
        transformer_model = {
            'type': 'transformer',
            'model': model,
            'hyperparams': default_params,
            'input_dim': X_train.shape[1]
        }
        
        # Evaluate
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
        
        # Default hyperparameters
        default_params = {"n_estimators": 100, "max_depth": 10, "random_state": 42}
        if hyperparams:
            default_params.update(hyperparams)
        
        model = RandomForestRegressor(**default_params)
        model.fit(X_train, y_train)
        
        # Evaluate
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
        
        # Default hyperparameters
        default_params = {"hidden_layer_sizes": (100, 50), "max_iter": 500, "random_state": 42}
        if hyperparams:
            default_params.update(hyperparams)
        
        model = MLPRegressor(**default_params)
        model.fit(X_train, y_train)
        
        # Evaluate
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
        
        # Default hyperparameters
        default_params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
        if hyperparams:
            default_params.update(hyperparams)
        
        model = GradientBoostingRegressor(**default_params)
        model.fit(X_train, y_train)
        
        # Evaluate
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
                # For quantile regression ensemble
                predictions = []
                for q in model['quantiles']:
                    pred = model['models'][q].predict(X_test)
                    predictions.append(pred)
                
                # Calculate metrics for median prediction
                y_pred = predictions[1]  # 0.5 quantile
                
                # Distributional metrics
                q10_pred, q50_pred, q90_pred = predictions[0], predictions[1], predictions[2]
                
                # Coverage metrics
                coverage_10 = np.mean((y_test >= q10_pred) & (y_test <= q90_pred))
                coverage_50 = np.mean((y_test >= q10_pred) & (y_test <= q50_pred))
                
            elif isinstance(model, dict) and model.get('type') == 'transformer':
                # For transformer model
                model['model'].eval()
                with torch.no_grad():
                    X_test_tensor = torch.FloatTensor(X_test)
                    quantiles, prob_up, vol = model['model'](X_test_tensor)
                    q10_pred, q50_pred, q90_pred = quantiles[:, 0].numpy(), quantiles[:, 1].numpy(), quantiles[:, 2].numpy()
                    y_pred = q50_pred
                    coverage_10 = np.mean((y_test >= q10_pred) & (y_test <= q90_pred))
                    coverage_50 = np.mean((y_test >= q10_pred) & (y_test <= q50_pred))
                
            else:
                # For single model
                y_pred = model.predict(X_test)
                coverage_10 = coverage_50 = 0.0  # Not available for non-distributional models
            
            # Calculate metrics
            mse = np.mean((y_test - y_pred) ** 2)
            mae = np.mean(np.abs(y_test - y_pred))
            r2 = 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
            
            metrics = {
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2),
                "coverage_10_90": float(coverage_10),
                "coverage_10_50": float(coverage_50)
            }
            
            return metrics
            
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
        horizon_minutes: int
    ) -> str:
        """Save trained model to disk"""
        # Create models directory if it doesn't exist
        models_dir = "models"
        os.makedirs(models_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{model_type}_{horizon_minutes}m_{timestamp}.joblib"
        filepath = os.path.join(models_dir, filename)
        
        # Save model
        joblib.dump(model, filepath)
        
        return filepath
    
    async def _store_model_metadata(
        self,
        db: Session,
        symbol: str,
        model_type: str,
        model_path: str,
        metrics: Dict[str, float],
        horizon_minutes: int,
        hyperparams: Dict[str, Any] = None
    ) -> int:
        """Store model metadata in database"""
        # Get symbol
        symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
        if not symbol_obj:
            raise ValueError(f"Symbol {symbol} not found")
        
        # Create model record
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
            status="active"
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        return model.id
    
    async def _get_features_for_prediction(
        self,
        db: Session,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get features for making predictions"""
        # Get symbol
        symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
        if not symbol_obj:
            raise ValueError(f"Symbol {symbol} not found")
        
        # Get features
        features = db.query(Feature).filter(
            Feature.symbol_id == symbol_obj.id,
            Feature.timestamp >= start_date,
            Feature.timestamp <= end_date
        ).order_by(Feature.timestamp).all()
        
        # Convert to list of dicts
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
                # Extract feature values (exclude timestamp)
                feature_values = {k: v for k, v in feature.items() if k != 'timestamp'}
                
                # Convert to numpy array
                X = np.array([list(feature_values.values())])
                
                if isinstance(model, dict) and model.get('type') == 'quantile_regression':
                    # For quantile regression ensemble
                    q10_pred = model['models'][0.1].predict(X)[0]
                    q50_pred = model['models'][0.5].predict(X)[0]
                    q90_pred = model['models'][0.9].predict(X)[0]
                    
                    # Calculate probability of up movement
                    prob_up = 0.5 + (q50_pred / (abs(q10_pred) + abs(q90_pred))) * 0.5
                    prob_up = max(0.0, min(1.0, prob_up))
                    
                    # Calculate volatility
                    volatility = abs(q90_pred - q10_pred) / 2
                    
                elif isinstance(model, dict) and model.get('type') == 'transformer':
                    # For transformer model
                    model['model'].eval()
                    with torch.no_grad():
                        X_tensor = torch.FloatTensor(X)
                        quantiles, prob_up, vol = model['model'](X_tensor)
                        q10_pred = quantiles[0, 0].item()
                        q50_pred = quantiles[0, 1].item()
                        q90_pred = quantiles[0, 2].item()
                        prob_up = prob_up[0, 0].item()
                        volatility = vol[0, 0].item()
                
                else:
                    # For single model
                    pred = model.predict(X)[0]
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
        horizon_minutes: int
    ):
        """Store forecasts in database"""
        try:
            # Get symbol
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            if not symbol_obj:
                raise ValueError(f"Symbol {symbol} not found")
            
            # Create forecast objects
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
            
            # Bulk insert
            db.bulk_save_objects(forecasts)
            db.commit()
            
            logger.info(f"Stored {len(forecasts)} forecasts for {symbol}")
            
        except Exception as e:
            db.rollback()
            raise e
