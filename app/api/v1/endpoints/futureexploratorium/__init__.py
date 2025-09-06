"""
FutureExploratorium API Endpoints
Independent API layer for the FutureExploratorium service
"""
from .core import router as core_router
from .dashboard import router as dashboard_router
from .analytics import router as analytics_router
from .strategy import router as strategy_router

__all__ = [
    "core_router",
    "dashboard_router", 
    "analytics_router",
    "strategy_router"
]
