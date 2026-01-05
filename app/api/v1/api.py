"""
API v1 router configuration
"""
from fastapi import APIRouter
from .endpoints import chat, stocks, sentiment, speech, monitoring, rag, aapl_analysis
from .endpoints.futurequant import (
    data_router, features_router, models_router, 
    signals_router, backtests_router, paper_trading_router
)
from .endpoints.futureexploratorium import (
    core_router, dashboard_router, analytics_router, strategy_router
)
from .endpoints.futureexploratorium.event_analysis import router as event_analysis_router
from .endpoints.minigolfstrategy import (
    core_router as minigolf_core_router,
    courses_router as minigolf_courses,
    strategy_router as minigolf_strategy,
    factor_analysis_router
)
from .endpoints.consumeroptions import (
    chain_router, analytics_router as consumeroptions_analytics_router, 
    dashboard_router as consumeroptions_dashboard_router
)
from .endpoints.consumeroptions import simulation as consumeroptions_simulation
from .endpoints import quantitative_analysis, websocket, simulation, etf

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(aapl_analysis.router, prefix="/aapl-analysis", tags=["aapl_analysis"])


# Include FutureQuant Trader endpoints
api_router.include_router(data_router, prefix="/futurequant/data", tags=["futurequant_data"])
api_router.include_router(features_router, prefix="/futurequant/features", tags=["futurequant_features"])
api_router.include_router(models_router, prefix="/futurequant/models", tags=["futurequant_models"])
api_router.include_router(signals_router, prefix="/futurequant/signals", tags=["futurequant_signals"])
api_router.include_router(backtests_router, prefix="/futurequant/backtests", tags=["futurequant_backtests"])
api_router.include_router(paper_trading_router, prefix="/futurequant/paper-trading", tags=["futurequant_paper_trading"])

# Include FutureExploratorium endpoints (separate service)
api_router.include_router(core_router, prefix="/futureexploratorium/core", tags=["futureexploratorium_core"])
api_router.include_router(dashboard_router, prefix="/futureexploratorium/dashboard", tags=["futureexploratorium_dashboard"])
api_router.include_router(analytics_router, prefix="/futureexploratorium/analytics", tags=["futureexploratorium_analytics"])
api_router.include_router(strategy_router, prefix="/futureexploratorium/strategy", tags=["futureexploratorium_strategy"])
api_router.include_router(event_analysis_router, prefix="/futureexploratorium/events", tags=["futureexploratorium_events"])

# Include Mini Golf Strategy endpoints
api_router.include_router(minigolf_core_router, prefix="/minigolfstrategy/core", tags=["minigolfstrategy_core"])
api_router.include_router(minigolf_strategy, prefix="/minigolfstrategy", tags=["minigolfstrategy_strategy"])
api_router.include_router(minigolf_courses, prefix="/minigolfstrategy", tags=["minigolfstrategy_courses"])
api_router.include_router(factor_analysis_router, prefix="/minigolfstrategy/factor-analysis", tags=["minigolfstrategy_factor_analysis"])

# Include Consumer Options Sentiment endpoints
api_router.include_router(chain_router, prefix="/consumeroptions/chain", tags=["consumeroptions_chain"])
api_router.include_router(consumeroptions_analytics_router, prefix="/consumeroptions/analytics", tags=["consumeroptions_analytics"])
api_router.include_router(consumeroptions_dashboard_router, prefix="/consumeroptions/dashboard", tags=["consumeroptions_dashboard"])
api_router.include_router(consumeroptions_simulation.router, prefix="/consumeroptions", tags=["consumeroptions_simulation"])

# Include ETF Dashboard endpoints
api_router.include_router(etf.router, prefix="/etf", tags=["etf"])

# Include Quantitative Analysis endpoints
api_router.include_router(quantitative_analysis.router, prefix="/quantitative-analysis", tags=["quantitative_analysis"])

# Include WebSocket endpoints
api_router.include_router(websocket.router, tags=["websocket"])

# Include Simulation endpoints
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])

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
            "aapl_analysis": "/aapl-analysis",
    
            "futurequant": {
                "data": "/futurequant/data",
                "features": "/futurequant/features",
                "models": "/futurequant/models",
                "signals": "/futurequant/signals",
                "backtests": "/futurequant/backtests",
                "paper_trading": "/futurequant/paper-trading"
            },
            "futureexploratorium": {
                "core": "/futureexploratorium/core",
                "dashboard": "/futureexploratorium/dashboard",
                "analytics": "/futureexploratorium/analytics",
                "strategy": "/futureexploratorium/strategy",
                "events": "/futureexploratorium/events"
            },
            "minigolfstrategy": {
                "core": "/minigolfstrategy/core",
                "strategy": "/minigolfstrategy/strategy",
                "courses": "/minigolfstrategy/courses"
            },
            "consumeroptions": {
                "chain": "/consumeroptions/chain",
                "analytics": "/consumeroptions/analytics",
                "dashboard": "/consumeroptions/dashboard"
            },
            "etf": {
                "dashboard": "/etf/dashboard",
                "info": "/etf/info",
                "holdings": "/etf/holdings",
                "comparison": "/etf/comparison",
                "risk_metrics": "/etf/risk-metrics",
                "technical_indicators": "/etf/technical-indicators"
            },
            "quantitative_analysis": "/quantitative-analysis",
            "websocket": "/ws",
            "simulation": {
                "explain": "/simulation/explain",
                "regime": "/simulation/regime",
                "diagnostics": "/simulation/diagnostics",
                "pipeline": "/simulation/pipeline"
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
            "futurequant": "/api/v1/futurequant",
            "futureexploratorium": "/api/v1/futureexploratorium",
            "minigolfstrategy": "/api/v1/minigolfstrategy"
        }
    } 