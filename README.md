# 🚀 Tokimeki 
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

**Tokimeki** is an educational platform for learning quantitative finance and market analysis through interactive simulations and research tools.

**Educational Purpose Only**: All tools are designed for learning financial concepts, not for actual investment decisions.

## 🏗️ Architecture

### Backend Structure (FastAPI)

```
Tokimeki/
├── main.py                          # Railway deployment entry point
├── config.py                        # Simple configuration
├── requirements.txt                 # Python dependencies
├── railway.toml                     # Railway configuration
├── app/                            # FastAPI application core
│   ├── main.py                     # FastAPI app configuration
│   ├── core/                       # Core system components
│   │   ├── config.py               # Application settings
│   │   ├── dependencies.py         # Dependency injection
│   │   └── middleware.py           # Request/response middleware
│   ├── models/                     # Database models
│   │   ├── database.py             # Database configuration
│   │   ├── golf_models.py          # Mini golf strategy models
│   │   ├── trading_models.py       # Trading system models
│   │   ├── aapl_analysis_models.py # AAPL analysis data models
│   │   ├── etf_models.py           # ETF dashboard models
│   │   ├── options_models.py       # Options chain models
│   │   ├── simulation_models.py    # Simulation data models
│   │   └── market_pulse_models.py  # Market Pulse data models
│   ├── services/                   # Business logic services
│   │   ├── ai_service.py           # AI integration (OpenRouter)
│   │   ├── brpc_service.py         # High-performance BRPC service
│   │   ├── cache_service.py        # Redis caching layer
│   │   ├── rag_service.py          # RAG system service
│   │   ├── stock_service.py        # Market data service
│   │   ├── usage_service.py        # Usage tracking and analytics
│   │   ├── aaplanalysis/           # AAPL Analysis services
│   │   │   ├── analysis_service.py # Core AAPL analysis logic
│   │   │   ├── backtest_service.py # AAPL strategy backtesting
│   │   │   ├── data_pipeline_service.py # Data processing pipeline
│   │   │   └── polygon_service.py  # Polygon.io market data integration
│   │   ├── consumeroptions/        # Consumer Options Dashboard services
│   │   │   ├── analytics_service.py # Options analytics and ratios
│   │   │   ├── chain_service.py    # Options chain processing
│   │   │   ├── dashboard_service.py # Dashboard orchestration
│   │   │   └── polygon_service.py  # Live options data from Polygon
│   │   ├── etf/                    # ETF Dashboard services
│   │   │   ├── analytics_service.py # Risk metrics and technical indicators
│   │   │   ├── dashboard_service.py # Multi-ETF comparison
│   │   │   ├── polygon_service.py  # Polygon.io ETF data
│   │   │   ├── search_service.py   # ETF ticker search
│   │   │   └── yfinance_service.py # Yahoo Finance fallback
│   │   ├── futureexploratorium/    # Futures Exploratorium services
│   │   │   ├── analytics_service.py
│   │   │   ├── core_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── event_analysis_service.py
│   │   │   ├── market_intelligence_service.py
│   │   │   └── strategy_service.py
│   │   ├── futurequant/            # FutureQuant trading services
│   │   │   ├── backtest_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── data_service.py
│   │   │   ├── feature_service.py
│   │   │   ├── model_service.py
│   │   │   ├── signal_service.py
│   │   │   ├── paper_broker_service.py
│   │   │   ├── mlflow_service.py
│   │   │   ├── vectorbt_service.py
│   │   │   └── qflib_service.py
│   │   ├── minigolfstrategy/       # Mini Golf Strategy services
│   │   │   ├── core_service.py
│   │   │   ├── strategy_service.py
│   │   │   ├── factor_analysis_service.py
│   │   │   └── clients/
│   │   │       └── golfcourse_api.py
│   │   └── simulation/             # Simulation services
│   │       ├── data_ingestion_service.py
│   │       ├── feature_service.py
│   │       ├── pipeline_service.py
│   │       ├── simulation_service.py
│   │       └── strategy_service.py
│   └── api/                        # REST API endpoints
│       ├── deps.py                 # API dependencies
│       └── v1/                     # API version 1
│           ├── api.py              # Main router configuration
│           └── endpoints/          # Feature-specific endpoints
│               ├── chat.py         # AI chat interface
│               ├── stocks.py       # Market data endpoints
│               ├── sentiment.py    # Text sentiment analysis
│               ├── speech.py       # Audio processing
│               ├── monitoring.py   # System health monitoring
│               ├── rag.py          # Document analysis endpoints
│               ├── websocket.py    # Real-time data streaming
│               ├── quantitative_analysis.py
│               ├── aapl_analysis.py # AAPL stock vs options analysis API
│               ├── simulation.py   # Simulation endpoints
│               ├── etf.py          # ETF Dashboard API
│               ├── consumeroptions/ # Consumer Options API
│               │   ├── chain.py
│               │   ├── analytics.py
│               │   ├── dashboard.py
│               │   └── simulation.py
│               ├── futurequant/    # FutureQuant trading API
│               │   ├── data.py
│               │   ├── features.py
│               │   ├── models.py
│               │   ├── signals.py
│               │   ├── backtests.py
│               │   └── paper_trading.py
│               ├── futureexploratorium/ # Futures Exploratorium API
│               │   ├── core.py
│               │   ├── dashboard.py
│               │   ├── analytics.py
│               │   ├── strategy.py
│               │   └── event_analysis.py
│               └── minigolfstrategy/ # Mini Golf Strategy API
│                   ├── core.py
│                   ├── courses.py
│                   ├── strategy.py
│                   └── factor_analysis.py
│               └── market_pulse.py  # Market Pulse API
├── data/                           # Data storage
│   ├── cache/                      # Cache databases
│   └── databases/                  # Application databases
│       └── futurequant_trader.db
├── docs/                           # Documentation
│   ├── ETF_DATA_SOURCES.md         # ETF data source documentation
│   ├── design-principles/          # Design principles
│   └── features/marketpulse/      # Market Pulse documentation
├── jobs/                           # Scheduled jobs
│   └── daily_run.py                # Daily data processing tasks
├── deployment/                     # Deployment configuration
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── railway.json
├── scripts/                        # Utility scripts
│   ├── cleanup_old_models.py
│   ├── demo_paper_trading.py
│   ├── init_database.py
│   ├── init_golf_database.py
│   ├── init_simulation_db.py
│   ├── generate_simulation_data.py
│   ├── trigger_lambda_agents.py    # Market Pulse: Trigger Lambda functions
│   ├── diagnose_data_collection.py # Market Pulse: Diagnose data issues
│   ├── view_s3_data.py            # Market Pulse: View S3 data
│   ├── check_lambda_status.py      # Market Pulse: Check Lambda status
│   ├── deploy-lambda-functions.sh  # Market Pulse: Deploy Lambda functions
│   └── start_data_collector.py    # Market Pulse: Start data collector
└── tests/                          # Test suite
    ├── core/
    ├── features/
    ├── futurequant/
    ├── market_data/
    ├── simulation/
    └── strategies/
```

### Frontend Structure (Modular)

```
static/
├── index.html                      # Main application interface
├── main.js                         # Core JavaScript functionality
├── favicon.ico                     # Site icon
├── css/                           # Modular CSS files
│   ├── main.css                   # Base styles and typography
│   ├── components.css             # Component-specific styles
│   ├── animations.css             # Animation keyframes and effects
│   └── sliders.css                # Slider-specific styles
├── js/                            # Modular JavaScript files
│   ├── app.js                     # Main application entry point
│   ├── utils/                     # Utility modules
│   │   ├── cache.js               # Cache management
│   │   ├── tabs.js                # Tab management
│   │   ├── modals.js              # Modal management
│   │   ├── loading.js             # Loading states and timers
│   │   └── component-loader.js    # Dynamic component loading
│   └── components/                # Component modules
│       ├── navigation.js          # Navigation component
│       ├── etf-dashboard-multi.js # Multi-ETF comparison dashboard
│       ├── consumeroptions.js     # Consumer options sentiment dashboard
│       ├── aapl-weekly-tracker.js # AAPL weekly investment tracker
│       ├── futures-exploratorium.js
│       ├── futurequant-dashboard.js
│       ├── minigolf-strategy.js
│       ├── rag-bi.js
│       ├── chatbot.js
│       ├── ai-platform-comparables.js
│       ├── market-overtime.js
│       ├── volatility-explorer.js
│       ├── hf-signal-tool.js
│       └── market-pulse.js          # Market Pulse dashboard
├── components/                    # HTML component templates
│   ├── etf-dashboard.html
│   ├── consumeroptions.html
│   ├── minigolf-strategy.html
│   ├── futurequant-dashboard.html
│   └── market-pulse.html            # Market Pulse dashboard
└── img/                           # Images and icons
    ├── cute.png
    ├── demo.png
    ├── handsome.png
    └── lionPixel.png
```

## 📚 Learning Modules

### 1. **ETF Dashboard**
- Multi-ETF comparison with live data from Polygon.io
- Risk metrics (volatility, Sharpe ratio, max drawdown)
- Technical indicators (RSI, MACD, moving averages)
- Holdings analysis and sector distribution
- Composite scoring and ranking system
- Real-time price data with fallback to yfinance

### 2. **Consumer Options Dashboard**
- Real-time options chain analysis with live Polygon.io data
- Volatility regime indicators and trading signals
- Call/Put ratios and unusual activity detection
- IV term structure visualization
- Greeks analysis (Delta, Gamma, Theta, Vega)
- Underlying price tracking with technical indicators

### 3. **AAPL Stock vs Options Analysis**
- Interactive comparison tool with strategy selector
- Backtesting simulations with historical data
- Visual P&L tracking and educational metrics
- Weekly investment tracker (DCA vs Options strategies)

### 4. **Quantitative Finance (FutureQuant)**
- Paper trading simulator and backtesting framework
- Machine learning experiments and risk analysis tools
- Performance dashboards and feature engineering
- Model tracking with MLflow

### 5. **Market Intelligence (FutureExploratorium)**
- Event analysis and strategy development tools
- Market data visualization and analytics dashboard
- Real-time market intelligence

### 6. **Simulation Services**
- Strategy simulation and backtesting framework
- Walk-forward analysis and performance metrics
- Feature engineering and data pipeline

### 7. **Market Pulse** ⭐ NEW
- Real-time market monitoring with dual-agent system
- Compute Agent: Automated signal computation every 5 minutes
- Learning Agent: Machine learning-based signal prediction
- Live market data collection via Polygon WebSocket
- AWS Lambda integration for automated processing
- Comprehensive dashboard for dual-agent signal comparison
- S3-based storage for raw and processed data
- See [Market Pulse Documentation](./docs/features/marketpulse/README.md) for details

### 8. **Academic Research Tools**
- AI-powered research assistant with RAG system
- Market data APIs and statistical analysis tools
- Document analysis and vector search

## 🔧 Technical Stack

### Backend
- **FastAPI** - Modern, high-performance web framework
- **SQLAlchemy** - Database ORM
- **Redis** - Caching layer
- **httpx** - Async HTTP client
- **Pydantic** - Data validation

### Data Sources
- **Polygon.io** - Primary source for live market data (stocks, options, ETFs)
- **yfinance** - Fallback source for historical ETF data
- **Data prioritization**: Polygon.io → yfinance (with automatic fallback)

### AI/ML
- **OpenRouter** - AI model access
- **LangChain** - RAG system
- **scikit-learn** - Machine learning
- **PyTorch** - Deep learning
- **VectorBT** - Quantitative analysis
- **MLflow** - Model tracking

### Data Processing
- **yfinance** - Market data
- **pandas/numpy** - Data processing
- **FAISS** - Vector search
- **SQLite** - Database

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **Bootstrap 5** - UI framework
- **Chart.js** - Data visualization (ETF Dashboard)
- **D3.js** - Advanced data visualization
- **Modular architecture** - Component-based design

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server (optional, for caching)
- Polygon.io API key (for live market data)
- OpenRouter API key (for AI features)
- AWS account (for Market Pulse features: S3, Lambda, IAM)

### Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd Tokimeki
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Set environment variables or edit config.py
export POLYGON_API_KEY="your_polygon_api_key"
export OPENROUTER_API_KEY="your_openrouter_api_key"
export REDIS_URL="redis://localhost:6379"  # Optional

# Market Pulse (optional)
export AWS_S3_PULSE_BUCKET="your-s3-bucket-name"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_REGION="us-east-2"
```

5. **Initialize database**
```bash
python3 scripts/init_database.py
python3 scripts/init_golf_database.py  # Optional
python3 scripts/init_simulation_db.py  # Optional
```

6. **Start application**
```bash
python3 main.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Open browser**
```
http://localhost:8000
```

## 📈 API Endpoints

### Core Services
- **AI Chat**: `/api/v1/chat` - Interactive AI conversations
- **Market Data**: `/api/v1/stocks` - Stock market information
- **RAG System**: `/api/v1/rag` - Document analysis
- **Speech Processing**: `/api/v1/speech` - Audio analysis
- **Sentiment Analysis**: `/api/v1/sentiment` - Text sentiment
- **System Monitoring**: `/api/v1/monitoring` - Performance metrics
- **WebSocket**: `/ws` - Real-time data streaming

### ETF Dashboard
- **Dashboard Data**: `/api/v1/etf/dashboard/data` - Multi-ETF comparison
- **ETF Info**: `/api/v1/etf/info/{symbol}` - Basic ETF information
- **Holdings**: `/api/v1/etf/holdings/{symbol}` - ETF holdings data
- **Comparison**: `/api/v1/etf/comparison` - Compare multiple ETFs
- **Risk Metrics**: `/api/v1/etf/risk-metrics/{symbol}` - Risk analysis
- **Technical Indicators**: `/api/v1/etf/technical-indicators/{symbol}` - Technical analysis
- **Search**: `/api/v1/etf/search` - Search ETF tickers

### Consumer Options Dashboard
- **Chain Data**: `/api/v1/consumeroptions/chain` - Options chain data
- **Analytics**: `/api/v1/consumeroptions/analytics` - Call/Put ratios, IV analysis
- **Dashboard**: `/api/v1/consumeroptions/dashboard/data/{ticker}` - Complete dashboard data
- **Simulation**: `/api/v1/consumeroptions/simulation` - Volatility regime and signals

### AAPL Analysis
- **Stock Prices**: `/api/v1/aapl-analysis/prices/{ticker}` - Historical price data
- **Option Contracts**: `/api/v1/aapl-analysis/options/contracts/{ticker}` - Options chain
- **Backtests**: `/api/v1/aapl-analysis/backtest/*` - Strategy backtesting

### FutureQuant Trading
- **Data**: `/api/v1/futurequant/data` - Market data ingestion
- **Features**: `/api/v1/futurequant/features` - Feature engineering
- **Models**: `/api/v1/futurequant/models` - ML model management
- **Signals**: `/api/v1/futurequant/signals` - Trading signals
- **Backtests**: `/api/v1/futurequant/backtests` - Strategy backtesting
- **Paper Trading**: `/api/v1/futurequant/paper-trading` - Simulation

### FutureExploratorium
- **Core**: `/api/v1/futureexploratorium/core` - Core functionality
- **Dashboard**: `/api/v1/futureexploratorium/dashboard` - Real-time data
- **Analytics**: `/api/v1/futureexploratorium/analytics` - Market analysis
- **Strategy**: `/api/v1/futureexploratorium/strategy` - Strategy tools
- **Events**: `/api/v1/futureexploratorium/events` - Event analysis

### Mini Golf Strategy
- **Core**: `/api/v1/minigolfstrategy/core` - Core functionality
- **Strategy**: `/api/v1/minigolfstrategy/strategy` - Strategy optimization
- **Courses**: `/api/v1/minigolfstrategy/courses` - Course search
- **Factor Analysis**: `/api/v1/minigolfstrategy/factor-analysis` - Conditions

### Simulation
- **Simulation**: `/api/v1/simulation/*` - Strategy simulation endpoints

### Market Pulse
- **Current Pulse**: `/api/v1/market-pulse/current` - Get current market pulse data
- **Today's Events**: `/api/v1/market-pulse/events/today` - Get today's pulse events
- **Compute Agent Data**: `/api/v1/market-pulse/compute-agent` - Get Compute Agent signals
- **Learning Agent Data**: `/api/v1/market-pulse/learning-agent` - Get Learning Agent predictions
- **Dual Agent Comparison**: `/api/v1/market-pulse/dual-agent` - Compare Compute vs Learning Agent signals

## 🔧 Configuration

### Environment Variables
```bash
# Required
POLYGON_API_KEY=your_polygon_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional
REDIS_URL=redis://localhost:6379
CACHE_TTL=300
RATE_LIMIT_PER_HOUR=50
RATE_LIMIT_PER_DAY=200
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### Data Sources
- **Primary**: Polygon.io (live market data for stocks, options, ETFs)
- **Fallback**: yfinance (historical ETF data when Polygon unavailable)
- **Caching**: Redis (optional, for performance optimization)
- **Storage**: AWS S3 (for Market Pulse raw and processed data)

### AI Models Supported
- **Mistral Small**: Primary AI model for analysis
- **DeepSeek R1**: Alternative AI model option
- **DeepSeek Chat**: Conversational AI capabilities
- **Llama 3.1 405B**: Large language model support

## 🚀 Deployment

### Market Pulse Deployment

Market Pulse requires AWS infrastructure setup:

1. **S3 Bucket**: Create S3 bucket for data storage
2. **Lambda Functions**: Deploy Compute Agent and Learning Agent
3. **IAM Permissions**: Configure IAM policies for S3 and Lambda access
4. **EventBridge**: Set up scheduled triggers (optional, for automation)

See [Market Pulse Deployment Guide](./docs/features/marketpulse/AWS-SETUP-DUAL-AGENT.md) for detailed instructions.

Quick start:
```bash
# Deploy Lambda functions
./scripts/deploy-lambda-functions.sh

# Trigger agents manually
python3 scripts/trigger_lambda_agents.py

# Start data collector
python3 scripts/start_data_collector.py
```

### Railway Deployment
```bash
# Deploy to Railway
railway login
railway link
railway up
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up --build
```

### Local Development
```bash
# Start with auto-reload
python3 main.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/core/
pytest tests/futurequant/
pytest tests/features/
pytest tests/simulation/
```

### Frontend Testing
```bash
# Open testing interface
http://localhost:8000/static/test-refactored.html
```

## 🤝 Development

### Frontend Development
The frontend uses a modular architecture:
- **Components**: Self-contained JavaScript classes
- **Utilities**: Shared functionality (cache, tabs, modals, loading)
- **Templates**: HTML component templates
- **Styles**: Modular CSS files

### Adding New Components
1. Create component class in `static/js/components/`
2. Create HTML template in `static/components/` (if needed)
3. Add component styles to `static/css/components.css`
4. Register component in `static/js/app.js` or `static/index.html`

### Backend Development
- **Service Layer Pattern**: Business logic in services
- **Dependency Injection**: Clean separation of concerns
- **Async/Await**: Non-blocking I/O throughout
- **Error Handling**: Comprehensive exception management
- **Data Source Prioritization**: Polygon.io → yfinance fallback

### Data Source Integration
- **Polygon.io**: Primary source for live data (real-time snapshots, no caching for live endpoints)
- **yfinance**: Fallback for historical data and when Polygon unavailable
- **Error Handling**: Graceful degradation with fallback mechanisms

## 📄 License

MIT License

## 🙏 Acknowledgments

- FastAPI & Uvicorn
- OpenRouter AI Models
- Polygon.io for live market data
- Redis & httpx
- yfinance & scikit-learn
- LangChain & FAISS
- PyTorch & Transformers
- Bootstrap, Chart.js & D3.js

## 📞 Support

For issues and questions:
- Check the API documentation at `/docs` when running
- Review the test interface at `/static/test-refactored.html`
- Examine logs for detailed error information
- See `docs/ETF_DATA_SOURCES.md` for ETF data source details
