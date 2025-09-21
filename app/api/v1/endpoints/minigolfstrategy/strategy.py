"""
CaddieAlpha Strategy Endpoints
Executive golf strategy recommendations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.models.golf_models import CaddieAlphaRequest, CaddieAlphaResponse
from app.services.minigolfstrategy.strategy_service import executive_caddie_calculator
from app.services.minigolfstrategy.clients.golfcourse_api import golf_course_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/strategy/caddiealpha", response_model=CaddieAlphaResponse)
async def calculate_caddie_alpha_strategy(request: CaddieAlphaRequest):
    """
    Calculate CaddieAlpha™ Risk-Reward Strategy
    
    Provides executive-level golf strategy recommendations using quantitative analysis:
    - Volatility analysis based on course slope and hole handicap
    - Expected strokes calculation for different strategies
    - Blow-up probability assessment
    - CaddieScore (Sharpe-like risk-adjusted return)
    - Per-hole Press/Protect recommendations
    """
    try:
        # Get course data from GolfCourseAPI
        course_data = await golf_course_client.get_course_details(request.course_id)
        
        if "error" in course_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Course not found: {course_data['error']}"
            )
        
        # Calculate CaddieAlpha strategy
        strategy_result = executive_caddie_calculator.calculate_caddie_alpha_strategy(
            course_data=course_data,
            tee_name=request.tee_name,
            gender=request.gender,
            risk_budget=request.risk_budget
        )
        
        # Filter holes if specific holes requested
        if request.holes:
            filtered_holes = [
                hole for hole in strategy_result["holes"] 
                if hole["hole"] in request.holes
            ]
            strategy_result["holes"] = filtered_holes
            
            # Recalculate summary for filtered holes
            press_holes = [h["hole"] for h in filtered_holes if h["recommended"] == "press"]
            protect_holes = [h["hole"] for h in filtered_holes if h["recommended"] == "protect"]
            total_risk = sum(h["risk_cost"] for h in filtered_holes)
            total_caddie = sum(h["caddie_score"] for h in filtered_holes)
            
            strategy_result["summary"]["press_holes"] = press_holes
            strategy_result["protect_holes"] = protect_holes
            strategy_result["summary"]["risk_budget_used"] = round(total_risk, 1)
            strategy_result["summary"]["caddie_score_total"] = round(total_caddie, 1)
            strategy_result["summary"]["total_holes"] = len(filtered_holes)
        
        logger.info(f"CaddieAlpha strategy calculated for course {request.course_id}, "
                   f"tee {request.tee_name}, gender {request.gender}")
        
        return CaddieAlphaResponse(**strategy_result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating CaddieAlpha strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/strategy/health")
async def strategy_health_check():
    """Health check for strategy service"""
    return {
        "status": "healthy",
        "service": "CaddieAlpha Strategy Calculator",
        "version": "1.0.0"
    }
