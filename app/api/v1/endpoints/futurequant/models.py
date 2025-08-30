"""
FutureQuant Trader ML Model Endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.futurequant.model_service import FutureQuantModelService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ModelTrainRequest(BaseModel):
    symbol: str = Field(..., description="Futures symbol to train model for")
    model_type: str = Field(default="quantile_regression", description="Model type")
    horizon_minutes: int = Field(default=1440, description="Forecast horizon in minutes")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Test set size")

class ModelPredictRequest(BaseModel):
    model_id: int = Field(..., description="Trained model ID")
    symbol: str = Field(..., description="Futures symbol")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")

class ModelInfoResponse(BaseModel):
    id: int
    name: str
    description: str
    symbol: str
    model_type: str
    horizon_minutes: int
    status: str
    metrics: dict

@router.post("/train", response_model=dict)
async def train_model(
    request: ModelTrainRequest,
    background_tasks: BackgroundTasks,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Train a new ML model for futures prediction"""
    try:
        # Create model service
        model_service = FutureQuantModelService()
        
        # Train model
        result = await model_service.train_model(
            symbol=request.symbol,
            model_type=request.model_type,
            horizon_minutes=request.horizon_minutes,
            start_date=request.start_date,
            end_date=request.end_date,
            test_size=request.test_size
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_train_model",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_train_model",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Model training error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_train_model",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=dict)
async def predict_with_model(
    request: ModelPredictRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Make predictions using a trained model"""
    try:
        # Create model service
        model_service = FutureQuantModelService()
        
        # Make predictions
        result = await model_service.predict(
            model_id=request.model_id,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_predict",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_predict",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_predict",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_model_types(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get available model types"""
    try:
        # Create model service
        model_service = FutureQuantModelService()
        
        model_types = []
        for key, name in model_service.model_types.items():
            model_types.append({
                "key": key,
                "name": name,
                "description": f"{name} model for futures prediction"
            })
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_model_types",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return {
            "success": True,
            "model_types": model_types
        }
        
    except Exception as e:
        logger.error(f"Error getting model types: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_model_types",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/horizons")
async def get_forecast_horizons(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get available forecast horizons"""
    try:
        # Create model service
        model_service = FutureQuantModelService()
        
        horizons = []
        for minutes in model_service.horizons:
            if minutes == 60:
                description = "1 hour"
            elif minutes == 240:
                description = "4 hours"
            elif minutes == 1440:
                description = "1 day"
            else:
                description = f"{minutes} minutes"
            
            horizons.append({
                "minutes": minutes,
                "description": description
            })
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_horizons",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return {
            "success": True,
            "horizons": horizons
        }
        
    except Exception as e:
        logger.error(f"Error getting horizons: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_horizons",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_model_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get ML model system status"""
    try:
        # Create model service
        model_service = FutureQuantModelService()
        
        status = {
            "available_model_types": list(model_service.model_types.keys()),
            "total_model_types": len(model_service.model_types),
            "available_horizons": model_service.horizons,
            "training_requirements": {
                "min_training_samples": 100,
                "recommended_samples": 500,
                "feature_requirements": "All features must be computed before training",
                "data_quality": "No missing values, proper time alignment"
            },
            "model_capabilities": {
                "quantile_regression": "Distributional forecasts (q10, q50, q90)",
                "random_forest": "Point predictions with uncertainty",
                "neural_network": "Non-linear pattern recognition",
                "gradient_boosting": "Ensemble learning with regularization"
            }
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_model_status",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_model_status",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-brpc")
async def train_model_brpc(
    model_config: Dict[str, Any],
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Train model using BRPC for high performance"""
    try:
        model_service = FutureQuantModelService()
        result = await model_service.train_model_brpc(model_config)
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futurequant_train_model_brpc",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futurequant_train_model_brpc",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
    except Exception as e:
        logger.error(f"BRPC model training error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_train_model_brpc",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-brpc")
async def predict_brpc(
    model_id: str,
    input_data: Dict[str, Any],
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Make predictions using BRPC"""
    try:
        model_service = FutureQuantModelService()
        result = await model_service.predict_brpc(model_id, input_data)
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futurequant_predict_brpc",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futurequant_predict_brpc",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
    except Exception as e:
        logger.error(f"BRPC prediction error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_predict_brpc",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
