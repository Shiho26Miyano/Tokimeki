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
        # Position sizing controls
        self.min_equity_to_notional = 0.10   # require ≥10% equity vs notional before adding
        self.max_add_per_week = 1            # cap new contracts per week

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
            # Use precomputed weekly data if available, otherwise group by week
            if 'weekly_data' in data:
                weekly_data = data['weekly_data']
            else:
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
        cash_balance = 0.0
        equity = 0.0
        total_contracts = 0
        total_invested = 0.0
        weekly_breakdown: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []
        prev_price: Optional[float] = None

        for i, week_data in enumerate(weekly_data):
            price = float(week_data['Close'])
            date = week_data['Date']

            # 1) Mark-to-market on existing position
            if prev_price is not None and total_contracts != 0:
                dPnL = (price - prev_price) * self.contract_multiplier * total_contracts
                cash_balance += dPnL
                equity += dPnL

            equity_before_contrib = equity

            # 2) Weekly contribution
            cash_balance += weekly_amount
            total_invested += weekly_amount
            equity += weekly_amount

            # 3) Controlled position adds
            def can_add_one(curr_contracts: int, eq: float) -> bool:
                next_contracts = curr_contracts + 1
                fees = (self.commission_per_contract + self.slippage_per_contract)
                eq_after_fees = eq - fees
                # initial margin check
                if eq_after_fees < next_contracts * self.margin_per_contract:
                    return False
                # equity/notional buffer
                notional_after = next_contracts * price * self.contract_multiplier
                return eq_after_fees >= notional_after * self.min_equity_to_notional

            adds = 0
            while (
                adds < self.max_add_per_week and
                total_contracts < self.max_contracts and
                can_add_one(total_contracts, equity)
            ):
                fees = (self.commission_per_contract + self.slippage_per_contract)
                cash_balance -= fees
                equity -= fees
                total_contracts += 1
                adds += 1

            # 4) Maintenance margin & forced liquidation
            required_maint = total_contracts * self.maintenance_margin_per_contract
            if total_contracts > 0 and equity < required_maint:
                close_fee = (self.commission_per_contract + self.slippage_per_contract)
                while total_contracts > 0 and equity < (total_contracts * self.maintenance_margin_per_contract):
                    cash_balance -= close_fee
                    equity -= close_fee
                    total_contracts -= 1
                required_maint = total_contracts * self.maintenance_margin_per_contract

            # 5) If fully flat and fees made equity negative, wipe to zero
            if total_contracts == 0 and equity < 0:
                equity = 0.0
                cash_balance = 0.0
                equity_before_contrib = 0.0

            current_equity = equity
            pnl = current_equity - total_invested
            exposure_notional = total_contracts * price * self.contract_multiplier

            # time-weighted return (exclude this week's contribution)
            twr = ((current_equity - equity_before_contrib - weekly_amount) / equity_before_contrib) if equity_before_contrib > 0 else 0.0

            weekly_breakdown.append({
                'week': i + 1,
                'date': date,
                'price': price,
                'investment': weekly_amount,
                'contracts_bought': adds,
                'total_contracts': total_contracts,
                'total_invested': total_invested,
                'current_value': current_equity,            # <-- equity
                'position_value': exposure_notional,        # <-- DISPLAY ONLY
                'cash_balance': cash_balance,
                'required_margin': required_maint,
                'pnl': pnl,
                'return_pct': (pnl / total_invested * 100) if total_invested > 0 else 0.0,
                'time_weighted_return': twr,
            })

            equity_curve.append({
                'date': date,
                'equity': current_equity,
                'cash_balance': cash_balance,
                'invested': total_invested,
                'pnl': pnl,
                'time_weighted_return': twr,
            })

            prev_price = price

        return {
            'total_invested': total_invested,
            'current_value': equity,       # equity, not notional
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
            'win_rate': round(win_rate, 2),
        }

    async def _prepare_weekly_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Precompute weekly data once for reuse across multiple calculations"""
        data = await self.get_mnq_futures_data(start_date, end_date)
        if not data or not data.get('data'):
            raise Exception("No MNQ futures data available")
        weekly_data = self._group_by_week(data['data'])
        return {
            "symbol": data["symbol"], 
            "weekly_data": weekly_data,
            "start_date": start_date, 
            "end_date": end_date
        }

    async def find_optimal_investment_amounts(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: float = 100.0,
        max_amount: float = 10000.0,
        step_size: float = 100.0,
        top_n: int = 5,
        sort_key: str = "total_return",
        descending: bool = True
    ) -> Dict[str, Any]:
        """
        Grid-search weekly amounts and rank strictly by *calculated* performance.
        Uses precomputed weekly data (1 fetch), respects position sizing rules,
        and returns a clean top-N along with full results.
        """

        try:
            # ---- Dates (defaults) ----
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            # ---- Precompute once (weekly prices) ----
            prepared = await self._prepare_weekly_data(start_date, end_date)  # {"weekly_data": ...}

            # ---- Build amount grid (use step_size; guard count) ----
            if step_size <= 0:
                step_size = 1.0
            if max_amount < min_amount:
                min_amount, max_amount = max_amount, min_amount

            # cap at ~500 evaluations to keep API snappy
            est_points = int((max_amount - min_amount) // step_size) + 1
            if est_points > 500:
                # stretch step to keep ~<=500
                step_size = max(step_size, (max_amount - min_amount) / 500.0)
                est_points = int((max_amount - min_amount) // step_size) + 1

            # numeric stability/rounding
            grid = [round(min_amount + i * step_size, 2) for i in range(est_points)]
            if grid[-1] < max_amount:
                grid.append(round(max_amount, 2))
            
            # Debug logging to see what grid is generated
            logger.info(f"Generated grid: min=${min_amount}, max=${max_amount}, step=${step_size}, points={est_points}")
            logger.info(f"Grid includes $120: {'$120' in [f'${amt}' for amt in grid]}")
            logger.info(f"First 10 grid values: {grid[:10]}")
            logger.info(f"Grid around $120: {[amt for amt in grid if 115 <= amt <= 125]}")

            valid_sort_keys = {"total_return", "sharpe_ratio", "profit_factor", "return_per_invested_dollar"}

            if sort_key not in valid_sort_keys:
                logger.warning(f"Invalid sort_key '{sort_key}', defaulting to 'total_return'")
                sort_key = "total_return"

            results: List[Dict[str, Any]] = []

            # ---- Evaluate sequentially (fast enough; uses precomputed data) ----
            for amt in grid:
                try:
                    perf = await self._calculate_dca_performance(
                        data=prepared, weekly_amount=amt,
                        start_date=start_date, end_date=end_date
                    )
                    metrics = perf["performance_metrics"]

                    # NOTE: current_value is *equity* (cash + MTM). This already prices the open position.
                    total_invested = float(perf["total_invested"])
                    current_value  = float(perf["current_value"])

                    total_return_pct = ((current_value / total_invested) - 1.0) * 100.0 if total_invested > 0 else 0.0
                    ret_per_dollar = ((current_value - total_invested) / total_invested) if total_invested > 0 else 0.0

                    results.append({
                        "weekly_amount": amt,
                        "total_invested": total_invested,
                        "current_value": current_value,
                        "total_return": round(total_return_pct, 2),
                        "cagr": metrics.get("cagr", 0.0),
                        "volatility": metrics.get("volatility", 0.0),
                        "sharpe_ratio": metrics.get("sharpe_ratio", 0.0),
                        "max_drawdown": metrics.get("max_drawdown", 0.0),
                        "win_rate": metrics.get("win_rate", 0.0),
                        "profit_factor": metrics.get("profit_factor", 0.0),
                        "total_contracts": perf.get("total_contracts", 0.0),
                        "return_per_invested_dollar": round(ret_per_dollar, 6),
                    })

                except Exception as e:
                    logger.warning(f"Amount ${amt}: calculation failed ({e})")
                    continue

            if not results:
                raise Exception("No valid results generated")

            # ---- Sort by percentage/return (existing behavior) ----
            results_by_percentage = sorted(results, key=lambda x: x.get(sort_key, 0.0), reverse=descending)
            top_by_percentage = results_by_percentage[:max(1, min(top_n, len(results)))]

            # ---- Sort by largest amount of money invested ----
            results_by_amount = sorted(results, key=lambda x: x.get("total_invested", 0.0), reverse=True)
            top_by_amount = results_by_amount[:5]  # Top 5 by money invested

            # ---- Summary ----
            summary = {
                "total_tested": len(results),
                "sort_key": sort_key,
                "sort_direction": "descending" if descending else "ascending",
                "best_return": top_by_percentage[0]["total_return"] if top_by_percentage else 0.0,
                "worst_return": results_by_percentage[-1]["total_return"] if results_by_percentage else 0.0,
                "avg_return": round(sum(r["total_return"] for r in results) / len(results), 3),
                "recommendation": f"Top {len(top_by_percentage)} by {sort_key} and Top 5 by amount invested.",
            }

            logger.info(
                f"Optimal search complete: tested={len(results)} "
                f"best=${top_by_percentage[0]['weekly_amount'] if top_by_percentage else 'N/A'} "
                f"({top_by_percentage[0]['total_return']:.2f}% by {sort_key})"
            )

            return {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "summary": summary,
                "top_by_percentage": top_by_percentage,  # Left side: sorted by percentage/return
                "top_by_amount": top_by_amount,          # Right side: top 5 by money invested
                "all_results": results,
            }

        except Exception as e:
            logger.error(f"Error finding optimal investment amounts: {e}")
            raise


