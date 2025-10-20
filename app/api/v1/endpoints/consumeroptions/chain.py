"""
Consumer Options Chain API Endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.consumeroptions.chain_service import ConsumerOptionsChainService
from app.services.usage_service import AsyncUsageService
from app.core.dependencies import get_usage_service
from app.models.options_models import (
    ChainSnapshotRequest, ChainSnapshotResponse, OptionContract,
    ContractDrilldownRequest, ContractDrilldownResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for requests
class ChainFilterRequest(BaseModel):
    ticker: str = Field(..., description="Underlying ticker symbol")
    expiry_start: Optional[str] = Field(None, description="Start expiry date (YYYY-MM-DD)")
    expiry_end: Optional[str] = Field(None, description="End expiry date (YYYY-MM-DD)")
    strike_min: Optional[float] = Field(None, description="Minimum strike price")
    strike_max: Optional[float] = Field(None, description="Maximum strike price")
    contract_type: Optional[str] = Field(None, description="call or put")
    min_volume: Optional[int] = Field(None, description="Minimum daily volume")
    min_oi: Optional[int] = Field(None, description="Minimum open interest")
    unusual_only: Optional[bool] = Field(False, description="Show only unusual activity")

class ChainSortRequest(BaseModel):
    ticker: str = Field(..., description="Underlying ticker symbol")
    sort_by: str = Field(default="oi", description="Sort by: oi, volume, iv, strike, expiry")
    ascending: bool = Field(default=False, description="Sort order")
    limit: Optional[int] = Field(None, description="Limit results")

@router.get("/snapshot/{ticker}", response_model=ChainSnapshotResponse)
async def get_chain_snapshot(
    ticker: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get option chain snapshot for ticker"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        result = await chain_service.get_chain_snapshot(ticker.upper())
        
        # Track successful request
        await usage_service.track_request(
            endpoint="consumeroptions_chain_snapshot",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Chain snapshot error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_snapshot",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()

@router.post("/filter", response_model=ChainSnapshotResponse)
async def filter_chain(
    request: ChainFilterRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get filtered option chain"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        # Build filter criteria
        filters = {}
        if request.expiry_start and request.expiry_end:
            filters["expiry_start"] = request.expiry_start
            filters["expiry_end"] = request.expiry_end
        if request.strike_min is not None and request.strike_max is not None:
            filters["strike_min"] = request.strike_min
            filters["strike_max"] = request.strike_max
        if request.contract_type:
            filters["contract_type"] = request.contract_type
        if request.min_volume:
            filters["min_volume"] = request.min_volume
        if request.min_oi:
            filters["min_oi"] = request.min_oi
        if request.unusual_only:
            filters["unusual_only"] = request.unusual_only
        
        result = await chain_service.get_chain_snapshot(request.ticker.upper(), filters)
        
        await usage_service.track_request(
            endpoint="consumeroptions_chain_filter",
            response_time=0.0,
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Chain filter error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_filter",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()

@router.post("/sort", response_model=List[OptionContract])
async def sort_chain(
    request: ChainSortRequest,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get sorted option chain"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        # Get chain data first
        chain_response = await chain_service.get_chain_snapshot(request.ticker.upper())
        contracts = chain_response.contracts
        
        # Sort contracts
        sorted_contracts = chain_service.sort_contracts(
            contracts, request.sort_by, request.ascending
        )
        
        # Apply limit if specified
        if request.limit:
            sorted_contracts = sorted_contracts[:request.limit]
        
        await usage_service.track_request(
            endpoint="consumeroptions_chain_sort",
            response_time=0.0,
            success=True
        )
        
        return sorted_contracts
        
    except Exception as e:
        logger.error(f"Chain sort error: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_sort",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()

@router.get("/top/{ticker}")
async def get_top_contracts(
    ticker: str,
    metric: str = Query(default="oi", description="Metric to rank by: oi, volume, iv"),
    limit: int = Query(default=10, description="Number of top contracts"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get top contracts by specified metric"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        # Get chain data
        chain_response = await chain_service.get_chain_snapshot(ticker.upper())
        contracts = chain_response.contracts
        
        # Get top contracts
        top_contracts = chain_service.get_top_contracts_by_metric(contracts, metric, limit)
        
        await usage_service.track_request(
            endpoint="consumeroptions_chain_top",
            response_time=0.0,
            success=True
        )
        
        return {
            "ticker": ticker.upper(),
            "metric": metric,
            "limit": limit,
            "contracts": top_contracts,
            "total_contracts": len(contracts)
        }
        
    except Exception as e:
        logger.error(f"Top contracts error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_top",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()

@router.get("/near-money/{ticker}")
async def get_near_money_contracts(
    ticker: str,
    underlying_price: float = Query(..., description="Current underlying price"),
    range_pct: float = Query(default=0.1, description="Percentage range (0.1 = 10%)"),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get near-the-money contracts"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        # Get chain data
        chain_response = await chain_service.get_chain_snapshot(ticker.upper())
        contracts = chain_response.contracts
        
        # Get near-the-money contracts
        near_money = chain_service.get_near_money_contracts(contracts, underlying_price, range_pct)
        
        await usage_service.track_request(
            endpoint="consumeroptions_chain_near_money",
            response_time=0.0,
            success=True
        )
        
        return {
            "ticker": ticker.upper(),
            "underlying_price": underlying_price,
            "range_pct": range_pct,
            "contracts": near_money,
            "total_near_money": len(near_money)
        }
        
    except Exception as e:
        logger.error(f"Near money contracts error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_near_money",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()

@router.get("/statistics/{ticker}")
async def get_chain_statistics(
    ticker: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get chain statistics and summary"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        # Get chain data
        chain_response = await chain_service.get_chain_snapshot(ticker.upper())
        contracts = chain_response.contracts
        
        # Calculate statistics
        stats = chain_service.calculate_chain_statistics(contracts)
        
        await usage_service.track_request(
            endpoint="consumeroptions_chain_statistics",
            response_time=0.0,
            success=True
        )
        
        return {
            "ticker": ticker.upper(),
            "statistics": stats,
            "timestamp": chain_response.timestamp
        }
        
    except Exception as e:
        logger.error(f"Chain statistics error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_statistics",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()

@router.get("/expiry-groups/{ticker}")
async def get_expiry_groups(
    ticker: str,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get contracts grouped by expiration date"""
    try:
        chain_service = ConsumerOptionsChainService()
        
        # Get chain data
        chain_response = await chain_service.get_chain_snapshot(ticker.upper())
        contracts = chain_response.contracts
        
        # Group by expiry
        expiry_groups = chain_service.get_expiry_groups(contracts)
        
        # Convert to serializable format
        serializable_groups = {}
        for expiry, expiry_contracts in expiry_groups.items():
            serializable_groups[expiry.isoformat()] = expiry_contracts
        
        await usage_service.track_request(
            endpoint="consumeroptions_chain_expiry_groups",
            response_time=0.0,
            success=True
        )
        
        return {
            "ticker": ticker.upper(),
            "expiry_groups": serializable_groups,
            "total_expiries": len(expiry_groups)
        }
        
    except Exception as e:
        logger.error(f"Expiry groups error for {ticker}: {str(e)}")
        await usage_service.track_request(
            endpoint="consumeroptions_chain_expiry_groups",
            response_time=0.0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await chain_service.close()
