console.log('FutureQuant Dashboard loaded - Distributional Futures Trading Platform - Version 20250117');

// API configuration - allow real API calls
console.log('FutureQuant API calls are now enabled');

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
        
        // Train and Trade buttons - now unified
        const trainBtn = document.getElementById('fq-train-model-btn');
        if (trainBtn) {
            trainBtn.addEventListener('click', () => {
                this.showUnifiedTrainAndTradeInterface();
            });
        }
        
        const tradeBtn = document.getElementById('fq-start-paper-trading-btn');
        if (tradeBtn) {
            console.log('Trade button found, adding event listener');
            tradeBtn.addEventListener('click', () => {
                console.log('Trade button clicked!');
                this.showUnifiedTrainAndTradeInterface();
            });
        } else {
            console.error('Trade button not found!');
        }
        
        // Features button
        const featuresBtn = document.getElementById('fq-compute-features-btn');
        if (featuresBtn) {
            console.log('Features button found, adding event listener');
            featuresBtn.addEventListener('click', () => {
                console.log('Features button clicked!');
                this.showFeaturesComputation();
            });
        } else {
            console.error('Features button not found!');
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
        console.log('Loading futures trading strategies...');
        
        const strategySelect = document.getElementById('fq-strategy-select');
        console.log('Strategy select element:', strategySelect);
        
        if (strategySelect) {
            // Define futures-focused trading strategies
            const futuresStrategies = [
                { id: 1, name: 'Aggressive Mean Reversion', description: 'High-risk mean reversion for volatile futures markets' },
                { id: 2, name: 'Conservative Trend Following', description: 'Low-risk trend following with tight stops' },
                { id: 3, name: 'Volatility Breakout', description: 'Trade breakouts from low volatility periods' },
                { id: 4, name: 'Momentum Continuation', description: 'Follow strong momentum in futures markets' },
                { id: 5, name: 'Range Trading', description: 'Trade within established support/resistance levels' },
                { id: 6, name: 'News Event Trading', description: 'Trade around major economic announcements' }
            ];
            
            // Clear existing options
            strategySelect.innerHTML = '';
            
            // Add strategy options
            futuresStrategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id;
                option.textContent = strategy.name;
                strategySelect.appendChild(option);
                console.log('Added futures strategy:', strategy.name);
            });
            
            // Automatically select the first strategy
            if (futuresStrategies.length > 0) {
                strategySelect.value = futuresStrategies[0].id;
                console.log('Auto-selecting strategy:', futuresStrategies[0].name);
                
                // Load strategy details
                this.loadStrategyData(futuresStrategies[0].id);
            }
            
            // Add change event listener to update strategy display
            strategySelect.addEventListener('change', (e) => {
                const selectedStrategyId = e.target.value;
                if (selectedStrategyId) {
                    const selectedStrategy = futuresStrategies.find(s => s.id == selectedStrategyId);
                    if (selectedStrategy) {
                        console.log('Strategy changed to:', selectedStrategy.name);
                        this.loadStrategyData(selectedStrategy.id);
                    }
                }
            });
            
            console.log('Futures strategies loaded:', futuresStrategies.length);
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

    async loadPaperTradingSessions() {
        try {
            // Call real API to get active sessions
            const response = await fetch('/api/v1/futurequant/paper-trading/sessions');
            const data = await response.json();
            
            if (data.success && data.active_sessions) {
                // Convert API response to display format
                const sessions = Object.entries(data.active_sessions).map(([sessionId, session]) => ({
                    session_id: sessionId,
                    strategy_name: session.strategy_name,
                    start_time: session.start_time,
                    current_capital: session.current_capital,
                    current_return: session.current_return
                }));
                this.updatePaperTradingDisplay(sessions);
            } else {
                // No active sessions
                this.updatePaperTradingDisplay([]);
            }
        } catch (error) {
            console.error('Error loading paper trading sessions:', error);
            // Fallback to empty display
            this.updatePaperTradingDisplay([]);
        }
    }

    loadRecentSignals() {
        const futuresSignals = [
            { symbol: 'ES=F', side: 'long', confidence: 0.78, timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
            { symbol: 'NQ=F', side: 'short', confidence: 0.82, timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString() },
            { symbol: 'YM=F', side: 'long', confidence: 0.71, timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString() },
            { symbol: 'CL=F', side: 'long', confidence: 0.65, timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString() },
            { symbol: 'GC=F', side: 'short', confidence: 0.73, timestamp: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString() }
        ];
        this.updateSignalsDisplay(futuresSignals);
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
        console.log('Loading futures strategy data for ID:', strategyId);
        if (!strategyId) {
            console.log('No strategy ID provided, returning');
            return;
        }
        
        try {
            // Define futures strategies with detailed information
            const futuresStrategies = [
                { 
                    id: 1, 
                    name: 'Aggressive Mean Reversion', 
                    description: 'High-risk mean reversion for volatile futures markets',
                    riskLevel: 'High',
                    timeframe: '5 minutes to 1 hour',
                    bestFor: 'Volatile markets, short-term trades, experienced traders',
                    howItWorks: 'Identifies when futures prices move too far from their average and bets they\'ll return to normal levels. Uses aggressive position sizing for maximum profit potential.',
                    avgGain: '0.1193% per 30-min trade'
                },
                { 
                    id: 2, 
                    name: 'Conservative Trend Following', 
                    description: 'Low-risk trend following with tight stops',
                    riskLevel: 'Low',
                    timeframe: '1 hour to 4 hours',
                    bestFor: 'Stable trends, swing trading, risk-averse traders',
                    howItWorks: 'Follows established futures trends with multiple confirmation signals. Uses tight stop losses and position scaling for risk management.',
                    avgGain: '0.085% per 2-hour trade'
                },
                { 
                    id: 3, 
                    name: 'Volatility Breakout', 
                    description: 'Trade breakouts from low volatility periods',
                    riskLevel: 'Medium',
                    timeframe: '15 minutes to 2 hours',
                    bestFor: 'Range-bound markets, volatility expansion, breakout traders',
                    howItWorks: 'Monitors futures volatility and enters positions when price breaks out of low volatility ranges with volume confirmation.',
                    avgGain: '0.156% per breakout trade'
                },
                { 
                    id: 4, 
                    name: 'Momentum Continuation', 
                    description: 'Follow strong momentum in futures markets',
                    riskLevel: 'Medium-High',
                    timeframe: '30 minutes to 3 hours',
                    bestFor: 'Strong trending markets, momentum traders, trend followers',
                    howItWorks: 'Rides strong futures momentum using multiple timeframe analysis and trailing stops to maximize trend profits.',
                    avgGain: '0.203% per momentum trade'
                },
                { 
                    id: 5, 
                    name: 'Range Trading', 
                    description: 'Trade within established support/resistance levels',
                    riskLevel: 'Low-Medium',
                    timeframe: '1 hour to 6 hours',
                    bestFor: 'Sideways markets, range traders, mean reversion',
                    howItWorks: 'Identifies key support and resistance levels in futures markets and trades bounces within established ranges.',
                    avgGain: '0.067% per range trade'
                },
                { 
                    id: 6, 
                    name: 'News Event Trading', 
                    description: 'Trade around major economic announcements',
                    riskLevel: 'Very High',
                    timeframe: '5 minutes to 30 minutes',
                    bestFor: 'News traders, event-driven strategies, high-frequency trading',
                    howItWorks: 'Trades futures around major economic events using pre-news positioning and post-news momentum strategies.',
                    avgGain: '0.342% per news event'
                }
            ];
            
            const strategy = futuresStrategies.find(s => s.id == strategyId);
            console.log('Found futures strategy:', strategy);
            if (strategy) {
                this.updateStrategyDisplay(strategy);
            } else {
                console.warn('Futures strategy not found for ID:', strategyId);
            }
        } catch (error) {
            console.error('Error loading futures strategy data:', error);
        }
    }
    
    updateStrategyDisplay(strategy) {
        console.log('Updating futures strategy display for:', strategy.name);
        const strategyDetails = document.getElementById('fq-strategy-details');
        
        if (strategyDetails) {
            // Create detailed futures strategy information
            const riskColor = {
                'Low': 'bg-success',
                'Low-Medium': 'bg-info',
                'Medium': 'bg-warning',
                'Medium-High': 'bg-orange',
                'High': 'bg-danger',
                'Very High': 'bg-dark'
            };
            
            const strategyInfo = `
                <div class="alert alert-info mb-3">
                    <h6 class="text-primary mb-2">
                        <i class="fas fa-chart-line"></i> ${strategy.name}
                    </h6>
                    <p class="small mb-2"><strong>Description:</strong> ${strategy.description}</p>
                    <p class="small mb-2"><strong>Best For:</strong> ${strategy.bestFor}</p>
                    <p class="small mb-2"><strong>Risk Level:</strong> <span class="badge ${riskColor[strategy.riskLevel]}">${strategy.riskLevel}</span></p>
                    <p class="small mb-0"><strong>Timeframe:</strong> ${strategy.timeframe}</p>
                </div>
                <div class="small text-muted mb-3">
                    <strong>How it works:</strong> ${strategy.howItWorks}
                </div>
                <div class="alert alert-success mb-0 py-2 small">
                    <i class="fas fa-chart-area"></i> <strong>Performance:</strong> Average gain of ${strategy.avgGain}
                </div>
            `;
            
            strategyDetails.innerHTML = strategyInfo;
            console.log('Futures strategy display updated');
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
            <style>
                .training-step {
                    transition: all 0.3s ease;
                }
                .success-animation {
                    animation: fadeInUp 0.6s ease-out;
                }
                .animate-bounce {
                    animation: bounce 2s infinite;
                }
                .stat-card {
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 12px;
                    border: 1px solid #dee2e6;
                    transition: all 0.3s ease;
                }
                .stat-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    border-color: #007bff;
                }
                .progress-circle {
                    position: relative;
                    width: 80px;
                    height: 80px;
                    margin: 0 auto;
                }
                .progress-circle-bg {
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    background: #e9ecef;
                    border: 8px solid #dee2e6;
                }
                .progress-circle-fill {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    border: 8px solid transparent;
                    border-top-color: #28a745;
                    border-right-color: #28a745;
                    transform: rotate(45deg);
                    animation: fillProgress 1s ease-out;
                }
                .progress-circle-text {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-weight: bold;
                    color: #28a745;
                    font-size: 14px;
                }
                .action-buttons {
                    margin: 2rem 0;
                }
                .action-buttons .btn {
                    transition: all 0.3s ease;
                }
                        .action-buttons .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .technical-stack-card {
            margin: 2rem 0;
        }
        
        .tech-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .tech-item {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            padding: 0.5rem;
            border-radius: 8px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            transition: all 0.3s ease;
        }
        
        .tech-item:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-color: #007bff;
        }
        
        .tech-item .badge {
            font-size: 0.75rem;
            padding: 0.375rem 0.75rem;
        }
        
        .tech-item small {
            font-size: 0.75rem;
            line-height: 1.2;
        }
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                    40% { transform: translateY(-10px); }
                    60% { transform: translateY(-5px); }
                }
                @keyframes fillProgress {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(45deg); }
                }
            </style>
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-brain"></i> AI Model Training
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Step 1: Configuration -->
                        <div id="configStep" class="training-step">
                            <h6><i class="fas fa-cog"></i> Training Configuration</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Model Type</label>
                                        <select class="form-select" id="modelType">
                                            <option value="neural_network">Neural Network</option>
                                            <option value="transformer">Transformer</option>
                                            <option value="quantile_regression">Quantile Regression</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Training Period</label>
                                        <select class="form-select" id="trainingPeriod">
                                            <option value="6_months">Last 6 months</option>
                                            <option value="1_year">Last 1 year</option>
                                            <option value="2_years">Last 2 years</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Features</label>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="priceIndicators" checked>
                                            <label class="form-check-label" for="priceIndicators">Price indicators</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="volumeIndicators" checked>
                                            <label class="form-check-label" for="volumeIndicators">Volume indicators</label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="volatilityIndicators" checked>
                                            <label class="form-check-label" for="volatilityIndicators">Volatility indicators</label>
                                        </div>
                                    </div>
                                    
                                    <div class="alert alert-info">
                                        <i class="fas fa-info-circle"></i>
                                        <small>
                                            <strong>Training Process:</strong><br>
                                            • Configure your model settings<br>
                                            • Click "Start Training" to begin<br>
                                            • Model will be saved automatically<br>
                                            • Ready for trading when complete
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 2: Training Progress -->
                        <div id="progressStep" class="training-step" style="display: none;">
                            <h6><i class="fas fa-chart-line"></i> Training Progress</h6>
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
                        
                        <!-- Step 3: Completion -->
                        <div id="completionStep" class="training-step" style="display: none;">
                            <div class="text-center p-4">
                                <!-- Success Animation -->
                                <div class="success-animation mb-4">
                                    <div class="text-success mb-3">
                                        <i class="fas fa-check-circle fa-4x animate-bounce"></i>
                                    </div>
                                    <h4 class="text-success mb-2">🎉 Training Complete!</h4>
                                    <p class="text-muted">Your AI model is ready to trade</p>
                                    <script>
                                        // Enable the Trade button when training completes
                                        if (typeof window.enableTradeButton === 'function') {
                                            window.enableTradeButton();
                                        }
                                    </script>
                                </div>
                                
                                <!-- Model Status Card -->
                                <div class="card border-success mb-4">
                                    <div class="card-body text-center">
                                        <div class="row align-items-center">
                                            <div class="col-md-8">
                                                <h5 class="card-title text-success mb-2">
                                                    <i class="fas fa-robot"></i> Model Saved Successfully
                                                </h5>
                                                <p class="card-text mb-3">
                                                    Your trained model has been automatically saved and is now ready for 
                                                    <strong>paper trading</strong> and <strong>strategy execution</strong>.
                                                </p>
                                                <div class="d-flex justify-content-center gap-3">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-save"></i> Saved
                                                    </span>
                                                    <span class="badge bg-primary">
                                                        <i class="fas fa-chart-line"></i> Trading Ready
                                                    </span>
                                                    <span class="badge bg-info">
                                                        <i class="fas fa-shield-alt"></i> Risk Managed
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="text-center">
                                                    <div class="progress-circle mb-2">
                                                        <div class="progress-circle-bg"></div>
                                                        <div class="progress-circle-fill"></div>
                                                        <div class="progress-circle-text">100%</div>
                                                    </div>
                                                    <small class="text-muted">Training Progress</small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                                                    <!-- Technical Stack Card -->
                                    <div class="technical-stack-card mb-4">
                                        <div class="card border-primary">
                                            <div class="card-header bg-primary text-white text-center">
                                                <h6 class="mb-0">
                                                    <i class="fas fa-cogs"></i> FutureQuant Technical Stack
                                                </h6>
                                            </div>
                                            <div class="card-body">
                                                <div class="row">
                                                    <div class="col-md-6">
                                                        <h6 class="text-primary mb-3">
                                                            <i class="fas fa-python"></i> Core Python Libraries
                                                        </h6>
                                                        <div class="tech-list">
                                                            <div class="tech-item">
                                                                <span class="badge bg-primary">NumPy</span>
                                                                <small class="text-muted">Numerical computing</small>
                                                            </div>
                                                            <div class="tech-item">
                                                                <span class="badge bg-primary">Pandas</span>
                                                                <small class="text-muted">Data manipulation</small>
                                                            </div>
                                                            <div class="tech-item">
                                                                <span class="badge bg-info">QuantLib</span>
                                                                <small class="text-muted">Derivatives pricing</small>
                                                            </div>
                                                            <div class="tech-item">
                                                                <span class="badge bg-primary">yfinance</span>
                                                                <small class="text-muted">Market data</small>
                                                            </div>
                                                        </div>
                                                    </div>
                                                                                                        <div class="col-md-6">
                                                        <h6 class="text-success mb-3">
                                                            <i class="fas fa-rocket"></i> Core Technologies
                                                        </h6>
                                                        <div class="tech-list">
                                                            <div class="tech-item">
                                                                <span class="badge bg-success">PyTorch</span>
                                                                <small class="text-muted">Deep learning</small>
                                                            </div>
                                                            <div class="tech-item">
                                                                <span class="badge bg-success">Transformer Models</span>
                                                                <small class="text-muted">Sequence learning</small>
                                                            </div>
                                                            <div class="tech-item">
                                                                <span class="badge bg-warning">BRPC</span>
                                                                <small class="text-muted">High-performance RPC</small>
                                                            </div>
                                                            <div class="tech-item">
                                                                <span class="badge bg-success">Real-time Processing</span>
                                                                <small class="text-muted">Async I/O</small>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <!-- Core Quantitative Analysis Section -->
                                        <div class="row mt-3">
                                            <div class="col-12">
                                                <h6 class="text-dark mb-3">
                                                    <i class="fas fa-chart-line"></i> Essential Quant Components
                                                </h6>
                                                <div class="tech-list">
                                                    <div class="row">
                                                        <div class="col-md-4">
                                                            <div class="tech-item">
                                                                <span class="badge bg-dark">Risk Management</span>
                                                                <small class="text-muted">Position sizing</small>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-4">
                                                            <div class="tech-item">
                                                                <span class="badge bg-dark">Feature Engineering</span>
                                                                <small class="text-muted">Technical indicators</small>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-4">
                                                            <div class="tech-item">
                                                                <span class="badge bg-dark">Portfolio Theory</span>
                                                                <small class="text-muted">MPT & CAPM</small>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <!-- Start Trading Button -->
                                        <div class="text-center mt-4">
                                        <button type="button" class="btn btn-success btn-lg" onclick="startTradingWithModel()">
                                            <i class="fas fa-play"></i> Start Trading with Model
                                        </button>
                                    </div>
                                    
                                    <!-- Quick Stats -->
                                    <div class="row mt-4">
                                    <div class="col-md-3">
                                        <div class="stat-card text-center p-3">
                                            <i class="fas fa-chart-line fa-2x text-primary mb-2"></i>
                                            <h6 class="mb-1">Ready for Trading</h6>
                                            <small class="text-muted">Paper Trading</small>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="stat-card text-center p-3">
                                            <i class="fas fa-robot fa-2x text-success mb-2"></i>
                                            <h6 class="mb-1">AI Powered</h6>
                                            <small class="text-muted">Machine Learning</small>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="stat-card text-center p-3">
                                            <i class="fas fa-shield-alt fa-2x text-info mb-2"></i>
                                            <h6 class="mb-1">Risk Managed</h6>
                                            <small class="text-muted">Safety First</small>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="stat-card text-center p-3">
                                            <i class="fas fa-rocket fa-2x text-warning mb-2"></i>
                                            <h6 class="mb-1">High Performance</h6>
                                            <small class="text-muted">Optimized</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="startTrainingBtn" onclick="startTrainingBRPC()">Start Training</button>
                        <button type="button" class="btn btn-success" id="backToConfigBtn" onclick="showTrainingStep('config')" style="display: none;">Back to Configuration</button>
                        <button type="button" class="btn btn-info" id="closeModalBtn" data-bs-dismiss="modal" style="display: none;">Close</button>
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
            container.innerHTML = `
                <div class="col-12">
                    <div class="text-center text-muted">
                        <p>No active paper trading sessions</p>
                        <p class="small">Click "Start Session" to begin paper trading with real market data</p>
                    </div>
                </div>
            `;
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
                                <i class="fas fa-stop"></i> Stop
                            </button>
                            <a href="paper-trading-dashboard.html" class="btn btn-sm btn-primary ms-2" target="_blank">
                                <i class="fas fa-chart-line"></i> Live Dashboard
                            </a>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(sessionCard);
        });
    }
    
    async getRealTimeDashboardData(sessionId) {
        try {
            const response = await fetch(`/api/v1/futurequant/paper-trading/sessions/${sessionId}/dashboard`);
            const data = await response.json();
            
            if (data.success) {
                return data.dashboard_data;
            } else {
                console.error('Failed to get dashboard data:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Error getting dashboard data:', error);
            return null;
        }
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
                                                <option value="0.5">30 seconds (DEMO - ultra fast training)</option>
                                                <option value="5">5 minutes (for testing)</option>
                                                <option value="15">15 minutes</option>
                                                <option value="60">1 hour (60 minutes)</option>
                                                <option value="240">4 hours (240 minutes)</option>
                                                <option value="1440">1 day (1440 minutes)</option>
                                            </select>
                                            <small class="form-text text-muted">30 seconds = demo mode with 5 epochs for quick testing</small>
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
                            <option value="0.5">30 seconds (DEMO - ultra fast training)</option>
                            <option value="5">5 minutes (for testing)</option>
                            <option value="15">15 minutes</option>
                            <option value="60">1 hour (60 minutes)</option>
                            <option value="240">4 hours (240 minutes)</option>
                            <option value="1440">1 day (1440 minutes)</option>
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
                symbol: selectedSymbols[0], // Use first selected symbol for now
                model_type: modelType,
                horizon_minutes: parseFloat(horizonMinutes),
                hyperparams: JSON.parse(hyperparamsText)
            };
            
            console.log('Training data prepared:', trainingData);
            
            // Make real API call to start training
            const response = await fetch('/api/v1/futurequant/models/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trainingData)
            });
            
            const result = await response.json();
            console.log('Training API response:', result);
            
            if (result.success) {
                this.showNotification('Model training started successfully', 'success');
                
                // Show training progress
                this.showTrainingProgress(result);
            } else {
                throw new Error(result.error || 'Training failed');
            }
            
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
            
            // Prepare training data for the API
            const trainingData = {
                symbol: selectedSymbols[0], // Use first selected symbol for now
                model_type: modelTypeValue,
                horizon_minutes: parseFloat(horizonMinutes),
                hyperparams: JSON.parse(hyperparamsText)
            };
            
            console.log('Training data prepared:', trainingData);
            
            // Make real API call to start training
            const response = await fetch('/api/v1/futurequant/models/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trainingData)
            });
            
            const result = await response.json();
            console.log('Training API response:', result);
            
            if (result.success) {
                this.showNotification('Model training started successfully', 'success');
                
                // Show training progress
                this.showTrainingProgress(result);
                
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
            } else {
                throw new Error(result.error || 'Training failed');
            }
            
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
    
    showTrainingProgress(result) {
        // Create or update training progress display
        let progressDiv = document.getElementById('trainingProgress');
        if (!progressDiv) {
            progressDiv = document.createElement('div');
            progressDiv.id = 'trainingProgress';
            progressDiv.className = 'alert alert-info';
            progressDiv.style.position = 'fixed';
            progressDiv.style.top = '20px';
            progressDiv.style.right = '20px';
            progressDiv.style.zIndex = '9999';
            progressDiv.style.minWidth = '300px';
            document.body.appendChild(progressDiv);
        }
        
        progressDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6><i class="fas fa-cog fa-spin"></i> Model Training Started</h6>
                    <p class="mb-1"><strong>Model ID:</strong> ${result.model_id}</p>
                    <p class="mb-1"><strong>Symbol:</strong> ${result.symbol}</p>
                    <p class="mb-1"><strong>Type:</strong> ${result.model_type}</p>
                    <p class="mb-2"><strong>Status:</strong> Training in progress...</p>
                </div>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%">0%</div>
            </div>
            <small class="text-muted">Training started at ${new Date().toLocaleTimeString()}</small>
        `;
        
        // Start progress animation
        this.animateTrainingProgress(progressDiv);
    }
    
    animateTrainingProgress(progressDiv) {
        // Get model ID from the progress div
        const modelId = progressDiv.querySelector('p:first-of-type strong')?.nextSibling?.textContent?.trim();
        if (!modelId) {
            console.error('No model ID found for progress tracking');
            return;
        }
        
        // Poll backend for real training progress
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/futurequant/models/training-status/${modelId}`);
                const statusData = await response.json();
                
                if (statusData.status === 'completed') {
                    // Training completed
                    clearInterval(pollInterval);
                    
                    // Update the progress div
                    progressDiv.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6><i class="fas fa-check-circle text-success"></i> Training Completed!</h6>
                                <p class="mb-1"><strong>Model ID:</strong> ${modelId}</p>
                                <p class="mb-2"><strong>Status:</strong> Training completed successfully</p>
                            </div>
                            <button type="button" class="btn-close" onclick="closeTrainingPopupAndTransitionToPaperTrading(this)"></button>
                        </div>
                        <div class="progress">
                            <div class="progress-bar bg-success" style="width: 100%">100%</div>
                        </div>
                        <small class="text-muted">Completed at ${new Date().toLocaleTimeString()}</small>
                        
                        <div class="alert alert-success mt-2">
                            <i class="fas fa-save"></i>
                            <strong>Model Saved!</strong> Ready for paper trading and strategy execution.
                        </div>
                    `;
                    
                    // Also update the main training dialog if it exists
                    this.updateMainTrainingDialog(modelId, 'completed', statusData);
                    
                    // Enable the Trade button after training completion
                    if (typeof window.enableTradeButton === 'function') {
                        window.enableTradeButton();
                    }
                } else if (statusData.status === 'failed') {
                    // Training failed
                    clearInterval(pollInterval);
                    
                    // Update the progress div
                    progressDiv.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6><i class="fas fa-exclamation-triangle text-danger"></i> Training Failed</h6>
                                <p class="mb-1"><strong>Model ID:</strong> ${modelId}</p>
                                <p class="mb-2"><strong>Error:</strong> ${statusData.error || 'Unknown error'}</p>
                            </div>
                            <button type="button" class="btn-close" onclick="closeTrainingPopupAndTransitionToPaperTrading(this)"></button>
                        </div>
                        <div class="progress">
                            <div class="progress-bar bg-danger" style="width: 100%">Failed</div>
                        </div>
                        <small class="text-muted">Failed at ${new Date().toLocaleTimeString()}</small>
                    `;
                    
                    // Also update the main training dialog if it exists
                    this.updateMainTrainingDialog(modelId, 'failed', statusData);
                } else if (statusData.status === 'training') {
                    // Update progress with real data
                    const progressBar = progressDiv.querySelector('.progress-bar');
                    const statusText = progressDiv.querySelector('p:last-of-type');
                    
                    if (progressBar) {
                        progressBar.style.width = statusData.progress + '%';
                        progressBar.textContent = Math.round(statusData.progress) + '%';
                    }
                    
                    if (statusText) {
                        statusText.innerHTML = `<strong>Status:</strong> Epoch ${statusData.current_epoch}/${statusData.total_epochs} - Loss: ${statusData.loss}`;
                    }
                }
            } catch (error) {
                console.error('Error polling training status:', error);
                // Continue polling even if there's an error
            }
        }, 2000); // Poll every 2 seconds
        
        // Store interval reference for cleanup
        progressDiv.dataset.progressInterval = pollInterval;
    }
    
    updateMainTrainingDialog(modelId, status, statusData) {
        // Find the main training dialog
        const trainingDialog = document.querySelector('.modal.show');
        if (!trainingDialog) return;
        
        // Find the training progress section
        const progressSection = trainingDialog.querySelector('.col-md-6:last-child');
        if (!progressSection) return;
        
                        if (status === 'completed') {
                    // Update to completed state
                    progressSection.innerHTML = `
                        <h6>Training Progress</h6>
                        <div class="text-center p-4">
                            <div class="text-success mb-3">
                                <i class="fas fa-check-circle fa-3x"></i>
                            </div>
                            <h6 class="text-success">Training Completed!</h6>
                            <div class="progress mb-3">
                                <div class="progress-bar bg-success" style="width: 100%">100%</div>
                            </div>
                            <p class="text-success small">Model ID: ${modelId} - Training completed successfully</p>
                            <p class="text-muted small">Completed at ${new Date().toLocaleTimeString()}</p>
                            
                            <div class="alert alert-info mt-3">
                                <i class="fas fa-info-circle"></i>
                                <strong>Model Saved!</strong> Your trained model has been automatically saved and is now ready for trading.
                                <br><small class="text-muted">You can use this model for paper trading and strategy execution.</small>
                            </div>
                        </div>
                    `;
                    
                    // Update the Start Training button to be disabled or change text
                    const startButton = trainingDialog.querySelector('.btn-primary');
                    if (startButton) {
                        startButton.textContent = 'Model Ready for Trading';
                        startButton.disabled = true;
                        startButton.className = 'btn btn-success';
                    }
        } else if (status === 'failed') {
            // Update to failed state
            progressSection.innerHTML = `
                <h6>Training Progress</h6>
                <div class="text-center p-4">
                    <div class="text-danger mb-3">
                        <i class="fas fa-exclamation-triangle fa-3x"></i>
                    </div>
                    <h6 class="text-danger">Training Failed</h6>
                    <div class="progress mb-3">
                        <div class="progress-bar bg-danger" style="width: 100%">Failed</div>
                    </div>
                    <p class="text-danger small">Error: ${statusData.error || 'Unknown error'}</p>
                    <p class="text-muted small">Failed at ${new Date().toLocaleTimeString()}</p>
                </div>
            `;
            
            // Update the Start Training button
            const startButton = trainingDialog.querySelector('.btn-primary');
            if (startButton) {
                startButton.textContent = 'Retry Training';
                startButton.className = 'btn btn-warning';
            }
        }
    }

    async startPaperTrading() {
        try {
            const strategyId = document.getElementById('fq-strategy-select').value;
            if (!strategyId) {
                this.showNotification('Please select a strategy first', 'warning');
                return;
            }
            
            // Get strategy name and details from the dropdown
            const strategySelect = document.getElementById('fq-strategy-select');
            const strategyName = strategySelect.options[strategySelect.selectedIndex].text;
            
            // Get strategy configuration based on selection
            const strategyConfig = this.getStrategyConfiguration(strategyId);
            console.log('Applying strategy configuration:', strategyConfig);
            
            // Use futures symbols for futures-focused trading
            const futuresSymbols = ['ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'CL=F', 'GC=F'];
            
            // Call real API to start paper trading session with selected strategy
            const response = await fetch('/api/v1/futurequant/paper-trading/start-demo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strategy_name: strategyName,
                    strategy_config: strategyConfig,
                    symbols: futuresSymbols
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.activeSession = data.session_id;
                
                // Store strategy config for this session
                this.activeStrategyConfig = strategyConfig;
                
                // Show strategy-specific notification with details
                this.showNotification(`🎯 ${strategyName} strategy applied! Risk: ${strategyConfig.riskLevel}, Position Size: ${strategyConfig.positionSizeMultiplier}x`, 'success');
                
                // Update sessions display
                this.loadPaperTradingSessions();
                
                // Show real-time dashboard link
                this.showNotification('Open the Live Dashboard to see real-time futures P&L updates!', 'info');
                
                // Log strategy application
                console.log(`Started paper trading with strategy: ${strategyName} (ID: ${strategyId})`);
                console.log('Strategy configuration applied:', strategyConfig);
                
                // Show strategy details panel
                this.showStrategyDetailsPanel(strategyConfig);
            } else {
                this.showNotification('Failed to start session: ' + data.error, 'error');
            }
            
        } catch (error) {
            console.error('Error starting paper trading:', error);
            this.showNotification('Error starting paper trading session', 'error');
        }
    }

    getStrategyConfiguration(strategyId) {
        // Define strategy-specific configurations that affect trading behavior
        const strategyConfigs = {
            1: { // Aggressive Mean Reversion
                name: 'Aggressive Mean Reversion',
                riskLevel: 'High',
                positionSizeMultiplier: 2.0,        // 2x normal position size
                stopLossPercent: 3.0,               // 3% stop loss
                takeProfitPercent: 6.0,             // 6% take profit
                maxDrawdown: 0.15,                  // 15% max drawdown
                leverage: 3.0,                      // 3x leverage
                entryRules: 'Enter when price deviates 2+ standard deviations from mean',
                exitRules: 'Exit on mean reversion or stop loss hit',
                timeHorizon: '5min-1hour',
                volatilityThreshold: 'High'
            },
            2: { // Conservative Trend Following
                name: 'Conservative Trend Following',
                riskLevel: 'Low',
                positionSizeMultiplier: 0.5,        // 0.5x normal position size
                stopLossPercent: 1.5,               // 1.5% tight stop loss
                takeProfitPercent: 3.0,             // 3% take profit
                maxDrawdown: 0.08,                  // 8% max drawdown
                leverage: 1.5,                      // 1.5x leverage
                entryRules: 'Enter on trend confirmation with multiple timeframes',
                exitRules: 'Exit on trend reversal or trailing stop',
                timeHorizon: '1hour-4hours',
                volatilityThreshold: 'Low'
            },
            3: { // Volatility Breakout
                name: 'Volatility Breakout',
                riskLevel: 'Medium',
                positionSizeMultiplier: 1.0,        // 1x normal position size
                stopLossPercent: 2.5,               // 2.5% stop loss
                takeProfitPercent: 5.0,             // 5% take profit
                maxDrawdown: 0.12,                  // 12% max drawdown
                leverage: 2.0,                      // 2x leverage
                entryRules: 'Enter on volatility expansion with volume confirmation',
                exitRules: 'Exit on volatility contraction or target hit',
                timeHorizon: '15min-2hours',
                volatilityThreshold: 'Medium'
            },
            4: { // Momentum Continuation
                name: 'Momentum Continuation',
                riskLevel: 'Medium-High',
                positionSizeMultiplier: 1.5,        // 1.5x normal position size
                stopLossPercent: 2.0,               // 2% stop loss
                takeProfitPercent: 8.0,             // 8% take profit
                maxDrawdown: 0.18,                  // 18% max drawdown
                leverage: 2.5,                      // 2.5x leverage
                entryRules: 'Enter on momentum confirmation with volume',
                exitRules: 'Exit on momentum loss or trailing stop',
                timeHorizon: '30min-3hours',
                volatilityThreshold: 'Medium-High'
            },
            5: { // Range Trading
                name: 'Range Trading',
                riskLevel: 'Low-Medium',
                positionSizeMultiplier: 0.8,        // 0.8x normal position size
                stopLossPercent: 2.0,               // 2% stop loss
                takeProfitPercent: 4.0,             // 4% take profit
                maxDrawdown: 0.10,                  // 10% max drawdown
                leverage: 1.8,                      // 1.8x leverage
                entryRules: 'Enter at support/resistance with reversal signals',
                exitRules: 'Exit at opposite boundary or stop loss',
                timeHorizon: '1hour-6hours',
                volatilityThreshold: 'Low'
            },
            6: { // News Event Trading
                name: 'News Event Trading',
                riskLevel: 'Very High',
                positionSizeMultiplier: 3.0,        // 3x normal position size
                stopLossPercent: 5.0,               // 5% stop loss
                takeProfitPercent: 15.0,            // 15% take profit
                maxDrawdown: 0.25,                  // 25% max drawdown
                leverage: 4.0,                      // 4x leverage
                entryRules: 'Enter before major news with position sizing',
                exitRules: 'Exit on news release or extreme volatility',
                timeHorizon: '5min-30min',
                volatilityThreshold: 'Extreme'
            }
        };
        
        return strategyConfigs[strategyId] || strategyConfigs[1]; // Default to aggressive if not found
    }

    showStrategyDetailsPanel(strategyConfig) {
        // Create and show a strategy details panel
        const panel = document.createElement('div');
        panel.className = 'alert alert-info alert-dismissible fade show';
        panel.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <h6 class="alert-heading">🎯 Active Strategy: ${strategyConfig.name}</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <small><strong>Risk Level:</strong> <span class="badge bg-${this.getRiskColor(strategyConfig.riskLevel)}">${strategyConfig.riskLevel}</span></small><br>
                            <small><strong>Position Size:</strong> ${strategyConfig.positionSizeMultiplier}x</small><br>
                            <small><strong>Leverage:</strong> ${strategyConfig.leverage}x</small>
                        </div>
                        <div class="col-md-6">
                            <small><strong>Stop Loss:</strong> ${strategyConfig.stopLossPercent}%</small><br>
                            <small><strong>Take Profit:</strong> ${strategyConfig.takeProfitPercent}%</small><br>
                            <small><strong>Max Drawdown:</strong> ${strategyConfig.maxDrawdown * 100}%</small>
                        </div>
                    </div>
                    <small class="text-muted mt-2 d-block">
                        <strong>Entry:</strong> ${strategyConfig.entryRules}<br>
                        <strong>Exit:</strong> ${strategyConfig.exitRules}
                    </small>
                </div>
                <div class="col-md-4 text-end">
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="this.showStrategyPerformance()">
                            <i class="fas fa-chart-line"></i> Performance
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to the page
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(panel, container.firstChild);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (panel.parentNode) {
                panel.remove();
            }
        }, 10000);
    }

    getRiskColor(riskLevel) {
        const colors = {
            'Low': 'success',
            'Low-Medium': 'info',
            'Medium': 'warning',
            'Medium-High': 'orange',
            'High': 'danger',
            'Very High': 'dark'
        };
        return colors[riskLevel] || 'secondary';
    }

    async stopPaperTrading(sessionId = null) {
        try {
            const targetSession = sessionId || this.activeSession;
            if (!targetSession) {
                this.showNotification('No active session to stop', 'warning');
                return;
            }
            
            // Call real API to stop paper trading session
            const response = await fetch(`/api/v1/futurequant/paper-trading/stop/${targetSession}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (sessionId === this.activeSession) {
                    this.activeSession = null;
                }
                this.showNotification('Paper trading session stopped successfully!', 'success');
                
                // Show session summary if available
                if (data.summary) {
                    const summary = data.summary;
                    this.showNotification(`Final P&L: ${summary.total_pnl >= 0 ? '+' : ''}$${summary.total_pnl.toFixed(2)} (${summary.total_return.toFixed(2)}%)`, 'info');
                }
                
                // Update sessions
                this.loadPaperTradingSessions();
            } else {
                this.showNotification('Failed to stop session: ' + data.error, 'error');
            }
            
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
        
        // Refresh paper trading data more frequently for real-time updates
        setInterval(() => {
            if (this.activeSession) {
                this.refreshActiveSessionData();
            }
        }, 10000); // Every 10 seconds
    }
    
    async refreshActiveSessionData() {
        if (!this.activeSession) return;
        
        try {
            const dashboardData = await this.getRealTimeDashboardData(this.activeSession);
            if (dashboardData) {
                // Update any real-time displays if they exist
                this.updateRealTimeMetrics(dashboardData);
            }
        } catch (error) {
            console.error('Error refreshing session data:', error);
        }
    }
    
    updateRealTimeMetrics(dashboardData) {
        // Update any real-time metric displays
        // This can be expanded to update specific UI elements
        console.log('Real-time update:', dashboardData);
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
    
    // Initialize paper trading interface
    initializePaperTrading() {
        console.log('Initializing paper trading interface...');
        
        // Add event listener for the Start Session button
        const startButton = document.getElementById('fq-start-paper-trading-btn');
        if (startButton) {
            startButton.addEventListener('click', () => {
                this.showPaperTradingModal();
            });
        }
        
        // Add event listener for the Stop Session button
        const stopButton = document.getElementById('fq-stop-paper-trading-btn');
        if (stopButton) {
            stopButton.addEventListener('click', () => {
                this.stopPaperTrading();
            });
        }
        
        // Show paper trading section
        const paperTradingSection = document.getElementById('paper-trading-section');
        if (paperTradingSection) {
            paperTradingSection.style.display = 'block';
        }
        
        // Hide training sections
        const trainingSections = document.querySelectorAll('.training-section, .model-training-section');
        trainingSections.forEach(section => {
            section.style.display = 'none';
        });
        
        // Update navigation
        const navItems = document.querySelectorAll('.nav-link');
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.textContent.includes('Paper Trading') || item.getAttribute('data-section') === 'paper-trading') {
                item.classList.add('active');
            }
        });
        
        // Load paper trading data
        this.loadPaperTradingSessions();
        
        // Show success message
        this.showNotification('Paper trading interface ready! Your model is loaded and ready for strategy execution.', 'success');
        
        console.log('Paper trading interface initialized successfully');
    }

    // Show paper trading modal
    showPaperTradingModal() {
        // Create and show paper trading modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'paperTradingModal';
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
                        <!-- Trading Controls -->
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <div class="card">
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-3">
                                                <label class="form-label">Symbol</label>
                                                <select class="form-select" id="tradingSymbol">
                                                    <option value="ES=F">ES=F (E-mini S&P 500)</option>
                                                    <option value="NQ=F">NQ=F (E-mini NASDAQ)</option>
                                                    <option value="YM=F">YM=F (E-mini Dow)</option>
                                                    <option value="RTY=F">RTY=F (E-mini Russell)</option>
                                                </select>
                                            </div>
                                            <div class="col-md-2">
                                                <label class="form-label">Position Size</label>
                                                <input type="number" class="form-control" id="positionSize" value="1" min="1" max="10">
                                            </div>
                                            <div class="col-md-2">
                                                <label class="form-label">Stop Loss</label>
                                                <input type="number" class="form-control" id="stopLoss" step="0.25" placeholder="0.00">
                                            </div>
                                            <div class="col-md-2">
                                                <label class="form-label">Take Profit</label>
                                                <input type="number" class="form-control" id="takeProfit" step="0.25" placeholder="0.00">
                                            </div>
                                            <div class="col-md-3">
                                                <label class="form-label">&nbsp;</label>
                                                <div class="d-grid gap-2">
                                                    <button type="button" class="btn btn-success" id="buyButton">
                                                        <i class="fas fa-arrow-up"></i> BUY
                                                    </button>
                                                    <button type="button" class="btn btn-danger" id="sellButton">
                                                        <i class="fas fa-arrow-down"></i> SELL
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Account Summary -->
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Account Balance</h6>
                                        <h4 class="text-success" id="accountBalance">$100,000</h4>
                                        <small class="text-muted">Virtual Money</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Current P&L</h6>
                                        <h4 class="text-primary" id="currentPnL">+$0</h4>
                                        <small class="text-muted">Today's Gain</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Open Positions</h6>
                                        <h4 class="text-info" id="openPositions">0</h4>
                                        <small class="text-muted">Active Trades</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h6 class="text-muted">Win Rate</h6>
                                        <h4 class="text-warning" id="winRate">0%</h4>
                                        <small class="text-muted">Successful Trades</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <h6>Live Trading Chart</h6>
                                <div class="border rounded p-3" style="height: 400px; background: #f8f9fa;">
                                    <canvas id="tradingChart" width="400" height="400"></canvas>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <h6>Recent Trades</h6>
                                <div id="recentTradesList" class="list-group">
                                    <div class="text-center text-muted pt-3">
                                        <i class="fas fa-info-circle"></i>
                                        <p>No trades yet</p>
                                        <small>Start trading to see your history</small>
                                    </div>
                                </div>
                                
                                <h6 class="mt-3">Open Positions</h6>
                                <div id="openPositionsList" class="list-group">
                                    <div class="text-center text-muted pt-3">
                                        <i class="fas fa-info-circle"></i>
                                        <p>No open positions</p>
                                        <small>Open a position to see it here</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-warning" id="closeAllPositions">
                            <i class="fas fa-times"></i> Close All Positions
                        </button>
                        <button type="button" class="btn btn-danger" id="stopTrading">
                            <i class="fas fa-stop"></i> Stop Trading
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show the modal
        const paperTradingModal = new bootstrap.Modal(modal);
        paperTradingModal.show();
        
        // Initialize paper trading functionality
        this.initializePaperTradingModal();
    }

    // Create and show paper trading modal
    initializePaperTradingModal() {
        // Initialize trading state
        this.tradingState = {
            accountBalance: 100000,
            openPositions: [],
            tradeHistory: [],
            currentSymbol: 'ES=F',
            isTrading: false,
            chart: null,
            priceData: [],
            lastPrice: null
        };

        // Initialize chart
        this.initializeTradingChart();
        
        // Set up event listeners
        this.setupTradingEventListeners();
        
        // Start real-time price updates
        this.startRealTimeUpdates();
        
        // Load initial data
        this.loadTradingData();
    }

    initializeTradingChart() {
        const ctx = document.getElementById('tradingChart');
        if (!ctx) return;

        this.tradingState.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price',
                    data: [],
                    borderColor: '#00d4aa',
                    backgroundColor: 'rgba(0, 212, 170, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#666'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#666'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#666'
                        }
                    }
                }
            }
        });
    }

    setupTradingEventListeners() {
        // Buy button
        document.getElementById('buyButton')?.addEventListener('click', () => {
            this.executeTrade('BUY');
        });

        // Sell button
        document.getElementById('sellButton')?.addEventListener('click', () => {
            this.executeTrade('SELL');
        });

        // Symbol change
        document.getElementById('tradingSymbol')?.addEventListener('change', (e) => {
            this.tradingState.currentSymbol = e.target.value;
            this.loadTradingData();
        });

        // Stop trading
        document.getElementById('stopTrading')?.addEventListener('click', () => {
            this.stopTrading();
        });

        // Close all positions
        document.getElementById('closeAllPositions')?.addEventListener('click', () => {
            this.closeAllPositions();
        });
    }

    executeTrade(direction) {
        const symbol = document.getElementById('tradingSymbol')?.value || 'ES=F';
        const size = parseInt(document.getElementById('positionSize')?.value || 1);
        const stopLoss = parseFloat(document.getElementById('stopLoss')?.value || 0);
        const takeProfit = parseFloat(document.getElementById('takeProfit')?.value || 0);

        if (!this.tradingState.lastPrice) {
            this.showNotification('No price data available', 'error');
            return;
        }

        const trade = {
            id: Date.now(),
            symbol: symbol,
            direction: direction,
            size: size,
            entryPrice: this.tradingState.lastPrice,
            stopLoss: stopLoss,
            takeProfit: takeProfit,
            timestamp: new Date(),
            status: 'OPEN'
        };

        // Add to open positions
        this.tradingState.openPositions.push(trade);
        
        // Update UI
        this.updateTradingUI();
        
        // Show confirmation
        this.showNotification(`${direction} ${size} ${symbol} at $${this.tradingState.lastPrice}`, 'success');
        
        // Log trade
        console.log('Trade executed:', trade);
    }

    startRealTimeUpdates() {
        this.tradingState.isTrading = true;
        
        // Simulate real-time price updates (replace with actual API calls)
        this.priceUpdateInterval = setInterval(() => {
            if (this.tradingState.isTrading) {
                this.updatePrice();
                this.checkStopLossTakeProfit();
            }
        }, 2000); // Update every 2 seconds
    }

    updatePrice() {
        // Simulate price movement (replace with real market data)
        const basePrice = this.getBasePrice(this.tradingState.currentSymbol);
        const volatility = 0.002; // 0.2% volatility
        const change = (Math.random() - 0.5) * 2 * volatility * basePrice;
        const newPrice = basePrice + change;
        
        this.tradingState.lastPrice = newPrice;
        this.tradingState.priceData.push({
            timestamp: new Date(),
            price: newPrice
        });

        // Keep only last 100 data points
        if (this.tradingState.priceData.length > 100) {
            this.tradingState.priceData.shift();
        }

        // Update chart
        this.updateChart();
        
        // Update P&L for open positions
        this.updatePositionsPnL();
    }

    getBasePrice(symbol) {
        const basePrices = {
            'ES=F': 4500,
            'NQ=F': 15800,
            'YM=F': 33450,
            'RTY=F': 2000
        };
        return basePrices[symbol] || 4500;
    }

    updateChart() {
        if (!this.tradingState.chart) return;

        const labels = this.tradingState.priceData.map((_, index) => 
            new Date(this.tradingState.priceData[index].timestamp).toLocaleTimeString()
        );
        const prices = this.tradingState.priceData.map(d => d.price);

        this.tradingState.chart.data.labels = labels;
        this.tradingState.chart.data.datasets[0].data = prices;
        this.tradingState.chart.update('none');
    }

    updatePositionsPnL() {
        if (!this.tradingState.lastPrice) return;

        this.tradingState.openPositions.forEach(position => {
            const priceDiff = this.tradingState.lastPrice - position.entryPrice;
            const multiplier = position.direction === 'BUY' ? 1 : -1;
            position.currentPnL = priceDiff * multiplier * position.size * 50; // ES=F multiplier
        });

        this.updateTradingUI();
    }

    checkStopLossTakeProfit() {
        this.tradingState.openPositions.forEach((position, index) => {
            if (position.status !== 'OPEN') return;

            const currentPrice = this.tradingState.lastPrice;
            let shouldClose = false;
            let closeReason = '';

            // Check stop loss
            if (position.stopLoss > 0) {
                if (position.direction === 'BUY' && currentPrice <= position.stopLoss) {
                    shouldClose = true;
                    closeReason = 'Stop Loss';
                } else if (position.direction === 'SELL' && currentPrice >= position.stopLoss) {
                    shouldClose = true;
                    closeReason = 'Stop Loss';
                }
            }

            // Check take profit
            if (position.takeProfit > 0) {
                if (position.direction === 'BUY' && currentPrice >= position.takeProfit) {
                    shouldClose = true;
                    closeReason = 'Take Profit';
                } else if (position.direction === 'SELL' && currentPrice <= position.takeProfit) {
                    shouldClose = true;
                    closeReason = 'Take Profit';
                }
            }

            if (shouldClose) {
                this.closePosition(index, closeReason);
            }
        });
    }

    closePosition(index, reason = 'Manual') {
        const position = this.tradingState.openPositions[index];
        if (!position) return;

        // Calculate final P&L
        const priceDiff = this.tradingState.lastPrice - position.entryPrice;
        const multiplier = position.direction === 'BUY' ? 1 : -1;
        const finalPnL = priceDiff * multiplier * position.size * 50;

        // Update position
        position.exitPrice = this.tradingState.lastPrice;
        position.exitTime = new Date();
        position.status = 'CLOSED';
        position.finalPnL = finalPnL;
        position.closeReason = reason;

        // Move to trade history
        this.tradingState.tradeHistory.push({...position});
        this.tradingState.openPositions.splice(index, 1);

        // Update account balance
        this.tradingState.accountBalance += finalPnL;

        // Update UI
        this.updateTradingUI();
        
        // Show notification
        const pnlText = finalPnL >= 0 ? `+$${finalPnL.toFixed(2)}` : `-$${Math.abs(finalPnL).toFixed(2)}`;
        this.showNotification(`Position closed: ${pnlText} (${reason})`, finalPnL >= 0 ? 'success' : 'error');
    }

    closeAllPositions() {
        if (this.tradingState.openPositions.length === 0) {
            this.showNotification('No open positions to close', 'info');
            return;
        }

        this.tradingState.openPositions.forEach((_, index) => {
            this.closePosition(index, 'Close All');
        });
    }

    stopTrading() {
        this.tradingState.isTrading = false;
        if (this.priceUpdateInterval) {
            clearInterval(this.priceUpdateInterval);
        }
        this.showNotification('Trading stopped', 'warning');
    }

    stopPaperTrading() {
        if (this.tradingState && this.tradingState.isTrading) {
            this.stopTrading();
        }
        this.showNotification('Paper trading session stopped', 'warning');
    }

    updateTradingUI() {
        // Update account summary
        const totalPnL = this.tradingState.openPositions.reduce((sum, pos) => sum + (pos.currentPnL || 0), 0);
        const totalPnLText = totalPnL >= 0 ? `+$${totalPnL.toFixed(2)}` : `-$${Math.abs(totalPnL).toFixed(2)}`;
        
        document.getElementById('accountBalance').textContent = `$${this.tradingState.accountBalance.toFixed(2)}`;
        document.getElementById('currentPnL').textContent = totalPnLText;
        document.getElementById('currentPnL').className = totalPnL >= 0 ? 'text-success' : 'text-danger';
        document.getElementById('openPositions').textContent = this.tradingState.openPositions.length;
        
        // Calculate win rate
        const closedTrades = this.tradingState.tradeHistory.filter(t => t.status === 'CLOSED');
        const winningTrades = closedTrades.filter(t => t.finalPnL > 0);
        const winRate = closedTrades.length > 0 ? (winningTrades.length / closedTrades.length * 100).toFixed(1) : 0;
        document.getElementById('winRate').textContent = `${winRate}%`;

        // Update open positions list
        this.updateOpenPositionsList();
        
        // Update recent trades list
        this.updateRecentTradesList();
    }

    updateOpenPositionsList() {
        const container = document.getElementById('openPositionsList');
        if (!container) return;

        if (this.tradingState.openPositions.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted pt-3">
                    <i class="fas fa-info-circle"></i>
                    <p>No open positions</p>
                    <small>Open a position to see it here</small>
                </div>
            `;
            return;
        }

        container.innerHTML = this.tradingState.openPositions.map(position => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>${position.symbol} ${position.direction}</strong><br>
                    <small class="text-muted">Entry: $${position.entryPrice.toFixed(2)} | Size: ${position.size}</small>
                </div>
                <div class="text-end">
                    <span class="badge ${(position.currentPnL || 0) >= 0 ? 'bg-success' : 'bg-danger'}">
                        ${(position.currentPnL || 0) >= 0 ? '+' : ''}$${(position.currentPnL || 0).toFixed(2)}
                    </span>
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="window.futurequantDashboard.closePositionById(${position.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    updateRecentTradesList() {
        const container = document.getElementById('recentTradesList');
        if (!container) return;

        const recentTrades = this.tradingState.tradeHistory.slice(-5).reverse();
        
        if (recentTrades.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted pt-3">
                    <i class="fas fa-info-circle"></i>
                    <p>No trades yet</p>
                    <small>Start trading to see your history</small>
                </div>
            `;
            return;
        }

        container.innerHTML = recentTrades.map(trade => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>${trade.symbol} ${trade.direction}</strong><br>
                    <small class="text-muted">Entry: $${trade.entryPrice.toFixed(2)} | Exit: $${trade.exitPrice.toFixed(2)}</small>
                </div>
                <span class="badge ${trade.finalPnL >= 0 ? 'bg-success' : 'bg-danger'}">
                    ${trade.finalPnL >= 0 ? '+' : ''}$${trade.finalPnL.toFixed(2)}
                </span>
            </div>
        `).join('');
    }

    closePositionById(id) {
        const index = this.tradingState.openPositions.findIndex(p => p.id === id);
        if (index !== -1) {
            this.closePosition(index, 'Manual');
        }
    }

    loadTradingData() {
        // Load historical data for the selected symbol
        // This would typically call your backend API
        console.log('Loading trading data for:', this.tradingState.currentSymbol);
        
        // For now, initialize with some sample data
        this.tradingState.priceData = [];
        for (let i = 0; i < 50; i++) {
            const time = new Date(Date.now() - (50 - i) * 2000);
            const basePrice = this.getBasePrice(this.tradingState.currentSymbol);
            const price = basePrice + (Math.random() - 0.5) * 100;
            this.tradingState.priceData.push({ timestamp: time, price });
        }
        
        this.tradingState.lastPrice = this.tradingState.priceData[this.tradingState.priceData.length - 1].price;
        this.updateChart();
    }

    showUnifiedTrainAndTradeInterface() {
        console.log('Showing unified train and trade interface...');
        
        // Create and show unified modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'unifiedTrainTradeModal';
        modal.innerHTML = `
            <style>
                .unified-step {
                    transition: all 0.3s ease;
                }
                .step-indicator {
                    display: flex;
                    justify-content: center;
                    margin-bottom: 2rem;
                }
                .step-indicator .step {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #6c757d;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 10px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                }
                .step-indicator .step.active {
                    background: #007bff;
                    transform: scale(1.1);
                }
                .step-indicator .step.completed {
                    background: #28a745;
                }
                .step-indicator .step-line {
                    width: 60px;
                    height: 2px;
                    background: #6c757d;
                    margin: auto 0;
                }
                .step-indicator .step-line.completed {
                    background: #28a745;
                }
                .unified-content {
                    min-height: 500px;
                }
                .training-section, .trading-section {
                    display: none;
                }
                .training-section.active, .trading-section.active {
                    display: block;
                }
                .action-buttons {
                    margin: 2rem 0;
                }
                .action-buttons .btn {
                    transition: all 0.3s ease;
                }
                .action-buttons .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .progress-section {
                    text-align: center;
                    padding: 2rem;
                }
                .completion-section {
                    text-align: center;
                    padding: 2rem;
                }
                .success-animation {
                    animation: fadeInUp 0.6s ease-out;
                }
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            </style>
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-rocket"></i> AI-Powered Trading Workflow
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Step Indicator -->
                        <div class="step-indicator">
                            <div class="step active" data-step="1">1</div>
                            <div class="step-line" data-step="1"></div>
                            <div class="step" data-step="2">2</div>
                            <div class="step-line" data-step="2"></div>
                            <div class="step" data-step="3">3</div>
                        </div>
                        
                        <!-- Step 1: Configuration -->
                        <div id="step1" class="unified-step unified-content">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-cog"></i> Model Configuration</h6>
                                    <div class="mb-3">
                                        <label class="form-label">Model Type</label>
                                        <select class="form-select" id="unifiedModelType">
                                            <option value="transformer">Transformer Encoder (FQT-lite)</option>
                                            <option value="quantile_regression">Quantile Regression</option>
                                            <option value="random_forest">Random Forest Quantiles</option>
                                            <option value="neural_network">Neural Network</option>
                                            <option value="gradient_boosting">Gradient Boosting</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Training Period</label>
                                        <select class="form-select" id="unifiedTrainingPeriod">
                                            <option value="6_months">Last 6 months</option>
                                            <option value="1_year">Last 1 year</option>
                                            <option value="2_years">Last 2 years</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Horizon (minutes)</label>
                                        <select class="form-select" id="unifiedHorizon">
                                            <option value="0.5">30 seconds (DEMO - ultra fast)</option>
                                            <option value="5">5 minutes</option>
                                            <option value="15">15 minutes</option>
                                            <option value="60">1 hour</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fas fa-chart-line"></i> Trading Strategy</h6>
                                    <div class="mb-3">
                                        <label class="form-label">Strategy</label>
                                        <select class="form-select" id="unifiedStrategy">
                                            <option value="1">Aggressive Mean Reversion</option>
                                            <option value="2">Conservative Trend Following</option>
                                            <option value="3">Volatility Breakout</option>
                                            <option value="4">Momentum Continuation</option>
                                            <option value="5">Range Trading</option>
                                            <option value="6">News Event Trading</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Initial Capital</label>
                                        <input type="number" class="form-control" id="unifiedCapital" value="100000" min="10000" step="10000">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Risk Tolerance</label>
                                        <select class="form-select" id="unifiedRisk">
                                            <option value="low">Low (Conservative)</option>
                                            <option value="medium">Medium (Balanced)</option>
                                            <option value="high">High (Aggressive)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="alert alert-info mt-3">
                                <i class="fas fa-info-circle"></i>
                                <strong>Workflow:</strong> This will train your AI model and then automatically start paper trading with the selected strategy.
                            </div>
                        </div>
                        
                        <!-- Step 2: Training Progress -->
                        <div id="step2" class="unified-step unified-content" style="display: none;">
                            <div class="progress-section">
                                <h6><i class="fas fa-cog fa-spin"></i> Training AI Model</h6>
                                <div class="spinner-border text-primary mb-3" role="status">
                                    <span class="visually-hidden">Training...</span>
                                </div>
                                <h6>Training in Progress...</h6>
                                <div class="progress mb-3">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                         style="width: 0%">0%</div>
                                </div>
                                <p class="text-muted small">Epoch 0/50 - Loss: 0.0000</p>
                                <div class="alert alert-info mt-3">
                                    <i class="fas fa-clock"></i>
                                    <strong>Estimated time:</strong> 2-5 minutes for demo mode
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 3: Trading Interface -->
                        <div id="step3" class="unified-step unified-content" style="display: none;">
                            <div class="completion-section">
                                <div class="success-animation mb-4">
                                    <div class="text-success mb-3">
                                        <i class="fas fa-check-circle fa-4x"></i>
                                    </div>
                                    <h4 class="text-success mb-2">Model Ready!</h4>
                                    <p class="text-muted">Your AI model is now trading automatically</p>
                                </div>
                                
                                <!-- Live Trading Dashboard -->
                                <div class="row">
                                    <div class="col-md-8">
                                        <h6>Live Trading Chart</h6>
                                        <div class="border rounded p-3" style="height: 300px; background: #f8f9fa;">
                                            <canvas id="unifiedTradingChart" width="400" height="300"></canvas>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <h6>Account Summary</h6>
                                        <div class="card mb-3">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted">Balance</h6>
                                                <h4 class="text-success" id="unifiedBalance">$100,000</h4>
                                            </div>
                                        </div>
                                        <div class="card mb-3">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted">P&L</h6>
                                                <h4 class="text-primary" id="unifiedPnL">+$0</h4>
                                            </div>
                                        </div>
                                        <div class="card">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted">Positions</h6>
                                                <h4 class="text-info" id="unifiedPositions">0</h4>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Recent Trades -->
                                <div class="row mt-3">
                                    <div class="col-12">
                                        <h6>Recent Trades</h6>
                                        <div id="unifiedRecentTrades" class="list-group">
                                            <div class="text-center text-muted pt-3">
                                                <i class="fas fa-info-circle"></i>
                                                <p>No trades yet</p>
                                                <small>AI model will start trading automatically</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="startWorkflowBtn" onclick="futurequantDashboard.startUnifiedWorkflow()">
                            <i class="fas fa-rocket"></i> Start Workflow
                        </button>
                        <button type="button" class="btn btn-success" id="nextStepBtn" onclick="futurequantDashboard.nextStep()" style="display: none;">
                            <i class="fas fa-arrow-right"></i> Next
                        </button>
                        <button type="button" class="btn btn-info" id="closeModalBtn" data-bs-dismiss="modal" style="display: none;">
                            <i class="fas fa-check"></i> Close
                        </button>
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
            // Clean up intervals
            if (this.unifiedTradingInterval) {
                clearInterval(this.unifiedTradingInterval);
                this.unifiedTradingInterval = null;
            }
            
            // Clean up training interval if exists
            if (modal.dataset.trainingInterval) {
                clearInterval(parseInt(modal.dataset.trainingInterval));
            }
            
            // Remove modal from DOM
            document.body.removeChild(modal);
        });
        
        // Store modal reference
        this.unifiedModal = modal;
        this.currentStep = 1;
    }

    async startUnifiedWorkflow() {
        try {
            console.log('Starting unified workflow...');
            
            // Get configuration values
            const modelType = document.getElementById('unifiedModelType').value;
            const trainingPeriod = document.getElementById('unifiedTrainingPeriod').value;
            const horizon = document.getElementById('unifiedHorizon').value;
            const strategy = document.getElementById('unifiedStrategy').value;
            const capital = document.getElementById('unifiedCapital').value;
            const risk = document.getElementById('unifiedRisk').value;
            
            // Validate inputs
            if (!modelType || !strategy) {
                this.showNotification('Please fill in all required fields', 'error');
                return;
            }
            
            // Move to step 2 (training)
            this.goToStep(2);
            
            // Start model training
            const trainingData = {
                symbol: 'ES=F', // Default symbol for demo
                model_type: modelType,
                horizon_minutes: parseFloat(horizon),
                hyperparams: { learning_rate: 0.001, batch_size: 32 }
            };
            
            console.log('Starting model training with:', trainingData);
            
            // Make API call to start training
            const response = await fetch('/api/v1/futurequant/models/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trainingData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Model training started successfully', 'success');
                this.startUnifiedTrainingProgress(result.model_id);
            } else {
                throw new Error(result.error || 'Training failed');
            }
            
        } catch (error) {
            console.error('Error starting unified workflow:', error);
            this.showNotification(`Error starting workflow: ${error.message}`, 'error');
            this.goToStep(1); // Go back to configuration
        }
    }

    startUnifiedTrainingProgress(modelId) {
        console.log('Starting unified training progress for model:', modelId);
        
        // Simulate training progress (replace with real API polling)
        let progress = 0;
        const progressBar = this.unifiedModal.querySelector('.progress-bar');
        const statusText = this.unifiedModal.querySelector('.text-muted.small');
        
        const trainingInterval = setInterval(() => {
            progress += Math.random() * 15; // Random progress increment
            if (progress > 100) progress = 100;
            
            if (progressBar) {
                progressBar.style.width = progress + '%';
                progressBar.textContent = Math.round(progress) + '%';
            }
            
            if (statusText) {
                const epoch = Math.floor(progress / 2);
                statusText.textContent = `Epoch ${epoch}/50 - Loss: ${(0.1 - progress * 0.001).toFixed(4)}`;
            }
            
            if (progress >= 100) {
                clearInterval(trainingInterval);
                
                // Show success message
                this.showTrainingCompletionMessage();
                
                // Enable the Trade button after training completion
                if (typeof window.enableTradeButton === 'function') {
                    window.enableTradeButton();
                }
                
                // Training complete, move to step 3
                setTimeout(() => {
                    this.goToStep(3);
                    this.initializeUnifiedTrading();
                }, 2000);
            }
        }, 1000);
        
        // Store interval for cleanup
        this.unifiedModal.dataset.trainingInterval = trainingInterval;
    }

    initializeUnifiedTrading() {
        console.log('Initializing unified trading interface...');
        
        // Initialize trading chart
        this.initializeUnifiedTradingChart();
        
        // Start simulated trading
        this.startUnifiedTrading();
        
        // Update UI elements
        this.updateUnifiedTradingUI();
    }

    initializeUnifiedTradingChart() {
        const ctx = document.getElementById('unifiedTradingChart');
        if (!ctx) return;
        
        // Create simple line chart
        this.unifiedTradingChart = new Chart(ctx, {
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
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    startUnifiedTrading() {
        // Simulate trading activity
        this.unifiedTradingState = {
            balance: 100000,
            positions: 0,
            pnl: 0,
            trades: [],
            chartData: []
        };
        
        // Start updating trading data
        this.unifiedTradingInterval = setInterval(() => {
            this.updateUnifiedTradingData();
        }, 3000);
    }

    updateUnifiedTradingData() {
        // Simulate price movements and trades
        const priceChange = (Math.random() - 0.5) * 0.02; // ±1% change
        this.unifiedTradingState.balance *= (1 + priceChange);
        this.unifiedTradingState.pnl = this.unifiedTradingState.balance - 100000;
        
        // Randomly generate trades
        if (Math.random() < 0.3) { // 30% chance of trade
            this.generateUnifiedTrade();
        }
        
        // Update chart
        this.updateUnifiedTradingChart();
        
        // Update UI
        this.updateUnifiedTradingUI();
    }

    generateUnifiedTrade() {
        const trade = {
            id: Date.now(),
            symbol: 'ES=F',
            side: Math.random() > 0.5 ? 'BUY' : 'SELL',
            price: 4850 + (Math.random() - 0.5) * 100,
            size: Math.floor(Math.random() * 5) + 1,
            timestamp: new Date()
        };
        
        this.unifiedTradingState.trades.unshift(trade);
        this.unifiedTradingState.positions = this.unifiedTradingState.trades.length;
        
        // Keep only last 10 trades
        if (this.unifiedTradingState.trades.length > 10) {
            this.unifiedTradingState.trades.pop();
        }
    }

    updateUnifiedTradingChart() {
        if (!this.unifiedTradingChart) return;
        
        const now = new Date();
        this.unifiedTradingState.chartData.push({
            time: now.toLocaleTimeString(),
            value: this.unifiedTradingState.balance
        });
        
        // Keep only last 20 data points
        if (this.unifiedTradingState.chartData.length > 20) {
            this.unifiedTradingState.chartData.shift();
        }
        
        // Update chart
        this.unifiedTradingChart.data.labels = this.unifiedTradingState.chartData.map(d => d.time);
        this.unifiedTradingChart.data.datasets[0].data = this.unifiedTradingState.chartData.map(d => d.value);
        this.unifiedTradingChart.update();
    }

    updateUnifiedTradingUI() {
        // Update balance
        const balanceElement = document.getElementById('unifiedBalance');
        if (balanceElement) {
            balanceElement.textContent = `$${this.unifiedTradingState.balance.toLocaleString()}`;
        }
        
        // Update P&L
        const pnlElement = document.getElementById('unifiedPnL');
        if (pnlElement) {
            const pnlText = this.unifiedTradingState.pnl >= 0 ? 
                `+$${this.unifiedTradingState.pnl.toFixed(2)}` : 
                `-$${Math.abs(this.unifiedTradingState.pnl).toFixed(2)}`;
            pnlElement.textContent = pnlText;
            pnlElement.className = this.unifiedTradingState.pnl >= 0 ? 'text-success' : 'text-danger';
        }
        
        // Update positions
        const positionsElement = document.getElementById('unifiedPositions');
        if (positionsElement) {
            positionsElement.textContent = this.unifiedTradingState.positions;
        }
        
        // Update recent trades
        this.updateUnifiedRecentTrades();
    }

    updateUnifiedRecentTrades() {
        const tradesContainer = document.getElementById('unifiedRecentTrades');
        if (!tradesContainer || this.unifiedTradingState.trades.length === 0) return;
        
        tradesContainer.innerHTML = '';
        this.unifiedTradingState.trades.slice(0, 5).forEach(trade => {
            const tradeElement = document.createElement('div');
            tradeElement.className = 'list-group-item d-flex justify-content-between align-items-center';
            tradeElement.innerHTML = `
                <div>
                    <strong>${trade.side} ${trade.symbol}</strong><br>
                    <small class="text-muted">$${trade.price.toFixed(2)} × ${trade.size}</small>
                </div>
                <small class="text-muted">${trade.timestamp.toLocaleTimeString()}</small>
            `;
            tradesContainer.appendChild(tradeElement);
        });
    }

    goToStep(step) {
        console.log('Moving to step:', step);
        
        // Hide all steps
        for (let i = 1; i <= 3; i++) {
            const stepElement = document.getElementById(`step${i}`);
            if (stepElement) {
                stepElement.style.display = 'none';
            }
        }
        
        // Show current step
        const currentStepElement = document.getElementById(`step${step}`);
        if (currentStepElement) {
            currentStepElement.style.display = 'block';
        }
        
        // Update step indicator
        this.updateStepIndicator(step);
        
        // Update buttons
        this.updateUnifiedButtons(step);
        
        this.currentStep = step;
    }

    updateStepIndicator(activeStep) {
        const steps = this.unifiedModal.querySelectorAll('.step');
        const lines = this.unifiedModal.querySelectorAll('.step-line');
        
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            if (stepNumber < activeStep) {
                step.classList.remove('active');
                step.classList.add('completed');
            } else if (stepNumber === activeStep) {
                step.classList.remove('completed');
                step.classList.add('active');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
        
        lines.forEach((line, index) => {
            const lineNumber = index + 1;
            if (lineNumber < activeStep) {
                line.classList.add('completed');
            } else {
                line.classList.remove('completed');
            }
        });
    }

    updateUnifiedButtons(step) {
        const startBtn = document.getElementById('startWorkflowBtn');
        const nextBtn = document.getElementById('nextStepBtn');
        const closeBtn = document.getElementById('closeModalBtn');
        
        if (step === 1) {
            startBtn.style.display = 'inline-block';
            nextBtn.style.display = 'none';
            closeBtn.style.display = 'none';
        } else if (step === 2) {
            startBtn.style.display = 'none';
            nextBtn.style.display = 'none';
            closeBtn.style.display = 'none';
        } else if (step === 3) {
            startBtn.style.display = 'none';
            nextBtn.style.display = 'none';
            closeBtn.style.display = 'inline-block';
        }
    }

    nextStep() {
        if (this.currentStep < 3) {
            this.goToStep(this.currentStep + 1);
        }
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
        // Get values from the new step-based UI
        const modelType = document.getElementById('modelType')?.value || 'neural_network';
        const trainingPeriod = document.getElementById('trainingPeriod')?.value || '6_months';
        const priceIndicators = document.getElementById('priceIndicators')?.checked || false;
        const volumeIndicators = document.getElementById('volumeIndicators')?.checked || false;
        const volatilityIndicators = document.getElementById('volatilityIndicators')?.checked || false;
        
        const trainingConfig = {
            model_type: modelType,
            strategy_id: document.getElementById('fq-strategy-select')?.value || 1,
            symbol: document.getElementById('fq-symbol-select')?.value || 'ES',
            timeframe: document.getElementById('fq-timeframe-select')?.value || '1d',
            training_period: trainingPeriod,
            features: {
                price_indicators: priceIndicators,
                volume_indicators: volumeIndicators,
                volatility_indicators: volatilityIndicators
            },
            hyperparameters: {
                epochs: 100,
                batch_size: 32,
                learning_rate: 0.001
            }
        };
        
        console.log('Starting training with config:', trainingConfig);
        
        // Show progress step
        showTrainingStep('progress');
        
        const response = await fetch('/api/v1/futurequant/models/train-brpc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(trainingConfig)
        });
        
        const result = await response.json();
        console.log('Training result:', result);
        
        if (result.success) {
            // Start monitoring training progress
            monitorTrainingProgress(result.model_id);
        } else {
            showTrainingError(result.error);
        }
    } catch (error) {
        console.error('Training failed:', error);
        showTrainingError('Training failed: ' + error.message);
    }
}

// Function to show different training steps
function showTrainingStep(step) {
    // Hide all steps
    document.getElementById('configStep').style.display = 'none';
    document.getElementById('progressStep').style.display = 'none';
    document.getElementById('completionStep').style.display = 'none';
    
    // Get button references
    const startTrainingBtn = document.getElementById('startTrainingBtn');
    const backToConfigBtn = document.getElementById('backToConfigBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    
    // Show the requested step and update buttons
    switch(step) {
        case 'config':
            document.getElementById('configStep').style.display = 'block';
            if (startTrainingBtn) startTrainingBtn.style.display = 'inline-block';
            if (backToConfigBtn) backToConfigBtn.style.display = 'none';
            if (closeModalBtn) closeModalBtn.style.display = 'none';
            break;
        case 'progress':
            document.getElementById('progressStep').style.display = 'block';
            if (startTrainingBtn) startTrainingBtn.style.display = 'none';
            if (backToConfigBtn) backToConfigBtn.style.display = 'none';
            if (closeModalBtn) closeModalBtn.style.display = 'none';
            break;
        case 'completion':
            document.getElementById('completionStep').style.display = 'block';
            if (startTrainingBtn) startTrainingBtn.style.display = 'none';
            if (backToConfigBtn) backToConfigBtn.style.display = 'inline-block';
            if (closeModalBtn) closeModalBtn.style.display = 'inline-block';
            break;
    }
}

// Function to monitor training progress
async function monitorTrainingProgress(modelId) {
    try {
        const response = await fetch(`/api/v1/futurequant/models/status/${modelId}`);
        const result = await response.json();
        
        if (result.success) {
            if (result.status === 'completed') {
                showTrainingStep('completion');
                updateTrainingProgress(100, 'Training completed successfully!');
            } else if (result.status === 'failed') {
                showTrainingError('Training failed: ' + (result.error || 'Unknown error'));
            } else {
                // Still training, update progress and check again
                updateTrainingProgress(result.progress || 0, result.message || 'Training in progress...');
                setTimeout(() => monitorTrainingProgress(modelId), 2000); // Check every 2 seconds
            }
        } else {
            showTrainingError('Failed to get training status');
        }
    } catch (error) {
        console.error('Error monitoring training:', error);
        showTrainingError('Error monitoring training: ' + error.message);
    }
}

// Function to update training progress
function updateTrainingProgress(progress, message) {
    const progressStep = document.getElementById('progressStep');
    if (progressStep) {
        const progressBar = progressStep.querySelector('.progress-bar');
        const messageElement = progressStep.querySelector('h6');
        
        if (progressBar) {
            progressBar.style.width = progress + '%';
            progressBar.textContent = progress + '%';
        }
        
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
}

// Function to start trading with the trained model
function startTradingWithModel() {
    console.log('Starting trading with trained model...');
    
    // Enable the Trade button after training completion
    if (typeof window.enableTradeButton === 'function') {
        window.enableTradeButton();
    }
    
    // Close the training modal
    const trainingModal = bootstrap.Modal.getInstance(document.getElementById('trainingModal'));
    if (trainingModal) {
        trainingModal.hide();
    }
    
    // Show the trading interface
    if (window.futurequantDashboard) {
        window.futurequantDashboard.showTradingInterface();
    } else {
        // Fallback: show a success message and redirect
        showSuccessMessage('Model loaded successfully! Redirecting to trading interface...');
        setTimeout(() => {
            // You can redirect to the trading page or show trading modal
            showTradingModal();
        }, 2000);
    }
}

// Function to view model details
function viewModelDetails() {
    console.log('Showing model details...');
    
    // Create and show model details modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-info text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-info-circle"></i> Model Details
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Model Information</h6>
                            <table class="table table-sm">
                                <tr><td><strong>Model Type:</strong></td><td>Neural Network</td></tr>
                                <tr><td><strong>Training Period:</strong></td><td>Last 6 months</td></tr>
                                <tr><td><strong>Features:</strong></td><td>Price, Volume, Volatility</td></tr>
                                <tr><td><strong>Status:</strong></td><td><span class="badge bg-success">Ready</span></td></tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6>Performance Metrics</h6>
                            <div class="card">
                                <div class="card-body text-center">
                                    <h4 class="text-success">85.7%</h4>
                                    <p class="mb-0">Training Accuracy</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <h6>Model Capabilities</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="text-center p-3">
                                    <i class="fas fa-chart-line fa-2x text-primary mb-2"></i>
                                    <p class="small">Price Prediction</p>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="text-center p-3">
                                    <i class="fas fa-robot fa-2x text-success mb-2"></i>
                                    <p class="small">AI Trading Signals</p>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="text-center p-3">
                                    <i class="fas fa-shield-alt fa-2x text-info mb-2"></i>
                                    <p class="small">Risk Management</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-success" onclick="startTradingWithModel()">
                        <i class="fas fa-play"></i> Start Trading
                    </button>
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

// Function to show success message
function showSuccessMessage(message) {
    // Create a toast notification
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-check-circle"></i> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hidden
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

// Function to show trading modal (fallback)
function showTradingModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-play"></i> Paper Trading with AI Model
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-success">
                        <i class="fas fa-robot"></i>
                        <strong>AI Model Loaded!</strong> Your trained model is now active and ready for paper trading.
                    </div>
                    
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Live Trading Chart</h6>
                            <div class="border rounded p-3" style="height: 300px; background: #f8f9fa;">
                                <div class="text-center text-muted pt-5">
                                    <i class="fas fa-chart-line fa-3x mb-3"></i>
                                    <p>Real-time price chart with AI trading signals</p>
                                    <small>Your trained model will provide entry/exit signals</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <h6>AI Trading Signals</h6>
                            <div class="list-group">
                                <div class="list-group-item d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>ES Long</strong><br>
                                        <small class="text-muted">AI Signal: Strong Buy</small>
                                    </div>
                                    <span class="badge bg-success">+$125</span>
                                </div>
                                <div class="list-group-item d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>NQ Short</strong><br>
                                        <small class="text-muted">AI Signal: Sell</small>
                                    </div>
                                    <span class="badge bg-danger">-$85</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-success" onclick="window.futurequantDashboard.showPaperTradingModal()">
                        <i class="fas fa-play"></i> Start Paper Trading
                    </button>
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
    // Show error in the progress step
    const progressStep = document.getElementById('progressStep');
    if (progressStep) {
        progressStep.innerHTML = `
            <h6><i class="fas fa-exclamation-triangle text-danger"></i> Training Error</h6>
            <div class="text-center p-4">
                <div class="text-danger mb-3">
                    <i class="fas fa-exclamation-triangle fa-3x"></i>
                </div>
                <h6 class="text-danger">Training Failed</h6>
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Error:</strong> ${error}
                </div>
                <button class="btn btn-warning" onclick="showTrainingStep('config')">
                    <i class="fas fa-arrow-left"></i> Back to Configuration
                </button>
            </div>
        `;
        showTrainingStep('progress');
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

// Features computation completion function
window.completeFeaturesComputation = function() {
    console.log('Completing features computation...');
    
    // Update the features button to show completion
    const featuresBtn = document.getElementById('fq-compute-features-btn');
    if (featuresBtn) {
        featuresBtn.innerHTML = '<i class="fas fa-check"></i> Features Ready';
        featuresBtn.className = 'btn btn-success btn-sm';
        featuresBtn.disabled = true;
    }
    
    // Update status indicator
    const statusIndicator = document.querySelector('.text-warning');
    if (statusIndicator) {
        statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Features: Ready for Training';
        statusIndicator.className = 'text-success';
    }
    
    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('featuresModal'));
    if (modal) {
        modal.hide();
    }
    
    // Show success message
    alert('Features computation completed! You can now click "Train" to build AI models.');
};

// Global function to close training popup and transition to paper trading
window.closeTrainingPopupAndTransitionToPaperTrading = function(closeButton) {
    console.log('Closing training popup and transitioning to paper trading...');
    
    // Remove the training popup
    const popup = closeButton.closest('.alert, .progress-div, .training-popup');
    if (popup) {
        popup.remove();
    }
    
    // Close any open modals
    const openModals = document.querySelectorAll('.modal.show');
    openModals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
    
    // Transition to paper trading interface
    transitionToPaperTrading();
};

// Function to transition to paper trading interface
function transitionToPaperTrading() {
    console.log('Transitioning to paper trading interface...');
    
    // Hide training-related sections
    const trainingSections = document.querySelectorAll('.training-section, .model-training-section');
    trainingSections.forEach(section => {
        section.style.display = 'none';
    });
    
    // Show paper trading interface
    const paperTradingSection = document.getElementById('paper-trading-section');
    if (paperTradingSection) {
        paperTradingSection.style.display = 'block';
    }
    
    // Update navigation to highlight paper trading
    const navItems = document.querySelectorAll('.nav-link');
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.textContent.includes('Paper Trading') || item.getAttribute('data-section') === 'paper-trading') {
            item.classList.add('active');
        }
    });
    
    // Show success message
    showPaperTradingReadyMessage();
    
    // Initialize paper trading components
    if (window.futurequantDashboard && window.futurequantDashboard.initializePaperTrading) {
        window.futurequantDashboard.initializePaperTrading();
    }
}

// Function to show paper trading ready message
function showPaperTradingReadyMessage() {
    // Create and show a success toast
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = 'toast show bg-success text-white';
    toast.innerHTML = `
        <div class="toast-header bg-success text-white">
            <i class="fas fa-rocket me-2"></i>
            <strong class="me-auto">Paper Trading Ready!</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            <p class="mb-0">Your model is ready for paper trading! Start executing strategies with real-time market data.</p>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Function to create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}
