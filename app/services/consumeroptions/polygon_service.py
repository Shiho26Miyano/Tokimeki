"""
Consumer Options Polygon API Service
Handles fetching Open Interest change data for heatmap visualization
Uses the massive library for Polygon API access
"""
import asyncio
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import yfinance as yf
from massive import RESTClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Thread pool executor for running synchronous massive library calls
_executor = ThreadPoolExecutor(max_workers=10)


def trading_days_2() -> Tuple[str, str]:
    """Return (T_minus_1, T) as ISO dates (skip weekends)."""
    d = date.today()
    if d.weekday() >= 5:  # Sat/Sun -> last Friday is T
        d = d - timedelta(days=d.weekday() - 4)
    t = d
    t1 = t - timedelta(days=1)
    while t1.weekday() >= 5:
        t1 -= timedelta(days=1)
    return t1.isoformat(), t.isoformat()


class ConsumerOptionsPolygonService:
    """Service for fetching consumer options data from Polygon API using massive library."""

    def __init__(self) -> None:
        self.api_key = settings.polygon_api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            logger.warning(
                "POLYGON_API_KEY not set. Consumer options features may not work."
            )
        self.client: Optional[RESTClient] = None

    def _get_client(self) -> RESTClient:
        """Get or create RESTClient."""
        if self.client is None:
            if not self.api_key:
                raise ValueError("POLYGON_API_KEY is not set. Cannot create RESTClient.")
            self.client = RESTClient(self.api_key)
        return self.client

    async def close(self) -> None:
        """Close client (no-op for RESTClient, but keeping interface consistent)."""
        self.client = None


    async def get_spot_price(self, client: RESTClient, ticker: str) -> float:
        """Get current spot price for underlying using massive library."""
        def _get_price():
            """Get price from Polygon API using available endpoints"""
            from datetime import date, timedelta
            
            ticker_upper = ticker.upper()
            today = date.today().strftime("%Y-%m-%d")
            yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Method 1: Try get_previous_close_agg (usually available on lower tier plans)
            try:
                logger.debug(f"Trying get_previous_close_agg for {ticker}")
                prev_close = client.get_previous_close_agg(ticker_upper)
                logger.debug(f"get_previous_close_agg response type: {type(prev_close)}, attributes: {dir(prev_close) if hasattr(prev_close, '__dict__') else 'N/A'}")
                
                # Try to extract price from various possible attributes
                for attr in ['close', 'c', 'price', 'p', 'results']:
                    if hasattr(prev_close, attr):
                        try:
                            value = getattr(prev_close, attr)
                            logger.debug(f"  Found attribute '{attr}': {type(value)} = {value}")
                            if attr in ['close', 'c', 'price', 'p'] and value:
                                logger.info(f"Got price for {ticker} from get_previous_close_agg.{attr}: {value}")
                                return float(value)
                        except Exception as e_attr:
                            logger.debug(f"  Error accessing attribute '{attr}': {e_attr}")
                
                # Try results attribute
                if hasattr(prev_close, 'results'):
                    results = prev_close.results
                    logger.debug(f"  Found results attribute: {type(results)}")
                    if isinstance(results, dict):
                        price = results.get("c") or results.get("close") or results.get("price") or results.get("p")
                        if price:
                            logger.info(f"Got price for {ticker} from get_previous_close_agg.results: {price}")
                            return float(price)
                    elif isinstance(results, list) and results:
                        price = results[0].get("c") or results[0].get("close") or results[0].get("price") or results[0].get("p")
                        if price:
                            logger.info(f"Got price for {ticker} from get_previous_close_agg.results[0]: {price}")
                            return float(price)
                
                # Try dict conversion
                try:
                    prev_dict = vars(prev_close) if hasattr(prev_close, '__dict__') else {}
                    logger.debug(f"  Dict representation keys: {list(prev_dict.keys()) if prev_dict else 'empty'}")
                    for key in ['c', 'close', 'price', 'p', 'results']:
                        if key in prev_dict and prev_dict[key]:
                            if key == 'results':
                                continue  # Already handled above
                            logger.info(f"Got price for {ticker} from get_previous_close_agg dict[{key}]: {prev_dict[key]}")
                            return float(prev_dict[key])
                except Exception as e_dict:
                    logger.debug(f"  Error converting to dict: {e_dict}")
                    
            except Exception as e1:
                logger.warning(f"get_previous_close_agg failed for {ticker}: {type(e1).__name__}: {str(e1)}")
            
            # Method 2: Try get_aggs with recent day data
            try:
                logger.debug(f"Trying get_aggs for {ticker} from {yesterday} to {today}")
                aggs = client.get_aggs(
                    ticker=ticker_upper,
                    multiplier=1,
                    timespan="day",
                    from_=yesterday,
                    to=today,
                )
                
                # Get the most recent aggregate
                latest_agg = None
                count = 0
                for agg in aggs:
                    latest_agg = agg
                    count += 1
                    if count == 1:  # Log first one
                        logger.debug(f"  First agg type: {type(agg)}, attributes: {dir(agg) if hasattr(agg, '__dict__') else 'N/A'}")
                
                if latest_agg:
                    for attr in ['c', 'close', 'price', 'p']:
                        if hasattr(latest_agg, attr):
                            try:
                                price = getattr(latest_agg, attr)
                                if price:
                                    logger.info(f"Got price for {ticker} from get_aggs.{attr}: {price}")
                                    return float(price)
                            except Exception as e_attr:
                                logger.debug(f"  Error accessing get_aggs attribute '{attr}': {e_attr}")
                    
                    # Try dict conversion
                    try:
                        agg_dict = vars(latest_agg) if hasattr(latest_agg, '__dict__') else {}
                        logger.debug(f"  get_aggs dict keys: {list(agg_dict.keys()) if agg_dict else 'empty'}")
                        for key in ['c', 'close', 'price', 'p']:
                            if key in agg_dict and agg_dict[key]:
                                logger.info(f"Got price for {ticker} from get_aggs dict[{key}]: {agg_dict[key]}")
                                return float(agg_dict[key])
                    except Exception as e_dict:
                        logger.debug(f"  Error converting get_aggs to dict: {e_dict}")
                else:
                    logger.debug(f"  No aggregates returned from get_aggs")
            except Exception as e2:
                logger.warning(f"get_aggs failed for {ticker}: {type(e2).__name__}: {str(e2)}")
            
            # Method 3: Try get_daily_open_close_agg
            try:
                logger.debug(f"Trying get_daily_open_close_agg for {ticker} on {yesterday}")
                daily_agg = client.get_daily_open_close_agg(ticker_upper, yesterday)
                logger.debug(f"  Response type: {type(daily_agg)}, attributes: {dir(daily_agg) if hasattr(daily_agg, '__dict__') else 'N/A'}")
                for attr in ['close', 'c', 'price', 'p']:
                    if hasattr(daily_agg, attr):
                        try:
                            price = getattr(daily_agg, attr)
                            if price:
                                logger.info(f"Got price for {ticker} from get_daily_open_close_agg.{attr}: {price}")
                                return float(price)
                        except Exception as e_attr:
                            logger.debug(f"  Error accessing get_daily_open_close_agg attribute '{attr}': {e_attr}")
            except Exception as e3:
                logger.warning(f"get_daily_open_close_agg failed for {ticker}: {type(e3).__name__}: {str(e3)}")
            
            # Method 4: Try get_ticker_details
            try:
                logger.debug(f"Trying get_ticker_details for {ticker}")
                details = client.get_ticker_details(ticker_upper)
                logger.debug(f"  Response type: {type(details)}, attributes: {dir(details) if hasattr(details, '__dict__') else 'N/A'}")
                for attr in ['price', 'p', 'market_cap', 'marketCap']:
                    if hasattr(details, attr):
                        try:
                            price = getattr(details, attr)
                            if price and attr in ['price', 'p']:  # Only use price fields
                                logger.info(f"Got price for {ticker} from get_ticker_details.{attr}: {price}")
                                return float(price)
                        except Exception as e_attr:
                            logger.debug(f"  Error accessing get_ticker_details attribute '{attr}': {e_attr}")
            except Exception as e4:
                logger.warning(f"get_ticker_details failed for {ticker}: {type(e4).__name__}: {str(e4)}")
            
            # If all Polygon methods failed, try yfinance as fallback
            logger.warning(f"All Polygon API methods failed for {ticker}, trying yfinance fallback")
            price = None
            yfinance_error = None
            
            try:
                logger.debug(f"Fetching {ticker} price from yfinance...")
                yf_ticker = yf.Ticker(ticker_upper)
                
                # Try info first
                try:
                    info = yf_ticker.info
                    logger.debug(f"yfinance info keys: {list(info.keys())[:10] if isinstance(info, dict) else 'not a dict'}")
                    
                    # Try multiple price fields from yfinance
                    price = (
                        info.get('regularMarketPrice') or
                        info.get('currentPrice') or
                        info.get('previousClose') or
                        info.get('regularMarketPreviousClose') or
                        info.get('close') or
                        None
                    )
                    if price:
                        logger.info(f"Got price for {ticker} from yfinance.info: {price}")
                        return float(price)
                except Exception as e_info:
                    logger.debug(f"yfinance.info failed: {e_info}")
                    yfinance_error = str(e_info)
                
                # Try getting from recent history (1 minute intervals)
                if price is None:
                    try:
                        logger.debug(f"Trying yfinance history 1d 1m...")
                        hist = yf_ticker.history(period="1d", interval="1m")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            logger.info(f"Got price for {ticker} from yfinance history (1d 1m): {price}")
                            return float(price)
                    except Exception as e_hist1:
                        logger.debug(f"yfinance history 1d 1m failed: {e_hist1}")
                        yfinance_error = str(e_hist1)
                
                # Try last 5 days and get most recent close
                if price is None:
                    try:
                        logger.debug(f"Trying yfinance history 5d...")
                        hist = yf_ticker.history(period="5d")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            logger.info(f"Got price for {ticker} from yfinance history (5d): {price}")
                            return float(price)
                    except Exception as e_hist5:
                        logger.debug(f"yfinance history 5d failed: {e_hist5}")
                        yfinance_error = str(e_hist5)
                
                # Try 1 day daily
                if price is None:
                    try:
                        logger.debug(f"Trying yfinance history 1d...")
                        hist = yf_ticker.history(period="1d")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            logger.info(f"Got price for {ticker} from yfinance history (1d): {price}")
                            return float(price)
                    except Exception as e_hist1d:
                        logger.debug(f"yfinance history 1d failed: {e_hist1d}")
                        yfinance_error = str(e_hist1d)
                    
            except Exception as e_yf:
                logger.error(f"yfinance fallback failed for {ticker}: {type(e_yf).__name__}: {e_yf}")
                yfinance_error = str(e_yf)
            
            # If we get here, all methods including yfinance failed
            error_msg = (
                f"Could not get price for {ticker} using any method. "
                f"Polygon methods tried: get_previous_close_agg, get_aggs, get_daily_open_close_agg, get_ticker_details. "
                f"yfinance fallback also failed: {yfinance_error or 'unknown error'}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Run synchronous call in thread pool
            loop = asyncio.get_event_loop()
            price = await loop.run_in_executor(_executor, _get_price)
            return price
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching spot price for {ticker}: {e}")
            raise ValueError(f"Failed to fetch spot price for {ticker}: {e}")

    async def list_contracts(
        self,
        client: RESTClient,
        underlying: str,
        contract_type: Optional[str] = None,  # "call"/"put" or None for both
        limit_expiries: int = 8,
    ) -> List[Dict[str, Any]]:
        """Pull option contract metadata and keep the nearest N expiries."""
        def _get_contracts():
            res: List[Dict[str, Any]] = []
            
            # Build parameters for list_options_contracts
            params: Dict[str, Any] = {
                "underlying_ticker": underlying.upper(),
                "expired": "false",
                "limit": 1000,
            }
            if contract_type:
                params["contract_type"] = contract_type[0].upper()  # C/P

            # Iterate through contracts using massive library
            for contract in client.list_options_contracts(**params):
                # Convert contract object to dict
                try:
                    contract_dict = vars(contract)
                except:
                    # Fallback: build dict from attributes
                    contract_dict = {
                        attr: getattr(contract, attr)
                        for attr in dir(contract)
                        if not attr.startswith('_') and not callable(getattr(contract, attr, None))
                    }
                res.append(contract_dict)
                
                # Limit total contracts fetched to avoid too many API calls
                if len(res) >= 5000:
                    break
            
            # Order expiries and keep nearest N
            by_exp: Dict[str, List[Dict[str, Any]]] = {}
            for x in res:
                e = x.get("expiration_date")
                if e:
                    by_exp.setdefault(e, []).append(x)

            expiries = sorted(by_exp.keys())[:limit_expiries]
            trimmed = [x for e in expiries for x in by_exp[e]]
            return trimmed
        
        try:
            # Run synchronous call in thread pool
            loop = asyncio.get_event_loop()
            contracts = await loop.run_in_executor(_executor, _get_contracts)
            return contracts
        except Exception as e:
            logger.error(f"Error fetching contracts: {e}")
            raise ValueError(f"Failed to fetch contracts: {e}")

    async def daily_oi_pair(
        self, client: RESTClient, option_ticker: str, d1: str, d2: str
    ) -> Tuple[int, int]:
        """Return (oi_T1, oi_T) for a single contract using 1D aggs."""
        def _get_oi():
            # Use massive library's get_aggs method
            aggs = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="day",
                from_=d1,
                to=d2,
            )
            
            results = []
            for agg in aggs:
                # Convert agg object to dict
                try:
                    agg_dict = vars(agg)
                except:
                    agg_dict = {
                        attr: getattr(agg, attr)
                        for attr in dir(agg)
                        if not attr.startswith('_') and not callable(getattr(agg, attr, None))
                    }
                results.append(agg_dict)
            
            if not results:
                logger.debug(f"No results for {option_ticker} from {d1} to {d2}")
                return 0, 0

            # Sort by timestamp and get first and last OI
            sorted_results = sorted(results, key=lambda x: x.get("t", x.get("timestamp", 0)))

            oi_t1 = int(sorted_results[0].get("oi", sorted_results[0].get("open_interest", 0)))
            oi_t = int(sorted_results[-1].get("oi", sorted_results[-1].get("open_interest", 0)))
            return oi_t1, oi_t
        
        try:
            # Run synchronous call in thread pool
            loop = asyncio.get_event_loop()
            oi_pair = await loop.run_in_executor(_executor, _get_oi)
            return oi_pair
        except Exception as e:
            logger.debug(
                f"Error fetching OI for {option_ticker} from {d1} to {d2}: {e}"
            )
            return 0, 0

    async def get_oi_change(
        self,
        symbol: str,
        strike_band_pct: float = 0.2,
        expiries: int = 8,
        combine_cp: bool = True,
        max_concurrency: int = 24,
    ) -> Dict[str, Any]:
        """
        Return a heatmap-ready payload: rows=expiries, cols=strikes, values=ΔOI.
        """
        if not self.api_key:
            raise ValueError(
                "POLYGON_API_KEY is not set. Please set POLYGON_API_KEY environment variable."
            )

        client = self._get_client()
        try:
            # Get trading days
            t1, t = trading_days_2()

            # Get spot price
            spot = await self.get_spot_price(client, symbol)
            logger.info(f"Spot price for {symbol}: ${spot:.2f}")

            # Get contracts metadata
            contracts = await self.list_contracts(client, symbol, None, expiries)
            logger.info(f"Found {len(contracts)} contracts for {symbol}")

            # Filter to strike band
            lo = spot * (1 - strike_band_pct)
            hi = spot * (1 + strike_band_pct)
            filtered = [
                c
                for c in contracts
                if (s := c.get("strike_price")) is not None and lo <= float(s) <= hi
            ]
            logger.info(
                f"Filtered to {len(filtered)} contracts within ±{strike_band_pct*100:.0f}% of spot"
            )

            if not filtered:
                return {
                    "symbol": symbol.upper(),
                    "t": t,
                    "t_minus_1": t1,
                    "expiries": [],
                    "strikes": [],
                    "matrix": [],
                    "spot": spot,
                }

            # Collect all (expiry, strike) buckets
            expiries_sorted = sorted({c["expiration_date"] for c in filtered})
            strikes_sorted = sorted({round(float(c["strike_price"]), 2) for c in filtered})
            idx_exp = {e: i for i, e in enumerate(expiries_sorted)}
            idx_str = {s: i for i, s in enumerate(strikes_sorted)}

            # Async gather OI for each contract
            sem = asyncio.Semaphore(max_concurrency)
            results: List[Tuple[str, float, str, int]] = []  # (expiry, strike, cp, dOI)

            async def worker(c: Dict[str, Any]) -> None:
                async with sem:
                    ti = c["ticker"]
                    expiry = c["expiration_date"]
                    s = round(float(c["strike_price"]), 2)
                    cp = c.get("contract_type", "")
                    try:
                        oi_t1, oi_t = await self.daily_oi_pair(client, ti, t1, t)
                        d_oi = oi_t - oi_t1
                        results.append((expiry, s, cp, d_oi))
                    except Exception as err:
                        logger.debug(f"Error processing contract {ti}: {err}")
                        results.append((expiry, s, cp, 0))

            await asyncio.gather(*(worker(c) for c in filtered))
            logger.info(f"Processed OI data for {len(results)} contracts")

            # Build matrix
            mat = np.zeros((len(expiries_sorted), len(strikes_sorted)), dtype=int)

            if combine_cp:
                for e, s, _, doi in results:
                    mat[idx_exp[e], idx_str[s]] += int(doi)

                return {
                    "symbol": symbol.upper(),
                    "t": t,
                    "t_minus_1": t1,
                    "expiries": expiries_sorted,
                    "strikes": strikes_sorted,
                    "matrix": mat.tolist(),
                    "spot": spot,
                }

            # Separate calls / puts
            mat_c = np.zeros_like(mat)
            mat_p = np.zeros_like(mat)
            for e, s, cp, doi in results:
                (mat_c if cp.upper() == "C" else mat_p)[idx_exp[e], idx_str[s]] += int(doi)

            return {
                "symbol": symbol.upper(),
                "t": t,
                "t_minus_1": t1,
                "expiries": expiries_sorted,
                "strikes": strikes_sorted,
                "matrix_calls": mat_c.tolist(),
                "matrix_puts": mat_p.tolist(),
                "spot": spot,
            }

        except Exception:
            logger.error(f"Error in get_oi_change for {symbol}", exc_info=True)
            # Optionally close the client on fatal errors
            try:
                await self.close()
            except Exception:
                pass
            raise
