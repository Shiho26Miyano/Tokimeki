"""
Pydantic models for AAPL stock vs options analysis dashboard
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Base models for market data
class OHLCData(BaseModel):
    """OHLC price data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockPriceResponse(BaseModel):
    """Response for stock price data"""
    ticker: str
    data: List[OHLCData]
    count: int
    from_date: date
    to_date: date
    source: str = "polygon"


# Option models
class OptionContract(BaseModel):
    """Option contract details"""
    ticker: str
    underlying_ticker: str
    option_type: OptionType
    strike_price: float
    expiration_date: date
    days_to_expiry: int
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None


class OptionChainResponse(BaseModel):
    """Response for option chain data"""
    underlying_ticker: str
    expiration_date: date
    underlying_price: float
    calls: List[OptionContract]
    puts: List[OptionContract]
    count: int


class OptionOHLCResponse(BaseModel):
    """Response for option OHLC data"""
    option_ticker: str
    underlying_ticker: str
    data: List[OHLCData]
    count: int
    contract_details: OptionContract


# Backtest request models
class StockDCARequest(BaseModel):
    """Request for stock DCA backtest"""
    ticker: str = "AAPL"
    start_date: date
    end_date: date
    shares_per_week: int = Field(default=100, ge=1, le=10000)
    buy_weekday: int = Field(default=1, ge=0, le=6)  # 0=Monday, 6=Sunday
    fee_per_trade: float = Field(default=0.0, ge=0.0)


class WeeklyOptionRequest(BaseModel):
    """Request for weekly option strategy backtest"""
    ticker: str = "AAPL"
    start_date: date
    end_date: date
    option_type: OptionType
    moneyness_offset: float = Field(default=0.0, ge=-0.5, le=0.5)  # 0 = ATM, 0.1 = 10% OTM
    min_days_to_expiry: int = Field(default=1, ge=1, le=30)
    contracts_per_week: int = Field(default=1, ge=1, le=100)
    buy_weekday: int = Field(default=1, ge=0, le=6)
    fee_per_trade: float = Field(default=0.0, ge=0.0)


class CombinedBacktestRequest(BaseModel):
    """Request for combined stock DCA + weekly option backtest"""
    stock_params: StockDCARequest
    option_params: WeeklyOptionRequest


# Backtest result models
class StockEntry(BaseModel):
    """Individual stock purchase entry"""
    date: date
    shares: int
    price: float
    cost: float
    fees: float
    cumulative_shares: int
    cumulative_cost: float


class OptionTrade(BaseModel):
    """Individual option trade"""
    entry_date: date
    exit_date: date
    option_ticker: str
    option_type: OptionType
    strike_price: float
    expiration_date: date
    entry_price: float
    exit_price: float
    contracts: int
    pnl: float
    fees: float
    status: Literal["closed", "expired_worthless", "expired_itm", "missing_exit_data"]
    days_held: int


class StockDCAResult(BaseModel):
    """Results for stock DCA strategy"""
    strategy: str = "stock_dca"
    ticker: str
    start_date: date
    end_date: date
    total_entries: int
    total_shares: int
    total_cost: float
    total_fees: float
    final_price: float
    market_value: float
    unrealized_pnl: float
    cost_basis: float
    entries: List[StockEntry]


class WeeklyOptionResult(BaseModel):
    """Results for weekly option strategy"""
    strategy: str = "weekly_options"
    ticker: str
    start_date: date
    end_date: date
    option_type: OptionType
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    total_fees: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float
    trades: List[OptionTrade]


class CombinedBacktestResult(BaseModel):
    """Combined results for both strategies"""
    stock_result: StockDCAResult
    option_result: WeeklyOptionResult
    comparison_metrics: Dict[str, Any]


# Diagnostics models
class DataDiagnostics(BaseModel):
    """Diagnostics for data quality and API performance"""
    polygon_api_calls: int
    polygon_avg_latency_ms: float
    cache_hits: int
    cache_misses: int
    missing_stock_data_days: int
    missing_option_contracts: int
    missing_option_exit_data: int
    partial_data_warnings: List[str]
    api_errors: List[str]


class BacktestDiagnostics(BaseModel):
    """Diagnostics specific to backtest execution"""
    total_expected_entries: int
    actual_entries: int
    missing_entry_dates: List[date]
    no_option_contracts_dates: List[date]
    fallback_intrinsic_exits: int
    data_quality_score: float  # 0-1 score


# API Response wrappers
class ApiResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class BacktestResponse(ApiResponse):
    """Response wrapper for backtest results"""
    data: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = None


# Configuration models
class PolygonConfig(BaseModel):
    """Configuration for Polygon API"""
    api_key: str
    base_url: str = "https://api.polygon.io"
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0


class CacheConfig(BaseModel):
    """Configuration for caching"""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1 hour default
    max_size: int = 1000
    redis_url: Optional[str] = None


class AppConfig(BaseModel):
    """Main application configuration"""
    polygon: PolygonConfig
    cache: CacheConfig
    log_level: str = "INFO"
    enable_diagnostics: bool = True
