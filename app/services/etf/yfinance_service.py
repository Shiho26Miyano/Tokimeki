"""
ETF YFinance Service
Service for fetching ETF data from Yahoo Finance using yfinance
"""
import asyncio
import logging
import warnings
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import pandas as pd

# Suppress yfinance 404 warnings globally
warnings.filterwarnings("ignore", message=".*404.*")
warnings.filterwarnings("ignore", category=UserWarning)

from app.models.etf_models import (
    ETFBasicInfo, ETFPriceData, ETFHolding, ETFDividendHistory
)

logger = logging.getLogger(__name__)


class ETFYFinanceService:
    """YFinance service for ETF data"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_etf_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive ETF information from yfinance"""
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol.upper())
            )
            
            # Suppress yfinance 404 warnings - they're common and handled gracefully
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                
                # Try to get info, with fallback to fast_info
                def get_info():
                    try:
                        info = ticker.info
                        if info and len(info) > 0:
                            return info
                        # Fallback to fast_info if info is empty
                        fast_info = ticker.fast_info
                        if fast_info:
                            # Convert fast_info to dict-like structure
                            return dict(fast_info) if hasattr(fast_info, '__dict__') else fast_info
                        return None
                    except Exception as e:
                        logger.debug(f"Error getting info for {symbol}: {str(e)}")
                        # Try fast_info as fallback
                        try:
                            fast_info = ticker.fast_info
                            if fast_info:
                                return dict(fast_info) if hasattr(fast_info, '__dict__') else fast_info
                        except:
                            pass
                        return None
                
                info = await loop.run_in_executor(self.executor, get_info)
            
            if not info or (isinstance(info, dict) and len(info) == 0):
                logger.debug(f"No info returned from yfinance for {symbol} (this is normal for some symbols)")
                # Try to get at least price from history
                try:
                    hist = await loop.run_in_executor(
                        self.executor,
                        lambda: ticker.history(period="5d")
                    )
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        return {
                            'symbol': symbol.upper(),
                            'name': symbol,
                            'current_price': float(latest['Close']),
                            'previous_close': float(hist.iloc[-2]['Close']) if len(hist) > 1 else float(latest['Close']),
                            'volume': int(latest['Volume']),
                        }
                except:
                    pass
                return None
            
            # Check if it's actually an ETF (some symbols might be stocks)
            # yfinance doesn't always distinguish, but we can check for common ETF indicators
            asset_type = info.get('quoteType', '').lower()
            if asset_type not in ['etf', 'mutualfund'] and 'etf' not in (info.get('longName', '') + info.get('shortName', '')).lower():
                logger.debug(f"{symbol} might not be an ETF (quoteType: {asset_type})")
                # Continue anyway, as some ETFs might not have proper quoteType
            
            # Extract relevant ETF information
            # Handle both dict and object-like info
            def get_value(key, default=None):
                if isinstance(info, dict):
                    return info.get(key, default)
                else:
                    return getattr(info, key, default) if hasattr(info, key) else default
            
            etf_info = {
                'symbol': symbol.upper(),
                'name': get_value('longName') or get_value('shortName') or get_value('name') or symbol,
                'description': get_value('longBusinessSummary') or get_value('description'),
                'current_price': get_value('currentPrice') or get_value('regularMarketPrice') or get_value('lastPrice') or get_value('previousClose'),
                'previous_close': get_value('previousClose') or get_value('regularMarketPreviousClose'),
                'day_change': None,
                'day_change_percent': get_value('regularMarketChangePercent') or get_value('regularMarketChange') or 0,
                'volume': get_value('volume') or get_value('regularMarketVolume'),
                'avg_volume': get_value('averageVolume'),
                'bid': get_value('bid'),
                'ask': get_value('ask'),
                'bid_ask_spread': None,
                'week_52_high': get_value('fiftyTwoWeekHigh'),
                'week_52_low': get_value('fiftyTwoWeekLow'),
                'aum': get_value('totalAssets'),
                'expense_ratio': get_value('annualReportExpenseRatio'),
                'inception_date': None,
                'issuer': get_value('fundFamily'),
                'benchmark_index': get_value('underlyingSymbol'),
                'dividend_yield': get_value('dividendYield'),
                'ex_dividend_date': None,
            }
            
            # Calculate day change
            if etf_info['current_price'] and etf_info['previous_close']:
                etf_info['day_change'] = etf_info['current_price'] - etf_info['previous_close']
            
            # Calculate bid-ask spread
            if etf_info['bid'] and etf_info['ask']:
                etf_info['bid_ask_spread'] = etf_info['ask'] - etf_info['bid']
            
            # Parse inception date
            if info.get('fundInceptionDate'):
                try:
                    inception_timestamp = info.get('fundInceptionDate')
                    if inception_timestamp:
                        etf_info['inception_date'] = datetime.fromtimestamp(inception_timestamp).date()
                except Exception:
                    pass
            
            # Parse ex-dividend date
            if info.get('exDividendDate'):
                try:
                    ex_div_timestamp = info.get('exDividendDate')
                    if ex_div_timestamp:
                        etf_info['ex_dividend_date'] = datetime.fromtimestamp(ex_div_timestamp).date()
                except Exception:
                    pass
            
            return etf_info
            
        except Exception as e:
            error_msg = str(e)
            # 404 errors are common with yfinance and can be ignored
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.debug(f"ETF {symbol} not found in yfinance (404) - this is normal")
            else:
                logger.warning(f"Error getting ETF info for {symbol}: {error_msg}")
            return None
    
    async def get_etf_basic_info(self, symbol: str) -> Optional[ETFBasicInfo]:
        """Get basic ETF information as ETFBasicInfo model"""
        info = await self.get_etf_info(symbol)
        if not info:
            return None
        
        return ETFBasicInfo(
            symbol=info['symbol'],
            name=info['name'],
            description=info.get('description'),
            current_price=info.get('current_price'),
            previous_close=info.get('previous_close'),
            day_change=info.get('day_change'),
            day_change_percent=info.get('day_change_percent'),
            volume=info.get('volume'),
            avg_volume=info.get('avg_volume'),
            bid=info.get('bid'),
            ask=info.get('ask'),
            bid_ask_spread=info.get('bid_ask_spread'),
            week_52_high=info.get('week_52_high'),
            week_52_low=info.get('week_52_low'),
            aum=info.get('aum'),
            expense_ratio=info.get('expense_ratio'),
            inception_date=info.get('inception_date'),
            issuer=info.get('issuer'),
            benchmark_index=info.get('benchmark_index'),
            dividend_yield=info.get('dividend_yield'),
            ex_dividend_date=info.get('ex_dividend_date'),
            timestamp=datetime.now()
        )
    
    async def get_etf_history(self, symbol: str, period: str = "1y", start_date: str = None, end_date: str = None) -> List[ETFPriceData]:
        """Get historical price data for ETF"""
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol.upper())
            )
            
            # Suppress yfinance warnings
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                
                # Get historical data
                def fetch_history():
                    try:
                        if start_date and end_date:
                            return ticker.history(start=start_date, end=end_date)
                        else:
                            return ticker.history(period=period)
                    except Exception as e:
                        # Handle 404 and other errors gracefully
                        if "404" in str(e) or "not found" in str(e).lower():
                            return pd.DataFrame()
                        raise
                
                hist = await loop.run_in_executor(self.executor, fetch_history)
            
            if hist is None or hist.empty:
                logger.debug(f"No historical data available for {symbol} (this is normal for some symbols)")
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
                        logger.debug(f"Skipping bar for {symbol} on {bar_date}: missing price data")
                        continue
                    
                    # Ensure high >= low, and both are within reasonable range of open/close
                    if high_price < low_price:
                        logger.warning(f"Invalid high/low for {symbol} on {bar_date}: high={high_price}, low={low_price}, swapping")
                        high_price, low_price = low_price, high_price
                    
                    # Ensure high >= max(open, close) and low <= min(open, close)
                    max_price = max(open_price, close_price)
                    min_price = min(open_price, close_price)
                    
                    if high_price < max_price:
                        logger.debug(f"Adjusting high for {symbol} on {bar_date}: {high_price} -> {max_price}")
                        high_price = max_price
                    
                    if low_price > min_price:
                        logger.debug(f"Adjusting low for {symbol} on {bar_date}: {low_price} -> {min_price}")
                        low_price = min_price
                    
                    # Check for unreasonable spreads (more than 20% daily range is suspicious)
                    price_range = high_price - low_price
                    avg_price = (open_price + close_price) / 2
                    spread_pct = (price_range / avg_price * 100) if avg_price > 0 else 0
                    
                    if spread_pct > 20:
                        logger.warning(f"Unusually large spread for {symbol} on {bar_date}: {spread_pct:.2f}% (high={high_price}, low={low_price})")
                        # Cap the spread to reasonable values
                        max_spread = avg_price * 0.10  # Max 10% spread
                        if price_range > max_spread:
                            center = (high_price + low_price) / 2
                            high_price = center + max_spread / 2
                            low_price = center - max_spread / 2
                            logger.info(f"Capped spread for {symbol} on {bar_date} to 10%")
                    
                    bar = ETFPriceData(
                        date=bar_date,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        adjusted_close=float(row['Close']) if pd.notna(row['Close']) else 0.0
                    )
                    
                    bars.append(bar)
                    
                except Exception as e:
                    logger.warning(f"Error processing row for {symbol}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(bars)} historical bars for {symbol}")
            return bars
            
        except Exception as e:
            error_msg = str(e)
            # 404 errors are common and can be ignored
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.debug(f"ETF {symbol} history not found (404) - this is normal")
            else:
                logger.warning(f"Error getting ETF history for {symbol}: {error_msg}")
            return []
    
    async def get_etf_holdings(self, symbol: str) -> List[ETFHolding]:
        """Get ETF holdings information"""
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol.upper())
            )
            
            # Suppress yfinance warnings
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                
                # Try to get holdings
                try:
                    # Some ETFs have holdings available
                    holdings_data = await loop.run_in_executor(
                        self.executor,
                        lambda: ticker.holdings if hasattr(ticker, 'holdings') else None
                    )
                    
                    # Alternative: try to get from info
                    if not holdings_data:
                        info = await loop.run_in_executor(
                            self.executor,
                            lambda: ticker.info
                        )
                        
                        # Some ETFs have topHoldings in info
                        if info and 'topHoldings' in info:
                            holdings_data = info['topHoldings']
                    
                    if not holdings_data:
                        # Try major_holders as fallback
                        try:
                            major_holders = await loop.run_in_executor(
                                self.executor,
                                lambda: ticker.major_holders
                            )
                            if major_holders is not None and not major_holders.empty:
                                # This is usually institutional holders, not stock holdings
                                # But we can try to extract some info
                                pass
                        except Exception:
                            pass
                    
                    if not holdings_data:
                        logger.debug(f"No holdings data available for {symbol}")
                        return []
                    
                    holdings = []
                    
                    # Handle different data formats
                    if isinstance(holdings_data, dict):
                        for holding_symbol, weight in holdings_data.items():
                            if weight and weight > 0:
                                holding = ETFHolding(
                                    symbol=holding_symbol,
                                    weight=float(weight) if isinstance(weight, (int, float)) else None,
                                )
                                holdings.append(holding)
                    elif isinstance(holdings_data, pd.DataFrame):
                        for _, row in holdings_data.iterrows():
                            try:
                                holding_symbol = str(row.iloc[0]) if len(row) > 0 else None
                                weight = float(row.iloc[1]) if len(row) > 1 else None
                                
                                if holding_symbol and weight:
                                    holding = ETFHolding(
                                        symbol=holding_symbol,
                                        weight=weight,
                                    )
                                    holdings.append(holding)
                            except Exception as e:
                                logger.debug(f"Error parsing holding row: {str(e)}")
                                continue
                    
                    logger.info(f"Retrieved {len(holdings)} holdings for {symbol}")
                    return holdings
                    
                except Exception as e:
                    logger.debug(f"Could not get holdings for {symbol}: {str(e)}")
                    return []
            
        except Exception as e:
            error_msg = str(e)
            # 404 errors are common and can be ignored
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.debug(f"ETF {symbol} holdings not found (404) - this is normal")
            else:
                logger.debug(f"Error getting ETF holdings for {symbol}: {error_msg}")
            return []
    
    async def get_etf_dividends(self, symbol: str) -> List[ETFDividendHistory]:
        """Get dividend history for ETF"""
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol.upper())
            )
            
            # Suppress yfinance warnings
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                
                dividends = await loop.run_in_executor(
                    self.executor,
                    lambda: ticker.dividends
                )
            
            if dividends is None or dividends.empty:
                return []
            
            dividend_history = []
            for date_idx, amount in dividends.items():
                try:
                    if isinstance(date_idx, pd.Timestamp):
                        div_date = date_idx.date()
                    else:
                        div_date = date_idx
                    
                    dividend = ETFDividendHistory(
                        date=div_date,
                        amount=float(amount)
                    )
                    
                    dividend_history.append(dividend)
                    
                except Exception as e:
                    logger.warning(f"Error processing dividend for {symbol}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(dividend_history)} dividend records for {symbol}")
            return dividend_history
            
        except Exception as e:
            error_msg = str(e)
            # 404 errors are common and can be ignored
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.debug(f"ETF {symbol} dividends not found (404) - this is normal")
            else:
                logger.debug(f"Error getting ETF dividends for {symbol}: {error_msg}")
            return []
    
    async def close(self):
        """Close the executor"""
        if self.executor:
            self.executor.shutdown(wait=True)

