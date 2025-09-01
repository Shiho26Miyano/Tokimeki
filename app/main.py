import os
import logging
import numpy as np
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from app.core.config import settings
from app.core.middleware import setup_middleware
from app.core.dependencies import get_cache_service, get_usage_service, get_ai_service, get_stock_service
from app.api.v1.api import api_router
from app.services.ai_service import AsyncAIService
from app.services.stock_service import AsyncStockService
from app.services.usage_service import AsyncUsageService
from app.services.cache_service import AsyncCacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def auto_cleanup_models():
    """Automatically clean up old model files on server startup"""
    try:
        import os
        import re
        from datetime import datetime
        from pathlib import Path
        
        logger.info("Starting automatic model cleanup...")
        
        # Define the models directory
        models_dir = Path("models")
        
        if not models_dir.exists():
            logger.info("Models directory not found, skipping cleanup")
            return
        
        # Find all .joblib files
        model_files = list(models_dir.glob("*.joblib"))
        
        if not model_files:
            logger.info("No model files found, skipping cleanup")
            return
        
        logger.info(f"Found {len(model_files)} model files for cleanup")
        
        # Group models by type (symbol_modeltype_horizon)
        model_groups = {}
        
        for model_file in model_files:
            # Parse filename: ES=F_transformer_0.5m_20250831_224805.joblib
            filename = model_file.name
            
            # Use regex to extract parts more reliably
            pattern = r'^(.+)_(\d{8}_\d{6})\.joblib$'
            match = re.match(pattern, filename)
            
            if match:
                base_id = match.group(1)  # e.g., ES=F_transformer_0.5m
                timestamp_str = match.group(2)  # e.g., 20250831_224805
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if base_id not in model_groups:
                        model_groups[base_id] = []
                    
                    model_groups[base_id].append({
                        'file': model_file,
                        'timestamp': timestamp,
                        'filename': filename
                    })
                    
                except ValueError:
                    logger.warning(f"Could not parse timestamp from {filename}")
                    continue
            else:
                logger.warning(f"Could not parse filename format: {filename}")
                continue
        
        logger.info(f"Grouped into {len(model_groups)} model types")
        
        # For each group, keep only the most recent model
        total_removed = 0
        total_kept = 0
        
        for base_id, models in model_groups.items():
            if len(models) > 1:
                # Sort by timestamp (newest first)
                models.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Keep the newest one
                newest = models[0]
                older_models = models[1:]
                
                logger.info(f"{base_id}: Keeping {newest['filename']} (newest)")
                
                # Remove older models
                for old_model in older_models:
                    try:
                        os.remove(old_model['file'])
                        logger.info(f"Removed old model: {old_model['filename']}")
                        total_removed += 1
                    except OSError as e:
                        logger.error(f"Error removing {old_model['filename']}: {e}")
                
                total_kept += 1
            else:
                # Only one model of this type, keep it
                logger.info(f"{base_id}: Keeping {models[0]['filename']} (only one)")
                total_kept += 1
        
        logger.info(f"Model cleanup completed: {total_kept} kept, {total_removed} removed")
        
        # Show remaining models
        remaining_files = list(models_dir.glob("*.joblib"))
        if remaining_files:
            logger.info(f"Remaining models ({len(remaining_files)}):")
            for model_file in sorted(remaining_files):
                logger.info(f"  {model_file.name}")
                
    except Exception as e:
        logger.error(f"Error during automatic model cleanup: {e}")
        # Don't fail startup if cleanup fails

# Get the absolute path to the static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
logger.info(f"Static directory path: {STATIC_DIR}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Tokimeki FastAPI - Async AI and Stock Analysis Platform",
    version="1.0.0",
    debug=settings.debug
)

# Setup middleware
setup_middleware(app)

# Add exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting Tokimeki FastAPI application...")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API key configured: {bool(settings.openrouter_api_key)}")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"Port: {os.getenv('PORT', '8000')}")
        
        # Auto-cleanup old models on startup (non-blocking)
        try:
            await auto_cleanup_models()
        except Exception as cleanup_error:
            logger.warning(f"Model cleanup failed (non-critical): {cleanup_error}")
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Don't raise the error - let the app start even if cleanup fails
        logger.warning("Continuing with startup despite errors...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    logger.info("Shutting down Tokimeki FastAPI application...")
    from .core.dependencies import cleanup_http_client
    await cleanup_http_client()

# Mount static files with cache busting
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Add middleware to prevent caching of static files
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Add favicon route
@app.get("/favicon.ico")
async def favicon():
    try:
        favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
        logger.info(f"Serving favicon from: {favicon_path}")
        return FileResponse(favicon_path)
    except Exception as e:
        logger.error(f"Error serving favicon: {e}")
        return JSONResponse(status_code=404, content={"error": "Favicon not found"})

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    """Simple health check that responds immediately"""
    try:
        return {"status": "healthy", "timestamp": time.time(), "service": "Tokimeki"}
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}

# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Root endpoint removed - duplicate route

# FutureQuant dashboard route
@app.get("/futurequant")
async def futurequant_dashboard():
    try:
        dashboard_path = os.path.join(STATIC_DIR, "futurequant-enhanced.html")
        logger.info(f"Serving FutureQuant dashboard from: {dashboard_path}")
        return FileResponse(dashboard_path)
    except Exception as e:
        logger.error(f"Error serving FutureQuant dashboard: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": "Failed to serve FutureQuant dashboard", "details": str(e)}
        )

# Core app endpoints (not part of API v1)

# Stock endpoints moved to /api/v1/stocks/

# @app.get("/volatility_event_correlation")  # Moved to /api/v1/stocks/
async def get_volatility_event_correlation(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    window: int = 30,
    years: int = 2,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get volatility event correlation data"""
    start_time = time.time()
    
    try:
        # Set default dates if not provided
        if not start_date or not end_date:
            from datetime import datetime, timedelta
            end = datetime.now()
            start = end - timedelta(days=years*365)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        # Get stock data
        stock_data = await stock_service.get_stock_data(symbol, 365)
        
        if not stock_data or not stock_data.get('data'):
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        # Extract dates and prices
        dates = []
        for day in stock_data['data']:
            if hasattr(day['Date'], 'strftime'):
                dates.append(day['Date'].strftime('%Y-%m-%d'))
            else:
                # Handle ISO format dates
                date_str = str(day['Date'])
                if 'T' in date_str:
                    dates.append(date_str.split('T')[0])
                else:
                    dates.append(date_str)
        prices = [day['Close'] for day in stock_data['data']]
        
        if len(prices) < window:
            raise HTTPException(status_code=400, detail=f"Not enough data for rolling volatility (need at least {window} days)")
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        # Calculate rolling volatility
        rolling_vol = []
        for i in range(window-1, len(returns)):
            window_returns = returns[i-window+1:i+1]
            vol = np.std(window_returns) * np.sqrt(252) * 100
            rolling_vol.append(vol)
        
        # Pad with None values for the first window-1 days
        volatility = [None] * (window-1) + rolling_vol
        
        # Find minimum volatility period
        valid_start = int(len(volatility) * 0.1)
        valid_vols = [v for v in volatility[valid_start:] if v is not None]
        valid_dates = dates[valid_start:]
        
        min_vol = None
        min_vol_date = None
        if valid_vols:
            min_vol = min(valid_vols)
            min_idx = volatility[valid_start:].index(min_vol) + valid_start
            min_vol_date = dates[min_idx]
        
        # Create event titles (empty for now)
        event_titles = [[] for _ in dates]
        
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_event_correlation",
            response_time=response_time,
            success=True
        )
        
        return {
            "dates": dates,
            "volatility": volatility,
            "event_titles": event_titles,
            "min_vol": min_vol,
            "min_vol_date": min_vol_date
        }
        
    except Exception as e:
        logger.error(f"Volatility event correlation error: {e}")
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_event_correlation",
            response_time=response_time,
            success=False
        )
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/volatility_regime/analyze")  # Moved to /api/v1/stocks/
async def analyze_volatility_regime(
    request: Request,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze volatility regime for a stock"""
    start_time = time.time()
    
    try:
        # Parse request data
        data = await request.json()
        symbol = data.get("symbol", "AAPL")
        period = data.get("period", "1y")
        window = data.get("window", 30)
        
        logger.info(f"Volatility regime analysis request: symbol={symbol}, period={period}, window={window}")
        
        # Get stock data
        stock_data = await stock_service.get_stock_data(symbol, 365)
        
        if not stock_data or not stock_data.get('data'):
            logger.warning(f"No stock data available for {symbol}")
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        logger.info(f"Retrieved {len(stock_data['data'])} data points for {symbol}")
        
        # Calculate volatility metrics
        prices = [day['Close'] for day in stock_data['data']]
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        # Calculate rolling volatility
        import numpy as np
        rolling_vol = []
        for i in range(window, len(returns)):
            window_returns = returns[i-window:i]
            vol = np.std(window_returns) * np.sqrt(252) * 100
            rolling_vol.append(vol)
        
        # Determine regime
        avg_vol = np.mean(rolling_vol)
        current_vol = rolling_vol[-1] if rolling_vol else 0
        
        if current_vol > avg_vol * 1.5:
            regime = "High Volatility"
        elif current_vol < avg_vol * 0.7:
            regime = "Low Volatility"
        else:
            regime = "Normal Volatility"
        
        # Calculate regime statistics
        high_vol_periods = sum(1 for vol in rolling_vol if vol > avg_vol * 1.5)
        low_vol_periods = sum(1 for vol in rolling_vol if vol < avg_vol * 0.7)
        normal_vol_periods = len(rolling_vol) - high_vol_periods - low_vol_periods
        
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_regime_analyze",
            response_time=response_time,
            success=True
        )
        
        response_data = {
            "success": True,
            "symbol": symbol,
            "regime": regime,
            "current_volatility": round(current_vol, 2),
            "average_volatility": round(avg_vol, 2),
            "volatility_trend": "Increasing" if current_vol > avg_vol else "Decreasing",
            "regime_distribution": {
                "high_volatility_periods": high_vol_periods,
                "low_volatility_periods": low_vol_periods,
                "normal_volatility_periods": normal_vol_periods
            },
            "rolling_volatility": [round(v, 2) for v in rolling_vol[-50:]],  # Last 50 points
            "response_time": response_time
        }
        
        logger.info(f"Volatility regime response: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"Volatility regime analysis error: {e}")
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_regime_analyze",
            response_time=response_time,
            success=False
        )
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoints moved to /api/v1/chat/

# Compare models endpoint moved to /api/v1/chat/compare_models

# Models endpoint moved to /api/v1/chat/models

@app.post("/analyze_tweet")
async def analyze_tweet_endpoint(
    request: Request,
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze tweet sentiment"""
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            text = body.get("text", "")
        else:
            # Handle form data
            form_data = await request.form()
            text = form_data.get("text", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Simple sentiment analysis (placeholder)
        # In a real app, you'd use a proper sentiment analysis model
        positive_words = ["love", "great", "good", "amazing", "wonderful", "excellent", "fantastic"]
        negative_words = ["hate", "terrible", "bad", "awful", "horrible", "disappointing", "worst"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            label = "positive"
            confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            label = "negative"
            confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            label = "neutral"
            confidence = 0.5
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze_tweet",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "label": label,
            "confidence": confidence,
            "text": text,
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze_tweet",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Tweet analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stock_symbols")
async def get_stock_symbols_endpoint():
    """Get available stock symbols"""
    common_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "META", "name": "Meta Platforms Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "NFLX", "name": "Netflix Inc."},
        {"symbol": "AMD", "name": "Advanced Micro Devices Inc."},
        {"symbol": "INTC", "name": "Intel Corporation"}
    ]
    
    return {
        "success": True,
        "symbols": common_stocks
    }






# Root endpoint - serve the main HTML page (using absolute path)
@app.get("/")
async def root():
    try:
        index_path = os.path.join(STATIC_DIR, "index.html")
        logger.info(f"Serving index.html from: {index_path}")
        response = FileResponse(index_path)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": "Failed to serve main page", "details": str(e)}
        )

# Add missing root-level endpoints for backward compatibility
@app.post("/analyze")
async def root_analyze_endpoint(request: Request):
    """Root-level analyze endpoint for backward compatibility"""
    # Redirect to the proper API endpoint
    from .api.v1.endpoints.stocks import analyze_stock
    from .core.dependencies import get_stock_service, get_usage_service
    
    try:
        data = await request.json()
        stock_service = await get_stock_service()
        usage_service = await get_usage_service()
        
        # Create a mock request object
        from .api.v1.endpoints.stocks import StockAnalysisRequest
        stock_request = StockAnalysisRequest(**data)
        
        # Call the actual endpoint
        return await analyze_stock(stock_request, stock_service, usage_service)
    except Exception as e:
        logger.error(f"Root analyze endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def root_chat_endpoint(request: Request):
    """Root-level chat endpoint for backward compatibility"""
    # Redirect to the proper API endpoint
    from .api.v1.endpoints.chat import chat_with_ai
    from .core.dependencies import get_ai_service, get_usage_service
    
    try:
        data = await request.json()
        ai_service = await get_ai_service()
        usage_service = await get_usage_service()
        
        # Create a mock request object
        from .api.v1.endpoints.chat import ChatRequest
        chat_request = ChatRequest(**data)
        
        # Call the actual endpoint
        return await chat_with_ai(chat_request, ai_service, usage_service)
    except Exception as e:
        logger.error(f"Root chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/volatility_event_correlation")
async def root_volatility_endpoint(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    window: int = 30,
    years: int = 2
):
    """Root-level volatility endpoint for backward compatibility"""
    # Redirect to the proper API endpoint
    from .api.v1.endpoints.stocks import get_volatility_event_correlation
    from .core.dependencies import get_stock_service, get_usage_service
    
    try:
        stock_service = await get_stock_service()
        usage_service = await get_usage_service()
        
        # Call the actual endpoint
        return await get_volatility_event_correlation(
            symbol, start_date, end_date, window, years, stock_service, usage_service
        )
    except Exception as e:
        logger.error(f"Root volatility endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check moved to /api/v1/monitoring/health

# Test endpoint moved to /api/v1/monitoring/test

# Test API endpoint moved to /api/v1/monitoring/test-api

# Test comparison endpoint moved to /api/v1/monitoring/test-comparison



# Legacy health endpoint removed - duplicate route

@app.get("/available_tickers")
async def legacy_available_tickers(
    stock_service: AsyncStockService = Depends(get_stock_service)
):
    """Backward-compatible endpoint for available tickers"""
    tickers = await stock_service.get_available_tickers()
    return tickers

@app.get("/available_companies")
async def legacy_available_companies(
    stock_service: AsyncStockService = Depends(get_stock_service)
):
    """Backward-compatible endpoint for available companies"""
    companies = await stock_service.get_available_companies()
    return companies

@app.get("/stocks/history")
async def legacy_stock_history(
    symbols: str,
    days: int = 1095,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Backward-compatible endpoint mapping to /api/v1/stocks/history"""
    start_time = time.time()
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        result = await stock_service.get_stock_history(symbols=symbol_list, days=days)
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="stock_history_legacy",
            response_time=response_time,
            success=True
        )
        return result
    except Exception as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="stock_history_legacy",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/ai-platform-comparison")
async def get_ai_platform_comparison():
    """Get AI platform comparison data"""
    platforms = [
        {
            "name": "OpenRouter",
            "category": "API Gateway",
            "models": 100,
            "pricing": "Pay-per-token",
            "features": ["Multiple models", "Unified API", "Cost tracking"],
            "rating": 4.5
        },
        {
            "name": "Together.ai",
            "category": "Inference Platform",
            "models": 50,
            "pricing": "Pay-per-token",
            "features": ["Open models", "Custom training", "Deployment"],
            "rating": 4.3
        },
        {
            "name": "Hugging Face",
            "category": "Model Hub",
            "models": 1000,
            "pricing": "Free + Premium",
            "features": ["Model hosting", "Inference API", "Spaces"],
            "rating": 4.7
        }
    ]
    
    return {
        "success": True,
        "platforms": platforms
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 