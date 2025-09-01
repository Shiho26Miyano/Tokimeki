# FutureQuant Trader System

A comprehensive futures trading system built on FastAPI that implements distributional ML models for futures prediction, feature engineering, signal generation, backtesting, and paper trading.

## 🚀 Features

### Core Components
- **Data Ingestion**: Pull historical futures data from yfinance
- **Feature Engineering**: Compute technical indicators and features
- **ML Models**: Train distributional models (quantile regression, random forest, neural networks)
- **Signal Generation**: Generate trading signals based on model forecasts
- **Backtesting**: Test strategies on historical data
- **Paper Trading**: Simulate live trading without real money

### Supported Futures
- **Energy**: CL=F (Crude Oil), BZ=F (Brent)
- **Equity**: ES=F (E-mini S&P 500), MNQ=F (Micro E-mini NASDAQ)
- **Metals**: GC=F (Gold), SI=F (Silver)
- **Grains**: ZC=F (Corn)

## 🏗️ Architecture

```
┌──────────────┐      ┌───────────────┐      ┌───────────────┐
│  Data Ingest │────▶ │  Feature Svc  │────▶ │  Model Train  │
└─────┬────────┘      └──────┬────────┘      └──────┬────────┘
      │                       │                      │
      ▼                       ▼                      ▼
  SQLite/Postgres      Feature Store          MLflow + Models
      ▲                       ▲                      ▲
      │                       │                      │
      └──────────▶  Signal Service  ◀───────────────┘
                         │
                         ▼
                     FastAPI API ──▶ React UI
                         │
                         ▼
                    Paper Broker (sim engine)
```

## 📁 Project Structure

```
app/
├── models/                          # Database models
│   ├── database.py                 # Database configuration
│   └── trading_models.py           # SQLAlchemy models
├── services/futurequant/            # Core services
│   ├── data_service.py             # Data ingestion
│   ├── feature_service.py          # Feature engineering
│   ├── model_service.py            # ML model training
│   ├── signal_service.py           # Signal generation
│   ├── backtest_service.py         # Backtesting engine
│   ├── paper_broker_service.py     # Paper trading
│   └── mlflow_service.py           # Experiment tracking
└── api/v1/endpoints/futurequant/   # API endpoints
    ├── data.py                     # Data endpoints
    ├── features.py                 # Feature endpoints
    ├── models.py                   # Model endpoints
    ├── signals.py                  # Signal endpoints
    ├── backtests.py                # Backtest endpoints
    └── paper_trading.py            # Paper trading endpoints
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export FUTUREQUANT_DATABASE_URL="sqlite:///./data/databases/futurequant_trader.db"
export MLFLOW_TRACKING_URI="http://localhost:5000"
```

### 3. Initialize Database
```python
from app.models.database import init_db
await init_db()
```

### 4. Start the API
```bash
uvicorn app.main:app --reload
```

## 📊 API Endpoints

### Data Management
- `POST /api/v1/futurequant/data/ingest` - Ingest futures data
- `GET /api/v1/futurequant/data/symbols` - Get available symbols
- `GET /api/v1/futurequant/data/symbols/{symbol}/latest` - Get latest data

### Feature Engineering
- `POST /api/v1/futurequant/features/compute` - Compute features
- `GET /api/v1/futurequant/features/recipes` - Get feature recipes
- `POST /api/v1/futurequant/features/batch` - Batch feature computation

### ML Models
- `POST /api/v1/futurequant/models/train` - Train a new model
- `POST /api/v1/futurequant/models/predict` - Make predictions
- `GET /api/v1/futurequant/models/types` - Get model types
- `GET /api/v1/futurequant/models/horizons` - Get forecast horizons

### Signal Generation
- `POST /api/v1/futurequant/signals/generate` - Generate trading signals
- `GET /api/v1/futurequant/signals/strategies` - Get trading strategies
- `GET /api/v1/futurequant/signals/strategies/{name}` - Get strategy details

### Backtesting
- `POST /api/v1/futurequant/backtests/run` - Run a backtest
- `GET /api/v1/futurequant/backtests/config` - Get backtest configuration

### Paper Trading
- `POST /api/v1/futurequant/paper-trading/start` - Start paper trading
- `POST /api/v1/futurequant/paper-trading/order` - Place an order
- `GET /api/v1/futurequant/paper-trading/sessions/{id}/status` - Get session status

## 🔧 Configuration

### Database
- **SQLite** (default): `sqlite:///./data/databases/futurequant_trader.db`
- **PostgreSQL**: `postgresql://user:pass@localhost/futurequant`

### MLflow
- **Tracking URI**: `http://localhost:5000`
- **Registry URI**: `http://localhost:5000`

### Feature Recipes
- **basic**: Returns, log returns, volatility
- **momentum**: RSI, MACD, Stochastic
- **trend**: SMA, EMA, Bollinger Bands
- **volatility**: ATR, BB width
- **regime**: Trend strength, volatility regime
- **full**: All features combined

### Trading Strategies
- **conservative**: Low risk, low return
- **moderate**: Balanced risk and return
- **aggressive**: High risk, high return

## 📈 Usage Examples

### 1. Ingest Data
```python
import requests

# Ingest CL=F data for the last year
response = requests.post("http://localhost:8000/api/v1/futurequant/data/ingest", json={
    "symbols": ["CL=F"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "interval": "1d"
})
```

### 2. Compute Features
```python
# Compute full feature set for CL=F
response = requests.post("http://localhost:8000/api/v1/futurequant/features/compute", json={
    "symbol": "CL=F",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "recipe": "full"
})
```

### 3. Train Model
```python
# Train quantile regression model
response = requests.post("http://localhost:8000/api/v1/futurequant/models/train", json={
    "symbol": "CL=F",
    "model_type": "quantile_regression",
    "horizon_minutes": 1440,  # 1 day
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
})
```

### 4. Generate Signals
```python
# Generate trading signals
response = requests.post("http://localhost:8000/api/v1/futurequant/signals/generate", json={
    "model_id": 1,
    "strategy_name": "moderate",
    "start_date": "2024-12-01",
    "end_date": "2024-12-31"
})
```

### 5. Run Backtest
```python
# Run backtest
response = requests.post("http://localhost:8000/api/v1/futurequant/backtests/run", json={
    "strategy_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "symbols": ["CL=F"],
    "initial_capital": 100000
})
```

### 6. Start Paper Trading
```python
# Start paper trading session
response = requests.post("http://localhost:8000/api/v1/futurequant/paper-trading/start", json={
    "model_id": 1,
    "strategy_id": 1,
    "symbols": ["CL=F"],
    "initial_capital": 100000,
    "session_name": "CL Oil Trading"
})
```

## 🔍 Monitoring & Observability

### MLflow Integration
- Track all experiments and model versions
- Compare model performance
- Model registry for production deployment

### Performance Metrics
- **Returns**: Total return, annualized return
- **Risk**: Volatility, maximum drawdown
- **Risk-Adjusted**: Sharpe ratio, Sortino ratio
- **Trading**: Win rate, profit factor, average trade

## 🚨 Risk Management

### Position Sizing
- Kelly criterion for optimal sizing
- Risk per trade limits
- Maximum leverage constraints

### Stop Loss & Take Profit
- Quantile-based stop losses
- Trailing stops
- Position-level risk limits

### Portfolio Constraints
- Maximum positions per symbol
- Correlation limits
- Sector exposure limits

## 🔮 Future Enhancements

### Planned Features
- **Real-time Data**: WebSocket feeds for live prices
- **Advanced Models**: Transformer-based models, ensemble methods
- **Portfolio Optimization**: Risk parity, mean-variance optimization
- **Live Trading**: Integration with real brokers (IBKR, Tradovate)
- **Advanced Analytics**: Regime detection, stress testing
- **Mobile App**: React Native mobile application

### Research Areas
- **Cross-Asset Models**: Multi-asset correlation modeling
- **Alternative Data**: News sentiment, options flow, order book
- **Market Microstructure**: Bid-ask spread modeling, liquidity analysis
- **Regime Detection**: Market state classification and adaptation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. It does not constitute financial advice. Trading futures involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Check the documentation
- Review the API examples

---

**FutureQuant Trader** - Building the future of quantitative futures trading, one model at a time.
