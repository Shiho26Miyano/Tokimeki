"""
Mini Golf Strategy API Endpoints Package
"""
from .core import router as core_router
from .factor_analysis import router as factor_analysis_router

__all__ = ["core_router", "factor_analysis_router"]
