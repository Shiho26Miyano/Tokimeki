"""
API endpoints for Decision Reflection Engine
Stateless computation endpoints for trader decision reflection tool
"""
import logging
from typing import Literal
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import ValidationError

from ....models.decision_reflection_models import TrajectoryResponse, DayData
from ....services.decision_reflection import DecisionReflectionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instance
_decision_reflection_service: DecisionReflectionService = None


def get_decision_reflection_service() -> DecisionReflectionService:
    """Dependency to get Decision Reflection service instance"""
    global _decision_reflection_service
    if _decision_reflection_service is None:
        _decision_reflection_service = DecisionReflectionService()
    return _decision_reflection_service


@router.get("/trajectory", response_model=TrajectoryResponse)
async def get_trajectory(
    intensity: int = Query(60, ge=0, le=100, description="Decision impact intensity (0-100)"),
    days: int = Query(14, ge=1, le=30, description="Number of days in trajectory"),
    mode: Literal["with", "without"] = Query("with", description="Reflection mode: 'with' or 'without'"),
    service: DecisionReflectionService = Depends(get_decision_reflection_service)
):
    """
    Get trajectory data for decision reflection visualization
    
    Args:
        intensity: Decision impact intensity (0-100)
        days: Number of days in trajectory (1-30)
        mode: Reflection mode - "with" for reflection, "without" for ignoring
        
    Returns:
        TrajectoryResponse with trajectory data and decision quality score
    """
    try:
        # Validate inputs (Query validation already handles this, but keeping for clarity)
        if intensity < 0 or intensity > 100:
            raise HTTPException(status_code=400, detail="intensity must be between 0 and 100")
        if days < 1 or days > 30:
            raise HTTPException(status_code=400, detail="days must be between 1 and 30")
        
        # Build trajectory data
        trajectory_data = service.build_trajectory(intensity, days)
        
        # Calculate score
        score = service.calculate_score(trajectory_data, mode, intensity)
        
        # Convert to DayData models
        day_data_list = [DayData(**day) for day in trajectory_data]
        
        return TrajectoryResponse(
            intensity=intensity,
            days=days,
            mode=mode,
            score=score,
            data=day_data_list
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in trajectory endpoint: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Error in trajectory endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

