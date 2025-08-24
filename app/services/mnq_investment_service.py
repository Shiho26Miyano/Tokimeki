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
    def __init__(self, cache_service: AsyncCacheService, contract_type: str = "MNQ"):
        self.cache_service = cache_service
        self.contract_type = contract_type.upper()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Set symbol based on contract type
        if self.contract_type == "MNQ":
            self.mnq_symbol = "MNQ=F"  # Micro E-mini NASDAQ-100 futures
            self.contract_multiplier = 2  # $2 per point (Micro E-mini NASDAQ-100)
        elif self.contract_type == "MES":
            self.mnq_symbol = "MES=F"  # Micro E-mini S&P 500 futures
            self.contract_multiplier = 5  # $5 per point (Micro E-mini S&P 500)
        elif self.contract_type == "MYM":
            self.mnq_symbol = "MYM=F"  # Micro E-mini Dow Jones futures
            self.contract_multiplier = 5  # $5 per point (Micro E-mini Dow Jones)
        else:
            # Default to MNQ if unknown contract type
            self.mnq_symbol = "MNQ=F"
            self.contract_multiplier = 2
            logger.warning(f"Unknown contract type '{contract_type}', defaulting to MNQ")
        
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

    async def get_max_available_date_range(self) -> Dict[str, Any]:
        """Get the maximum available date range for MNQ futures data"""
        try:
            # Get data for a very wide range to determine availability
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')  # 5 years back
            
            data = await self.get_mnq_futures_data(start_date, end_date)
            if not data or not data.get('data'):
                raise Exception("No MNQ futures data available")
            
            # Get the actual date range from the data
            dates = [row['Date'] for row in data['data']]
            dates.sort()
            
            earliest_available = dates[0]
            latest_available = dates[-1]
            
            # Calculate range in weeks and days
            earliest_dt = datetime.strptime(earliest_available, '%Y-%m-%d')
            latest_dt = datetime.strptime(latest_available, '%Y-%m-%d')
            max_range_days = (latest_dt - earliest_dt).days
            max_range_weeks = max_range_days // 7
            
            return {
                "earliest_available": earliest_available,
                "latest_available": latest_available,
                "max_range_days": max_range_days,
                "max_range_weeks": max_range_weeks,
                "data_points": len(dates)
            }
            
        except Exception as e:
            logger.error(f"Error getting max available date range: {e}")
            # Return fallback range
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            return {
                "earliest_available": start_date,
                "latest_available": end_date,
                "max_range_days": 365,
                "max_range_weeks": 52,
                "data_points": 0
            }

    async def find_optimal_percentage_amounts(
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
        Find the top N weekly amounts that produce the best performance by percentage-based metrics.
        
        This function ranks amounts by percentage-based metrics (returns, Sharpe ratio, etc.)
        and is designed for performance analysis and comparison.
        """

        try:
            # ---- Dates (defaults) ----
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            # ---- Precompute once (weekly prices) ----
            prepared = await self._prepare_weekly_data(start_date, end_date)  # {"weekly_data": ...}
            if not prepared or 'weekly_data' not in prepared:
                raise Exception("Failed to prepare weekly data")

            # ---- Build amount grid (use step_size; guard count) ----
            if step_size <= 0:
                step_size = 1.0
            if max_amount < min_amount:
                min_amount, max_amount = max_amount, min_amount

            # cap at ~1000 evaluations to keep API snappy but allow more granular testing
            est_points = int((max_amount - min_amount) // step_size) + 1
            if est_points > 1000:
                # stretch step to keep ~<=1000
                step_size = max(step_size, (max_amount - min_amount) / 1000.0)
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

            # ---- Evaluate sequentially for now (will optimize later) ----
            logger.info(f"Starting sequential evaluation of {len(grid)} amounts...")
            
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
                    dollar_profit = current_value - total_invested  # Calculate absolute dollar profit

                    results.append({
                        "weekly_amount": amt,
                        "total_invested": total_invested,
                        "current_value": current_value,
                        "total_return": round(total_return_pct, 2),
                        "dollar_profit": round(dollar_profit, 2),  # Add dollar profit to results
                        "cagr": metrics.get("cagr", 0.0),
                        "volatility": metrics.get("volatility", 0.0),
                        "sharpe_ratio": metrics.get("sharpe_ratio", 0.0),
                        "max_drawdown": metrics.get("max_drawdown", 0.0),
                        "win_rate": metrics.get("win_rate", 0.0),
                        "profit_factor": metrics.get("profit_factor", 0.0),
                        "total_contracts": perf.get("total_contracts", 0.0),
                        "return_per_invested_dollar": round(ret_per_dollar, 6),
                    })
                    
                    logger.info(f"Amount ${amt}: return={total_return_pct:.2f}%, profit=${dollar_profit:.2f}")

                except Exception as e:
                    logger.warning(f"Amount ${amt}: calculation failed ({e})")
                    continue
            
            logger.info(f"Sequential evaluation completed. {len(results)} successful results out of {len(grid)} attempts.")

            if not results:
                raise Exception("No valid results generated")

            # ---- Sort by percentage/return (existing behavior) ----
            results_by_percentage = sorted(results, key=lambda x: x.get(sort_key, 0.0), reverse=descending)
            top_by_percentage = results_by_percentage[:max(1, min(top_n, len(results)))]

            # ---- Sort by dollar profit (best absolute returns) ----
            results_by_profit = sorted(results, key=lambda x: x.get("dollar_profit", -999999.0), reverse=True)
            top_by_profit = results_by_profit[:5]  # Top 5 by dollar profit

            # ---- Summary ----
            summary = {
                "total_tested": len(results),
                "sort_key": sort_key,
                "sort_direction": "descending" if descending else "ascending",
                "best_return": top_by_percentage[0]["total_return"] if top_by_percentage else 0.0,
                "worst_return": results_by_percentage[-1]["total_return"] if results_by_percentage else 0.0,
                "avg_return": round(sum(r["total_return"] for r in results) / len(results), 3),
                "recommendation": f"Top {len(top_by_percentage)} by {sort_key} and Top 5 by dollar profit.",
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
                "top_by_profit": top_by_profit,          # Right side: top 5 by dollar profit
                "all_results": results,
            }

        except Exception as e:
            logger.error(f"Error finding optimal investment amounts: {e}")
            raise

    async def find_optimal_dollar_profit_amounts(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: float = 100.0,
        max_amount: float = 10000.0,
        step: float = 100.0,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Find the top N weekly amounts that produce the largest absolute dollars of profit.
        
        Ranking rule:
        1. Primary: PROFIT(A) = EQ(A) - INV(A) descending (largest dollar profit first)
        2. Tie-breaker 1: Sharpe ratio descending (better risk-adjusted among equal profits)
        3. Tie-breaker 2: Lower volatility
        4. Tie-breaker 3: Smaller weekly amount (prefer cheaper plan if tied)
        
        This function is designed for profit maximization, not performance analysis.
        """
        try:
            logger.info(f"Finding optimal profit amounts: ${min_amount}-${max_amount}, step ${step}")
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            # Get MNQ futures data
            data = await self.get_mnq_futures_data(start_date, end_date)
            if not data or not data.get('data'):
                raise Exception("No MNQ futures data available")

            # Generate grid of amounts to test
            amounts = np.arange(min_amount, max_amount + step, step)
            logger.info(f"Generated grid: min=${min_amount}, max=${max_amount}, step=${step}, points={len(amounts)}")

            results = []
            
            # Test each amount
            for amt in amounts:
                try:
                    logger.info(f"Testing amount: ${amt}")
                    
                    # Run DCA simulation for this amount
                    dca_result = await self._calculate_dca_performance(data, amt, start_date, end_date)
                    
                    if not dca_result:
                        continue
                    
                    # Calculate dollar profit: PROFIT(A) = EQ(A) - INV(A)
                    total_invested = float(dca_result['total_invested'])
                    current_value = float(dca_result['current_value'])
                    dollar_profit = current_value - total_invested
                    
                    # Calculate Sharpe ratio from time-weighted returns
                    equity_curve = dca_result['equity_curve']
                    if len(equity_curve) < 2:
                        continue
                    
                    # Get weekly time-weighted returns, skip week 1
                    weekly_returns = [p.get('time_weighted_return', None) for p in equity_curve[1:]]
                    weekly_returns = [x for x in weekly_returns if x is not None and not math.isnan(x)]
                    
                    if len(weekly_returns) < 2:
                        continue
                    
                    # Calculate Sharpe ratio (annualized, rf=0)
                    mean_return = np.mean(weekly_returns)
                    std_return = np.std(weekly_returns)
                    
                    if std_return > 0:
                        sharpe_ratio = (mean_return / std_return) * np.sqrt(52)
                    else:
                        sharpe_ratio = 0.0
                    
                    # Calculate volatility
                    volatility = std_return * np.sqrt(52) * 100 if std_return > 0 else 0.0
                    
                    # Calculate max drawdown
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
                    
                    result = {
                        'weekly_amount': amt,
                        'dollar_profit': dollar_profit,
                        'total_invested': total_invested,
                        'current_value': current_value,
                        'sharpe_ratio': sharpe_ratio,
                        'volatility': volatility,
                        'max_drawdown': max_drawdown * 100,  # Convert to percentage
                        'total_weeks': len(equity_curve)
                    }
                    
                    results.append(result)
                    logger.info(f"Amount ${amt}: profit=${dollar_profit:.2f}, Sharpe={sharpe_ratio:.2f}")
                    
                except Exception as e:
                    logger.warning(f"Amount ${amt}: calculation failed ({e})")
                    continue

            if not results:
                raise Exception("No valid results generated")

            # Sort by dollar profit (descending), then by Sharpe ratio (descending), then by volatility (ascending), then by weekly amount (ascending)
            results_sorted = sorted(
                results, 
                key=lambda x: (
                    -x['dollar_profit'],      # Primary: dollar profit descending
                    -x['sharpe_ratio'],       # Tie-breaker 1: Sharpe ratio descending
                    x['volatility'],           # Tie-breaker 2: volatility ascending
                    x['weekly_amount']         # Tie-breaker 3: weekly amount ascending
                )
            )
            
            top_by_profit = results_sorted[:top_n]

            # Summary
            summary = {
                "total_tested": len(results),
                "objective": "maximize_dollar_profit",
                "best_profit": top_by_profit[0]['dollar_profit'] if top_by_profit else 0.0,
                "worst_profit": results_sorted[-1]['dollar_profit'] if results_sorted else 0.0,
                "avg_profit": round(sum(r['dollar_profit'] for r in results) / len(results), 2),
                "recommendation": f"Top {len(top_by_profit)} by absolute dollar profit with Sharpe ratio tie-breakers.",
            }

            logger.info(
                f"Optimal profit search complete: tested={len(results)} "
                f"best=${top_by_profit[0]['weekly_amount'] if top_by_profit else 'N/A'} "
                f"(profit=${top_by_profit[0]['dollar_profit']:.2f})"
            )

            return {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "summary": summary,
                "top_by_profit": top_by_profit,  # Right side: sorted by dollar profit
                "all_results": results,
            }

        except Exception as e:
            logger.error(f"Error finding optimal profit amounts: {e}")
            raise

    async def generate_diagnostic_event_analysis(
        self,
        weekly_amount: float = 1000.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate diagnostic event analysis identifying worst week and factor impacts"""
        try:
            logger.info(f"Starting diagnostic event analysis with weekly_amount: ${weekly_amount}")

            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            # Get MNQ futures data
            data = await self.get_mnq_futures_data(start_date, end_date)
            if not data or not data.get('data'):
                raise Exception("No MNQ futures data available")

            # Calculate DCA performance to get weekly breakdown
            logger.info(f"Calculating DCA performance with weekly_amount: ${weekly_amount}")
            dca_results = await self._calculate_dca_performance(data, weekly_amount, start_date, end_date)
            
            if not dca_results or 'weekly_breakdown' not in dca_results:
                raise Exception("No weekly breakdown data available")

            # Validate weekly breakdown structure
            weekly_breakdown = dca_results['weekly_breakdown']
            if not weekly_breakdown:
                raise Exception("Weekly breakdown is empty")
            
            # Check if all required fields are present in the first week
            required_fields = ['date', 'return_pct', 'price', 'contracts_bought']
            if weekly_breakdown and len(weekly_breakdown) > 0:
                first_week = weekly_breakdown[0]
                missing_fields = [field for field in required_fields if field not in first_week]
                if missing_fields:
                    logger.warning(f"Missing fields in weekly breakdown: {missing_fields}")
                    logger.warning(f"Available fields: {list(first_week.keys())}")
            
            logger.info(f"Analyzing {len(weekly_breakdown)} weeks for worst performance")
            
            if not weekly_breakdown:
                raise Exception("Weekly breakdown is empty")
            
            worst_week = None
            worst_return = float('inf')
            
            for week_data in weekly_breakdown:
                if week_data.get('return_pct') is not None:
                    twr = week_data['return_pct']
                    if twr < worst_return:
                        worst_return = twr
                        worst_week = week_data

            if not worst_week:
                # If no worst week found, use the first week as fallback
                logger.warning("Could not identify worst week, using first week as fallback")
                worst_week = weekly_breakdown[0] if weekly_breakdown else {
                    'date': 'Unknown Date',
                    'return_pct': 0.0,
                    'price': 0.0,
                    'contracts_bought': 0
                }

            # Log the worst week details for debugging
            logger.info(f"Worst week identified: {worst_week.get('date')} with return_pct: {worst_week.get('return_pct'):.2f}%")

            # Create factor impact analysis
            factor_analysis = await self._create_factor_impact_table(worst_week, data)

            # Create the diagnostic report in HTML format - concentrated and focused
            diagnostic_report = f"""<div class="diagnostic-analysis">
                <div class="diagnostic-header text-center mb-3">
                    <h4 class="text-primary mb-2">🔍 Diagnostic Event Analysis</h4>
                    <div class="alert alert-danger py-2">
                        <strong>Worst Week: {worst_week.get('date', 'Unknown Date')} ({worst_week.get('return_pct', 0.0):.2f}% loss)</strong>
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
                                    <th>Impact on {worst_week.get('date', 'Unknown Date')}</th>
                                </tr>
                            </thead>
                            <tbody>"""

            for factor in factor_analysis['factor_table']:
                factor_type = self._get_factor_type(factor.get('factor', 'Unknown Factor'))
                diagnostic_report += f"""
                                <tr>
                                    <td>{factor.get('factor', 'Unknown Factor')}</td>
                                    <td>{factor_type}</td>
                                    <td>{factor.get('impact', 'Impact not specified')}</td>
                                </tr>"""
            diagnostic_report += """
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="equity-curve-section mb-3">
                    <h5 class="text-dark mb-2">Equity Curve</h5>
                    <div class="chart-container">
                        <canvas id="equityCurveChart"></canvas>
                    </div>
                </div>
                
                <div class="weekly-breakdown-section mb-3">
                    <h5 class="text-dark mb-2">Weekly Breakdown</h5>
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead class="table-dark">
                                <tr>
                                    <th>Week</th>
                                    <th>Date</th>
                                    <th>Price</th>
                                    <th>Investment</th>
                                    <th>Contracts Bought</th>
                                    <th>Total Contracts</th>
                                    <th>Total Invested</th>
                                    <th>Current Value</th>
                                    <th>Position Value</th>
                                    <th>Cash Balance</th>
                                    <th>Required Margin</th>
                                    <th>PnL</th>
                                    <th>Return %</th>
                                    <th>Time-Weighted Return</th>
                                </tr>
                            </thead>
                            <tbody>"""

            for week_data in dca_results['weekly_breakdown']:
                diagnostic_report += f"""
                                <tr>
                                    <td>{week_data.get('week', 'N/A')}</td>
                                    <td>{week_data.get('date', 'N/A')}</td>
                                    <td>${week_data.get('price', 0):.2f}</td>
                                    <td>${week_data.get('investment', 0):.2f}</td>
                                    <td>{week_data.get('contracts_bought', 0)}</td>
                                    <td>{week_data.get('total_contracts', 0)}</td>
                                    <td>${week_data.get('total_invested', 0):.2f}</td>
                                    <td>${week_data.get('current_value', 0):.2f}</td>
                                    <td>${week_data.get('position_value', 0):.2f}</td>
                                    <td>${week_data.get('cash_balance', 0):.2f}</td>
                                    <td>${week_data.get('required_margin', 0):.2f}</td>
                                    <td>${week_data.get('pnl', 0):.2f}</td>
                                    <td>{week_data.get('return_pct', 0):.2f}%</td>
                                    <td>{week_data.get('time_weighted_return', 0):.4f}</td>
                                </tr>"""
            diagnostic_report += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>"""

            logger.info("Diagnostic event analysis completed successfully")
            
            # Final validation - ensure the report is complete
            if not diagnostic_report or len(diagnostic_report) < 100:
                logger.warning("Diagnostic report seems incomplete, creating fallback")
                diagnostic_report = f"""<div class="diagnostic-analysis">
                    <div class="diagnostic-header text-center mb-3">
                        <h4 class="text-primary mb-2">🔍 Diagnostic Event Analysis</h4>
                        <div class="alert alert-warning py-2">
                            <strong>Analysis completed for {worst_week.get('date', 'Unknown Date')}</strong>
                        </div>
                    </div>
                    <div class="alert alert-info">
                        <p>Diagnostic analysis completed successfully. Please check the logs for detailed information.</p>
                    </div>
                </div>"""
            
            return {
                'worst_week': worst_week,
                'factor_analysis': factor_analysis,
                'diagnostic_report': diagnostic_report
            }

        except Exception as e:
            logger.error(f"Diagnostic event analysis error: {e}")
            raise

    async def _create_factor_impact_table(self, worst_week: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create factor impact table using AI analysis"""
        
        # Extract worst week details
        worst_date = worst_week.get('date', 'Unknown Date')
        worst_return = worst_week.get('return_pct', 0.0)
        worst_return_pct = worst_return  # return_pct is already a percentage
        
        # Get market context data
        price_change = worst_week.get('price', 0)
        volume_change = worst_week.get('contracts_bought', 0)
        
        # Initialize factor_table with default values
        factor_table = [
            {"factor": "Market Volatility", "impact": "Increased market uncertainty and price swings", "factor_type": "Market Event"},
            {"factor": "Economic Data Release", "impact": "Unfavorable economic indicators affecting market sentiment", "factor_type": "Policy"},
            {"factor": "Sector Rotation", "impact": "Shift in investor preferences away from tech stocks", "factor_type": "Sector"},
            {"factor": "Global Market Conditions", "impact": "International market pressures affecting US futures", "factor_type": "Global Market"},
            {"factor": "Technical Breakdown", "impact": "Price breaking below key support levels", "factor_type": "Technical"}
        ]
        
        # Create AI prompt for factor analysis
        ai_prompt = f"""You are a financial market analyst. Analyze the worst week in MNQ futures trading and identify the key factors that caused the {worst_return_pct:.2f}% loss on {worst_date}.

Context:
- Date: {worst_date}
- Weekly return: {worst_return_pct:.2f}%
- Price change: ${price_change:.2f}
- Volume change: {volume_change} contracts

Generate exactly 5 specific market factors that likely contributed to this loss. For each factor:
1. Provide a specific, realistic factor name (e.g., "Fed Rate Decision", "Earnings Miss", "Geopolitical Tension")
2. Describe the concrete impact on the market
3. Categorize the factor type (Policy, Market Index, Futures Market, Global Market, Volatility, Trade Relations, or Market Event)

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{{
    "factor_table": [
        {{"factor": "Factor Name", "impact": "Specific impact description", "factor_type": "Factor Type"}},
        {{"factor": "Factor Name", "impact": "Specific impact description", "factor_type": "Factor Type"}},
        {{"factor": "Factor Name", "impact": "Specific impact description", "factor_type": "Factor Type"}},
        {{"factor": "Factor Name", "impact": "Specific impact description", "factor_type": "Factor Type"}},
        {{"factor": "Factor Name", "impact": "Specific impact description", "factor_type": "Factor Type"}}
    ]
}}

Focus on realistic market events that could cause such losses. Be specific and avoid generic statements. Do not include any text before or after the JSON."""
        
        try:
            # Import AI service here to avoid circular imports
            from app.services.ai_service import AsyncAIService
            import httpx
            
            logger.info("Creating AI service for factor analysis...")
            
            # Create HTTP client for AI service
            async with httpx.AsyncClient() as http_client:
                ai_service = AsyncAIService(http_client, self.cache_service)
                
                logger.info("Calling AI service for factor analysis...")
                
                # Get AI analysis with stricter parameters
                ai_result = await ai_service.chat(
                    message=ai_prompt,
                    model="mistral-small",
                    temperature=0.1,  # Lower temperature for more consistent output
                    max_tokens=500    # Limit tokens to prevent long responses
                )
                
                logger.info(f"AI service response received: {type(ai_result)}")
                logger.info(f"AI service response keys: {list(ai_result.keys()) if isinstance(ai_result, dict) else 'Not a dict'}")
            
            # Parse AI response
            response_text = ai_result.get("response", "")
            logger.info(f"AI response text length: {len(response_text)}")
            logger.info(f"AI response received: {response_text[:200]}...")
            
            # Check if response looks like JSON
            if not response_text.strip().startswith('{'):
                logger.warning("AI response doesn't start with '{', likely not JSON format")
                logger.warning(f"Response starts with: {response_text[:50]}...")
            
            # Try to extract JSON from response
            import json
            import re
            
            # Clean the response text - remove any markdown formatting
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            logger.info(f"Cleaned text starts with: {cleaned_text[:50]}...")
            
            # Try to parse the cleaned text directly first
            try:
                parsed_data = json.loads(cleaned_text)
                logger.info("Successfully parsed cleaned text as JSON")
                if 'factor_table' in parsed_data:
                    ai_factor_table = parsed_data['factor_table']
                    # Validate that we have exactly 5 factors with correct structure
                    if (len(ai_factor_table) == 5 and 
                        all(isinstance(f, dict) and 'factor' in f and 'impact' in f and 'factor_type' in f 
                            for f in ai_factor_table)):
                        factor_table = ai_factor_table  # Use AI-generated factors if valid
                        logger.info("Successfully parsed AI-generated factor table")
                    else:
                        logger.warning("AI response has invalid factor structure, using default")
                        logger.warning(f"Factor table structure: {[list(f.keys()) for f in ai_factor_table]}")
                else:
                    logger.warning("No factor_table in AI response, using default")
                    logger.warning(f"Available keys: {list(parsed_data.keys())}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse cleaned text as JSON: {e}")
                # Fallback: try to extract JSON using regex
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        logger.info("Successfully parsed JSON via regex")
                        if 'factor_table' in parsed_data:
                            ai_factor_table = parsed_data['factor_table']
                            if (len(ai_factor_table) == 5 and 
                                all(isinstance(f, dict) and 'factor' in f and 'impact' in f and 'factor_type' in f 
                                    for f in ai_factor_table)):
                                factor_table = ai_factor_table  # Use AI-generated factors if valid
                                logger.info("Successfully parsed AI-generated factor table via regex")
                            else:
                                logger.warning("AI response has invalid factor structure, using default")
                        else:
                            logger.warning("No factor_table in AI response, using default")
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Invalid JSON in AI response via regex: {e2}")
                else:
                    logger.warning("No JSON found in AI response")
            
        except Exception as e:
            logger.error(f"AI factor analysis failed: {e}, using default factors")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {str(e)}")
            # factor_table already has default values, so we can continue

        return {
            'worst_date': worst_date,
            'worst_return_pct': worst_return_pct,
            'factor_table': factor_table
        }

    def _get_factor_type(self, factor_name: str) -> str:
        """
        Helper to categorize factors into broad categories.
        This is a placeholder and can be expanded based on more specific rules.
        """
        if not factor_name:
            return "Other"
            
        factor_name = str(factor_name).lower()
        
        if "fed rate" in factor_name or "interest rate" in factor_name or "policy" in factor_name:
            return "Policy"
        elif "earnings" in factor_name or "revenue" in factor_name or "profit" in factor_name:
            return "Earnings"
        elif "geopolitical" in factor_name or "conflict" in factor_name or "tension" in factor_name:
            return "Geopolitical"
        elif "technical" in factor_name or "support" in factor_name or "resistance" in factor_name:
            return "Technical"
        elif "sector" in factor_name or "rotation" in factor_name:
            return "Sector"
        elif "volatility" in factor_name or "risk" in factor_name:
            return "Risk"
        elif "market" in factor_name or "index" in factor_name:
            return "Market Event"
        else:
            return "Other"


