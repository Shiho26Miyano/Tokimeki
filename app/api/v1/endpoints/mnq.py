"""
MNQ Investment endpoints
"""
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.core.dependencies import get_cache_service, get_usage_service
from app.services.mnq_investment_service import AsyncMNQInvestmentService
from app.services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class MNQInvestmentRequest(BaseModel):
    weekly_amount: float = Field(default=1000.0, ge=100, le=10000, description="Weekly investment amount in USD")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")

class MNQPerformanceResponse(BaseModel):
    success: bool
    weekly_amount: float
    start_date: str
    end_date: str
    total_weeks: int
    total_invested: float
    current_value: float
    total_return: float
    weekly_breakdown: List[dict]
    performance_metrics: dict
    equity_curve: List[dict]

@router.post("/calculate", response_model=MNQPerformanceResponse)
async def calculate_mnq_dca(
    request: MNQInvestmentRequest,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Calculate MNQ weekly DCA performance"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting MNQ DCA calculation: ${request.weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=request.weekly_amount,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if not result:
            logger.error("No result returned from MNQ service")
            raise HTTPException(status_code=500, detail="MNQ calculation failed - no result returned")
        
        logger.info(f"MNQ DCA calculation completed successfully")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_calculate",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_calculate",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ DCA calculation error: {e}")
        
        if "No data available" in str(e):
            raise HTTPException(status_code=404, detail="No MNQ futures data available")
        elif "yfinance" in str(e).lower():
            raise HTTPException(status_code=503, detail="MNQ data service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail=f"MNQ calculation failed: {str(e)}")

@router.get("/equity")
async def get_mnq_equity(
    weekly_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ equity curve data"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Fetching MNQ equity curve: ${weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance to get equity curve
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=weekly_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result or 'equity_curve' not in result:
            raise HTTPException(status_code=500, detail="Failed to generate equity curve")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_equity",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "equity_curve": result['equity_curve'],
            "weekly_amount": weekly_amount,
            "start_date": result['start_date'],
            "end_date": result['end_date']
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_equity",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ equity curve error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch equity curve: {str(e)}")

@router.get("/metrics")
async def get_mnq_metrics(
    weekly_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ performance metrics"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Fetching MNQ metrics: ${weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance to get metrics
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=weekly_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result or 'performance_metrics' not in result:
            raise HTTPException(status_code=500, detail="Failed to generate performance metrics")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_metrics",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "metrics": result['performance_metrics'],
            "summary": {
                "total_invested": result['total_invested'],
                "current_value": result['current_value'],
                "total_return": result['total_return'],
                "total_weeks": result['total_weeks']
            }
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_metrics",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/positions")
async def get_mnq_positions(
    weekly_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ position tracking data"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Fetching MNQ positions: ${weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance to get weekly breakdown
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=weekly_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result or 'weekly_breakdown' not in result:
            raise HTTPException(status_code=500, detail="Failed to generate position data")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_positions",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "positions": result['weekly_breakdown'],
            "summary": {
                "total_contracts": result.get('total_contracts', 0),
                "total_invested": result['total_invested'],
                "current_value": result['current_value']
            }
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_positions",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ positions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

@router.get("/available")
async def get_mnq_info(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ futures information"""
    
    start_time = time.time()
    
    try:
        logger.info("Fetching MNQ futures information")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_info",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "symbol": "MNQ=F",
            "name": "Micro E-mini NASDAQ-100 Futures",
            "contract_multiplier": 2,                # $2 per index point
            "point_value_usd": 2.0,                  # helpful explicit field
            "margin_model": "Approx. $1,000 initial / $800 maintenance per contract (varies)",
            "trading_hours": "Sun 6:00 PM – Fri 5:00 PM ET (with daily 5–6 PM pause)",
            "description": "Micro E-mini NASDAQ-100 futures contract, $2 per index point."
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_info",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch MNQ info: {str(e)}")

@router.get("/date-range")
async def get_mnq_date_range(
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get the maximum available date range for MNQ data"""
    
    start_time = time.time()
    
    try:
        logger.info("Fetching MNQ available date range")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Get available date range
        date_range = await mnq_service.get_max_available_date_range()
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_date_range",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "data": date_range
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_date_range",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ date range error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch date range: {str(e)}")
