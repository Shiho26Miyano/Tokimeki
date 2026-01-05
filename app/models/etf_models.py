"""
Pydantic models for ETF Dashboard
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date as DateType
from pydantic import BaseModel, Field


class ETFBasicInfo(BaseModel):
    """ETF basic information"""
    symbol: str = Field(..., description="ETF ticker symbol")
    name: str = Field(..., description="ETF name")
    description: Optional[str] = Field(None, description="ETF description")
    
    # Key metrics
    current_price: Optional[float] = Field(None, description="Current price")
    previous_close: Optional[float] = Field(None, description="Previous close price")
    day_change: Optional[float] = Field(None, description="Day change amount")
    day_change_percent: Optional[float] = Field(None, description="Day change percentage")
    
    # Fund details
    aum: Optional[float] = Field(None, description="Assets Under Management")
    expense_ratio: Optional[float] = Field(None, description="Expense ratio (as decimal)")
    inception_date: Optional[DateType] = Field(None, description="Inception date")
    issuer: Optional[str] = Field(None, description="Fund issuer/company")
    benchmark_index: Optional[str] = Field(None, description="Benchmark index tracked")
    
    # Trading info
    volume: Optional[int] = Field(None, description="Trading volume")
    avg_volume: Optional[int] = Field(None, description="Average volume")
    bid: Optional[float] = Field(None, description="Bid price")
    ask: Optional[float] = Field(None, description="Ask price")
    bid_ask_spread: Optional[float] = Field(None, description="Bid-ask spread")
    
    # 52-week range
    week_52_high: Optional[float] = Field(None, description="52-week high")
    week_52_low: Optional[float] = Field(None, description="52-week low")
    
    # Dividend info
    dividend_yield: Optional[float] = Field(None, description="Dividend yield")
    ex_dividend_date: Optional[DateType] = Field(None, description="Ex-dividend date")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")


class ETFPriceData(BaseModel):
    """Historical price data point"""
    date: DateType = Field(..., description="Date")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: int = Field(..., description="Volume")
    adjusted_close: Optional[float] = Field(None, description="Adjusted close price")


class ETFHolding(BaseModel):
    """ETF holding information"""
    symbol: str = Field(..., description="Holding ticker symbol")
    name: Optional[str] = Field(None, description="Holding company name")
    weight: Optional[float] = Field(None, description="Weight in ETF (as percentage)")
    shares: Optional[int] = Field(None, description="Number of shares held")
    value: Optional[float] = Field(None, description="Market value")
    price: Optional[float] = Field(None, description="Current price")
    day_change: Optional[float] = Field(None, description="Day change")
    day_change_percent: Optional[float] = Field(None, description="Day change percentage")
    sector: Optional[str] = Field(None, description="Sector")
    industry: Optional[str] = Field(None, description="Industry")


class ETFRiskMetrics(BaseModel):
    """Risk metrics for ETF"""
    symbol: str = Field(..., description="ETF symbol")
    analysis_date: DateType = Field(..., description="Analysis date")
    
    # Volatility
    volatility_30d: Optional[float] = Field(None, description="30-day volatility (annualized)")
    volatility_60d: Optional[float] = Field(None, description="60-day volatility (annualized)")
    volatility_1y: Optional[float] = Field(None, description="1-year volatility (annualized)")
    
    # Beta
    beta: Optional[float] = Field(None, description="Beta vs benchmark (typically S&P 500)")
    beta_3y: Optional[float] = Field(None, description="3-year beta")
    
    # Risk-adjusted returns
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sharpe_ratio_3y: Optional[float] = Field(None, description="3-year Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    
    # Drawdown
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown (as percentage)")
    max_drawdown_duration: Optional[int] = Field(None, description="Maximum drawdown duration (days)")
    current_drawdown: Optional[float] = Field(None, description="Current drawdown (as percentage)")
    
    # Value at Risk
    var_95: Optional[float] = Field(None, description="95% Value at Risk")
    var_99: Optional[float] = Field(None, description="99% Value at Risk")
    
    # Tracking error
    tracking_error: Optional[float] = Field(None, description="Tracking error vs benchmark")
    information_ratio: Optional[float] = Field(None, description="Information ratio")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")


class ETFTechnicalIndicators(BaseModel):
    """Technical indicators for ETF"""
    symbol: str = Field(..., description="ETF symbol")
    date: DateType = Field(..., description="Date")
    
    # Moving averages
    sma_20: Optional[float] = Field(None, description="20-day Simple Moving Average")
    sma_50: Optional[float] = Field(None, description="50-day Simple Moving Average")
    sma_200: Optional[float] = Field(None, description="200-day Simple Moving Average")
    ema_12: Optional[float] = Field(None, description="12-day Exponential Moving Average")
    ema_26: Optional[float] = Field(None, description="26-day Exponential Moving Average")
    
    # Momentum indicators
    rsi_14: Optional[float] = Field(None, description="14-day RSI")
    macd: Optional[float] = Field(None, description="MACD line")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    macd_histogram: Optional[float] = Field(None, description="MACD histogram")
    
    # Volatility indicators
    bollinger_upper: Optional[float] = Field(None, description="Bollinger Upper Band")
    bollinger_middle: Optional[float] = Field(None, description="Bollinger Middle Band")
    bollinger_lower: Optional[float] = Field(None, description="Bollinger Lower Band")
    atr_14: Optional[float] = Field(None, description="14-day Average True Range")
    
    # Volume indicators
    volume_sma: Optional[float] = Field(None, description="Volume SMA")
    on_balance_volume: Optional[float] = Field(None, description="On Balance Volume")


class ETFDividendHistory(BaseModel):
    """Dividend payment history"""
    date: DateType = Field(..., description="Ex-dividend date")
    amount: float = Field(..., description="Dividend amount per share")
    payment_date: Optional[DateType] = Field(None, description="Payment date")
    record_date: Optional[DateType] = Field(None, description="Record date")


class ETFComparison(BaseModel):
    """ETF comparison data"""
    symbol: str = Field(..., description="ETF symbol")
    name: str = Field(..., description="ETF name")
    
    # Performance metrics
    return_1d: Optional[float] = Field(None, description="1-day return (%)")
    return_1w: Optional[float] = Field(None, description="1-week return (%)")
    return_1m: Optional[float] = Field(None, description="1-month return (%)")
    return_3m: Optional[float] = Field(None, description="3-month return (%)")
    return_6m: Optional[float] = Field(None, description="6-month return (%)")
    return_1y: Optional[float] = Field(None, description="1-year return (%)")
    return_3y: Optional[float] = Field(None, description="3-year return (%)")
    return_5y: Optional[float] = Field(None, description="5-year return (%)")
    
    # Risk metrics
    volatility_1y: Optional[float] = Field(None, description="1-year volatility")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    
    # Fund metrics
    aum: Optional[float] = Field(None, description="Assets Under Management")
    expense_ratio: Optional[float] = Field(None, description="Expense ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield")
    
    # Current price
    current_price: Optional[float] = Field(None, description="Current price")


class ETFIndustryDistribution(BaseModel):
    """Industry distribution within ETF"""
    industry: str = Field(..., description="Industry name")
    weight: float = Field(..., description="Weight in ETF (as percentage)")
    holdings_count: Optional[int] = Field(None, description="Number of holdings in this industry")


class ETFSectorDistribution(BaseModel):
    """Sector distribution within ETF"""
    sector: str = Field(..., description="Sector name")
    weight: float = Field(..., description="Weight in ETF (as percentage)")
    holdings_count: Optional[int] = Field(None, description="Number of holdings in this sector")


class ETFDashboardResponse(BaseModel):
    """Complete ETF dashboard response"""
    symbol: str = Field(..., description="ETF symbol")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    # Basic info
    basic_info: ETFBasicInfo = Field(..., description="Basic ETF information")
    
    # Price data
    price_data: List[ETFPriceData] = Field(default_factory=list, description="Historical price data")
    
    # Holdings
    top_holdings: List[ETFHolding] = Field(default_factory=list, description="Top holdings")
    total_holdings_count: Optional[int] = Field(None, description="Total number of holdings")
    holdings_concentration: Optional[float] = Field(None, description="Top 10 holdings concentration (%)")
    
    # Distribution
    sector_distribution: List[ETFSectorDistribution] = Field(default_factory=list, description="Sector distribution")
    industry_distribution: List[ETFIndustryDistribution] = Field(default_factory=list, description="Industry distribution")
    
    # Risk metrics
    risk_metrics: Optional[ETFRiskMetrics] = Field(None, description="Risk metrics")
    
    # Technical indicators
    technical_indicators: List[ETFTechnicalIndicators] = Field(default_factory=list, description="Technical indicators")
    
    # Dividend history
    dividend_history: List[ETFDividendHistory] = Field(default_factory=list, description="Dividend history")
    
    # Comparison data (optional)
    comparison_data: Optional[List[ETFComparison]] = Field(None, description="Comparison with similar ETFs")
    
    # Additional metadata
    data_source: str = Field(default="polygon", description="Primary data source used")
    cache_timestamp: Optional[datetime] = Field(None, description="Cache timestamp if data was cached")

