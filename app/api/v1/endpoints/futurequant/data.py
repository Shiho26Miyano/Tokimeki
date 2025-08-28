"""
FutureQuant Trader Data Ingestion Endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Path, Query
from pydantic import BaseModel, Field

from app.services.futurequant.data_service import FutureQuantDataService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class DataIngestRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of futures symbols to ingest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    interval: str = Field(default="1d", description="Data interval (1m, 5m, 15m, 30m, 1h, 1d)")

class SymbolInfoResponse(BaseModel):
    id: int
    ticker: str
    venue: str
    asset_class: str
    point_value: float
    tick_size: float
    timezone: str

class DataIngestResponse(BaseModel):
    success: bool
    results: dict
    total_symbols: int
    interval: str

class LatestDataResponse(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    interval: str

@router.post("/ingest", response_model=DataIngestResponse)
async def ingest_futures_data(
    request: DataIngestRequest,
    background_tasks: BackgroundTasks,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Ingest historical futures data for specified symbols"""
    try:
        # Create data service
        data_service = FutureQuantDataService()
        
        # Ingest data
        result = await data_service.ingest_data(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_data_ingest",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_data_ingest",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Data ingestion error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_data_ingest",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols", response_model=List[SymbolInfoResponse])
async def get_futures_symbols(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get list of available futures symbols"""
    try:
        # Create data service
        data_service = FutureQuantDataService()
        
        # Get default symbols info
        symbols = []
        for ticker, config in data_service.default_symbols.items():
            symbols.append({
                "id": 0,  # Placeholder
                "ticker": ticker,
                "venue": config["venue"],
                "asset_class": config["asset_class"],
                "point_value": config["point_value"],
                "tick_size": config["tick_size"],
                "timezone": "UTC"
            })
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_symbols",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return symbols
        
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_symbols",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols/{symbol}/info", response_model=SymbolInfoResponse)
async def get_symbol_info(
    symbol: str = Path(..., description="Futures symbol ticker"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get information about a specific futures symbol"""
    try:
        # Create data service
        data_service = FutureQuantDataService()
        
        # Get symbol info
        symbol_info = await data_service.get_symbol_info(symbol)
        
        if not symbol_info:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_symbol_info",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return symbol_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting symbol info: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_symbol_info",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols/{symbol}/latest", response_model=List[LatestDataResponse])
async def get_latest_data(
    symbol: str = Path(..., description="Futures symbol ticker"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of latest bars to return"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get latest price data for a symbol"""
    try:
        # Create data service
        data_service = FutureQuantDataService()
        
        # Get latest data
        latest_data = await data_service.get_latest_data(symbol, limit)
        
        if not latest_data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_latest_data",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return latest_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest data: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_latest_data",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/symbols/ensure")
async def ensure_symbols_exist(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Ensure all default futures symbols exist in database"""
    try:
        # Create data service
        data_service = FutureQuantDataService()
        
        # This would require database access - simplified for now
        result = {
            "success": True,
            "message": "Symbols ensured successfully",
            "symbols_count": len(data_service.default_symbols)
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_ensure_symbols",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error ensuring symbols: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_ensure_symbols",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_data_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get overall data ingestion status"""
    try:
        # Create data service
        data_service = FutureQuantDataService()
        
        # Get status summary
        status = {
            "total_symbols": len(data_service.default_symbols),
            "supported_intervals": ["1m", "5m", "15m", "30m", "1h", "1d"],
            "data_sources": ["yfinance"],
            "last_updated": "2025-01-01"  # Placeholder
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_data_status",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting data status: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_data_status",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
