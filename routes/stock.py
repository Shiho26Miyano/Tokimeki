from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from sklearn.linear_model import LogisticRegression
from transformers import pipeline
import requests
import bs4
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stock_bp = Blueprint('stock', __name__)

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
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if not hist.empty:
                results[name] = {
                    'symbol': symbol,
                    'dates': [d.strftime('%Y-%m-%d') for d in hist.index],
                    'closes': [float(c) for c in hist['Close']]
                }
            else:
                results[name] = {'symbol': symbol, 'error': 'No data'}
        except Exception as e:
            results[name] = {'symbol': symbol, 'error': str(e)}
    return jsonify(results)

@stock_bp.route('/available_tickers')
def available_tickers():
    try:
        default_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
            'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM',
            'SPY', 'QQQ', 'VOO', 'ARKK', 'EEM', 'XLF',
            'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
            'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F', 'ZS=F', 'ZW=F',
            'VX=F', 'BTC=F', 'ETH=F'
        ]
        if yf is None:
            return jsonify(default_tickers)
        validation_period = '5d'
        available = []
        for t in default_tickers:
            try:
                hist = yf.Ticker(t).history(period=validation_period)
                if not hist.empty:
                    available.append(t)
            except Exception:
                continue
        if not available:
            return jsonify(default_tickers)
        return jsonify(available)
    except Exception:
        return jsonify(default_tickers)

@stock_bp.route('/explain_stability')
def explain_stability():
    try:
        if request.method == 'POST':
            data = request.json
            stock = data.get('stock')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
        else:
            stock = request.args.get('stock', 'NVDA')
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
        if not stock:
            return jsonify({'explanation': 'Missing required parameter: stock.'})
        try:
            end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date_str:
                start = datetime.strptime(start_date_str, '%Y-%m-%d')
            else:
                year = datetime.now().year
                start = datetime.strptime(f"{year}-01-01", '%Y-%m-%d')
            max_range = timedelta(days=1095)
            if end - start > max_range:
                start = end - max_range
        except ValueError as e:
            return jsonify({'explanation': f"Invalid date format: {str(e)}"})
        ticker = yf.Ticker(stock)
        hist = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if hist.empty:
            return jsonify({'explanation': f"No data available for {stock} in the selected date range."})
        closes = hist['Close'].tolist()
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
        daily_changes = []
        for i in range(1, len(closes)):
            pct_change = ((closes[i] - closes[i-1]) / closes[i-1]) * 100
            daily_changes.append({
                'date': dates[i],
                'change': pct_change
            })
        top_events = sorted(daily_changes, key=lambda x: abs(x['change']), reverse=True)[:3]
        date_range_str = f"from {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
        explanation = f"Biggest price movement events for {stock} {date_range_str}:\n\n"
        if not top_events:
            explanation += "No significant price movements detected in this period."
        else:
            for event in top_events:
                direction = 'up' if event['change'] > 0 else 'down'
                explanation += f"• {event['date']}: {direction} {abs(event['change']):.2f}%\n"
        return jsonify({'explanation': explanation})
    except Exception as e:
        return jsonify({'explanation': f"Error analyzing {stock}: {str(e)}"})

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
    event_count = [0 for _ in dates]
    event_titles = [[] for _ in dates]
    return jsonify({
        'dates': dates,
        'volatility': rolling_vol,
        'event_count': event_count,
        'event_titles': event_titles,
        'min_vol': min_vol,
        'min_vol_date': min_vol_date
    })

# Add any additional helpers or mock data generators as needed

# ... (other stock endpoints: maxchange, stable, available_tickers, available_for_prediction, etc.) ... 