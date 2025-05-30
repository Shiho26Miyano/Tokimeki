from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import List
from math import comb
import os
import requests
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import time

try:
    import yfinance as yf
except ImportError:
    yf = None

# Add sqlite for mood tracking
import sqlite3
import json

app = Flask(__name__)
# Configure CORS to allow requests from any origin
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

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
    
    # Parse date ranges
    end_date_str = request.args.get('end_date')
    start_date_str = request.args.get('start_date')
    
    try:
        # Default end date is today
        end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # If start_date is provided, use it; otherwise use days or default to 31 days
        if start_date_str:
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            days_param = request.args.get('days')
            days = int(days_param) if days_param and days_param.isdigit() else 31
            start = end - timedelta(days=days)
        
        # Validate the date range doesn't exceed 3 years (1095 days)
        max_range = timedelta(days=1095)  # 3 years
        if end - start > max_range:
            start = end - max_range
    except ValueError as e:
        # Handle invalid date format
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
    
    # Parse date ranges
    end_date_str = request.args.get('end_date')
    start_date_str = request.args.get('start_date')
    
    try:
        # Default end date is today
        end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # If start_date is provided, use it; otherwise use days or default to 31 days
        if start_date_str:
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            days_param = request.args.get('days')
            days = int(days_param) if days_param and days_param.isdigit() else 31
            start = end - timedelta(days=days)
        
        # Validate the date range doesn't exceed 3 years (1095 days)
        max_range = timedelta(days=1095)  # 3 years
        if end - start > max_range:
            start = end - max_range
    except ValueError as e:
        # Handle invalid date format
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
    
    results = []
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
    try:
        data = request.json
        problem = data.get('problem', '')
        prices = data.get('prices', [])
        k = data.get('k', 2)
        fee = data.get('fee', 0)
        
        print(f"DEBUG: leetcode_stock accessed, problem={problem}, prices={prices[:5]}...")
        
        if problem == '121':  # Best Time to Buy and Sell Stock (One transaction)
            result = max_profit_one_transaction(prices)
            code = """def maxProfit(prices):
    max_profit = 0
    min_price = float('inf')
    
    for price in prices:
        # Update minimum price seen so far
        min_price = min(min_price, price)
        # Calculate profit if we sell at current price
        current_profit = price - min_price
        # Update max profit if current profit is better
        max_profit = max(max_profit, current_profit)
    
    return max_profit"""
            cpp_code = """int maxProfit(vector<int>& prices) {
    int maxProfit = 0;
    int minPrice = INT_MAX;
    
    for (int price : prices) {
        // Update minimum price seen so far
        minPrice = min(minPrice, price);
        // Calculate profit if we sell at current price
        int currentProfit = price - minPrice;
        // Update max profit if current profit is better
        maxProfit = max(maxProfit, currentProfit);
    }
    
    return maxProfit;
}"""
            time_complexity = 'O(n)'
            space_complexity = 'O(1)'
            explanation = 'Track min price and max profit in one pass through prices array'
        
        elif problem == '122':  # Best Time to Buy and Sell Stock II (Unlimited transactions)
            result = max_profit_unlimited_transactions(prices)
            code = """def maxProfit(prices):
    max_profit = 0
    
    # For each pair of consecutive days
    for i in range(1, len(prices)):
        # If price increases, we buy yesterday and sell today
        if prices[i] > prices[i-1]:
            max_profit += prices[i] - prices[i-1]
    
    return max_profit"""
            cpp_code = """int maxProfit(vector<int>& prices) {
    int maxProfit = 0;
    
    // For each pair of consecutive days
    for (int i = 1; i < prices.size(); i++) {
        // If price increases, we buy yesterday and sell today
        if (prices[i] > prices[i-1]) {
            maxProfit += prices[i] - prices[i-1];
        }
    }
    
    return maxProfit;
}"""
            time_complexity = 'O(n)'
            space_complexity = 'O(1)'
            explanation = 'Capitalize on every price increase between consecutive days'
            
        elif problem == '123':  # Best Time to Buy and Sell Stock III (At most two transactions)
            result = max_profit_two_transactions(prices)
            code = """def maxProfit(prices):
    n = len(prices)
    if n <= 1:
        return 0
    
    # Forward pass: dp[i] represents max profit with one transaction up to day i
    # dp[0] = 0 (no profit on first day)
    dp_one_transaction = [0] * n
    min_price = prices[0]
    
    for i in range(1, n):
        min_price = min(min_price, prices[i])
        dp_one_transaction[i] = max(dp_one_transaction[i-1], prices[i] - min_price)
    
    # Backward pass: calculate max profit with two transactions
    max_price = prices[n-1]
    max_profit = dp_one_transaction[n-1]  # At least as good as one transaction
    
    for i in range(n-2, 0, -1):
        max_price = max(max_price, prices[i])
        # Max profit = best of (one transaction) or (one transaction until day i + another transaction after day i)
        max_profit = max(max_profit, dp_one_transaction[i-1] + max_price - prices[i])
    
    return max_profit"""
            cpp_code = """int maxProfit(vector<int>& prices) {
    int n = prices.size();
    if (n <= 1) return 0;
    
    // Forward pass: dp[i] represents max profit with one transaction up to day i
    vector<int> dpOneTransaction(n, 0);
    int minPrice = prices[0];
    
    for (int i = 1; i < n; i++) {
        minPrice = min(minPrice, prices[i]);
        dpOneTransaction[i] = max(dpOneTransaction[i-1], prices[i] - minPrice);
    }
    
    // Backward pass: calculate max profit with two transactions
    int maxPrice = prices[n-1];
    int maxProfit = dpOneTransaction[n-1];  // At least as good as one transaction
    
    for (int i = n-2; i > 0; i--) {
        maxPrice = max(maxPrice, prices[i]);
        // Max profit = best of (one transaction) or (one transaction until day i + another transaction after day i)
        maxProfit = max(maxProfit, dpOneTransaction[i-1] + maxPrice - prices[i]);
    }
    
    return maxProfit;
}"""
            time_complexity = 'O(n)'
            space_complexity = 'O(n)'
            explanation = 'Use dynamic programming with two passes: forward pass to find best single transaction until each day, backward pass to find second best transaction'
            
        elif problem == '188':  # Best Time to Buy and Sell Stock IV (At most k transactions)
            result = max_profit_k_transactions(prices, k)
            code = """def maxProfit(prices, k):
    n = len(prices)
    if n <= 1 or k <= 0:
        return 0
    
    # If k is large enough, it's equivalent to unlimited transactions
    if k >= n // 2:
        max_profit = 0
        for i in range(1, n):
            if prices[i] > prices[i-1]:
                max_profit += prices[i] - prices[i-1]
        return max_profit
    
    # dp[i][j] = max profit with i transactions on day j
    dp = [[0 for _ in range(n)] for _ in range(k+1)]
    
    for i in range(1, k+1):
        # Initialize max_diff as the profit of buying on day 0 and selling on day 1
        max_diff = -prices[0]
        
        for j in range(1, n):
            # Either we don't make a transaction on day j, or we sell on day j
            dp[i][j] = max(dp[i][j-1], prices[j] + max_diff)
            # Update max_diff to potentially buy on day j
            max_diff = max(max_diff, dp[i-1][j] - prices[j])
    
    return dp[k][n-1]"""
            cpp_code = """int maxProfit(vector<int>& prices, int k) {
    int n = prices.size();
    if (n <= 1 || k <= 0) return 0;
    
    // If k is large enough, it's equivalent to unlimited transactions
    if (k >= n / 2) {
        int maxProfit = 0;
        for (int i = 1; i < n; i++) {
            if (prices[i] > prices[i-1]) {
                maxProfit += prices[i] - prices[i-1];
            }
        }
        return maxProfit;
    }
    
    // dp[i][j] = max profit with i transactions on day j
    vector<vector<int>> dp(k+1, vector<int>(n, 0));
    
    for (int i = 1; i <= k; i++) {
        // Initialize max_diff as the profit of buying on day 0 and selling on day 1
        int maxDiff = -prices[0];
        
        for (int j = 1; j < n; j++) {
            // Either we don't make a transaction on day j, or we sell on day j
            dp[i][j] = max(dp[i][j-1], prices[j] + maxDiff);
            // Update max_diff to potentially buy on day j
            maxDiff = max(maxDiff, dp[i-1][j] - prices[j]);
        }
    }
    
    return dp[k][n-1];
}"""
            time_complexity = 'O(k*n)'
            space_complexity = 'O(k*n)'
            explanation = 'Use dynamic programming with a 2D array to track max profit with i transactions by day j'
            
        elif problem == '309':  # Best Time to Buy and Sell Stock with Cooldown
            result = max_profit_with_cooldown(prices)
            code = """def maxProfit(prices):
    n = len(prices)
    if n <= 1:
        return 0
    
    # Three states:
    # buy[i]: Maximum profit ending with a buy on day i or earlier
    # sell[i]: Maximum profit ending with a sell on day i
    # cool[i]: Maximum profit ending with a cooldown on day i
    
    buy = [0] * n
    sell = [0] * n
    cool = [0] * n
    
    buy[0] = -prices[0]  # Initial buy on day 0
    
    for i in range(1, n):
        # Buy: Either keep previous buy state or buy after cooldown
        buy[i] = max(buy[i-1], cool[i-1] - prices[i])
        
        # Sell: Sell the stock bought earlier
        sell[i] = buy[i-1] + prices[i]
        
        # Cooldown: Either keep previous cooldown or come from a sell
        cool[i] = max(cool[i-1], sell[i-1])
    
    # The final state must be either selling or in cooldown
    return max(sell[n-1], cool[n-1])"""
            cpp_code = """int maxProfit(vector<int>& prices) {
    int n = prices.size();
    if (n <= 1) return 0;
    
    // Three states:
    // buy[i]: Maximum profit ending with a buy on day i or earlier
    // sell[i]: Maximum profit ending with a sell on day i
    // cool[i]: Maximum profit ending with a cooldown on day i
    
    vector<int> buy(n, 0);
    vector<int> sell(n, 0);
    vector<int> cool(n, 0);
    
    buy[0] = -prices[0];  // Initial buy on day 0
    
    for (int i = 1; i < n; i++) {
        // Buy: Either keep previous buy state or buy after cooldown
        buy[i] = max(buy[i-1], cool[i-1] - prices[i]);
        
        // Sell: Sell the stock bought earlier
        sell[i] = buy[i-1] + prices[i];
        
        // Cooldown: Either keep previous cooldown or come from a sell
        cool[i] = max(cool[i-1], sell[i-1]);
    }
    
    // The final state must be either selling or in cooldown
    return max(sell[n-1], cool[n-1]);
}"""
            time_complexity = 'O(n)'
            space_complexity = 'O(n)'
            explanation = 'Use state machine approach with three states: buy, sell, and cooldown'
            
        elif problem == '714':  # Best Time to Buy and Sell Stock with Transaction Fee
            result = max_profit_with_fee(prices, fee)
            code = """def maxProfit(prices, fee):
    n = len(prices)
    if n <= 1:
        return 0
    
    # Two states: cash (not holding stock) and hold (holding stock)
    cash, hold = 0, -prices[0]
    
    for i in range(1, n):
        # If we had cash, we can stay in cash or sell stock from previous hold
        previous_cash = cash
        cash = max(cash, hold + prices[i] - fee)
        
        # If we were holding stock, we can stay holding or buy with our previous cash
        hold = max(hold, previous_cash - prices[i])
    
    # We want to end with cash (not holding stock)
    return cash"""
            cpp_code = """int maxProfit(vector<int>& prices, int fee) {
    int n = prices.size();
    if (n <= 1) return 0;
    
    // Two states: cash (not holding stock) and hold (holding stock)
    int cash = 0, hold = -prices[0];
    
    for (int i = 1; i < n; i++) {
        // If we had cash, we can stay in cash or sell stock from previous hold
        int previousCash = cash;
        cash = max(cash, hold + prices[i] - fee);
        
        // If we were holding stock, we can stay holding or buy with our previous cash
        hold = max(hold, previousCash - prices[i]);
    }
    
    // We want to end with cash (not holding stock)
    return cash;
}"""
            time_complexity = 'O(n)'
            space_complexity = 'O(1)'
            explanation = 'Use state machine approach with two states: holding cash or holding stock'
            
        else:
            result = 0
            code = "def maxProfit(prices):\n    # Unknown problem number\n    return 0"
            cpp_code = "int maxProfit(vector<int>& prices) {\n    // Unknown problem number\n    return 0;\n}"
            time_complexity = 'N/A'
            space_complexity = 'N/A'
            explanation = f'Unknown problem number: {problem}'
        
        return jsonify({
            'result': result,
            'code': code,
            'cpp_code': cpp_code,
            'time_complexity': time_complexity,
            'space_complexity': space_complexity,
            'explanation': explanation
        })
        
    except Exception as e:
        print(f"ERROR in leetcode_stock: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Helper functions for stock problems
def max_profit_one_transaction(prices):
    """LeetCode 121: Best Time to Buy and Sell Stock"""
    if not prices:
        return 0
    
    max_profit = 0
    min_price = float('inf')
    
    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    
    return max_profit

def max_profit_unlimited_transactions(prices):
    """LeetCode 122: Best Time to Buy and Sell Stock II"""
    if not prices:
        return 0
    
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            profit += prices[i] - prices[i-1]
    
    return profit

def max_profit_two_transactions(prices):
    """LeetCode 123: Best Time to Buy and Sell Stock III"""
    if not prices or len(prices) <= 1:
        return 0
    
    n = len(prices)
    
    # Forward pass: max profit with one transaction up to day i
    dp_one_transaction = [0] * n
    min_price = prices[0]
    
    for i in range(1, n):
        min_price = min(min_price, prices[i])
        dp_one_transaction[i] = max(dp_one_transaction[i-1], prices[i] - min_price)
    
    # Backward pass: calculate max profit with two transactions
    max_price = prices[n-1]
    max_profit = dp_one_transaction[n-1]  # At least as good as one transaction
    
    for i in range(n-2, 0, -1):
        max_price = max(max_price, prices[i])
        max_profit = max(max_profit, dp_one_transaction[i-1] + max_price - prices[i])
    
    return max_profit

def max_profit_k_transactions(prices, k):
    """LeetCode 188: Best Time to Buy and Sell Stock IV"""
    n = len(prices)
    if n <= 1 or k <= 0:
        return 0
    
    # If k is large enough, it's equivalent to unlimited transactions
    if k >= n // 2:
        return max_profit_unlimited_transactions(prices)
    
    # dp[i][j] = max profit with i transactions on day j
    dp = [[0 for _ in range(n)] for _ in range(k+1)]
    
    for i in range(1, k+1):
        max_diff = -prices[0]
        
        for j in range(1, n):
            dp[i][j] = max(dp[i][j-1], prices[j] + max_diff)
            max_diff = max(max_diff, dp[i-1][j] - prices[j])
    
    return dp[k][n-1]

def max_profit_with_cooldown(prices):
    """LeetCode 309: Best Time to Buy and Sell Stock with Cooldown"""
    if not prices or len(prices) <= 1:
        return 0
    
    n = len(prices)
    
    # Three states: buy, sell, cooldown
    buy = [0] * n
    sell = [0] * n
    cool = [0] * n
    
    buy[0] = -prices[0]  # Initial buy on day 0
    
    for i in range(1, n):
        buy[i] = max(buy[i-1], cool[i-1] - prices[i])
        sell[i] = buy[i-1] + prices[i]
        cool[i] = max(cool[i-1], sell[i-1])
    
    return max(sell[n-1], cool[n-1])

def max_profit_with_fee(prices, fee):
    """LeetCode 714: Best Time to Buy and Sell Stock with Transaction Fee"""
    if not prices or len(prices) <= 1:
        return 0
    
    cash, hold = 0, -prices[0]
    
    for i in range(1, len(prices)):
        prev_cash = cash
        cash = max(cash, hold + prices[i] - fee)
        hold = max(hold, prev_cash - prices[i])
    
    return cash

# Add a new alternate route with a different path
@app.route('/stock-problems', methods=['POST'])
def stock_problems():
    """Alternate route for the stock problems playground"""
    return leetcode_stock()

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
    try:
        print("DEBUG: /stocks/stable endpoint accessed")
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
        window_size_str = request.args.get('window', '20')
        
        # Parse date ranges
        end_date_str = request.args.get('end_date')
        start_date_str = request.args.get('start_date')
        
        print(f"DEBUG: Params - metric={metric}, order={order}, symbol_filter={symbol_filter}, window={window_size_str}, start_date={start_date_str}, end_date={end_date_str}")
        
        try:
            window_size = int(window_size_str)
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Error parsing window_size: {e}")
            window_size = 20
        
        # Handle date ranges
        try:
            # Default end date is today
            end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # If start_date is provided, use it; otherwise use days parameter
            if start_date_str:
                start = datetime.strptime(start_date_str, '%Y-%m-%d')
            else:
                days_param = request.args.get('days')
                days = int(days_param) if days_param and days_param.isdigit() else 1095
                start = end - timedelta(days=days)
            
            # Validate the date range doesn't exceed 3 years (1095 days)
            max_range = timedelta(days=1095)  # 3 years
            if end - start > max_range:
                start = end - max_range
                print(f"DEBUG: Date range exceeded 3 years, adjusted to max range")
        except ValueError as e:
            print(f"DEBUG: Error parsing dates: {e}")
            end = datetime.now()
            start = end - timedelta(days=1095)  # Default to 3 years if date parsing fails
        
        results = []
        
        # If yfinance is not available, use mock data
        if yf is None:
            print("DEBUG: yfinance module is not available, using mock data")
            # Generate mock data for demo purposes
            return generate_mock_data(default_tickers, metric, order, symbol_filter, window_size)
            
        for name, symbol in default_tickers.items():
            if symbol_filter and symbol != symbol_filter:
                continue
                
            print(f"DEBUG: Fetching data for {name} ({symbol})")
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
                if hist.empty:
                    print(f"DEBUG: No history data for {symbol}")
                    results.append({'name': name, 'symbol': symbol, 'error': 'No data available for this time period.'})
                    continue
                    
                closes = [float(c) for c in hist['Close']]
                dates = [d.strftime('%Y-%m-%d') for d in hist.index]
                n = len(closes)
                
                print(f"DEBUG: Got {n} data points for {symbol}")
                
                if n < window_size:
                    print(f"DEBUG: Not enough data for {symbol} - needed {window_size}, got {n}")
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
                    print(f"DEBUG: Invalid metric/order combination: {metric}/{order}")
                    results.append({'name': name, 'symbol': symbol, 'error': 'Invalid metric or order.'})
                    continue
                
                if best_i is None:
                    print(f"DEBUG: No valid window found for {symbol}")
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
                print(f"DEBUG: Successfully processed {symbol}")
            except Exception as e:
                print(f"DEBUG: Error processing {symbol}: {str(e)}")
                results.append({'name': name, 'symbol': symbol, 'error': str(e)})
        
        # If all results have errors, use mock data as fallback
        if results and all('error' in r for r in results):
            print("DEBUG: All results have errors, using mock data as fallback")
            return generate_mock_data(default_tickers, metric, order, symbol_filter, window_size)
            
        results = sorted(results, key=lambda x: x.get('stability_score', float('inf')), reverse=(order=='desc'))
        if symbol_filter:
            print(f"DEBUG: Returning 1 result for {symbol_filter}")
            return jsonify(results[:1])
        
        print(f"DEBUG: Returning {min(5, len(results))} results")
        return jsonify(results[:5])
    except Exception as e:
        print(f"DEBUG: Global error in /stocks/stable: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify([{"error": f"Server error: {str(e)}"}])

def generate_mock_data(default_tickers, metric, order, symbol_filter, window_size):
    """Generate mock data for demo purposes when yfinance fails"""
    import random
    import numpy as np
    from datetime import datetime, timedelta
    
    print("DEBUG: Generating mock data")
    results = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)  # Default to 3 years of data
    
    # Filter tickers if needed
    tickers_to_use = {k: v for k, v in default_tickers.items() 
                     if not symbol_filter or v == symbol_filter}
    
    # Generate data for up to 5 companies or just the specified one
    for name, symbol in list(tickers_to_use.items())[:5 if not symbol_filter else 1]:
        try:
            # Generate days between start and end date
            days_count = (end_date - start_date).days + 1
            # Ensure we don't generate too much data
            days_to_generate = min(days_count, 100)
            
            # Generate dates from start_date to end_date
            dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') 
                    for i in range(days_to_generate - 1, -1, -1)]
            
            base_price = random.uniform(50, 500)  # Random base price
            trend = random.uniform(-0.3, 0.3)     # Random trend direction
            volatility = random.uniform(0.5, 3.0)  # Random volatility
            
            # Generate prices with trend and random noise
            closes = [base_price * (1 + trend * i/100 + random.gauss(0, volatility)/100) 
                     for i in range(days_to_generate)]
            
            # Calculate window statistics
            windows = []
            for i in range(len(closes) - window_size + 1):
                window = closes[i:i+window_size]
                if metric == 'std':
                    score = np.std(window)
                else:  # 'meanabs'
                    changes = [abs(window[j+1] - window[j]) for j in range(len(window)-1)]
                    score = np.mean(changes)
                windows.append((i, score))
            
            # Sort by score
            windows.sort(key=lambda x: x[1], reverse=(order == 'desc'))
            best_i, best_score = windows[0]
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
            print(f"DEBUG: Generated mock data for {symbol}")
        except Exception as e:
            print(f"DEBUG: Error generating mock data for {symbol}: {str(e)}")
            results.append({'name': name, 'symbol': symbol, 'error': 'Error generating mock data.'})
    
    return jsonify(results)

@app.route('/available_tickers')
def available_tickers():
    """Get a list of available tickers that can be used for analysis"""
    try:
        print("DEBUG: /available_tickers endpoint accessed")
        default_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
            'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM',
            'SPY', 'QQQ', 'VOO', 'ARKK', 'EEM', 'XLF',
            'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
            'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F', 'ZS=F', 'ZW=F',
            'VX=F', 'BTC=F', 'ETH=F'
        ]
        
        # If yfinance is not available, return the default tickers without validation
        if yf is None:
            print("DEBUG: yfinance module is not available, returning default tickers")
            return jsonify(default_tickers)
        
        # Use a shorter validation period to speed up the check
        validation_period = '5d'  # Just check if we can get 5 days of data
        print(f"DEBUG: Validating tickers with period={validation_period}")
        
        available = []
        for t in default_tickers:
            try:
                hist = yf.Ticker(t).history(period=validation_period)
                if not hist.empty:
                    available.append(t)
                    print(f"DEBUG: Ticker {t} is available")
                else:
                    print(f"DEBUG: Ticker {t} returned empty data")
            except Exception as e:
                print(f"DEBUG: Error checking ticker {t}: {str(e)}")
                continue
        
        # If no tickers are available, return the default list
        if not available:
            print("DEBUG: No tickers validated, returning default list")
            return jsonify(default_tickers)
            
        print(f"DEBUG: Returning {len(available)} validated tickers")
        return jsonify(available)
    except Exception as e:
        print(f"DEBUG: Global error in /available_tickers: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return default tickers as fallback
        return jsonify(default_tickers)

@app.route('/explain_stability')
def explain_stability():
    print("DEBUG: /explain_stability endpoint accessed")
    try:
        if request.method == 'POST':
            data = request.json
            stock = data.get('stock')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
        else:  # GET
            stock = request.args.get('stock', 'NVDA')
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
        if not stock:
            return jsonify({'explanation': 'Missing required parameter: stock.'})
        
        # Parse date ranges
        try:
            # Default end date is today
            end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # If start_date is provided, use it; otherwise default to start of current year
            if start_date_str:
                start = datetime.strptime(start_date_str, '%Y-%m-%d')
            else:
                # Default to start of current year
                year = datetime.now().year
                start = datetime.strptime(f"{year}-01-01", '%Y-%m-%d')
            
            # Validate the date range doesn't exceed 3 years (1095 days)
            max_range = timedelta(days=1095)  # 3 years
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
        import traceback
        print(f"Error in explain_stability: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'explanation': f"Error analyzing {stock}: {str(e)}"})

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
    
    # Parse date ranges
    end_date_str = request.args.get('end_date')
    start_date_str = request.args.get('start_date')
    
    try:
        # Default end date is today
        end = datetime.now() if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # If start_date is provided, use it; otherwise use days parameter
        if start_date_str:
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            days_param = request.args.get('days')
            days = int(days_param) if days_param and days_param.isdigit() else 1095
            start = end - timedelta(days=days)
        
        # Validate the date range doesn't exceed 3 years (1095 days)
        max_range = timedelta(days=1095)  # 3 years
        if end - start > max_range:
            start = end - max_range
    except ValueError as e:
        # Handle invalid date format
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
    
    available = []
    for t in default_tickers:
        try:
            hist = yf.Ticker(t).history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if not hist.empty and len(hist) > 0:
                available.append(t)
        except Exception:
            continue
    return jsonify(available)

@app.route('/test-post', methods=['GET', 'POST'])
def test_post():
    """Simple test endpoint that works with both GET and POST"""
    if request.method == 'POST':
        try:
            data = request.json
            return jsonify({
                'success': True,
                'message': 'POST request received',
                'data': data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    else:
        return jsonify({
            'success': True,
            'message': 'GET request received'
        })

# Initialize SQLite database for mood tracking
def init_mood_db():
    conn = sqlite3.connect('mood_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mood_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        mood_score INTEGER NOT NULL,
        mood_note TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_mood_db()

@app.route('/mood/entries', methods=['GET'])
def get_mood_entries():
    try:
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('mood_tracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
        SELECT * FROM mood_entries 
        WHERE date BETWEEN ? AND ? 
        ORDER BY date DESC
        '''
        
        cursor.execute(query, (start_date, end_date))
        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"entries": entries})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mood/add', methods=['POST'])
def add_mood_entry():
    try:
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        mood_score = data.get('mood_score')
        mood_note = data.get('mood_note', '')
        tags = data.get('tags', [])
        
        # Validate inputs
        if mood_score is None or not (1 <= mood_score <= 10):
            return jsonify({"error": "Mood score must be between 1 and 10"}), 400
        
        # Store tags as JSON
        tags_json = json.dumps(tags)
        
        conn = sqlite3.connect('mood_tracker.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO mood_entries (date, mood_score, mood_note, tags) VALUES (?, ?, ?, ?)',
            (date, mood_score, mood_note, tags_json)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "id": new_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mood/stats', methods=['GET'])
def get_mood_stats():
    try:
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('mood_tracker.db')
        cursor = conn.cursor()
        
        # Get average mood
        cursor.execute(
            'SELECT AVG(mood_score) FROM mood_entries WHERE date BETWEEN ? AND ?',
            (start_date, end_date)
        )
        avg_mood = cursor.fetchone()[0]
        
        # Get mood trend (day by day)
        cursor.execute(
            'SELECT date, mood_score FROM mood_entries WHERE date BETWEEN ? AND ? ORDER BY date',
            (start_date, end_date)
        )
        mood_trend = cursor.fetchall()
        
        # Get most mentioned tags
        cursor.execute(
            'SELECT tags FROM mood_entries WHERE date BETWEEN ? AND ?',
            (start_date, end_date)
        )
        tag_mentions = {}
        for (tags_json,) in cursor.fetchall():
            if tags_json:
                tags = json.loads(tags_json)
                for tag in tags:
                    tag_mentions[tag] = tag_mentions.get(tag, 0) + 1
        
        # Convert to sorted list of [tag, count]
        top_tags = sorted(tag_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        conn.close()
        
        return jsonify({
            "avg_mood": avg_mood if avg_mood else 0,
            "mood_trend": mood_trend,
            "top_tags": top_tags
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mood/delete/<int:entry_id>', methods=['DELETE'])
def delete_mood_entry(entry_id):
    try:
        conn = sqlite3.connect('mood_tracker.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mood_entries WHERE id = ?', (entry_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 