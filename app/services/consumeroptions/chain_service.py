"""
Consumer Options Chain Service
Handles option chain data processing and management
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

from app.models.options_models import (
    OptionContract, ChainSnapshotResponse, ContractType
)
from .polygon_service import ConsumerOptionsPolygonService
from .analytics_service import ConsumerOptionsAnalyticsService

logger = logging.getLogger(__name__)

class ConsumerOptionsChainService:
    """Service for managing option chain data"""
    
    def __init__(self):
        self.polygon_service = ConsumerOptionsPolygonService()
        self.analytics_service = ConsumerOptionsAnalyticsService()
    
    async def get_chain_snapshot(self, ticker: str, filters: Dict[str, Any] = None) -> ChainSnapshotResponse:
        """
        Get complete option chain snapshot with filtering
        
        Args:
            ticker: Underlying ticker
            filters: Optional filtering criteria
            
        Returns:
            ChainSnapshotResponse with processed data
        """
        try:
            # Fetch raw chain data
            contracts = await self.polygon_service.get_option_chain_snapshot(ticker)
            
            # Apply filters if provided
            if filters:
                contracts = self.analytics_service.filter_contracts_by_criteria(contracts, filters)
            
            # Detect unusual activity
            unusual_activities = self.analytics_service.detect_unusual_activity(contracts, ticker)
            unusual_contract_symbols = {ua.contract for ua in unusual_activities}
            
            # Mark unusual contracts
            for contract in contracts:
                if contract.contract in unusual_contract_symbols:
                    contract.is_unusual = True
                    # Find the reason
                    for ua in unusual_activities:
                        if ua.contract == contract.contract:
                            contract.unusual_reason = f"{ua.trigger_type}: {ua.z_score:.1f}σ"
                            break
            
            return ChainSnapshotResponse(
                ticker=ticker,
                timestamp=datetime.now(),
                contracts=contracts,
                total_contracts=len(contracts)
            )
            
        except Exception as e:
            logger.error(f"Error getting chain snapshot for {ticker}: {str(e)}")
            raise
    
    def sort_contracts(self, contracts: List[OptionContract], 
                      sort_by: str = "oi", ascending: bool = False) -> List[OptionContract]:
        """
        Sort contracts by specified criteria
        
        Args:
            contracts: List of contracts to sort
            sort_by: Sort criteria (oi, volume, iv, strike, expiry)
            ascending: Sort order
            
        Returns:
            Sorted list of contracts
        """
        try:
            sort_key_map = {
                "oi": lambda c: c.day_oi or 0,
                "volume": lambda c: c.day_volume or 0,
                "iv": lambda c: c.implied_volatility or 0,
                "strike": lambda c: c.strike,
                "expiry": lambda c: c.expiry,
                "last_price": lambda c: c.last_price or 0
            }
            
            if sort_by not in sort_key_map:
                logger.warning(f"Unknown sort criteria: {sort_by}, using 'oi'")
                sort_by = "oi"
            
            sorted_contracts = sorted(contracts, key=sort_key_map[sort_by], reverse=not ascending)
            
            logger.info(f"Sorted {len(contracts)} contracts by {sort_by}")
            return sorted_contracts
            
        except Exception as e:
            logger.error(f"Error sorting contracts: {str(e)}")
            return contracts
    
    def get_top_contracts_by_metric(self, contracts: List[OptionContract], 
                                  metric: str = "oi", limit: int = 10) -> List[OptionContract]:
        """
        Get top contracts by specified metric
        
        Args:
            contracts: List of contracts
            metric: Metric to rank by (oi, volume, iv)
            limit: Number of top contracts to return
            
        Returns:
            Top contracts list
        """
        try:
            sorted_contracts = self.sort_contracts(contracts, sort_by=metric, ascending=False)
            return sorted_contracts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top contracts by {metric}: {str(e)}")
            return contracts[:limit]
    
    def get_near_money_contracts(self, contracts: List[OptionContract], 
                               underlying_price: float, range_pct: float = 0.1) -> List[OptionContract]:
        """
        Get contracts near the money (within specified percentage range)
        
        Args:
            contracts: List of contracts
            underlying_price: Current underlying price
            range_pct: Percentage range around underlying price (0.1 = 10%)
            
        Returns:
            Near-the-money contracts
        """
        try:
            price_range = underlying_price * range_pct
            lower_bound = underlying_price - price_range
            upper_bound = underlying_price + price_range
            
            near_money = [
                c for c in contracts 
                if lower_bound <= c.strike <= upper_bound
            ]
            
            # Sort by distance from underlying price
            near_money.sort(key=lambda c: abs(c.strike - underlying_price))
            
            logger.info(f"Found {len(near_money)} near-the-money contracts")
            return near_money
            
        except Exception as e:
            logger.error(f"Error getting near-the-money contracts: {str(e)}")
            return []
    
    def get_expiry_groups(self, contracts: List[OptionContract]) -> Dict[date, List[OptionContract]]:
        """
        Group contracts by expiration date
        
        Args:
            contracts: List of contracts
            
        Returns:
            Dictionary mapping expiry dates to contract lists
        """
        try:
            expiry_groups = {}
            
            for contract in contracts:
                expiry = contract.expiry
                if expiry not in expiry_groups:
                    expiry_groups[expiry] = []
                expiry_groups[expiry].append(contract)
            
            # Sort each group by strike
            for expiry in expiry_groups:
                expiry_groups[expiry].sort(key=lambda c: c.strike)
            
            logger.info(f"Grouped contracts into {len(expiry_groups)} expiry dates")
            return expiry_groups
            
        except Exception as e:
            logger.error(f"Error grouping contracts by expiry: {str(e)}")
            return {}
    
    def get_strike_chain(self, contracts: List[OptionContract], 
                        expiry: date) -> Dict[float, Dict[str, OptionContract]]:
        """
        Get strike chain for specific expiry (calls and puts by strike)
        
        Args:
            contracts: List of contracts
            expiry: Target expiration date
            
        Returns:
            Dictionary mapping strikes to {call, put} contracts
        """
        try:
            expiry_contracts = [c for c in contracts if c.expiry == expiry]
            strike_chain = {}
            
            for contract in expiry_contracts:
                strike = contract.strike
                if strike not in strike_chain:
                    strike_chain[strike] = {}
                
                contract_type = "call" if contract.type == ContractType.CALL else "put"
                strike_chain[strike][contract_type] = contract
            
            logger.info(f"Built strike chain for {expiry} with {len(strike_chain)} strikes")
            return strike_chain
            
        except Exception as e:
            logger.error(f"Error building strike chain for {expiry}: {str(e)}")
            return {}
    
    def calculate_chain_statistics(self, contracts: List[OptionContract]) -> Dict[str, Any]:
        """
        Calculate overall chain statistics
        
        Args:
            contracts: List of contracts
            
        Returns:
            Dictionary of chain statistics
        """
        try:
            if not contracts:
                return {}
            
            # Basic counts
            total_contracts = len(contracts)
            call_count = len([c for c in contracts if c.type == ContractType.CALL])
            put_count = len([c for c in contracts if c.type == ContractType.PUT])
            
            # Volume and OI totals
            total_volume = sum(c.day_volume or 0 for c in contracts)
            total_oi = sum(c.day_oi or 0 for c in contracts)
            
            # IV statistics
            iv_values = [c.implied_volatility for c in contracts if c.implied_volatility is not None]
            if iv_values:
                min_iv = min(iv_values)
                max_iv = max(iv_values)
                avg_iv = sum(iv_values) / len(iv_values)
            else:
                min_iv = max_iv = avg_iv = None
            
            # Strike range
            strikes = [c.strike for c in contracts]
            min_strike = min(strikes) if strikes else None
            max_strike = max(strikes) if strikes else None
            
            # Expiry range
            expiries = [c.expiry for c in contracts]
            min_expiry = min(expiries) if expiries else None
            max_expiry = max(expiries) if expiries else None
            
            return {
                "total_contracts": total_contracts,
                "call_count": call_count,
                "put_count": put_count,
                "total_volume": total_volume,
                "total_oi": total_oi,
                "min_iv": min_iv,
                "max_iv": max_iv,
                "avg_iv": avg_iv,
                "min_strike": min_strike,
                "max_strike": max_strike,
                "min_expiry": min_expiry,
                "max_expiry": max_expiry,
                "unique_expiries": len(set(expiries))
            }
            
        except Exception as e:
            logger.error(f"Error calculating chain statistics: {str(e)}")
            return {}
    
    async def close(self):
        """Close underlying services"""
        await self.polygon_service.close()
