from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ....core.dependencies import get_portfolio_service
from ....services.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)
router = APIRouter()

class PortfolioRequest(BaseModel):
    """Portfolio analysis request model"""
    tickers: List[str]
    primary: str
    start: str
    end: str
    fee_bps: float = 1.0
    slip_bps: float = 2.0

class PortfolioResponse(BaseModel):
    """Portfolio analysis response model"""
    success: bool
    data: Dict[str, Any]
    message: str

@router.post("/analyze", response_model=PortfolioResponse)
async def analyze_portfolio(
    request: PortfolioRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """Run complete portfolio analysis with multi-agent workflow"""
    try:
        logger.info(f"Portfolio analysis request: {request.tickers}, primary: {request.primary}")
        
        # Run portfolio workflow
        config = {
            "tickers": request.tickers,
            "primary": request.primary,
            "start": request.start,
            "end": request.end,
            "fee_bps": request.fee_bps,
            "slip_bps": request.slip_bps
        }
        
        result = await portfolio_service.run_portfolio_workflow(config)
        
        # Convert pandas objects to serializable format
        serializable_result = {}
        for key, value in result.items():
            if key == "prices":
                serializable_result[key] = value.to_dict() if hasattr(value, 'to_dict') else str(value)
            elif key == "features":
                serializable_result[key] = {
                    ticker: {
                        col: series.to_dict() if hasattr(series, 'to_dict') else str(series)
                        for col, series in df.items()
                    }
                    for ticker, df in value.items()
                }
            elif key == "position":
                serializable_result[key] = {
                    ticker: pos.to_dict() if hasattr(pos, 'to_dict') else str(pos)
                    for ticker, pos in value.items()
                }
            elif key == "backtest_results":
                serializable_result[key] = {
                    k: v.to_dict() if hasattr(v, 'to_dict') else v
                    for k, v in value.items()
                }
            else:
                serializable_result[key] = value
        
        return PortfolioResponse(
            success=True,
            data=serializable_result,
            message="Portfolio analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Portfolio analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regimes")
async def get_market_regimes():
    """Get available market regime types"""
    regimes = [
        {"name": "Bull", "description": "Strong upward trend with positive momentum"},
        {"name": "Bear", "description": "Strong downward trend with negative momentum"},
        {"name": "High Volatility", "description": "Elevated volatility above historical average"},
        {"name": "Low Volatility", "description": "Below average volatility levels"},
        {"name": "Neutral", "description": "Sideways or mixed market conditions"}
    ]
    
    return {
        "success": True,
        "regimes": regimes
    }

@router.get("/strategies")
async def get_trading_strategies():
    """Get available trading strategy types"""
    strategies = [
        {
            "name": "Momentum",
            "description": "Follows strong trends with fast moving averages",
            "best_for": "Bull markets",
            "risk_level": "Medium"
        },
        {
            "name": "Mean Reversion",
            "description": "Trades against extremes using statistical measures",
            "best_for": "Bear markets, range-bound conditions",
            "risk_level": "High"
        },
        {
            "name": "Volatility Breakout",
            "description": "Captures volatility expansion periods",
            "best_for": "High volatility regimes",
            "risk_level": "High"
        },
        {
            "name": "Trend Following",
            "description": "Classical moving average crossover approach",
            "best_for": "Trending markets",
            "risk_level": "Medium"
        }
    ]
    
    return {
        "success": True,
        "strategies": strategies
    }

@router.get("/metrics")
async def get_risk_metrics():
    """Get risk metric definitions and thresholds"""
    metrics = {
        "sharpe_ratio": {
            "description": "Risk-adjusted return measure",
            "excellent": "> 1.5",
            "good": "1.0 - 1.5",
            "fair": "0.5 - 1.0",
            "poor": "< 0.5"
        },
        "max_drawdown": {
            "description": "Maximum peak-to-trough decline",
            "excellent": "< -10%",
            "good": "-10% to -15%",
            "fair": "-15% to -25%",
            "poor": "> -25%"
        },
        "calmar_ratio": {
            "description": "Annual return / Maximum drawdown",
            "excellent": "> 2.0",
            "good": "1.0 - 2.0",
            "fair": "0.5 - 1.0",
            "poor": "< 0.5"
        },
        "win_rate": {
            "description": "Percentage of profitable trades",
            "excellent": "> 60%",
            "good": "50% - 60%",
            "fair": "40% - 50%",
            "poor": "< 40%"
        }
    }
    
    return {
        "success": True,
        "metrics": metrics
    }
