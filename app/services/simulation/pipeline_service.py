"""
Daily Pipeline Service for Trading Simulation
Orchestrates: ingest → features → simulate → persist → report
"""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.simulation_models import (
    PricesDaily, OptionsSnapshotDaily, FeaturesDaily, SignalsDaily,
    Trades, PortfolioDaily, StrategyMetadata, RegimeStates
)
from .feature_service import SimulationFeatureService
from .strategy_service import StrategyPlugin, VolatilityRegimeStrategy
from .simulation_service import SimulationService

logger = logging.getLogger(__name__)


class DailyPipelineService:
    """Service for running the complete daily trading simulation pipeline"""
    
    def __init__(self, db: Session, strategy: Optional[StrategyPlugin] = None):
        self.db = db
        self.feature_service = SimulationFeatureService(db)
        self.strategy = strategy or VolatilityRegimeStrategy()
        self.simulation_service = SimulationService(db, self.strategy)
    
    def ensure_strategy_metadata(self) -> StrategyMetadata:
        """Ensure strategy metadata exists in database"""
        metadata = self.db.query(StrategyMetadata).filter(
            StrategyMetadata.strategy_id == self.strategy.strategy_id
        ).first()
        
        if not metadata:
            metadata = StrategyMetadata(
                strategy_id=self.strategy.strategy_id,
                name="Volatility Regime Strategy",
                version=self.strategy.version,
                params_json=self.strategy.params,
                description="Trades only when volatility regime is active. Uses options metrics for sentiment confirmation.",
                is_active=True
            )
            self.db.add(metadata)
            self.db.commit()
            self.db.refresh(metadata)
        
        return metadata
    
    def run_pipeline(
        self,
        symbol: str,
        target_date: date,
        skip_ingest: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete daily pipeline for a symbol and date
        
        Steps:
        1. Ingest (if not skipped) - assumes data already exists or will be ingested separately
        2. Compute features
        3. Generate signals
        4. Simulate trades
        5. Update portfolio
        6. Persist regime states
        
        Returns:
            Dictionary with pipeline results
        """
        results = {
            'symbol': symbol,
            'date': target_date.isoformat(),
            'steps': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Step 0: Ensure strategy metadata
            self.ensure_strategy_metadata()
            
            # Step 1: Verify data exists (ingest is assumed to be done separately)
            if not skip_ingest:
                price_data = self.db.query(PricesDaily).filter(
                    and_(
                        PricesDaily.symbol == symbol,
                        PricesDaily.date == target_date
                    )
                ).first()
                
                if not price_data:
                    results['errors'].append(f"No price data found for {symbol} on {target_date}")
                    return results
            
            # Step 2: Compute features
            logger.info(f"Computing features for {symbol} on {target_date}")
            features_dict = self.feature_service.compute_features_for_date(symbol, target_date)
            
            if not features_dict:
                results['errors'].append(f"Could not compute features for {symbol} on {target_date}")
                return results
            
            features = self.feature_service.persist_features(features_dict)
            results['steps']['features'] = {
                'success': True,
                'rv20': features.rv20,
                'rv60': features.rv60,
                'atr14': features.atr14,
                'rv20_pct': features.rv20_pct,
                'atr14_pct': features.atr14_pct,
                'iv_median_pct': features.iv_median_pct
            }
            
            # Step 3: Generate signal
            logger.info(f"Generating signal for {symbol} on {target_date}")
            signal_dict = self.strategy.generate_signal(
                self.db, symbol, target_date, features
            )
            
            # Persist signal
            existing_signal = self.db.query(SignalsDaily).filter(
                and_(
                    SignalsDaily.strategy_id == self.strategy.strategy_id,
                    SignalsDaily.symbol == symbol,
                    SignalsDaily.date == target_date
                )
            ).first()
            
            if existing_signal:
                existing_signal.signal = signal_dict['signal']
                existing_signal.target_position = signal_dict['target_position']
                existing_signal.reason_json = signal_dict['reason_json']
                signal = existing_signal
            else:
                signal = SignalsDaily(
                    strategy_id=self.strategy.strategy_id,
                    symbol=symbol,
                    date=target_date,
                    signal=signal_dict['signal'],
                    target_position=signal_dict['target_position'],
                    reason_json=signal_dict['reason_json']
                )
                self.db.add(signal)
            
            self.db.commit()
            self.db.refresh(signal)
            
            results['steps']['signal'] = {
                'success': True,
                'signal': signal.signal,
                'target_position': signal.target_position
            }
            
            # Step 4: Persist regime state (for explainability)
            regime_on = signal_dict['reason_json'].get('regime', {}).get('on', False)
            regime_state = self.db.query(RegimeStates).filter(
                and_(
                    RegimeStates.strategy_id == self.strategy.strategy_id,
                    RegimeStates.symbol == symbol,
                    RegimeStates.date == target_date
                )
            ).first()
            
            if regime_state:
                regime_state.regime_on = regime_on
                regime_state.reasons_json = signal_dict['reason_json'].get('regime', {})
            else:
                regime_state = RegimeStates(
                    strategy_id=self.strategy.strategy_id,
                    symbol=symbol,
                    date=target_date,
                    regime_on=regime_on,
                    reasons_json=signal_dict['reason_json'].get('regime', {})
                )
                self.db.add(regime_state)
            
            self.db.commit()
            
            # Step 5: Simulate (execute trades and update portfolio)
            logger.info(f"Simulating for {symbol} on {target_date}")
            sim_result = self.simulation_service.simulate_day(symbol, target_date)
            
            if not sim_result.get('success'):
                results['errors'].append(f"Simulation failed: {sim_result.get('error')}")
                results['success'] = False
                return results
            
            results['steps']['simulation'] = {
                'success': True,
                'trade_executed': sim_result.get('trade') is not None,
                'nav': sim_result['portfolio'].nav,
                'daily_pnl': sim_result['portfolio'].daily_pnl
            }
            
            results['success'] = True
            results['portfolio'] = {
                'nav': sim_result['portfolio'].nav,
                'cash': sim_result['portfolio'].cash,
                'positions': sim_result['portfolio'].positions_json,
                'daily_pnl': sim_result['portfolio'].daily_pnl,
                'cumulative_pnl': sim_result['portfolio'].cumulative_pnl,
                'drawdown': sim_result['portfolio'].drawdown,
                'max_drawdown': sim_result['portfolio'].max_drawdown
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline error for {symbol} on {target_date}: {str(e)}", exc_info=True)
            results['errors'].append(str(e))
            results['success'] = False
            return results
    
    def run_pipeline_batch(
        self,
        symbols: List[str],
        target_date: date,
        skip_ingest: bool = False
    ) -> Dict[str, Any]:
        """
        Run pipeline for multiple symbols
        
        Returns:
            Dictionary with results for each symbol
        """
        results = {
            'date': target_date.isoformat(),
            'symbols': {},
            'summary': {
                'total': len(symbols),
                'success': 0,
                'failed': 0
            }
        }
        
        for symbol in symbols:
            symbol_result = self.run_pipeline(symbol, target_date, skip_ingest)
            results['symbols'][symbol] = symbol_result
            
            if symbol_result['success']:
                results['summary']['success'] += 1
            else:
                results['summary']['failed'] += 1
        
        return results
    
    def generate_report(
        self,
        strategy_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate performance report for a date range
        
        Returns:
            Dictionary with performance metrics
        """
        portfolios = self.db.query(PortfolioDaily).filter(
            and_(
                PortfolioDaily.strategy_id == strategy_id,
                PortfolioDaily.date >= start_date,
                PortfolioDaily.date <= end_date
            )
        ).order_by(PortfolioDaily.date).all()
        
        if not portfolios:
            return {
                'success': False,
                'error': 'No portfolio data found'
            }
        
        # Compute metrics
        initial_nav = portfolios[0].nav
        final_nav = portfolios[-1].nav
        total_return = (final_nav - initial_nav) / initial_nav if initial_nav > 0 else 0.0
        
        daily_returns = []
        for i in range(1, len(portfolios)):
            if portfolios[i-1].nav > 0:
                daily_ret = (portfolios[i].nav - portfolios[i-1].nav) / portfolios[i-1].nav
                daily_returns.append(daily_ret)
        
        sharpe_ratio = None
        if len(daily_returns) > 0:
            import numpy as np
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            if std_return > 0:
                sharpe_ratio = (mean_return / std_return) * np.sqrt(252)  # Annualized
        
        max_dd = max([p.max_drawdown or 0.0 for p in portfolios])
        
        # Count signals
        signals = self.db.query(SignalsDaily).filter(
            and_(
                SignalsDaily.strategy_id == strategy_id,
                SignalsDaily.date >= start_date,
                SignalsDaily.date <= end_date
            )
        ).all()
        
        signal_counts = {'LONG': 0, 'SHORT': 0, 'FLAT': 0}
        for signal in signals:
            signal_counts[signal.signal] = signal_counts.get(signal.signal, 0) + 1
        
        # Count trades
        trades = self.db.query(Trades).filter(
            and_(
                Trades.strategy_id == strategy_id,
                Trades.date >= start_date,
                Trades.date <= end_date
            )
        ).count()
        
        return {
            'success': True,
            'strategy_id': strategy_id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'metrics': {
                'initial_nav': initial_nav,
                'final_nav': final_nav,
                'total_return': total_return,
                'total_return_pct': total_return * 100,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_dd,
                'max_drawdown_pct': max_dd * 100,
                'trading_days': len(portfolios),
                'total_trades': trades
            },
            'signals': signal_counts,
            'daily_performance': [
                {
                    'date': p.date.isoformat(),
                    'nav': p.nav,
                    'daily_pnl': p.daily_pnl,
                    'drawdown': p.drawdown
                }
                for p in portfolios
            ]
        }

