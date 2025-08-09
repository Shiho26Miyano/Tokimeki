import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import numpy as np
import pandas as pd
from .cache_service import AsyncCacheService

logger = logging.getLogger(__name__)

class AsyncStockService:
    def __init__(self, cache_service: AsyncCacheService):
        self.cache_service = cache_service
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def analyze_stock(
        self, 
        symbol: str, 
        strategy: str = "trend",
        period: str = "1y"
    ) -> Dict[str, Any]:
        """Analyze stock using trading strategies"""
        
        try:
            logger.info(f"Starting stock analysis for {symbol} with strategy {strategy} and period {period}")
            
            # Convert period to days
            period_days = {
                "3mo": 90,
                "6mo": 180,
                "1y": 365,
                "2y": 730,
                "5y": 1825
            }.get(period, 365)
            
            logger.info(f"Fetching {period_days} days of data for {symbol}")
            
            # Get stock data
            data = await self.get_stock_data(symbol, period_days)
            if not data:
                logger.error(f"No data returned from get_stock_data for {symbol}")
                raise Exception(f"No data available for {symbol}")
            
            if not data.get('data') or len(data['data']) == 0:
                logger.error(f"Empty data array for {symbol}")
                raise Exception(f"No data available for {symbol}")
            
            logger.info(f"Retrieved {len(data['data'])} data points for {symbol}")
            
            # Calculate metrics based on strategy
            prices = [day['Close'] for day in data['data']]
            if len(prices) < 2:
                logger.error(f"Not enough price data for {symbol}: {len(prices)} points")
                raise Exception(f"Not enough price data for {symbol}")
            
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:  # Avoid division by zero
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
                else:
                    returns.append(0)
            
            if len(returns) == 0:
                logger.error(f"No valid returns calculated for {symbol}")
                raise Exception(f"Unable to calculate returns for {symbol}")
            
            # Calculate basic metrics
            total_return = ((prices[-1] / prices[0]) - 1) * 100 if prices[0] > 0 else 0
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
            sharpe_ratio = (np.mean(returns) * np.sqrt(252)) / (np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
            
            # Calculate max drawdown
            peak = prices[0]
            max_drawdown = 0
            for price in prices:
                if price > peak:
                    peak = price
                if peak > 0:
                    drawdown = (peak - price) / peak
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
            
            # Calculate VaR (95%)
            var_95 = np.percentile(returns, 5) * 100 if len(returns) > 0 else 0
            
            # Generate trading signals based on strategy
            latest_signal = self._generate_signal(prices, strategy)
            
            # Handle date formatting safely
            last_data_point = data['data'][-1]
            
            # Try different ways to get the date
            last_date = None
            if 'Date' in last_data_point:
                last_date = last_data_point['Date']
            elif 'date' in last_data_point:
                last_date = last_data_point['date']
            else:
                last_date = datetime.now()
            
            if hasattr(last_date, 'strftime'):
                date_str = last_date.strftime('%Y-%m-%d')
            else:
                date_str = str(last_date)
            
            result = {
                "latest_signals": {
                    "signal": latest_signal,
                    "price": prices[-1],
                    "date": date_str
                },
                "metrics": {
                    "total_return": round(total_return, 2),
                    "volatility": round(volatility, 2),
                    "sharpe_ratio": round(sharpe_ratio, 2),
                    "max_drawdown": round(max_drawdown * 100, 2),
                    "var_95": round(var_95, 2)
                }
            }
            
            logger.info(f"Stock analysis completed successfully for {symbol}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_stock for {symbol}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise e
    
    def _generate_signal(self, prices: List[float], strategy: str) -> int:
        """Generate trading signal based on strategy"""
        if len(prices) < 20:
            return 0  # Hold
        
        if strategy == "trend":
            # Simple moving average crossover
            short_ma = np.mean(prices[-10:])
            long_ma = np.mean(prices[-20:])
            current_price = prices[-1]
            
            if current_price > short_ma > long_ma:
                return 1  # Buy
            elif current_price < short_ma < long_ma:
                return -1  # Sell
            else:
                return 0  # Hold
                
        elif strategy == "mean_reversion":
            # Mean reversion strategy
            mean_price = np.mean(prices)
            current_price = prices[-1]
            std_price = np.std(prices)
            
            if current_price < mean_price - std_price:
                return 1  # Buy (oversold)
            elif current_price > mean_price + std_price:
                return -1  # Sell (overbought)
            else:
                return 0  # Hold
                
        elif strategy == "momentum":
            # Momentum strategy
            recent_return = (prices[-1] / prices[-5] - 1) * 100
            if recent_return > 5:
                return 1  # Buy (strong momentum)
            elif recent_return < -5:
                return -1  # Sell (weak momentum)
            else:
                return 0  # Hold
        
        return 0  # Default to hold
    
    async def get_stock_history(
        self, 
        symbols: List[str], 
        days: int = 1095
    ) -> Dict[str, Any]:
        """Get historical stock data for multiple symbols"""
        
        # Create tasks for concurrent execution
        tasks = [self.get_stock_data(symbol, days) for symbol in symbols]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                processed_results[symbol] = {
                    "success": False,
                    "error": str(result)
                }
            elif result is None:
                processed_results[symbol] = {
                    "success": False,
                    "error": "No data available"
                }
            else:
                # Format data for D3.js charts
                dates = []
                closes = []
                for day in result['data']:
                    date_obj = day['Date']
                    if hasattr(date_obj, 'strftime'):
                        dates.append(date_obj.strftime('%Y-%m-%d'))
                    else:
                        dates.append(str(date_obj))
                    closes.append(float(day['Close']))
                
                processed_results[symbol] = {
                    "success": True,
                    "symbol": symbol,
                    "dates": dates,
                    "closes": closes
                }
        
        return processed_results
    
    async def get_available_companies(self) -> List[Dict[str, str]]:
        """Get list of available companies"""
        companies = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "META", "name": "Meta Platforms Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "NFLX", "name": "Netflix Inc."},
            {"symbol": "AMD", "name": "Advanced Micro Devices Inc."},
            {"symbol": "INTC", "name": "Intel Corporation"}
        ]
        return companies
    
    async def get_available_tickers(self) -> List[str]:
        """Get list of available tickers"""
        tickers = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC",
            "BRK-B", "JNJ", "V", "JPM", "WMT", "PG", "KO", "XOM", "SPY", "QQQ", "VOO",
            "ARKK", "EEM", "XLF", "ES=F", "NQ=F", "YM=F", "RTY=F", "MES=F", "MNQ=F",
            "MYM=F", "M2K=F", "GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F", "ZC=F",
            "ZS=F", "ZW=F", "VX=F", "BTC=F", "ETH=F"
        ]
        return tickers

    async def get_stock_data(
        self, 
        symbol: str, 
        days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """Get stock data asynchronously using ThreadPoolExecutor"""
        
        try:
            logger.info(f"Fetching stock data for {symbol} for {days} days")
            
            # Generate cache key
            cache_key = f"stock_data:{symbol}:{days}"
            
            # Check cache first
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for stock data: {symbol}")
                return cached_data
            
            logger.info(f"Cache miss for {symbol}, fetching from yfinance")
            
            # Run yfinance in thread pool (since it's not async)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol)
            )
            
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
            
            hist = await loop.run_in_executor(
                self.executor,
                lambda: ticker.history(start=start_date, end=end_date)
            )
            
            if hist.empty:
                logger.warning(f"No data available for {symbol} - empty DataFrame returned")
                return None
            
            logger.info(f"Retrieved {len(hist)} rows from yfinance for {symbol}")
            
            # Process data - yfinance returns DataFrame with datetime index
            records = []
            for date, row in hist.iterrows():
                try:
                    record = {
                        'Date': date,
                        'Open': float(row['Open']) if pd.notna(row['Open']) else 0.0,
                        'High': float(row['High']) if pd.notna(row['High']) else 0.0,
                        'Low': float(row['Low']) if pd.notna(row['Low']) else 0.0,
                        'Close': float(row['Close']) if pd.notna(row['Close']) else 0.0,
                        'Volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        'Dividends': float(row['Dividends']) if pd.notna(row['Dividends']) else 0.0,
                        'Stock Splits': float(row['Stock Splits']) if pd.notna(row['Stock Splits']) else 0.0
                    }
                    records.append(record)
                except Exception as row_error:
                    logger.error(f"Error processing row for {symbol} at {date}: {row_error}")
                    continue
            
            if len(records) == 0:
                logger.error(f"No valid records processed for {symbol}")
                return None
            
            # Calculate summary statistics
            close_prices = [r['Close'] for r in records if r['Close'] > 0]
            if len(close_prices) == 0:
                logger.error(f"No valid close prices for {symbol}")
                return None
            
            data = {
                "symbol": symbol,
                "period": f"{days} days",
                "data": records,
                "summary": {
                    "start_price": float(close_prices[0]),
                    "end_price": float(close_prices[-1]),
                    "min_price": float(min(close_prices)),
                    "max_price": float(max(close_prices)),
                    "avg_price": float(sum(close_prices) / len(close_prices)),
                    "volume": int(sum(r['Volume'] for r in records)),
                    "price_change": float(close_prices[-1] - close_prices[0]),
                    "percent_change": float(((close_prices[-1] / close_prices[0]) - 1) * 100) if close_prices[0] > 0 else 0
                }
            }
            
            # Cache the result
            try:
                await self.cache_service.set(cache_key, data, ttl=300)  # 5 minutes
                logger.info(f"Cached stock data for {symbol}")
            except Exception as cache_error:
                logger.warning(f"Failed to cache data for {symbol}: {cache_error}")
            
            logger.info(f"Successfully fetched data for {symbol}: {len(records)} records")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            return None
    
    async def get_multiple_stocks(
        self, 
        symbols: List[str], 
        days: int = 7
    ) -> Dict[str, Any]:
        """Get data for multiple stocks concurrently"""
        
        # Create tasks for concurrent execution
        tasks = [self.get_stock_data(symbol, days) for symbol in symbols]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                processed_results[symbol] = {
                    "success": False,
                    "error": str(result)
                }
            elif result is None:
                processed_results[symbol] = {
                    "success": False,
                    "error": "No data available"
                }
            else:
                processed_results[symbol] = {
                    "success": True,
                    "data": result
                }
        
        return processed_results
    
    async def get_comprehensive_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive stock data including all yfinance information"""
        
        cache_key = f"comprehensive_stock_data:{symbol}"
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for comprehensive stock data: {symbol}")
            return cached_data
        
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol)
            )
            
            # Fetch only reliable yfinance data
            tasks = [
                loop.run_in_executor(self.executor, lambda: ticker.info),
                loop.run_in_executor(self.executor, lambda: ticker.fast_info),
                loop.run_in_executor(self.executor, lambda: ticker.history(period="1y")),
                loop.run_in_executor(self.executor, lambda: ticker.dividends),
                loop.run_in_executor(self.executor, lambda: ticker.splits),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            info, fast_info, history, dividends, splits = results
            
            # Basic company info
            company_info = {
                "symbol": symbol,
                "name": info.get("longName", "") if not isinstance(info, Exception) else "",
                "sector": info.get("sector", "") if not isinstance(info, Exception) else "",
                "industry": info.get("industry", "") if not isinstance(info, Exception) else "",
                "website": info.get("website", "") if not isinstance(info, Exception) else "",
                "employees": info.get("fullTimeEmployees", 0) if not isinstance(info, Exception) else 0,
                "description": info.get("longBusinessSummary", "") if not isinstance(info, Exception) else "",
            }
            
            # Market data
            market_data = {
                "current_price": fast_info.get("lastPrice", 0) if not isinstance(fast_info, Exception) else 0,
                "market_cap": fast_info.get("marketCap", 0) if not isinstance(fast_info, Exception) else 0,
                "shares_outstanding": fast_info.get("sharesOutstanding", 0) if not isinstance(fast_info, Exception) else 0,
                "pe_ratio": info.get("trailingPE", 0) if not isinstance(info, Exception) else 0,
                "dividend_yield": info.get("dividendYield", 0) if not isinstance(info, Exception) else 0,
                "beta": info.get("beta", 0) if not isinstance(info, Exception) else 0,
                "volume": fast_info.get("volume", 0) if not isinstance(fast_info, Exception) else 0,
            }
            
            # Historical data
            historical_data = {}
            if not isinstance(history, Exception) and not history.empty:
                historical_data = {
                    "period": "1y",
                    "data_points": len(history),
                    "start_price": float(history['Close'].iloc[0]),
                    "end_price": float(history['Close'].iloc[-1]),
                    "min_price": float(history['Close'].min()),
                    "max_price": float(history['Close'].max()),
                    "avg_price": float(history['Close'].mean()),
                    "total_volume": int(history['Volume'].sum()),
                    "price_change": float(history['Close'].iloc[-1] - history['Close'].iloc[0]),
                    "percent_change": float(((history['Close'].iloc[-1] / history['Close'].iloc[0]) - 1) * 100),
                    "volatility": float(history['Close'].pct_change().std() * np.sqrt(252) * 100),
                }
            
            # Dividends and splits
            dividend_data = {
                "dividends": dividends.to_dict() if not isinstance(dividends, Exception) and hasattr(dividends, 'empty') and not dividends.empty else {},
                "splits": splits.to_dict() if not isinstance(splits, Exception) and hasattr(splits, 'empty') and not splits.empty else {},
            }
            
            # Financial data (simplified)
            financial_data = {
                "available": "Basic data only - financial statements require premium access"
            }
            
            # Analyst data (simplified)
            analyst_data = {
                "available": "Basic data only - analyst data requires premium access"
            }
            
            # Additional data (simplified)
            additional_data = {
                "available": "Basic data only - additional data requires premium access"
            }
            
            comprehensive_data = {
                "company_info": company_info,
                "market_data": market_data,
                "historical_data": historical_data,
                "dividend_data": dividend_data,
                "financial_data": financial_data,
                "analyst_data": analyst_data,
                "additional_data": additional_data,
                "last_updated": datetime.now().isoformat(),
            }
            
            # Cache for 30 minutes (comprehensive data)
            await self.cache_service.set(cache_key, comprehensive_data, ttl=1800)
            
            logger.info(f"Successfully fetched comprehensive data for {symbol}")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive stock data for {symbol}: {e}")
            return None
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get basic stock information"""
        
        cache_key = f"stock_info:{symbol}"
        cached_info = await self.cache_service.get(cache_key)
        if cached_info:
            return cached_info
        
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(
                self.executor,
                lambda: yf.Ticker(symbol)
            )
            
            info = await loop.run_in_executor(
                self.executor,
                lambda: ticker.info
            )
            
            # Extract relevant info
            stock_info = {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "current_price": info.get("currentPrice", 0)
            }
            
            # Cache for 1 hour
            await self.cache_service.set(cache_key, stock_info, ttl=3600)
            
            return stock_info
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None
    
    async def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """Search for stocks by name or symbol"""
        
        # Simple stock search - in a real app, you'd use a proper search API
        common_stocks = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "META", "name": "Meta Platforms Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "NFLX", "name": "Netflix Inc."},
            {"symbol": "AMD", "name": "Advanced Micro Devices Inc."},
            {"symbol": "INTC", "name": "Intel Corporation"}
        ]
        
        query_lower = query.lower()
        results = []
        
        for stock in common_stocks:
            if (query_lower in stock["symbol"].lower() or 
                query_lower in stock["name"].lower()):
                results.append(stock)
        
        return results[:10]  # Limit to 10 results

    async def get_volatility_event_correlation(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        window: int = 30,
        years: int = 2
    ) -> Dict[str, Any]:
        """Get volatility event correlation data"""
        try:
            # Set default dates if not provided
            if not start_date or not end_date:
                from datetime import datetime, timedelta
                end = datetime.now()
                start = end - timedelta(days=years*365)
                start_date = start.strftime('%Y-%m-%d')
                end_date = end.strftime('%Y-%m-%d')
            
            # Get stock data
            stock_data = await self.get_stock_data(symbol, 365)
            
            if not stock_data or not stock_data.get('data'):
                raise Exception(f"No data available for {symbol}")
            
            # Extract dates and prices
            dates = []
            for day in stock_data['data']:
                if hasattr(day['Date'], 'strftime'):
                    dates.append(day['Date'].strftime('%Y-%m-%d'))
                else:
                    # Handle ISO format dates
                    date_str = str(day['Date'])
                    if 'T' in date_str:
                        dates.append(date_str.split('T')[0])
                    else:
                        dates.append(date_str)
            prices = [day['Close'] for day in stock_data['data']]
            
            if len(prices) < window:
                raise Exception(f"Not enough data for rolling volatility (need at least {window} days)")
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
            
            # Calculate rolling volatility
            rolling_vol = []
            for i in range(window-1, len(returns)):
                window_returns = returns[i-window+1:i+1]
                vol = np.std(window_returns) * np.sqrt(252) * 100
                rolling_vol.append(vol)
            
            # Pad with None values for the first window-1 days
            volatility = [None] * (window-1) + rolling_vol
            
            # Find minimum volatility period
            valid_start = int(len(volatility) * 0.1)
            valid_vols = [v for v in volatility[valid_start:] if v is not None]
            valid_dates = dates[valid_start:]
            
            min_vol = None
            min_vol_date = None
            if valid_vols:
                min_vol = min(valid_vols)
                min_idx = volatility[valid_start:].index(min_vol) + valid_start
                min_vol_date = dates[min_idx]
            
            # Create event titles (empty for now)
            event_titles = [[] for _ in dates]
            
            return {
                "dates": dates,
                "volatility": volatility,
                "event_titles": event_titles,
                "min_vol": min_vol,
                "min_vol_date": min_vol_date
            }
            
        except Exception as e:
            logger.error(f"Volatility event correlation error: {e}")
            raise e

    async def analyze_volatility_regime(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        window: int = 30
    ) -> Dict[str, Any]:
        """Analyze volatility regime"""
        try:
            # Set default dates if not provided
            if not start_date or not end_date:
                from datetime import datetime, timedelta
                end = datetime.now()
                start = end - timedelta(days=365)
                start_date = start.strftime('%Y-%m-%d')
                end_date = end.strftime('%Y-%m-%d')
            
            # Get stock data
            stock_data = await self.get_stock_data(symbol, 365)
            
            if not stock_data or not stock_data.get('data'):
                raise Exception(f"No data available for {symbol}")
            
            # Extract prices
            prices = [day['Close'] for day in stock_data['data']]
            
            if len(prices) < window:
                raise Exception(f"Not enough data for volatility analysis (need at least {window} days)")
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
            
            # Calculate rolling volatility
            rolling_vol = []
            for i in range(window-1, len(returns)):
                window_returns = returns[i-window+1:i+1]
                vol = np.std(window_returns) * np.sqrt(252) * 100
                rolling_vol.append(vol)
            
            # Pad with None values for the first window-1 days
            volatility = [None] * (window-1) + rolling_vol
            
            # Calculate regime statistics
            valid_vols = [v for v in volatility if v is not None]
            if valid_vols:
                avg_vol = np.mean(valid_vols)
                vol_std = np.std(valid_vols)
                high_vol_threshold = avg_vol + vol_std
                low_vol_threshold = avg_vol - vol_std
                
                # Classify regimes
                high_vol_count = sum(1 for v in valid_vols if v > high_vol_threshold)
                low_vol_count = sum(1 for v in valid_vols if v < low_vol_threshold)
                normal_vol_count = len(valid_vols) - high_vol_count - low_vol_count
                
                current_regime = "normal"
                if volatility[-1] and volatility[-1] > high_vol_threshold:
                    current_regime = "high"
                elif volatility[-1] and volatility[-1] < low_vol_threshold:
                    current_regime = "low"
                
                return {
                    "symbol": symbol,
                    "current_regime": current_regime,
                    "avg_volatility": round(avg_vol, 2),
                    "volatility_std": round(vol_std, 2),
                    "high_vol_threshold": round(high_vol_threshold, 2),
                    "low_vol_threshold": round(low_vol_threshold, 2),
                    "regime_counts": {
                        "high": high_vol_count,
                        "normal": normal_vol_count,
                        "low": low_vol_count
                    },
                    "volatility_data": volatility
                }
            else:
                raise Exception("No valid volatility data available")
                
        except Exception as e:
            logger.error(f"Volatility regime analysis error: {e}")
            raise e 