"""
Data Ingestion Service for Simulation System
Bridges consumer options data and other sources to simulation tables
"""
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.simulation_models import (
    PricesDaily, OptionsSnapshotDaily
)
from app.services.consumeroptions.polygon_service import ConsumerOptionsPolygonService

logger = logging.getLogger(__name__)


class SimulationDataIngestionService:
    """Service for ingesting data into simulation tables"""
    
    def __init__(self, db: Session):
        self.db = db
        self.polygon_service = ConsumerOptionsPolygonService()
    
    async def ingest_prices_from_yfinance(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Ingest daily price data from yfinance into prices_daily table
        
        This is a placeholder - in production you'd use yfinance or another data source
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                return {
                    'success': False,
                    'error': f'No data found for {symbol}'
                }
            
            ingested_count = 0
            for idx, row in data.iterrows():
                price_date = idx.date() if hasattr(idx, 'date') else date.fromisoformat(str(idx).split()[0])
                
                # Check if already exists
                existing = self.db.query(PricesDaily).filter(
                    and_(
                        PricesDaily.symbol == symbol,
                        PricesDaily.date == price_date
                    )
                ).first()
                
                if existing:
                    continue
                
                price = PricesDaily(
                    symbol=symbol,
                    date=price_date,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    adjusted_close=float(row['Close']) if 'Adj Close' not in row else float(row['Adj Close']),
                    split_factor=1.0
                )
                
                self.db.add(price)
                ingested_count += 1
            
            self.db.commit()
            
            return {
                'success': True,
                'symbol': symbol,
                'ingested_count': ingested_count,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error ingesting prices for {symbol}: {str(e)}", exc_info=True)
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def ingest_options_from_consumer_dashboard(
        self,
        symbol: str,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Ingest options data from consumer options dashboard/Polygon into options_snapshot_daily
        
        This bridges the consumer options dashboard data to the simulation system
        """
        try:
            # Check if already exists
            existing = self.db.query(OptionsSnapshotDaily).filter(
                and_(
                    OptionsSnapshotDaily.symbol == symbol,
                    OptionsSnapshotDaily.date == target_date
                )
            ).first()
            
            if existing:
                return {
                    'success': True,
                    'symbol': symbol,
                    'date': target_date.isoformat(),
                    'message': 'Already exists',
                    'snapshot_id': existing.id
                }
            
            # Get options chain from Polygon service
            contracts = await self.polygon_service.get_option_chain_snapshot(symbol)
            
            if not contracts:
                return {
                    'success': False,
                    'error': f'No options contracts found for {symbol}'
                }
            
            # Calculate IV metrics
            valid_ivs = [c.implied_volatility for c in contracts if c.implied_volatility is not None and c.implied_volatility > 0]
            
            if not valid_ivs:
                return {
                    'success': False,
                    'error': f'No valid IV data found for {symbol}'
                }
            
            import numpy as np
            from datetime import timedelta
            
            iv_median = float(np.median(valid_ivs))
            
            # Calculate IV near (7-21 days) and far (60-120 days)
            today = date.today()
            iv_near_list = []
            iv_far_list = []
            
            for contract in contracts:
                if contract.expiry and contract.implied_volatility and contract.implied_volatility > 0:
                    days_to_expiry = (contract.expiry - target_date).days
                    
                    if 7 <= days_to_expiry <= 21:
                        iv_near_list.append(contract.implied_volatility)
                    elif 60 <= days_to_expiry <= 120:
                        iv_far_list.append(contract.implied_volatility)
            
            iv_near = float(np.median(iv_near_list)) if iv_near_list else None
            iv_far = float(np.median(iv_far_list)) if iv_far_list else None
            
            # If buckets are empty, use closest/furthest available
            if not iv_near_list or not iv_far_list:
                # Find closest expiry with IV
                closest_iv = None
                closest_days = float('inf')
                furthest_iv = None
                furthest_days = 0
                
                for contract in contracts:
                    if contract.expiry and contract.implied_volatility and contract.implied_volatility > 0:
                        days_to_expiry = (contract.expiry - target_date).days
                        if 0 < days_to_expiry <= 180:
                            if days_to_expiry < closest_days:
                                closest_days = days_to_expiry
                                closest_iv = contract.implied_volatility
                            if days_to_expiry > furthest_days:
                                furthest_days = days_to_expiry
                                furthest_iv = contract.implied_volatility
                
                if not iv_near and closest_iv:
                    iv_near = float(closest_iv)
                if not iv_far and furthest_iv:
                    iv_far = float(furthest_iv)
            
            iv_slope = (iv_near - iv_far) if (iv_near and iv_far) else None
            iv_bucket_quality = "sufficient" if (iv_near_list and iv_far_list) else "fallback"
            
            # Calculate call/put ratios
            from app.models.options_models import ContractType
            calls = [c for c in contracts if c.type == ContractType.CALL]
            puts = [c for c in contracts if c.type == ContractType.PUT]
            
            total_call_volume = sum(c.day_volume or 0 for c in calls)
            total_put_volume = sum(c.day_volume or 0 for c in puts)
            total_call_oi = sum(c.day_oi or 0 for c in calls)
            total_put_oi = sum(c.day_oi or 0 for c in puts)
            
            # Count unusual activity
            unusual_count = sum(1 for c in contracts if getattr(c, 'is_unusual', False))
            
            # Create snapshot JSON
            snapshot_json = {
                'contracts_count': len(contracts),
                'calls_count': len(calls),
                'puts_count': len(puts),
                'timestamp': datetime.now().isoformat()
            }
            
            snapshot = OptionsSnapshotDaily(
                symbol=symbol,
                date=target_date,
                snapshot_json=snapshot_json,
                iv_median=iv_median,
                iv_near=iv_near,
                iv_far=iv_far,
                iv_slope=iv_slope,
                iv_bucket_quality=iv_bucket_quality,
                total_call_volume=total_call_volume,
                total_put_volume=total_put_volume,
                total_call_oi=total_call_oi,
                total_put_oi=total_put_oi,
                unusual_count=unusual_count
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            return {
                'success': True,
                'symbol': symbol,
                'date': target_date.isoformat(),
                'snapshot_id': snapshot.id,
                'metrics': {
                    'iv_median': iv_median,
                    'iv_near': iv_near,
                    'iv_far': iv_far,
                    'iv_slope': iv_slope,
                    'call_volume': total_call_volume,
                    'put_volume': total_put_volume,
                    'call_oi': total_call_oi,
                    'put_oi': total_put_oi,
                    'unusual_count': unusual_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error ingesting options for {symbol} on {target_date}: {str(e)}", exc_info=True)
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def sync_consumer_options_to_simulation(
        self,
        symbol: str,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Sync data from consumer options dashboard to simulation tables
        
        This is the main integration point between consumer options and simulation
        """
        try:
            # Get dashboard data (this would use the consumer options service)
            # For now, we'll ingest options snapshot
            
            result = await self.ingest_options_from_consumer_dashboard(symbol, target_date)
            
            return {
                'success': result['success'],
                'symbol': symbol,
                'date': target_date.isoformat(),
                'options_snapshot': result
            }
            
        except Exception as e:
            logger.error(f"Error syncing consumer options for {symbol}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

