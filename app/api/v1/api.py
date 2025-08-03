"""
API v1 router configuration
"""
from fastapi import APIRouter
from .endpoints import chat, stocks, monitoring, sentiment, speech

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])

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
            "monitoring": "/monitoring",
            "sentiment": "/sentiment",
            "speech": "/speech"
        }
    } 