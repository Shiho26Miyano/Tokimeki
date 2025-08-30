console.log('FutureQuant Dashboard loaded - Distributional Futures Trading Platform - Version 20250117');

// Block any FutureQuant API calls to prevent 404 errors
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && url.includes('/api/v1/futurequant/')) {
        console.warn('BLOCKED FutureQuant API call to:', url);
        console.trace('API call blocked from:');
        return Promise.resolve(new Response(JSON.stringify({ 
            success: false, 
            error: 'API calls blocked - using mock data' 
        }), { status: 200 }));
    }
    return originalFetch.apply(this, args);
};

console.log('FutureQuant API calls are now blocked - using mock data only');

class FutureQuantDashboard {
    constructor() {
        console.log('FutureQuantDashboard constructor called');
        
        this.currentSymbol = 'ES=F';
        this.currentTimeframe = '1d';
        this.activeSession = null;
        this.charts = {};
        this.dataCache = {};
        
        console.log('Dashboard properties initialized');
        
        // Mock data for demonstration
        this.mockSymbols = [
            { ticker: 'ES=F', name: 'E-mini S&P 500', price: 4850.25, change: 12.50, changePercent: 0.26, volume: 1250000 },
            { ticker: 'NQ=F', name: 'E-mini NASDAQ', price: 16850.75, change: -45.25, changePercent: -0.27, volume: 890000 },
            { ticker: 'YM=F', name: 'E-mini Dow', price: 38500.50, change: 125.00, changePercent: 0.33, volume: 450000 },
            { ticker: 'RTY=F', name: 'E-mini Russell', price: 2150.25, change: 8.75, changePercent: 0.41, volume: 320000 },
            { ticker: 'CL=F', name: 'Crude Oil', price: 78.45, change: -1.20, changePercent: -1.51, volume: 280000 },
            { ticker: 'GC=F', name: 'Gold', price: 2050.80, change: 15.60, changePercent: 0.77, volume: 180000 }
        ];
        
        this.mockStrategies = [
            { id: 1, name: 'Conservative Momentum', description: 'Low-risk momentum strategy with tight stops', risk: 'Low', expectedReturn: '8-12%', maxDrawdown: '5%' },
            { id: 2, name: 'Moderate Trend Following', description: 'Balanced trend following with moderate risk', risk: 'Medium', expectedReturn: '15-20%', maxDrawdown: '12%' },
            { id: 3, name: 'Aggressive Mean Reversion', description: 'High-risk mean reversion with wide stops', risk: 'High', expectedReturn: '25-35%', maxDrawdown: '20%' },
            { id: 4, name: 'Volatility Breakout', description: 'Volatility-based breakout strategy', risk: 'Medium-High', expectedReturn: '18-25%', maxDrawdown: '15%' },
            { id: 5, name: 'Statistical Arbitrage', description: 'Pairs trading with statistical edge', risk: 'Low-Medium', expectedReturn: '10-15%', maxDrawdown: '8%' }
        ];
        
        console.log('Mock strategies initialized:', this.mockStrategies);
        
        this.mockModels = [
            { id: 1, name: 'Transformer Encoder (FQT-lite)', description: 'Lightweight transformer for quick predictions', accuracy: '78%', trainingTime: '2-4 hours' },
            { id: 2, name: 'Quantile Regression', description: 'Distributional forecasting model', accuracy: '82%', trainingTime: '1-2 hours' },
            { id: 3, name: 'Random Forest Quantiles', description: 'Ensemble method for robust predictions', accuracy: '75%', trainingTime: '30-60 min' },
            { id: 4, name: 'Neural Network', description: 'Deep learning for complex patterns', accuracy: '85%', trainingTime: '4-8 hours' },
            { id: 5, name: 'Gradient Boosting', description: 'Advanced boosting for high accuracy', accuracy: '80%', trainingTime: '2-3 hours' }
        ];
        
        this.init();
    }

    init() {
        console.log('Initializing FutureQuant Dashboard...');
        console.log('Current symbol:', this.currentSymbol);
        console.log('Mock symbols available:', this.mockSymbols.length);
        console.log('Mock symbols:', this.mockSymbols.map(s => s.ticker));
        
        // Check if elements are accessible
        console.log('Checking element accessibility...');
        console.log('Symbol select:', document.getElementById('fq-symbol-select'));
        console.log('Price chart:', document.getElementById('fq-price-chart'));
        console.log('Distribution chart:', document.getElementById('fq-distribution-chart'));
        console.log('Performance chart:', document.getElementById('fq-performance-chart'));
        
        this.setupEventListeners();
        this.loadInitialData();
        this.initializeCharts();
        // Temporarily disable data refresh to debug
        // this.startDataRefresh();
        
        // Test initialization
        setTimeout(() => {
            console.log('Dashboard initialization complete');
            console.log('Charts initialized:', Object.keys(this.charts));
            console.log('Current symbol data:', this.mockSymbols.find(s => s.ticker === this.currentSymbol));
            console.log('Chart objects:', this.charts);
            
                    // Test button accessibility
        const trainBtn = document.getElementById('fq-train-model-btn');
        console.log('Train model button accessible:', !!trainBtn);
        if (trainBtn) {
            console.log('Train button text:', trainBtn.textContent);
            console.log('Train button onclick:', trainBtn.onclick);
        }
        
        // Test strategy elements
        const strategySelect = document.getElementById('fq-strategy-select');
        const strategyDetails = document.getElementById('fq-strategy-details');
        console.log('Strategy select accessible:', !!strategySelect);
        console.log('Strategy details accessible:', !!strategyDetails);
        
        // Test strategy loading
        this.loadStrategies();
        console.log('Strategies loaded, checking if populated...');
        if (strategySelect) {
            console.log('Strategy select options count:', strategySelect.options.length);
            console.log('Strategy select value:', strategySelect.value);
        }
        }, 2000);
    }

    setupEventListeners() {
        // Symbol selector
        const symbolSelect = document.getElementById('fq-symbol-select');
        if (symbolSelect) {
            symbolSelect.addEventListener('change', (e) => {
                this.currentSymbol = e.target.value;
                this.loadSymbolData();
            });
        }

        // Timeframe selector
        const timeframeSelect = document.getElementById('fq-timeframe-select');
        if (timeframeSelect) {
            timeframeSelect.addEventListener('change', (e) => {
                this.currentTimeframe = e.target.value;
                this.loadSymbolData();
            });
        }

        // Strategy selector
        const strategySelect = document.getElementById('fq-strategy-select');
        if (strategySelect) {
            console.log('Strategy select found, adding change event listener');
            
            // Add click handler for debugging
            strategySelect.addEventListener('click', (e) => {
                console.log('Strategy select clicked!');
                console.log('Current options count:', e.target.options.length);
                console.log('Current HTML:', e.target.innerHTML);
            });
            
            // Add change handler
            strategySelect.addEventListener('change', (e) => {
                console.log('Strategy changed to:', e.target.value);
                this.loadStrategyData(e.target.value);
            });
            
            // Add focus handler
            strategySelect.addEventListener('focus', (e) => {
                console.log('Strategy select focused');
                console.log('Options available:', e.target.options.length);
            });
        } else {
            console.error('Strategy select element not found during event listener setup');
        }
        
        // Train button
        const trainBtn = document.getElementById('fq-train-model-btn');
        if (trainBtn) {
            trainBtn.addEventListener('click', () => {
                this.showTrainingInterface();
            });
        }
        
        // Trade button
        const tradeBtn = document.getElementById('fq-start-paper-trading-btn');
        if (tradeBtn) {
            console.log('Trade button found, adding event listener');
            tradeBtn.addEventListener('click', () => {
                console.log('Trade button clicked!');
                this.showTradingInterface();
            });
        } else {
            console.error('Trade button not found!');
        }

        // Model training
        const trainModelBtn = document.getElementById('fq-train-model-btn');
        if (trainModelBtn) {
            console.log('Train model button found, adding event listener');
            trainModelBtn.addEventListener('click', () => {
                console.log('Train model button clicked');
                this.showModelTrainingModal();
            });
        } else {
            console.error('Train model button not found');
        }

        // Backtest button
        const backtestBtn = document.getElementById('fq-backtest-btn');
        if (backtestBtn) {
            backtestBtn.addEventListener('click', () => this.runBacktest());
        }

        // Paper trading - using the showTradingInterface method instead
        // const startPaperTradingBtn = document.getElementById('fq-start-paper-trading-btn');
        // if (startPaperTradingBtn) {
        //     startPaperTradingBtn.addEventListener('click', () => this.startPaperTrading());
        // }

        const stopPaperTradingBtn = document.getElementById('fq-stop-paper-trading-btn');
        if (stopPaperTradingBtn) {
            stopPaperTradingBtn.addEventListener('click', () => this.stopPaperTrading());
        }

        // Data ingestion
        const ingestDataBtn = document.getElementById('fq-ingest-data-btn');
        if (ingestDataBtn) {
            ingestDataBtn.addEventListener('click', () => this.ingestData());
        }

        // Feature computation
        const computeFeaturesBtn = document.getElementById('fq-compute-features-btn');
        if (computeFeaturesBtn) {
            computeFeaturesBtn.addEventListener('click', () => this.computeFeatures());
        }
    }

    async loadInitialData() {
        try {
            // Load available symbols
            this.loadSymbols();
            
            // Load strategies
            this.loadStrategies();
            
            // Load models
            this.loadModels();
            
            // Load recent backtests
            this.loadRecentBacktests();
            
            // Load paper trading sessions
            this.loadPaperTradingSessions();
            
            // Load recent signals
            this.loadRecentSignals();
            
            // Load job statuses
            this.loadJobStatuses();
            
            // Generate initial chart data
            this.generateInitialChartData();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data', 'error');
        }
    }

    loadSymbols() {
        console.log('Loading symbols...');
        const symbolSelect = document.getElementById('fq-symbol-select');
        console.log('Symbol select element:', symbolSelect);
        
        if (symbolSelect) {
            symbolSelect.innerHTML = '<option value="">Select Symbol</option>';
            this.mockSymbols.forEach(symbol => {
                symbolSelect.innerHTML += `<option value="${symbol.ticker}">${symbol.ticker} - ${symbol.name}</option>`;
            });
            
            console.log('Symbols loaded into select:', this.mockSymbols.length);
            
            // Set default symbol
            if (this.mockSymbols.length > 0) {
                this.currentSymbol = this.mockSymbols[0].ticker;
                symbolSelect.value = this.currentSymbol;
                console.log('Default symbol set to:', this.currentSymbol);
                
                this.updateMarketDataDisplay(this.mockSymbols[0]);
                
                // Generate initial price data for the default symbol
                setTimeout(() => {
                    this.generateMockPriceData();
                }, 200);
            }
        } else {
            console.error('Symbol select element not found!');
        }
    }

    loadStrategies() {
        console.log('Loading strategies...');
        console.log('Available mock strategies:', this.mockStrategies);
        
        const strategySelect = document.getElementById('fq-strategy-select');
        console.log('Strategy select element:', strategySelect);
        
        if (strategySelect) {
            // Clear existing options and add default
            strategySelect.innerHTML = '<option value="">Aggressive Mean Reversion</option>';
            this.mockStrategies.forEach(strategy => {
                const option = `<option value="${strategy.id}">${strategy.name}</option>`;
                strategySelect.innerHTML += option;
                console.log('Added strategy option:', option);
            });
            console.log('Strategies loaded into select:', this.mockStrategies.length);
            console.log('Strategy select HTML:', strategySelect.innerHTML);
            
            // Verify the options were added
            console.log('Final strategy select options count:', strategySelect.options.length);
            for (let i = 0; i < strategySelect.options.length; i++) {
                console.log(`Option ${i}:`, strategySelect.options[i].text, 'Value:', strategySelect.options[i].value);
            }
            
            // Automatically select and display the first strategy (Aggressive Mean Reversion)
            if (this.mockStrategies.length > 0) {
                const firstStrategy = this.mockStrategies[0];
                strategySelect.value = firstStrategy.id;
                console.log('Auto-selecting strategy:', firstStrategy.name);
                
                // Trigger the change event to load strategy details
                this.loadStrategyData(firstStrategy.id);
            }
        } else {
            console.error('Strategy select element not found!');
        }
    }

    loadModels() {
        this.updateModelTypesDisplay(this.mockModels);
    }

    loadRecentBacktests() {
        const mockConfig = {
            initial_capital: 100000,
            commission_rate: 0.0002,
            max_leverage: 2.0,
            max_drawdown: 0.20,
            daily_loss_limit: 0.03,
            position_limit: 0.25
        };
        this.updateBacktestConfigDisplay(mockConfig);
    }

    loadPaperTradingSessions() {
        const mockSessions = [
            {
                session_id: 'session_1',
                strategy_name: 'Moderate Trend Following',
                start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                current_capital: 105000,
                current_return: 5.0
            }
        ];
        this.updatePaperTradingDisplay(mockSessions);
    }

    loadRecentSignals() {
        const mockSignals = [
            { symbol: 'ES=F', side: 'long', confidence: 0.78, timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
            { symbol: 'NQ=F', side: 'short', confidence: 0.82, timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString() },
            { symbol: 'YM=F', side: 'long', confidence: 0.71, timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString() }
        ];
        this.updateSignalsDisplay(mockSignals);
    }

    loadJobStatuses() {
        const mockJobs = [
            { id: 1, type: 'data_ingestion', status: 'completed', progress: 100 },
            { id: 2, type: 'feature_computation', status: 'running', progress: 65 },
            { id: 3, type: 'model_training', status: 'queued', progress: 0 }
        ];
        
        this.updateJobStatusDisplay(mockJobs);
    }

    async loadSymbolData() {
        if (!this.currentSymbol) return;
        
        console.log('Loading symbol data for:', this.currentSymbol);
        
        try {
            // Find symbol data
            const symbolData = this.mockSymbols.find(s => s.ticker === this.currentSymbol);
            if (symbolData) {
                console.log('Found symbol data:', symbolData);
                this.updateMarketDataDisplay(symbolData);
                this.generateMockPriceData();
            } else {
                console.log('No symbol data found for:', this.currentSymbol);
            }
        } catch (error) {
            console.error('Error loading symbol data:', error);
        }
    }

    async loadStrategyData(strategyId) {
        console.log('Loading strategy data for ID:', strategyId);
        if (!strategyId) {
            console.log('No strategy ID provided, returning');
            return;
        }
        
        try {
            const strategy = this.mockStrategies.find(s => s.id == strategyId);
            console.log('Found strategy:', strategy);
            if (strategy) {
                this.updateStrategyDisplay(strategy);
            } else {
                console.warn('Strategy not found for ID:', strategyId);
            }
        } catch (error) {
            console.error('Error loading strategy data:', error);
        }
    }
    
    updateStrategyDisplay(strategy) {
        console.log('Updating strategy display for:', strategy.name);
        const strategyDetails = document.getElementById('fq-strategy-details');
        
        if (strategyDetails) {
            // Create detailed strategy information
            let strategyInfo = '';
            
            if (strategy.name === 'Aggressive Mean Reversion') {
                strategyInfo = `
                    <div class="alert alert-info mb-2">
                        <h6 class="text-primary mb-2"><i class="fas fa-chart-line"></i> ${strategy.name}</h6>
                        <p class="small mb-2"><strong>Strategy Type:</strong> Mean Reversion with High Risk Tolerance</p>
                        <p class="small mb-2"><strong>Best For:</strong> Volatile markets, short-term trades, experienced traders</p>
                        <p class="small mb-2"><strong>Risk Level:</strong> <span class="badge bg-danger">High</span></p>
                        <p class="small mb-0"><strong>Timeframe:</strong> 5 minutes to 1 hour</p>
                    </div>
                    <div class="small text-muted mb-2">
                        <strong>How it works:</strong> Identifies when prices move too far from their average and bets they'll return to normal levels. 
                        Uses aggressive position sizing for maximum profit potential.
                    </div>
                    <div class="alert alert-warning mb-0 py-2 small">
                        <i class="fas fa-graduation-cap"></i> <strong>Research:</strong> Based on 
                        <a href="https://arxiv.org/abs/2505.05595" target="_blank" class="text-decoration-none">
                            FutureQuant Transformer
                        </a> 
                        achieving 0.1193% avg gain per 30-min trade.
                    </div>
                `;
            } else {
                strategyInfo = `
                    <div class="alert alert-secondary mb-2">
                        <h6 class="text-secondary mb-2"><i class="fas fa-chart-line"></i> ${strategy.name}</h6>
                        <p class="small mb-0">Strategy details will be displayed here.</p>
                    </div>
                `;
            }
            
            strategyDetails.innerHTML = strategyInfo;
            console.log('Strategy display updated');
        } else {
            console.error('Strategy details element not found');
        }
    }
    
    showTrainingInterface() {
        console.log('Showing training interface...');
        
        // Create and show training modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'trainingModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-brain"></i> AI Model Training
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Training Configuration</h6>
                                <div class="mb-3">
                                    <label class="form-label">Model Type</label>
                                    <select class="form-select">
                                        <option>Neural Network</option>
                                        <option>Random Forest</option>
                                        <option>Gradient Boosting</option>
                                        <option>LSTM</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Training Period</label>
                                    <select class="form-select">
                                        <option>Last 6 months</option>
                                        <option>Last 1 year</option>
                                        <option>Last 2 years</option>
                                        <option>All available data</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Features</label>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" checked>
                                        <label class="form-check-label">Price indicators</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" checked>
                                        <label class="form-check-label">Volume indicators</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" checked>
                                        <label class="form-check-label">Volatility indicators</label>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h6>Training Progress</h6>
                                <div class="text-center p-4">
                                    <div class="spinner-border text-primary mb-3" role="status">
                                        <span class="visually-hidden">Training...</span>
                                    </div>
                                    <h6>Training in Progress...</h6>
                                    <div class="progress mb-3">
                                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                             style="width: 45%">45%</div>
                                    </div>
                                    <p class="text-muted small">Epoch 23/50 - Loss: 0.0234</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="startTrainingBRPC()">Start Training</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show the modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Clean up when modal is hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    showTradingInterface() {
        console.log('Showing trading interface...');
        
        // Create and show trading modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'tradingModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-play"></i> Paper Trading Session
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Account Balance</h6>
                                        <h4 class="text-success">$100,000</h4>
                                        <small class="text-muted">Virtual Money</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Current P&L</h6>
                                        <h4 class="text-primary">+$2,450</h4>
                                        <small class="text-muted">Today's Gain</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="card-body">
                                        <h6 class="text-muted">Open Positions</h6>
                                        <h4 class="text-info">3</h4>
                                        <small class="text-muted">Active Trades</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Win Rate</h6>
                                        <h4 class="text-warning">68%</h4>
                                        <small class="text-muted">Successful Trades</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <h6>Live Trading Chart</h6>
                                <div class="border rounded p-3" style="height: 300px; background: #f8f9fa;">
                                    <div class="text-center text-muted pt-5">
                                        <i class="fas fa-chart-line fa-3x mb-3"></i>
                                        <p>Real-time price chart with trade signals</p>
                                        <small>Chart will show live data and entry/exit points</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <h6>Recent Trades</h6>
                                <div class="list-group">
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>ES Long</strong><br>
                                            <small class="text-muted">Entry: $4,250</small>
                                        </div>
                                        <span class="badge bg-success">+$125</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>NQ Short</strong><br>
                                            <small class="text-muted">Entry: $15,800</small>
                                        </div>
                                        <span class="badge bg-danger">-$85</span>
                                    </div>
                                    <div class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>YM Long</strong><br>
                                            <small class="text-body">
                                            <small class="text-muted">Entry: $33,450</small>
                                        </div>
                                        <span class="badge bg-success">+$210</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger">
                            <i class="fas fa-stop"></i> Stop Trading
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show the modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Clean up when modal is hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    generateMockPriceData() {
        console.log('Generating mock price data for symbol:', this.currentSymbol);
        
        // Generate mock price data for charts
        const days = 30;
        const basePrice = this.mockSymbols.find(s => s.ticker === this.currentSymbol)?.price || 100;
        console.log('Base price:', basePrice);
        
        const mockData = [];
        
        // Create a more realistic price trend
        let currentPrice = basePrice;
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
            
            // Add some trend and volatility
            const trend = Math.sin(i * 0.1) * 0.005; // Small trend component
            const volatility = (Math.random() - 0.5) * 0.015; // ±0.75% daily change
            currentPrice = currentPrice * (1 + trend + volatility);
            
            const open = currentPrice * (1 + (Math.random() - 0.5) * 0.008);
            const high = Math.max(open, currentPrice) * (1 + Math.random() * 0.005);
            const low = Math.min(open, currentPrice) * (1 - Math.random() * 0.005);
            const close = currentPrice;
            
            mockData.push({
                timestamp: date.toISOString().split('T')[0],
                open: open,
                high: high,
                low: low,
                close: close,
                volume: Math.floor(Math.random() * 1000000) + 500000
            });
        }
        
        console.log('Generated mock data:', mockData.length, 'data points');
        console.log('First few data points:', mockData.slice(0, 3));
        
        this.updatePriceChart(mockData);
        this.updateDistributionChart(this.generateMockDistribution());
    }

    generateMockDistribution() {
        // Generate more realistic distribution data
        return {
            q10: -3.2,
            q25: -1.8,
            q50: 0.5,
            q75: 2.1,
            q90: 4.2
        };
    }
    
    generateInitialChartData() {
        // Generate initial data for all charts
        if (this.currentSymbol) {
            this.generateMockPriceData();
        }
        
        // Generate performance data
        this.generateMockPerformanceData();
        
        // Generate distribution data
        const distributionData = this.generateMockDistribution();
        this.updateDistributionChart(distributionData);
    }

    initializeCharts() {
        console.log('Initializing charts...');
        console.log('Chart.js available:', typeof Chart !== 'undefined');
        
        // Check if elements are accessible before initializing
        const priceChartElement = document.getElementById('fq-price-chart');
        const distributionChartElement = document.getElementById('fq-distribution-chart');
        const performanceChartElement = document.getElementById('fq-performance-chart');
        
        console.log('Chart elements found:', {
            price: priceChartElement,
            distribution: distributionChartElement,
            performance: performanceChartElement
        });
        
        if (!priceChartElement || !distributionChartElement || !performanceChartElement) {
            console.error('Some chart elements not found, cannot initialize charts');
            return;
        }
        
        // Initialize price chart
        this.initializePriceChart();
        
        // Initialize performance chart
        this.initializePerformanceChart();
        
        // Initialize distribution chart
        this.initializeDistributionChart();
        
        // Force chart resize after a short delay
        setTimeout(() => {
            this.forceChartResize();
        }, 100);
        
        // Generate initial data for charts after initialization
        setTimeout(() => {
            this.generateInitialChartData();
        }, 300);
        
        // Test chart functionality after a longer delay
        setTimeout(() => {
            console.log('Testing chart functionality...');
            console.log('Charts object:', this.charts);
            console.log('Price chart:', this.charts.price);
            if (this.charts.price) {
                console.log('Price chart data:', this.charts.price.data);
                
                // Force add some test data if chart is empty
                if (this.charts.price.data.labels.length === 0) {
                    console.log('Chart is empty, adding test data...');
                    this.charts.price.data.labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May'];
                    this.charts.price.data.datasets[0].data = [100, 120, 115, 130, 125];
                    this.charts.price.update();
                    console.log('Test data added to price chart');
                }
            }
        }, 1000);
    }
    
    forceChartResize() {
        // Force all charts to maintain their dimensions
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }

    initializePriceChart() {
        const chartContainer = document.getElementById('fq-price-chart');
        if (!chartContainer) {
            console.log('Price chart container not found');
            return;
        }
        
        console.log('Initializing price chart...');
        console.log('Chart container found:', chartContainer);
        console.log('Chart container dimensions:', chartContainer.offsetWidth, 'x', chartContainer.offsetHeight);
        
        // Force fixed dimensions
        chartContainer.style.height = '300px';
        chartContainer.style.width = '100%';
        chartContainer.style.maxHeight = '300px';
        chartContainer.style.minHeight = '300px';
        
        // Create a simple price chart using Chart.js
        const ctx = chartContainer.getContext('2d');
        console.log('Canvas context:', ctx);
        
        try {
            this.charts.price = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Price',
                        data: [],
                        borderColor: '#183153',
                        backgroundColor: 'rgba(24, 49, 83, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Price Chart'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });
            console.log('Price chart created successfully');
        } catch (error) {
            console.error('Error creating price chart:', error);
        }
    }

    initializePerformanceChart() {
        const chartContainer = document.getElementById('fq-performance-chart');
        if (!chartContainer) return;
        
        // Force fixed dimensions
        chartContainer.style.height = '250px';
        chartContainer.style.width = '100%';
        chartContainer.style.maxHeight = '250px';
        chartContainer.style.minHeight = '250px';
        
        const ctx = chartContainer.getContext('2d');
        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Performance Chart'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
        
        // Generate mock performance data
        this.generateMockPerformanceData();
    }

    initializeDistributionChart() {
        const chartContainer = document.getElementById('fq-distribution-chart');
        if (!chartContainer) return;
        
        // Force fixed dimensions
        chartContainer.style.height = '300px';
        chartContainer.style.width = '100%';
        chartContainer.style.maxHeight = '300px';
        chartContainer.style.minHeight = '300px';
        
        const ctx = chartContainer.getContext('2d');
        this.charts.distribution = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Q10', 'Q25', 'Q50', 'Q75', 'Q90'],
                datasets: [{
                    label: 'Return Distribution',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(54, 162, 235, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Return Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    generateMockPerformanceData() {
        const days = 20;
        const mockData = [];
        let currentValue = 100000;
        
        for (let i = 0; i < days; i++) {
            const date = new Date(Date.now() - (days - 1 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            
            // Create a more realistic performance trend
            const dailyReturn = (Math.random() - 0.48) * 0.02; // Slightly positive bias
            const trend = Math.sin(i * 0.15) * 0.005; // Small trend component
            currentValue = currentValue * (1 + dailyReturn + trend);
            
            mockData.push({
                date: date,
                value: currentValue
            });
        }
        
        this.updatePerformanceChart(mockData);
    }

    updatePriceChart(data) {
        if (!this.charts.price || !data) {
            console.log('Cannot update price chart:', !this.charts.price ? 'chart not initialized' : 'no data');
            return;
        }
        
        console.log('Updating price chart with data:', data.length, 'points');
        console.log('Sample data:', data.slice(0, 3));
        
        const chart = this.charts.price;
        chart.data.labels = data.map(d => d.timestamp);
        chart.data.datasets[0].data = data.map(d => d.close);
        chart.update();
        
        console.log('Price chart updated with labels:', chart.data.labels.length, 'and data:', chart.data.datasets[0].data.length);
    }

    updatePerformanceChart(data) {
        if (!this.charts.performance || !data) return;
        
        const chart = this.charts.performance;
        chart.data.labels = data.map(d => d.date);
        chart.data.datasets[0].data = data.map(d => d.value);
        chart.update();
    }

    updateDistributionChart(data) {
        if (!this.charts.distribution || !data) return;
        
        const chart = this.charts.distribution;
        chart.data.datasets[0].data = [
            data.q10 || 0,
            data.q25 || 0,
            data.q50 || 0,
            data.q75 || 0,
            data.q90 || 0
        ];
        chart.update();
    }

    updateMarketDataDisplay(symbolData) {
        if (!symbolData) return;
        
        // Update price display
        const priceElement = document.getElementById('fq-current-price');
        if (priceElement) {
            priceElement.textContent = `$${symbolData.price.toFixed(2)}`;
        }
        
        // Update change display
        const changeElement = document.getElementById('fq-price-change');
        if (changeElement) {
            const change = symbolData.change;
            const changePercent = symbolData.changePercent;
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
            changeElement.className = change >= 0 ? 'text-success' : 'text-danger';
        }
        
        // Update volume display
        const volumeElement = document.getElementById('fq-volume');
        if (volumeElement) {
            volumeElement.textContent = symbolData.volume.toLocaleString();
        }
    }

    updateModelTypesDisplay(modelTypes) {
        const container = document.getElementById('fq-model-types');
        if (!container) return;
        
        container.innerHTML = '';
        modelTypes.forEach(type => {
            const typeCard = document.createElement('div');
            typeCard.className = 'col-md-6 col-lg-4 mb-3';
            typeCard.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">${type.name}</h6>
                        <p class="card-text small text-muted">${type.description}</p>
                        <div class="small text-muted mb-2">
                            <strong>Accuracy:</strong> ${type.accuracy}<br>
                            <strong>Training Time:</strong> ${type.trainingTime}
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="futurequantDashboard.trainModel('${type.id}')">
                            Train Model
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(typeCard);
        });
    }

    updateBacktestConfigDisplay(config) {
        const container = document.getElementById('fq-backtest-config');
        if (!container) return;
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Backtest Configuration</h6>
                    <ul class="list-unstyled small">
                        <li><strong>Initial Capital:</strong> $${config.initial_capital?.toLocaleString() || '100,000'}</li>
                        <li><strong>Commission:</strong> ${config.commission_rate ? (config.commission_rate * 10000).toFixed(1) + ' bps' : '2.0 bps'}</li>
                        <li><strong>Max Leverage:</strong> ${config.max_leverage || '2.0'}x</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Risk Parameters</h6>
                    <ul class="list-unstyled small">
                        <li><strong>Max Drawdown:</strong> ${config.max_drawdown ? (config.max_drawdown * 100).toFixed(1) + '%' : '20%'}</li>
                        <li><strong>Daily Loss Limit:</strong> ${config.daily_loss_limit ? (config.daily_loss_limit * 100).toFixed(1) + '%' : '3%'}</li>
                        <li><strong>Position Limit:</strong> ${config.position_limit ? (config.position_limit * 100).toFixed(1) + '%' : '25%'}</li>
                    </ul>
                </div>
            </div>
        `;
    }

    updatePaperTradingDisplay(sessions) {
        const container = document.getElementById('fq-paper-trading-sessions');
        if (!container) return;
        
        if (!sessions || sessions.length === 0) {
            container.innerHTML = '<p class="text-muted">No active paper trading sessions</p>';
            return;
        }
        
        container.innerHTML = '';
        sessions.forEach(session => {
            const sessionCard = document.createElement('div');
            sessionCard.className = 'col-md-6 mb-3';
            sessionCard.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">${session.strategy_name}</h6>
                        <p class="small text-muted">Started: ${new Date(session.start_time).toLocaleString()}</p>
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Capital</small><br>
                                <strong>$${session.current_capital.toLocaleString()}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Return</small><br>
                                <strong class="${session.current_return >= 0 ? 'text-success' : 'text-danger'}">
                                    ${session.current_return >= 0 ? '+' : ''}${session.current_return.toFixed(2)}%
                                </strong>
                            </div>
                        </div>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-danger" onclick="futurequantDashboard.stopPaperTrading('${session.session_id}')">
                                Stop Session
                            </button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(sessionCard);
        });
    }

    updateSignalsDisplay(signals) {
        const container = document.getElementById('fq-recent-signals');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent signals</p>';
            return;
        }
        
        container.innerHTML = '';
        signals.slice(0, 5).forEach(signal => {
            const signalCard = document.createElement('div');
            signalCard.className = 'col-md-6 mb-2';
            signalCard.innerHTML = `
                <div class="card">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-${signal.side === 'long' ? 'success' : 'danger'}">${signal.side.toUpperCase()}</span>
                            <small class="text-muted">${new Date(signal.timestamp).toLocaleDateString()}</small>
                        </div>
                        <div class="mt-1">
                            <strong>${signal.symbol}</strong><br>
                            <small class="text-muted">Confidence: ${(signal.confidence * 100).toFixed(1)}%</small>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(signalCard);
        });
    }

    updateJobStatusDisplay(jobs) {
        const container = document.getElementById('fq-job-statuses');
        if (!container) return;
        
        container.innerHTML = '';
        jobs.forEach(job => {
            const jobCard = document.createElement('div');
            jobCard.className = 'col-md-6 mb-2';
            jobCard.innerHTML = `
                <div class="card">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-${this.getJobStatusColor(job.status)}">${job.status}</span>
                            <small class="text-muted">${job.type.replace('_', ' ').toUpperCase()}</small>
                        </div>
                        <div class="mt-1">
                            <div class="progress" style="height: 6px;">
                                <div class="progress-bar" style="width: ${job.progress}%"></div>
                            </div>
                            <small class="text-muted">${job.progress}% complete</small>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(jobCard);
        });
    }

    getJobStatusColor(status) {
        switch (status) {
            case 'completed': return 'success';
            case 'running': return 'primary';
            case 'queued': return 'warning';
            case 'failed': return 'danger';
            default: return 'secondary';
        }
    }

    updateStrategyDisplay(strategy) {
        console.log('Updating strategy display for:', strategy);
        const container = document.getElementById('fq-strategy-details');
        console.log('Strategy details container:', container);
        
        if (!container) {
            console.error('Strategy details container not found');
            return;
        }
        
        container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">${strategy.name}</h6>
                    <p class="card-text small">${strategy.description}</p>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Risk Profile</h6>
                            <ul class="list-unstyled small">
                                <li><strong>Risk Level:</strong> <span class="badge bg-${this.getRiskColor(strategy.risk)}">${strategy.risk}</span></li>
                                <li><strong>Expected Return:</strong> ${strategy.expectedReturn}</li>
                                <li><strong>Max Drawdown:</strong> ${strategy.maxDrawdown}</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Strategy Features</h6>
                            <ul class="list-unstyled small">
                                <li><strong>Position Sizing:</strong> Kelly Criterion</li>
                                <li><strong>Stop Loss:</strong> Dynamic ATR-based</li>
                                <li><strong>Take Profit:</strong> Risk-reward 2:1</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getRiskColor(risk) {
        switch (risk.toLowerCase()) {
            case 'low': return 'success';
            case 'medium': return 'warning';
            case 'high': return 'danger';
            default: return 'secondary';
        }
    }

    showModelTrainingModal() {
        try {
            console.log('Showing model training modal...');
            
            // Check if Bootstrap is available
            if (typeof bootstrap === 'undefined') {
                console.warn('Bootstrap not available, using fallback modal');
                this.createFallbackModal();
                return;
            }
            
            // Remove existing modal if it exists
            const existingModal = document.getElementById('modelTrainingModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Create and show modal for model training
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'modelTrainingModal';
            modal.style.zIndex = '9999';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Train Distributional Model</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="modelTrainingForm">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Model Type</label>
                                            <select class="form-select" id="modelType" name="modelType">
                                                <option value="transformer">Transformer Encoder (FQT-lite)</option>
                                                <option value="quantile_regression">Quantile Regression</option>
                                                <option value="random_forest">Random Forest Quantiles</option>
                                                <option value="neural_network">Neural Network</option>
                                                <option value="gradient_boosting">Gradient Boosting</option>
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Symbols</label>
                                            <select class="form-select" id="modelSymbols" name="modelSymbols" multiple>
                                                <option value="ES=F" selected>ES=F (E-mini S&P 500)</option>
                                                <option value="NQ=F">NQ=F (E-mini NASDAQ)</option>
                                                <option value="YM=F">YM=F (E-mini Dow)</option>
                                                <option value="RTY=F">RTY=F (E-mini Russell)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Training Period</label>
                                            <select class="form-select" id="trainingPeriod" name="trainingPeriod">
                                                <option value="1y">1 Year</option>
                                                <option value="2y">2 Years</option>
                                                <option value="5y">5 Years</option>
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Horizon (minutes)</label>
                                            <select class="form-select" id="modelHorizon" name="modelHorizon">
                                                <option value="15">15 minutes</option>
                                                <option value="30">30 minutes</option>
                                                <option value="60">1 hour</option>
                                                <option value="240">4 hours</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Hyperparameters (JSON)</label>
                                    <textarea class="form-control" id="modelHyperparams" name="modelHyperparams" rows="4" placeholder='{"learning_rate": 0.001, "batch_size": 32}'>{"learning_rate": 0.001, "batch_size": 32}</textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="startTrainingBtn">Start Training</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            console.log('Modal created and added to DOM');
            console.log('Modal element:', modal);
            console.log('Form element in modal:', modal.querySelector('#modelTrainingForm'));
            
            // Create Bootstrap modal instance
            let modalInstance;
            try {
                modalInstance = new bootstrap.Modal(modal);
                console.log('Bootstrap modal instance created');
                
                // Show the modal immediately
                modalInstance.show();
                console.log('Modal shown');
            } catch (bootstrapError) {
                console.error('Bootstrap modal creation failed:', bootstrapError);
                // Fallback to simple modal
                this.createFallbackModal();
                return;
            }
            
            // Add event listener for the start training button
            const startTrainingBtn = modal.querySelector('#startTrainingBtn');
            if (startTrainingBtn) {
                startTrainingBtn.addEventListener('click', () => {
                    console.log('Start training button clicked');
                    this.trainModel();
                });
            }
            
            // Clean up modal when hidden
            modal.addEventListener('hidden.bs.modal', () => {
                console.log('Modal hidden, cleaning up...');
                // Add a small delay before cleanup to ensure all operations complete
                setTimeout(() => {
                    if (document.body.contains(modal)) {
                        document.body.removeChild(modal);
                        console.log('Modal removed from DOM');
                    }
                }, 500);
            });
            
        } catch (error) {
            console.error('Error showing model training modal:', error);
            this.showNotification(`Error showing modal: ${error.message}`, 'error');
            
            // Fallback: try to show a simple alert with form data
            console.log('Attempting fallback modal creation...');
            try {
                this.createFallbackModal();
            } catch (fallbackError) {
                console.error('Fallback modal also failed:', fallbackError);
                this.showNotification('Modal creation failed completely', 'error');
            }
        }
    }

    createFallbackModal() {
        console.log('Creating fallback modal...');
        
        // Create a simple modal using basic HTML
        const fallbackModal = document.createElement('div');
        fallbackModal.id = 'fallbackModelTrainingModal';
        fallbackModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        fallbackModal.innerHTML = `
            <div style="background: white; padding: 20px; border-radius: 8px; max-width: 500px; width: 90%;">
                <h4>Train Distributional Model</h4>
                <form id="fallbackModelTrainingForm">
                    <div style="margin-bottom: 15px;">
                        <label>Model Type:</label>
                        <select id="fallbackModelType" style="width: 100%; padding: 8px; margin-top: 5px;">
                            <option value="transformer">Transformer Encoder (FQT-lite)</option>
                            <option value="quantile_regression">Quantile Regression</option>
                            <option value="random_forest">Random Forest Quantiles</option>
                            <option value="neural_network">Neural Network</option>
                            <option value="gradient_boosting">Gradient Boosting</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Symbols:</label>
                        <select id="fallbackModelSymbols" multiple style="width: 100%; padding: 8px; margin-top: 5px;">
                            <option value="ES=F" selected>ES=F (E-mini S&P 500)</option>
                            <option value="NQ=F">NQ=F (E-mini NASDAQ)</option>
                            <option value="YM=F">YM=F (E-mini Dow)</option>
                            <option value="RTY=F">RTY=F (E-mini Russell)</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Training Period:</label>
                        <select id="fallbackTrainingPeriod" style="width: 100%; padding: 8px; margin-top: 5px;">
                            <option value="1y">1 Year</option>
                            <option value="2y">2 Years</option>
                            <option value="5y">5 Years</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Horizon (minutes):</label>
                        <select id="fallbackModelHorizon" style="width: 100%; padding: 8px; margin-top: 5px;">
                            <option value="15">15 minutes</option>
                            <option value="30">30 minutes</option>
                            <option value="60">1 hour</option>
                            <option value="240">4 hours</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Hyperparameters (JSON):</label>
                        <textarea id="fallbackModelHyperparams" style="width: 100%; padding: 8px; margin-top: 5px; height: 60px;" placeholder='{"learning_rate": 0.001, "batch_size": 32}'>{}</textarea>
                    </div>
                    <div style="text-align: right;">
                        <button type="button" onclick="document.getElementById('fallbackModelTrainingModal').remove()" style="margin-right: 10px; padding: 8px 16px;">Cancel</button>
                        <button type="button" onclick="window.futurequantDashboard.trainModelFallback()" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px;">Start Training</button>
                    </div>
                </form>
            </div>
        `;
        
        document.body.appendChild(fallbackModal);
        console.log('Fallback modal created');
    }

    async trainModelFallback() {
        try {
            console.log('Starting model training with fallback form...');
            
            const modelType = document.getElementById('fallbackModelType').value;
            const symbolsElement = document.getElementById('fallbackModelSymbols');
            const trainingPeriod = document.getElementById('fallbackTrainingPeriod').value;
            const horizonMinutes = document.getElementById('fallbackModelHorizon').value;
            const hyperparamsText = document.getElementById('fallbackModelHyperparams').value || '{}';
            
            const selectedSymbols = Array.from(symbolsElement.selectedOptions).map(opt => opt.value);
            
            if (selectedSymbols.length === 0) {
                this.showNotification('Please select at least one symbol', 'error');
                return;
            }
            
            const trainingData = {
                model_type: modelType,
                symbols: selectedSymbols,
                training_period: trainingPeriod,
                horizon_minutes: parseInt(horizonMinutes),
                hyperparams: JSON.parse(hyperparamsText)
            };
            
            console.log('Training data prepared:', trainingData);
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showNotification('Model training started successfully', 'success');
            
            // Remove fallback modal
            const modal = document.getElementById('fallbackModelTrainingModal');
            if (modal) {
                modal.remove();
            }
            
            // Update job statuses
            this.loadJobStatuses();
            
        } catch (error) {
            console.error('Error training model with fallback:', error);
            this.showNotification(`Error starting model training: ${error.message}`, 'error');
        }
    }

    async trainModel(modelType = null) {
        try {
            console.log('Starting model training...');
            console.log('Model type parameter:', modelType);
            
            console.log('Looking for form with ID: modelTrainingForm');
            
            // Try to find the form in the modal first
            let form = null;
            const modal = document.getElementById('modelTrainingModal');
            if (modal) {
                form = modal.querySelector('#modelTrainingForm');
                console.log('Form found in modal:', form);
            }
            
            // If not found in modal, try document
            if (!form) {
                form = document.getElementById('modelTrainingForm');
                console.log('Form found in document:', form);
            }
            
            if (!form) {
                throw new Error('Model training form not found');
            }
            
            const formData = new FormData(form);
            console.log('Form data collected');
            
            // Get form values with error checking
            const modelTypeValue = modelType || formData.get('modelType');
            const symbolsElement = document.getElementById('modelSymbols');
            const trainingPeriod = formData.get('trainingPeriod');
            const horizonMinutes = formData.get('modelHorizon');
            const hyperparamsText = formData.get('modelHyperparams') || '{}';
            
            console.log('Form values:', {
                modelType: modelTypeValue,
                trainingPeriod,
                horizonMinutes,
                hyperparamsText
            });
            
            if (!symbolsElement) {
                throw new Error('Symbols select element not found');
            }
            
            const selectedSymbols = Array.from(symbolsElement.selectedOptions).map(opt => opt.value);
            console.log('Selected symbols:', selectedSymbols);
            
            if (selectedSymbols.length === 0) {
                throw new Error('Please select at least one symbol');
            }
            
            const trainingData = {
                model_type: modelTypeValue,
                symbols: selectedSymbols,
                training_period: trainingPeriod,
                horizon_minutes: parseInt(horizonMinutes),
                hyperparams: JSON.parse(hyperparamsText)
            };
            
            console.log('Training data prepared:', trainingData);
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showNotification('Model training started successfully', 'success');
            
            // Hide modal if it exists
            const modalToHide = document.getElementById('modelTrainingModal');
            if (modalToHide) {
                const modalInstance = bootstrap.Modal.getInstance(modalToHide);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
            
            // Update job statuses
            this.loadJobStatuses();
            
        } catch (error) {
            console.error('Error training model:', error);
            this.showNotification(`Error starting model training: ${error.message}`, 'error');
        }
    }

    async runBacktest() {
        try {
            const strategyId = document.getElementById('fq-strategy-select').value;
            if (!strategyId) {
                this.showNotification('Please select a strategy first', 'warning');
                return;
            }
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showNotification('Backtest started successfully', 'success');
            
            // Generate mock backtest results
            this.generateMockBacktestResults();
            
        } catch (error) {
            console.error('Error running backtest:', error);
            this.showNotification('Error starting backtest', 'error');
        }
    }

    generateMockBacktestResults() {
        // Update performance chart with backtest results
        const days = 30;
        const mockData = Array.from({ length: days }, (_, i) => ({
            date: new Date(Date.now() - (days - 1 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            value: 100000 + Math.sin(i * 0.2) * 5000 + Math.random() * 2000
        }));
        
        this.updatePerformanceChart(mockData);
    }

    async startPaperTrading() {
        try {
            const strategyId = document.getElementById('fq-strategy-select').value;
            if (!strategyId) {
                this.showNotification('Please select a strategy first', 'warning');
                return;
            }
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.activeSession = 'session_' + Date.now();
            this.showNotification('Paper trading session started', 'success');
            
            // Update sessions
            this.loadPaperTradingSessions();
            
        } catch (error) {
            console.error('Error starting paper trading:', error);
            this.showNotification('Error starting paper trading session', 'error');
        }
    }

    async stopPaperTrading(sessionId = null) {
        try {
            const targetSession = sessionId || this.activeSession;
            if (!targetSession) {
                this.showNotification('No active session to stop', 'warning');
                return;
            }
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            if (sessionId === this.activeSession) {
                this.activeSession = null;
            }
            this.showNotification('Paper trading session stopped', 'success');
            
            // Update sessions
            this.loadPaperTradingSessions();
            
        } catch (error) {
            console.error('Error stopping paper trading:', error);
            this.showNotification('Error stopping paper trading session', 'error');
        }
    }

    async ingestData() {
        try {
            this.showNotification('Data ingestion started successfully', 'success');
            
            // Update job statuses
            setTimeout(() => {
                this.loadJobStatuses();
            }, 2000);
            
        } catch (error) {
            console.error('Error ingesting data:', error);
            this.showNotification('Error starting data ingestion', 'error');
        }
    }

    async computeFeatures() {
        try {
            this.showNotification('Feature computation started successfully', 'success');
            
            // Update job statuses
            setTimeout(() => {
                this.loadJobStatuses();
            }, 2000);
            
        } catch (error) {
            console.error('Error computing features:', error);
            this.showNotification('Error starting feature computation', 'error');
        }
    }

    startDataRefresh() {
        // Refresh data every 30 seconds
        setInterval(() => {
            if (this.currentSymbol) {
                this.loadSymbolData();
            }
        }, 30000);
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        const toastContainer = document.getElementById('toast-container') || document.body;
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toast);
        });
    }
    
    // Public method to manually trigger chart initialization
    forceChartInitialization() {
        console.log('Force initializing charts...');
        this.initializeCharts();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking for Chart.js...');
    console.log('Chart.js available:', typeof Chart !== 'undefined');
    
    // Initialize Bootstrap tooltips
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        console.log('Bootstrap tooltips initialized');
    }
    
    if (typeof Chart !== 'undefined') {
        console.log('Chart.js found, setting up dashboard initialization...');
        // Don't initialize immediately - wait for tab to be active
        setupDashboardInitialization();
    } else {
        console.warn('Chart.js not loaded, dashboard initialization delayed');
        // Wait for Chart.js to load
        const checkChart = setInterval(() => {
            if (typeof Chart !== 'undefined') {
                console.log('Chart.js now available, setting up dashboard initialization...');
                clearInterval(checkChart);
            }
        }, 100);
    }
});

function setupDashboardInitialization() {
    // Initialize dashboard immediately for better responsiveness
    if (!window.futurequantDashboard) {
        console.log('Creating FutureQuant Dashboard immediately...');
        window.futurequantDashboard = new FutureQuantDashboard();
        window.futurequantDashboard.init();
        
        // Force load strategies and symbols immediately
        setTimeout(() => {
            if (window.futurequantDashboard.loadStrategies) {
                console.log('Loading strategies immediately...');
                window.futurequantDashboard.loadStrategies();
            }
            if (window.futurequantDashboard.loadSymbols) {
                console.log('Loading symbols immediately...');
                window.futurequantDashboard.loadSymbols();
            }
        }, 500);
    }
    
    // Wait for FutureQuant tab to be shown before initializing dashboard
    const futurequantTab = document.getElementById('futurequant-dashboard-tab');
    if (futurequantTab) {
        console.log('FutureQuant tab found, setting up event listener...');
        
        // Listen for tab shown event
        futurequantTab.addEventListener('shown.bs.tab', function() {
            console.log('FutureQuant tab shown, ensuring dashboard is initialized...');
            if (!window.futurequantDashboard) {
                window.futurequantDashboard = new FutureQuantDashboard();
                window.futurequantDashboard.init();
            }
            // Force refresh of strategies and symbols when tab is shown
            if (window.futurequantDashboard.loadStrategies) {
                window.futurequantDashboard.loadStrategies();
            }
            if (window.futurequantDashboard.loadSymbols) {
                window.futurequantDashboard.loadSymbols();
            }
        });
        
        // Also check if tab is already active
        if (futurequantTab.classList.contains('active')) {
            console.log('FutureQuant tab already active, ensuring dashboard is initialized...');
            if (!window.futurequantDashboard) {
                window.futurequantDashboard = new FutureQuantDashboard();
                window.futurequantDashboard.init();
            }
        }
    } else {
        console.error('FutureQuant tab not found, dashboard already initialized...');
    }
}

// Export for global access
window.FutureQuantDashboard = FutureQuantDashboard;

// Global function to manually trigger chart initialization (for debugging)
window.forceFutureQuantCharts = function() {
    if (window.futurequantDashboard) {
        console.log('Manually forcing chart initialization...');
        window.futurequantDashboard.forceChartInitialization();
    } else {
        console.log('Dashboard not initialized yet');
    }
};

// Global function to test model training (for debugging)
window.testModelTraining = function() {
    if (window.futurequantDashboard) {
        console.log('Testing model training...');
        window.futurequantDashboard.showModelTrainingModal();
    } else {
        console.log('Dashboard not initialized yet');
    }
};

// Global function to test modal creation directly
window.testModalCreation = function() {
    console.log('Testing modal creation directly...');
    
    // Create a simple test modal
    const testModal = document.createElement('div');
    testModal.id = 'testModal';
    testModal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    testModal.innerHTML = `
        <div style="background: white; padding: 20px; border-radius: 8px; max-width: 400px;">
            <h4>Test Modal</h4>
            <p>This is a test modal to verify modal creation works.</p>
            <button onclick="document.getElementById('testModal').remove()" style="padding: 8px 16px;">Close</button>
        </div>
    `;
    
    document.body.appendChild(testModal);
    console.log('Test modal created');
};

// Global function to initialize the dashboard
window.initializeFutureQuantDashboard = function() {
    console.log('Manually initializing FutureQuant Dashboard...');
    if (!window.futurequantDashboard) {
        window.futurequantDashboard = new FutureQuantDashboard();
    }
    window.futurequantDashboard.init();
    
    // Force load strategies and symbols
    if (window.futurequantDashboard.loadStrategies) {
        window.futurequantDashboard.loadStrategies();
    }
    if (window.futurequantDashboard.loadSymbols) {
        window.futurequantDashboard.loadSymbols();
    }
    
    console.log('Dashboard initialization complete');
};

// Fallback initialization after a delay to ensure everything loads
setTimeout(() => {
    if (!window.futurequantDashboard) {
        console.log('Fallback initialization of FutureQuant Dashboard...');
        window.initializeFutureQuantDashboard();
    } else {
        // Force load strategies even if dashboard exists
        console.log('Dashboard exists, forcing strategy load...');
        if (window.futurequantDashboard.loadStrategies) {
            window.futurequantDashboard.loadStrategies();
        }
    }
}, 3000);

// Additional fallback for strategies
setTimeout(() => {
    console.log('Final strategy loading attempt...');
    const strategySelect = document.getElementById('fq-strategy-select');
    if (strategySelect && strategySelect.options.length <= 1) {
        console.log('Strategy select still empty, forcing manual population...');
        window.debugStrategyButton();
    }
}, 5000);

// Global function to force load strategies
window.forceLoadStrategies = function() {
    console.log('Force loading strategies...');
    if (window.futurequantDashboard && window.futurequantDashboard.loadStrategies) {
        window.futurequantDashboard.loadStrategies();
        console.log('Strategies loaded');
    } else {
        console.log('Dashboard not ready, initializing first...');
        window.initializeFutureQuantDashboard();
    }
};

// Global function to debug strategy button
window.debugStrategyButton = function() {
    console.log('=== DEBUGGING STRATEGY BUTTON ===');
    
    // Check if dashboard exists
    console.log('Dashboard exists:', !!window.futurequantDashboard);
    
    // Check strategy select element
    const strategySelect = document.getElementById('fq-strategy-select');
    console.log('Strategy select element found:', !!strategySelect);
    if (strategySelect) {
        console.log('Strategy select HTML:', strategySelect.outerHTML);
        console.log('Strategy select options count:', strategySelect.options.length);
        console.log('Strategy select value:', strategySelect.value);
    }
    
    // Check if strategies are loaded
    if (window.futurequantDashboard) {
        console.log('Mock strategies available:', window.futurequantDashboard.mockStrategies);
        console.log('Mock strategies count:', window.futurequantDashboard.mockStrategies.length);
    }
    
    // Try to force load strategies
    if (window.futurequantDashboard && window.futurequantDashboard.loadStrategies) {
        console.log('Calling loadStrategies...');
        window.futurequantDashboard.loadStrategies();
    } else {
        console.log('loadStrategies method not available');
    }
    
    // Manual population test
    if (strategySelect) {
        console.log('Manually populating strategy select...');
        strategySelect.innerHTML = '<option value="">Aggressive Mean Reversion</option>';
        strategySelect.innerHTML += '<option value="1">Conservative Momentum</option>';
        strategySelect.innerHTML += '<option value="2">Moderate Trend Following</option>';
        strategySelect.innerHTML += '<option value="3">Aggressive Mean Reversion</option>';
        strategySelect.innerHTML += '<option value="4">Volatility Breakout</option>';
        strategySelect.innerHTML += '<option value="5">Statistical Arbitrage</option>';
        console.log('Manual population complete. Options count:', strategySelect.options.length);
    }
    
    console.log('=== END DEBUG ===');
};

// Global function to test trade button
window.testTradeButton = function() {
    console.log('=== TESTING TRADE BUTTON ===');
    
    // Check if dashboard exists
    console.log('Dashboard exists:', !!window.futurequantDashboard);
    
    // Check trade button element
    const tradeBtn = document.getElementById('fq-start-paper-trading-btn');
    console.log('Trade button element found:', !!tradeBtn);
    if (tradeBtn) {
        console.log('Trade button HTML:', tradeBtn.outerHTML);
        console.log('Trade button onclick:', tradeBtn.onclick);
        console.log('Trade button event listeners:', tradeBtn);
    }
    
    // Try to manually trigger the trading interface
    if (window.futurequantDashboard && window.futurequantDashboard.showTradingInterface) {
        console.log('Calling showTradingInterface directly...');
        window.futurequantDashboard.showTradingInterface();
    } else {
        console.log('showTradingInterface method not available');
    }
    
    console.log('=== END TRADE TEST ===');
};

// BRPC Training Function
async function startTrainingBRPC() {
    try {
        const trainingConfig = {
            model_type: document.querySelector('#trainingModal select')?.value || 'Neural Network',
            strategy_id: document.getElementById('fq-strategy-select')?.value || 1,
            symbol: document.getElementById('fq-symbol-select')?.value || 'ES',
            timeframe: document.getElementById('fq-timeframe-select')?.value || '1d',
            hyperparameters: {
                epochs: 100,
                batch_size: 32,
                learning_rate: 0.001
            }
        };
        
        console.log('Starting BRPC training with config:', trainingConfig);
        
        const response = await fetch('/api/v1/futurequant/models/train-brpc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(trainingConfig)
        });
        
        const result = await response.json();
        console.log('BRPC training result:', result);
        
        if (result.success) {
            showTrainingProgressBRPC(result);
        } else {
            showTrainingError(result.error);
        }
    } catch (error) {
        console.error('BRPC training failed:', error);
        showTrainingError('Training failed: ' + error.message);
    }
}

function showTrainingProgressBRPC(result) {
    const progressDiv = document.getElementById('trainingProgress');
    if (progressDiv) {
        progressDiv.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-rocket"></i> BRPC Training Started!</h6>
                <p><strong>Model ID:</strong> ${result.model_id}</p>
                <p><strong>Status:</strong> ${result.training_status}</p>
                <p><strong>Estimated Time:</strong> ${result.estimated_completion}</p>
                <p><strong>Mode:</strong> ${result.brpc_mode ? 'High-Performance BRPC' : 'Fallback HTTP'}</p>
                <div class="progress mt-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%">0%</div>
                </div>
            </div>
        `;
        progressDiv.style.display = 'block';
    }
}

function showTrainingError(error) {
    const progressDiv = document.getElementById('trainingProgress');
    if (progressDiv) {
        progressDiv.innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="fas fa-exclamation-triangle"></i> Training Error</h6>
                <p>${error}</p>
            </div>
        `;
        progressDiv.style.display = 'block';
    }
}

// Global function to test strategy loading
window.testStrategyLoading = function() {
    if (window.futurequantDashboard) {
        console.log('Testing strategy loading...');
        console.log('Current mock strategies:', window.futurequantDashboard.mockStrategies);
        
        // Test loading a specific strategy
        window.futurequantDashboard.loadStrategyData(1);
        
        // Test updating the strategy display
        const strategy = window.futurequantDashboard.mockStrategies[0];
        if (strategy) {
            window.futurequantDashboard.updateStrategyDisplay(strategy);
        }
        
        // Test manually populating strategy select
        const strategySelect = document.getElementById('fq-strategy-select');
        if (strategySelect) {
            console.log('Manually populating strategy select...');
            strategySelect.innerHTML = '<option value="">Select Strategy</option>';
            window.futurequantDashboard.mockStrategies.forEach(strategy => {
                strategySelect.innerHTML += `<option value="${strategy.id}">${strategy.name}</option>`;
            });
            console.log('Strategy select populated manually');
        }
    } else {
        console.log('Dashboard not initialized yet');
    }
};
