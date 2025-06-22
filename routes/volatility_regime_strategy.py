from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

volatility_regime_bp = Blueprint('volatility_regime', __name__)

def calculate_features(df):
    """Calculate technical features for volatility regime prediction"""
    features = {}
    
    # Rolling volatility (5d, 10d, 20d)
    for window in [5, 10, 20]:
        features[f'volatility_{window}d'] = df['Close'].pct_change().rolling(window).std()
    
    # Momentum features
    for window in [5, 10, 20]:
        features[f'momentum_{window}d'] = df['Close'].pct_change(window)
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    features['macd'] = exp1 - exp2
    features['macd_signal'] = features['macd'].ewm(span=9).mean()
    
    # ATR (Average True Range)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    features['atr'] = true_range.rolling(14).mean()
    
    # Bollinger Bands
    sma_20 = df['Close'].rolling(20).mean()
    std_20 = df['Close'].rolling(20).std()
    features['bb_upper'] = sma_20 + (std_20 * 2)
    features['bb_lower'] = sma_20 - (std_20 * 2)
    features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma_20
    
    # Volume features
    features['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    
    return pd.DataFrame(features)

def label_volatility_regimes(df, volatility_threshold=0.75):
    """Label volatility regimes based on rolling volatility percentile"""
    volatility_5d = df['Close'].pct_change().rolling(5).std()
    threshold = volatility_5d.quantile(volatility_threshold)
    
    # 1 for high volatility, 0 for low volatility
    regimes = (volatility_5d > threshold).astype(int)
    return regimes

def train_regime_model(features_df, regimes, lookback_days=252):
    """Train a model to predict volatility regimes"""
    # Prepare data
    X = features_df.dropna()
    y = regimes[X.index]
    
    # Use last lookback_days for training
    if len(X) > lookback_days:
        X = X.tail(lookback_days)
        y = y.tail(lookback_days)
    
    # Remove any remaining NaN values
    mask = ~(X.isna().any(axis=1) | y.isna())
    X = X[mask]
    y = y[mask]
    
    if len(X) < 50:  # Need minimum data
        return None, None
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    return model, scaler

def momentum_strategy(df, regime_prediction):
    """Apply momentum or mean-reversion strategy based on regime prediction"""
    signals = pd.Series(0, index=df.index)
    
    # Pre-calculate RSI once
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Pre-calculate SMAs
    sma_short = df['Close'].rolling(10).mean()
    sma_long = df['Close'].rolling(20).mean()
    
    # Only use indices present in all required series and regime_prediction
    valid_idx = (
        df.index.intersection(regime_prediction.index)
        .intersection(sma_short.dropna().index)
        .intersection(sma_long.dropna().index)
        .intersection(rsi.dropna().index)
    )
    valid_idx = valid_idx.sort_values()
    
    for i in range(1, len(valid_idx)):
        current_idx = valid_idx[i]
        prev_idx = valid_idx[i-1]
        
        if pd.isna(regime_prediction.get(current_idx)):
            continue
        if pd.isna(sma_short[current_idx]) or pd.isna(sma_long[current_idx]) or pd.isna(rsi[current_idx]):
            continue
        
        if regime_prediction[current_idx] == 0:  # Low volatility - trend following
            # SMA crossover strategy
            if sma_short[current_idx] > sma_long[current_idx] and sma_short[prev_idx] <= sma_long[prev_idx]:
                signals[current_idx] = 1  # Buy signal
            elif sma_short[current_idx] < sma_long[current_idx] and sma_short[prev_idx] >= sma_long[prev_idx]:
                signals[current_idx] = -1  # Sell signal
        else:  # High volatility - mean reversion
            # RSI mean reversion strategy
            if rsi[current_idx] < 30:
                signals[current_idx] = 1  # Buy signal (oversold)
            elif rsi[current_idx] > 70:
                signals[current_idx] = -1  # Sell signal (overbought)
    
    return signals

def backtest_strategy(df, signals, initial_capital=100000):
    """Backtest the strategy with position sizing and risk management"""
    positions = pd.Series(0, index=df.index)
    portfolio_value = pd.Series(initial_capital, index=df.index)
    cash = initial_capital
    shares = 0
    
    for i in range(1, len(df)):
        if signals[i] == 1 and shares == 0:  # Buy signal
            shares = cash / df['Close'][i]
            cash = 0
        elif signals[i] == -1 and shares > 0:  # Sell signal
            cash = shares * df['Close'][i]
            shares = 0
        
        # Update portfolio value
        portfolio_value[i] = cash + (shares * df['Close'][i])
    
    # Calculate returns
    returns = portfolio_value.pct_change().dropna()
    
    # Calculate metrics
    total_return = (portfolio_value.iloc[-1] - initial_capital) / initial_capital
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    max_drawdown = ((portfolio_value - portfolio_value.expanding().max()) / portfolio_value.expanding().max()).min()
    
    # Win rate
    trade_returns = returns[returns != 0]
    win_rate = (trade_returns > 0).mean() if len(trade_returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'portfolio_value': portfolio_value.tolist(),
        'signals': signals.tolist()
    }

@volatility_regime_bp.route('/analyze_volatility_regime', methods=['POST'])
def analyze_volatility_regime():
    data = request.get_json()
    symbol = data.get('symbol', 'ES=F')  # Default to E-mini S&P 500
    lookback_days = data.get('lookback_days', 252)
    volatility_threshold = data.get('volatility_threshold', 0.75)
    
    try:
        # Fetch data
        print(f"Fetching data for {symbol}...")
        stock = yf.Ticker(symbol)
        df = stock.history(period=f"{lookback_days + 50}d")  # Extra days for calculations
        
        if len(df) < 100:
            return jsonify({'error': 'Insufficient data for analysis'}), 400
        
        print(f"Data fetched successfully. Shape: {df.shape}")
        
        # Calculate features
        print("Calculating features...")
        features_df = calculate_features(df)
        print(f"Features calculated. Shape: {features_df.shape}")
        
        # Label regimes
        print("Labeling regimes...")
        regimes = label_volatility_regimes(df, volatility_threshold)
        print(f"Regimes labeled. High volatility periods: {regimes.sum()}")
        
        # Train model
        print("Training model...")
        model, scaler = train_regime_model(features_df, regimes, lookback_days)
        
        if model is None:
            return jsonify({'error': 'Unable to train model with available data'}), 400
        
        print("Model trained successfully")
        
        # Make predictions
        print("Making predictions...")
        X_pred = features_df.dropna()
        if len(X_pred) > 0:
            X_scaled = scaler.transform(X_pred)
            regime_predictions = model.predict(X_scaled)
            
            # Apply strategy
            print("Applying strategy...")
            signals = momentum_strategy(df, pd.Series(regime_predictions, index=X_pred.index))
            
            # Backtest
            print("Running backtest...")
            results = backtest_strategy(df, signals)
            
            # Calculate regime accuracy
            actual_regimes = regimes[X_pred.index]
            regime_accuracy = float((regime_predictions == actual_regimes).mean())
            
            print("Analysis completed successfully")
            
            # Convert all results to native Python types
            results_py = {
                'total_return': float(results['total_return']),
                'sharpe_ratio': float(results['sharpe_ratio']),
                'max_drawdown': float(results['max_drawdown']),
                'win_rate': float(results['win_rate']),
                'portfolio_value': [float(x) for x in results['portfolio_value']],
                'signals': [int(x) for x in results['signals']]
            }
            
            return jsonify({
                'symbol': symbol,
                'strategy_results': results_py,
                'regime_accuracy': regime_accuracy,
                'volatility_threshold': float(volatility_threshold),
                'lookback_days': int(lookback_days),
                'data_points': int(len(df)),
                'regime_distribution': {
                    'low_volatility': int((regime_predictions == 0).sum()),
                    'high_volatility': int((regime_predictions == 1).sum())
                }
            })
        
        else:
            return jsonify({'error': 'No valid data for prediction'}), 400
            
    except Exception as e:
        import traceback
        print(f"Error in analyze_volatility_regime: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@volatility_regime_bp.route('/available_futures', methods=['GET'])
def get_available_futures():
    """Get list of available futures contracts"""
    futures = [
        {'symbol': 'ES=F', 'name': 'E-mini S&P 500'},
        {'symbol': 'NQ=F', 'name': 'E-mini NASDAQ-100'},
        {'symbol': 'YM=F', 'name': 'E-mini Dow Jones'},
        {'symbol': 'RTY=F', 'name': 'E-mini Russell 2000'},
        {'symbol': 'MES=F', 'name': 'Micro E-mini S&P 500'},
        {'symbol': 'MNQ=F', 'name': 'Micro E-mini NASDAQ-100'},
        {'symbol': 'MYM=F', 'name': 'Micro E-mini Dow'},
        {'symbol': 'M2K=F', 'name': 'Micro E-mini Russell 2000'},
        {'symbol': 'GC=F', 'name': 'Gold Futures'},
        {'symbol': 'CL=F', 'name': 'Crude Oil WTI'},
        {'symbol': 'VX=F', 'name': 'VIX Futures'}
    ]
    return jsonify(futures) 