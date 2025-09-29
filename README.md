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
│   │   └── aapl_analysis_models.py # AAPL analysis data models
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
│   │   └── minigolfstrategy/       # Mini Golf Strategy services
│   │       ├── core_service.py
│   │       ├── strategy_service.py
│   │       ├── factor_analysis_service.py
│   │       └── clients/
│   │           └── golfcourse_api.py
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
├── data/                           # Data storage
│   └── databases/
│       └── futurequant_trader.db
├── deployment/                     # Deployment configuration
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── railway.json
├── scripts/                        # Utility scripts
│   ├── cleanup_old_models.py
│   ├── demo_paper_trading.py
│   ├── init_database.py
│   └── init_golf_database.py
└── tests/                          # Test suite
    ├── core/
    ├── features/
    ├── futurequant/
    ├── market_data/
    └── strategies/
```

### Frontend Structure (Modular)

```
static/
├── index.html                      # Main application interface
├── main.js                         # Core JavaScript functionality
├── favicon.ico                     # Site icon
├── validate_js.py                  # JavaScript validation utility
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
│       ├── futures-exploratorium.js
│       ├── futurequant-dashboard.js
│       ├── minigolf-strategy.js
│       ├── rag-bi.js
│       ├── chatbot.js
│       ├── ai-platform-comparables.js
│       ├── market-overtime.js
│       ├── volatility-explorer.js
│       └── hf-signal-tool.js
├── components/                    # HTML component templates
│   ├── minigolf-strategy.html
│   └── futurequant-dashboard.html
├── img/                           # Images and icons
│   ├── cute.png
│   ├── demo.png
│   ├── handsome.png
│   └── lionPixel.png
└── futures-exploratorium-react/   # React components
    └── package.json
```

## 📚 Learning Modules

### 1. **AAPL Stock vs Options Analysis**
- Interactive comparison tool with strategy selector dropdown
- Backtesting simulations with historical data
- Visual P&L tracking and educational metrics

### 2. **Quantitative Finance (FutureQuant)**
- Paper trading simulator and backtesting framework
- Machine learning experiments and risk analysis tools
- Performance dashboards and feature engineering

### 3. **Market Intelligence (FutureExploratorium)**
- Event analysis and strategy development tools
- Market data visualization and analytics dashboard

### 4. **Academic Research Tools**
- AI-powered research assistant with RAG system
- Market data APIs and statistical analysis tools

## 🔧 Technical Stack

### Backend
- **FastAPI** - Modern, high-performance web framework
- **SQLAlchemy** - Database ORM
- **Redis** - Caching layer
- **httpx** - Async HTTP client
- **Pydantic** - Data validation

### AI/ML
- **OpenRouter** - AI model access
- **LangChain** - RAG system
- **scikit-learn** - Machine learning
- **PyTorch** - Deep learning
- **VectorBT** - Quantitative analysis
- **MLflow** - Model tracking

### Data
- **yfinance** - Market data
- **pandas/numpy** - Data processing
- **FAISS** - Vector search
- **SQLite** - Database

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **Bootstrap 5** - UI framework
- **D3.js** - Data visualization
- **Modular architecture** - Component-based design

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server (optional)
- OpenRouter API key

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
# Edit config.py and set your API keys
OPENROUTER_API_KEY = "your_openrouter_api_key_here"
```

5. **Initialize database**
```bash
python3 scripts/init_database.py
```

6. **Start application**
```bash
python3 main.py
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

## 🔧 Configuration

### Environment Variables
```bash
OPENROUTER_API_KEY=your_api_key_here
REDIS_URL=redis://localhost:6379
CACHE_TTL=300
RATE_LIMIT_PER_HOUR=50
RATE_LIMIT_PER_DAY=200
DEBUG=false
HOST=0.0.0.0
PORT=8080
```

### AI Models Supported
- **Mistral Small**: Primary AI model for analysis
- **DeepSeek R1**: Alternative AI model option
- **DeepSeek Chat**: Conversational AI capabilities
- **Llama 3.1 405B**: Large language model support

## 🚀 Deployment

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
2. Create HTML template in `static/components/`
3. Add component styles to `static/css/components.css`
4. Register component in `static/js/app.js`

### Backend Development
- **Service Layer Pattern**: Business logic in services
- **Dependency Injection**: Clean separation of concerns
- **Async/Await**: Non-blocking I/O throughout
- **Error Handling**: Comprehensive exception management

## 📄 License

MIT License

## 🙏 Acknowledgments

- FastAPI & Uvicorn
- OpenRouter AI Models
- Redis & httpx
- yfinance & scikit-learn
- LangChain & FAISS
- PyTorch & Transformers
- Bootstrap & D3.js

## 📞 Support

For issues and questions:
- Check the API documentation at `/docs` when running
- Review the test interface at `/static/test-refactored.html`
- Examine logs for detailed error information
