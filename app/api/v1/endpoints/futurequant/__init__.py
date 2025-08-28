"""
FutureQuant Trader API Endpoints
"""
from .data import router as data_router
from .features import router as features_router
from .models import router as models_router
from .signals import router as signals_router
from .backtests import router as backtests_router
from .paper_trading import router as paper_trading_router

__all__ = [
    "data_router",
    "features_router", 
    "models_router",
    "signals_router",
    "backtests_router",
    "paper_trading_router"
]
