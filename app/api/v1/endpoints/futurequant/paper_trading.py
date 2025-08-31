"""
FutureQuant Trader Paper Trading Endpoints
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import BaseModel, Field

from app.services.futurequant.paper_broker_service import FutureQuantPaperBrokerService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

# Create a shared instance of the paper broker service
paper_broker_service = FutureQuantPaperBrokerService()

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
        # Start session using shared service
        result = await paper_broker_service.start_paper_trading(
            user_id=1,  # Default user ID
            strategy_id=request.strategy_id,
            initial_capital=request.initial_capital,
            symbols=request.symbols
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

@router.post("/start-demo", response_model=dict)
async def start_demo_paper_trading(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Start a demo paper trading session without database requirements"""
    try:
        # Start demo session using shared service with futures focus
        result = await paper_broker_service.start_paper_trading_demo(
            strategy_name="Futures Trading Strategy",
            initial_capital=100000,
            symbols=['ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'CL=F', 'GC=F']  # Futures symbols
        )
        
        # Store strategy configuration in the session if result is successful
        if result.get('success') and 'session_id' in result:
            session_id = result['session_id']
            if session_id in paper_broker_service.active_sessions:
                # Store default strategy config for demo
                paper_broker_service.active_sessions[session_id]['strategy_config'] = {
                    'name': 'Demo Strategy',
                    'riskLevel': 'Medium',
                    'positionSizeMultiplier': 1.0,
                    'stopLossPercent': 2.0,
                    'takeProfitPercent': 4.0,
                    'maxDrawdown': 0.10,
                    'leverage': 2.0
                }
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_start_demo_paper_trading",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_start_demo_paper_trading",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Demo paper trading start error: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_start_demo_paper_trading",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop/{session_id}", response_model=dict)
async def stop_paper_trading(
    session_id: str = Path(..., description="Paper trading session ID"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Stop a paper trading session"""
    try:
        # Stop session using shared service
        result = await paper_broker_service.stop_paper_trading(session_id)
        
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
    session_id: str = Path(..., description="Paper trading session ID"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get status of a paper trading session"""
    try:
        # Get status using shared service
        result = await paper_broker_service.get_session_status(session_id)
        
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
        # Get strategy configuration from session if available
        strategy_config = None
        if request.session_id in paper_broker_service.active_sessions:
            session = paper_broker_service.active_sessions[request.session_id]
            strategy_config = session.get('strategy_config')
        
        # Place order using shared service
        result = await paper_broker_service.place_order(
            session_id=request.session_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            strategy_config=strategy_config
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
        # Get active sessions using shared service
        sessions = await paper_broker_service.get_active_sessions()
        
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
    session_id: str = Path(..., description="Paper trading session ID"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Close all positions in a paper trading session"""
    try:
        # Close all positions using shared service
        result = await paper_broker_service.close_all_positions(session_id)
        
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

@router.get("/sessions/{session_id}/dashboard", response_model=dict)
async def get_session_dashboard(
    session_id: str = Path(..., description="Paper trading session ID"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get real-time dashboard data for a paper trading session"""
    try:
        # Get dashboard data using shared service
        result = await paper_broker_service.get_real_time_dashboard_data(session_id)
        
        if result["success"]:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_get_session_dashboard",
                response_time=0.0,  # Placeholder
                success=True
            )
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_get_session_dashboard",
                response_time=0.0,  # Placeholder
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting session dashboard: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_session_dashboard",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{symbol}", response_model=dict)
async def get_market_data(
    symbol: str = Path(..., description="Symbol to get market data for"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get real-time market data for a symbol"""
    try:
        # Import market data service
        from app.services.futurequant.market_data_service import market_data_service
        
        # Get current price
        current_price = await market_data_service.get_current_price(symbol)
        
        # Get symbol info
        symbol_info = await market_data_service.get_symbol_info(symbol)
        
        # Get historical data for chart
        historical_data = await market_data_service.get_historical_data(symbol, period="1d", interval="5m")
        
        if current_price is not None:
            # Track successful request
            await usage_service.track_request(
                endpoint="futurequant_get_market_data",
                response_time=0.0,  # Placeholder
                success=True
            )
            
            return {
                "success": True,
                "symbol": symbol,
                "current_price": current_price,
                "symbol_info": symbol_info,
                "historical_data": historical_data.to_dict('records') if historical_data is not None else [],
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Track failed request
            await usage_service.track_request(
                endpoint="futurequant_get_market_data",
                response_time=0.0,  # Placeholder
                success=False,
                error="Unable to fetch market data"
            )
            
            return {
                "success": False,
                "error": "Unable to fetch market data for symbol"
            }
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        await usage_service.track_request(
            endpoint="futurequant_get_market_data",
            response_time=0.0,  # Placeholder
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
