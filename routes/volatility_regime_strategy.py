from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

volatility_regime_bp = Blueprint('volatility_regime', __name__)

class VolatilityRegimeAnalyzer:
    def __init__(self):
        self.regime_thresholds = {
            'low': 0.15,      # Below 15% volatility
            'medium': 0.25,   # 15-25% volatility
            'high': 0.35,     # 25-35% volatility
            'extreme': float('inf')  # Above 35% volatility
        }
    
    def fetch_stock_data(self, symbol, period='2y'):
        """Fetch historical stock data"""
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            if df.empty:
                raise ValueError(f"No data found for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def calculate_rolling_volatility(self, df, window=30):
        """Calculate rolling volatility"""
        returns = df['Close'].pct_change().dropna()
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
        return rolling_vol
    
    def detect_volatility_regime(self, volatility):
        """Detect volatility regime based on thresholds"""
        if volatility < self.regime_thresholds['low']:
            return 'Low Volatility'
        elif volatility < self.regime_thresholds['medium']:
            return 'Medium Volatility'
        elif volatility < self.regime_thresholds['high']:
            return 'High Volatility'
        else:
            return 'Extreme Volatility'
    
    def analyze_regime_changes(self, rolling_vol):
        """Analyze regime changes over time"""
        regimes = rolling_vol.apply(self.detect_volatility_regime)
        regime_changes = regimes.ne(regimes.shift()).cumsum()
        
        regime_periods = []
        for i in range(1, regime_changes.max() + 1):
            period_mask = regime_changes == i
            if period_mask.any():
                start_date = rolling_vol[period_mask].index[0]
                end_date = rolling_vol[period_mask].index[-1]
                avg_vol = rolling_vol[period_mask].mean()
                regime = regimes[period_mask].iloc[0]
                duration = len(rolling_vol[period_mask])
                
                regime_periods.append({
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'regime': regime,
                    'avg_volatility': round(avg_vol, 2),
                    'duration_days': duration
                })
        
        return regime_periods
    
    def calculate_regime_statistics(self, rolling_vol):
        """Calculate statistics for each regime"""
        regimes = rolling_vol.apply(self.detect_volatility_regime)
        stats = {}
        
        for regime in regimes.unique():
            if pd.notna(regime):
                regime_data = rolling_vol[regimes == regime]
                stats[regime] = {
                    'count': len(regime_data),
                    'avg_volatility': round(regime_data.mean(), 2),
                    'min_volatility': round(regime_data.min(), 2),
                    'max_volatility': round(regime_data.max(), 2),
                    'percentage_of_time': round(len(regime_data) / len(rolling_vol) * 100, 1)
                }
        
        return stats

@volatility_regime_bp.route('/analyze', methods=['POST'])
def analyze_volatility_regime():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        window = data.get('window', 30)
        period = data.get('period', '2y')
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        analyzer = VolatilityRegimeAnalyzer()
        df = analyzer.fetch_stock_data(symbol, period)
        rolling_vol = analyzer.calculate_rolling_volatility(df, window)
        
        # Remove NaN values
        rolling_vol_clean = rolling_vol.dropna()
        
        if len(rolling_vol_clean) == 0:
            return jsonify({'error': 'Insufficient data for analysis'}), 400
        
        # Current regime
        current_vol = rolling_vol_clean.iloc[-1]
        current_regime = analyzer.detect_volatility_regime(current_vol)
        
        # Regime analysis
        regime_periods = analyzer.analyze_regime_changes(rolling_vol_clean)
        regime_stats = analyzer.calculate_regime_statistics(rolling_vol_clean)
        
        # Prepare response
        response = {
            'symbol': symbol,
            'analysis_period': period,
            'rolling_window': window,
            'current_volatility': round(current_vol, 2),
            'current_regime': current_regime,
            'regime_periods': regime_periods,
            'regime_statistics': regime_stats,
            'volatility_data': {
                'dates': [d.strftime('%Y-%m-%d') for d in rolling_vol_clean.index],
                'values': [round(v, 2) for v in rolling_vol_clean.values]
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in volatility regime analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@volatility_regime_bp.route('/regimes', methods=['GET'])
def get_regime_info():
    """Get information about volatility regimes"""
    return jsonify({
        'regime_thresholds': {
            'low': 'Below 15%',
            'medium': '15-25%',
            'high': '25-35%',
            'extreme': 'Above 35%'
        },
        'description': 'Volatility regimes help identify different market conditions and risk levels'
    }) 