console.log('FutureQuant Dashboard loaded - Distributional Futures Trading Platform');

class FutureQuantDashboard {
    constructor() {
        this.currentSymbol = 'ES';
        this.currentTimeframe = '1d';
        this.activeSession = null;
        this.websocket = null;
        this.charts = {};
        this.dataCache = {};
        
        this.init();
    }

    init() {
        console.log('Initializing FutureQuant Dashboard...');
        this.setupEventListeners();
        this.loadInitialData();
        this.initializeCharts();
        this.startDataRefresh();
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
            strategySelect.addEventListener('change', (e) => {
                this.loadStrategyData(e.target.value);
            });
        }

        // Model training
        const trainModelBtn = document.getElementById('fq-train-model-btn');
        if (trainModelBtn) {
            trainModelBtn.addEventListener('click', () => this.showModelTrainingModal());
        }

        // Backtest button
        const backtestBtn = document.getElementById('fq-backtest-btn');
        if (backtestBtn) {
            backtestBtn.addEventListener('click', () => this.runBacktest());
        }

        // Paper trading
        const startPaperTradingBtn = document.getElementById('fq-start-paper-trading-btn');
        if (startPaperTradingBtn) {
            startPaperTradingBtn.addEventListener('click', () => this.startPaperTrading());
        }

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
            await this.loadSymbols();
            
            // Load strategies
            await this.loadStrategies();
            
            // Load models
            await this.loadModels();
            
            // Load recent backtests
            await this.loadRecentBacktests();
            
            // Load paper trading sessions
            await this.loadPaperTradingSessions();
            
            // Load recent signals
            await this.loadRecentSignals();
            
            // Load job statuses
            await this.loadJobStatuses();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data', 'error');
        }
    }

    async loadSymbols() {
        try {
            const response = await fetch('/api/v1/futurequant/symbols');
            const data = await response.json();
            
            if (data.success && data.symbols) {
                const symbolSelect = document.getElementById('fq-symbol-select');
                if (symbolSelect) {
                    symbolSelect.innerHTML = '<option value="">Select Symbol</option>';
                    data.symbols.forEach(symbol => {
                        symbolSelect.innerHTML += `<option value="${symbol.ticker}">${symbol.ticker} - ${symbol.name}</option>`;
                    });
                }
                
                // Set default symbol
                if (data.symbols.length > 0) {
                    this.currentSymbol = data.symbols[0].ticker;
                    symbolSelect.value = this.currentSymbol;
                }
            }
        } catch (error) {
            console.error('Error loading symbols:', error);
        }
    }

    async loadStrategies() {
        try {
            const response = await fetch('/api/v1/futurequant/signals/strategies');
            const data = await response.json();
            
            if (data.success && data.strategies) {
                const strategySelect = document.getElementById('fq-strategy-select');
                if (strategySelect) {
                    strategySelect.innerHTML = '<option value="">Select Strategy</option>';
                    data.strategies.forEach(strategy => {
                        strategySelect.innerHTML += `<option value="${strategy.id}">${strategy.name}</option>`;
                    });
                }
            }
        } catch (error) {
            console.error('Error loading strategies:', error);
        }
    }

    async loadModels() {
        try {
            const response = await fetch('/api/v1/futurequant/models/types');
            const data = await response.json();
            
            if (data.success && data.model_types) {
                this.updateModelTypesDisplay(data.model_types);
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }

    async loadRecentBacktests() {
        try {
            const response = await fetch('/api/v1/futurequant/backtests/config');
            const data = await response.json();
            
            if (data.success) {
                this.updateBacktestConfigDisplay(data.config);
            }
        } catch (error) {
            console.error('Error loading backtests:', error);
        }
    }

    async loadPaperTradingSessions() {
        try {
            const response = await fetch('/api/v1/futurequant/paper-trading/sessions');
            const data = await response.json();
            
            if (data.success) {
                this.updatePaperTradingDisplay(data.active_sessions);
            }
        } catch (error) {
            console.error('Error loading paper trading sessions:', error);
        }
    }

    async loadRecentSignals() {
        try {
            const response = await fetch('/api/v1/futurequant/signals/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    strategy_id: 1,
                    start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                    end_date: new Date().toISOString().split('T')[0]
                })
            });
            const data = await response.json();
            
            if (data.success) {
                this.updateSignalsDisplay(data.signals);
            }
        } catch (error) {
            console.error('Error loading signals:', error);
        }
    }

    async loadJobStatuses() {
        try {
            // This would typically come from a jobs endpoint
            const mockJobs = [
                { id: 1, type: 'data_ingestion', status: 'completed', progress: 100 },
                { id: 2, type: 'feature_computation', status: 'running', progress: 65 },
                { id: 3, type: 'model_training', status: 'queued', progress: 0 }
            ];
            
            this.updateJobStatusDisplay(mockJobs);
        } catch (error) {
            console.error('Error loading job statuses:', error);
        }
    }

    async loadSymbolData() {
        if (!this.currentSymbol) return;
        
        try {
            // Load latest data
            const response = await fetch(`/api/v1/futurequant/symbols/${this.currentSymbol}/latest`);
            const data = await response.json();
            
            if (data.success) {
                this.updatePriceChart(data.data);
                this.updateMarketDataDisplay(data.data);
            }
        } catch (error) {
            console.error('Error loading symbol data:', error);
        }
    }

    async loadStrategyData(strategyId) {
        if (!strategyId) return;
        
        try {
            const response = await fetch(`/api/v1/futurequant/signals/strategies/${strategyId}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStrategyDisplay(data.strategy);
            }
        } catch (error) {
            console.error('Error loading strategy data:', error);
        }
    }

    initializeCharts() {
        // Initialize price chart
        this.initializePriceChart();
        
        // Initialize performance chart
        this.initializePerformanceChart();
        
        // Initialize distribution chart
        this.initializeDistributionChart();
    }

    initializePriceChart() {
        const chartContainer = document.getElementById('fq-price-chart');
        if (!chartContainer) return;
        
        // Create a simple price chart using Chart.js
        const ctx = chartContainer.getContext('2d');
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
                responsive: true,
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
    }

    initializePerformanceChart() {
        const chartContainer = document.getElementById('fq-performance-chart');
        if (!chartContainer) return;
        
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
                responsive: true,
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
    }

    initializeDistributionChart() {
        const chartContainer = document.getElementById('fq-distribution-chart');
        if (!chartContainer) return;
        
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
                responsive: true,
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

    updatePriceChart(data) {
        if (!this.charts.price || !data) return;
        
        const chart = this.charts.price;
        chart.data.labels = data.map(d => d.timestamp);
        chart.data.datasets[0].data = data.map(d => d.close);
        chart.update();
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

    updateMarketDataDisplay(data) {
        if (!data || data.length === 0) return;
        
        const latest = data[data.length - 1];
        
        // Update price display
        const priceElement = document.getElementById('fq-current-price');
        if (priceElement) {
            priceElement.textContent = `$${latest.close.toFixed(2)}`;
        }
        
        // Update change display
        const changeElement = document.getElementById('fq-price-change');
        if (changeElement && data.length > 1) {
            const change = latest.close - data[data.length - 2].close;
            const changePercent = (change / data[data.length - 2].close) * 100;
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
            changeElement.className = change >= 0 ? 'text-success' : 'text-danger';
        }
        
        // Update volume display
        const volumeElement = document.getElementById('fq-volume');
        if (volumeElement) {
            volumeElement.textContent = latest.volume.toLocaleString();
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
        const container = document.getElementById('fq-strategy-details');
        if (!container) return;
        
        container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">${strategy.name}</h6>
                    <p class="card-text small">${strategy.description}</p>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Parameters</h6>
                            <ul class="list-unstyled small">
                                <li><strong>Min Probability:</strong> ${(strategy.params.min_prob * 100).toFixed(0)}%</li>
                                <li><strong>Risk Budget:</strong> ${(strategy.params.risk_budget * 100).toFixed(1)}%</li>
                                <li><strong>Max Leverage:</strong> ${strategy.params.max_leverage}x</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Constraints</h6>
                            <ul class="list-unstyled small">
                                <li><strong>Daily Loss Limit:</strong> ${(strategy.params.max_daily_loss * 100).toFixed(1)}%</li>
                                <li><strong>Max Drawdown:</strong> ${(strategy.params.max_drawdown * 100).toFixed(1)}%</li>
                                <li><strong>Cooldown:</strong> ${strategy.params.cooldown_after_stop} days</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showModelTrainingModal() {
        // Create and show modal for model training
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'modelTrainingModal';
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
                                        <select class="form-select" id="modelType">
                                            <option value="transformer">Transformer Encoder (FQT-lite)</option>
                                            <option value="quantile_regression">Quantile Regression</option>
                                            <option value="random_forest">Random Forest Quantiles</option>
                                            <option value="neural_network">Neural Network</option>
                                            <option value="gradient_boosting">Gradient Boosting</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Symbols</label>
                                        <select class="form-select" id="modelSymbols" multiple>
                                            <option value="ES">ES (E-mini S&P 500)</option>
                                            <option value="NQ">NQ (E-mini NASDAQ)</option>
                                            <option value="YM">YM (E-mini Dow)</option>
                                            <option value="RTY">RTY (E-mini Russell)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Training Period</label>
                                        <select class="form-select" id="trainingPeriod">
                                            <option value="1y">1 Year</option>
                                            <option value="2y">2 Years</option>
                                            <option value="5y">5 Years</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Horizon (minutes)</label>
                                        <select class="form-select" id="modelHorizon">
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
                                <textarea class="form-control" id="modelHyperparams" rows="4" placeholder='{"learning_rate": 0.001, "batch_size": 32}'></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="futurequantDashboard.trainModel()">Start Training</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Clean up modal when hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    async trainModel(modelType = null) {
        try {
            const form = document.getElementById('modelTrainingForm');
            const formData = new FormData(form);
            
            const trainingData = {
                model_type: modelType || formData.get('modelType'),
                symbols: Array.from(document.getElementById('modelSymbols').selectedOptions).map(opt => opt.value),
                training_period: formData.get('trainingPeriod'),
                horizon_minutes: parseInt(formData.get('modelHorizon')),
                hyperparams: JSON.parse(formData.get('modelHyperparams') || '{}')
            };
            
            const response = await fetch('/api/v1/futurequant/models/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trainingData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Model training started successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('modelTrainingModal')).hide();
                this.loadModels(); // Refresh model list
            } else {
                this.showNotification(`Training failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error training model:', error);
            this.showNotification('Error starting model training', 'error');
        }
    }

    async runBacktest() {
        try {
            const strategyId = document.getElementById('fq-strategy-select').value;
            if (!strategyId) {
                this.showNotification('Please select a strategy first', 'warning');
                return;
            }
            
            const backtestData = {
                strategy_id: parseInt(strategyId),
                start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                end_date: new Date().toISOString().split('T')[0],
                config_name: 'moderate'
            };
            
            const response = await fetch('/api/v1/futurequant/backtests/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(backtestData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Backtest started successfully', 'success');
                this.loadRecentBacktests(); // Refresh backtest list
            } else {
                this.showNotification(`Backtest failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error running backtest:', error);
            this.showNotification('Error starting backtest', 'error');
        }
    }

    async startPaperTrading() {
        try {
            const strategyId = document.getElementById('fq-strategy-select').value;
            if (!strategyId) {
                this.showNotification('Please select a strategy first', 'warning');
                return;
            }
            
            const sessionData = {
                user_id: 1, // Mock user ID
                strategy_id: parseInt(strategyId),
                initial_capital: 100000,
                symbols: [this.currentSymbol]
            };
            
            const response = await fetch('/api/v1/futurequant/paper-trading/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sessionData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.activeSession = result.session_id;
                this.showNotification('Paper trading session started', 'success');
                this.loadPaperTradingSessions(); // Refresh sessions
                this.startWebSocketConnection();
            } else {
                this.showNotification(`Failed to start session: ${result.error}`, 'error');
            }
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
            
            const response = await fetch(`/api/v1/futurequant/paper-trading/stop/${targetSession}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (sessionId === this.activeSession) {
                    this.activeSession = null;
                    this.stopWebSocketConnection();
                }
                this.showNotification('Paper trading session stopped', 'success');
                this.loadPaperTradingSessions(); // Refresh sessions
            } else {
                this.showNotification(`Failed to stop session: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error stopping paper trading:', error);
            this.showNotification('Error stopping paper trading session', 'error');
        }
    }

    async ingestData() {
        try {
            const symbols = [this.currentSymbol];
            if (!symbols.length) {
                this.showNotification('Please select symbols to ingest', 'warning');
                return;
            }
            
            const response = await fetch('/api/v1/futurequant/data/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbols })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Data ingestion started successfully', 'success');
            } else {
                this.showNotification(`Data ingestion failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error ingesting data:', error);
            this.showNotification('Error starting data ingestion', 'error');
        }
    }

    async computeFeatures() {
        try {
            const symbolId = 1; // Mock symbol ID - would need to get from symbol lookup
            
            const response = await fetch('/api/v1/futurequant/features/compute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol_id: symbolId,
                    recipe_name: 'full'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Feature computation started successfully', 'success');
            } else {
                this.showNotification(`Feature computation failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error computing features:', error);
            this.showNotification('Error starting feature computation', 'error');
        }
    }

    startWebSocketConnection() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Mock WebSocket connection for paper trading updates
        this.websocket = {
            send: (data) => console.log('WebSocket send:', data),
            close: () => console.log('WebSocket closed')
        };
        
        // Simulate real-time updates
        this.websocketInterval = setInterval(() => {
            this.updatePaperTradingData();
        }, 5000);
    }

    stopWebSocketConnection() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        if (this.websocketInterval) {
            clearInterval(this.websocketInterval);
            this.websocketInterval = null;
        }
    }

    updatePaperTradingData() {
        // Simulate real-time position updates
        if (this.activeSession) {
            // Update performance chart with mock data
            const mockData = Array.from({ length: 20 }, (_, i) => ({
                date: new Date(Date.now() - (19 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                value: 100000 + Math.random() * 10000
            }));
            
            this.updatePerformanceChart(mockData);
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
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart !== 'undefined') {
        window.futurequantDashboard = new FutureQuantDashboard();
    } else {
        console.warn('Chart.js not loaded, dashboard initialization delayed');
        // Wait for Chart.js to load
        const checkChart = setInterval(() => {
            if (typeof Chart !== 'undefined') {
                clearInterval(checkChart);
                window.futurequantDashboard = new FutureQuantDashboard();
            }
        }, 100);
    }
});

// Export for global access
window.FutureQuantDashboard = FutureQuantDashboard;
