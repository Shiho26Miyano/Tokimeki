import os
import logging
import numpy as np
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from .core.config import settings
from .core.middleware import setup_middleware
from .core.dependencies import get_cache_service, get_usage_service, get_ai_service, get_stock_service
# from .api.v1.api import api_router  # Commented out to avoid conflicts
from .services.ai_service import AsyncAIService
from .services.stock_service import AsyncStockService
from .services.usage_service import AsyncUsageService
from .services.cache_service import AsyncCacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add favicon route
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

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

# Include API router - commented out to avoid conflicts
# app.include_router(api_router, prefix="/api/v1")

# Direct endpoints to match original Flask app
@app.get("/available_tickers")
async def get_available_tickers():
    """Get list of available tickers"""
    tickers = [
        "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC",
        "BRK-B", "JNJ", "V", "JPM", "WMT", "PG", "KO", "XOM", "SPY", "QQQ", "VOO",
        "ARKK", "EEM", "XLF", "ES=F", "NQ=F", "YM=F", "RTY=F", "MES=F", "MNQ=F",
        "MYM=F", "M2K=F", "GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F", "ZC=F",
        "ZS=F", "ZW=F", "VX=F", "BTC=F", "ETH=F"
    ]
    
    return {
        "success": True,
        "tickers": tickers
    }

@app.get("/available_companies")
async def get_available_companies():
    """Get list of available companies"""
    companies = [
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
    
    return companies

@app.get("/stocks/history")
async def get_stock_history(
    symbols: str,
    days: int = 7,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get historical stock data"""
    start_time = time.time()
    
    try:
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        # Get historical data using the correct method
        result = await stock_service.get_stock_history(
            symbols=symbol_list,
            days=days
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="stock_history",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="stock_history",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Stock history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_stock_endpoint(
    request: Request,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze stock using trading strategies"""
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            symbol = body.get("symbol", "").upper()
            strategy = body.get("strategy", "trend")
            period = body.get("period", "1y")
        else:
            # Handle form data
            form_data = await request.form()
            symbol = form_data.get("symbol", "").upper()
            strategy = form_data.get("strategy", "trend")
            period = form_data.get("period", "1y")
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Get stock data and perform analysis
        result = await stock_service.analyze_stock(
            symbol=symbol,
            strategy=strategy,
            period=period
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "strategy": strategy,
            "period": period,
            "latest_signals": result.get("latest_signals", {}),
            "metrics": result.get("metrics", {}),
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Stock analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/volatility_event_correlation")
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

@app.post("/volatility_regime/analyze")
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

# Chat endpoints to match original Flask app
@app.post("/chat")
async def chat_endpoint(
    request: Request,
    ai_service: AsyncAIService = Depends(get_ai_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Main chat endpoint - handles both JSON and form data"""
    start_time = time.time()
    
    # Debug: Check API key status
    logger.info(f"Chat endpoint - API key configured: {bool(ai_service.api_key)}")
    logger.info(f"Chat endpoint - API key length: {len(ai_service.api_key) if ai_service.api_key else 0}")
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            message = body.get("message", "")
            model = body.get("model", "mistral-small")
            temperature = float(body.get("temperature", 0.7))
            max_tokens = int(body.get("max_tokens", 1000))
        else:
            # Handle form data (like original Flask app)
            form_data = await request.form()
            message = form_data.get("message", "")
            model = form_data.get("model", "mistral-small")
            temperature = float(form_data.get("temperature", 0.7))
            max_tokens = int(form_data.get("max_tokens", 1000))
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Make async API call with enhanced stock analysis
        result = await ai_service.chat_with_stock_analysis(
            message=message,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="chat",
            model=model,
            response_time=response_time,
            success=True
        )
        
        response_data = {
            "success": True,
            "response": result["response"],
            "model": result["model"],
            "usage": result["usage"],
            "response_time": response_time
        }
        
        # Add stock analysis data if available
        if "stock_analysis" in result:
            response_data["stock_analysis"] = result["stock_analysis"]
            response_data["symbol_analyzed"] = result.get("symbol_analyzed")
        
        return response_data
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        try:
            await usage_service.track_request(
                endpoint="chat",
                response_time=response_time,
                success=False,
                error=str(e)
            )
        except Exception as track_error:
            logger.error(f"Failed to track usage: {track_error}")
        
        logger.error(f"Chat error: {e}")
        
        # Provide more helpful error messages
        if "OpenRouter API key not configured" in str(e):
            error_detail = "OpenRouter API key is not configured. Please set the OPENROUTER_API_KEY environment variable."
        elif "API call failed" in str(e):
            error_detail = f"AI service error: {str(e)}"
        else:
            error_detail = str(e)
        
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/compare_models")
async def compare_models_endpoint(
    request: Request,
    ai_service: AsyncAIService = Depends(get_ai_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Compare multiple AI models"""
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            prompt = body.get("prompt", "")
            models = body.get("models", []) if body.get("models") else None
            temperature = float(body.get("temperature", 0.7))
            max_tokens = int(body.get("max_tokens", 1000))
        else:
            # Handle form data
            form_data = await request.form()
            prompt = form_data.get("prompt", "")
            models = form_data.get("models", "").split(",") if form_data.get("models") else None
            temperature = float(form_data.get("temperature", 0.7))
            max_tokens = int(form_data.get("max_tokens", 1000))
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Compare models concurrently
        results = await ai_service.compare_models(
            prompt=prompt,
            models=models,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="compare_models",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "results": results,
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="compare_models",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Model comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models_endpoint(
    ai_service: AsyncAIService = Depends(get_ai_service)
):
    """Get available AI models"""
    try:
        models = await ai_service.get_available_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return {
            "success": False,
            "error": str(e),
            "api_key_configured": bool(settings.openrouter_api_key)
        }

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

@app.get("/api/model-comparison")
async def get_model_comparison():
    """Get model comparison data"""
    models = [
        {
            "name": "Mistral Small",
            "provider": "Mistral AI",
            "context_window": "32K",
            "performance": "High",
            "model_size": "7B",
            "best_for": "General purpose",
            "strengths": "Fast, efficient, good reasoning",
            "notes": "Excellent balance of speed and capability"
        },
        {
            "name": "DeepSeek Chat",
            "provider": "DeepSeek",
            "context_window": "128K",
            "performance": "Very High",
            "model_size": "67B",
            "best_for": "Complex reasoning",
            "strengths": "Strong reasoning, long context",
            "notes": "Best for complex tasks"
        },
        {
            "name": "Qwen 3 8B",
            "provider": "Alibaba",
            "context_window": "32K",
            "performance": "High",
            "model_size": "8B",
            "best_for": "Code and reasoning",
            "strengths": "Good coding, efficient",
            "notes": "Strong for technical tasks"
        }
    ]
    
    return {
        "success": True,
        "models": models
    }




# Root endpoint - serve the main HTML page
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "app_name": settings.app_name,
        "debug": settings.debug,
        "api_key_configured": bool(settings.openrouter_api_key)
    }

# Test endpoint
@app.get("/test")
async def test():
    return {
        "message": "Hello, FastAPI world!",
        "api_key_configured": bool(settings.openrouter_api_key),
        "api_key_length": len(settings.openrouter_api_key) if settings.openrouter_api_key else 0,
        "debug_mode": settings.debug,
        "app_name": settings.app_name
    }

@app.get("/test-api")
async def test_api(
    ai_service: AsyncAIService = Depends(get_ai_service)
):
    """Test API call directly"""
    try:
        # Test a simple API call
        result = await ai_service.call_api(
            messages=[{"role": "user", "content": "Hello"}],
            model="mistral-small",
            temperature=0.7,
            max_tokens=50
        )
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "api_key_configured": bool(ai_service.api_key),
            "api_key_length": len(ai_service.api_key) if ai_service.api_key else 0
        }

# Serve monitoring page
@app.get("/monitoring")
async def monitoring():
    return FileResponse("templates/monitoring.html")

@app.get("/api/usage-stats")
async def get_usage_stats(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get usage statistics"""
    try:
        stats = await usage_service.get_hourly_stats()
        return {
            "success": True,
            "requests": stats.get("requests", 0),
            "total_cost": stats.get("total_cost", 0.0),
            "current_memory_percent": 75.0,  # Placeholder
            "uptime_seconds": time.time() - 1700000000,  # Placeholder
            "model_costs": stats.get("model_costs", {})
        }
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cache-status")
async def get_cache_status(
    cache_service: AsyncCacheService = Depends(get_cache_service)
):
    """Get cache status"""
    try:
        redis_connected = await cache_service.is_redis_connected()
        test_passed = await cache_service.test_connection()
        return {
            "success": True,
            "redis_connected": redis_connected,
            "test_passed": test_passed,
            "cache_ttl": 300
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-redis")
async def test_redis(
    cache_service: AsyncCacheService = Depends(get_cache_service)
):
    """Test Redis connection"""
    try:
        success = await cache_service.test_connection()
        return {
            "success": success,
            "error": None if success else "Redis connection failed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/cache-clear")
async def clear_cache(
    cache_service: AsyncCacheService = Depends(get_cache_service)
):
    """Clear all cache"""
    try:
        await cache_service.clear_all()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/reset-stats")
async def reset_stats(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Reset usage statistics"""
    try:
        await usage_service.reset_stats()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

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