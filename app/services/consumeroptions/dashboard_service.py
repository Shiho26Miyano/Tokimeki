"""
Consumer Options Dashboard Service
Orchestrates all services to provide complete dashboard data
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import pandas as pd
import warnings

# Suppress yfinance warnings
warnings.filterwarnings("ignore", message=".*404.*")
warnings.filterwarnings("ignore", category=UserWarning)

from app.models.options_models import (
    DashboardResponse, ChainSnapshotResponse, CallPutRatios, 
    IVTermPoint, UnusualActivity, UnderlyingData, ContractBars,
    OptionContract
)
from .polygon_service import ConsumerOptionsPolygonService
from .analytics_service import ConsumerOptionsAnalyticsService
from .chain_service import ConsumerOptionsChainService

# Import simulation services for integration
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.database import get_db
from app.models.simulation_models import (
    SignalsDaily, RegimeStates, FeaturesDaily, PortfolioDaily
)

logger = logging.getLogger(__name__)

class ConsumerOptionsDashboardService:
    """Main orchestration service for the dashboard"""
    
    def __init__(self):
        self.polygon_service = ConsumerOptionsPolygonService()
        self.analytics_service = ConsumerOptionsAnalyticsService()
        self.chain_service = ConsumerOptionsChainService()
        
        # Thread pool executor for yfinance fallback
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Default tickers for consumer options
        self.default_tickers = ["COST", "WMT", "TGT", "AMZN", "AAPL"]
    
    async def get_simulation_data(self, ticker: str, target_date: date = None) -> Dict[str, Any]:
        """
        Get simulation data for a ticker (regime state, signals, features)
        
        Args:
            ticker: Stock ticker
            target_date: Date to get data for (defaults to today)
            
        Returns:
            Dictionary with simulation data
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            db: Session = next(get_db())
            
            # Get latest signal
            signal = db.query(SignalsDaily).filter(
                and_(
                    SignalsDaily.symbol == ticker.upper(),
                    SignalsDaily.date <= target_date,
                    SignalsDaily.strategy_id == "vol_regime_v1"
                )
            ).order_by(SignalsDaily.date.desc()).first()
            
            # Get regime state
            regime = db.query(RegimeStates).filter(
                and_(
                    RegimeStates.symbol == ticker.upper(),
                    RegimeStates.date <= target_date,
                    RegimeStates.strategy_id == "vol_regime_v1"
                )
            ).order_by(RegimeStates.date.desc()).first()
            
            # Get latest features
            features = db.query(FeaturesDaily).filter(
                and_(
                    FeaturesDaily.symbol == ticker.upper(),
                    FeaturesDaily.date <= target_date
                )
            ).order_by(FeaturesDaily.date.desc()).first()
            
            # Get portfolio if available
            portfolio = db.query(PortfolioDaily).filter(
                and_(
                    PortfolioDaily.strategy_id == "vol_regime_v1",
                    PortfolioDaily.date <= target_date
                )
            ).order_by(PortfolioDaily.date.desc()).first()
            
            db.close()
            
            return {
                'ticker': ticker.upper(),
                'date': target_date.isoformat(),
                'signal': {
                    'signal': signal.signal if signal else None,
                    'target_position': signal.target_position if signal else None,
                    'reason_json': signal.reason_json if signal else None,
                    'date': signal.date.isoformat() if signal else None
                },
                'regime': {
                    'on': regime.regime_on if regime else None,
                    'reasons': regime.reasons_json if regime else None,
                    'date': regime.date.isoformat() if regime else None
                },
                'features': {
                    'rv20': features.rv20 if features else None,
                    'rv60': features.rv60 if features else None,
                    'atr14': features.atr14 if features else None,
                    'rv20_pct': features.rv20_pct if features else None,
                    'atr14_pct': features.atr14_pct if features else None,
                    'iv_median_pct': features.iv_median_pct if features else None,
                    'iv_slope': features.iv_slope if features else None,
                    'cp_vol_ratio': features.cp_vol_ratio if features else None,
                    'cp_oi_ratio': features.cp_oi_ratio if features else None,
                    'date': features.date.isoformat() if features else None
                },
                'portfolio': {
                    'nav': portfolio.nav if portfolio else None,
                    'daily_pnl': portfolio.daily_pnl if portfolio else None,
                    'drawdown': portfolio.drawdown if portfolio else None,
                    'date': portfolio.date.isoformat() if portfolio else None
                }
            }
        except Exception as e:
            logger.error(f"Error getting simulation data for {ticker}: {str(e)}")
            return {
                'ticker': ticker.upper(),
                'date': target_date.isoformat(),
                'error': str(e)
            }
    
    async def get_dashboard_data(self, focus_ticker: str, 
                               tickers: List[str] = None,
                               date_range_days: int = 60,
                               include_simulation: bool = True) -> DashboardResponse:
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
            
            # Fetch LIVE data concurrently with error handling
            # Note: get_option_chain_snapshot uses real-time snapshot API (no caching)
            tasks = [
                self._get_chain_data(focus_ticker),  # Uses live snapshot API
                self._get_underlying_data(focus_ticker, start_date.isoformat(), end_date.isoformat()),
                self._get_analytics_data(focus_ticker)  # Uses live snapshot API
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
            
            # Get LIVE underlying snapshot (real-time price)
            underlying_snapshot = None
            try:
                underlying_snapshot = await self.polygon_service.get_underlying_snapshot(focus_ticker)
                if underlying_snapshot:
                    logger.info(f"Retrieved LIVE snapshot for {focus_ticker}: price=${underlying_snapshot.get('current_price')}")
            except Exception as e:
                logger.warning(f"Could not fetch live underlying snapshot: {str(e)}")
            
            # Get simulation data if requested
            simulation_data = None
            if include_simulation:
                try:
                    simulation_data = await self.get_simulation_data(focus_ticker)
                except Exception as e:
                    logger.warning(f"Could not fetch simulation data: {str(e)}")
            
            # Create response
            response = DashboardResponse(
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
            
            # Convert to dict with proper serialization of nested models
            if hasattr(response, 'model_dump'):
                response_dict = response.model_dump(mode='json')
            elif hasattr(response, 'dict'):
                response_dict = response.dict()
            else:
                response_dict = {}
            
            # Ensure underlying_data is properly serialized (list of dicts)
            if underlying_data and len(underlying_data) > 0:
                logger.info(f"Serializing {len(underlying_data)} underlying data points for {focus_ticker}")
                if isinstance(underlying_data[0], UnderlyingData):
                    response_dict['underlying_data'] = [
                        item.dict() if hasattr(item, 'dict') else item.model_dump(mode='json') if hasattr(item, 'model_dump') else item
                        for item in underlying_data
                    ]
                    logger.info(f"Successfully serialized {len(response_dict.get('underlying_data', []))} underlying data points")
                else:
                    # Already dicts, just use them
                    response_dict['underlying_data'] = underlying_data
                    logger.info(f"Underlying data already in dict format, {len(underlying_data)} points")
            else:
                logger.warning(f"No underlying_data to serialize for {focus_ticker} (empty list or None)")
                response_dict['underlying_data'] = []
            
            # Add simulation data and live snapshot to response
            response_dict['simulation_data'] = simulation_data
            response_dict['underlying_snapshot'] = underlying_snapshot  # Add live price data
            response_dict['data_source'] = 'polygon_live' if underlying_snapshot else ('yfinance' if underlying_data else 'none')
            
            return response_dict
            
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
        """Get underlying stock data with technical indicators, with yfinance fallback"""
        try:
            logger.info(f"Fetching underlying data for {ticker} from {start_date} to {end_date}")
            
            # Try Polygon first
            bars = await self.polygon_service.get_underlying_daily_bars(ticker, start_date, end_date)
            logger.info(f"Retrieved {len(bars)} raw bars from Polygon for {ticker}")
            
            # If Polygon fails or returns no data, try yfinance fallback
            if not bars:
                logger.warning(f"No underlying data from Polygon for {ticker}, trying yfinance fallback")
                try:
                    bars = await self._get_underlying_data_yfinance(ticker, start_date, end_date)
                    if bars:
                        logger.info(f"Retrieved {len(bars)} bars from yfinance fallback for {ticker}")
                    else:
                        logger.warning(f"No underlying data found for {ticker} from {start_date} to {end_date}. This may indicate:")
                        logger.warning(f"  1. Polygon API subscription doesn't include historical stock data")
                        logger.warning(f"  2. Date range is invalid or too large")
                        logger.warning(f"  3. Ticker symbol is invalid")
                        return []
                except Exception as yf_error:
                    logger.error(f"yfinance fallback also failed for {ticker}: {str(yf_error)}")
                    return []
            
            # Calculate technical indicators
            bars_with_indicators = self.analytics_service.calculate_technical_indicators(bars)
            logger.info(f"Processed {len(bars_with_indicators)} bars with technical indicators for {ticker}")
            return bars_with_indicators
        except Exception as e:
            logger.error(f"Error getting underlying data for {ticker}: {str(e)}", exc_info=True)
            # Try yfinance fallback as last resort
            try:
                logger.info(f"Attempting yfinance fallback for {ticker}")
                bars = await self._get_underlying_data_yfinance(ticker, start_date, end_date)
                if bars:
                    bars_with_indicators = self.analytics_service.calculate_technical_indicators(bars)
                    logger.info(f"Successfully retrieved {len(bars_with_indicators)} bars from yfinance fallback")
                    return bars_with_indicators
            except Exception as yf_error:
                logger.error(f"yfinance fallback failed: {str(yf_error)}")
            return []
    
    async def _get_underlying_data_yfinance(self, ticker: str, start_date: str, end_date: str) -> List[UnderlyingData]:
        """Get underlying stock data from yfinance as fallback"""
        try:
            logger.info(f"Fetching yfinance data for {ticker} from {start_date} to {end_date}")
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(ticker.upper())
            )
            
            # Suppress yfinance warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                
                def fetch_history():
                    try:
                        # yfinance expects dates in YYYY-MM-DD format
                        # Also add 1 day to end_date to make it inclusive
                        from datetime import datetime, timedelta
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        end_inclusive = (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                        logger.debug(f"Fetching yfinance history: start={start_date}, end={end_inclusive}")
                        hist = ticker_obj.history(start=start_date, end=end_inclusive)
                        logger.debug(f"yfinance returned {len(hist)} rows")
                        return hist
                    except Exception as e:
                        logger.error(f"Error in yfinance fetch_history: {str(e)}")
                        if "404" in str(e) or "not found" in str(e).lower():
                            return pd.DataFrame()
                        raise
                
                hist = await loop.run_in_executor(self.executor, fetch_history)
            
            if hist is None or hist.empty:
                logger.debug(f"No historical data available from yfinance for {ticker}")
                return []
            
            bars = []
            for date_idx, row in hist.iterrows():
                try:
                    # Convert index to date
                    if isinstance(date_idx, pd.Timestamp):
                        bar_date = date_idx.date()
                    else:
                        bar_date = date_idx
                    
                    # Extract and validate price data
                    open_price = float(row['Open']) if pd.notna(row['Open']) and row['Open'] > 0 else None
                    high_price = float(row['High']) if pd.notna(row['High']) and row['High'] > 0 else None
                    low_price = float(row['Low']) if pd.notna(row['Low']) and row['Low'] > 0 else None
                    close_price = float(row['Close']) if pd.notna(row['Close']) and row['Close'] > 0 else None
                    
                    # Skip if missing critical data
                    if not all([open_price, high_price, low_price, close_price]):
                        logger.debug(f"Skipping bar for {ticker} on {bar_date}: missing price data")
                        continue
                    
                    # Ensure high >= low, and both are within reasonable range of open/close
                    if high_price < low_price:
                        logger.warning(f"Invalid high/low for {ticker} on {bar_date}: high={high_price}, low={low_price}, swapping")
                        high_price, low_price = low_price, high_price
                    
                    # Ensure high >= max(open, close) and low <= min(open, close)
                    max_price = max(open_price, close_price)
                    min_price = min(open_price, close_price)
                    
                    if high_price < max_price:
                        logger.debug(f"Adjusting high for {ticker} on {bar_date}: {high_price} -> {max_price}")
                        high_price = max_price
                    
                    if low_price > min_price:
                        logger.debug(f"Adjusting low for {ticker} on {bar_date}: {low_price} -> {min_price}")
                        low_price = min_price
                    
                    bar = UnderlyingData(
                        ticker=ticker.upper(),
                        bar_date=bar_date,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=int(row['Volume']) if pd.notna(row['Volume']) else 0
                    )
                    
                    bars.append(bar)
                    
                except Exception as e:
                    logger.warning(f"Error processing row for {ticker}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(bars)} historical bars from yfinance for {ticker}")
            return bars
            
        except Exception as e:
            error_msg = str(e)
            # 404 errors are common and can be ignored
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.debug(f"Stock {ticker} history not found in yfinance (404) - this is normal")
            else:
                logger.warning(f"Error getting stock history from yfinance for {ticker}: {error_msg}")
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
        if self.executor:
            self.executor.shutdown(wait=True)
