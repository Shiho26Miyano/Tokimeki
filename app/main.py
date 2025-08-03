import os
import logging
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
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get volatility event correlation data"""
    start_time = time.time()
    
    try:
        data = await stock_service.get_stock_data(symbol, 365)
        
        if data is None:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        # Calculate volatility (simplified)
        prices = [day['Close'] for day in data['data']]
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        volatility = sum(returns) / len(returns) if returns else 0
        
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_analysis",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "volatility": volatility,
            "data_points": len(data['data']),
            "response_time": response_time
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="volatility_analysis",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Volatility analysis error: {e}")
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
        
        # Make async API call
        result = await ai_service.chat(
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
        
        return {
            "success": True,
            "response": result["response"],
            "model": result["model"],
            "usage": result["usage"],
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="chat",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare_models")
async def compare_models_endpoint(
    request: Request,
    ai_service: AsyncAIService = Depends(get_ai_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Compare multiple AI models"""
    start_time = time.time()
    
    try:
        # Parse form data
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
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/analyze_playbook")
async def analyze_playbook_endpoint(
    request: Request,
    stock_service: AsyncStockService = Depends(get_stock_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Analyze stock using investment playbooks"""
    start_time = time.time()
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            symbol = body.get("symbol", "").upper()
            playbook_name = body.get("playbook_name", "Value Investing")
        else:
            # Handle form data
            form_data = await request.form()
            symbol = form_data.get("symbol", "").upper()
            playbook_name = form_data.get("playbook_name", "Value Investing")
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Get stock data
        data = await stock_service.get_stock_data(symbol, 365)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        # Get stock info
        stock_info = await stock_service.get_stock_info(symbol)
        
        # Simple playbook analysis
        decision = "HOLD"
        reasons = []
        
        if playbook_name == "Value Investing":
            if stock_info and stock_info.get("pe_ratio", 0) < 15:
                decision = "BUY"
                reasons.append("Low P/E ratio indicates undervaluation")
            else:
                decision = "HOLD"
                reasons.append("P/E ratio is not in value territory")
                
        elif playbook_name == "Growth Investing":
            # Simple growth analysis based on price momentum
            prices = [day['Close'] for day in data['data']]
            recent_return = ((prices[-1] / prices[-30]) - 1) * 100 if len(prices) >= 30 else 0
            
            if recent_return > 10:
                decision = "BUY"
                reasons.append("Strong recent price momentum")
            else:
                decision = "HOLD"
                reasons.append("Moderate growth momentum")
                
        elif playbook_name == "Dividend Investing":
            if stock_info and stock_info.get("dividend_yield", 0) > 3:
                decision = "BUY"
                reasons.append("High dividend yield")
            else:
                decision = "HOLD"
                reasons.append("Dividend yield below threshold")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze_playbook",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "playbook": {
                "name": playbook_name,
                "role": f"{playbook_name} Analyst",
                "philosophy": f"Apply {playbook_name} principles to evaluate {symbol}"
            },
            "decision": decision,
            "reasons": reasons,
            "stock_data": stock_info or {},
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="analyze_playbook",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Playbook analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playbooks")
async def get_playbooks():
    """Get investment playbooks"""
    playbooks = [
        {
            "name": "Value Investing",
            "description": "Find undervalued stocks with strong fundamentals",
            "criteria": ["Low P/E ratio", "High dividend yield", "Strong balance sheet"],
            "confidence": 0.85
        },
        {
            "name": "Growth Investing",
            "description": "Invest in companies with high growth potential",
            "criteria": ["High revenue growth", "Strong market position", "Innovation focus"],
            "confidence": 0.78
        },
        {
            "name": "Dividend Investing",
            "description": "Focus on stocks with consistent dividend payments",
            "criteria": ["High dividend yield", "Dividend growth history", "Stable earnings"],
            "confidence": 0.92
        }
    ]
    
    return playbooks

# Root endpoint - serve the main HTML page
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

# Test endpoint
@app.get("/test")
async def test():
    return {"message": "Hello, FastAPI world!"}

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