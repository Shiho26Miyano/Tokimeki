"""
FutureQuant Trader Paper Trading Endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.futurequant.paper_broker_service import FutureQuantPaperBrokerService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class PaperTradingStartRequest(BaseModel):
    model_id: int = Field(..., description="Model ID to use for trading")
    strategy_id: int = Field(..., description="Strategy ID to use for trading")
    symbols: List[str] = Field(..., description="List of symbols to trade")
    initial_capital: float = Field(default=100000, description="Initial capital")
    session_name: Optional[str] = Field(None, description="Custom session name")

class OrderRequest(BaseModel):
    session_id: str = Field(..., description="Paper trading session ID")
    symbol: str = Field(..., description="Symbol to trade")
    side: str = Field(..., description="Buy or sell")
    quantity: float = Field(..., description="Quantity to trade")
    order_type: str = Field(default="market", description="Order type")
    price: Optional[float] = Field(None, description="Limit price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

@router.post("/start", response_model=dict)
async def start_paper_trading(
    request: PaperTradingStartRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Start a new paper trading session"""
    try:
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Start session
        result = await paper_broker.start_paper_trading(
            model_id=request.model_id,
            strategy_id=request.strategy_id,
            symbols=request.symbols,
            initial_capital=request.initial_capital,
            session_name=request.session_name
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_start_paper_trading",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_start_paper_trading",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Paper trading start error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_start_paper_trading",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop/{session_id}", response_model=dict)
async def stop_paper_trading(
    session_id: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Stop a paper trading session"""
    try:
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Stop session
        result = await paper_broker.stop_paper_trading(session_id)
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_stop_paper_trading",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_stop_paper_trading",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Paper trading stop error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_stop_paper_trading",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/status", response_model=dict)
async def get_session_status(
    session_id: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get status of a paper trading session"""
    try:
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Get status
        result = await paper_broker.get_session_status(session_id)
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_get_session_status",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_get_session_status",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_session_status",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order", response_model=dict)
async def place_order(
    request: OrderRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Place an order in paper trading"""
    try:
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Place order
        result = await paper_broker.place_order(
            session_id=request.session_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit
        )
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_place_order",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_place_order",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Order placement error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_place_order",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=dict)
async def get_active_sessions(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get list of active paper trading sessions"""
    try:
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Get active sessions
        sessions = await paper_broker.get_active_sessions()
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_active_sessions",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return {
            "success": True,
            "active_sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_active_sessions",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/close-all", response_model=dict)
async def close_all_positions(
    session_id: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Close all positions in a paper trading session"""
    try:
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Close all positions
        result = await paper_broker.close_all_positions(session_id)
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_close_all_positions",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_close_all_positions",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error closing all positions: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_close_all_positions",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_paper_trading_status(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get paper trading system status"""
    try:
        status = {
            "system_status": "active",
            "supported_order_types": ["market", "limit"],
            "supported_sides": ["buy", "sell"],
            "risk_features": [
                "Position size limits",
                "Leverage constraints",
                "Stop loss orders",
                "Take profit orders"
            ],
            "simulation_features": [
                "Real-time price updates",
                "Commission modeling",
                "Slippage simulation",
                "Position tracking"
            ],
            "paper_trading_benefits": [
                "Risk-free strategy testing",
                "Performance validation",
                "Parameter optimization",
                "Real market conditions"
            ]
        }
        
        # Track successful request
        await usage_service.track_request(
            endpoint="futurequant_get_paper_trading_status",
            response_time=0.0,  # Placeholder
            success=True
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting paper trading status: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_paper_trading_status",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
