# FutureQuant Quantitative Analysis Integration

This document describes the integration of three powerful quantitative finance libraries into the FutureQuant trading system:

- **VectorBT**: Vectorized backtesting and analysis
- **QF-Lib**: Quantitative Finance Library for risk and factor analysis  
- **Lean**: QuantConnect LEAN Engine for algorithmic trading

## Overview

The quantitative analysis integration provides a comprehensive suite of tools for:
- Strategy backtesting and optimization
- Risk management and portfolio analysis
- Factor analysis and statistical modeling
- Algorithmic trading simulation
- Performance benchmarking and comparison

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FutureQuant System                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  VectorBT   │  │   QF-Lib    │  │    Lean     │        │
│  │   Service   │  │   Service   │  │   Service   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│              Unified Quantitative Service                   │
├─────────────────────────────────────────────────────────────┤
│              API Endpoints & Integration                    │
└─────────────────────────────────────────────────────────────┘
```

## Services

### 1. VectorBT Service (`vectorbt_service.py`)

**Purpose**: High-performance vectorized backtesting and strategy analysis

**Features**:
- Momentum strategies
- Mean reversion strategies  
- Trend following strategies
- Statistical arbitrage strategies
- Advanced portfolio analytics
- Risk metrics calculation

**Key Methods**:
```python
async def run_vectorbt_backtest(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    strategy_type: str,
    custom_params: Dict[str, Any] = None
) -> Dict[str, Any]
```

**Strategy Types**:
- `momentum`: Price momentum-based strategies
- `mean_reversion`: Mean reversion strategies using Bollinger Bands
- `trend_following`: Moving average crossover strategies with ATR
- `statistical_arbitrage`: Z-score based statistical arbitrage

### 2. QF-Lib Service (`qflib_service.py`)

**Purpose**: Quantitative finance analysis and risk management

**Features**:
- Risk metrics calculation (VaR, CVaR, Sharpe ratio)
- Factor analysis (market, size, volatility factors)
- Portfolio optimization (minimum variance, maximum Sharpe)
- Correlation and beta analysis
- Statistical modeling

**Key Methods**:
```python
async def run_qflib_analysis(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    analysis_type: str
) -> Dict[str, Any]
```

**Analysis Types**:
- `risk_metrics`: Comprehensive risk analysis
- `factor_analysis`: Factor decomposition and analysis
- `portfolio_optimization`: Portfolio weight optimization

### 3. Lean Service (`lean_service.py`)

**Purpose**: Algorithmic trading simulation and execution

**Features**:
- Strategy code parsing and execution
- Real-time signal generation
- Position sizing and risk management
- Trade execution simulation
- Performance tracking

**Key Methods**:
```python
async def run_lean_backtest(
    strategy_id: int,
    start_date: str,
    end_date: str,
    symbols: List[str],
    strategy_code: str,
    custom_config: Dict[str, Any] = None
) -> Dict[str, Any]
```

### 4. Unified Service (`unified_quant_service.py`)

**Purpose**: Orchestrates all three libraries for comprehensive analysis

**Features**:
- Multi-library analysis coordination
- Performance comparison across strategies
- Unified reporting and recommendations
- Benchmark comparison
- Risk assessment aggregation

## API Endpoints

### Base URL: `/quantitative-analysis`

#### 1. Comprehensive Analysis
```http
POST /comprehensive-analysis
```
Runs analysis using all three libraries based on specified types.

**Parameters**:
- `strategy_id`: Strategy identifier
- `start_date`: Analysis start date (YYYY-MM-DD)
- `end_date`: Analysis end date (YYYY-MM-DD)
- `symbols`: List of trading symbols
- `analysis_types`: List of analysis types to run
- `custom_params`: Optional custom parameters

#### 2. VectorBT Backtesting
```http
POST /vectorbt-backtest
```
Runs VectorBT backtest for specific strategy type.

**Parameters**:
- `strategy_id`: Strategy identifier
- `start_date`: Backtest start date
- `end_date`: Backtest end date
- `symbols`: Trading symbols
- `strategy_type`: Strategy type (momentum, mean_reversion, etc.)
- `custom_params`: Optional custom parameters

#### 3. QF-Lib Analysis
```http
POST /qflib-analysis
```
Runs QF-Lib quantitative analysis.

**Parameters**:
- `strategy_id`: Strategy identifier
- `start_date`: Analysis start date
- `end_date`: Analysis end date
- `symbols`: Trading symbols
- `analysis_type`: Analysis type (risk_metrics, factor_analysis, etc.)

#### 4. Lean Backtesting
```http
POST /lean-backtest
```
Runs Lean algorithmic trading simulation.

**Parameters**:
- `strategy_id`: Strategy identifier
- `start_date`: Backtest start date
- `end_date`: Backtest end date
- `symbols`: Trading symbols
- `strategy_code`: Strategy implementation code
- `custom_config`: Optional configuration

#### 5. Portfolio Analysis
```http
GET /portfolio-analysis/{backtest_id}
```
Retrieves detailed portfolio analysis for a completed backtest.

**Parameters**:
- `backtest_id`: Backtest identifier
- `analysis_type`: Type of analysis (vectorbt, qflib, lean)

#### 6. Benchmark Comparison
```http
POST /benchmark-comparison
```
Compares strategy performance against benchmark across all libraries.

**Parameters**:
- `strategy_id`: Strategy identifier
- `start_date`: Comparison start date
- `end_date`: Comparison end date
- `symbols`: Trading symbols
- `benchmark_symbol`: Benchmark symbol (default: SPY)

#### 7. Available Strategies
```http
GET /available-strategies
```
Returns available strategy types for each library.

#### 8. Library Information
```http
GET /library-info
```
Returns detailed information about integrated libraries.

## Usage Examples

### 1. Running Comprehensive Analysis

```python
import requests

# Run comprehensive analysis
response = requests.post("http://localhost:8000/quantitative-analysis/comprehensive-analysis", json={
    "strategy_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "symbols": ["ES=F", "CL=F", "GC=F"],
    "analysis_types": ["momentum", "risk_metrics", "portfolio_optimization"],
    "custom_params": {
        "momentum": {"window": 20, "threshold": 0.02},
        "portfolio_optimization": {"risk_tolerance": "moderate"}
    }
})

result = response.json()
print(f"Analysis completed: {result['success']}")
print(f"Unified report: {result['unified_report']}")
```

### 2. VectorBT Momentum Strategy

```python
# Run VectorBT momentum backtest
response = requests.post("http://localhost:8000/quantitative-analysis/vectorbt-backtest", json={
    "strategy_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "symbols": ["ES=F"],
    "strategy_type": "momentum",
    "custom_params": {
        "window": 20,
        "threshold": 0.02,
        "stop_loss": 0.05,
        "take_profit": 0.10
    }
})

result = response.json()
if result['success']:
    print(f"Total Return: {result['results']['total_return']:.2%}")
    print(f"Sharpe Ratio: {result['results']['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {result['results']['max_drawdown']:.2%}")
```

### 3. QF-Lib Risk Analysis

```python
# Run QF-Lib risk metrics analysis
response = requests.post("http://localhost:8000/quantitative-analysis/qflib-analysis", json={
    "strategy_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "symbols": ["ES=F", "CL=F", "GC=F"],
    "analysis_type": "risk_metrics"
})

result = response.json()
if result['success']:
    risk_data = result['results']
    print(f"Sharpe Ratios: {risk_data['returns_analysis']['sharpe_ratio']}")
    print(f"VaR (95%): {risk_data['risk_metrics']['var_95']}")
    print(f"Max Drawdown: {risk_data['risk_metrics']['max_drawdown']}")
```

### 4. Lean Algorithmic Trading

```python
# Run Lean backtest
strategy_code = """
// Simple momentum strategy
public class MomentumStrategy : QCAlgorithm
{
    private int lookbackPeriod = 20;
    private decimal threshold = 0.02m;
    
    public override void Initialize()
    {
        SetStartDate(2024, 1, 1);
        SetEndDate(2024, 12, 31);
        AddEquity("ES=F");
    }
}
"""

response = requests.post("http://localhost:8000/quantitative-analysis/lean-backtest", json={
    "strategy_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "symbols": ["ES=F"],
    "strategy_code": strategy_code,
    "custom_config": {
        "initial_capital": 100000,
        "commission_rate": 0.001,
        "slippage": 0.0005
    }
})

result = response.json()
if result['success']:
    print(f"Final Capital: ${result['results']['final_capital']:,.2f}")
    print(f"Total Return: {result['results']['total_return']:.2%}")
    print(f"Trades Executed: {result['results']['trades_count']}")
```

## Configuration

### VectorBT Configuration
```python
vbt_config = {
    "fees": 0.001,           # 0.1% commission
    "slippage": 0.0005,      # 0.05% slippage
    "freq": "1D",            # Daily frequency
    "init_cash": 100000,     # Initial capital
    "size": 0.1,             # Position size as fraction of portfolio
    "accumulate": False,      # Don't accumulate positions
    "upon_long_conflict": "ignore",
    "upon_short_conflict": "ignore"
}
```

### QF-Lib Configuration
```python
qf_config = {
    "risk_free_rate": 0.02,      # 2% annual risk-free rate
    "benchmark": "SPY",          # Benchmark symbol
    "confidence_level": 0.95,    # VaR confidence level
    "lookback_period": 252       # Trading days in year
}
```

### Lean Configuration
```python
lean_config = {
    "initial_capital": 100000,
    "benchmark": "SPY",
    "risk_free_rate": 0.02,
    "brokerage_model": "InteractiveBrokersBrokerageModel",
    "data_feed": "InteractiveBrokers",
    "resolution": "Minute",
    "warmup_period": 30
}
```

## Performance Metrics

### VectorBT Metrics
- Total Return
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- Total Trades
- Portfolio Value
- Drawdown Curve

### QF-Lib Metrics
- Annualized Return
- Annualized Volatility
- Sharpe Ratio
- Value at Risk (VaR)
- Conditional VaR (CVaR)
- Maximum Drawdown
- Correlation Matrix
- Beta Coefficients

### Lean Metrics
- Total Return
- Sharpe Ratio
- Maximum Drawdown
- Trade Count
- Portfolio Values
- Position History
- Final Positions

## Error Handling

All services include comprehensive error handling:

```python
try:
    result = await service.run_analysis(...)
    if result.get("success"):
        # Process successful result
        pass
    else:
        # Handle error
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Analysis failed: {error_msg}")
except Exception as e:
    logger.error(f"Service error: {str(e)}")
    # Handle exception
```

## Testing

Run the test suite:

```bash
# Run all quantitative analysis tests
python3 -m pytest tests/test_quantitative_analysis.py -v

# Run specific service tests
python3 -m pytest tests/test_quantitative_analysis.py::TestVectorBTService -v
python3 -m pytest tests/test_quantitative_analysis.py::TestQFLibService -v
python3 -m pytest tests/test_quantitative_analysis.py::TestLeanService -v
```

## Dependencies

The following packages are required:

```txt
# Quantitative Finance Libraries
vectorbt==0.25.4          # Vectorized backtesting and analysis
qf-lib==1.0.0             # Quantitative Finance Library
lean==1.0.0               # QuantConnect LEAN Engine
empyrical==0.5.5          # Financial risk and performance analytics
pyfolio==0.9.2            # Portfolio and risk analysis
alphalens==0.4.0          # Alpha factor analysis
pykalman==0.9.5           # Kalman filtering for time series
arch==6.2.0               # Autoregressive conditional heteroskedasticity models
statsmodels==0.14.1       # Statistical models and tests
scipy==1.12.0             # Scientific computing
```

## Future Enhancements

- Real-time data streaming integration
- Machine learning model integration
- Advanced risk management features
- Multi-asset class support
- Cloud deployment optimization
- Performance benchmarking database
- Strategy marketplace integration

## Support

For questions and support regarding the quantitative analysis integration:

1. Check the test files for usage examples
2. Review the API documentation
3. Examine the service implementations
4. Run the test suite to verify functionality

## License

This integration is part of the FutureQuant trading system and follows the same licensing terms.
