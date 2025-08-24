from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ....services.ai_service import AsyncAIService
from ....services.intention_interpreter_service import IntentionInterpreterService
from ....services.cache_service import AsyncCacheService
from ....services.usage_service import AsyncUsageService
from ....core.dependencies import get_ai_service, get_cache_service, get_usage_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class UserProfile(BaseModel):
    profile: str

class TargetPersonProfile(BaseModel):
    profile: str

class IntentionAnalysisRequest(BaseModel):
    user_profile: UserProfile
    target_person_profile: TargetPersonProfile
    use_case: str

class IntentionAnalysisResponse(BaseModel):
    success: bool
    intention: str
    rationale: List[str]
    reflective_question: str
    error: Optional[str] = None

@router.post("/analyze-intention", response_model=IntentionAnalysisResponse)
async def analyze_intention(
    request: IntentionAnalysisRequest,
    ai_service: AsyncAIService = Depends(get_ai_service),
    cache_service: AsyncCacheService = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Analyze the intention of a target person based on user profile, target profile, and specific use case.
    Uses clinical psychological assessment framework with evidence-based analysis.
    """
    try:
        # Create the intention interpreter service
        intention_service = IntentionInterpreterService(ai_service)
        
        # Analyze the intention
        result = await intention_service.analyze_intention(
            user_profile=request.user_profile.dict(),
            target_person_profile=request.target_person_profile.dict(),
            use_case=request.use_case
        )
        
        # Track usage
        await usage_service.track_request(
            endpoint="intention_interpreter",
            model="mistral-small",
            success=result.get("success", False)
        )
        
        # Return the result
        return IntentionAnalysisResponse(
            success=result.get("success", False),
            intention=result.get("intention", "unknown"),
            rationale=result.get("rationale", []),
            reflective_question=result.get("reflective_question", ""),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in intention analysis: {str(e)}")
        await usage_service.track_request(
            endpoint="intention_interpreter",
            model="mistral-small",
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for the intention interpreter service."""
    return {"status": "healthy", "service": "intention_interpreter"}
