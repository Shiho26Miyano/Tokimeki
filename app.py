from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import List
from math import comb
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from transformers import pipeline
from threading import Thread
import time

try:
    import yfinance as yf
except ImportError:
    yf = None

app = Flask(__name__)
CORS(app)

# Use a smaller, faster model for explanation
explanation_pipe = pipeline('text-generation', model='sshleifer/tiny-gpt2')

# In-memory cache for explanations
explanation_cache = {}

def generate_explanation_async(key, prompt):
    # Generate and cache the explanation in the background
    result = explanation_pipe(prompt, max_length=20, num_return_sequences=1)
    explanation = result[0]['generated_text'].split('Explanation:')[-1].strip()
    if '.' in explanation:
        explanation = explanation.split('.', 1)[0].strip() + '.'
    explanation = explanation[:200]
    explanation_cache[key] = explanation

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
        'Alibaba': 'BABA',
        'S&P 500 ETF': 'SPY',
        'Nasdaq 100 ETF': 'QQQ',
        'S&P 500 ETF (VOO)': 'VOO',
        'Good Times Restaurants': 'GTIM',
        'ARK Innovation ETF': 'ARKK',
        'Emerging Markets ETF': 'EEM',
        'Financial Select Sector SPDR': 'XLF'
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

@app.route('/leetcode/stock', methods=['POST'])
def leetcode_stock():
    data = request.json
    problem = data.get('problem')
    prices = data.get('prices', [])
    k = data.get('k', 2)
    fee = data.get('fee', 0)
    result = None
    code = ''
    cpp_code = ''
    time_complexity = ''
    space_complexity = ''
    explanation = ''
    if problem == '121':
        # LeetCode 121: Best Time to Buy and Sell Stock (one transaction)
        min_price = float('inf')
        max_profit = 0
        for price in prices:
            if price < min_price:
                min_price = price
            elif price - min_price > max_profit:
                max_profit = price - min_price
        result = max_profit
        code = '''def maxProfit(prices):
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > max_profit:
            max_profit = price - min_price
    return max_profit'''
        cpp_code = '''int maxProfit(vector<int>& prices) {
    int min_price = INT_MAX, max_profit = 0;
    for (int price : prices) {
        min_price = min(min_price, price);
        max_profit = max(max_profit, price - min_price);
    }
    return max_profit;
}'''
        time_complexity = 'O(n)'
        space_complexity = 'O(1)'
        explanation = 'Track the minimum price and the maximum profit as you iterate.'
    elif problem == '122':
        # LeetCode 122: Best Time to Buy and Sell Stock II (unlimited transactions)
        profit = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                profit += prices[i] - prices[i-1]
        result = profit
        code = '''def maxProfit(prices):
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            profit += prices[i] - prices[i-1]
    return profit'''
        cpp_code = '''int maxProfit(vector<int>& prices) {
    int profit = 0;
    for (int i = 1; i < prices.size(); ++i) {
        if (prices[i] > prices[i-1])
            profit += prices[i] - prices[i-1];
    }
    return profit;
}'''
        time_complexity = 'O(n)'
        space_complexity = 'O(1)'
        explanation = 'Sum all positive price differences.'
    elif problem == '123':
        # LeetCode 123: Best Time to Buy and Sell Stock III (at most two transactions)
        buy1 = buy2 = float('inf')
        profit1 = profit2 = 0
        for price in prices:
            buy1 = min(buy1, price)
            profit1 = max(profit1, price - buy1)
            buy2 = min(buy2, price - profit1)
            profit2 = max(profit2, price - buy2)
        result = profit2
        code = '''def maxProfit(prices):
    buy1 = buy2 = float('inf')
    profit1 = profit2 = 0
    for price in prices:
        buy1 = min(buy1, price)
        profit1 = max(profit1, price - buy1)
        buy2 = min(buy2, price - profit1)
        profit2 = max(profit2, price - buy2)
    return profit2'''
        cpp_code = '''int maxProfit(vector<int>& prices) {
    int buy1 = INT_MAX, buy2 = INT_MAX;
    int profit1 = 0, profit2 = 0;
    for (int price : prices) {
        buy1 = min(buy1, price);
        profit1 = max(profit1, price - buy1);
        buy2 = min(buy2, price - profit1);
        profit2 = max(profit2, price - buy2);
    }
    return profit2;
}'''
        time_complexity = 'O(n)'
        space_complexity = 'O(1)'
        explanation = 'Track two buys and two profits for two transactions.'
    elif problem == '188':
        # LeetCode 188: Best Time to Buy and Sell Stock IV (at most k transactions)
        if not prices or k == 0:
            result = 0
        elif k >= len(prices) // 2:
            profit = 0
            for i in range(1, len(prices)):
                if prices[i] > prices[i-1]:
                    profit += prices[i] - prices[i-1]
            result = profit
        else:
            dp = [[0] * len(prices) for _ in range(k+1)]
            for t in range(1, k+1):
                max_diff = -prices[0]
                for d in range(1, len(prices)):
                    dp[t][d] = max(dp[t][d-1], prices[d] + max_diff)
                    max_diff = max(max_diff, dp[t-1][d] - prices[d])
            result = dp[k][-1]
        code = '''def maxProfit(k, prices):
    if not prices or k == 0:
        return 0
    if k >= len(prices) // 2:
        profit = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                profit += prices[i] - prices[i-1]
        return profit
    dp = [[0] * len(prices) for _ in range(k+1)]
    for t in range(1, k+1):
        max_diff = -prices[0]
        for d in range(1, len(prices)):
            dp[t][d] = max(dp[t][d-1], prices[d] + max_diff)
            max_diff = max(max_diff, dp[t-1][d] - prices[d])
    return dp[k][-1]'''
        cpp_code = '''int maxProfit(int k, vector<int>& prices) {
    int n = prices.size();
    if (n == 0 || k == 0) return 0;
    if (k >= n / 2) {
        int profit = 0;
        for (int i = 1; i < n; ++i)
            if (prices[i] > prices[i-1])
                profit += prices[i] - prices[i-1];
        return profit;
    }
    vector<vector<int>> dp(k+1, vector<int>(n, 0));
    for (int t = 1; t <= k; ++t) {
        int maxDiff = -prices[0];
        for (int d = 1; d < n; ++d) {
            dp[t][d] = max(dp[t][d-1], prices[d] + maxDiff);
            maxDiff = max(maxDiff, dp[t-1][d] - prices[d]);
        }
    }
    return dp[k][n-1];
}'''
        time_complexity = 'O(kn)'
        space_complexity = 'O(kn)'
        explanation = 'DP for at most k transactions.'
    elif problem == '309':
        # LeetCode 309: Best Time to Buy and Sell Stock with Cooldown
        if not prices:
            result = 0
        else:
            n = len(prices)
            hold = [0]*n
            sold = [0]*n
            rest = [0]*n
            hold[0] = -prices[0]
            for i in range(1, n):
                hold[i] = max(hold[i-1], rest[i-1] - prices[i])
                sold[i] = hold[i-1] + prices[i]
                rest[i] = max(rest[i-1], sold[i-1])
            result = max(sold[-1], rest[-1])
        code = '''def maxProfit(prices):
    if not prices:
        return 0
    n = len(prices)
    hold = [0]*n
    sold = [0]*n
    rest = [0]*n
    hold[0] = -prices[0]
    for i in range(1, n):
        hold[i] = max(hold[i-1], rest[i-1] - prices[i])
        sold[i] = hold[i-1] + prices[i]
        rest[i] = max(rest[i-1], sold[i-1])
    return max(sold[-1], rest[-1])'''
        cpp_code = '''int maxProfit(vector<int>& prices) {
    int n = prices.size();
    if (n == 0) return 0;
    vector<int> hold(n), sold(n), rest(n);
    hold[0] = -prices[0];
    for (int i = 1; i < n; ++i) {
        hold[i] = max(hold[i-1], rest[i-1] - prices[i]);
        sold[i] = hold[i-1] + prices[i];
        rest[i] = max(rest[i-1], sold[i-1]);
    }
    return max(sold[n-1], rest[n-1]);
}'''
        time_complexity = 'O(n)'
        space_complexity = 'O(n)'
        explanation = 'DP with three states: hold, sold, rest.'
    elif problem == '714':
        # LeetCode 714: Best Time to Buy and Sell Stock with Transaction Fee
        if not prices:
            result = 0
        else:
            n = len(prices)
            cash, hold = 0, -prices[0]
            for i in range(1, n):
                cash = max(cash, hold + prices[i] - fee)
                hold = max(hold, cash - prices[i])
            result = cash
        code = '''def maxProfit(prices, fee):
    if not prices:
        return 0
    cash, hold = 0, -prices[0]
    for price in prices[1:]:
        cash = max(cash, hold + price - fee)
        hold = max(hold, cash - price)
    return cash'''
        cpp_code = '''int maxProfit(vector<int>& prices, int fee) {
    int n = prices.size();
    if (n == 0) return 0;
    int cash = 0, hold = -prices[0];
    for (int i = 1; i < n; ++i) {
        cash = max(cash, hold + prices[i] - fee);
        hold = max(hold, cash - prices[i]);
    }
    return cash;
}'''
        time_complexity = 'O(n)'
        space_complexity = 'O(1)'
        explanation = 'DP with cash and hold states, subtracting fee on sell.'
    else:
        return jsonify({'error': 'Unknown problem'}), 400
    return jsonify({
        'result': result,
        'code': code,
        'cpp_code': cpp_code,
        'time_complexity': time_complexity,
        'space_complexity': space_complexity,
        'explanation': explanation
    })

# --- Stability window helper functions ---
def lowest_std_window(prices, window_size):
    min_std = float('inf')
    best_i = None
    for i in range(len(prices) - window_size + 1):
        window = prices[i:i+window_size]
        std = np.std(window)
        if std < min_std:
            min_std = std
            best_i = i
    if best_i is None:
        return None, None
    return best_i, min_std

def highest_std_window(prices, window_size):
    max_std = float('-inf')
    best_i = None
    for i in range(len(prices) - window_size + 1):
        window = prices[i:i+window_size]
        std = np.std(window)
        if std > max_std:
            max_std = std
            best_i = i
    if best_i is None:
        return None, None
    return best_i, max_std

def lowest_meanabs_window(prices, window_size):
    min_meanabs = float('inf')
    best_i = None
    for i in range(len(prices) - window_size + 1):
        window = prices[i:i+window_size]
        changes = [abs(window[j+1] - window[j]) for j in range(len(window)-1)]
        meanabs = np.mean(changes)
        if meanabs < min_meanabs:
            min_meanabs = meanabs
            best_i = i
    if best_i is None:
        return None, None
    return best_i, min_meanabs

def highest_meanabs_window(prices, window_size):
    max_meanabs = float('-inf')
    best_i = None
    for i in range(len(prices) - window_size + 1):
        window = prices[i:i+window_size]
        changes = [abs(window[j+1] - window[j]) for j in range(len(window)-1)]
        meanabs = np.mean(changes)
        if meanabs > max_meanabs:
            max_meanabs = meanabs
            best_i = i
    if best_i is None:
        return None, None
    return best_i, max_meanabs

@app.route('/stocks/stable', methods=['GET'])
def stocks_stable():
    # Default tickers
    default_tickers = {
        'Apple': 'AAPL',
        'Microsoft': 'MSFT',
        'Google': 'GOOGL',
        'Amazon': 'AMZN',
        'Meta': 'META',
        'Nvidia': 'NVDA',
        'Tesla': 'TSLA',
        'Netflix': 'NFLX',
        'AMD': 'AMD',
        'Intel': 'INTC',
        'Berkshire Hathaway': 'BRK-B',
        'Johnson & Johnson': 'JNJ',
        'Visa': 'V',
        'JPMorgan Chase': 'JPM',
        'Walmart': 'WMT',
        'Procter & Gamble': 'PG',
        'Coca-Cola': 'KO',
        'Exxon Mobil': 'XOM',
        'SPY': 'SPY',
        'QQQ': 'QQQ',
        'VOO': 'VOO',
        'ARKK': 'ARKK',
        'EEM': 'EEM',
        'XLF': 'XLF'
    }
    metric = request.args.get('metric', 'std')
    order = request.args.get('order', 'asc')
    symbol_filter = request.args.get('symbol')
    window_size = int(request.args.get('window', 20))
    days_param = request.args.get('days')
    days = int(days_param) if days_param and days_param.isdigit() else 1095
    results = []
    end = datetime.now()
    start = end - timedelta(days=days)
    for name, symbol in default_tickers.items():
        if symbol_filter and symbol != symbol_filter:
            continue
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            closes = [float(c) for c in hist['Close']]
            dates = [d.strftime('%Y-%m-%d') for d in hist.index]
            n = len(closes)
            if n < window_size:
                results.append({'name': name, 'symbol': symbol, 'error': 'Not enough data for this window size.'})
                continue
            # Use the appropriate function for metric/order
            if metric == 'std' and order == 'asc':
                best_i, best_score = lowest_std_window(closes, window_size)
            elif metric == 'std' and order == 'desc':
                best_i, best_score = highest_std_window(closes, window_size)
            elif metric == 'meanabs' and order == 'asc':
                best_i, best_score = lowest_meanabs_window(closes, window_size)
            elif metric == 'meanabs' and order == 'desc':
                best_i, best_score = highest_meanabs_window(closes, window_size)
            else:
                results.append({'name': name, 'symbol': symbol, 'error': 'Invalid metric or order.'})
                continue
            if best_i is None:
                results.append({'name': name, 'symbol': symbol, 'error': 'No valid window found for this metric/order.'})
                continue
            best_j = best_i + window_size - 1
            results.append({
                'name': name,
                'symbol': symbol,
                'start_date': dates[best_i],
                'end_date': dates[best_j],
                'stability_score': float(best_score),
                'window_prices': closes[best_i:best_j+1],
                'metric': metric,
                'order': order,
                'window_len': window_size,
                'window_start_idx': best_i,
                'window_end_idx': best_j,
                'all_closes': closes,
                'all_dates': dates
            })
        except Exception as e:
            results.append({'name': name, 'symbol': symbol, 'error': str(e)})
    results = sorted(results, key=lambda x: x.get('stability_score', float('inf')), reverse=(order=='desc'))
    if symbol_filter:
        return jsonify(results[:1])
    return jsonify(results[:5])

@app.route('/available_tickers')
def available_tickers():
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
        'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM',
        'SPY', 'QQQ', 'VOO', 'ARKK', 'EEM', 'XLF',
        'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
        'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F', 'ZS=F', 'ZW=F',
        'VX=F', 'BTC=F', 'ETH=F'
    ]
    available = []
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period='1095d')  # 3 years
            if not hist.empty and len(hist) > 200:
                available.append(t)
        except Exception:
            continue
    return jsonify(available)

@app.route('/explain_stability', methods=['POST'])
def explain_stability():
    data = request.json
    stock = data.get('stock')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    explanation = f"A major event or news between {start_date} and {end_date} may have impacted the stability of {stock}."
    return jsonify({'explanation': explanation})

@app.route('/stocks/available_for_prediction', methods=['GET'])
def available_for_prediction():
    default_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
        'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM',
        'SPY', 'QQQ', 'VOO', 'ARKK', 'EEM', 'XLF',
        'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
        'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F', 'ZS=F', 'ZW=F',
        'VX=F', 'BTC=F', 'ETH=F'
    ]
    days_param = request.args.get('days')
    days = int(days_param) if days_param and days_param.isdigit() else 1095
    end = datetime.now()
    start = end - timedelta(days=days)
    available = []
    for t in default_tickers:
        try:
            hist = yf.Ticker(t).history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if not hist.empty and len(hist) > 0:
                available.append(t)
        except Exception:
            continue
    return jsonify(available)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 