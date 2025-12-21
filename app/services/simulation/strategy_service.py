"""
Strategy Plugin System and Volatility Regime Strategy v1
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np

from app.models.simulation_models import FeaturesDaily, PricesDaily, PortfolioDaily


class StrategyPlugin(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, strategy_id: str, version: str, params: Dict[str, Any]):
        self.strategy_id = strategy_id
        self.version = version
        self.params = params
    
    @abstractmethod
    def generate_signal(
        self,
        db: Session,
        symbol: str,
        target_date: date,
        features: Optional[FeaturesDaily] = None
    ) -> Dict[str, Any]:
        """
        Generate trading signal for a given symbol and date
        
        Returns:
            Dictionary with:
            - signal: "LONG", "SHORT", or "FLAT"
            - target_position: float (fraction of NAV, 0.0 to 1.0)
            - reason_json: Dict with explainability data
        """
        pass
    
    @abstractmethod
    def check_risk_controls(
        self,
        db: Session,
        symbol: str,
        target_date: date,
        portfolio: Optional[PortfolioDaily] = None
    ) -> Dict[str, Any]:
        """
        Check risk controls and return risk state
        
        Returns:
            Dictionary with risk control state
        """
        pass


class VolatilityRegimeStrategy(StrategyPlugin):
    """
    Volatility Regime Strategy v1
    
    Only trades when volatility regime is active.
    Uses options metrics for sentiment confirmation.
    Executes stock positions only.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'base_exposure': 0.30,  # 30% of NAV
            'rv60_target': 0.25,  # 25% annualized vol target
            'rv20_pct_threshold': 70,
            'atr14_pct_threshold': 60,
            'iv_median_pct_threshold': 60,
            'cp_vol_ratio_bullish': 1.05,
            'cp_vol_ratio_bearish': 0.95,
            'cp_oi_ratio_bullish': 1.05,
            'cp_oi_ratio_bearish': 0.95,
            'mom20_window': 20,
            'daily_loss_stop_pct': -0.015,  # -1.5% of NAV
            'daily_loss_cooldown_days': 3,
            'max_drawdown_stop_pct': 0.08,  # 8%
            'drawdown_cooldown_days': 10,
            'reversal_exit_days': 3,
            'execution_timing': 'MOC'  # MOC or NEXT_OPEN
        }
        
        if params:
            default_params.update(params)
        
        super().__init__(
            strategy_id="vol_regime_v1",
            version="1.0.0",
            params=default_params
        )
    
    def _get_price_data(self, db: Session, symbol: str, target_date: date, days_back: int) -> Optional[Dict]:
        """Get price data for a date range"""
        prices = db.query(PricesDaily).filter(
            PricesDaily.symbol == symbol,
            PricesDaily.date <= target_date
        ).order_by(PricesDaily.date.desc()).limit(days_back + 1).all()
        
        if len(prices) < days_back + 1:
            return None
        
        # Sort by date ascending
        prices = sorted(prices, key=lambda x: x.date)
        
        return {
            'current': prices[-1],
            'historical': prices[:-1]
        }
    
    def _check_regime(self, features: FeaturesDaily) -> Tuple[bool, Dict]:
        """
        Check if volatility regime is ON
        
        Returns:
            (regime_on, rules_dict)
        """
        rules = {}
        
        # Rule 1: rv20_pct >= threshold
        rv20_pct = features.rv20_pct
        rv20_threshold = self.params['rv20_pct_threshold']
        rv20_pass = rv20_pct is not None and rv20_pct >= rv20_threshold
        rules['rv20_pct'] = {
            'value': rv20_pct,
            'threshold': rv20_threshold,
            'pass': rv20_pass
        }
        
        # Rule 2: atr14_pct >= threshold
        atr14_pct = features.atr14_pct
        atr14_threshold = self.params['atr14_pct_threshold']
        atr14_pass = atr14_pct is not None and atr14_pct >= atr14_threshold
        rules['atr14_pct'] = {
            'value': atr14_pct,
            'threshold': atr14_threshold,
            'pass': atr14_pass
        }
        
        # Rule 3: iv_median_pct >= threshold OR iv_slope > 0
        iv_median_pct = features.iv_median_pct
        iv_slope = features.iv_slope
        iv_median_threshold = self.params['iv_median_pct_threshold']
        
        iv_median_pass = iv_median_pct is not None and iv_median_pct >= iv_median_threshold
        iv_slope_pass = iv_slope is not None and iv_slope > 0
        
        iv_gate_pass = iv_median_pass or iv_slope_pass
        
        rules['iv_gate'] = {
            'iv_median_pct': {
                'value': iv_median_pct,
                'threshold': iv_median_threshold,
                'pass': iv_median_pass
            },
            'iv_slope': {
                'value': iv_slope,
                'threshold': 0,
                'pass': iv_slope_pass
            },
            'pass': iv_gate_pass
        }
        
        # Regime is ON if all rules pass
        regime_on = rv20_pass and atr14_pass and iv_gate_pass
        
        return regime_on, rules
    
    def _compute_direction(self, db: Session, symbol: str, target_date: date, features: FeaturesDaily) -> Dict:
        """Compute signal direction (LONG, SHORT, or FLAT)"""
        # Get price data for momentum
        price_data = self._get_price_data(db, symbol, target_date, self.params['mom20_window'])
        if not price_data:
            return {
                'signal': 'FLAT',
                'mom20': None,
                'sentiment': None
            }
        
        current_close = price_data['current'].close
        historical = price_data['historical']
        
        if len(historical) < self.params['mom20_window']:
            return {
                'signal': 'FLAT',
                'mom20': None,
                'sentiment': None
            }
        
        # Compute momentum
        past_close = historical[-self.params['mom20_window']].close
        mom20 = (current_close / past_close) - 1.0
        
        # Compute sentiment from options
        cp_vol_ratio = features.cp_vol_ratio or 1.0
        cp_oi_ratio = features.cp_oi_ratio or 1.0
        
        vol_bullish = cp_vol_ratio >= self.params['cp_vol_ratio_bullish']
        oi_bullish = cp_oi_ratio >= self.params['cp_oi_ratio_bullish']
        vol_bearish = cp_vol_ratio <= self.params['cp_vol_ratio_bearish']
        oi_bearish = cp_oi_ratio <= self.params['cp_oi_ratio_bearish']
        
        if vol_bullish and oi_bullish:
            sent = 1
        elif vol_bearish and oi_bearish:
            sent = -1
        else:
            sent = 0
        
        # Determine signal
        if mom20 > 0 and sent >= 0:
            signal = 'LONG'
        elif mom20 < 0 and sent <= 0:
            signal = 'SHORT'
        else:
            signal = 'FLAT'
        
        return {
            'signal': signal,
            'mom20': mom20,
            'sentiment': {
                'cp_vol_ratio': cp_vol_ratio,
                'cp_oi_ratio': cp_oi_ratio,
                'sent': sent
            }
        }
    
    def _compute_position_sizing(self, features: FeaturesDaily, signal: str) -> Dict:
        """Compute target position size"""
        if signal == 'FLAT':
            return {
                'base': self.params['base_exposure'],
                'rv60': features.rv60,
                'rv60_target': self.params['rv60_target'],
                'scale': 1.0,
                'target_position': 0.0
            }
        
        base = self.params['base_exposure']
        rv60_target = self.params['rv60_target']
        rv60 = features.rv60 or 0.25  # Default if missing
        
        # Volatility scaling
        eps = 1e-9
        scale = np.clip(rv60_target / max(rv60, eps), 0.5, 1.5)
        
        # Target position
        target = np.clip(base * scale, 0.10, 0.50)  # 10% to 50% NAV
        
        return {
            'base': base,
            'rv60': rv60,
            'rv60_target': rv60_target,
            'scale': scale,
            'target_position': target
        }
    
    def check_risk_controls(
        self,
        db: Session,
        symbol: str,
        target_date: date,
        portfolio: Optional[PortfolioDaily] = None
    ) -> Dict[str, Any]:
        """Check risk controls and return risk state"""
        risk_state = {
            'cooldown': {'active': False, 'days_left': 0},
            'drawdown_stop': {'active': False, 'days_left': 0},
            'reversal_exit': {'active': False}
        }
        
        if not portfolio:
            return risk_state
        
        # Get recent portfolio states
        recent_portfolios = db.query(PortfolioDaily).filter(
            PortfolioDaily.strategy_id == self.strategy_id,
            PortfolioDaily.date <= target_date
        ).order_by(PortfolioDaily.date.desc()).limit(20).all()
        
        if not recent_portfolios:
            return risk_state
        
        # Check daily loss stop
        daily_loss_stop_pct = self.params['daily_loss_stop_pct']
        cooldown_days = self.params['daily_loss_cooldown_days']
        
        # Check if we had a daily loss stop recently
        for i, p in enumerate(recent_portfolios[:cooldown_days]):
            if p.daily_pnl and p.daily_pnl <= (daily_loss_stop_pct * p.nav):
                days_left = cooldown_days - i
                risk_state['cooldown'] = {
                    'active': True,
                    'days_left': days_left
                }
                break
        
        # Check max drawdown stop
        max_drawdown_stop_pct = self.params['max_drawdown_stop_pct']
        drawdown_cooldown_days = self.params['drawdown_cooldown_days']
        
        if portfolio.drawdown and portfolio.drawdown >= max_drawdown_stop_pct:
            # Check how many days since drawdown was triggered
            drawdown_portfolios = [p for p in recent_portfolios if p.drawdown and p.drawdown >= max_drawdown_stop_pct]
            if drawdown_portfolios:
                days_since_trigger = len([p for p in recent_portfolios if p.date >= drawdown_portfolios[0].date])
                days_left = max(0, drawdown_cooldown_days - days_since_trigger)
                risk_state['drawdown_stop'] = {
                    'active': days_left > 0,
                    'days_left': days_left
                }
        
        # Check momentum reversal: if in position and mom20 opposite sign for 3 consecutive days
        reversal_exit_days = self.params['reversal_exit_days']
        
        if portfolio and portfolio.positions_json:
            positions = portfolio.positions_json
            has_position = any(abs(qty) > 0.01 for qty in positions.values())
            
            if has_position:
                # Get recent signals to check momentum reversal
                recent_signals = db.query(SignalsDaily).filter(
                    and_(
                        SignalsDaily.strategy_id == self.strategy_id,
                        SignalsDaily.symbol == symbol,
                        SignalsDaily.date <= target_date
                    )
                ).order_by(SignalsDaily.date.desc()).limit(reversal_exit_days + 1).all()
                
                if len(recent_signals) >= reversal_exit_days + 1:
                    # Get current position direction
                    current_pos = positions.get(symbol, 0.0)
                    is_long = current_pos > 0.01
                    is_short = current_pos < -0.01
                    
                    if is_long or is_short:
                        # Check if momentum has been opposite for N consecutive days
                        opposite_count = 0
                        for i in range(reversal_exit_days):
                            if i < len(recent_signals) - 1:
                                signal = recent_signals[i]
                                prev_signal = recent_signals[i + 1]
                                
                                # Get reason_json to extract mom20
                                if signal.reason_json and prev_signal.reason_json:
                                    curr_mom = signal.reason_json.get('direction', {}).get('mom20')
                                    prev_mom = prev_signal.reason_json.get('direction', {}).get('mom20')
                                    
                                    if curr_mom is not None and prev_mom is not None:
                                        # Check if momentum flipped
                                        if is_long and curr_mom < 0 and prev_mom < 0:
                                            opposite_count += 1
                                        elif is_short and curr_mom > 0 and prev_mom > 0:
                                            opposite_count += 1
                        
                        if opposite_count >= reversal_exit_days:
                            risk_state['reversal_exit'] = {'active': True}
        
        return risk_state
    
    def generate_signal(
        self,
        db: Session,
        symbol: str,
        target_date: date,
        features: Optional[FeaturesDaily] = None
    ) -> Dict[str, Any]:
        """Generate trading signal"""
        # Get features if not provided
        if not features:
            features = db.query(FeaturesDaily).filter(
                FeaturesDaily.symbol == symbol,
                FeaturesDaily.date == target_date
            ).first()
        
        if not features:
            return {
                'signal': 'FLAT',
                'target_position': 0.0,
                'reason_json': {
                    'error': 'Features not available'
                }
            }
        
        # Check risk controls
        portfolio = db.query(PortfolioDaily).filter(
            PortfolioDaily.strategy_id == self.strategy_id,
            PortfolioDaily.date < target_date
        ).order_by(PortfolioDaily.date.desc()).first()
        
        risk_state = self.check_risk_controls(db, symbol, target_date, portfolio)
        
        # Check regime
        regime_on, regime_rules = self._check_regime(features)
        
        # If regime is OFF, return FLAT
        if not regime_on:
            return {
                'signal': 'FLAT',
                'target_position': 0.0,
                'reason_json': {
                    'strategy': self.strategy_id,
                    'version': self.version,
                    'regime': {
                        'on': False,
                        'rules': regime_rules
                    },
                    'direction': None,
                    'sizing': None,
                    'risk': risk_state,
                    'execution': {
                        'timing': self.params['execution_timing'],
                        'price_ref': 'close' if self.params['execution_timing'] == 'MOC' else 'next_open'
                    }
                }
            }
        
        # Compute direction
        direction = self._compute_direction(db, symbol, target_date, features)
        signal = direction['signal']
        
        # Apply risk controls
        if risk_state['cooldown']['active'] or risk_state['drawdown_stop']['active'] or risk_state['reversal_exit']['active']:
            signal = 'FLAT'
        
        # Compute position sizing
        sizing = self._compute_position_sizing(features, signal)
        
        # Build reason JSON
        reason_json = {
            'strategy': self.strategy_id,
            'version': self.version,
            'regime': {
                'on': True,
                'rules': regime_rules
            },
            'direction': direction,
            'sizing': sizing,
            'risk': risk_state,
            'execution': {
                'timing': self.params['execution_timing'],
                'price_ref': 'close' if self.params['execution_timing'] == 'MOC' else 'next_open'
            }
        }
        
        return {
            'signal': signal,
            'target_position': sizing['target_position'],
            'reason_json': reason_json
        }

