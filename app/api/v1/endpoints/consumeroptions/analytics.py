"""
Consumer Options Analytics API Endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.consumeroptions.analytics_service import ConsumerOptionsAnalyticsService
from app.services.consumeroptions.polygon_service import ConsumerOptionsPolygonService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service
from app.models.options_models import (
    AnalyticsRequest, AnalyticsResponse, CallPutRatios, 
    IVTermPoint, UnusualActivity
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for requests
class CallPutRatiosRequest(BaseModel):
    ticker: str = Field(..., description="Underlying ticker symbol")

class IVTermRequest(BaseModel):
    ticker: str = Field(..., description="Underlying ticker symbol")
    min_contracts: int = Field(default=3, description="Minimum contracts per expiry")

class UnusualActivityRequest(BaseModel):
    ticker: str = Field(..., description="Underlying ticker symbol")
    volume_threshold: Optional[float] = Field(None, description="Volume multiplier threshold")
    oi_threshold: Optional[float] = Field(None, description="OI multiplier threshold")

class MultiTickerAnalyticsRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols")
    analysis_types: List[str] = Field(
        default=["call_put_ratios", "iv_term", "unusual"],
        description="Types of analysis to perform"
    )

@router.post("/call-put-ratios", response_model=CallPutRatios)
async def get_call_put_ratios(
    request: CallPutRatiosRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Calculate call/put volume and OI ratios for ticker"""
    try:
        polygon_service = ConsumerOptionsPolygonService()
        analytics_service = ConsumerOptionsAnalyticsService()
        
        # Get option chain
        contracts = await polygon_service.get_option_chain_snapshot(request.ticker.upper())
        
        # Calculate ratios
        ratios = analytics_service.calculate_call_put_ratios(contracts, request.ticker.upper())
        
        await usage_service.track_request(
            endpoint="consumeroptions_call_put_ratios",
            response_time=0.0,
            success=True
        )
        
        return ratios
        
    except Exception as e:
        logger.error(f"Call/put ratios error for {request.ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_call_put_ratios",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await polygon_service.close()

@router.post("/iv-term-structure", response_model=List[IVTermPoint])
async def get_iv_term_structure(
    request: IVTermRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Calculate implied volatility term structure"""
    try:
        polygon_service = ConsumerOptionsPolygonService()
        analytics_service = ConsumerOptionsAnalyticsService()
        
        # Get option chain
        contracts = await polygon_service.get_option_chain_snapshot(request.ticker.upper())
        
        # Calculate IV term structure
        iv_term = analytics_service.calculate_iv_term_structure(contracts)
        
        # Filter by minimum contracts if specified
        if request.min_contracts > 1:
            iv_term = [point for point in iv_term if point.contract_count >= request.min_contracts]
        
        await usage_service.track_request(
            endpoint="consumeroptions_iv_term_structure",
            response_time=0.0,
            success=True
        )
        
        return iv_term
        
    except Exception as e:
        logger.error(f"IV term structure error for {request.ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_iv_term_structure",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await polygon_service.close()

@router.post("/unusual-activity", response_model=List[UnusualActivity])
async def get_unusual_activity(
    request: UnusualActivityRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Detect unusual options activity"""
    try:
        polygon_service = ConsumerOptionsPolygonService()
        analytics_service = ConsumerOptionsAnalyticsService()
        
        # Update thresholds if provided
        if request.volume_threshold:
            analytics_service.unusual_thresholds["volume_multiplier"] = request.volume_threshold
        if request.oi_threshold:
            analytics_service.unusual_thresholds["oi_multiplier"] = request.oi_threshold
        
        # Get option chain
        contracts = await polygon_service.get_option_chain_snapshot(request.ticker.upper())
        
        # Detect unusual activity
        unusual = analytics_service.detect_unusual_activity(contracts, request.ticker.upper())
        
        await usage_service.track_request(
            endpoint="consumeroptions_unusual_activity",
            response_time=0.0,
            success=True
        )
        
        return unusual
        
    except Exception as e:
        logger.error(f"Unusual activity error for {request.ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_unusual_activity",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await polygon_service.close()

@router.post("/multi-ticker", response_model=Dict[str, Any])
async def get_multi_ticker_analytics(
    request: MultiTickerAnalyticsRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get analytics for multiple tickers"""
    try:
        polygon_service = ConsumerOptionsPolygonService()
        analytics_service = ConsumerOptionsAnalyticsService()
        
        results = {}
        
        for ticker in request.tickers:
            try:
                ticker_upper = ticker.upper()
                
                # Get option chain
                contracts = await polygon_service.get_option_chain_snapshot(ticker_upper)
                
                ticker_results = {}
                
                # Calculate requested analytics
                if "call_put_ratios" in request.analysis_types:
                    ratios = analytics_service.calculate_call_put_ratios(contracts, ticker_upper)
                    ticker_results["call_put_ratios"] = ratios
                
                if "iv_term" in request.analysis_types:
                    iv_term = analytics_service.calculate_iv_term_structure(contracts)
                    ticker_results["iv_term_structure"] = iv_term
                
                if "unusual" in request.analysis_types:
                    unusual = analytics_service.detect_unusual_activity(contracts, ticker_upper)
                    ticker_results["unusual_activity"] = unusual
                
                results[ticker_upper] = ticker_results
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                results[ticker.upper()] = {"error": str(e)}
        
        # Generate market summary if call_put_ratios were calculated
        market_summary = None
        if "call_put_ratios" in request.analysis_types:
            ratios_dict = {}
            for ticker, data in results.items():
                if "call_put_ratios" in data and not isinstance(data["call_put_ratios"], str):
                    ratios_dict[ticker] = data["call_put_ratios"]
            
            if ratios_dict:
                market_summary = analytics_service.get_market_sentiment_summary(ratios_dict)
        
        await usage_service.track_request(
            endpoint="consumeroptions_multi_ticker_analytics",
            response_time=0.0,
            success=True
        )
        
        return {
            "tickers": results,
            "market_summary": market_summary,
            "analysis_types": request.analysis_types
        }
        
    except Exception as e:
        logger.error(f"Multi-ticker analytics error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_multi_ticker_analytics",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await polygon_service.close()

@router.get("/market-sentiment")
async def get_market_sentiment(
    tickers: str = Query(..., description="Comma-separated ticker symbols"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get overall market sentiment summary"""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        polygon_service = ConsumerOptionsPolygonService()
        analytics_service = ConsumerOptionsAnalyticsService()
        
        ratios_dict = {}
        
        for ticker in ticker_list:
            try:
                # Get option chain
                contracts = await polygon_service.get_option_chain_snapshot(ticker)
                
                # Calculate call/put ratios
                ratios = analytics_service.calculate_call_put_ratios(contracts, ticker)
                ratios_dict[ticker] = ratios
                
            except Exception as e:
                logger.error(f"Error processing {ticker} for market sentiment: {str(e)}")
                continue
        
        # Generate market summary
        market_summary = analytics_service.get_market_sentiment_summary(ratios_dict)
        
        await usage_service.track_request(
            endpoint="consumeroptions_market_sentiment",
            response_time=0.0,
            success=True
        )
        
        return {
            "market_summary": market_summary,
            "ticker_ratios": ratios_dict,
            "tickers_analyzed": len(ratios_dict)
        }
        
    except Exception as e:
        logger.error(f"Market sentiment error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_market_sentiment",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await polygon_service.close()

@router.get("/technical-indicators/{ticker}")
async def get_technical_indicators(
    ticker: str,
    days: int = Query(default=60, description="Days of historical data"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get technical indicators for underlying stock"""
    try:
        from datetime import date, timedelta
        
        polygon_service = ConsumerOptionsPolygonService()
        analytics_service = ConsumerOptionsAnalyticsService()
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get underlying data
        bars = await polygon_service.get_underlying_daily_bars(
            ticker.upper(), start_date.isoformat(), end_date.isoformat()
        )
        
        # Calculate technical indicators
        bars_with_indicators = analytics_service.calculate_technical_indicators(bars)
        
        await usage_service.track_request(
            endpoint="consumeroptions_technical_indicators",
            response_time=0.0,
            success=True
        )
        
        return {
            "ticker": ticker.upper(),
            "bars": bars_with_indicators,
            "total_bars": len(bars_with_indicators),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Technical indicators error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_technical_indicators",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await polygon_service.close()
