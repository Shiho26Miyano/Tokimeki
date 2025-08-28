"""
FutureQuant Trader Backtesting Endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.futurequant.backtest_service import FutureQuantBacktestService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class BacktestRequest(BaseModel):
    strategy_id: int = Field(..., description="Strategy ID to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    symbols: Optional[List[str]] = Field(None, description="List of symbols to backtest")
    initial_capital: float = Field(default=100000, description="Initial capital")
    config: Optional[dict] = Field(None, description="Backtest configuration")

@router.post("/run", response_model=dict)
async def run_backtest(
    request: BacktestRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Run a backtest for a strategy"""
    try:
        # Create backtest service
        backtest_service = FutureQuantBacktestService()
        
        # Run backtest
        result = await backtest_service.run_backtest(
            strategy_id=request.strategy_id,
            start_date=request.start_date,
            end_date=request.end_date,
            symbols=request.symbols,
            initial_capital=request.initial_capital,
            config=request.config
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_run_backtest",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_run_backtest",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_run_backtest",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_backtest_config(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get default backtest configuration"""
    try:
        # Create backtest service
        backtest_service = FutureQuantBacktestService()
        
        config = backtest_service.default_config
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_backtest_config",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return {
            "success": True,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error getting backtest config: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_backtest_config",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_backtest_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get backtesting system status"""
    try:
        # Create backtest service
        backtest_service = FutureQuantBacktestService()
        
        status = {
            "default_config": backtest_service.default_config,
            "supported_constraints": [
                "Maximum leverage",
                "Position limits",
                "Risk per trade",
                "Drawdown limits"
            ],
            "cost_models": [
                "Commission rates",
                "Slippage models",
                "Spread considerations"
            ],
            "performance_metrics": [
                "Total return",
                "Sharpe ratio",
                "Maximum drawdown",
                "Win rate",
                "Profit factor"
            ]
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_backtest_status",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting backtest status: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_backtest_status",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
