"""
Monitoring endpoints
"""
import time
import logging
from fastapi import APIRouter, HTTPException, Depends
from ....core.dependencies import get_ai_service
from ....services.ai_service import AsyncAIService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": time.time()
    }

@router.get("/test")
async def test():
    """Basic test endpoint"""
    return {
        "success": True,
        "message": "Test endpoint working",
        "timestamp": time.time()
    }

@router.get("/test-api")
async def test_api(
    ai_service: AsyncAIService = Depends(get_ai_service)
):
    """Test AI API connectivity"""
    try:
        # Test simple API call
        result = await ai_service.chat(
            message="Hello, this is a test.",
            model="mistral-small",
            temperature=0.7,
            max_tokens=50
        )
        
        return {
            "success": True,
            "message": "AI API test successful",
            "response": result.get("response", "")[:100] + "...",
            "model": result.get("model"),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"AI API test failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI API test failed: {str(e)}")

@router.get("/test-comparison")
async def test_comparison(
    ai_service: AsyncAIService = Depends(get_ai_service)
):
    """Test model comparison functionality"""
    try:
        # Test model comparison
        result = await ai_service.compare_models(
            prompt="What is 2+2?",
            models=["mistral-small", "deepseek-chat"],
            temperature=0.7,
            max_tokens=100
        )
        
        successful_models = len([r for r in result if r.get("success", False)])
        
        return {
            "success": True,
            "message": f"Model comparison test successful - {successful_models} models responded",
            "total_models": len(result),
            "successful_models": successful_models,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Model comparison test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model comparison test failed: {str(e)}") 