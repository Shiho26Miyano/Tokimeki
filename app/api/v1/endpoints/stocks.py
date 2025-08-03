"""
Stock endpoints
"""
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from ....core.dependencies import get_stock_service, get_usage_service
from ....services.stock_service import AsyncStockService
from ....services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class StockAnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    strategy: str = Field(default="trend")
    period: str = Field(default="1y")

class StockHistoryRequest(BaseModel):
    symbols: List[str] = Field(..., min_items=1, max_items=10)
    days: int = Field(default=1095, ge=1, le=3650)

@router.post("/analyze")
async def analyze_stock(
    request: StockAnalysisRequest,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze stock using trading strategies"""
    
    start_time = time.time()
    
    try:
        # Validate symbol
        symbol = request.symbol.upper()
        
        # Get stock data and perform analysis
        result = await stock_service.analyze_stock(
            symbol=symbol,
            strategy=request.strategy,
            period=request.period
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "strategy": request.strategy,
            "period": request.period,
            "latest_signals": result.get("latest_signals", {}),
            "metrics": result.get("metrics", {}),
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Stock analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_stock_history(
    symbols: str,
    days: int = 1095,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get historical stock data"""
    
    start_time = time.time()
    
    try:
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        # Get historical data
        result = await stock_service.get_stock_history(
            symbols=symbol_list,
            days=days
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="stock_history",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="stock_history",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Stock history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available_companies")
async def get_available_companies(
    stock_service: AsyncStockService = Depends(get_stock_service)
):
    """Get list of available companies"""
    try:
        companies = await stock_service.get_available_companies()
        return companies
    except Exception as e:
        logger.error(f"Error getting companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available_tickers")
async def get_available_tickers(
    stock_service: AsyncStockService = Depends(get_stock_service)
):
    """Get list of available tickers"""
    try:
        tickers = await stock_service.get_available_tickers()
        return tickers
    except Exception as e:
        logger.error(f"Error getting tickers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for stock service"""
    return {
        "status": "healthy",
        "service": "stocks",
        "timestamp": time.time()
    } 