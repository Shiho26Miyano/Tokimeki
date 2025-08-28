"""
API v1 router configuration
"""
from fastapi import APIRouter
from .endpoints import chat, stocks, sentiment, speech, monitoring, rag, mnq, intention
from .endpoints.futurequant import (
    data_router, features_router, models_router, 
    signals_router, backtests_router, paper_trading_router
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(mnq.router, prefix="/mnq", tags=["mnq"])
api_router.include_router(intention.router, prefix="/intention", tags=["intention_interpreter_engine"])

# Include FutureQuant Trader endpoints
api_router.include_router(data_router, prefix="/futurequant/data", tags=["futurequant_data"])
api_router.include_router(features_router, prefix="/futurequant/features", tags=["futurequant_features"])
api_router.include_router(models_router, prefix="/futurequant/models", tags=["futurequant_models"])
api_router.include_router(signals_router, prefix="/futurequant/signals", tags=["futurequant_signals"])
api_router.include_router(backtests_router, prefix="/futurequant/backtests", tags=["futurequant_backtests"])
api_router.include_router(paper_trading_router, prefix="/futurequant/paper-trading", tags=["futurequant_paper_trading"])

# Add API version info
@api_router.get("/")
async def api_info():
    """API version information"""
    return {
        "version": "v1",
        "status": "active",
        "endpoints": {
            "chat": "/chat",
            "stocks": "/stocks", 
            "sentiment": "/sentiment",
            "speech": "/speech",
            "monitoring": "/monitoring",
            "rag": "/rag",
            "mnq": "/mnq",
            "intention": "/intention",
            "futurequant": {
                "data": "/futurequant/data",
                "features": "/futurequant/features",
                "models": "/futurequant/models",
                "signals": "/futurequant/signals",
                "backtests": "/futurequant/backtests",
                "paper_trading": "/futurequant/paper-trading"
            }
        }
    }

# Add model comparison endpoint
@api_router.get("/model-comparison")
async def get_model_comparison():
    """Get model comparison data"""
    models = [
        {
            "name": "Mistral Small",
            "provider": "Mistral AI",
            "context_window": "32K",
            "performance": "High",
            "model_size": "7B",
            "best_for": ["General purpose"],
            "strengths": ["Fast", "efficient", "good reasoning"],
            "note": "Excellent balance of speed and capability",
            "notes": "Excellent balance of speed and capability"
        },
        {
            "name": "DeepSeek Chat",
            "provider": "DeepSeek",
            "context_window": "128K",
            "performance": "Very High",
            "model_size": "67B",
            "best_for": ["Complex reasoning"],
            "strengths": ["Strong reasoning", "long context"],
            "note": "Best for complex tasks",
            "notes": "Best for complex tasks"
        },
        {
            "name": "Qwen 3 8B",
            "provider": "Alibaba",
            "context_window": "32K",
            "performance": "High",
            "model_size": "8B",
            "best_for": ["Code and reasoning"],
            "strengths": ["Good coding", "efficient"],
            "note": "Strong for technical tasks",
            "notes": "Strong for technical tasks"
        }
    ]
    
    return {
        "success": True,
        "models": models
    }

# Add test endpoint to verify API is working
@api_router.get("/test")
async def test_api():
    """Test endpoint to verify API is working"""
    return {
        "success": True,
        "message": "API is working",
        "timestamp": "2025-01-01",
        "endpoints": {
            "stocks": "/api/v1/stocks",
            "chat": "/api/v1/chat",
            "rag": "/api/v1/rag",
            "monitoring": "/api/v1/monitoring",
            "mnq": "/api/v1/mnq",
            "futurequant": "/api/v1/futurequant"
        }
    } 