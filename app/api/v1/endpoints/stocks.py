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
        logger.info(f"Starting stock analysis for {symbol} with strategy {request.strategy}")
        
        # Get stock data and perform analysis
        result = await stock_service.analyze_stock(
            symbol=symbol,
            strategy=request.strategy,
            period=request.period
        )
        
        if not result:
            logger.error(f"No result returned from stock service for {symbol}")
            raise HTTPException(status_code=500, detail="Stock analysis failed - no result returned")
        
        logger.info(f"Stock analysis completed for {symbol}: {result}")
        
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
        
        logger.error(f"Stock analysis error for {request.symbol}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        
        # Return a more detailed error response
        if "No data available" in str(e):
            raise HTTPException(status_code=404, detail=f"No stock data available for {request.symbol}")
        elif "yfinance" in str(e).lower():
            raise HTTPException(status_code=503, detail="Stock data service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail=f"Stock analysis failed: {str(e)}")

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

@router.get("/volatility_event_correlation")
async def get_volatility_event_correlation(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    window: int = 30,
    years: int = 2,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get volatility event correlation data"""
    start_time = time.time()
    
    try:
        # Get volatility correlation data
        result = await stock_service.get_volatility_event_correlation(
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            window=window,
            years=years
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_event_correlation",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_event_correlation",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Volatility event correlation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/volatility_regime/analyze")
async def analyze_volatility_regime(
    request: Request,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze volatility regime"""
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            symbol = body.get("symbol", "").upper()
            start_date = body.get("start_date")
            end_date = body.get("end_date")
            window = body.get("window", 30)
        else:
            # Handle form data
            form_data = await request.form()
            symbol = form_data.get("symbol", "").upper()
            start_date = form_data.get("start_date")
            end_date = form_data.get("end_date")
            window = int(form_data.get("window", 30))
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Get volatility regime analysis
        result = await stock_service.analyze_volatility_regime(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            window=window
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_regime_analyze",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_regime_analyze",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Volatility regime analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for stock service"""
    return {
        "status": "healthy",
        "service": "stocks",
        "timestamp": time.time()
    } 