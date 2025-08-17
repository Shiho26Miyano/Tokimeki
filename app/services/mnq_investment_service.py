import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import numpy as np
import pandas as pd
import math
from app.services.cache_service import AsyncCacheService

logger = logging.getLogger(__name__)


class AsyncMNQInvestmentService:
    def __init__(self, cache_service: AsyncCacheService):
        self.cache_service = cache_service
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.mnq_symbol = "MNQ=F"  # Micro E-mini NASDAQ-100 futures
        self.contract_multiplier = 2  # $2 per point (Micro E-mini NASDAQ-100)
        self.margin_per_contract = 1000  # $1000 initial margin per contract (approximate)
        self.maintenance_margin_per_contract = 800  # $800 maintenance margin per contract
        self.commission_per_contract = 2.50  # $2.50 commission per contract
        self.slippage_per_contract = 1.00  # $1.00 estimated slippage per contract
        self.max_contracts = 100  # Maximum contracts to prevent runaway leverage

    async def calculate_weekly_dca_performance(
        self,
        weekly_amount: float = 1000.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculate weekly DCA performance for MNQ futures"""
        try:
            logger.info(f"Starting MNQ DCA calculation: ${weekly_amount}/week")

            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            # Get MNQ futures data
            data = await self.get_mnq_futures_data(start_date, end_date)
            if not data or not data.get('data'):
                raise Exception("No MNQ futures data available")

            # Calculate weekly DCA performance
            result = await self._calculate_dca_performance(data, weekly_amount, start_date, end_date)

            logger.info("MNQ DCA calculation completed successfully")
            return result
        except Exception as e:
            logger.error(f"MNQ DCA calculation error: {e}")
            raise

    async def get_mnq_futures_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get MNQ futures price data"""
        cache_key = f"mnq_data_{start_date}_{end_date}"

        # Check cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info("Retrieved MNQ data from cache")
            return cached_data

        try:
            # Fetch data using yfinance
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor,
                self._fetch_mnq_data,
                start_date,
                end_date,
            )

            # Cache the data for 1 hour
            await self.cache_service.set(cache_key, data, ttl=3600)
            return data
        except Exception as e:
            logger.error(f"Error fetching MNQ data: {e}")
            raise

    def _fetch_mnq_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch MNQ data using yfinance (runs in executor)"""
        try:
            ticker = yf.Ticker(self.mnq_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            if hist.empty:
                raise Exception("No historical data available")

            # Convert to list of dictionaries
            data = []
            for date, row in hist.iterrows():
                data.append(
                    {
                        'Date': date.strftime('%Y-%m-%d'),
                        'Open': float(row['Open']),
                        'High': float(row['High']),
                        'Low': float(row['Low']),
                        'Close': float(row['Close']),
                        'Adj Close': float(row.get('Adj Close', row['Close'])),
                        'Volume': int(row['Volume']),
                    }
                )

            return {
                'symbol': self.mnq_symbol,
                'data': data,
                'start_date': start_date,
                'end_date': end_date,
            }
        except Exception as e:
            logger.error(f"Error in _fetch_mnq_data: {e}")
            raise

    async def _calculate_dca_performance(
        self,
        data: Dict[str, Any],
        weekly_amount: float,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Calculate DCA performance metrics"""
        try:
            # Group data by week (Friday close)
            weekly_data = self._group_by_week(data['data'])

            # Calculate DCA performance
            dca_results = self._simulate_dca_investment(weekly_data, weekly_amount)

            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(dca_results)

            return {
                'success': True,
                'weekly_amount': weekly_amount,
                'start_date': start_date,
                'end_date': end_date,
                'total_weeks': len(weekly_data),
                'total_invested': dca_results['total_invested'],
                'current_value': dca_results['current_value'],
                'total_return': metrics['total_return'],
                'weekly_breakdown': dca_results['weekly_breakdown'],
                'performance_metrics': metrics,
                'equity_curve': dca_results['equity_curve'],
            }
        except Exception as e:
            logger.error(f"Error calculating DCA performance: {e}")
            raise

    def _group_by_week(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group daily data by week using pandas resample (Friday close)"""
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        price_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'

        # Resample to weekly Friday close
        weekly_df = df[price_col].resample('W-FRI').last().dropna()

        weekly_data: List[Dict[str, Any]] = []
        for date, price in weekly_df.items():
            weekly_data.append({'Date': date.strftime('%Y-%m-%d'), 'Close': float(price)})
        return weekly_data

    def _simulate_dca_investment(
        self,
        weekly_data: List[Dict[str, Any]],
        weekly_amount: float,
    ) -> Dict[str, Any]:
        """Simulate weekly DCA investment with futures-style margin logic.

        NOTE: This simplified model values equity as cash + position_value.
        That implicitly treats contract notional as an asset; opening trades
        do not debit notional, only fees. Liquidations transfer notional to cash,
        keeping equity nearly unchanged net of fees. This is internally consistent
        but not a full variation-margin model.
        """
        cash_balance = 0.0  # Track unspent cash
        total_contracts = 0  # Integer contracts only
        total_invested = 0.0
        weekly_breakdown: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []
        prev_equity = 0.0

        for i, week_data in enumerate(weekly_data):
            price = float(week_data['Close'])
            date = week_data['Date']

            # Add weekly contribution
            cash_balance += weekly_amount
            total_invested += weekly_amount

            # Pre-trade equity
            position_value = total_contracts * price * self.contract_multiplier
            current_equity = cash_balance + position_value

            # --- Margin-based buying logic (initial margin to open) ---
            def can_hold(k: int) -> bool:
                if k <= 0:
                    return True
                if total_contracts + k > self.max_contracts:
                    return False
                fees = k * (self.commission_per_contract + self.slippage_per_contract)
                eq_after = current_equity - fees
                req_initial_after = (total_contracts + k) * self.margin_per_contract
                return eq_after >= req_initial_after

            contracts_to_buy = 0
            # Safety guard in pathological cases
            while can_hold(contracts_to_buy + 1) and contracts_to_buy < 10_000:
                contracts_to_buy += 1

            if contracts_to_buy > 0:
                total_fees = contracts_to_buy * (self.commission_per_contract + self.slippage_per_contract)
                cash_balance -= total_fees  # pay fees only
                total_contracts += contracts_to_buy
                # Recompute equity after trade
                position_value = total_contracts * price * self.contract_multiplier
                current_equity = cash_balance + position_value

            # --- Maintenance margin & forced liquidation ---
            required_margin = total_contracts * self.maintenance_margin_per_contract
            if current_equity < required_margin and total_contracts > 0:
                deficit = required_margin - current_equity
                contracts_to_liquidate = math.ceil(deficit / self.maintenance_margin_per_contract)
                contracts_to_liquidate = min(contracts_to_liquidate, total_contracts)

                if contracts_to_liquidate > 0:
                    liquidation_proceeds = contracts_to_liquidate * price * self.contract_multiplier
                    liquidation_commissions = contracts_to_liquidate * self.commission_per_contract
                    liquidation_slippage = contracts_to_liquidate * self.slippage_per_contract
                    net_proceeds = liquidation_proceeds - liquidation_commissions - liquidation_slippage

                    total_contracts -= contracts_to_liquidate
                    cash_balance += net_proceeds

                    # Recalculate after liquidation
                    position_value = total_contracts * price * self.contract_multiplier
                    current_equity = cash_balance + position_value

            # Time-weighted return (exclude external cash flow this week)
            if prev_equity > 0:
                time_weighted_return = (current_equity - prev_equity - weekly_amount) / prev_equity
            else:
                time_weighted_return = 0.0

            pnl = current_equity - total_invested

            weekly_breakdown.append(
                {
                    'week': i + 1,
                    'date': date,
                    'price': price,
                    'investment': weekly_amount,
                    'contracts_bought': contracts_to_buy,
                    'total_contracts': total_contracts,
                    'total_invested': total_invested,
                    'current_value': current_equity,
                    'position_value': position_value,
                    'cash_balance': cash_balance,
                    'required_margin': required_margin,
                    'pnl': pnl,
                    'return_pct': (pnl / total_invested * 100) if total_invested > 0 else 0.0,
                    'time_weighted_return': time_weighted_return,
                }
            )

            equity_curve.append(
                {
                    'date': date,
                    'equity': current_equity,
                    'position_value': position_value,
                    'cash_balance': cash_balance,
                    'invested': total_invested,
                    'pnl': pnl,
                    'time_weighted_return': time_weighted_return,
                    'prev_equity': prev_equity,
                }
            )

            prev_equity = current_equity

        return {
            'total_invested': total_invested,
            'current_value': current_equity,
            'total_contracts': total_contracts,
            'cash_balance': cash_balance,
            'weekly_breakdown': weekly_breakdown,
            'equity_curve': equity_curve,
        }

    def _calculate_performance_metrics(self, dca_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics using time-weighted weekly returns."""
        equity_curve = dca_results['equity_curve']
        total_invested = float(dca_results['total_invested'])
        current_value = float(dca_results['current_value'])

        if not equity_curve:
            return {}

        total_return = ((current_value / total_invested) - 1) * 100 if total_invested > 0 else 0.0

        # Weekly time-weighted returns, skip week 1
        wr = [p.get('time_weighted_return', None) for p in equity_curve[1:]]
        wr = np.array([x for x in wr if x is not None], dtype=float)
        wr = wr[~np.isnan(wr)]

        ann = np.sqrt(52)
        if wr.size > 1 and np.std(wr) > 0:
            volatility = float(np.std(wr) * ann * 100)
            sharpe = float((np.mean(wr) / np.std(wr)) * ann)
            twr = float(np.prod(1.0 + wr))
            years = wr.size / 52.0
            cagr = (twr ** (1.0 / years) - 1.0) * 100 if years > 0 else 0.0
        else:
            volatility = 0.0
            sharpe = 0.0
            cagr = 0.0

        # Max drawdown on equity path
        peak = equity_curve[0]['equity']
        max_drawdown = 0.0
        for point in equity_curve:
            eq = point['equity']
            if eq > peak:
                peak = eq
            if peak > 0:
                dd = (peak - eq) / peak
                if dd > max_drawdown:
                    max_drawdown = dd

        # Profit factor & win rate using weekly returns
        gains = losses = 0.0
        prev_eq = equity_curve[0]['equity']
        positive_weeks = total_weeks = 0
        for p in equity_curve[1:]:
            r = p.get('time_weighted_return')
            if r is None or math.isnan(r):
                continue
            pnl_t = r * prev_eq
            if pnl_t > 0:
                gains += pnl_t
                positive_weeks += 1
            else:
                losses += -pnl_t
            total_weeks += 1
            prev_eq = p['equity']

        profit_factor = round(gains / losses, 2) if losses > 0 else 0.0
        win_rate = round((positive_weeks / total_weeks) * 100, 2) if total_weeks > 0 else 0.0

        return {
            'total_return': round(total_return, 2),
            'cagr': round(cagr, 2),
            'volatility': round(volatility, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_drawdown * 100, 2),
            'profit_factor': profit_factor,
            'win_rate': win_rate,
        }
