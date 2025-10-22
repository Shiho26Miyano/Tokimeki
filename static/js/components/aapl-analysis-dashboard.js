/**
 * AAPL Stock vs Weekly Options Analysis Dashboard
 * React component for analyzing AAPL stock DCA vs weekly option strategies
 */

// Wait for React to be available before defining the component
(function() {
    'use strict';
    
    function defineComponent() {
        if (typeof React === 'undefined' || typeof React.Component === 'undefined') {
            console.log('React not available yet for AAPLAnalysisDashboard, retrying in 100ms...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining AAPLAnalysisDashboard component...');

class AAPLAnalysisDashboard extends React.Component {
    constructor(props) {
        super(props);
        
        // Calculate default date range (1 year)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setFullYear(endDate.getFullYear() - 1);
        
        this.state = {
            // Backtest parameters
            backtestWindow: 1,
            startDate: startDate.toISOString().split('T')[0],
            endDate: endDate.toISOString().split('T')[0],
            buyWeekday: 1, // Tuesday
            sharesPerWeek: 100,
            optionType: 'call',
            moneynessOffset: 0.0,
            minDaysToExpiry: 1,
            contractsPerWeek: 1,
            feePerTrade: 0.0,
            
            // Results
            stockResult: null,
            optionResult: null,
            combinedResult: null,
            diagnostics: null,
            
            // UI state
            loading: false,
            error: null,
            activeTab: 'controls',
            selectedStrategy: 'options', // 'stock' or 'options'
            
            // Chart data
            stockEquityCurve: [],
            optionPnLCurve: [],
            stockEntries: [],
            optionTrades: []
        };
        
        this.runBacktest = this.runBacktest.bind(this);
        this.handleParameterChange = this.handleParameterChange.bind(this);
        this.renderChart = this.renderChart.bind(this);
        this.refreshData = this.refreshData.bind(this);
    }
    
    componentDidMount() {
        console.log('AAPL Analysis Dashboard mounted');
        // Load cached performance data first (fast)
        this.loadCachedData();
        // Then load defaults
        this.loadDefaults();
    }
    
    async loadDefaults() {
        try {
            console.log('Loading AAPL analysis defaults...');
            const response = await fetch('/api/v1/aapl-analysis/defaults');
            console.log('Defaults response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Defaults data:', data);
            
            if (data.stock_dca && data.weekly_option) {
                this.setState({
                    startDate: data.stock_dca.start_date,
                    endDate: data.stock_dca.end_date,
                    sharesPerWeek: data.stock_dca.shares_per_week,
                    buyWeekday: data.stock_dca.buy_weekday,
                    optionType: data.weekly_option.option_type,
                    moneynessOffset: data.weekly_option.moneyness_offset,
                    minDaysToExpiry: data.weekly_option.min_days_to_expiry,
                    contractsPerWeek: data.weekly_option.contracts_per_week
                });
                console.log('Defaults loaded successfully');
            }
        } catch (error) {
            console.error('Failed to load defaults:', error);
            // Set some fallback defaults so the UI still works
            const endDate = new Date();
            const startDate = new Date();
            startDate.setFullYear(endDate.getFullYear() - 1);
            
            this.setState({
                startDate: startDate.toISOString().split('T')[0],
                endDate: endDate.toISOString().split('T')[0],
                error: `API Error: ${error.message}. Using fallback defaults.`
            });
        }
    }
    
    async loadCachedData() {
        try {
            console.log('Loading cached AAPL performance data...');
            const response = await fetch('/api/v1/aapl-analysis/dashboard');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Cached data loaded:', data);
            
            // Update state with cached performance data
            this.setState({
                cachedPerformance: data,
                lastUpdated: data.last_updated,
                // Show some quick results
                stockResult: {
                    total_cost: data.stock_performance?.market_value || 0,
                    market_value: data.stock_performance?.market_value || 0,
                    unrealized_pnl: data.stock_performance?.total_return || 0,
                    total_entries: 0,
                    total_shares: 0,
                    cost_basis: 0
                },
                optionResult: {
                    total_pnl: data.option_performance?.total_pnl || 0,
                    total_trades: data.option_performance?.total_trades || 0,
                    win_rate: data.option_performance?.win_rate || 0,
                    avg_win: 0,
                    avg_loss: 0,
                    max_win: 0
                },
                combinedResult: {
                    comparison_metrics: {
                        stock_return_pct: data.stock_performance?.return_pct || 0,
                        combined_return: data.stock_performance?.total_return + data.option_performance?.total_pnl || 0
                    }
                },
                activeTab: 'results' // Show results immediately
            });
            
        } catch (error) {
            console.error('Failed to load cached data:', error);
            // Don't show error for cached data, just continue with defaults
        }
    }
    
    handleParameterChange(event) {
        const { name, value, type } = event.target;
        const parsedValue = type === 'number' ? parseFloat(value) : value;
        
        this.setState({ [name]: parsedValue });
        
        // Update date range based on backtest window
        if (name === 'backtestWindow') {
            const endDate = new Date();
            const startDate = new Date();
            startDate.setFullYear(endDate.getFullYear() - parsedValue);
            
            this.setState({
                startDate: startDate.toISOString().split('T')[0],
                endDate: endDate.toISOString().split('T')[0]
            });
        }
    }
    
    async runBacktest() {
        this.setState({ loading: true, error: null });
        
        try {
            const requestBody = {
                stock_params: {
                    ticker: 'AAPL',
                    start_date: this.state.startDate,
                    end_date: this.state.endDate,
                    shares_per_week: this.state.sharesPerWeek,
                    buy_weekday: this.state.buyWeekday,
                    fee_per_trade: this.state.feePerTrade
                },
                option_params: {
                    ticker: 'AAPL',
                    start_date: this.state.startDate,
                    end_date: this.state.endDate,
                    option_type: this.state.optionType,
                    moneyness_offset: this.state.moneynessOffset,
                    min_days_to_expiry: this.state.minDaysToExpiry,
                    contracts_per_week: this.state.contractsPerWeek,
                    buy_weekday: this.state.buyWeekday,
                    fee_per_trade: this.state.feePerTrade
                }
            };
            
            const response = await fetch('/api/v1/aapl-analysis/backtest/combined', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.message || 'Backtest failed');
            }
            
            this.setState({
                combinedResult: result.data,
                stockResult: result.data.stock_result,
                optionResult: result.data.option_result,
                diagnostics: result.diagnostics,
                activeTab: 'results'
            });
            
            // Process data for charts
            this.processChartData(result.data);
            
        } catch (error) {
            console.error('Backtest error:', error);
            this.setState({ error: error.message });
        } finally {
            this.setState({ loading: false });
        }
    }
    
    async refreshData() {
        try {
            this.setState({ loading: true, error: null });
            
            console.log('Refreshing AAPL analysis data...');
            const response = await fetch('/api/v1/aapl-analysis/refresh', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Refresh response:', result);
            
            // Reload cached data after refresh
            setTimeout(() => {
                this.loadCachedData();
                this.setState({ loading: false });
            }, 2000); // Give it 2 seconds to process
            
        } catch (error) {
            console.error('Refresh error:', error);
            this.setState({ 
                error: `Refresh failed: ${error.message}`,
                loading: false 
            });
        }
    }
    
    processChartData(data) {
        const stockEntries = data.stock_result.entries || [];
        const optionTrades = data.option_result.trades || [];
        
        // Build stock equity curve
        const stockEquityCurve = [];
        let cumulativeCost = 0;
        let cumulativeShares = 0;
        
        stockEntries.forEach(entry => {
            cumulativeCost += entry.cost + entry.fees;
            cumulativeShares += entry.shares;
            const marketValue = cumulativeShares * entry.price;
            const unrealizedPnL = marketValue - cumulativeCost;
            
            stockEquityCurve.push({
                date: entry.date,
                cost: cumulativeCost,
                marketValue: marketValue,
                unrealizedPnL: unrealizedPnL,
                shares: cumulativeShares
            });
        });
        
        // Build option PnL curve
        const optionPnLCurve = [];
        let cumulativePnL = 0;
        
        optionTrades.forEach(trade => {
            cumulativePnL += trade.pnl;
            optionPnLCurve.push({
                date: trade.exit_date,
                pnl: trade.pnl,
                cumulativePnL: cumulativePnL
            });
        });
        
        this.setState({
            stockEquityCurve,
            optionPnLCurve,
            stockEntries,
            optionTrades
        });
    }
    
    renderChart() {
        if (!this.state.stockEquityCurve.length && !this.state.optionPnLCurve.length) {
            return <div className="text-center text-muted">No data to display</div>;
        }
        
        return (
            <div className="chart-container">
                <canvas id="equityCurveChart" width="800" height="400"></canvas>
            </div>
        );
    }
    
    renderControls() {
        return (
            <div className="row">
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">Backtest Parameters</h5>
                        </div>
                        <div className="card-body">
                            <div className="mb-3">
                                <label className="form-label">Backtest Window (Years)</label>
                                <select 
                                    className="form-select" 
                                    name="backtestWindow" 
                                    value={this.state.backtestWindow}
                                    onChange={this.handleParameterChange}
                                >
                                    <option value={1}>1 Year</option>
                                    <option value={2}>2 Years</option>
                                    <option value={3}>3 Years</option>
                                    <option value={5}>5 Years</option>
                                    <option value={10}>10 Years</option>
                                </select>
                            </div>
                            
                            <div className="row">
                                <div className="col-6">
                                    <div className="mb-3">
                                        <label className="form-label">Start Date</label>
                                        <input 
                                            type="date" 
                                            className="form-control" 
                                            name="startDate"
                                            value={this.state.startDate}
                                            onChange={this.handleParameterChange}
                                        />
                                    </div>
                                </div>
                                <div className="col-6">
                                    <div className="mb-3">
                                        <label className="form-label">End Date</label>
                                        <input 
                                            type="date" 
                                            className="form-control" 
                                            name="endDate"
                                            value={this.state.endDate}
                                            onChange={this.handleParameterChange}
                                        />
                                    </div>
                                </div>
                            </div>
                            
                            <div className="mb-3">
                                <label className="form-label">Buy Weekday</label>
                                <select 
                                    className="form-select" 
                                    name="buyWeekday" 
                                    value={this.state.buyWeekday}
                                    onChange={this.handleParameterChange}
                                >
                                    <option value={0}>Monday</option>
                                    <option value={1}>Tuesday</option>
                                    <option value={2}>Wednesday</option>
                                    <option value={3}>Thursday</option>
                                    <option value={4}>Friday</option>
                                </select>
                            </div>
                            
                            <div className="mb-3">
                                <label className="form-label">Fee Per Trade ($)</label>
                                <input 
                                    type="number" 
                                    className="form-control" 
                                    name="feePerTrade"
                                    value={this.state.feePerTrade}
                                    onChange={this.handleParameterChange}
                                    step="0.01"
                                    min="0"
                                />
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">Strategy Parameters</h5>
                        </div>
                        <div className="card-body">
                            <div className="mb-3">
                                <label className="form-label">Shares Per Week (DCA)</label>
                                <input 
                                    type="number" 
                                    className="form-control" 
                                    name="sharesPerWeek"
                                    value={this.state.sharesPerWeek}
                                    onChange={this.handleParameterChange}
                                    min="1"
                                    max="10000"
                                />
                            </div>
                            
                            <div className="mb-3">
                                <label className="form-label">Option Type</label>
                                <select 
                                    className="form-select" 
                                    name="optionType" 
                                    value={this.state.optionType}
                                    onChange={this.handleParameterChange}
                                >
                                    <option value="call">Call Options</option>
                                    <option value="put">Put Options</option>
                                </select>
                            </div>
                            
                            <div className="mb-3">
                                <label className="form-label">Moneyness Offset</label>
                                <select 
                                    className="form-select" 
                                    name="moneynessOffset" 
                                    value={this.state.moneynessOffset}
                                    onChange={this.handleParameterChange}
                                >
                                    <option value={-0.1}>10% ITM</option>
                                    <option value={-0.05}>5% ITM</option>
                                    <option value={0.0}>ATM</option>
                                    <option value={0.05}>5% OTM</option>
                                    <option value={0.1}>10% OTM</option>
                                </select>
                            </div>
                            
                            <div className="mb-3">
                                <label className="form-label">Min Days to Expiry</label>
                                <input 
                                    type="number" 
                                    className="form-control" 
                                    name="minDaysToExpiry"
                                    value={this.state.minDaysToExpiry}
                                    onChange={this.handleParameterChange}
                                    min="1"
                                    max="30"
                                />
                            </div>
                            
                            <div className="mb-3">
                                <label className="form-label">Contracts Per Week</label>
                                <input 
                                    type="number" 
                                    className="form-control" 
                                    name="contractsPerWeek"
                                    value={this.state.contractsPerWeek}
                                    onChange={this.handleParameterChange}
                                    min="1"
                                    max="100"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    renderResults() {
        if (!this.state.stockResult || !this.state.optionResult) {
            return <div className="text-center text-muted">No results to display</div>;
        }
        
        const stockResult = this.state.stockResult;
        const optionResult = this.state.optionResult;
        const comparison = this.state.combinedResult.comparison_metrics;
        
        // Render based on selected strategy
        if (this.state.selectedStrategy === 'stock') {
            return this.renderStockResults(stockResult);
        } else if (this.state.selectedStrategy === 'options') {
            return this.renderOptionsResults(optionResult);
        } else {
            // Default comparison view
            return this.renderComparisonResults(stockResult, optionResult, comparison);
        }
    }
    
    renderStockResults(stockResult) {
        return (
            <div className="row justify-content-center">
                <div className="col-md-8">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">📈 Stock DCA Strategy Results</h5>
                            <small className="text-muted">Dollar-Cost Averaging with weekly AAPL purchases</small>
                        </div>
                        <div className="card-body">
                            <div className="row">
                                <div className="col-md-6">
                                    <div className="metric-row">
                                        <span className="metric-label">Total Entries:</span>
                                        <span className="metric-value">{stockResult.total_entries}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Total Shares:</span>
                                        <span className="metric-value">{stockResult.total_shares.toLocaleString()}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Total Cost:</span>
                                        <span className="metric-value">${stockResult.total_cost.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="metric-row">
                                        <span className="metric-label">Market Value:</span>
                                        <span className="metric-value">${stockResult.market_value.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Unrealized P&L:</span>
                                        <span className={`metric-value ${stockResult.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                            ${stockResult.unrealized_pnl.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                        </span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Cost Basis:</span>
                                        <span className="metric-value">${stockResult.cost_basis.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    renderOptionsResults(optionResult) {
        return (
            <div className="row justify-content-center">
                <div className="col-md-8">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">📊 Weekly Options Strategy Results</h5>
                            <small className="text-muted">Weekly AAPL options trading strategy</small>
                        </div>
                        <div className="card-body">
                            <div className="row">
                                <div className="col-md-6">
                                    <div className="metric-row">
                                        <span className="metric-label">Total Trades:</span>
                                        <span className="metric-value">{optionResult.total_trades}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Win Rate:</span>
                                        <span className="metric-value">{(optionResult.win_rate * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Total P&L:</span>
                                        <span className={`metric-value ${optionResult.total_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                            ${optionResult.total_pnl.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                        </span>
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="metric-row">
                                        <span className="metric-label">Avg Win:</span>
                                        <span className="metric-value text-success">${optionResult.avg_win.toFixed(2)}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Avg Loss:</span>
                                        <span className="metric-value text-danger">${optionResult.avg_loss.toFixed(2)}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span className="metric-label">Max Win:</span>
                                        <span className="metric-value text-success">${optionResult.max_win.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    renderComparisonResults(stockResult, optionResult, comparison) {
        return (
            <div className="row">
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">📈 Stock DCA Results</h5>
                        </div>
                        <div className="card-body">
                            <div className="metric-row">
                                <span className="metric-label">Total Entries:</span>
                                <span className="metric-value">{stockResult.total_entries}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Total Shares:</span>
                                <span className="metric-value">{stockResult.total_shares.toLocaleString()}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Total Cost:</span>
                                <span className="metric-value">${stockResult.total_cost.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Market Value:</span>
                                <span className="metric-value">${stockResult.market_value.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Unrealized P&L:</span>
                                <span className={`metric-value ${stockResult.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                    ${stockResult.unrealized_pnl.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                </span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Cost Basis:</span>
                                <span className="metric-value">${stockResult.cost_basis.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">📊 Weekly Options Results</h5>
                        </div>
                        <div className="card-body">
                            <div className="metric-row">
                                <span className="metric-label">Total Trades:</span>
                                <span className="metric-value">{optionResult.total_trades}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Win Rate:</span>
                                <span className="metric-value">{(optionResult.win_rate * 100).toFixed(1)}%</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Total P&L:</span>
                                <span className={`metric-value ${optionResult.total_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                    ${optionResult.total_pnl.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                </span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Avg Win:</span>
                                <span className="metric-value text-success">${optionResult.avg_win.toFixed(2)}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Avg Loss:</span>
                                <span className="metric-value text-danger">${optionResult.avg_loss.toFixed(2)}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Max Win:</span>
                                <span className="metric-value text-success">${optionResult.max_win.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">⚖️ Comparison</h5>
                        </div>
                        <div className="card-body">
                            <div className="metric-row">
                                <span className="metric-label">Stock Return:</span>
                                <span className={`metric-value ${comparison.stock_return_pct >= 0 ? 'text-success' : 'text-danger'}`}>
                                    {comparison.stock_return_pct.toFixed(1)}%
                                </span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Combined Return:</span>
                                <span className={`metric-value ${comparison.combined_return >= 0 ? 'text-success' : 'text-danger'}`}>
                                    ${comparison.combined_return.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    renderTables() {
        if (!this.state.stockEntries.length && !this.state.optionTrades.length) {
            return <div className="text-center text-muted">No data to display</div>;
        }
        
        return (
            <div className="row">
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">Stock Entries (Last 10)</h5>
                        </div>
                        <div className="card-body">
                            <div className="table-responsive">
                                <table className="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Shares</th>
                                            <th>Price</th>
                                            <th>Cost</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {this.state.stockEntries.slice(-10).map((entry, index) => (
                                            <tr key={index}>
                                                <td>{entry.date}</td>
                                                <td>{entry.shares}</td>
                                                <td>${entry.price.toFixed(2)}</td>
                                                <td>${entry.cost.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">Option Trades (Last 10)</h5>
                        </div>
                        <div className="card-body">
                            <div className="table-responsive">
                                <table className="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Entry</th>
                                            <th>Type</th>
                                            <th>Strike</th>
                                            <th>P&L</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {this.state.optionTrades.slice(-10).map((trade, index) => (
                                            <tr key={index}>
                                                <td>{trade.entry_date}</td>
                                                <td>{trade.option_type.toUpperCase()}</td>
                                                <td>${trade.strike_price.toFixed(0)}</td>
                                                <td className={trade.pnl >= 0 ? 'text-success' : 'text-danger'}>
                                                    ${trade.pnl.toFixed(2)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    renderDiagnostics() {
        if (!this.state.diagnostics) {
            return <div className="text-center text-muted">No diagnostics available</div>;
        }
        
        const polygon = this.state.diagnostics.polygon;
        const backtest = this.state.diagnostics.backtest;
        
        return (
            <div className="row">
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">API Performance</h5>
                        </div>
                        <div className="card-body">
                            <div className="metric-row">
                                <span className="metric-label">API Calls:</span>
                                <span className="metric-value">{polygon.polygon_api_calls}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Avg Latency:</span>
                                <span className="metric-value">{polygon.polygon_avg_latency_ms.toFixed(0)}ms</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Cache Hits:</span>
                                <span className="metric-value">{polygon.cache_hits}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Cache Misses:</span>
                                <span className="metric-value">{polygon.cache_misses}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header">
                            <h5 className="card-title">Data Quality</h5>
                        </div>
                        <div className="card-body">
                            <div className="metric-row">
                                <span className="metric-label">Data Quality Score:</span>
                                <span className="metric-value">{(backtest.data_quality_score * 100).toFixed(1)}%</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Missing Entry Dates:</span>
                                <span className="metric-value">{backtest.missing_entry_dates.length}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">No Option Contracts:</span>
                                <span className="metric-value">{backtest.no_option_contracts_dates.length}</span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">Intrinsic Value Exits:</span>
                                <span className="metric-value">{backtest.fallback_intrinsic_exits}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    
    render() {
        console.log('AAPL Dashboard render called, state:', this.state);
        
        return (
            <div className="aapl-analysis-dashboard" style={{
                background: '#f8f9fa', 
                borderRadius: '12px', 
                padding: '2rem',
                minHeight: '500px'
            }}>
                {/* Header */}
                <div className="header mb-4" style={{
                    background: 'linear-gradient(135deg, #6c757d 0%, #495057 100%)', 
                    color: 'white', 
                    padding: '2rem 0', 
                    marginBottom: '2rem', 
                    borderRadius: '12px'
                }}>
                    <h1 className="text-center" style={{
                        fontSize: '2.5rem', 
                        fontWeight: '700', 
                        margin: '0'
                    }}>
                        AAPL Analysis Dashboard
                    </h1>
                    <p className="text-center" style={{
                        fontSize: '1.1rem', 
                        margin: '0.5rem 0 1rem 0', 
                        opacity: '0.9'
                    }}>
                        Compare Dollar-Cost Averaging vs Weekly Options Strategies
                    </p>
                    
                    {/* Strategy Selector */}
                    <div className="text-center">
                        <div className="d-inline-flex align-items-center" style={{
                            background: 'rgba(255,255,255,0.1)', 
                            borderRadius: '8px', 
                            padding: '0.5rem 1rem'
                        }}>
                            <label className="form-label me-3 mb-0" style={{color: 'white', fontSize: '1rem'}}>
                                View Strategy:
                            </label>
                            <select 
                                className="form-select" 
                                name="selectedStrategy"
                                value={this.state.selectedStrategy}
                                onChange={this.handleParameterChange}
                                style={{
                                    width: 'auto',
                                    minWidth: '200px',
                                    background: 'white',
                                    border: 'none'
                                }}
                            >
                                <option value="stock">📈 Stock DCA Strategy</option>
                                <option value="options">📊 Weekly Options Strategy</option>
                                <option value="comparison">⚖️ Side-by-Side Comparison</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Main Controls */}
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h3 style={{color: '#495057', margin: 0}}>Analysis Controls</h3>
                        {this.state.lastUpdated && (
                            <small className="text-muted">
                                Last updated: {new Date(this.state.lastUpdated).toLocaleString()}
                            </small>
                        )}
                    </div>
                    <div>
                        <button 
                            className="btn btn-outline-secondary me-2"
                            onClick={this.refreshData}
                            disabled={this.state.loading}
                            style={{borderColor: '#6c757d', color: '#6c757d'}}
                        >
                            Refresh Data
                        </button>
                        <button 
                            className="btn btn-primary"
                            onClick={this.runBacktest}
                            disabled={this.state.loading}
                            style={{backgroundColor: '#6c757d', borderColor: '#6c757d'}}
                        >
                            {this.state.loading ? 'Running Backtest...' : 'Run Backtest'}
                        </button>
                    </div>
                </div>
                
                {this.state.error && (
                    <div className="alert alert-danger" role="alert">
                        {this.state.error}
                    </div>
                )}
                
                <ul className="nav nav-tabs mb-4">
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${this.state.activeTab === 'controls' ? 'active' : ''}`}
                            onClick={() => this.setState({ activeTab: 'controls' })}
                        >
                            Controls
                        </button>
                    </li>
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${this.state.activeTab === 'results' ? 'active' : ''}`}
                            onClick={() => this.setState({ activeTab: 'results' })}
                        >
                            Results
                        </button>
                    </li>
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${this.state.activeTab === 'charts' ? 'active' : ''}`}
                            onClick={() => this.setState({ activeTab: 'charts' })}
                        >
                            Charts
                        </button>
                    </li>
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${this.state.activeTab === 'tables' ? 'active' : ''}`}
                            onClick={() => this.setState({ activeTab: 'tables' })}
                        >
                            Tables
                        </button>
                    </li>
                    <li className="nav-item">
                        <button 
                            className={`nav-link ${this.state.activeTab === 'diagnostics' ? 'active' : ''}`}
                            onClick={() => this.setState({ activeTab: 'diagnostics' })}
                        >
                            Diagnostics
                        </button>
                    </li>
                </ul>
                
                <div className="tab-content">
                    {this.state.activeTab === 'controls' && this.renderControls()}
                    {this.state.activeTab === 'results' && this.renderResults()}
                    {this.state.activeTab === 'charts' && this.renderChart()}
                    {this.state.activeTab === 'tables' && this.renderTables()}
                    {this.state.activeTab === 'diagnostics' && this.renderDiagnostics()}
                </div>
                
                {/* Disclaimer */}
                <div className="disclaimer mt-4 p-3 rounded text-center" style={{
                    background: '#fff3cd',
                    border: '1px solid #ffeaa7',
                    color: '#856404'
                }}>
                    <strong>Disclaimer:</strong> This analysis is for educational purposes only and does not constitute investment advice. 
                    Past performance does not guarantee future results. Daily closing prices are used for fills (no intraday data). 
                    Option expiry data may fall back to intrinsic value calculations when market data is unavailable.
                </div>
                
                <style jsx>{`
                    .aapl-analysis-dashboard {
                        background: #f8f9fa;
                        color: #495057;
                        font-family: 'Inter', 'Segoe UI', sans-serif;
                    }
                    
                    .metric-row {
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 8px;
                        padding: 8px 0;
                        border-bottom: 1px solid #e9ecef;
                    }
                    
                    .metric-label {
                        font-weight: 500;
                        color: #6c757d;
                    }
                    
                    .metric-value {
                        font-weight: 600;
                        text-align: right;
                        color: #495057;
                    }
                    
                    .chart-container {
                        height: 400px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: white;
                        border-radius: 8px;
                        border: 1px solid #e9ecef;
                        color: #6c757d;
                    }
                    
                    .nav-tabs .nav-link {
                        color: #6c757d;
                        border: none;
                        border-bottom: 2px solid transparent;
                        background: white;
                        margin-right: 2px;
                    }
                    
                    .nav-tabs .nav-link.active {
                        color: #495057;
                        border-bottom-color: #6c757d;
                        background: white;
                    }
                    
                    .nav-tabs .nav-link:hover {
                        color: #495057;
                        border-bottom-color: #adb5bd;
                        background: #f8f9fa;
                    }
                    
                    .table th {
                        font-weight: 600;
                        color: #495057;
                        border-bottom: 2px solid #dee2e6;
                        background: #f8f9fa;
                    }
                    
                    .btn-primary {
                        background-color: #6c757d;
                        border-color: #6c757d;
                        color: white;
                    }
                    
                    .btn-primary:hover {
                        background-color: #5a6268;
                        border-color: #545b62;
                    }
                    
                    .btn-primary:disabled {
                        background-color: #adb5bd;
                        border-color: #adb5bd;
                    }
                    
                    .card {
                        background: white;
                        border: 1px solid #e9ecef;
                        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
                    }
                    
                    .card-header {
                        background: #f8f9fa;
                        border-bottom: 1px solid #e9ecef;
                        color: #495057;
                    }
                    
                    .form-control, .form-select {
                        border-color: #ced4da;
                        color: #495057;
                    }
                    
                    .form-control:focus, .form-select:focus {
                        border-color: #6c757d;
                        box-shadow: 0 0 0 0.2rem rgba(108, 117, 125, 0.25);
                    }
                    
                    .alert-danger {
                        background-color: #f8d7da;
                        border-color: #f5c6cb;
                        color: #721c24;
                    }
                `}</style>
            </div>
        );
    }
}

        // Export for use in other components
        window.AAPLAnalysisDashboard = AAPLAnalysisDashboard;
        console.log('✅ AAPLAnalysisDashboard component exported to window object');
    }
    
    // Start trying to define the component
    defineComponent();
})();
