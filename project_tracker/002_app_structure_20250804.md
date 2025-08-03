# Tokimeki App Structure (2025-08-04)

This document describes the current structure of the Tokimeki project as of **2025-08-04**. Each major script and folder is briefly explained for clarity and onboarding.

---

## Current App Structure (Tree View)

```
Tokimeki/
├── main.py                           # Railway/FastAPI entry point
├── Procfile                          # Railway deployment config
├── requirements_fastapi.txt           # FastAPI dependencies
├── app/
│   ├── __init__.py                   # App package init
│   ├── main.py                       # Main FastAPI app (896 lines)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings & configuration
│   │   ├── dependencies.py           # Dependency injection
│   │   └── middleware.py             # CORS, rate limiting
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py            # OpenRouter API integration
│   │   ├── stock_service.py         # yfinance data fetching
│   │   ├── cache_service.py         # Redis caching
│   │   └── usage_service.py         # Request tracking
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                  # API dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py               # API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── chat.py          # Chat endpoints
│   │           ├── stocks.py        # Stock endpoints
│   │           ├── sentiment.py     # Sentiment analysis
│   │           ├── speech.py        # Speech processing
│   │           └── monitoring.py    # Monitoring endpoints
│   └── utils/
│       ├── async_cache.py           # Cache utilities
│       └── async_usage_tracker.py   # Usage tracking utilities
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # pytest configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_ai_service.py       # AI service tests
│   │   ├── test_stock_service.py    # Stock service tests
│   │   ├── test_cache_service.py    # Cache service tests
│   │   └── test_usage_service.py    # Usage service tests
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py    # API endpoint tests
│   │   ├── test_chat_integration.py # Chat integration tests
│   │   └── test_stock_integration.py # Stock integration tests
│   ├── e2e/
│   │   ├── __init__.py
│   │   └── test_deployment.py       # Deployment verification
│   ├── performance/
│   │   ├── __init__.py
│   │   ├── test_response_times.py   # Performance tests
│   │   └── test_concurrent_requests.py # Load tests
│   └── fixtures/
│       ├── __init__.py
│       └── mock_data.py             # Test fixtures
├── static/                           # Static files (HTML, CSS, JS)
├── templates/                        # HTML templates
├── project_tracker/                  # Project documentation
│   ├── 001_fastapi_migration_plan_20250803.md
│   └── 002_app_structure_20250804.md
└── Legacy Files (can be removed):
    ├── app.py                        # Old Flask app
    ├── routes/                       # Old Flask routes
    └── requirements.txt              # Old Flask dependencies
```

---

