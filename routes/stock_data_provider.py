from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
import requests
import bs4
import logging
from bs4 import BeautifulSoup
import time
from requests.exceptions import RequestException
import json
import os

# Optional imports - app will work without these
try:
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stock_bp = Blueprint('stock', __name__)

# Cache configuration
CACHE_DIR = 'cache'
CACHE_DURATION = 3600  # 1 hour in seconds

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(symbol, start_date, end_date):
    """Get cache file path for a symbol and date range"""
    ensure_cache_dir()
    cache_key = f"{symbol}_{start_date}_{end_date}.json"
    return os.path.join(CACHE_DIR, cache_key)

def get_cached_data(symbol, start_date, end_date):
    """Get cached data if available and not expired"""
    cache_path = get_cache_path(symbol, start_date, end_date)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                cache_time = cache_data.get('timestamp', 0)
                if time.time() - cache_time < CACHE_DURATION:
                    return cache_data.get('data')
        except Exception as e:
            logger.warning(f"Error reading cache for {symbol}: {str(e)}")
    return None

def save_to_cache(symbol, start_date, end_date, data):
    """Save data to cache"""
    cache_path = get_cache_path(symbol, start_date, end_date)
    try:
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        logger.warning(f"Error saving cache for {symbol}: {str(e)}")

def fetch_ticker_with_retry(symbol, max_retries=3, delay=2):
    """Fetch ticker data with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1} to fetch data for {symbol}")
            ticker = yf.Ticker(symbol)
            # Add delay between attempts
            if attempt > 0:
                time.sleep(delay * (attempt + 1))  # Exponential backoff
            return ticker
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (attempt + 1))  # Exponential backoff

def get_fallback_data(symbol, start_date, end_date):
    """Get fallback sample data when yfinance fails"""
    try:
        # Generate sample data for demonstration
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days
        
        # Generate sample dates and prices
        dates = []
        closes = []
        base_price = 100.0  # Base price for sample data
        
        for i in range(days + 1):
            current_date = start + timedelta(days=i)
            dates.append(current_date.strftime('%Y-%m-%d'))
            # Generate realistic price movement
            price_change = np.random.normal(0, 0.02)  # 2% daily volatility
            base_price *= (1 + price_change)
            closes.append(max(base_price, 1.0))  # Ensure price doesn't go negative
        
        return {
            'symbol': symbol,
            'dates': dates,
            'closes': [round(price, 2) for price in closes],
            'note': 'Sample data (yfinance unavailable)'
        }
    except Exception as e:
        logger.error(f"Error generating fallback data: {str(e)}")
        return None

@stock_bp.route('/stocks/history', methods=['GET'])
def stocks_history():
    default_tickers = {
        'Google': 'GOOGL',
        'Nvidia': 'NVDA',
        'Apple': 'AAPL',
        'Microsoft': 'MSFT',
        'Amazon': 'AMZN',
        'Meta': 'META',
        'Tesla': 'TSLA',
        'Netflix': 'NFLX',
        'AMD': 'AMD',
        'Intel': 'INTC',
        'Alibaba': 'BABA',
        'S&P 500 ETF': 'SPY',
        'Nasdaq 100 ETF': 'QQQ',
        'S&P 500 ETF (VOO)': 'VOO',
        'Good Times Restaurants': 'GTIM',
        'ARK Innovation ETF': 'ARKK',
        'Emerging Markets ETF': 'EEM',
        'Financial Select Sector SPDR': 'XLF'
    }
    symbols_param = request.args.get('symbols')
    if symbols_param:
        symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
        tickers = {k: v for k, v in default_tickers.items() if v in symbols}
        for s in symbols:
            if s not in tickers.values():
                tickers[s] = s
    else:
        tickers = default_tickers
    end_date_str = request.args.get('end_date')
    start_date_str = request.args.get('start_date')
    try:
        end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date_str:
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            days_param = request.args.get('days')
            days = int(days_param) if days_param and days_param.isdigit() else 31
            start = end - timedelta(days=days)
        max_range = timedelta(days=1095)
        if end - start > max_range:
            start = end - max_range
    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
    results = {}
    for name, symbol in tickers.items():
        try:
            # Try to get from cache first
            cached_data = get_cached_data(symbol, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
            if cached_data:
                results[name] = cached_data
                continue

            # If not in cache, fetch from yfinance
            ticker = fetch_ticker_with_retry(symbol)
            hist = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if not hist.empty:
                data = {
                    'symbol': symbol,
                    'dates': [d.strftime('%Y-%m-%d') for d in hist.index],
                    'closes': [float(c) for c in hist['Close']]
                }
                results[name] = data
                # Save to cache
                save_to_cache(symbol, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), data)
            else:
                results[name] = {'symbol': symbol, 'error': 'No data'}
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            # Try to get from cache even if expired
            cached_data = get_cached_data(symbol, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
            if cached_data:
                results[name] = cached_data
            else:
                # Use fallback data as last resort
                fallback_data = get_fallback_data(symbol, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
                if fallback_data:
                    results[name] = fallback_data
                else:
                    results[name] = {'symbol': symbol, 'error': str(e)}
    return jsonify(results)

@stock_bp.route('/available_companies')
def available_companies():
    companies = {
        'Google': 'GOOGL', 'Nvidia': 'NVDA', 'Apple': 'AAPL', 'Microsoft': 'MSFT',
        'Amazon': 'AMZN', 'Meta': 'META', 'Tesla': 'TSLA', 'Netflix': 'NFLX',
        'AMD': 'AMD', 'Intel': 'INTC', 'Alibaba': 'BABA', 'S&P 500 ETF': 'SPY',
        'Nasdaq 100 ETF': 'QQQ', 'S&P 500 ETF (VOO)': 'VOO',
        'Good Times Restaurants': 'GTIM', 'ARK Innovation ETF': 'ARKK',
        'Emerging Markets ETF': 'EEM', 'Financial Select Sector SPDR': 'XLF'
    }
    # Convert to list of dicts
    company_list = [{"name": name, "symbol": symbol} for name, symbol in companies.items()]
    return jsonify(company_list)

@stock_bp.route('/available_tickers')
def available_tickers():
    try:
        default_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
            'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM',
            'SPY', 'QQQ', 'VOO', 'ARKK', 'EEM', 'XLF',
            'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
            'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F', 'ZS=F', 'ZW=F',
            '^VIX', 'BTC=F', 'ETH=F'
        ]
        
        # If yfinance is not available, return default list
        if yf is None:
            logger.warning("yfinance not available, returning default tickers")
            return jsonify(default_tickers)
        
        validation_period = '5d'
        available = []
        failed_count = 0
        
        for t in default_tickers:
            try:
                ticker = fetch_ticker_with_retry(t)
                hist = ticker.history(period=validation_period)
                if not hist.empty:
                    available.append(t)
                else:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"Failed to validate ticker {t}: {str(e)}")
                failed_count += 1
                continue
        
        # If too many tickers failed validation, return default list
        if failed_count > len(default_tickers) * 0.5:  # If more than 50% failed
            logger.warning(f"Too many tickers failed validation ({failed_count}/{len(default_tickers)}), returning default list")
            return jsonify(default_tickers)
        
        # If no tickers validated, return default list
        if not available:
            logger.warning("No tickers validated, returning default list")
            return jsonify(default_tickers)
        
        return jsonify(available)
    except Exception as e:
        logger.error(f"Error in available_tickers: {str(e)}")
        return jsonify(default_tickers)

@stock_bp.route('/volatility_event_correlation', methods=['GET'])
def volatility_event_correlation():
    symbol = request.args.get('symbol', 'AAPL')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    window = int(request.args.get('window', 10))
    years = int(request.args.get('years', 2))
    if not start_date or not end_date:
        end = datetime.now()
        start = end - timedelta(days=years*365)
        start_date = start.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        closes = hist['Close'].tolist()
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
        if len(closes) < window:
            return jsonify({'error': f'Not enough data for rolling volatility (need at least {window} days)'}), 400
        returns = np.diff(closes) / closes[:-1]
        # Efficient rolling std calculation using numpy
        returns_np = np.array(returns)
        if hasattr(np.lib.stride_tricks, 'sliding_window_view'):
            windows = np.lib.stride_tricks.sliding_window_view(returns_np, window_shape=window)
            rolling_vol_np = np.std(windows, axis=1)
            rolling_vol = [None] * (window-1) + rolling_vol_np.tolist()
        else:
            rolling_vol = [None] * (window-1) + [float(np.std(returns_np[i-window+1:i+1])) for i in range(window-1, len(returns_np))]
        # Ignore the first 10% of valid rolling volatility data when searching for the minimum
        valid_start = int(len(rolling_vol) * 0.1)
        valid_vols = np.array(rolling_vol[valid_start:])
        valid_dates = dates[valid_start:]
        min_vol = None
        min_vol_date = None
        if np.any(valid_vols != None):
            valid_mask = np.array([v is not None for v in valid_vols])
            if np.any(valid_mask):
                min_idx = np.argmin(np.where(valid_mask, valid_vols, np.inf))
                min_vol = float(valid_vols[min_idx])
                min_vol_date = valid_dates[min_idx]
    except Exception as e:
        return jsonify({'error': f'Error fetching stock data: {str(e)}'}), 500
    # Remove event/news/sentiment fetching and alignment
    event_titles = [[] for _ in dates]
    return jsonify({
        'dates': dates,
        'volatility': rolling_vol,
        'event_titles': event_titles,
        'min_vol': min_vol,
        'min_vol_date': min_vol_date
    })

# Add any additional helpers or mock data generators as needed

# ... (other stock endpoints: maxchange, stable, available_tickers, available_for_prediction, etc.) ... 