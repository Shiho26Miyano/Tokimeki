"""
Quantitative Analysis API Endpoints
Integrates VectorBT, QF-Lib, and Lean services
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.futurequant.unified_quant_service import FutureQuantUnifiedService
from app.services.futurequant.vectorbt_service import FutureQuantVectorBTService
from app.services.futurequant.qflib_service import FutureQuantQFLibService
from app.services.futurequant.lean_service import FutureQuantLeanService

router = APIRouter()
unified_service = FutureQuantUnifiedService()
vectorbt_service = FutureQuantVectorBTService()
qflib_service = FutureQuantQFLibService()
lean_service = FutureQuantLeanService()

@router.post("/comprehensive-analysis")
async def run_comprehensive_analysis(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    analysis_types: List[str],
    custom_params: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Run comprehensive analysis using all three libraries"""
    try:
        result = await unified_service.run_comprehensive_analysis(
            strategy_id, start_date, end_date, symbols, analysis_types, custom_params
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vectorbt-backtest")
async def run_vectorbt_backtest(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    strategy_type: str = Query("momentum", description="Strategy type: momentum, mean_reversion, trend_following, statistical_arbitrage"),
    custom_params: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Run VectorBT backtest for a strategy"""
    try:
        result = await vectorbt_service.run_vectorbt_backtest(
            strategy_id, start_date, end_date, symbols, strategy_type, custom_params
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "VectorBT backtest failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/qflib-analysis")
async def run_qflib_analysis(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    analysis_type: str = Query("risk_metrics", description="Analysis type: risk_metrics, factor_analysis, portfolio_optimization"),
    db: Session = Depends(get_db)
):
    """Run QF-Lib analysis for a strategy"""
    try:
        result = await qflib_service.run_qflib_analysis(
            strategy_id, start_date, end_date, symbols, analysis_type
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "QF-Lib analysis failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lean-backtest")
async def run_lean_backtest(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    strategy_code: str,
    custom_config: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Run Lean backtest for a strategy"""
    try:
        result = await lean_service.run_lean_backtest(
            strategy_id, start_date, end_date, symbols, strategy_code, custom_config
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Lean backtest failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio-analysis/{backtest_id}")
async def get_portfolio_analysis(
    backtest_id: int,
    analysis_type: str = Query("vectorbt", description="Analysis type: vectorbt, qflib, lean"),
    db: Session = Depends(get_db)
):
    """Get detailed portfolio analysis for a backtest"""
    try:
        if analysis_type == "vectorbt":
            result = await vectorbt_service.get_portfolio_analysis(backtest_id)
        elif analysis_type == "qflib":
            result = await qflib_service.get_portfolio_analysis(backtest_id)
        elif analysis_type == "lean":
            result = await lean_service.get_lean_analysis(backtest_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/benchmark-comparison")
async def run_benchmark_comparison(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    benchmark_symbol: str = "SPY",
    db: Session = Depends(get_db)
):
    """Run benchmark comparison across all three libraries"""
    try:
        result = await unified_service.run_benchmark_comparison(
            strategy_id, start_date, end_date, symbols, benchmark_symbol
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Benchmark comparison failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-strategies")
async def get_available_strategies():
    """Get available strategy types for each library"""
    return {
        "vectorbt": [
            "momentum",
            "mean_reversion", 
            "trend_following",
            "statistical_arbitrage"
        ],
        "qflib": [
            "risk_metrics",
            "factor_analysis",
            "portfolio_optimization"
        ],
        "lean": [
            "algorithmic_trading"
        ]
    }

@router.get("/library-info")
async def get_library_info():
    """Get information about the integrated libraries"""
    return {
        "vectorbt": {
            "description": "Vectorized backtesting and analysis library",
            "version": "0.25.4",
            "features": [
                "Fast vectorized operations",
                "Multiple strategy types",
                "Advanced portfolio analysis",
                "Risk metrics calculation"
            ]
        },
        "qf-lib": {
            "description": "Quantitative Finance Library for risk and factor analysis",
            "version": "1.0.0",
            "features": [
                "Risk metrics calculation",
                "Factor analysis",
                "Portfolio optimization",
                "Statistical models"
            ]
        },
        "lean": {
            "description": "QuantConnect LEAN Engine for algorithmic trading",
            "version": "1.0.0",
            "features": [
                "Algorithmic trading simulation",
                "Real-time data processing",
                "Strategy execution",
                "Performance tracking"
            ]
        }
    }
