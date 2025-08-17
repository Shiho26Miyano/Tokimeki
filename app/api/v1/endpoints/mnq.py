"""
MNQ Investment endpoints
"""
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.core.dependencies import get_cache_service, get_usage_service, get_ai_service
from app.services.mnq_investment_service import AsyncMNQInvestmentService
from app.services.usage_service import AsyncUsageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class MNQInvestmentRequest(BaseModel):
    weekly_amount: float = Field(default=1000.0, ge=100, le=10000, description="Weekly investment amount in USD")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")

class MNQOptimalAmountsRequest(BaseModel):
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    min_amount: float = Field(default=100.0, ge=50, le=5000, description="Minimum weekly investment amount to test")
    max_amount: float = Field(default=10000.0, ge=500, le=50000, description="Maximum weekly investment amount to test")
    step_size: float = Field(default=100.0, ge=25, le=1000, description="Step size between test amounts")
    top_n: int = Field(default=5, ge=1, le=20, description="Number of top results to return")
    sort_key: str = Field(default="total_return", description="Sort key: total_return, sharpe_ratio, profit_factor, or return_per_invested_dollar")
    descending: bool = Field(default=True, description="Sort in descending order (True) or ascending (False)")

class MNQPerformanceResponse(BaseModel):
    success: bool
    weekly_amount: float
    start_date: str
    end_date: str
    total_weeks: int
    total_invested: float
    current_value: float
    total_return: float
    weekly_breakdown: List[dict]
    performance_metrics: dict
    equity_curve: List[dict]

class MNQOptimalAmountsResponse(BaseModel):
    success: bool
    start_date: str
    end_date: str
    summary: dict
    top_by_percentage: List[dict]  # Left side: sorted by percentage/return
    top_by_profit: List[dict]      # Right side: top 5 by dollar profit
    all_results: List[dict]

class MNQAnalysisRequest(BaseModel):
    weekly_amount: float
    start_date: str
    end_date: str
    total_weeks: int
    total_invested: float
    current_value: float
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_contracts: float

class MNQAnalysisResponse(BaseModel):
    success: bool
    analysis: str
    model_used: str
    response_time: float

@router.post("/calculate", response_model=MNQPerformanceResponse)
async def calculate_mnq_dca(
    request: MNQInvestmentRequest,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Calculate MNQ weekly DCA performance"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting MNQ DCA calculation: ${request.weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=request.weekly_amount,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if not result:
            logger.error("No result returned from MNQ service")
            raise HTTPException(status_code=500, detail="MNQ calculation failed - no result returned")
        
        logger.info(f"MNQ DCA calculation completed successfully")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_calculate",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_calculate",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ DCA calculation error: {e}")
        
        if "No data available" in str(e):
            raise HTTPException(status_code=404, detail="No MNQ futures data available")
        elif "yfinance" in str(e).lower():
            raise HTTPException(status_code=503, detail="MNQ data service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail=f"MNQ calculation failed: {str(e)}")

@router.get("/equity")
async def get_mnq_equity(
    weekly_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ equity curve data"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Fetching MNQ equity curve: ${weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance to get equity curve
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=weekly_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result or 'equity_curve' not in result:
            raise HTTPException(status_code=500, detail="Failed to generate equity curve")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_equity",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "equity_curve": result['equity_curve'],
            "weekly_amount": weekly_amount,
            "start_date": result['start_date'],
            "end_date": result['end_date']
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_equity",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ equity curve error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch equity curve: {str(e)}")

@router.get("/metrics")
async def get_mnq_metrics(
    weekly_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ performance metrics"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Fetching MNQ metrics: ${weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance to get metrics
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=weekly_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result or 'performance_metrics' not in result:
            raise HTTPException(status_code=500, detail="Failed to generate performance metrics")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_metrics",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "metrics": result['performance_metrics'],
            "summary": {
                "total_invested": result['total_invested'],
                "current_value": result['current_value'],
                "total_return": result['total_return'],
                "total_weeks": result['total_weeks']
            }
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_metrics",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/positions")
async def get_mnq_positions(
    weekly_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ position tracking data"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Fetching MNQ positions: ${weekly_amount}/week")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Calculate performance to get weekly breakdown
        result = await mnq_service.calculate_weekly_dca_performance(
            weekly_amount=weekly_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result or 'weekly_breakdown' not in result:
            raise HTTPException(status_code=500, detail="Failed to generate position data")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_positions",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "positions": result['weekly_breakdown'],
            "summary": {
                "total_contracts": result.get('total_contracts', 0),
                "total_invested": result['total_invested'],
                "current_value": result['current_value']
            }
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_positions",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ positions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

@router.get("/available")
async def get_mnq_info(
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get MNQ futures information"""
    
    start_time = time.time()
    
    try:
        logger.info("Fetching MNQ futures information")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_info",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "symbol": "MNQ=F",
            "name": "Micro E-mini NASDAQ-100 Futures",
            "contract_multiplier": 2,                # $2 per index point
            "point_value_usd": 2.0,                  # helpful explicit field
            "margin_model": "Approx. $1,000 initial / $800 maintenance per contract (varies)",
            "trading_hours": "Sun 6:00 PM – Fri 5:00 PM ET (with daily 5–6 PM pause)",
            "description": "Micro E-mini NASDAQ-100 futures contract, $2 per index point."
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_info",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch MNQ info: {str(e)}")

@router.get("/date-range")
async def get_mnq_date_range(
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Get the maximum available date range for MNQ data"""
    
    start_time = time.time()
    
    try:
        logger.info("Fetching MNQ available date range")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Get available date range
        date_range = await mnq_service.get_max_available_date_range()
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_date_range",
            response_time=response_time,
            success=True
        )
        
        return {
            "success": True,
            "data": date_range
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_date_range",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"MNQ date range error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch date range: {str(e)}")

@router.post("/optimal-amounts", response_model=MNQOptimalAmountsResponse)
async def find_optimal_mnq_amounts(
    request: MNQOptimalAmountsRequest,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Find the optimal weekly investment amounts for maximum returns"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Finding optimal MNQ investment amounts: ${request.min_amount}-${request.max_amount}, step ${request.step_size}")
        
        # Create MNQ service instance
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Find optimal amounts
        result = await mnq_service.find_optimal_investment_amounts(
            start_date=request.start_date,
            end_date=request.end_date,
            min_amount=request.min_amount,
            max_amount=request.max_amount,
            step_size=request.step_size,
            top_n=request.top_n,
            sort_key=request.sort_key,
            descending=request.descending
        )
        
        if not result:
            logger.error("No result returned from optimal amounts service")
            raise HTTPException(status_code=500, detail="Optimal amounts calculation failed")
        
        logger.info(f"Optimal amounts calculation completed successfully")
        
        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_optimal_amounts",
            response_time=response_time,
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_optimal_amounts",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Optimal amounts calculation error: {e}")
        
        if "No data available" in str(e):
            raise HTTPException(status_code=404, detail="No MNQ futures data available")
        elif "yfinance" in str(e).lower():
            raise HTTPException(status_code=503, detail="MNQ data service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail=f"Optimal amounts calculation failed: {str(e)}")

@router.post("/generate-analysis", response_model=MNQAnalysisResponse)
async def generate_mnq_analysis(
    request: MNQAnalysisRequest,
    ai_service = Depends(get_ai_service),
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Generate AI-powered quantitative analysis for MNQ DCA strategy"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Generating AI analysis for MNQ strategy: ${request.weekly_amount}/week")
        
        # First, calculate optimal amounts to get real top 5 performers
        from app.services.mnq_investment_service import AsyncMNQInvestmentService
        
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Use the improved service to find optimal amounts (real calculations)
        logger.info("Finding optimal amounts via service (real calculations)...")
        optimal = await mnq_service.find_optimal_investment_amounts(
            start_date=request.start_date,
            end_date=request.end_date,
            min_amount=max(50.0, request.weekly_amount * 0.1),  # sensible local neighborhood
            max_amount=request.weekly_amount * 2.0,
            step_size=10.0,  # Small step to catch $120, $125, $150, etc.
            top_n=5,
            sort_key="total_return",
            descending=True
        )

        # Get top results by percentage (existing behavior)
        top_by_percentage = optimal.get("top_by_percentage", [])[:5]
        top_5_amounts = []
        for i, t in enumerate(top_by_percentage):
            top_5_amounts.append(f"{i+1}. ${t['weekly_amount']:,.0f} - {t['total_return']:.2f}% return")
        
        # Also get top results by Sharpe ratio for comparison
        top_by_sharpe = optimal.get("top_by_sharpe", [])[:5]
        top_5_by_sharpe = []
        for i, t in enumerate(top_by_sharpe):
            top_5_by_sharpe.append(f"{i+1}. ${t['weekly_amount']:,.0f} - {t['sharpe_ratio']:.2f} Sharpe")
        
        # Create simple table format
        table_rows = []
        for i in range(5):
            left_item = top_5_amounts[i] if i < len(top_5_amounts) else ""
            right_item = top_5_by_sharpe[i] if i < len(top_5_by_sharpe) else ""
            table_rows.append(f"| {left_item} | {right_item} |")
        
        table_content = "\n".join(table_rows)
        logger.info(f"Service returned top amounts by percentage: {top_5_amounts}")
        logger.info(f"Service returned top amounts by Sharpe ratio: {top_5_by_sharpe}")
        
        # Create structured prompt for AI service
        structured_prompt = f"""You are a quantitative product manager and research writer.

Turn this MNQ futures DCA strategy backtest data into a simple, brief, high-signal write-up for investors and traders.

FOLLOW THIS EXACT FORMAT (no deviations):

**Executive Summary** (≤80 words, bullet format)
• Analysis period: {request.total_weeks} weeks
• Strategy: ${request.weekly_amount:,.0f}/week DCA into MNQ futures
• Results: {request.total_return:.2f}% return, {request.cagr:.2f}% CAGR
• Key insight: One-sentence summary of performance

**Top 5 Weekly Amounts by Performance** (Based on Actual Calculations)

| Left: By Return % | Right: By Sharpe Ratio |
|-------------------|------------------------|
| {table_content} |

**Key Performance Metrics**
| Metric | Value |
|--------|-------|
| Total Return | {request.total_return:.2f}% |
| CAGR | {request.cagr:.2f}% |
| Volatility | {request.volatility:.2f}% |
| Sharpe Ratio | {request.sharpe_ratio:.2f} |
| Max Drawdown | {request.max_drawdown:.2f}% |
| Win Rate | {request.win_rate:.2f}% |
| Profit Factor | {request.profit_factor:.2f} |
| Total Contracts | {request.total_contracts:.1f} |


Data: Weekly ${request.weekly_amount:,.0f} investment over {request.total_weeks} weeks. Total invested: ${request.total_invested:,.0f}, Current value: ${request.current_value:,.0f}, Return: {request.total_return:.2f}%, CAGR {request.cagr:.2f}%, Volatility {request.volatility:.2f}%, Max drawdown {request.max_drawdown:.2f}%, Total contracts: {request.total_contracts:.4f}.

IMPORTANT: Use ONLY the actual calculated data provided above in the "Top 5 Weekly Amounts by Performance" section. Do NOT generate new recommendations. The {table_content} contains the real performance data that should be displayed exactly as shown."""

        # Call AI service
        logger.info("Calling AI service with structured prompt...")
        try:
            ai_result = await ai_service.chat(
                message=structured_prompt,
                model="mistral-small",
                temperature=0.3,
                max_tokens=1500
            )
            
            logger.info(f"AI service response: {ai_result}")
            analysis = ai_result.get("response", "AI analysis generated successfully.")
            
            # Track usage
            response_time = time.time() - start_time
            await usage_service.track_request(
                endpoint="mnq_analysis",
                model="mistral-small",
                response_time=response_time,
                success=True
            )
            
            logger.info(f"AI analysis generated successfully in {response_time:.2f}s")
            
            return {
                "success": True,
                "analysis": analysis,
                "model_used": "mistral-small",
                "response_time": response_time
            }
            
        except Exception as ai_error:
            logger.error(f"AI service call failed: {ai_error}")
            # Continue to fallback analysis
            raise Exception(f"AI service unavailable: {str(ai_error)}")
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_analysis",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"AI analysis generation error: {e}")
        
        # Return fallback analysis
        fallback_analysis = f"""**Executive Summary** (≤80 words, bullet format)
• Analysis period: {request.total_weeks} weeks
• Strategy: ${request.weekly_amount:,.0f}/week DCA into MNQ futures
• Results: {request.total_return:.2f}% return, {request.cagr:.2f}% CAGR
• Key insight: {'Positive' if request.total_return > 0 else 'Negative'} returns over {request.total_weeks} weeks with {request.max_drawdown:.2f}% max drawdown

**Top 5 Weekly Amounts by Performance** (Based on Actual Calculations)

| Left: By Return % | Right: By Sharpe Ratio |
|-------------------|------------------------|
| {table_content} |

**Key Performance Metrics**
| Metric | Value |
|--------|-------|
| Total Return | {request.total_return:.2f}% |
| CAGR | {request.cagr:.2f}% |
| Volatility | {request.volatility:.2f}% |
| Sharpe Ratio | {request.sharpe_ratio:.2f} |
| Max Drawdown | {request.max_drawdown:.2f}% |
| Win Rate | {request.win_rate:.2f}% |
| Profit Factor | {request.profit_factor:.2f} |
| Total Contracts | {request.total_contracts:.1f} |"""

        return {
            "success": False,
            "analysis": fallback_analysis,
            "model_used": "fallback",
            "response_time": response_time
        }

@router.post("/generate-diagnostic-analysis", response_model=MNQAnalysisResponse)
async def generate_mnq_diagnostic_analysis(
    request: MNQAnalysisRequest,
    cache_service = Depends(get_cache_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Generate diagnostic event analysis identifying worst week and factor impacts"""
    
    start_time = time.time()
    
    try:
        logger.info(f"Generating diagnostic analysis for MNQ strategy: ${request.weekly_amount}/week")
        
        from app.services.mnq_investment_service import AsyncMNQInvestmentService
        
        mnq_service = AsyncMNQInvestmentService(cache_service)
        
        # Generate diagnostic event analysis
        diagnostic_result = await mnq_service.generate_diagnostic_event_analysis(
            weekly_amount=request.weekly_amount,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if not diagnostic_result:
            raise Exception("Failed to generate diagnostic analysis")
        
        worst_week = diagnostic_result['worst_week']
        factor_analysis = diagnostic_result['factor_analysis']
        
        # Create diagnostic analysis report
        worst_date = factor_analysis['worst_date']
        worst_return_pct = factor_analysis['worst_return_pct']
        
        # Create the diagnostic report in HTML format - concentrated and focused
        diagnostic_report = f"""<div class="diagnostic-analysis">
            <div class="diagnostic-header text-center mb-3">
                <h4 class="text-primary mb-2">🔍 Diagnostic Event Analysis</h4>
                <div class="alert alert-danger py-2">
                    <strong>Worst Week: {worst_date} ({worst_return_pct:.2f}% loss)</strong>
                </div>
            </div>
            
            <div class="factor-impact-section mb-3">
                <h5 class="text-dark mb-2">Factor Impact Table</h5>
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Factor</th>
                                <th>Type</th>
                                <th>Impact on {worst_date}</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        # Add table rows - only the most important factors with type categorization
        important_factors = factor_analysis['factor_table'][:5]  # Limit to top 5
        for factor in important_factors:
            factor_type = factor.get('factor_type', 'Market Event')  # Get factor type from AI response
            diagnostic_report += f"""
                            <tr>
                                <td><strong>{factor['factor']}</strong></td>
                                <td><span class="badge bg-secondary">{factor_type}</span></td>
                                <td>{factor['impact']}</td>
                            </tr>"""
        
        diagnostic_report += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>"""

        # Track usage
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_diagnostic_analysis",
            model="diagnostic_analysis",
            response_time=response_time,
            success=True
        )
        
        logger.info(f"Diagnostic analysis generated successfully in {response_time:.2f}s")
        
        return {
            "success": True,
            "analysis": diagnostic_report,
            "model_used": "diagnostic_analysis",
            "response_time": response_time
        }
        
    except Exception as e:
        # Track failed request
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="mnq_diagnostic_analysis",
            response_time=response_time,
            success=False,
            error=str(e)
        )
        
        logger.error(f"Diagnostic analysis generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnostic analysis failed: {str(e)}")
