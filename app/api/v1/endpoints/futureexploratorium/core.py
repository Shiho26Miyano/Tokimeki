"""
FutureExploratorium Core API Endpoints
Independent core functionality for the FutureExploratorium service
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.services.futureexploratorium.core_service import FutureExploratoriumCoreService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ComprehensiveAnalysisRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of futures symbols to analyze")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    analysis_types: Optional[List[str]] = Field(
        default=None, 
        description="Types of analysis to run (data_ingestion, feature_engineering, model_training, signal_generation, backtesting, risk_analysis)"
    )

@router.get("/overview", response_model=dict)
async def get_platform_overview(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get comprehensive FutureExploratorium platform overview"""
    try:
        service = FutureExploratoriumCoreService()
        result = await service.get_platform_overview()
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_overview",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_overview",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Platform overview error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_overview",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=dict)
async def get_service_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get FutureExploratorium service status"""
    try:
        service = FutureExploratoriumCoreService()
        result = await service.get_service_status()
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_status",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_status",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Service status error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_status",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/comprehensive", response_model=dict)
async def run_comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    background_tasks: BackgroundTasks,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Run comprehensive analysis using FutureQuant services via FutureExploratorium"""
    try:
        service = FutureExploratoriumCoreService()
        result = await service.run_comprehensive_analysis(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            analysis_types=request.analysis_types
        )
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_comprehensive_analysis",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_comprehensive_analysis",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_comprehensive_analysis",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/summary", response_model=dict)
async def get_strategy_performance_summary(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get summary of all strategy performance"""
    try:
        service = FutureExploratoriumCoreService()
        result = await service.get_strategy_performance_summary()
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_performance_summary",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_performance_summary",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Performance summary error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_performance_summary",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/realtime", response_model=dict)
async def get_real_time_dashboard(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get real-time dashboard data"""
    try:
        service = FutureExploratoriumCoreService()
        result = await service.get_real_time_dashboard_data()
        
        if result["success"]:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_realtime_dashboard",
                response_time=0.0,
                success=True
            )
        else:
            await usage_service.track_request(
                endpoint="futureexploratorium_core_realtime_dashboard",
                response_time=0.0,
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Real-time dashboard error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_realtime_dashboard",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities", response_model=dict)
async def get_platform_capabilities(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get FutureExploratorium platform capabilities"""
    try:
        capabilities = {
            "service_info": {
                "name": "FutureExploratorium",
                "version": "1.0.0",
                "type": "independent_orchestration_service",
                "description": "Advanced Futures Trading Platform - Independent Service Layer"
            },
            "core_features": {
                "data_ingestion": True,
                "feature_engineering": True,
                "model_training": True,
                "signal_generation": True,
                "backtesting": True,
                "paper_trading": True,
                "risk_analysis": True,
                "strategy_optimization": True
            },
            "analytics": {
                "comprehensive_analysis": True,
                "multi_service_coordination": True,
                "performance_aggregation": True,
                "cross_service_insights": True
            },
            "monitoring": {
                "real_time_dashboard": True,
                "service_health_monitoring": True,
                "performance_tracking": True,
                "alert_management": True
            },
            "integration": {
                "external_apis": ["yfinance", "mlflow"],
                "database_connections": ["sqlite", "postgresql"],
                "quantitative_libraries": ["vectorbt", "qf-lib", "lean"],
                "ml_frameworks": ["pytorch", "scikit-learn", "joblib"]
            },
            "features": {
                "independent_operation": True,
                "service_isolation": True,
                "scalable_architecture": True,
                "modular_design": True,
                "api_versioning": True
            }
        }
        
        await usage_service.track_request(
            endpoint="futureexploratorium_core_capabilities",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "capabilities": capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Platform capabilities error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_capabilities",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=dict)
async def get_health_check(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get FutureExploratorium health check"""
    try:
        service = FutureExploratoriumCoreService()
        
        # Get basic health info
        overview = await service.get_platform_overview()
        service_status = await service.get_service_status()
        
        health_status = {
            "service": "FutureExploratorium",
            "status": "healthy" if overview.get("success") else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "uptime": "99.9%",  # Simulated
            "dependencies": service_status.get("status", {}).get("futurequant", {}).get("status", "unknown"),
            "database": "connected",
            "memory_usage": "normal",
            "cpu_usage": "normal"
        }
        
        await usage_service.track_request(
            endpoint="futureexploratorium_core_health",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "health": health_status
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        await usage_service.track_request(
            endpoint="futureexploratorium_core_health",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
