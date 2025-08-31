"""
FutureQuant Trader Unified Quantitative Finance Service
Integrates VectorBT, QF-Lib, and Lean (QuantConnect)
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import asyncio

from app.models.trading_models import Symbol, Bar, Strategy, Backtest
from app.models.database import get_db
from .vectorbt_service import FutureQuantVectorBTService
from .qflib_service import FutureQuantQFLibService
from .lean_service import FutureQuantLeanService

logger = logging.getLogger(__name__)

class FutureQuantUnifiedService:
    """Unified service integrating VectorBT, QF-Lib, and Lean"""
    
    def __init__(self):
        self.vectorbt_service = FutureQuantVectorBTService()
        self.qflib_service = FutureQuantQFLibService()
        self.lean_service = FutureQuantLeanService()
        
        self.strategy_mapping = {
            "momentum": "vectorbt",
            "mean_reversion": "vectorbt", 
            "trend_following": "vectorbt",
            "statistical_arbitrage": "vectorbt",
            "risk_analysis": "qflib",
            "factor_analysis": "qflib",
            "portfolio_optimization": "qflib",
            "algorithmic_trading": "lean"
        }
    
    async def run_comprehensive_analysis(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str],
        analysis_types: List[str],
        custom_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run comprehensive analysis using all three libraries"""
        try:
            results = {}
            
            for analysis_type in analysis_types:
                if analysis_type in ["momentum", "mean_reversion", "trend_following", "statistical_arbitrage"]:
                    # Use VectorBT for strategy backtesting
                    result = await self.vectorbt_service.run_vectorbt_backtest(
                        strategy_id, start_date, end_date, symbols, analysis_type, custom_params
                    )
                    results[f"vectorbt_{analysis_type}"] = result
                    
                elif analysis_type in ["risk_metrics", "factor_analysis", "portfolio_optimization"]:
                    # Use QF-Lib for quantitative analysis
                    result = await self.qflib_service.run_qflib_analysis(
                        strategy_id, start_date, end_date, symbols, analysis_type
                    )
                    results[f"qflib_{analysis_type}"] = result
                    
                elif analysis_type == "algorithmic_trading":
                    # Use Lean for algorithmic trading simulation
                    strategy_code = custom_params.get("strategy_code", "") if custom_params else ""
                    result = await self.lean_service.run_lean_backtest(
                        strategy_id, start_date, end_date, symbols, strategy_code, custom_params
                    )
                    results["lean_algorithmic_trading"] = result
            
            # Generate unified report
            unified_report = await self._generate_unified_report(results, symbols, start_date, end_date)
            
            return {
                "success": True,
                "analysis_types": analysis_types,
                "results": results,
                "unified_report": unified_report,
                "symbols": symbols,
                "date_range": {"start": start_date, "end": end_date}
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_unified_report(self, results: Dict[str, Any], symbols: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate unified analysis report"""
        try:
            report = {
                "summary": {
                    "total_analyses": len(results),
                    "symbols_analyzed": symbols,
                    "date_range": {"start": start_date, "end": end_date},
                    "timestamp": datetime.utcnow().isoformat()
                },
                "performance_comparison": {},
                "risk_assessment": {},
                "recommendations": {}
            }
            
            # Extract performance metrics
            performance_data = {}
            for key, result in results.items():
                if result.get("success"):
                    if "vectorbt" in key:
                        perf_data = result.get("results", {})
                        performance_data[key] = {
                            "total_return": perf_data.get("total_return", 0),
                            "sharpe_ratio": perf_data.get("sharpe_ratio", 0),
                            "max_drawdown": perf_data.get("max_drawdown", 0),
                            "win_rate": perf_data.get("win_rate", 0)
                        }
                    elif "qflib" in key:
                        perf_data = result.get("results", {})
                        if "returns_analysis" in perf_data:
                            performance_data[key] = {
                                "sharpe_ratios": perf_data["returns_analysis"].get("sharpe_ratio", {}),
                                "volatilities": perf_data["returns_analysis"].get("annualized_volatility", {})
                            }
                    elif "lean" in key:
                        perf_data = result.get("results", {})
                        performance_data[key] = {
                            "total_return": perf_data.get("total_return", 0),
                            "sharpe_ratio": perf_data.get("sharpe_ratio", 0),
                            "max_drawdown": perf_data.get("max_drawdown", 0)
                        }
            
            # Generate performance comparison
            if performance_data:
                report["performance_comparison"] = self._compare_performance(performance_data)
            
            # Generate risk assessment
            report["risk_assessment"] = await self._assess_risk(results)
            
            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(performance_data, results)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating unified report: {str(e)}")
            return {"error": str(e)}
    
    def _compare_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance across different analysis types"""
        try:
            comparison = {
                "best_performing": {},
                "risk_adjusted_returns": {},
                "consistency_analysis": {}
            }
            
            # Find best performing strategies
            total_returns = {}
            sharpe_ratios = {}
            
            for key, data in performance_data.items():
                if "total_return" in data:
                    total_returns[key] = data["total_return"]
                if "sharpe_ratio" in data:
                    sharpe_ratios[key] = data["sharpe_ratio"]
            
            if total_returns:
                best_return = max(total_returns.items(), key=lambda x: x[1])
                comparison["best_performing"]["highest_return"] = {
                    "strategy": best_return[0],
                    "return": best_return[1]
                }
            
            if sharpe_ratios:
                best_sharpe = max(sharpe_ratios.items(), key=lambda x: x[1])
                comparison["best_performing"]["highest_sharpe"] = {
                    "strategy": best_sharpe[0],
                    "sharpe_ratio": best_sharpe[1]
                }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing performance: {str(e)}")
            return {}
    
    async def _assess_risk(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk across all analyses"""
        try:
            risk_assessment = {
                "overall_risk_level": "medium",
                "risk_factors": [],
                "diversification_score": 0.0,
                "correlation_analysis": {}
            }
            
            # Extract risk metrics
            max_drawdowns = []
            volatilities = []
            
            for key, result in results.items():
                if result.get("success"):
                    if "vectorbt" in key:
                        perf_data = result.get("results", {})
                        if "max_drawdown" in perf_data:
                            max_drawdowns.append(perf_data["max_drawdown"])
                    
                    elif "qflib" in key and "risk_metrics" in result.get("results", {}):
                        risk_data = result["results"]["risk_metrics"]
                        if "var_95" in risk_data:
                            volatilities.extend(list(risk_data["var_95"].values()))
            
            # Assess overall risk level
            if max_drawdowns:
                avg_drawdown = np.mean(max_drawdowns)
                if avg_drawdown > 0.20:
                    risk_assessment["overall_risk_level"] = "high"
                elif avg_drawdown < 0.10:
                    risk_assessment["overall_risk_level"] = "low"
            
            # Calculate diversification score
            if len(results) > 1:
                risk_assessment["diversification_score"] = min(1.0, len(results) / 5.0)
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return {"overall_risk_level": "unknown"}
    
    def _generate_recommendations(self, performance_data: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading and investment recommendations"""
        try:
            recommendations = {
                "strategy_recommendations": [],
                "risk_management": [],
                "portfolio_optimization": []
            }
            
            # Strategy recommendations based on performance
            if performance_data:
                best_strategies = []
                for key, data in performance_data.items():
                    if "sharpe_ratio" in data and data["sharpe_ratio"] > 1.0:
                        best_strategies.append(key)
                
                if best_strategies:
                    recommendations["strategy_recommendations"].append({
                        "type": "high_performance",
                        "strategies": best_strategies,
                        "reason": "Strategies with Sharpe ratio > 1.0"
                    })
            
            # Risk management recommendations
            recommendations["risk_management"].extend([
                {
                    "type": "position_sizing",
                    "recommendation": "Use dynamic position sizing based on volatility"
                },
                {
                    "type": "stop_loss",
                    "recommendation": "Implement trailing stop-losses for trend-following strategies"
                }
            ])
            
            # Portfolio optimization recommendations
            if "qflib_portfolio_optimization" in results:
                recommendations["portfolio_optimization"].append({
                    "type": "rebalancing",
                    "recommendation": "Consider monthly rebalancing based on QF-Lib optimization"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {}
    
    async def run_benchmark_comparison(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        symbols: List[str],
        benchmark_symbol: str = "SPY"
    ) -> Dict[str, Any]:
        """Run benchmark comparison across all three libraries"""
        try:
            # Add benchmark to symbols if not present
            if benchmark_symbol not in symbols:
                symbols.append(benchmark_symbol)
            
            # Run VectorBT analysis
            vectorbt_result = await self.vectorbt_service.run_vectorbt_backtest(
                strategy_id, start_date, end_date, symbols, "momentum"
            )
            
            # Run QF-Lib analysis
            qflib_result = await self.qflib_service.run_qflib_analysis(
                strategy_id, start_date, end_date, symbols, "risk_metrics"
            )
            
            # Run Lean analysis
            lean_result = await self.lean_service.run_lean_backtest(
                strategy_id, start_date, end_date, symbols, "momentum_strategy"
            )
            
            # Compare against benchmark
            benchmark_comparison = await self._compare_against_benchmark(
                vectorbt_result, qflib_result, lean_result, benchmark_symbol
            )
            
            return {
                "success": True,
                "benchmark_symbol": benchmark_symbol,
                "vectorbt_analysis": vectorbt_result,
                "qflib_analysis": qflib_result,
                "lean_analysis": lean_result,
                "benchmark_comparison": benchmark_comparison
            }
            
        except Exception as e:
            logger.error(f"Benchmark comparison error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _compare_against_benchmark(
        self,
        vectorbt_result: Dict[str, Any],
        qflib_result: Dict[str, Any],
        lean_result: Dict[str, Any],
        benchmark_symbol: str
    ) -> Dict[str, Any]:
        """Compare strategy performance against benchmark"""
        try:
            comparison = {
                "excess_returns": {},
                "risk_adjusted_comparison": {},
                "correlation_analysis": {}
            }
            
            # Calculate excess returns if available
            if vectorbt_result.get("success") and "results" in vectorbt_result:
                strategy_return = vectorbt_result["results"].get("total_return", 0)
                # Assume benchmark return (in real implementation, get from data)
                benchmark_return = 0.08  # 8% annual return
                comparison["excess_returns"]["vectorbt"] = strategy_return - benchmark_return
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing against benchmark: {str(e)}")
            return {}
