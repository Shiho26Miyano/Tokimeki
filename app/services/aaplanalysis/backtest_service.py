"""
Backtesting service for stock DCA and weekly option strategies
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from collections import defaultdict

from .polygon_service import PolygonService
from ...models.aapl_analysis_models import (
    StockDCARequest, WeeklyOptionRequest, CombinedBacktestRequest,
    StockDCAResult, WeeklyOptionResult, CombinedBacktestResult,
    StockEntry, OptionTrade, OptionType, BacktestDiagnostics,
    OHLCData, OptionContract
)

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Engine for running backtests on stock and option strategies"""
    
    def __init__(self, polygon_service: PolygonService):
        self.polygon = polygon_service
        self.diagnostics = {
            'missing_entry_dates': [],
            'no_option_contracts_dates': [],
            'fallback_intrinsic_exits': 0,
            'api_errors': []
        }
    
    def _get_trading_dates(self, start_date: date, end_date: date, weekday: int) -> List[date]:
        """Get all trading dates for a specific weekday between start and end dates"""
        trading_dates = []
        current_date = start_date
        
        # Find first occurrence of the weekday
        while current_date.weekday() != weekday and current_date <= end_date:
            current_date += timedelta(days=1)
        
        # Add all subsequent occurrences
        while current_date <= end_date:
            trading_dates.append(current_date)
            current_date += timedelta(days=7)
        
        return trading_dates
    
    def _find_closest_price(self, target_date: date, price_data: List[OHLCData]) -> Optional[float]:
        """Find the closest available price to the target date"""
        if not price_data:
            return None
        
        # Create date to price mapping
        price_map = {data.timestamp.date(): data.close for data in price_data}
        
        # Try exact match first
        if target_date in price_map:
            return price_map[target_date]
        
        # Find closest date within 5 days
        for days_offset in range(1, 6):
            # Try previous days first (more likely to have data)
            prev_date = target_date - timedelta(days=days_offset)
            if prev_date in price_map:
                return price_map[prev_date]
            
            # Then try next days
            next_date = target_date + timedelta(days=days_offset)
            if next_date in price_map:
                return price_map[next_date]
        
        return None
    
    def _find_best_option_contract(
        self,
        contracts: List[OptionContract],
        target_moneyness: float,
        underlying_price: float,
        min_days_to_expiry: int
    ) -> Optional[OptionContract]:
        """Find the best option contract based on moneyness and expiry criteria"""
        if not contracts:
            return None
        
        # Filter by minimum days to expiry
        valid_contracts = [c for c in contracts if c.days_to_expiry >= min_days_to_expiry]
        if not valid_contracts:
            return None
        
        # Calculate target strike price
        target_strike = underlying_price * (1 + target_moneyness)
        
        # Find contract with strike closest to target
        best_contract = min(
            valid_contracts,
            key=lambda c: abs(c.strike_price - target_strike)
        )
        
        return best_contract
    
    def _calculate_intrinsic_value(
        self,
        option_type: OptionType,
        strike_price: float,
        underlying_price: float
    ) -> float:
        """Calculate intrinsic value of option at expiry"""
        if option_type == OptionType.CALL:
            return max(0, underlying_price - strike_price)
        else:  # PUT
            return max(0, strike_price - underlying_price)
    
    async def run_stock_dca_backtest(self, request: StockDCARequest) -> StockDCAResult:
        """Run backtest for stock DCA strategy"""
        logger.info(f"Running stock DCA backtest for {request.ticker}")
        
        # Get stock price data
        try:
            price_response = await self.polygon.get_stock_prices(
                request.ticker,
                request.start_date,
                request.end_date
            )
        except Exception as e:
            logger.error(f"Failed to get stock prices: {e}")
            self.diagnostics['api_errors'].append(str(e))
            raise
        
        # Get trading dates
        trading_dates = self._get_trading_dates(
            request.start_date,
            request.end_date,
            request.buy_weekday
        )
        
        # Execute DCA strategy
        entries = []
        total_shares = 0
        total_cost = 0.0
        total_fees = 0.0
        
        for trade_date in trading_dates:
            price = self._find_closest_price(trade_date, price_response.data)
            
            if price is None:
                self.diagnostics['missing_entry_dates'].append(trade_date)
                continue
            
            # Calculate trade details
            cost = request.shares_per_week * price
            fees = request.fee_per_trade
            total_shares += request.shares_per_week
            total_cost += cost + fees
            total_fees += fees
            
            entry = StockEntry(
                date=trade_date,
                shares=request.shares_per_week,
                price=price,
                cost=cost,
                fees=fees,
                cumulative_shares=total_shares,
                cumulative_cost=total_cost
            )
            entries.append(entry)
        
        # Calculate final metrics
        final_price = price_response.data[-1].close if price_response.data else 0.0
        market_value = total_shares * final_price
        unrealized_pnl = market_value - total_cost
        cost_basis = total_cost / max(total_shares, 1)
        
        return StockDCAResult(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            total_entries=len(entries),
            total_shares=total_shares,
            total_cost=total_cost,
            total_fees=total_fees,
            final_price=final_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            cost_basis=cost_basis,
            entries=entries
        )
    
    async def run_weekly_option_backtest(self, request: WeeklyOptionRequest) -> WeeklyOptionResult:
        """Run backtest for weekly option strategy"""
        logger.info(f"Running weekly option backtest for {request.ticker}")
        
        # Get stock price data for underlying
        try:
            price_response = await self.polygon.get_stock_prices(
                request.ticker,
                request.start_date,
                request.end_date
            )
        except Exception as e:
            logger.error(f"Failed to get stock prices: {e}")
            self.diagnostics['api_errors'].append(str(e))
            raise
        
        # Create price lookup
        price_map = {data.timestamp.date(): data.close for data in price_response.data}
        
        # Get trading dates
        trading_dates = self._get_trading_dates(
            request.start_date,
            request.end_date,
            request.buy_weekday
        )
        
        trades = []
        total_pnl = 0.0
        total_fees = 0.0
        winning_trades = 0
        losing_trades = 0
        pnl_values = []
        
        for trade_date in trading_dates:
            underlying_price = price_map.get(trade_date)
            if underlying_price is None:
                self.diagnostics['missing_entry_dates'].append(trade_date)
                continue
            
            # Find next Friday for weekly expiry (simplified)
            expiry_date = trade_date
            while expiry_date.weekday() != 4:  # Friday
                expiry_date += timedelta(days=1)
            
            # Get option contracts for expiry date
            try:
                option_chain = await self.polygon.get_option_contracts(
                    request.ticker,
                    expiry_date,
                    underlying_price
                )
            except Exception as e:
                logger.warning(f"Failed to get option contracts for {expiry_date}: {e}")
                self.diagnostics['no_option_contracts_dates'].append(trade_date)
                continue
            
            # Select appropriate contracts
            contracts = option_chain.calls if request.option_type == OptionType.CALL else option_chain.puts
            
            best_contract = self._find_best_option_contract(
                contracts,
                request.moneyness_offset,
                underlying_price,
                request.min_days_to_expiry
            )
            
            if best_contract is None:
                self.diagnostics['no_option_contracts_dates'].append(trade_date)
                continue
            
            # Try to get option price data
            try:
                option_ohlc = await self.polygon.get_option_ohlc(
                    best_contract.ticker,
                    trade_date,
                    expiry_date
                )
                
                # Find entry and exit prices
                entry_price = self._find_closest_price(trade_date, option_ohlc.data)
                exit_price = self._find_closest_price(expiry_date, option_ohlc.data)
                
            except Exception:
                # Fallback to intrinsic value calculation
                entry_price = None
                exit_price = None
            
            # Use intrinsic value if no market data available
            if entry_price is None or exit_price is None:
                self.diagnostics['fallback_intrinsic_exits'] += 1
                
                # Estimate entry price (simplified)
                entry_price = entry_price or max(0.50, underlying_price * 0.02)  # Rough estimate
                
                # Calculate exit price using intrinsic value
                expiry_underlying_price = price_map.get(expiry_date, underlying_price)
                exit_price = self._calculate_intrinsic_value(
                    request.option_type,
                    best_contract.strike_price,
                    expiry_underlying_price
                )
            
            # Calculate trade PnL
            trade_pnl = (exit_price - entry_price) * request.contracts_per_week * 100  # Options are per 100 shares
            trade_fees = request.fee_per_trade * 2  # Entry and exit
            net_pnl = trade_pnl - trade_fees
            
            total_pnl += net_pnl
            total_fees += trade_fees
            pnl_values.append(net_pnl)
            
            if net_pnl > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            # Determine trade status
            if exit_price == 0:
                status = "expired_worthless"
            elif exit_price == self._calculate_intrinsic_value(request.option_type, best_contract.strike_price, price_map.get(expiry_date, underlying_price)):
                status = "expired_itm"
            else:
                status = "closed"
            
            trade = OptionTrade(
                entry_date=trade_date,
                exit_date=expiry_date,
                option_ticker=best_contract.ticker,
                option_type=request.option_type,
                strike_price=best_contract.strike_price,
                expiration_date=expiry_date,
                entry_price=entry_price,
                exit_price=exit_price,
                contracts=request.contracts_per_week,
                pnl=net_pnl,
                fees=trade_fees,
                status=status,
                days_held=(expiry_date - trade_date).days
            )
            trades.append(trade)
        
        # Calculate summary statistics
        total_trades = len(trades)
        win_rate = winning_trades / max(total_trades, 1)
        
        winning_pnls = [pnl for pnl in pnl_values if pnl > 0]
        losing_pnls = [pnl for pnl in pnl_values if pnl <= 0]
        
        avg_win = sum(winning_pnls) / max(len(winning_pnls), 1)
        avg_loss = sum(losing_pnls) / max(len(losing_pnls), 1)
        max_win = max(pnl_values) if pnl_values else 0.0
        max_loss = min(pnl_values) if pnl_values else 0.0
        
        return WeeklyOptionResult(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            option_type=request.option_type,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            total_fees=total_fees,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_win=max_win,
            max_loss=max_loss,
            trades=trades
        )
    
    async def run_combined_backtest(self, request: CombinedBacktestRequest) -> CombinedBacktestResult:
        """Run both stock DCA and weekly option backtests"""
        logger.info("Running combined backtest")
        
        # Run both strategies in parallel
        stock_result, option_result = await asyncio.gather(
            self.run_stock_dca_backtest(request.stock_params),
            self.run_weekly_option_backtest(request.option_params)
        )
        
        # Calculate comparison metrics
        comparison_metrics = {
            'stock_total_return': stock_result.unrealized_pnl,
            'stock_return_pct': (stock_result.unrealized_pnl / max(stock_result.total_cost, 1)) * 100,
            'option_total_return': option_result.total_pnl,
            'option_return_pct': 0.0,  # Would need initial capital to calculate
            'stock_sharpe_ratio': 0.0,  # Would need daily returns to calculate
            'option_sharpe_ratio': 0.0,  # Would need daily returns to calculate
            'combined_return': stock_result.unrealized_pnl + option_result.total_pnl,
            'stock_max_drawdown': 0.0,  # Would need to track equity curve
            'option_max_drawdown': 0.0,  # Would need to track equity curve
        }
        
        return CombinedBacktestResult(
            stock_result=stock_result,
            option_result=option_result,
            comparison_metrics=comparison_metrics
        )
    
    def get_diagnostics(self) -> BacktestDiagnostics:
        """Get backtest diagnostics"""
        total_expected = len(self.diagnostics['missing_entry_dates']) + len(self.diagnostics['no_option_contracts_dates'])
        actual_entries = total_expected - len(self.diagnostics['missing_entry_dates'])
        
        data_quality_score = 1.0
        if total_expected > 0:
            data_quality_score = actual_entries / total_expected
        
        return BacktestDiagnostics(
            total_expected_entries=total_expected,
            actual_entries=actual_entries,
            missing_entry_dates=self.diagnostics['missing_entry_dates'],
            no_option_contracts_dates=self.diagnostics['no_option_contracts_dates'],
            fallback_intrinsic_exits=self.diagnostics['fallback_intrinsic_exits'],
            data_quality_score=data_quality_score
        )
