"""
FutureQuant Trader Feature Engineering Endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.futurequant.feature_service import FutureQuantFeatureService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class FeatureComputeRequest(BaseModel):
    symbol: str = Field(..., description="Futures symbol to compute features for")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    recipe: str = Field(default="basic", description="Feature recipe (basic, momentum, trend, volatility, regime, full)")
    interval: str = Field(default="1d", description="Data interval")

class FeatureRecipeResponse(BaseModel):
    name: str
    description: str
    features: List[str]

class FeatureComputeResponse(BaseModel):
    success: bool
    symbol: str
    recipe: str
    features_count: int
    start_date: str
    end_date: str
    interval: str

@router.post("/compute", response_model=FeatureComputeResponse)
async def compute_features(
    request: FeatureComputeRequest,
    background_tasks: BackgroundTasks,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Compute technical features for a futures symbol"""
    try:
        # Create feature service
        feature_service = FutureQuantFeatureService()
        
        # Compute features
        result = await feature_service.compute_features(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            recipe=request.recipe,
            interval=request.interval
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_compute_features",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_compute_features",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Feature computation error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_compute_features",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recipes", response_model=List[FeatureRecipeResponse])
async def get_feature_recipes(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get available feature computation recipes"""
    try:
        # Create feature service
        feature_service = FutureQuantFeatureService()
        
        # Get recipes
        recipes = []
        for name, features in feature_service.feature_recipes.items():
            recipes.append({
                "name": name,
                "description": f"Features: {', '.join(features)}",
                "features": features
            })
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_feature_recipes",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return recipes
        
    except Exception as e:
        logger.error(f"Error getting feature recipes: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_feature_recipes",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recipes/{recipe_name}")
async def get_feature_recipe_details(
    recipe_name: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get detailed information about a specific feature recipe"""
    try:
        # Create feature service
        feature_service = FutureQuantFeatureService()
        
        if recipe_name not in feature_service.feature_recipes:
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_name} not found")
        
        features = feature_service.feature_recipes[recipe_name]
        
        recipe_info = {
            "name": recipe_name,
            "description": f"Features: {', '.join(features)}",
            "features": features,
            "feature_count": len(features),
            "categories": {
                "basic": ["returns", "log_returns", "volatility"],
                "momentum": ["rsi", "macd", "stoch"],
                "trend": ["sma", "ema", "bbands"],
                "volatility": ["atr", "bbands", "volatility"],
                "regime": ["regime_features", "calendar_dummies"]
            }
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_recipe_details",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return recipe_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe details: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_recipe_details",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_feature_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get feature engineering system status"""
    try:
        # Create feature service
        feature_service = FutureQuantFeatureService()
        
        status = {
            "available_recipes": list(feature_service.feature_recipes.keys()),
            "total_recipes": len(feature_service.feature_recipes),
            "supported_intervals": ["1d"],  # For now, only daily features
            "feature_categories": [
                "Basic (returns, volatility)",
                "Momentum (RSI, MACD, Stochastic)",
                "Trend (SMA, EMA, Bollinger Bands)",
                "Volatility (ATR, BB width)",
                "Regime (trend strength, volatility regime)",
                "Calendar (day of week, month, quarter)"
            ],
            "computation_methods": [
                "Rolling windows",
                "Technical indicators",
                "Statistical measures",
                "Calendar features"
            ]
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_feature_status",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting feature status: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_feature_status",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def compute_features_batch(
    symbols: List[str] = Field(..., description="List of symbols to compute features for"),
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Field(..., description="End date (YYYY-MM-DD)"),
    recipe: str = Field(default="basic", description="Feature recipe"),
    interval: str = Field(default="1d", description="Data interval"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Compute features for multiple symbols in batch"""
    try:
        # Create feature service
        feature_service = FutureQuantFeatureService()
        
        results = {}
        total_features = 0
        
        for symbol in symbols:
            try:
                result = await feature_service.compute_features(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    recipe=recipe,
                    interval=interval
                )
                
                results[symbol] = result
                if result["success"]:
                    total_features += result["features_count"]
                    
            except Exception as e:
                results[symbol] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Calculate summary
        successful_symbols = [s for s, r in results.items() if r["success"]]
        failed_symbols = [s for s, r in results.items() if not r["success"]]
        
        summary = {
            "success": True,
            "total_symbols": len(symbols),
            "successful_symbols": len(successful_symbols),
            "failed_symbols": len(failed_symbols),
            "total_features_computed": total_features,
            "recipe": recipe,
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "results": results
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_compute_features_batch",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Batch feature computation error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_compute_features_batch",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
