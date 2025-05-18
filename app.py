from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import List
from math import comb
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import logging
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    yf = None

app = Flask(__name__)
CORS(app)

def name_to_numbers(name):
    name = name.lower()
    return [ord(c) - ord('a') for c in name if 'a' <= c <= 'z']

def longest_consecutive(nums: List[int]) -> int:
    if not nums:
        return 0
    nums_set = set(nums)
    longest = 0
    for num in nums_set:
        if num - 1 not in nums_set:
            cur_num = num
            cur_len = 1
            while cur_num + 1 in nums_set:
                cur_num += 1
                cur_len += 1
            longest = max(longest, cur_len)
    return longest

def lcs(nums1: List[int], nums2: List[int]) -> int:
    m, n = len(nums1), len(nums2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if nums1[i] == nums2[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
    return dp[m][n]

def longest_increasing_subsequence(nums):
    if not nums:
        return []
    n = len(nums)
    dp = [1] * n
    prev = [-1] * n
    max_len = 1
    max_idx = 0
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
        if dp[i] > max_len:
            max_len = dp[i]
            max_idx = i
    # reconstruct LIS
    lis = []
    idx = max_idx
    while idx != -1:
        lis.append(nums[idx])
        idx = prev[idx]
    return lis[::-1]

analyzer = SentimentIntensityAnalyzer()

@app.route('/match', methods=['POST'])
def match():
    data = request.json
    name1 = data.get('name1', '')
    name2 = data.get('name2', '')
    algorithm = data.get('algorithm', 'sum')
    nums1 = name_to_numbers(name1)
    nums2 = name_to_numbers(name2)
    if algorithm == 'longest':
        combined = nums1 + nums2
        if not combined:
            percentage = 0
        else:
            longest = longest_consecutive(combined)
            unique_count = len(set(combined))
            if unique_count == 0:
                percentage = 0
            else:
                percentage = round(longest / unique_count * 100, 2)
    elif algorithm == 'lcs':
        if not nums1 or not nums2:
            percentage = 0
        else:
            lcs_len = lcs(nums1, nums2)
            max_len = max(len(nums1), len(nums2))
            percentage = round(lcs_len / max_len * 100, 2) if max_len > 0 else 0
    else:
        sum1 = sum(nums1)
        sum2 = sum(nums2)
        if max(sum1, sum2) == 0:
            percentage = 0
        else:
            percentage = round(min(sum1, sum2) / max(sum1, sum2) * 100, 2)
    return jsonify({'percentage': percentage})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    sentence = data.get('sentence', '')
    scores = analyzer.polarity_scores(sentence)
    compound = scores['compound']
    if compound >= 0.05:
        sentiment = 'positive'
    elif compound <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    return jsonify({'sentiment': sentiment, 'score': compound})

@app.route('/lis', methods=['POST'])
def lis_api():
    data = request.json
    nums = data.get('nums', [])
    lis = longest_increasing_subsequence(nums)
    return jsonify({'lis': lis, 'length': len(lis)})

@app.route('/stock/googl', methods=['GET'])
def get_googl_stock():
    url = 'https://query1.finance.yahoo.com/v7/finance/quote?symbols=GOOGL'
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        price = data['quoteResponse']['result'][0]['regularMarketPrice']
        time = data['quoteResponse']['result'][0]['regularMarketTime']
        return jsonify({'price': price, 'time': time})
    except Exception as e:
        logging.error(f"Yahoo direct fetch failed: {e}")
        # Try yfinance as a fallback
        if yf is not None:
            try:
                ticker = yf.Ticker('GOOGL')
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    time = int(hist.index[-1].timestamp())
                    return jsonify({'price': float(price), 'time': time})
            except Exception as e2:
                logging.error(f"yfinance fetch failed: {e2}")
        return jsonify({'error': f'Failed to fetch stock price. {str(e)}'}), 500

@app.route('/stocks/history', methods=['GET'])
def stocks_history():
    # Default tickers
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
        'Alibaba': 'BABA'
    }
    # Parse symbols from query param
    symbols_param = request.args.get('symbols')
    if symbols_param:
        symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
        tickers = {k: v for k, v in default_tickers.items() if v in symbols}
        # Add any custom tickers not in default list
        for s in symbols:
            if s not in tickers.values():
                tickers[s] = s
    else:
        tickers = default_tickers
    results = {}
    end = datetime.now()
    start = end - timedelta(days=31)
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

@app.route('/stocks/maxchange', methods=['GET'])
def stocks_maxchange():
    # Default tickers
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
        'Alibaba': 'BABA'
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
    results = []
    end = datetime.now()
    start = end - timedelta(days=31)
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            closes = [float(c) for c in hist['Close']]
            dates = [d.strftime('%Y-%m-%d') for d in hist.index]
            if len(closes) > 1:
                max_sum, (i, j) = max_abs_sum_change(closes)
                results.append({
                    'name': name,
                    'symbol': symbol,
                    'max_abs_sum': max_sum,
                    'start_date': dates[i],
                    'end_date': dates[j],
                    'start_price': closes[i],
                    'end_price': closes[j],
                    'dates': dates,
                    'closes': closes
                })
        except Exception as e:
            results.append({'name': name, 'symbol': symbol, 'error': str(e)})
    # Sort by max_abs_sum descending
    results = sorted(results, key=lambda x: x.get('max_abs_sum', 0), reverse=True)
    return jsonify(results)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

def max_abs_sum_change(prices):
    # Find the time range with the largest absolute sum of price changes
    n = len(prices)
    max_sum = 0
    best_range = (0, 0)
    for i in range(n):
        for j in range(i+1, n):
            abs_sum = sum(abs(prices[k+1] - prices[k]) for k in range(i, j))
            if abs_sum > max_sum:
                max_sum = abs_sum
                best_range = (i, j)
    return max_sum, best_range

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 