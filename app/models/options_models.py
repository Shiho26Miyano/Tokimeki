"""
Pydantic models for Consumer Options Sentiment Dashboard
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from datetime import date as DateType
from pydantic import BaseModel, Field
from enum import Enum

class ContractType(str, Enum):
    CALL = "call"
    PUT = "put"

class OptionContract(BaseModel):
    """Individual option contract data"""
    contract: str = Field(..., description="Contract symbol")
    underlying: str = Field(..., description="Underlying ticker")
    expiry: DateType = Field(..., description="Expiration date")
    strike: float = Field(..., description="Strike price")
    type: ContractType = Field(..., description="Call or Put")
    
    # Market data
    last_price: Optional[float] = Field(None, description="Last trade price")
    bid: Optional[float] = Field(None, description="Bid price")
    ask: Optional[float] = Field(None, description="Ask price")
    
    # Volume and OI
    day_volume: Optional[int] = Field(None, description="Today's volume")
    day_oi: Optional[int] = Field(None, description="Open interest")
    
    # Greeks and IV
    implied_volatility: Optional[float] = Field(None, description="Implied volatility")
    delta: Optional[float] = Field(None, description="Delta")
    gamma: Optional[float] = Field(None, description="Gamma")
    theta: Optional[float] = Field(None, description="Theta")
    vega: Optional[float] = Field(None, description="Vega")
    
    # Flags
    is_unusual: Optional[bool] = Field(False, description="Unusual activity flag")
    unusual_reason: Optional[str] = Field(None, description="Reason for unusual flag")

class CallPutRatios(BaseModel):
    """Call/Put ratio analysis"""
    ticker: str = Field(..., description="Underlying ticker")
    analysis_date: DateType = Field(..., description="Analysis date")
    
    # Volume ratios
    call_volume: int = Field(..., description="Total call volume")
    put_volume: int = Field(..., description="Total put volume")
    volume_ratio: Optional[float] = Field(None, description="Call/Put volume ratio")
    
    # Open interest ratios
    call_oi: int = Field(..., description="Total call open interest")
    put_oi: int = Field(..., description="Total put open interest")
    oi_ratio: Optional[float] = Field(None, description="Call/Put OI ratio")
    
    # Sentiment indicators
    sentiment: str = Field(..., description="Bullish/Bearish/Neutral")
    confidence: float = Field(..., description="Confidence score 0-1")
    
    # Additional metrics
    median_iv: Optional[float] = Field(None, description="Median implied volatility across all contracts")

class IVTermPoint(BaseModel):
    """IV term structure data point"""
    expiry: DateType = Field(..., description="Expiration date")
    days_to_expiry: int = Field(..., description="Days until expiration")
    median_iv: float = Field(..., description="Median implied volatility")
    contract_count: int = Field(..., description="Number of contracts")

class UnusualActivity(BaseModel):
    """Unusual activity detection"""
    contract: str = Field(..., description="Contract symbol")
    trigger_type: str = Field(..., description="Volume/OI/IV")
    current_value: float = Field(..., description="Current value")
    average_value: float = Field(..., description="Historical average")
    z_score: float = Field(..., description="Z-score vs historical")
    threshold: float = Field(..., description="Threshold used")
    timestamp: datetime = Field(..., description="Detection timestamp")

class UnderlyingData(BaseModel):
    """Underlying stock data"""
    ticker: str = Field(..., description="Stock ticker")
    bar_date: DateType = Field(..., description="Date")
    
    # OHLCV
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: int = Field(..., description="Volume")
    
    # Technical indicators
    sma_20: Optional[float] = Field(None, description="20-day SMA")
    sma_50: Optional[float] = Field(None, description="50-day SMA")
    rsi_14: Optional[float] = Field(None, description="14-day RSI")

class ContractBars(BaseModel):
    """1-minute contract price/volume data"""
    contract: str = Field(..., description="Contract symbol")
    timestamp: datetime = Field(..., description="Bar timestamp")
    
    # OHLCV
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: int = Field(..., description="Volume")

# Request/Response models
class ChainSnapshotRequest(BaseModel):
    """Request for option chain snapshot"""
    ticker: str = Field(..., description="Underlying ticker")
    expiry_filter: Optional[List[str]] = Field(None, description="Filter by expiries (YYYY-MM-DD)")
    strike_range: Optional[Dict[str, float]] = Field(None, description="Strike range filter")

class ChainSnapshotResponse(BaseModel):
    """Response for option chain snapshot"""
    ticker: str = Field(..., description="Underlying ticker")
    timestamp: datetime = Field(..., description="Data timestamp")
    contracts: List[OptionContract] = Field(..., description="Option contracts")
    total_contracts: int = Field(..., description="Total contract count")

class AnalyticsRequest(BaseModel):
    """Request for analytics data"""
    tickers: List[str] = Field(..., description="List of tickers to analyze")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    analysis_types: List[str] = Field(default=["call_put_ratios", "iv_term", "unusual"], 
                                    description="Types of analysis to perform")

class AnalyticsResponse(BaseModel):
    """Response for analytics data"""
    timestamp: datetime = Field(..., description="Analysis timestamp")
    call_put_ratios: Dict[str, CallPutRatios] = Field(..., description="Call/Put ratios by ticker")
    iv_term_structure: Dict[str, List[IVTermPoint]] = Field(..., description="IV term structure by ticker")
    unusual_activity: List[UnusualActivity] = Field(..., description="Unusual activity alerts")

class DashboardRequest(BaseModel):
    """Request for dashboard data"""
    tickers: List[str] = Field(default=["COST", "WMT", "TGT", "AMZN", "AAPL"], 
                              description="Tickers to display")
    focus_ticker: str = Field(default="COST", description="Primary ticker for detailed view")
    date_range_days: int = Field(default=60, description="Days of historical data")

class DashboardResponse(BaseModel):
    """Complete dashboard data response"""
    focus_ticker: str = Field(..., description="Primary ticker")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # Chain data
    chain_data: ChainSnapshotResponse = Field(..., description="Option chain data")
    
    # Analytics
    call_put_ratios: CallPutRatios = Field(..., description="Call/Put analysis")
    iv_term_structure: List[IVTermPoint] = Field(..., description="IV term structure")
    unusual_activity: List[UnusualActivity] = Field(..., description="Unusual activity")
    
    # Chart data
    oi_heatmap_data: Optional[Dict[str, Any]] = Field(None, description="Open Interest Change heatmap data")
    delta_distribution_data: Optional[Dict[str, Any]] = Field(None, description="Delta Distribution histogram data")
    
    # Underlying data
    underlying_data: List[UnderlyingData] = Field(..., description="Historical underlying data")
    
    # Contract drilldown (if selected)
    contract_bars: Optional[List[ContractBars]] = Field(None, description="Selected contract bars")

class ContractDrilldownRequest(BaseModel):
    """Request for contract drilldown data"""
    contract: str = Field(..., description="Contract symbol to analyze")
    date_range_days: int = Field(default=5, description="Days of historical data")

class ContractDrilldownResponse(BaseModel):
    """Response for contract drilldown"""
    contract: str = Field(..., description="Contract symbol")
    contract_info: OptionContract = Field(..., description="Contract details")
    bars: List[ContractBars] = Field(..., description="Historical price/volume data")
    latest_greeks: Dict[str, float] = Field(..., description="Latest Greeks and IV")
