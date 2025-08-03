"""
Sentiment analysis endpoints
"""
import time
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ....core.dependencies import get_usage_service
from ....services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    model: str = Field(default="distilbert-base-uncased-finetuned-sst-2-english")

@router.post("/analyze")
async def analyze_sentiment(
    request: SentimentRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze sentiment of text"""
    
    start_time = time.time()
    
    try:
        # Placeholder for sentiment analysis
        # In a real implementation, this would use the ML service
        sentiment_result = {
            "text": request.text,
            "sentiment": "positive",  # Placeholder
            "confidence": 0.85,       # Placeholder
            "model": request.model
        }
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="sentiment_analysis",
            model=request.model,
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "result": sentiment_result,
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="sentiment_analysis",
            model=request.model,
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for sentiment service"""
    return {
        "status": "healthy",
        "service": "sentiment",
        "timestamp": time.time()
    } 