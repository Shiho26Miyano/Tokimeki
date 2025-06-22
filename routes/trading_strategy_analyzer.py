from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hf_signal_bp = Blueprint('hf_signal', __name__)

class HedgeFundTool:
    def __init__(self):
        self.indicators = {
            'MA': self.calculate_ma,
            'EMA': self.calculate_ema,
            'RSI': self.calculate_rsi,
            'MACD': self.calculate_macd,
            'BB': self.calculate_bollinger_bands,
            'ATR': self.calculate_atr
        }

    def fetch_stock_data(self, symbol, period='1y'):
        """Fetch historical stock data with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} to fetch data for {symbol}")
                stock = yf.Ticker(symbol)
                df = stock.history(period=period)

                if df.empty:
                    logger.warning(f"No data found for {symbol} on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    raise ValueError(f"No data found for {symbol} after {max_retries} attempts")

                logger.info(f"Successfully fetched data for {symbol}")
                return df

            except Exception as e:
                logger.error(f"Error fetching data for {symbol} on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                raise Exception(f"Failed to fetch data for {symbol} after {max_retries} attempts: {str(e)}")

        raise Exception(f"Failed to fetch data for {symbol} after {max_retries} attempts")

    def calculate_ma(self, df, window=20):
        """Calculate Simple Moving Average"""
        return df['Close'].rolling(window=window).mean()

    def calculate_ema(self, df, window=20):
        """Calculate Exponential Moving Average"""
        return df['Close'].ewm(span=window).mean()

    def calculate_rsi(self, df, window=14):
        """Calculate Relative Strength Index"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return pd.DataFrame({
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': histogram
        })

    def calculate_bollinger_bands(self, df, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        ma = df['Close'].rolling(window=window).mean()
        std = df['Close'].rolling(window=window).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        
        return pd.DataFrame({
            'Upper': upper,
            'Middle': ma,
            'Lower': lower
        })

    def calculate_atr(self, df, window=14):
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()
        return atr

    def generate_signals(self, df, strategy='trend'):
        """Generate trading signals based on selected strategy"""
        signals = pd.DataFrame(index=df.index)

        if strategy == 'trend':
            # Trend following strategy using MA crossover
            signals['MA20'] = self.calculate_ma(df, 20)
            signals['MA50'] = self.calculate_ma(df, 50)
            signals['Signal'] = np.where(signals['MA20'] > signals['MA50'], 1, -1)

        elif strategy == 'mean_reversion':
            # Mean reversion strategy using Bollinger Bands
            bb = self.calculate_bollinger_bands(df)
            signals['Signal'] = np.where(df['Close'] < bb['Lower'], 1,
                                      np.where(df['Close'] > bb['Upper'], -1, 0))

        elif strategy == 'momentum':
            # Momentum strategy using RSI
            signals['RSI'] = self.calculate_rsi(df)
            signals['Signal'] = np.where(signals['RSI'] < 30, 1,
                                      np.where(signals['RSI'] > 70, -1, 0))

        return signals

    def calculate_portfolio_metrics(self, df, signals, initial_capital=100000):
        """Calculate portfolio performance metrics"""
        portfolio = pd.DataFrame(index=df.index)
        portfolio['Position'] = signals['Signal']
        portfolio['Price'] = df['Close']
        portfolio['Holdings'] = portfolio['Position'] * portfolio['Price']
        portfolio['Cash'] = initial_capital - (portfolio['Position'].diff() * portfolio['Price']).cumsum()
        portfolio['Total'] = portfolio['Holdings'] + portfolio['Cash']
        portfolio['Returns'] = portfolio['Total'].pct_change()

        # Calculate risk metrics
        portfolio['Drawdown'] = (portfolio['Total'] - portfolio['Total'].cummax()) / portfolio['Total'].cummax()
        
        # Use np.nanmean and np.nanstd to handle potential NaN values in returns
        mean_return = np.nanmean(portfolio['Returns'])
        std_return = np.nanstd(portfolio['Returns'])
        
        sharpe_ratio = np.sqrt(252) * mean_return / std_return if std_return != 0 else 0
        max_drawdown = np.nanmin(portfolio['Drawdown'])
        
        # Use np.nanpercentile for VaR to ignore NaN values
        var_95 = np.nanpercentile(portfolio['Returns'].dropna(), 5)

        return {
            'total_return': (portfolio['Total'].iloc[-1] / initial_capital - 1) * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'var_95': var_95 * 100,
            'portfolio_data': portfolio
        }

@hf_signal_bp.route('/analyze', methods=['POST'])
def analyze_stock():
    logger.info("Received request to /analyze endpoint")
    try:
        data = request.get_json()
        logger.info(f"Request data: {data}")
        symbol = data.get('symbol')
        strategy = data.get('strategy', 'trend')
        period = data.get('period', '1y')

        if not symbol:
            logger.warning("No symbol provided in request")
            return jsonify({'error': 'Symbol is required'}), 400

        logger.info(f"Processing request for symbol: {symbol}, strategy: {strategy}, period: {period}")
        tool = HedgeFundTool()
        df = tool.fetch_stock_data(symbol, period)
        signals = tool.generate_signals(df, strategy)
        
        # Fill NaNs in signals to avoid issues in metric calculations
        signals.fillna(0, inplace=True)

        metrics = tool.calculate_portfolio_metrics(df, signals)

        # Prepare response data
        response = {
            'symbol': symbol,
            'strategy': strategy,
            'period': period,
            'metrics': {
                'total_return': f"{metrics['total_return']:.2f}%",
                'sharpe_ratio': f"{metrics['sharpe_ratio']:.2f}",
                'max_drawdown': f"{metrics['max_drawdown']:.2f}%",
                'var_95': f"{metrics['var_95']:.2f}%"
            },
            'latest_signals': {
                'date': signals.index[-1].strftime('%Y-%m-%d'),
                'signal': int(signals['Signal'].iloc[-1]),
                'price': float(df['Close'].iloc[-1])
            }
        }

        logger.info("Successfully processed request")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in analyze_stock: {str(e)}")
        return jsonify({'error': str(e)}), 500

# @hf_signal_bp.route('/indicators', methods=['GET'])
# def get_indicators():
#     """Get available technical indicators"""
#     return jsonify({
#         'indicators': list(HedgeFundTool().indicators.keys())
#     })

# @hf_signal_bp.route('/strategies', methods=['GET'])
# def get_strategies():
#     """Get available trading strategies"""
#     return jsonify({
#         'strategies': ['trend', 'mean_reversion', 'momentum']
#     }) 