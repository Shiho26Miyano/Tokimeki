"""
Consumer Options Dashboard API Endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.consumeroptions.polygon_service import ConsumerOptionsPolygonService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service

logger = logging.getLogger(__name__)

router = APIRouter()


class OIChangeRequest(BaseModel):
    """Request model for OI change data"""
    symbol: str = Field(..., description="Underlying ticker (e.g., AAPL)")
    strike_band_pct: float = Field(0.2, ge=0.02, le=1.0, description="±% around spot (default 0.2)")
    expiries: int = Field(8, ge=1, le=20, description="Nearest N expiries (default 8)")
    combine_cp: bool = Field(True, description="Combine calls and puts (default True)")


@router.get("/oi-change")
async def get_oi_change(
    symbol: str = Query(..., description="Underlying ticker (e.g., AAPL)"),
    strike_band_pct: float = Query(default=0.2, ge=0.02, le=1.0, description="±% around spot"),
    expiries: int = Query(default=8, ge=1, le=20, description="Nearest N expiries"),
    combine_cp: str = Query(default="true", description="Sum calls & puts per cell (true/false)"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get Open Interest change data for heatmap visualization
    
    Returns a heatmap-ready payload with:
    - expiries: sorted list of expiry dates
    - strikes: sorted list of strike prices
    - matrix: 2D array of OI changes (ΔOI)
    - spot: current spot price
    """
    logger.info(f"OI change request: symbol={symbol}, strike_band_pct={strike_band_pct}, expiries={expiries}, combine_cp={combine_cp}")
    
    service = ConsumerOptionsPolygonService()
    
    # Convert string to boolean (handle "true", "True", "1", etc.)
    combine_cp_lower = combine_cp.lower().strip() if combine_cp else "true"
    combine_cp_bool = combine_cp_lower in ("true", "1", "yes", "on")
    
    try:
        result = await service.get_oi_change(
            symbol=symbol.upper(),
            strike_band_pct=strike_band_pct,
            expiries=expiries,
            combine_cp=combine_cp_bool,
        )
        
        await usage_service.track_request(
            endpoint="consumeroptions_oi_change",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Validation error for OI change: {error_msg}", exc_info=True)
        try:
            await usage_service.track_request(
                endpoint="consumeroptions_oi_change",
                response_time=0.0,
                success=False,
                error=error_msg
            )
        except:
            pass
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error fetching OI change for {symbol}: {error_msg}", exc_info=True)
        try:
            await usage_service.track_request(
                endpoint="consumeroptions_oi_change",
                response_time=0.0,
                success=False,
                error=error_msg
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        try:
            await service.close()
        except Exception as close_error:
            logger.warning(f"Error closing service: {close_error}")


@router.post("/oi-change")
async def get_oi_change_post(
    request: OIChangeRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """
    Get Open Interest change data for heatmap visualization (POST endpoint)
    """
    service = ConsumerOptionsPolygonService()
    
    try:
        result = await service.get_oi_change(
            symbol=request.symbol.upper(),
            strike_band_pct=request.strike_band_pct,
            expiries=request.expiries,
            combine_cp=request.combine_cp,
        )
        
        await usage_service.track_request(
            endpoint="consumeroptions_oi_change",
            response_time=0.0,
            success=True
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Validation error for OI change: {error_msg}", exc_info=True)
        try:
            await usage_service.track_request(
                endpoint="consumeroptions_oi_change",
                response_time=0.0,
                success=False,
                error=error_msg
            )
        except:
            pass
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error fetching OI change for {request.symbol}: {error_msg}", exc_info=True)
        try:
            await usage_service.track_request(
                endpoint="consumeroptions_oi_change",
                response_time=0.0,
                success=False,
                error=error_msg
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        try:
            await service.close()
        except Exception as close_error:
            logger.warning(f"Error closing service: {close_error}")

