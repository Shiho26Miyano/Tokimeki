"""
FutureQuant Trader Market Data Service
Real-time market data integration with Yahoo Finance
"""
import asyncio
import logging
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import json
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class MarketDataService:
    """Real-time market data service using Yahoo Finance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds cache
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Check cache first
            cache_key = f"price_{symbol}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_ttl:
                    return cached_data['price']
            
            # Fetch from Yahoo Finance
            price = await self._fetch_yahoo_price(symbol)
            
            if price is not None:
                # Update cache
                self.cache[cache_key] = {
                    'price': price,
                    'timestamp': time.time()
                }
                return price
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            
        return None
    
    async def get_batch_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        try:
            # Check cache for all symbols
            prices = {}
            symbols_to_fetch = []
            
            for symbol in symbols:
                cache_key = f"price_{symbol}"
                if cache_key in self.cache:
                    cached_data = self.cache[cache_key]
                    if time.time() - cached_data['timestamp'] < self.cache_ttl:
                        prices[symbol] = cached_data['price']
                    else:
                        symbols_to_fetch.append(symbol)
                else:
                    symbols_to_fetch.append(symbol)
            
            # Fetch remaining symbols
            if symbols_to_fetch:
                batch_prices = await self._fetch_yahoo_batch_prices(symbols_to_fetch)
                prices.update(batch_prices)
                
                # Update cache
                for symbol, price in batch_prices.items():
                    if price is not None:
                        cache_key = f"price_{symbol}"
                        self.cache[cache_key] = {
                            'price': price,
                            'timestamp': time.time()
                        }
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting batch prices: {str(e)}")
            return {}
    
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1d", 
        interval: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """Get historical data for a symbol"""
        try:
            # Check cache first
            cache_key = f"hist_{symbol}_{period}_{interval}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data['timestamp'] < 300:  # 5 min cache for historical
                    return cached_data['data']
            
            # Fetch from Yahoo Finance
            data = await self._fetch_yahoo_historical(symbol, period, interval)
            
            if data is not None and not data.empty:
                # Update cache
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': time.time()
                }
                return data
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            
        return None
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a symbol"""
        try:
            # Check cache first
            cache_key = f"info_{symbol}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data['timestamp'] < 3600:  # 1 hour cache for info
                    return cached_data['data']
            
            # Fetch from Yahoo Finance
            info = await self._fetch_yahoo_info(symbol)
            
            if info:
                # Update cache
                self.cache[cache_key] = {
                    'data': info,
                    'timestamp': time.time()
                }
                return info
                
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {str(e)}")
            
        return None
    
    async def _fetch_yahoo_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Yahoo Finance"""
        try:
            # Use ThreadPoolExecutor to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            
            # Get current price
            price = await loop.run_in_executor(
                self.executor, 
                lambda: ticker.info.get('regularMarketPrice', None)
            )
            
            if price is None:
                # Try alternative method
                hist = await loop.run_in_executor(
                    self.executor,
                    lambda: ticker.history(period="1d", interval="1m")
                )
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            return float(price) if price is not None else None
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo price for {symbol}: {str(e)}")
            return None
    
    async def _fetch_yahoo_batch_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch prices for multiple symbols"""
        try:
            prices = {}
            
            # Process in batches to avoid overwhelming Yahoo Finance
            batch_size = 5
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                
                # Create tasks for batch
                tasks = [self._fetch_yahoo_price(symbol) for symbol in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for symbol, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.error(f"Error fetching price for {symbol}: {str(result)}")
                        prices[symbol] = None
                    else:
                        prices[symbol] = result
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching batch prices: {str(e)}")
            return {symbol: None for symbol in symbols}
    
    async def _fetch_yahoo_historical(
        self, 
        symbol: str, 
        period: str = "1d", 
        interval: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance"""
        try:
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            
            data = await loop.run_in_executor(
                self.executor,
                lambda: ticker.history(period=period, interval=interval)
            )
            
            return data if not data.empty else None
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    async def _fetch_yahoo_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch symbol information from Yahoo Finance"""
        try:
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            
            info = await loop.run_in_executor(
                self.executor,
                lambda: ticker.info
            )
            
            # Extract relevant information
            relevant_info = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'volume': info.get('volume'),
                'avg_volume': info.get('averageVolume'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'Unknown')
            }
            
            return relevant_info
            
        except Exception as e:
            logger.error(f"Error fetching symbol info for {symbol}: {str(e)}")
            return None
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get overall market status"""
        try:
            # Check major indices
            major_indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']  # S&P 500, Dow, NASDAQ, VIX
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'indices': {},
                'market_open': True,
                'last_update': None
            }
            
            for index in major_indices:
                price = await self.get_current_price(index)
                if price is not None:
                    status['indices'][index] = {
                        'price': price,
                        'change': 0.0,  # Would need previous close for change calculation
                        'change_percent': 0.0
                    }
            
            # Determine if market is open (simplified logic)
            now = datetime.now()
            if now.weekday() < 5 and 9 <= now.hour < 16:  # Mon-Fri, 9 AM - 4 PM EST
                status['market_open'] = True
            else:
                status['market_open'] = False
            
            status['last_update'] = datetime.now().isoformat()
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting market status: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'market_open': False
            }
    
    def clear_cache(self, symbol: str = None):
        """Clear cache for specific symbol or all symbols"""
        if symbol:
            # Clear specific symbol cache
            for key in list(self.cache.keys()):
                if key.startswith(f"price_{symbol}") or key.startswith(f"hist_{symbol}") or key.startswith(f"info_{symbol}"):
                    del self.cache[key]
        else:
            # Clear all cache
            self.cache.clear()
        
        logger.info(f"Cache cleared for {'symbol ' + symbol if symbol else 'all symbols'}")
    
    async def start_real_time_updates(self, symbols: List[str], callback):
        """Start real-time price updates for symbols"""
        try:
            while True:
                prices = await self.get_batch_prices(symbols)
                if callback:
                    await callback(prices)
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Real-time updates cancelled")
        except Exception as e:
            logger.error(f"Error in real-time updates: {str(e)}")

# Global instance
market_data_service = MarketDataService()
