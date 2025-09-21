"""
Mini Golf Strategy API Endpoints Package
"""
from .core import router as core_router
from .courses import router as courses_router
from .strategy import router as strategy_router
from .factor_analysis import router as factor_analysis_router

__all__ = ["core_router", "courses_router", "strategy_router", "factor_analysis_router"]
