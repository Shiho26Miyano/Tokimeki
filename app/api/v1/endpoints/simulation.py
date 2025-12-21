"""
API endpoints for Trading Simulation System
Additive endpoints: /explain, /regime, /diagnostics
"""
import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.database import get_db
from app.models.simulation_models import (
    SignalsDaily, RegimeStates, PortfolioDaily, FeaturesDaily, Trades, StrategyMetadata
)
from app.services.simulation import (
    SimulationFeatureService, VolatilityRegimeStrategy, SimulationService, DailyPipelineService
)
from app.services.simulation.data_ingestion_service import SimulationDataIngestionService

logger = logging.getLogger(__name__)

router = APIRouter()


class ExplainResponse(BaseModel):
    """Response for explain endpoint"""
    success: bool
    symbol: str
    date: str
    strategy_id: str
    explanation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RegimeResponse(BaseModel):
    """Response for regime endpoint"""
    success: bool
    symbol: str
    date: str
    regime_on: bool
    rules: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DiagnosticsResponse(BaseModel):
    """Response for diagnostics endpoint"""
    success: bool
    strategy_id: str
    diagnostics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PipelineRunRequest(BaseModel):
    """Request to run daily pipeline"""
    symbol: str
    date: str
    skip_ingest: bool = False


class PipelineRunResponse(BaseModel):
    """Response from pipeline run"""
    success: bool
    symbol: str
    date: str
    steps: Dict[str, Any]
    portfolio: Optional[Dict[str, Any]] = None
    errors: List[str] = []


@router.get("/explain", response_model=ExplainResponse)
async def explain_signal(
    symbol: str = Query(..., description="Stock symbol"),
    date_str: str = Query(..., alias="date", description="Date in YYYY-MM-DD format"),
    strategy_id: str = Query(default="vol_regime_v1", description="Strategy ID"),
    db: Session = Depends(get_db)
):
    """
    Explain a trading signal for a given symbol and date
    
    Returns the reason_json from signals_daily with full explainability
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        signal = db.query(SignalsDaily).filter(
            and_(
                SignalsDaily.strategy_id == strategy_id,
                SignalsDaily.symbol == symbol,
                SignalsDaily.date == target_date
            )
        ).first()
        
        if not signal:
            return ExplainResponse(
                success=False,
                symbol=symbol,
                date=date_str,
                strategy_id=strategy_id,
                error=f"No signal found for {symbol} on {date_str}"
            )
        
        return ExplainResponse(
            success=True,
            symbol=symbol,
            date=date_str,
            strategy_id=strategy_id,
            explanation=signal.reason_json
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error in explain endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime", response_model=RegimeResponse)
async def get_regime_state(
    symbol: str = Query(..., description="Stock symbol"),
    date_str: str = Query(..., alias="date", description="Date in YYYY-MM-DD format"),
    strategy_id: str = Query(default="vol_regime_v1", description="Strategy ID"),
    db: Session = Depends(get_db)
):
    """
    Get volatility regime state for a given symbol and date
    
    Returns whether regime is ON/OFF and the rules that determined it
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        regime_state = db.query(RegimeStates).filter(
            and_(
                RegimeStates.strategy_id == strategy_id,
                RegimeStates.symbol == symbol,
                RegimeStates.date == target_date
            )
        ).first()
        
        if not regime_state:
            # Try to get from signal's reason_json
            signal = db.query(SignalsDaily).filter(
                and_(
                    SignalsDaily.strategy_id == strategy_id,
                    SignalsDaily.symbol == symbol,
                    SignalsDaily.date == target_date
                )
            ).first()
            
            if signal and signal.reason_json:
                regime_data = signal.reason_json.get('regime', {})
                return RegimeResponse(
                    success=True,
                    symbol=symbol,
                    date=date_str,
                    regime_on=regime_data.get('on', False),
                    rules=regime_data.get('rules')
                )
            
            return RegimeResponse(
                success=False,
                symbol=symbol,
                date=date_str,
                regime_on=False,
                error=f"No regime state found for {symbol} on {date_str}"
            )
        
        return RegimeResponse(
            success=True,
            symbol=symbol,
            date=date_str,
            regime_on=regime_state.regime_on,
            rules=regime_state.reasons_json
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error in regime endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def get_diagnostics(
    strategy_id: str = Query(default="vol_regime_v1", description="Strategy ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get diagnostics for a strategy
    
    Returns health metrics, data quality, and performance indicators
    """
    try:
        # Get strategy metadata
        strategy_meta = db.query(StrategyMetadata).filter(
            StrategyMetadata.strategy_id == strategy_id
        ).first()
        
        if not strategy_meta:
            return DiagnosticsResponse(
                success=False,
                strategy_id=strategy_id,
                error=f"Strategy {strategy_id} not found"
            )
        
        # Get date range
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days)
        
        # Count signals
        signal_count = db.query(SignalsDaily).filter(
            and_(
                SignalsDaily.strategy_id == strategy_id,
                SignalsDaily.date >= start_date,
                SignalsDaily.date <= end_date
            )
        ).count()
        
        # Count trades
        trade_count = db.query(Trades).filter(
            and_(
                Trades.strategy_id == strategy_id,
                Trades.date >= start_date,
                Trades.date <= end_date
            )
        ).count()
        
        # Get portfolio stats
        portfolios = db.query(PortfolioDaily).filter(
            and_(
                PortfolioDaily.strategy_id == strategy_id,
                PortfolioDaily.date >= start_date,
                PortfolioDaily.date <= end_date
            )
        ).order_by(PortfolioDaily.date).all()
        
        nav_stats = {}
        if portfolios:
            navs = [p.nav for p in portfolios]
            nav_stats = {
                'current_nav': navs[-1] if navs else None,
                'min_nav': min(navs) if navs else None,
                'max_nav': max(navs) if navs else None,
                'avg_nav': sum(navs) / len(navs) if navs else None
            }
            
            # Get latest portfolio
            latest_portfolio = portfolios[-1]
            nav_stats['latest'] = {
                'nav': latest_portfolio.nav,
                'cash': latest_portfolio.cash,
                'daily_pnl': latest_portfolio.daily_pnl,
                'drawdown': latest_portfolio.drawdown,
                'max_drawdown': latest_portfolio.max_drawdown
            }
        
        # Check data quality - count missing features
        missing_features = db.query(FeaturesDaily).filter(
            and_(
                FeaturesDaily.date >= start_date,
                FeaturesDaily.date <= end_date,
                FeaturesDaily.rv20.is_(None)
            )
        ).count()
        
        total_feature_days = db.query(FeaturesDaily).filter(
            and_(
                FeaturesDaily.date >= start_date,
                FeaturesDaily.date <= end_date
            )
        ).count()
        
        data_quality = {
            'total_feature_days': total_feature_days,
            'missing_features_count': missing_features,
            'completeness_pct': ((total_feature_days - missing_features) / total_feature_days * 100) if total_feature_days > 0 else 0
        }
        
        diagnostics = {
            'strategy': {
                'id': strategy_meta.strategy_id,
                'name': strategy_meta.name,
                'version': strategy_meta.version,
                'is_active': strategy_meta.is_active,
                'params': strategy_meta.params_json
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'activity': {
                'signals_generated': signal_count,
                'trades_executed': trade_count,
                'signals_per_day': signal_count / days if days > 0 else 0,
                'trades_per_day': trade_count / days if days > 0 else 0
            },
            'portfolio': nav_stats,
            'data_quality': data_quality
        }
        
        return DiagnosticsResponse(
            success=True,
            strategy_id=strategy_id,
            diagnostics=diagnostics
        )
        
    except Exception as e:
        logger.error(f"Error in diagnostics endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    db: Session = Depends(get_db)
):
    """
    Run the daily pipeline for a symbol and date
    
    Executes: ingest (if not skipped) → features → simulate → persist → report
    """
    try:
        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        
        strategy = VolatilityRegimeStrategy()
        pipeline = DailyPipelineService(db, strategy)
        
        result = pipeline.run_pipeline(
            request.symbol,
            target_date,
            skip_ingest=request.skip_ingest
        )
        
        return PipelineRunResponse(
            success=result['success'],
            symbol=result['symbol'],
            date=result['date'],
            steps=result.get('steps', {}),
            portfolio=result.get('portfolio'),
            errors=result.get('errors', [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {request.date}. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error in pipeline run: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/report")
async def get_pipeline_report(
    strategy_id: str = Query(default="vol_regime_v1", description="Strategy ID"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Generate performance report for a date range
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        strategy = VolatilityRegimeStrategy()
        pipeline = DailyPipelineService(db, strategy)
        
        report = pipeline.generate_report(strategy_id, start, end)
        
        return report
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/consumer-options")
async def sync_consumer_options_data(
    symbol: str = Query(..., description="Stock symbol"),
    date_str: str = Query(..., alias="date", description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Sync options data from consumer options dashboard to simulation tables
    
    This endpoint bridges the consumer options dashboard data to the simulation system.
    It takes options data (IV, volume, OI, etc.) and stores it in OptionsSnapshotDaily
    for use by the simulation strategy.
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        ingestion_service = SimulationDataIngestionService(db)
        result = await ingestion_service.sync_consumer_options_to_simulation(symbol, target_date)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error syncing consumer options data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

