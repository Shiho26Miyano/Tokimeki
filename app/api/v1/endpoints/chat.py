"""
Chat endpoints
"""
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ....core.dependencies import get_ai_service, get_usage_service
from ....services.ai_service import AsyncAIService
from ....services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    model: str = Field(default="mistral-small")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    conversation_history: Optional[List[dict]] = Field(default=None)

class ModelComparisonRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    models: Optional[List[str]] = Field(default=None)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)

# Match original Flask endpoints
@router.post("/chat")
@limiter.limit("50/hour")
async def chat(
    request: Request,
    ai_service: AsyncAIService = Depends(get_ai_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Main chat endpoint with async AI service - handles both JSON and form data"""
    
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            message = body.get("message", "")
            model = body.get("model", "mistral-small")
            temperature = float(body.get("temperature", 0.7))
            max_tokens = int(body.get("max_tokens", 1000))
        else:
            # Handle form data (like original Flask app)
            form_data = await request.form()
            message = form_data.get("message", "")
            model = form_data.get("model", "mistral-small")
            temperature = float(form_data.get("temperature", 0.7))
            max_tokens = int(form_data.get("max_tokens", 1000))
        
        # Validate model
        if model not in ["mistral-small", "deepseek-chat", "deepseek-r1", "llama-3.1-405b"]:
            raise HTTPException(status_code=400, detail="Invalid model specified")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Make async API call
        result = await ai_service.chat(
            message=message,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="chat",
            model=model,
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "response": result["response"],
            "model": result["model"],
            "usage": result["usage"],
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="chat",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare_models")
@limiter.limit("10/hour")
async def compare_models(
    request: Request,
    ai_service: AsyncAIService = Depends(get_ai_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Compare multiple AI models concurrently"""
    
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            prompt = body.get("prompt", "")
            models = body.get("models", [])
            temperature = float(body.get("temperature", 0.7))
            max_tokens = int(body.get("max_tokens", 1000))
        else:
            # Handle form data
            form_data = await request.form()
            prompt = form_data.get("prompt", "")
            models_str = form_data.get("models", "")
            models = models_str.split(",") if models_str else []
            temperature = float(form_data.get("temperature", 0.7))
            max_tokens = int(form_data.get("max_tokens", 1000))
        
        # Validate models if provided
        if models:
            for model in models:
                if model not in ["mistral-small", "deepseek-chat", "deepseek-r1", "llama-3.1-405b"]:
                    raise HTTPException(status_code=400, detail=f"Invalid model: {model}")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Compare models concurrently
        results = await ai_service.compare_models(
            prompt=prompt,
            models=models,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="compare_models",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "results": results,
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="compare_models",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Model comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_models(
    ai_service: AsyncAIService = Depends(get_ai_service)
):
    """Get available AI models"""
    try:
        models = await ai_service.get_available_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock_symbols")
async def get_stock_symbols():
    """Get available stock symbols"""
    common_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "META", "name": "Meta Platforms Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "NFLX", "name": "Netflix Inc."},
        {"symbol": "AMD", "name": "Advanced Micro Devices Inc."},
        {"symbol": "INTC", "name": "Intel Corporation"}
    ]
    
    return {
        "success": True,
        "symbols": common_stocks
    }

@router.get("/health")
async def health_check():
    """Health check for chat service"""
    return {
        "status": "healthy",
        "service": "chat",
        "timestamp": time.time()
    } 