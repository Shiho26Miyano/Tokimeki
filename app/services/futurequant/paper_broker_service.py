"""
FutureQuant Trader Paper Broker Service - Enhanced Engine
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid
import json

from app.models.trading_models import Symbol, Bar, Feature, Forecast, Strategy, Trade, User
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantPaperBrokerService:
    """Enhanced paper trading engine for distributional futures strategies"""
    
    def __init__(self):
        self.active_sessions = {}
        self.order_counter = 0
        
        # Default risk parameters
        self.default_risk_params = {
            "max_position_size": 0.20,      # Max 20% in single position
            "max_leverage": 2.0,            # Max 2x leverage
            "max_daily_loss": 0.05,         # Max 5% daily loss
            "max_drawdown": 0.25,           # Max 25% drawdown
            "position_sizing": "kelly",     # Kelly criterion
            "stop_loss_type": "quantile",   # Quantile-based stops
            "take_profit_type": "quantile", # Quantile-based targets
            "trailing_stop": True,          # Enable trailing stops
            "cooldown_after_stop": 2,       # Days to wait after stop loss
            "max_trades_per_day": 5,        # Max trades per day
            "min_probability": 0.60,        # Minimum probability for entry
            "volatility_adjustment": True   # Adjust position size by volatility
        }
    
    async def start_paper_trading(
        self,
        user_id: int,
        strategy_id: int,
        initial_capital: float = 100000,
        risk_params: Dict[str, Any] = None,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """Start a new paper trading session"""
        try:
            # Get database session
            db = next(get_db())
            
            # Validate user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Validate strategy
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Merge risk parameters
            risk_config = self.default_risk_params.copy()
            if risk_params:
                risk_config.update(risk_params)
            
            # Initialize session
            session = {
                'session_id': session_id,
                'user_id': user_id,
                'strategy_id': strategy_id,
                'strategy_name': strategy.name,
                'start_time': datetime.now(),
                'status': 'active',
                'initial_capital': initial_capital,
                'current_capital': initial_capital,
                'cash': initial_capital,
                'positions': {},
                'orders': [],
                'trades': [],
                'daily_pnl': [],
                'risk_params': risk_config,
                'symbols': symbols or [],
                'constraints_violated': [],
                'last_rebalance': datetime.now(),
                'daily_trades': 0,
                'last_trade_date': None
            }
            
            # Store session
            self.active_sessions[session_id] = session
            
            logger.info(f"Started paper trading session {session_id} for user {user_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Paper trading session started successfully',
                'session_info': {
                    'strategy_name': strategy.name,
                    'initial_capital': initial_capital,
                    'risk_params': risk_config,
                    'symbols': symbols or []
                }
            }
            
        except Exception as e:
            logger.error(f"Error starting paper trading: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def stop_paper_trading(self, session_id: str) -> Dict[str, Any]:
        """Stop a paper trading session"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Close all positions
            await self._close_all_positions(session)
            
            # Calculate final P&L
            final_pnl = session['current_capital'] - session['initial_capital']
            total_return = (final_pnl / session['initial_capital']) * 100
            
            # Update session status
            session['status'] = 'stopped'
            session['end_time'] = datetime.now()
            session['final_capital'] = session['current_capital']
            session['total_return'] = total_return
            
            # Generate session summary
            summary = await self._generate_session_summary(session)
            
            logger.info(f"Stopped paper trading session {session_id}")
            
            return {
                'success': True,
                'message': 'Paper trading session stopped successfully',
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error stopping paper trading: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def place_order(
        self,
        session_id: str,
        symbol: str,
        side: str,
        order_type: str = "market",
        quantity: float = None,
        price: float = None,
        stop_loss: float = None,
        take_profit: float = None,
        strategy_signal: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Place an order in paper trading"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            if session['status'] != 'active':
                raise ValueError("Session is not active")
            
            # Validate order parameters
            if side not in ['buy', 'sell']:
                raise ValueError("Side must be 'buy' or 'sell'")
            
            if order_type not in ['market', 'limit', 'stop']:
                raise ValueError("Order type must be 'market', 'limit', or 'stop'")
            
            # Get current market data
            current_price = await self._get_current_price(symbol)
            if not current_price:
                raise ValueError(f"Unable to get current price for {symbol}")
            
            # Calculate position size if not provided
            if quantity is None:
                quantity = await self._calculate_distribution_position_size(
                    session, symbol, side, strategy_signal
                )
                if quantity <= 0:
                    return {
                        'success': False,
                        'error': 'Position size calculation resulted in zero or negative quantity'
                    }
            
            # Validate risk constraints
            risk_check = await self._validate_order_risk(session, symbol, side, quantity, current_price)
            if not risk_check['valid']:
                return {
                    'success': False,
                    'error': f"Risk constraints violated: {', '.join(risk_check['violations'])}"
                }
            
            # Create order
            order_id = self._generate_order_id()
            order = {
                'order_id': order_id,
                'session_id': session_id,
                'symbol': symbol,
                'side': side,
                'order_type': order_type,
                'quantity': quantity,
                'price': price or current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'status': 'pending',
                'timestamp': datetime.now(),
                'strategy_signal': strategy_signal
            }
            
            # Execute order
            execution_result = await self._execute_order(session, order, current_price)
            
            if execution_result['success']:
                # Add order to session
                session['orders'].append(order)
                session['daily_trades'] += 1
                session['last_trade_date'] = datetime.now().date()
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'message': 'Order executed successfully',
                    'execution_details': execution_result['details']
                }
            else:
                return {
                    'success': False,
                    'error': execution_result['error']
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _calculate_distribution_position_size(
        self,
        session: Dict[str, Any],
        symbol: str,
        side: str,
        strategy_signal: Dict[str, Any] = None
    ) -> float:
        """Calculate position size using distribution-aware Kelly criterion"""
        try:
            risk_config = session['risk_params']
            sizing_method = risk_config.get('position_sizing', 'kelly')
            
            if sizing_method == 'kelly' and strategy_signal:
                # Kelly criterion based on distributional forecasts
                prob_up = strategy_signal.get('prob_up', 0.5)
                q10 = strategy_signal.get('q10', 0)
                q50 = strategy_signal.get('q50', 0)
                q90 = strategy_signal.get('q90', 0)
                volatility = strategy_signal.get('volatility', 0)
                
                current_price = await self._get_current_price(symbol)
                if not current_price:
                    return 0.0
                
                # Calculate win probability and odds
                if side == 'buy':  # Long position
                    p = prob_up
                    q = 1 - prob_up
                    # Odds = (take_profit - entry) / (entry - stop_loss)
                    take_profit = q90 if q90 > current_price else current_price * 1.05
                    stop_loss = q10 if q10 < current_price else current_price * 0.95
                    odds = (take_profit - current_price) / (current_price - stop_loss) if current_price > stop_loss else 1.0
                else:  # Short position
                    p = 1 - prob_up
                    q = prob_up
                    # Odds = (entry - take_profit) / (stop_loss - entry)
                    take_profit = q10 if q10 < current_price else current_price * 0.95
                    stop_loss = q90 if q90 > current_price else current_price * 1.05
                    odds = (current_price - take_profit) / (stop_loss - current_price) if stop_loss > current_price else 1.0
                
                # Kelly fraction
                if p > 0.5 and odds > 1.0:
                    kelly_fraction = (odds * p - q) / odds
                    # Clamp between 0 and 0.25 (max 25% per trade)
                    kelly_fraction = max(0.0, min(kelly_fraction, 0.25))
                else:
                    kelly_fraction = 0.0
                
                # Volatility adjustment
                if risk_config.get('volatility_adjustment', True) and volatility > 0:
                    vol_factor = 1.0 / (1.0 + volatility)
                    kelly_fraction *= vol_factor
                
                # Apply to available capital
                available_capital = session['cash']
                position_value = kelly_fraction * available_capital
                
                # Convert to quantity
                quantity = position_value / current_price
                
                # Apply position size limits
                max_position_value = session['current_capital'] * risk_config.get('max_position_size', 0.20)
                if position_value > max_position_value:
                    position_value = max_position_value
                    quantity = position_value / current_price
                
                return quantity
                
            else:
                # Fixed sizing
                position_value = session['current_capital'] * 0.1  # 10% default
                current_price = await self._get_current_price(symbol)
                if current_price:
                    return position_value / current_price
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0
    
    async def _validate_order_risk(
        self,
        session: Dict[str, Any],
        symbol: str,
        side: str,
        quantity: float,
        current_price: float
    ) -> Dict[str, Any]:
        """Validate order against risk constraints"""
        violations = []
        
        risk_config = session['risk_params']
        
        # Check leverage constraints
        current_positions_value = sum(pos['value'] for pos in session['positions'].values())
        new_position_value = quantity * current_price
        total_exposure = current_positions_value + new_position_value
        current_leverage = total_exposure / session['current_capital']
        
        if current_leverage > risk_config.get('max_leverage', 2.0):
            violations.append('max_leverage')
        
        # Check position size limits
        position_weight = new_position_value / session['current_capital']
        if position_weight > risk_config.get('max_position_size', 0.20):
            violations.append('max_position_size')
        
        # Check daily trade limit
        if session['last_trade_date'] == datetime.now().date():
            if session['daily_trades'] >= risk_config.get('max_trades_per_day', 5):
                violations.append('max_daily_trades')
        else:
            # Reset daily trade counter for new day
            session['daily_trades'] = 0
        
        # Check daily loss limit
        if session['daily_pnl']:
            today_pnl = [pnl for pnl in session['daily_pnl'] 
                        if pnl['date'] == datetime.now().date()]
            if today_pnl:
                daily_return = (session['current_capital'] - today_pnl[0]['capital']) / today_pnl[0]['capital']
                if daily_return < -risk_config.get('max_daily_loss', 0.05):
                    violations.append('max_daily_loss')
        
        # Check cooldown after stop loss
        if session['constraints_violated']:
            last_stop_violation = [v for v in session['constraints_violated'] 
                                 if 'stop_loss' in v.get('type', '')]
            if last_stop_violation:
                last_violation_time = last_stop_violation[-1]['timestamp']
                cooldown_days = risk_config.get('cooldown_after_stop', 2)
                if (datetime.now() - last_violation_time).days < cooldown_days:
                    violations.append('cooldown_after_stop')
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    async def _execute_order(
        self,
        session: Dict[str, Any],
        order: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Execute an order"""
        try:
            symbol = order['symbol']
            side = order['side']
            quantity = order['quantity']
            
            # Calculate execution price (with slippage simulation)
            slippage_bps = 1.0  # 1 basis point slippage
            execution_price = current_price * (1 + (slippage_bps / 10000) if side == 'buy' else 1 - (slippage_bps / 10000))
            
            # Calculate costs
            commission_rate = 0.0002  # 2 basis points
            commission = quantity * execution_price * commission_rate
            total_cost = commission
            
            # Check if we have enough cash
            required_cash = quantity * execution_price + total_cost
            if side == 'buy' and session['cash'] < required_cash:
                return {
                    'success': False,
                    'error': 'Insufficient cash for order'
                }
            
            # Execute the order
            if side == 'buy':
                # Open long position
                if symbol in session['positions']:
                    # Add to existing position
                    existing_pos = session['positions'][symbol]
                    total_quantity = existing_pos['quantity'] + quantity
                    avg_price = ((existing_pos['quantity'] * existing_pos['entry_price']) + 
                               (quantity * execution_price)) / total_quantity
                    
                    session['positions'][symbol] = {
                        'side': 'long',
                        'quantity': total_quantity,
                        'entry_price': avg_price,
                        'entry_time': datetime.now(),
                        'value': total_quantity * current_price,
                        'stop_loss': order.get('stop_loss'),
                        'take_profit': order.get('take_profit')
                    }
                else:
                    # New position
                    session['positions'][symbol] = {
                        'side': 'long',
                        'quantity': quantity,
                        'entry_price': execution_price,
                        'entry_time': datetime.now(),
                        'value': quantity * current_price,
                        'stop_loss': order.get('stop_loss'),
                        'take_profit': order.get('take_profit')
                    }
                
                # Deduct cash
                session['cash'] -= required_cash
                
            else:  # sell
                # Close long position or open short
                if symbol in session['positions'] and session['positions'][symbol]['side'] == 'long':
                    # Close long position
                    position = session['positions'][symbol]
                    pnl = (execution_price - position['entry_price']) * quantity - total_cost
                    
                    # Add cash back
                    session['cash'] += (quantity * execution_price - total_cost)
                    
                    # Remove position
                    del session['positions'][symbol]
                    
                    # Record trade
                    trade = {
                        'trade_id': str(uuid.uuid4()),
                        'session_id': session['session_id'],
                        'symbol': symbol,
                        'side': 'sell',
                        'quantity': quantity,
                        'entry_price': position['entry_price'],
                        'exit_price': execution_price,
                        'pnl': pnl,
                        'commission': commission,
                        'timestamp': datetime.now()
                    }
                    session['trades'].append(trade)
                    
                    # Update capital
                    session['current_capital'] += pnl
                    
                else:
                    # Open short position
                    if symbol in session['positions']:
                        # Add to existing short position
                        existing_pos = session['positions'][symbol]
                        total_quantity = existing_pos['quantity'] + quantity
                        avg_price = ((existing_pos['quantity'] * existing_pos['entry_price']) + 
                                   (quantity * execution_price)) / total_quantity
                        
                        session['positions'][symbol] = {
                            'side': 'short',
                            'quantity': total_quantity,
                            'entry_price': avg_price,
                            'entry_time': datetime.now(),
                            'value': total_quantity * current_price,
                            'stop_loss': order.get('stop_loss'),
                            'take_profit': order.get('take_profit')
                        }
                    else:
                        # New short position
                        session['positions'][symbol] = {
                            'side': 'short',
                            'quantity': quantity,
                            'entry_price': execution_price,
                            'entry_time': datetime.now(),
                            'value': quantity * current_price,
                            'stop_loss': order.get('stop_loss'),
                            'take_profit': order.get('take_profit')
                        }
                    
                    # Add cash (short sale proceeds)
                    session['cash'] += (quantity * execution_price - total_cost)
            
            # Update order status
            order['status'] = 'executed'
            order['execution_price'] = execution_price
            order['execution_time'] = datetime.now()
            order['commission'] = commission
            
            # Update position values
            await self._update_position_values(session)
            
            return {
                'success': True,
                'details': {
                    'execution_price': execution_price,
                    'commission': commission,
                    'pnl': pnl if side == 'sell' else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _update_position_values(self, session: Dict[str, Any]) -> None:
        """Update position values based on current market prices"""
        for symbol, position in session['positions'].items():
            current_price = await self._get_current_price(symbol)
            if current_price:
                if position['side'] == 'long':
                    position['value'] = position['quantity'] * current_price
                else:  # short
                    position['value'] = position['quantity'] * (2 * position['entry_price'] - current_price)
        
        # Update total capital
        positions_value = sum(pos['value'] for pos in session['positions'].values())
        session['current_capital'] = session['cash'] + positions_value
    
    async def _close_all_positions(self, session: Dict[str, Any]) -> None:
        """Close all positions in the session"""
        symbols_to_close = list(session['positions'].keys())
        
        for symbol in symbols_to_close:
            current_price = await self._get_current_price(symbol)
            if current_price:
                position = session['positions'][symbol]
                
                # Calculate P&L
                if position['side'] == 'long':
                    pnl = (current_price - position['entry_price']) * position['quantity']
                else:  # short
                    pnl = (position['entry_price'] - current_price) * position['quantity']
                
                # Calculate costs
                commission_rate = 0.0002
                commission = position['quantity'] * current_price * commission_rate
                pnl -= commission
                
                # Update cash
                if position['side'] == 'long':
                    session['cash'] += (position['quantity'] * current_price - commission)
                else:  # short
                    session['cash'] += (position['quantity'] * (2 * position['entry_price'] - current_price) - commission)
                
                # Record trade
                trade = {
                    'trade_id': str(uuid.uuid4()),
                    'session_id': session['session_id'],
                    'symbol': symbol,
                    'side': 'sell' if position['side'] == 'long' else 'buy',
                    'quantity': position['quantity'],
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'pnl': pnl,
                    'commission': commission,
                    'timestamp': datetime.now()
                }
                session['trades'].append(trade)
                
                # Remove position
                del session['positions'][symbol]
        
        # Update capital
        session['current_capital'] = session['cash']
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # This would typically fetch from a real-time data source
            # For now, return a placeholder price
            return 100.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID"""
        self.order_counter += 1
        return f"ORD_{datetime.now().strftime('%Y%m%d')}_{self.order_counter:06d}"
    
    async def _generate_session_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the trading session"""
        try:
            # Calculate performance metrics
            total_trades = len(session['trades'])
            winning_trades = len([t for t in session['trades'] if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in session['trades'] if t.get('pnl', 0) < 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_pnl = sum(t.get('pnl', 0) for t in session['trades'])
            total_commission = sum(t.get('commission', 0) for t in session['trades'])
            
            # Calculate returns
            total_return = (session['final_capital'] - session['initial_capital']) / session['initial_capital']
            
            # Calculate drawdown
            max_drawdown = 0
            if session['daily_pnl']:
                peak_capital = session['initial_capital']
                for pnl in session['daily_pnl']:
                    if pnl['capital'] > peak_capital:
                        peak_capital = pnl['capital']
                    drawdown = (peak_capital - pnl['capital']) / peak_capital
                    max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'session_id': session['session_id'],
                'strategy_name': session['strategy_name'],
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'duration_days': (session['end_time'] - session['start_time']).days,
                'initial_capital': session['initial_capital'],
                'final_capital': session['final_capital'],
                'total_return': total_return,
                'total_pnl': total_pnl,
                'total_commission': total_commission,
                'net_pnl': total_pnl - total_commission,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'constraints_violated': len(session['constraints_violated'])
            }
            
        except Exception as e:
            logger.error(f"Error generating session summary: {str(e)}")
            return {}
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a paper trading session"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Update position values
            await self._update_position_values(session)
            
            # Calculate current P&L
            current_pnl = session['current_capital'] - session['initial_capital']
            current_return = (current_pnl / session['initial_capital']) * 100
            
            return {
                'success': True,
                'session_id': session_id,
                'status': session['status'],
                'strategy_name': session['strategy_name'],
                'start_time': session['start_time'],
                'initial_capital': session['initial_capital'],
                'current_capital': session['current_capital'],
                'cash': session['cash'],
                'positions_value': sum(pos['value'] for pos in session['positions'].values()),
                'current_pnl': current_pnl,
                'current_return': current_return,
                'total_trades': len(session['trades']),
                'daily_trades': session['daily_trades'],
                'positions': session['positions'],
                'risk_params': session['risk_params']
            }
            
        except Exception as e:
            logger.error(f"Error getting session status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active paper trading sessions"""
        try:
            active_sessions = {}
            
            for session_id, session in self.active_sessions.items():
                if session['status'] == 'active':
                    # Update position values
                    await self._update_position_values(session)
                    
                    active_sessions[session_id] = {
                        'user_id': session['user_id'],
                        'strategy_name': session['strategy_name'],
                        'start_time': session['start_time'],
                        'initial_capital': session['initial_capital'],
                        'current_capital': session['current_capital'],
                        'current_return': ((session['current_capital'] - session['initial_capital']) / 
                                         session['initial_capital']) * 100,
                        'total_trades': len(session['trades']),
                        'positions_count': len(session['positions'])
                    }
            
            return {
                'success': True,
                'active_sessions': active_sessions,
                'total_sessions': len(active_sessions)
            }
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_all_positions(self, session_id: str) -> Dict[str, Any]:
        """Close all positions in a session"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            if session['status'] != 'active':
                raise ValueError("Session is not active")
            
            # Close all positions
            await self._close_all_positions(session)
            
            return {
                'success': True,
                'message': 'All positions closed successfully',
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Error closing all positions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
