"""
Consumer Options Dashboard - Simulation Integration Endpoints
Adds simulation features to consumer options dashboard
"""
import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.consumeroptions.dashboard_service import ConsumerOptionsDashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


class SimulationDataResponse(BaseModel):
    """Response for simulation data"""
    ticker: str
    date: str
    signal: Optional[dict] = None
    regime: Optional[dict] = None
    features: Optional[dict] = None
    portfolio: Optional[dict] = None
    error: Optional[str] = None


@router.get("/simulation/{ticker}", response_model=SimulationDataResponse)
async def get_simulation_data_for_ticker(
    ticker: str,
    date_str: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format (defaults to today)"),
    usage_service = None  # Optional dependency
):
    """
    Get simulation data (regime, signals, features) for a ticker
    
    This endpoint provides simulation features for the consumer options dashboard
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
        
        dashboard_service = ConsumerOptionsDashboardService()
        result = await dashboard_service.get_simulation_data(ticker.upper(), target_date)
        
        return SimulationDataResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting simulation data for {ticker}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

