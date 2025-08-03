"""
Speech analysis endpoints
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
class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en")

@router.post("/analyze")
async def analyze_speech(
    request: SpeechRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze speech text"""
    
    start_time = time.time()
    
    try:
        # Placeholder for speech analysis
        # In a real implementation, this would use the ML service
        speech_result = {
            "text": request.text,
            "language": request.language,
            "analysis": {
                "sentiment": "positive",
                "confidence": 0.85,
                "entities": [],
                "summary": "Speech analysis completed"
            }
        }
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="speech_analysis",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "result": speech_result,
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="speech_analysis",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Speech analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for speech service"""
    return {
        "status": "healthy",
        "service": "speech",
        "timestamp": time.time()
    } 