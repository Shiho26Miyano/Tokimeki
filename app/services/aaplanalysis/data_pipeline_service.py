"""
AAPL Data Pipeline Service - Pre-calculates and caches performance data
"""
import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict

from .polygon_service import PolygonService
from .backtest_service import BacktestEngine
from ...models.aapl_analysis_models import PolygonConfig, StockDCARequest, WeeklyOptionRequest

logger = logging.getLogger(__name__)


@dataclass
class AAPLSnapshot:
    """Snapshot of AAPL analysis data"""
    timestamp: str
    period_start: str
    period_end: str
    stock_performance: Dict[str, Any]
    option_performance: Dict[str, Any]
    comparison_metrics: Dict[str, Any]
    market_data_summary: Dict[str, Any]


class AAPLDataPipeline:
    """Optimized data pipeline for AAPL analysis"""
    
    def __init__(self, polygon_config: PolygonConfig, cache_dir: str = "data/cache"):
        self.polygon_service = PolygonService(polygon_config)
        self.backtest_service = BacktestEngine(self.polygon_service)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for structured data
        self.db_path = self.cache_dir / "aapl_analysis.db"
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for caching"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS aapl_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data_cache (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, date, data_type)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_period 
                ON aapl_snapshots(period_start, period_end)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_date 
                ON market_data_cache(symbol, date)
            """)
    
    async def generate_3year_snapshot(self) -> AAPLSnapshot:
        """Generate comprehensive 1-year AAPL analysis snapshot"""
        logger.info("Generating 1-year AAPL analysis snapshot...")
        
        # Define 1-year period
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        try:
            # Run optimized backtests
            stock_params = StockDCARequest(
                ticker="AAPL",
                start_date=start_date,
                end_date=end_date,
                shares_per_week=100,
                buy_weekday=1,  # Tuesday
                fee_per_trade=0.0
            )
            
            option_params = WeeklyOptionRequest(
                ticker="AAPL",
                start_date=start_date,
                end_date=end_date,
                option_type="call",
                moneyness_offset=0.0,
                min_days_to_expiry=1,
                contracts_per_week=1,
                buy_weekday=1,
                fee_per_trade=0.0
            )
            
            # Run combined backtest
            logger.info("Running combined backtest...")
            from ...models.aapl_analysis_models import CombinedBacktestRequest
            combined_request = CombinedBacktestRequest(
                stock_params=stock_params,
                option_params=option_params
            )
            combined_result = await self.backtest_service.run_combined_backtest(combined_request)
            
            # Get market data summary
            market_summary = await self._get_market_summary(start_date, end_date)
            
            # Create snapshot
            snapshot = AAPLSnapshot(
                timestamp=datetime.now().isoformat(),
                period_start=start_date.isoformat(),
                period_end=end_date.isoformat(),
                stock_performance={
                    "total_return": combined_result.stock_result.unrealized_pnl,
                    "total_cost": combined_result.stock_result.total_cost,
                    "market_value": combined_result.stock_result.market_value,
                    "return_percentage": (combined_result.stock_result.unrealized_pnl / combined_result.stock_result.total_cost * 100) if combined_result.stock_result.total_cost > 0 else 0,
                    "total_entries": combined_result.stock_result.total_entries,
                    "total_shares": combined_result.stock_result.total_shares,
                    "avg_cost_basis": combined_result.stock_result.cost_basis
                },
                option_performance={
                    "total_pnl": combined_result.option_result.total_pnl,
                    "total_trades": combined_result.option_result.total_trades,
                    "win_rate": combined_result.option_result.win_rate,
                    "avg_win": combined_result.option_result.avg_win,
                    "avg_loss": combined_result.option_result.avg_loss,
                    "max_win": combined_result.option_result.max_win,
                    "max_loss": combined_result.option_result.max_loss,
                    "profit_factor": combined_result.option_result.avg_win / abs(combined_result.option_result.avg_loss) if combined_result.option_result.avg_loss != 0 else 0
                },
                comparison_metrics={
                    "stock_return_pct": combined_result.comparison_metrics.get("stock_return_pct", 0),
                    "combined_return": combined_result.comparison_metrics.get("combined_return", 0),
                    "option_vs_stock_ratio": combined_result.option_result.total_pnl / combined_result.stock_result.unrealized_pnl if combined_result.stock_result.unrealized_pnl != 0 else 0,
                    "better_strategy": "options" if combined_result.option_result.total_pnl > combined_result.stock_result.unrealized_pnl else "stock"
                },
                market_data_summary=market_summary
            )
            
            # Store snapshot
            await self._store_snapshot(snapshot)
            
            logger.info("3-year snapshot generated successfully")
            return snapshot
            
        except Exception as e:
            logger.error(f"Error generating snapshot: {e}")
            raise
    
    async def _get_market_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get market data summary for the period"""
        try:
            # Get AAPL price data for the period
            price_data = await self.polygon_service.get_stock_prices(
                "AAPL", start_date, end_date
            )
            
            if not price_data.results:
                return {"error": "No price data available"}
            
            prices = [float(bar.close) for bar in price_data.results]
            start_price = prices[0]
            end_price = prices[-1]
            max_price = max(prices)
            min_price = min(prices)
            
            return {
                "start_price": start_price,
                "end_price": end_price,
                "price_change": end_price - start_price,
                "price_change_pct": ((end_price - start_price) / start_price * 100) if start_price > 0 else 0,
                "max_price": max_price,
                "min_price": min_price,
                "volatility": self._calculate_volatility(prices),
                "total_trading_days": len(prices)
            }
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {"error": str(e)}
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate simple volatility measure"""
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return (variance ** 0.5) * (252 ** 0.5)  # Annualized volatility
    
    async def _store_snapshot(self, snapshot: AAPLSnapshot):
        """Store snapshot in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO aapl_snapshots (timestamp, period_start, period_end, data_json)
                VALUES (?, ?, ?, ?)
            """, (
                snapshot.timestamp,
                snapshot.period_start,
                snapshot.period_end,
                json.dumps(asdict(snapshot))
            ))
    
    async def get_latest_snapshot(self, max_age_hours: int = 24) -> Optional[AAPLSnapshot]:
        """Get latest snapshot if it's not too old"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT data_json FROM aapl_snapshots 
                WHERE created_at > ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (cutoff_time.isoformat(),))
            
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return AAPLSnapshot(**data)
        
        return None
    
    async def get_cached_data_or_generate(self) -> AAPLSnapshot:
        """Get cached data or generate new snapshot"""
        # Try to get recent snapshot first
        snapshot = await self.get_latest_snapshot(max_age_hours=6)
        
        if snapshot:
            logger.info("Using cached snapshot")
            return snapshot
        
        # Generate new snapshot
        logger.info("Generating new snapshot...")
        return await self.generate_3year_snapshot()
    
    async def refresh_cache_background(self):
        """Background task to refresh cache periodically"""
        while True:
            try:
                logger.info("Background cache refresh starting...")
                await self.generate_3year_snapshot()
                logger.info("Background cache refresh completed")
                
                # Wait 4 hours before next refresh
                await asyncio.sleep(4 * 3600)
                
            except Exception as e:
                logger.error(f"Background cache refresh failed: {e}")
                # Wait 30 minutes before retry
                await asyncio.sleep(30 * 60)
    
    async def cleanup_old_snapshots(self, keep_days: int = 7):
        """Clean up old snapshots to save space"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM aapl_snapshots 
                WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} old snapshots")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get quick performance summary for UI"""
        snapshot = await self.get_cached_data_or_generate()
        
        return {
            "last_updated": snapshot.timestamp,
            "period": f"{snapshot.period_start} to {snapshot.period_end}",
            "stock_performance": {
                "return_pct": snapshot.stock_performance["return_percentage"],
                "total_return": snapshot.stock_performance["total_return"],
                "market_value": snapshot.stock_performance["market_value"]
            },
            "option_performance": {
                "total_pnl": snapshot.option_performance["total_pnl"],
                "win_rate": snapshot.option_performance["win_rate"],
                "total_trades": snapshot.option_performance["total_trades"]
            },
            "comparison": {
                "better_strategy": snapshot.comparison_metrics["better_strategy"],
                "performance_ratio": snapshot.comparison_metrics["option_vs_stock_ratio"]
            },
            "market_summary": snapshot.market_data_summary
        }
