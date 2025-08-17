# 🚀 Tokimeki - Experimental and Learning Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🏗️ Architecture

```
Tokimeki/
├── app/                          # FastAPI application core
│   ├── __init__.py
│   ├── main.py                   # FastAPI app configuration
│   ├── core/                     # Core system components
│   │   ├── config.py            # Application settings
│   │   ├── dependencies.py      # Dependency injection
│   │   └── middleware.py        # Request/response middleware
│   ├── services/                 # Business logic services
│   │   ├── ai_service.py        # AI integration (OpenRouter)
│   │   ├── mnq_investment_service.py  # Investment analysis service
│   │   ├── stock_service.py     # Market data service
│   │   ├── cache_service.py     # Redis caching layer
│   │   ├── rag_service.py       # RAG system service
│   │   └── usage_service.py     # Usage tracking and analytics
│   └── api/                     # REST API endpoints
│       └── v1/                  # API version 1
│           ├── api.py           # Main router configuration
│           └── endpoints/       # Feature-specific endpoints
│               ├── chat.py      # AI chat interface
│               ├── mnq.py       # Investment analysis endpoints
│               ├── stocks.py    # Market data endpoints
│               ├── rag.py       # RAG system endpoints
│               ├── speech.py    # Speech processing endpoints
│               ├── sentiment.py # Sentiment analysis endpoints
│               └── monitoring.py # System monitoring endpoints
├── static/                       # Frontend assets
│   ├── index.html               # Main application interface
│   ├── main.js                  # Core JavaScript functionality
│   ├── mnq-dashboard.js         # Dashboard interface
│   ├── style.css                # Application styling
│   └── img/                     # Images and icons
├── main.py                      # Application entry point
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis server
- MNQ futures data access

### Installation

1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Configure environment
5. Start application
6. Open browser

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


## 📈 Usage Examples

### API Endpoints

1. **AI Chat**: `/api/v1/chat` - Interactive AI conversations
2. **Market Data**: `/api/v1/stocks` - Stock market information
3. **Investment Analysis**: `/api/v1/mnq` - Investment strategy endpoints
4. **RAG System**: `/api/v1/rag` - Retrieval-augmented generation
5. **Speech Processing**: `/api/v1/speech` - Audio analysis
6. **Sentiment Analysis**: `/api/v1/sentiment` - Text sentiment processing
7. **System Monitoring**: `/api/v1/monitoring` - Performance metrics

## 🔬 Technical Details

### Backend Design Framework
- **FastAPI Architecture**: Modern, high-performance web framework with automatic API documentation
- **Async/Await Pattern**: Non-blocking I/O operations for improved scalability
- **Dependency Injection**: Clean separation of concerns with centralized dependency management
- **Middleware Stack**: CORS, rate limiting, and logging middleware
- **Service Layer Pattern**: Business logic separated into dedicated service modules
- **OpenRouter Integration**: AI model access through OpenRouter API

### Optimization Technologies
- **Redis Caching**: In-memory caching for frequently accessed data with configurable TTL
- **Async HTTP Client**: httpx with HTTP/2 support for external API calls
- **Rate Limiting**: Built-in rate limiting with slowapi integration
- **Data Preprocessing**: Optimized data structures and algorithms
- **Memory Management**: Efficient memory usage patterns and garbage collection
- **Performance Monitoring**: Real-time metrics and performance analytics

### AI Models Supported
- **Mistral Small**: Primary AI model for analysis
- **DeepSeek R1**: Alternative AI model option
- **DeepSeek Chat**: Conversational AI capabilities
- **Llama 3.1 405B**: Large language model support

## 🤝 Contributing

### Development Setup
```bash
pip install -r requirements-dev.txt
pytest tests/
black app/ static/
```

## 📄 License

MIT License

## 🙏 Acknowledgments

- FastAPI & Uvicorn
- OpenRouter AI Models
- Redis & httpx
- yfinance & scikit-learn
- LangChain & FAISS
- PyTorch & Transformers

## 📞 Support

- [Wiki](https://github.com/yourusername/tokimeki/wiki)
- [Issues](https://github.com/yourusername/tokimeki/issues)
- [Discussions](https://github.com/yourusername/tokimeki/discussions)
