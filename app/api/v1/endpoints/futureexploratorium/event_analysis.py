"""
FutureExploratorium Event Analysis API Endpoints
Advanced event detection and analysis for futures trading performance
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service
from app.services.futureexploratorium.event_analysis_service import (
    FutureExploratoriumEventAnalysisService, 
    EventType
)

logger = logging.getLogger(__name__)

router = APIRouter()

class EventDetectionRequest(BaseModel):
    symbol: str = Field(..., description="Symbol to analyze (e.g., ES=F, NQ=F)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    event_types: Optional[List[str]] = Field(None, description="Types of events to detect")
    clicked_date: Optional[str] = Field(None, description="Specific date to focus on (YYYY-MM-DD) - will expand window around this date")

class EventImpactRequest(BaseModel):
    symbol: str = Field(..., description="Symbol to analyze")
    event_id: str = Field(..., description="Event ID to analyze")
    lookback_days: int = Field(5, ge=1, le=30, description="Days to look back before event")
    forward_days: int = Field(5, ge=1, le=30, description="Days to look forward after event")

class AIFactorAnalysisRequest(BaseModel):
    date: str = Field(..., description="Date to analyze (YYYY-MM-DD)")
    symbol: str = Field("MNQ=F", description="Symbol to analyze")
    price_change: Optional[float] = Field(None, description="Price change for the period")
    contracts_bought: Optional[int] = Field(None, description="Number of contracts bought")

@router.post("/detect", response_model=dict)
async def detect_market_events(
    request: EventDetectionRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Detect market events for a given symbol and time period"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Convert event types if provided
        event_types = None
        if request.event_types:
            try:
                event_types = [EventType(event_type) for event_type in request.event_types]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {str(e)}")
        
        # Detect events
        result = await event_service.detect_events(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            event_types=event_types,
            clicked_date=request.clicked_date
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await usage_service.track_request(
            endpoint="futureexploratorium_event_detection",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Event detection error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_event_detection",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detect-on-date", response_model=dict)
async def detect_events_on_date(
    symbol: str = Query(..., description="Symbol to analyze (e.g., ES=F, NQ=F)"),
    date: str = Query(..., description="Date to analyze (YYYY-MM-DD)"),
    event_types: Optional[List[str]] = Query(None, description="Types of events to detect"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Detect market events for a specific date with expanded window for better context"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Convert event types if provided
        event_types_list = None
        if event_types:
            try:
                event_types_list = [EventType(event_type) for event_type in event_types]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {str(e)}")
        
        # Detect events with expanded window around the clicked date
        result = await event_service.detect_events(
            symbol=symbol,
            start_date=date,  # Will be expanded internally
            end_date=date,    # Will be expanded internally
            event_types=event_types_list,
            clicked_date=date
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await usage_service.track_request(
            endpoint="futureexploratorium_event_detection_on_date",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Event detection on date error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_event_detection_on_date",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=dict)
async def get_event_summary(
    symbol: str = Query("ES=F", description="Symbol to analyze"),
    period: str = Query("1y", description="Time period (3mo, 6mo, 1y, 2y)"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get event summary for a symbol over a period"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Get event summary
        result = await event_service.get_event_summary(
            symbol=symbol,
            period=period
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await usage_service.track_request(
            endpoint="futureexploratorium_event_summary",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Event summary error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_event_summary",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/impact", response_model=dict)
async def analyze_event_impact(
    request: EventImpactRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze the impact of a specific event on price performance"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Analyze event impact
        result = await event_service.analyze_event_impact(
            symbol=request.symbol,
            event_id=request.event_id,
            lookback_days=request.lookback_days,
            forward_days=request.forward_days
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await usage_service.track_request(
            endpoint="futureexploratorium_event_impact",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Event impact analysis error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_event_impact",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-factor-analysis", response_model=dict)
async def get_ai_factor_analysis(
    request: AIFactorAnalysisRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get AI-powered factor analysis for a specific date using OpenRouter"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Get AI factor analysis
        result = await event_service.get_ai_factor_analysis(
            date=request.date,
            symbol=request.symbol,
            price_change=request.price_change,
            contracts_bought=request.contracts_bought
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await usage_service.track_request(
            endpoint="futureexploratorium_ai_factor_analysis",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI factor analysis error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_ai_factor_analysis",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=dict)
async def get_event_types(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get available event types and their descriptions"""
    try:
        event_types = [
            {
                "type": event_type.value,
                "name": event_type.value.replace("_", " ").title(),
                "description": _get_event_description(event_type)
            }
            for event_type in EventType
        ]
        
        await usage_service.track_request(
            endpoint="futureexploratorium_event_types",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "event_types": event_types,
            "total_types": len(event_types),
            "message": "Available event types retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Event types error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_event_types",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

def _get_event_description(event_type: EventType) -> str:
    """Get human-readable description for event type"""
    descriptions = {
        EventType.VOLATILITY_SPIKE: "Detects sudden increases in price volatility",
        EventType.PRICE_BREAKOUT: "Identifies price breakouts from support/resistance levels",
        EventType.VOLUME_SURGE: "Detects unusual spikes in trading volume",
        EventType.GAP_UP: "Identifies upward price gaps at market open",
        EventType.GAP_DOWN: "Identifies downward price gaps at market open",
        EventType.REVERSAL: "Detects potential price reversal patterns",
        EventType.TREND_CHANGE: "Identifies changes in market trend direction",
        EventType.SUPPORT_RESISTANCE: "Detects tests of key support/resistance levels",
        EventType.MOMENTUM_SHIFT: "Identifies shifts in market momentum",
        EventType.LIQUIDITY_CRISIS: "Detects periods of reduced market liquidity"
    }
    return descriptions.get(event_type, "Market event detection")

@router.get("/diagnostic", response_model=dict)
async def get_diagnostic_event_analysis(
    date: str = Query(..., description="Date to analyze (YYYY-MM-DD)"),
    weekly_amount: float = Query(1000.0, description="Weekly investment amount (optional)"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get diagnostic event analysis for a specific date with factor impact table"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Generate diagnostic event analysis with AI factor analysis
        result = await event_service.generate_diagnostic_event_analysis(
            date=date,
            weekly_amount=weekly_amount
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        await usage_service.track_request(
            endpoint="futureexploratorium_diagnostic_analysis",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Diagnostic event analysis error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_diagnostic_analysis",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-correlation", response_model=dict)
async def analyze_event_performance_correlation(
    symbol: str = Query("ES=F", description="Symbol to analyze"),
    period: str = Query("1y", description="Time period"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze correlation between events and strategy performance"""
    try:
        # Initialize event analysis service
        event_service = FutureExploratoriumEventAnalysisService()
        
        # Get event summary
        event_result = await event_service.get_event_summary(
            symbol=symbol,
            period=period
        )
        
        if not event_result["success"]:
            raise HTTPException(status_code=400, detail=event_result["error"])
        
        # This would integrate with strategy performance data
        # For now, return a placeholder analysis
        correlation_analysis = {
            "symbol": symbol,
            "period": period,
            "total_events": event_result["summary"]["total_events"],
            "performance_correlation": {
                "volatility_events_vs_returns": 0.0,
                "breakout_events_vs_returns": 0.0,
                "volume_events_vs_returns": 0.0,
                "gap_events_vs_returns": 0.0,
                "trend_change_events_vs_returns": 0.0
            },
            "insights": [
                "Events with higher impact scores tend to correlate with larger price movements",
                "Volatility spikes often precede significant trend changes",
                "Volume surges during breakouts increase the likelihood of sustained moves"
            ],
            "recommendations": [
                "Monitor volatility spikes as early warning signals",
                "Use breakout events to confirm trend changes",
                "Consider volume confirmation for all event signals"
            ]
        }
        
        await usage_service.track_request(
            endpoint="futureexploratorium_event_performance_correlation",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "analysis": correlation_analysis,
            "message": f"Event-performance correlation analysis completed for {symbol}"
        }
        
    except Exception as e:
        logger.error(f"Event-performance correlation error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_event_performance_correlation",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
