"""
ETF Dashboard Service
Orchestrates all services to provide complete dashboard data
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

from app.models.etf_models import (
    ETFDashboardResponse, ETFBasicInfo, ETFPriceData, ETFHolding,
    ETFRiskMetrics, ETFTechnicalIndicators, ETFDividendHistory,
    ETFComparison, ETFSectorDistribution, ETFIndustryDistribution
)
from .polygon_service import ETFPolygonService
from .yfinance_service import ETFYFinanceService
from .analytics_service import ETFAnalyticsService

logger = logging.getLogger(__name__)


class ETFDashboardService:
    """Main orchestration service for the ETF dashboard"""
    
    def __init__(self):
        self.polygon_service = ETFPolygonService()
        self.yfinance_service = ETFYFinanceService()
        self.analytics_service = ETFAnalyticsService()
    
    async def get_dashboard_data(
        self,
        symbol: str,
        date_range_days: int = 365
    ) -> ETFDashboardResponse:
        """
        Get complete dashboard data for specified ETF
        
        Args:
            symbol: ETF ticker symbol
            date_range_days: Days of historical data to fetch
            
        Returns:
            Complete dashboard data
        """
        try:
            symbol = symbol.upper()
            logger.info(f"Generating dashboard data for {symbol}")
            
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=date_range_days)
            
            # Fetch data concurrently with error handling
            tasks = [
                self._get_basic_info(symbol),
                self._get_price_data(symbol, start_date.isoformat(), end_date.isoformat()),
                self._get_holdings(symbol),
                self._get_dividends(symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract results, handling exceptions
            basic_info = results[0] if not isinstance(results[0], Exception) else None
            price_data = results[1] if not isinstance(results[1], Exception) else []
            holdings = results[2] if not isinstance(results[2], Exception) else []
            dividends = results[3] if not isinstance(results[3], Exception) else []
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Error in task {i}: {str(result)}")
            
            # If basic_info is None, try to get minimal info from yfinance
            if basic_info is None:
                logger.warning(f"Basic info is None for {symbol}, trying to get minimal info")
                try:
                    # Try to get at least price data
                    if not price_data:
                        # Try again with shorter period
                        price_data = await self._get_price_data(
                            symbol,
                            (date.today() - timedelta(days=30)).isoformat(),
                            date.today().isoformat()
                        )
                    
                    # Create minimal basic info from price data
                    if price_data and len(price_data) > 0:
                        latest_price = price_data[-1].close
                        previous_price = price_data[-2].close if len(price_data) > 1 else latest_price
                        day_change = latest_price - previous_price
                        day_change_percent = (day_change / previous_price * 100) if previous_price > 0 else 0
                        
                        basic_info = ETFBasicInfo(
                            symbol=symbol,
                            name=symbol,
                            current_price=latest_price,
                            previous_close=previous_price,
                            day_change=day_change,
                            day_change_percent=day_change_percent,
                            timestamp=datetime.now()
                        )
                        logger.info(f"Created minimal basic info from price data for {symbol}")
                    else:
                        basic_info = ETFBasicInfo(
                            symbol=symbol,
                            name=symbol,
                            timestamp=datetime.now()
                        )
                        logger.warning(f"Could not create basic info for {symbol} - no price data available")
                except Exception as e:
                    logger.error(f"Error creating minimal basic info: {str(e)}")
                    basic_info = ETFBasicInfo(
                        symbol=symbol,
                        name=symbol,
                        timestamp=datetime.now()
                    )
            
            # If basic_info has no price but we have price_data, update it
            if basic_info and (not basic_info.current_price or basic_info.current_price == 0):
                if price_data and len(price_data) > 0:
                    latest_price = price_data[-1].close
                    previous_price = price_data[-2].close if len(price_data) > 1 else latest_price
                    day_change = latest_price - previous_price
                    day_change_percent = (day_change / previous_price * 100) if previous_price > 0 else 0
                    
                    # Update basic_info with price data
                    basic_info.current_price = latest_price
                    basic_info.previous_close = previous_price
                    basic_info.day_change = day_change
                    basic_info.day_change_percent = day_change_percent
                    logger.info(f"Updated basic_info with price data for {symbol}")
            
            # Analyze holdings
            holdings_analysis = self.analytics_service.analyze_holdings(holdings)
            top_holdings = self.analytics_service.calculate_top_holdings(holdings, top_n=10)
            
            # Calculate risk metrics
            risk_metrics = None
            if price_data and len(price_data) >= 30:
                prices = [bar.close for bar in price_data]
                try:
                    risk_metrics = self.analytics_service.calculate_risk_metrics(
                        symbol=symbol,
                        prices=prices
                    )
                except Exception as e:
                    logger.warning(f"Error calculating risk metrics: {str(e)}")
            
            # Calculate technical indicators
            technical_indicators = []
            if price_data and len(price_data) >= 20:
                try:
                    dates = [bar.date for bar in price_data]
                    prices = [bar.close for bar in price_data]
                    highs = [bar.high for bar in price_data]
                    lows = [bar.low for bar in price_data]
                    closes = [bar.close for bar in price_data]
                    
                    technical_indicators = self.analytics_service.calculate_technical_indicators(
                        symbol=symbol,
                        dates=dates,
                        prices=prices,
                        highs=highs,
                        lows=lows,
                        closes=closes
                    )
                except Exception as e:
                    logger.warning(f"Error calculating technical indicators: {str(e)}")
            
            # Determine data source
            data_source = "polygon" if self.polygon_service.api_key and self.polygon_service.rest_client else "yfinance"
            
            # Log data availability
            logger.info(f"Data summary for {symbol}: basic_info={basic_info is not None}, price_data={len(price_data)}, holdings={len(holdings)}, dividends={len(dividends)}")
            
            # Create response
            response = ETFDashboardResponse(
                symbol=symbol,
                timestamp=datetime.now(),
                basic_info=basic_info,
                price_data=price_data,
                top_holdings=top_holdings,
                total_holdings_count=holdings_analysis.get('total_holdings'),
                holdings_concentration=holdings_analysis.get('top_10_concentration'),
                sector_distribution=holdings_analysis.get('sector_distribution', []),
                industry_distribution=holdings_analysis.get('industry_distribution', []),
                risk_metrics=risk_metrics,
                technical_indicators=technical_indicators,
                dividend_history=dividends,
                data_source=data_source
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            raise
    
    async def get_etf_comparison(self, symbols: List[str]) -> List[ETFComparison]:
        """Get comparison data for multiple ETFs"""
        try:
            logger.info(f"Getting comparison data for {len(symbols)} ETFs")
            
            # Fetch data for all symbols concurrently
            tasks = [self._get_comparison_data(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            comparisons = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error getting comparison for {symbols[i]}: {str(result)}")
                    continue
                if result:
                    comparisons.append(result)
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error getting ETF comparison: {str(e)}")
            return []
    
    async def get_etf_holdings_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get detailed holdings analysis"""
        try:
            holdings = await self._get_holdings(symbol)
            analysis = self.analytics_service.analyze_holdings(holdings)
            
            return {
                'symbol': symbol.upper(),
                'total_holdings': analysis.get('total_holdings', 0),
                'top_10_concentration': analysis.get('top_10_concentration'),
                'top_holdings': self.analytics_service.calculate_top_holdings(holdings, top_n=10),
                'sector_distribution': analysis.get('sector_distribution', []),
                'industry_distribution': analysis.get('industry_distribution', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting holdings analysis for {symbol}: {str(e)}")
            return {
                'symbol': symbol.upper(),
                'error': str(e)
            }
    
    async def _get_basic_info(self, symbol: str) -> Optional[ETFBasicInfo]:
        """Get basic info, trying Polygon first, then yfinance"""
        try:
            # Try Polygon first
            if self.polygon_service.api_key and self.polygon_service.rest_client:
                try:
                    basic_info = await self.polygon_service.get_etf_basic_info(symbol)
                    if basic_info and basic_info.current_price:
                        logger.info(f"Got basic info from Polygon for {symbol}")
                        return basic_info
                except Exception as e:
                    logger.debug(f"Polygon failed for {symbol}: {str(e)}")
            
            # Fallback to yfinance
            basic_info = await self.yfinance_service.get_etf_basic_info(symbol)
            if basic_info:
                logger.info(f"Got basic info from yfinance for {symbol}")
            else:
                logger.warning(f"No basic info from yfinance for {symbol}")
            return basic_info
            
        except Exception as e:
            logger.warning(f"Error getting basic info for {symbol}: {str(e)}")
            return None
    
    async def _get_price_data(self, symbol: str, start_date: str, end_date: str) -> List[ETFPriceData]:
        """Get price data, trying Polygon first, then yfinance"""
        try:
            # Try Polygon first
            if self.polygon_service.api_key and self.polygon_service.rest_client:
                try:
                    price_data = await self.polygon_service.get_etf_daily_bars(symbol, start_date, end_date)
                    if price_data and len(price_data) > 0:
                        logger.info(f"Got {len(price_data)} price bars from Polygon for {symbol}")
                        return price_data
                except Exception as e:
                    logger.debug(f"Polygon price data failed for {symbol}: {str(e)}")
            
            # Fallback to yfinance
            price_data = await self.yfinance_service.get_etf_history(
                symbol,
                start_date=start_date,
                end_date=end_date
            )
            if price_data and len(price_data) > 0:
                logger.info(f"Got {len(price_data)} price bars from yfinance for {symbol}")
            else:
                logger.warning(f"No price data from yfinance for {symbol}")
            return price_data
            
        except Exception as e:
            logger.warning(f"Error getting price data for {symbol}: {str(e)}")
            return []
    
    async def _get_holdings(self, symbol: str) -> List[ETFHolding]:
        """Get holdings, using yfinance (more reliable for holdings)"""
        try:
            # yfinance is better for holdings
            holdings = await self.yfinance_service.get_etf_holdings(symbol)
            return holdings
            
        except Exception as e:
            logger.warning(f"Error getting holdings for {symbol}: {str(e)}")
            return []
    
    async def _get_dividends(self, symbol: str) -> List[ETFDividendHistory]:
        """Get dividend history, using yfinance"""
        try:
            dividends = await self.yfinance_service.get_etf_dividends(symbol)
            return dividends
            
        except Exception as e:
            logger.warning(f"Error getting dividends for {symbol}: {str(e)}")
            return []
    
    async def _get_comparison_data(self, symbol: str) -> Optional[ETFComparison]:
        """Get comparison data for a single ETF"""
        try:
            # Get basic info and price data
            basic_info = await self._get_basic_info(symbol)
            price_data = await self._get_price_data(
                symbol,
                (date.today() - timedelta(days=365*5)).isoformat(),
                date.today().isoformat()
            )
            
            if not basic_info or not price_data:
                return None
            
            # Calculate returns for different periods
            current_price = basic_info.current_price or (price_data[-1].close if price_data else None)
            if not current_price:
                return None
            
            returns = {}
            
            # Calculate returns for different periods
            periods = {
                '1d': 1,
                '1w': 7,
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365,
                '3y': 365 * 3,
                '5y': 365 * 5
            }
            
            for period_name, days in periods.items():
                if len(price_data) >= days:
                    past_price = price_data[-days].close if len(price_data) >= days else None
                    if past_price and past_price > 0:
                        returns[period_name] = ((current_price - past_price) / past_price) * 100
            
            # Calculate risk metrics
            prices = [bar.close for bar in price_data]
            risk_metrics = None
            if len(prices) >= 252:
                risk_metrics = self.analytics_service.calculate_risk_metrics(symbol, prices)
            
            return ETFComparison(
                symbol=symbol.upper(),
                name=basic_info.name,
                return_1d=returns.get('1d'),
                return_1w=returns.get('1w'),
                return_1m=returns.get('1m'),
                return_3m=returns.get('3m'),
                return_6m=returns.get('6m'),
                return_1y=returns.get('1y'),
                return_3y=returns.get('3y'),
                return_5y=returns.get('5y'),
                volatility_1y=risk_metrics.volatility_1y if risk_metrics else None,
                sharpe_ratio=risk_metrics.sharpe_ratio if risk_metrics else None,
                max_drawdown=risk_metrics.max_drawdown if risk_metrics else None,
                aum=basic_info.aum,
                expense_ratio=basic_info.expense_ratio,
                dividend_yield=basic_info.dividend_yield,
                current_price=current_price
            )
            
        except Exception as e:
            logger.warning(f"Error getting comparison data for {symbol}: {str(e)}")
            return None
    
    async def close(self):
        """Close all underlying services"""
        await self.polygon_service.close()
        await self.yfinance_service.close()

