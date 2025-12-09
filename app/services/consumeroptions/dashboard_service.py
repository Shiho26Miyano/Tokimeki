"""
Consumer Options Dashboard Service
Orchestrates all services to provide complete dashboard data
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

from app.models.options_models import (
    DashboardResponse, ChainSnapshotResponse, CallPutRatios, 
    IVTermPoint, UnusualActivity, UnderlyingData, ContractBars,
    OptionContract
)
from .polygon_service import ConsumerOptionsPolygonService
from .analytics_service import ConsumerOptionsAnalyticsService
from .chain_service import ConsumerOptionsChainService

logger = logging.getLogger(__name__)

class ConsumerOptionsDashboardService:
    """Main orchestration service for the dashboard"""
    
    def __init__(self):
        self.polygon_service = ConsumerOptionsPolygonService()
        self.analytics_service = ConsumerOptionsAnalyticsService()
        self.chain_service = ConsumerOptionsChainService()
        
        # Default tickers for consumer options
        self.default_tickers = ["COST", "WMT", "TGT", "AMZN", "AAPL"]
    
    async def get_dashboard_data(self, focus_ticker: str, 
                               tickers: List[str] = None,
                               date_range_days: int = 60) -> DashboardResponse:
        """
        Get complete dashboard data for specified ticker and timeframe
        
        Args:
            focus_ticker: Primary ticker for detailed analysis
            tickers: List of all tickers to analyze
            date_range_days: Days of historical data
            
        Returns:
            Complete dashboard data
        """
        try:
            if tickers is None:
                tickers = self.default_tickers
            
            if focus_ticker not in tickers:
                tickers.append(focus_ticker)
            
            logger.info(f"Generating dashboard data for {focus_ticker} with {len(tickers)} tickers")
            
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=date_range_days)
            
            # Fetch data concurrently with error handling
            tasks = [
                self._get_chain_data(focus_ticker),
                self._get_underlying_data(focus_ticker, start_date.isoformat(), end_date.isoformat()),
                self._get_analytics_data(focus_ticker)
            ]
            
            # Use return_exceptions=True to handle individual task failures gracefully
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract results, handling exceptions
            chain_data = results[0] if not isinstance(results[0], Exception) else ChainSnapshotResponse(
                ticker=focus_ticker,
                timestamp=datetime.now(),
                contracts=[],
                total_contracts=0
            )
            underlying_data = results[1] if not isinstance(results[1], Exception) else []
            analytics_result = results[2] if not isinstance(results[2], Exception) else (
                # Return default empty analytics on error
                CallPutRatios(
                    ticker=focus_ticker,
                    analysis_date=date.today(),
                    volume_ratio=None,
                    oi_ratio=None,
                    call_volume=0,
                    put_volume=0,
                    call_oi=0,
                    put_oi=0,
                    median_iv=None,
                    sentiment="Neutral",
                    confidence=0.0
                ),
                [],
                [],
                {},
                {}
            )
            
            call_put_ratios, iv_term, unusual_activity, oi_heatmap_data, delta_distribution_data = analytics_result
            
            return DashboardResponse(
                focus_ticker=focus_ticker,
                timestamp=datetime.now(),
                chain_data=chain_data,
                call_put_ratios=call_put_ratios,
                iv_term_structure=iv_term,
                unusual_activity=unusual_activity,
                oi_heatmap_data=oi_heatmap_data,
                delta_distribution_data=delta_distribution_data,
                underlying_data=underlying_data
            )
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            raise
    
    async def get_multi_ticker_analytics(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Get analytics data for multiple tickers
        
        Args:
            tickers: List of tickers to analyze
            
        Returns:
            Dictionary with analytics for each ticker
        """
        try:
            logger.info(f"Getting analytics for {len(tickers)} tickers")
            
            # Fetch analytics for all tickers concurrently
            tasks = [self._get_analytics_data(ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            analytics_data = {}
            for i, ticker in enumerate(tickers):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"Error getting analytics for {ticker}: {str(result)}")
                    continue
                
                call_put_ratios, iv_term, unusual_activity, oi_heatmap_data, delta_distribution_data = result
                analytics_data[ticker] = {
                    "call_put_ratios": call_put_ratios,
                    "iv_term_structure": iv_term,
                    "unusual_activity": unusual_activity,
                    "oi_heatmap_data": oi_heatmap_data,
                    "delta_distribution_data": delta_distribution_data
                }
            
            # Generate market summary
            all_ratios = {ticker: data["call_put_ratios"] for ticker, data in analytics_data.items()}
            market_summary = self.analytics_service.get_market_sentiment_summary(all_ratios)
            
            return {
                "tickers": analytics_data,
                "market_summary": market_summary,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting multi-ticker analytics: {str(e)}")
            raise
    
    async def get_contract_drilldown(self, contract: str, date_range_days: int = 5) -> Dict[str, Any]:
        """
        Get detailed drilldown data for specific contract
        
        Args:
            contract: Contract symbol
            date_range_days: Days of historical data
            
        Returns:
            Contract drilldown data
        """
        try:
            logger.info(f"Getting drilldown data for contract {contract}")
            
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=date_range_days)
            
            # Get contract bars
            bars = await self.polygon_service.get_contract_minute_bars(
                contract, start_date.isoformat(), end_date.isoformat()
            )
            
            # Get contract info from chain (we'll need the underlying ticker)
            # For now, extract from contract symbol (simplified)
            underlying = self._extract_underlying_from_contract(contract)
            
            if underlying:
                # Get current chain to find contract details
                chain_contracts = await self.polygon_service.get_option_chain_snapshot(underlying)
                contract_info = next((c for c in chain_contracts if c.contract == contract), None)
            else:
                contract_info = None
            
            # Calculate latest Greeks/IV
            latest_greeks = {}
            if contract_info:
                latest_greeks = {
                    "delta": contract_info.delta,
                    "gamma": contract_info.gamma,
                    "theta": contract_info.theta,
                    "vega": contract_info.vega,
                    "implied_volatility": contract_info.implied_volatility
                }
            
            return {
                "contract": contract,
                "contract_info": contract_info,
                "bars": bars,
                "latest_greeks": latest_greeks,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting contract drilldown for {contract}: {str(e)}")
            raise
    
    async def _get_chain_data(self, ticker: str) -> ChainSnapshotResponse:
        """Get option chain data for ticker"""
        try:
            result = await self.chain_service.get_chain_snapshot(ticker)
            if result.total_contracts == 0:
                logger.warning(f"No contracts found for {ticker}. This may indicate the ticker has no options data available or the API returned empty results.")
            return result
        except Exception as e:
            logger.error(f"Error getting chain data for {ticker}: {str(e)}")
            # Return empty chain snapshot instead of raising error
            return ChainSnapshotResponse(
                ticker=ticker,
                timestamp=datetime.now(),
                contracts=[],
                total_contracts=0
            )
    
    async def _get_underlying_data(self, ticker: str, start_date: str, end_date: str) -> List[UnderlyingData]:
        """Get underlying stock data with technical indicators"""
        try:
            bars = await self.polygon_service.get_underlying_daily_bars(ticker, start_date, end_date)
            if not bars:
                logger.warning(f"No underlying data found for {ticker} from {start_date} to {end_date}")
                return []
            return self.analytics_service.calculate_technical_indicators(bars)
        except Exception as e:
            logger.error(f"Error getting underlying data for {ticker}: {str(e)}")
            # Return empty list instead of raising error
            return []
    
    async def _get_analytics_data(self, ticker: str) -> tuple:
        """Get analytics data for ticker"""
        try:
            # Get option chain
            contracts = await self.polygon_service.get_option_chain_snapshot(ticker)
            
            if not contracts:
                logger.warning(f"No contracts available for {ticker} to calculate analytics")
                # Return empty/default analytics data
                return (
                    CallPutRatios(
                        ticker=ticker,
                        analysis_date=date.today(),
                        volume_ratio=None,
                        oi_ratio=None,
                        call_volume=0,
                        put_volume=0,
                        call_oi=0,
                        put_oi=0,
                        median_iv=None,
                        sentiment="Neutral",
                        confidence=0.0
                    ),
                    [],
                    [],
                    {},
                    {}
                )
            
            # Calculate analytics
            call_put_ratios = self.analytics_service.calculate_call_put_ratios(contracts, ticker)
            iv_term = self.analytics_service.calculate_iv_term_structure(contracts)
            unusual_activity = self.analytics_service.detect_unusual_activity(contracts, ticker)
            
            # Calculate new chart data
            oi_heatmap_data = self.analytics_service.calculate_oi_change_heatmap_data(contracts)
            delta_distribution_data = self.analytics_service.calculate_delta_distribution_data(contracts)
            
            return call_put_ratios, iv_term, unusual_activity, oi_heatmap_data, delta_distribution_data
        except Exception as e:
            logger.error(f"Error getting analytics data for {ticker}: {str(e)}")
            # Return empty/default analytics data on error
            return (
                CallPutRatios(
                    ticker=ticker,
                    analysis_date=date.today(),
                    volume_ratio=None,
                    oi_ratio=None,
                    call_volume=0,
                    put_volume=0,
                    call_oi=0,
                    put_oi=0,
                    median_iv=None,
                    sentiment="Neutral",
                    confidence=0.0
                ),
                [],
                [],
                {},
                {}
            )
    
    def _extract_underlying_from_contract(self, contract: str) -> Optional[str]:
        """
        Extract underlying ticker from contract symbol
        This is a simplified implementation
        """
        try:
            # Contract format is typically: AAPL251122C00150000
            # Extract the ticker part (letters at the beginning)
            ticker = ""
            for char in contract:
                if char.isalpha():
                    ticker += char
                else:
                    break
            
            return ticker.upper() if ticker else None
            
        except Exception as e:
            logger.error(f"Error extracting underlying from {contract}: {str(e)}")
            return None
    
    async def get_top_movers(self, tickers: List[str] = None) -> Dict[str, Any]:
        """
        Get top moving options across all tickers
        
        Args:
            tickers: List of tickers to analyze
            
        Returns:
            Top movers data
        """
        try:
            if tickers is None:
                tickers = self.default_tickers
            
            logger.info(f"Getting top movers for {len(tickers)} tickers")
            
            all_contracts = []
            
            # Fetch all contracts
            for ticker in tickers:
                try:
                    contracts = await self.polygon_service.get_option_chain_snapshot(ticker)
                    all_contracts.extend(contracts)
                except Exception as e:
                    logger.error(f"Error fetching contracts for {ticker}: {str(e)}")
                    continue
            
            # Sort by various metrics
            top_volume = self.chain_service.get_top_contracts_by_metric(all_contracts, "volume", 20)
            top_oi = self.chain_service.get_top_contracts_by_metric(all_contracts, "oi", 20)
            top_iv = self.chain_service.get_top_contracts_by_metric(all_contracts, "iv", 20)
            
            # Get unusual activity across all tickers
            all_unusual = []
            for ticker in tickers:
                try:
                    ticker_contracts = [c for c in all_contracts if c.underlying == ticker]
                    unusual = self.analytics_service.detect_unusual_activity(ticker_contracts, ticker)
                    all_unusual.extend(unusual)
                except Exception as e:
                    logger.error(f"Error detecting unusual activity for {ticker}: {str(e)}")
                    continue
            
            # Sort unusual by z-score
            all_unusual.sort(key=lambda x: x.z_score, reverse=True)
            
            return {
                "top_volume": top_volume[:10],
                "top_oi": top_oi[:10],
                "top_iv": top_iv[:10],
                "unusual_activity": all_unusual[:15],
                "timestamp": datetime.now(),
                "total_contracts_analyzed": len(all_contracts)
            }
            
        except Exception as e:
            logger.error(f"Error getting top movers: {str(e)}")
            raise
    
    async def close(self):
        """Close all underlying services"""
        await self.polygon_service.close()
        await self.chain_service.close()
