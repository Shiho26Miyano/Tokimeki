# Portfolio Manager Dashboard

A multi-agent portfolio management system built with FastAPI backend and Streamlit frontend, designed to provide comprehensive portfolio analysis, risk management, and trading strategy generation.

## Features

### Multi-Agent Architecture
- **Data Agent**: Collects and processes market data from Yahoo Finance
- **Research Agent**: Analyzes market conditions and identifies market regimes
- **Strategy Agent**: Designs trading strategies based on market conditions
- **Risk Agent**: Calculates risk metrics and provides risk analysis
- **Execution Agent**: Creates trade execution plans and position sizing

### Portfolio Analysis
- Multi-timeframe analysis with customizable date ranges
- Regime-aware strategy selection (Bull, Bear, High Volatility, Low Volatility, Neutral)
- Technical indicators: Moving averages, RSI, Bollinger Bands, ATR
- Risk-adjusted performance metrics (Sharpe ratio, max drawdown, Calmar ratio)
- Transaction cost modeling (commissions and slippage)

### Interactive Dashboard
- Real-time data visualization with Plotly charts
- Tabbed interface for different analysis components
- Agent activity logging and monitoring
- Responsive design with custom CSS styling

## Architecture

```
Frontend (Streamlit) ←→ Backend (FastAPI) ←→ Portfolio Service
                                              ↓
                                    Multi-Agent Workflow
                                              ↓
                                    Data → Research → Strategy → Risk → Execution
```

## Installation

### Prerequisites
- Python 3.8+
- FastAPI backend running on localhost:8000

### Backend Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the FastAPI backend:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
1. Install Streamlit:
```bash
pip install streamlit plotly
```

2. Run the dashboard:
```bash
streamlit run portfolio_dashboard.py
```

## Usage

### 1. Configuration
- **Tickers**: Enter comma-separated stock symbols (e.g., SPY,QQQ,AAPL,MSFT)
- **Primary Ticker**: Select the main asset for analysis
- **Date Range**: Choose start and end dates for analysis
- **Transaction Costs**: Set commission and slippage in basis points

### 2. Analysis Execution
- Click "Run Portfolio Analysis" to start the multi-agent workflow
- Monitor agent progress through the activity log
- View results across five main tabs

### 3. Results Interpretation

#### Overview Tab
- Price charts with technical indicators
- Market regime classification
- Research thesis summary
- Quick statistics

#### Research Tab
- Market regime analysis
- Trend strength assessment
- Volatility analysis

#### Strategy Tab
- Strategy type and parameters
- Moving average settings
- Position sizing recommendations

#### Risk Tab
- Performance metrics (Sharpe, max drawdown, etc.)
- Risk-adjusted return analysis
- Risk warnings and recommendations

#### Execution Tab
- Trade execution plan
- Current position status
- Stop-loss and take-profit levels
- Agent activity log

## API Endpoints

### Portfolio Analysis
- `POST /api/v1/portfolio/analyze` - Run complete portfolio analysis
- `GET /api/v1/portfolio/regimes` - Get available market regimes
- `GET /api/v1/portfolio/strategies` - Get trading strategy types
- `GET /api/v1/portfolio/metrics` - Get risk metric definitions

### Request Format
```json
{
  "tickers": ["SPY", "QQQ", "AAPL"],
  "primary": "SPY",
  "start": "2024-01-01",
  "end": "2024-12-31",
  "fee_bps": 1.0,
  "slip_bps": 2.0
}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "regime": "Bull",
    "thesis": ["Market Regime: **Bull**", "..."],
    "strategy_params": {...},
    "backtest_results": {...},
    "risk_notes": [...],
    "trade_plan": [...],
    "agent_log": [...]
  },
  "message": "Portfolio analysis completed successfully"
}
```

## Market Regimes

### Bull Market
- Strong upward trend with positive momentum
- Strategy: Momentum-based with fast moving averages
- Position sizing: Full allocation

### Bear Market
- Strong downward trend with negative momentum
- Strategy: Mean reversion with shorter timeframes
- Position sizing: Reduced allocation

### High Volatility
- Elevated volatility above historical average
- Strategy: Volatility breakout with tight stops
- Position sizing: Conservative allocation

### Low Volatility
- Below average volatility levels
- Strategy: Range trading with mean reversion
- Position sizing: Standard allocation

### Neutral
- Sideways or mixed market conditions
- Strategy: Trend following with filters
- Position sizing: Moderate allocation

## Trading Strategies

### Momentum Strategy
- Fast moving average crossover
- Best for: Bull markets
- Risk level: Medium

### Mean Reversion Strategy
- Statistical mean reversion signals
- Best for: Bear markets, range-bound conditions
- Risk level: High

### Volatility Breakout Strategy
- Volatility expansion detection
- Best for: High volatility regimes
- Risk level: High

### Trend Following Strategy
- Classical moving average approach
- Best for: Trending markets
- Risk level: Medium

## Risk Metrics

### Sharpe Ratio
- **Excellent**: > 1.5
- **Good**: 1.0 - 1.5
- **Fair**: 0.5 - 1.0
- **Poor**: < 0.5

### Maximum Drawdown
- **Excellent**: < -10%
- **Good**: -10% to -15%
- **Fair**: -15% to -25%
- **Poor**: > -25%

### Calmar Ratio
- **Excellent**: > 2.0
- **Good**: 1.0 - 2.0
- **Fair**: 0.5 - 1.0
- **Poor**: < 0.5

### Win Rate
- **Excellent**: > 60%
- **Good**: 50% - 60%
- **Fair**: 40% - 50%
- **Poor**: < 40%

## Testing

Run the test suite:
```bash
python -m pytest tests/unit/test_portfolio_service.py -v
```

## Customization

### Adding New Agents
1. Create agent function in `PortfolioService`
2. Add to workflow in `run_portfolio_workflow`
3. Update state management and logging

### Adding New Strategies
1. Extend `strategy_agent` method
2. Add strategy parameters and logic
3. Update regime-strategy mapping

### Adding New Risk Metrics
1. Extend `_run_backtest` method
2. Add new calculations
3. Update risk analysis and notes

## Troubleshooting

### Common Issues

1. **Backend Connection Error**
   - Ensure FastAPI server is running on port 8000
   - Check firewall and network settings

2. **Data Loading Issues**
   - Verify ticker symbols are valid
   - Check internet connection for Yahoo Finance access
   - Ensure sufficient historical data exists

3. **Performance Issues**
   - Reduce date range for faster analysis
   - Limit number of tickers
   - Check system resources

### Debug Mode
Enable debug logging in the backend:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub
4. Contact the development team

## Roadmap

### Phase 2 Features
- Real-time data streaming
- Advanced machine learning models
- Portfolio optimization algorithms
- Multi-asset class support
- Integration with broker APIs

### Phase 3 Features
- Cloud deployment
- User authentication and portfolios
- Advanced backtesting engine
- Risk management automation
- Performance attribution analysis
