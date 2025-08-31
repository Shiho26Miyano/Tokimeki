console.log('FutureQuant Enhanced Dashboard loaded - Bloomberg-Style Trading Platform - Version 20250117');

class FutureQuantEnhancedDashboard {
    constructor() {
        console.log('FutureQuantEnhancedDashboard constructor called');
        
        // Configuration
        this.config = {
            apiBaseUrl: '/api/v1',
            wsBaseUrl: 'ws://localhost:8000/ws',
            refreshInterval: 5000,
            maxRetries: 3,
            retryDelay: 1000,
            enableMockMode: true,
            enableHotkeys: true,
            enableNotifications: true,
            enableDraggablePanels: true
        };
        
        // State management
        this.state = {
            currentSymbol: localStorage.getItem('fq_symbol') || 'ES=F',
            currentTimeframe: localStorage.getItem('fq_timeframe') || '1d',
            currentStrategy: localStorage.getItem('fq_strategy') || null,
            isMockMode: false,
            isConnected: false,
            lastUpdate: null
        };
        
        // Data stores
        this.data = {
            symbols: [],
            strategies: [],
            models: [],
            backtests: [],
            trades: [],
            jobs: [],
            watchlist: []
        };
        
        // UI components
        this.components = {
            charts: {},
            panels: {},
            modals: {},
            notifications: null
        };
        
        // WebSocket connection
        this.ws = null;
        
        // Mock data fallback
        this.mockData = this.initializeMockData();
        
        this.init();
    }
    
    initializeMockData() {
        return {
            symbols: [
                { ticker: 'ES=F', name: 'E-mini S&P 500', price: 4850.25, change: 12.50, changePercent: 0.26, volume: 1250000, bid: 4849.75, ask: 4850.50 },
                { ticker: 'NQ=F', name: 'E-mini NASDAQ', price: 16850.75, change: -45.25, changePercent: -0.27, volume: 890000, bid: 16850.25, ask: 16851.25 },
                { ticker: 'YM=F', name: 'E-mini Dow', price: 38500.50, change: 125.00, changePercent: 0.33, volume: 450000, bid: 38499.75, ask: 38501.25 },
                { ticker: 'RTY=F', name: 'E-mini Russell', price: 2150.25, change: 8.75, changePercent: 0.41, volume: 320000, bid: 2149.75, ask: 2150.75 },
                { ticker: 'CL=F', name: 'Crude Oil', price: 78.45, change: -1.20, changePercent: -1.51, volume: 280000, bid: 78.40, ask: 78.50 },
                { ticker: 'GC=F', name: 'Gold', price: 2050.80, change: 15.60, changePercent: 0.77, volume: 180000, bid: 2050.50, ask: 2051.10 }
            ],
            strategies: [
                { id: 1, name: 'Conservative Momentum', description: 'Low-risk momentum strategy with tight stops', risk: 'Low', expectedReturn: '8-12%', maxDrawdown: '5%', type: 'momentum' },
                { id: 2, name: 'Moderate Trend Following', description: 'Balanced trend following with moderate risk', risk: 'Medium', expectedReturn: '15-20%', maxDrawdown: '12%', type: 'trend_following' },
                { id: 3, name: 'Aggressive Mean Reversion', description: 'High-risk mean reversion with wide stops', risk: 'High', expectedReturn: '25-35%', maxDrawdown: '20%', type: 'mean_reversion' },
                { id: 4, name: 'Volatility Breakout', description: 'Volatility-based breakout strategy', risk: 'Medium-High', expectedReturn: '18-25%', maxDrawdown: '15%', type: 'statistical_arbitrage' },
                { id: 5, name: 'Statistical Arbitrage', description: 'Pairs trading with statistical edge', risk: 'Low-Medium', expectedReturn: '10-15%', maxDrawdown: '8%', type: 'statistical_arbitrage' }
            ],
            models: [
                { id: 1, name: 'Transformer Encoder (FQT-lite)', description: 'Lightweight transformer for quick predictions', accuracy: '78%', trainingTime: '2-4 hours', status: 'trained' },
                { id: 2, name: 'Quantile Regression', description: 'Distributional forecasting model', accuracy: '82%', trainingTime: '1-2 hours', status: 'trained' },
                { id: 3, name: 'Random Forest Quantiles', description: 'Ensemble method for robust predictions', accuracy: '75%', trainingTime: '30-60 min', status: 'training' },
                { id: 4, name: 'Neural Network', description: 'Deep learning for complex patterns', accuracy: '85%', trainingTime: '4-8 hours', status: 'trained' },
                { id: 5, name: 'Gradient Boosting', description: 'Advanced boosting for high accuracy', accuracy: '80%', trainingTime: '2-3 hours', status: 'pending' }
            ]
        };
    }
    
    async init() {
        console.log('Initializing FutureQuant Enhanced Dashboard...');
        
        try {
            // Initialize UI components
            this.initializeUI();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Setup hotkeys
            if (this.config.enableHotkeys) {
                this.setupHotkeys();
            }
            
            // Initialize notifications
            if (this.config.enableNotifications) {
                this.initializeNotifications();
            }
            
            // Setup draggable panels
            if (this.config.enableDraggablePanels) {
                this.initializeDraggablePanels();
            }
            
            // Load initial data
            await this.loadInitialData();
            
            // Initialize charts
            this.initializeCharts();
            
            // Setup WebSocket connection
            this.setupWebSocket();
            
            // Start data refresh
            this.startDataRefresh();
            
            // Load user preferences
            this.loadUserPreferences();
            
            console.log('Enhanced Dashboard initialization complete');
            
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showNotification('Dashboard initialization failed', 'error');
        }
    }
    
    initializeUI() {
        // Create Bloomberg-style layout
        this.createDashboardLayout();
        
        // Initialize panels
        this.initializePanels();
        
        // Setup dark theme
        this.setupDarkTheme();
    }
    
    createDashboardLayout() {
        const dashboard = document.getElementById('futurequant-dashboard');
        if (!dashboard) return;
        
        // Clear existing content
        dashboard.innerHTML = '';
        
        // Create grid layout
        dashboard.className = 'dashboard-grid bloomberg-theme';
        dashboard.innerHTML = `
            <!-- Header Panel -->
            <div class="panel header-panel" data-panel="header">
                <div class="panel-header">
                    <h1>FutureQuant Trading Terminal</h1>
                    <div class="header-controls">
                        <div class="symbol-search">
                            <input type="text" id="symbol-search" placeholder="Symbol (S)" class="form-control">
                            <button id="symbol-search-btn" class="btn btn-primary">Search</button>
                        </div>
                        <div class="timeframe-selector">
                            <select id="timeframe-select" class="form-control">
                                <option value="1m">1m</option>
                                <option value="5m">5m</option>
                                <option value="15m">15m</option>
                                <option value="1h">1h</option>
                                <option value="1d">1d</option>
                            </select>
                        </div>
                        <div class="connection-status">
                            <span id="connection-indicator" class="status-indicator"></span>
                            <span id="connection-text">Connecting...</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Market Overview Panel -->
            <div class="panel market-panel" data-panel="market">
                <div class="panel-header">
                    <h3>Market Overview</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="refresh-market">↻</button>
                        <button class="btn btn-sm btn-outline" id="add-watchlist">+</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div class="market-ticker-table">
                        <table class="table table-dark table-sm">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Price</th>
                                    <th>Change</th>
                                    <th>Volume</th>
                                    <th>Bid/Ask</th>
                                </tr>
                            </thead>
                            <tbody id="market-ticker-body">
                                <!-- Market data will be populated here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Price Chart Panel -->
            <div class="panel chart-panel" data-panel="price-chart">
                <div class="panel-header">
                    <h3>Price Chart</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="chart-fullscreen">⛶</button>
                        <button class="btn btn-sm btn-outline" id="chart-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="price-chart-container" class="chart-container"></div>
                </div>
            </div>
            
            <!-- Distribution Chart Panel -->
            <div class="panel chart-panel" data-panel="distribution-chart">
                <div class="panel-header">
                    <h3>Distribution Forecast</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="dist-fullscreen">⛶</button>
                        <button class="btn btn-sm btn-outline" id="dist-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="distribution-chart-container" class="chart-container"></div>
                </div>
            </div>
            
            <!-- Performance Chart Panel -->
            <div class="panel chart-panel" data-panel="performance-chart">
                <div class="panel-header">
                    <h3>Performance</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="perf-fullscreen">⛶</button>
                        <button class="btn btn-sm btn-outline" id="perf-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="performance-chart-container" class="chart-container"></div>
                </div>
            </div>
            
            <!-- Strategies Panel -->
            <div class="panel strategies-panel" data-panel="strategies">
                <div class="panel-header">
                    <h3>Strategies</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="new-strategy">+</button>
                        <button class="btn btn-sm btn-outline" id="strategy-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div class="strategy-selector">
                        <select id="strategy-select" class="form-control">
                            <option value="">Select Strategy</option>
                        </select>
                    </div>
                    <div id="strategy-details" class="strategy-details">
                        <!-- Strategy details will be populated here -->
                    </div>
                    <div class="strategy-actions">
                        <button id="run-backtest-btn" class="btn btn-primary">Run Backtest (B)</button>
                        <button id="paper-trade-btn" class="btn btn-success">Paper Trade (T)</button>
                    </div>
                </div>
            </div>
            
            <!-- Models Panel -->
            <div class="panel models-panel" data-panel="models">
                <div class="panel-header">
                    <h3>ML Models</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="train-model">Train</button>
                        <button class="btn btn-sm btn-outline" id="model-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="models-list" class="models-list">
                        <!-- Models will be populated here -->
                    </div>
                </div>
            </div>
            
            <!-- Trade Monitor Panel -->
            <div class="panel trade-panel" data-panel="trade-monitor">
                <div class="panel-header">
                    <h3>Trade Monitor</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="refresh-trades">↻</button>
                        <button class="btn btn-sm btn-outline" id="trade-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div class="trade-tabs">
                        <ul class="nav nav-tabs" role="tablist">
                            <li class="nav-item">
                                <a class="nav-link active" data-toggle="tab" href="#open-positions">Open Positions</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" data-toggle="tab" href="#recent-trades">Recent Trades</a>
                            </li>
                        </ul>
                        <div class="tab-content">
                            <div id="open-positions" class="tab-pane active">
                                <div id="positions-list" class="positions-list">
                                    <!-- Open positions will be populated here -->
                                </div>
                            </div>
                            <div id="recent-trades" class="tab-pane">
                                <div id="trades-list" class="trades-list">
                                    <!-- Recent trades will be populated here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Jobs Panel -->
            <div class="panel jobs-panel" data-panel="jobs">
                <div class="panel-header">
                    <h3>Job Status</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="refresh-jobs">↻</button>
                        <button class="btn btn-sm btn-outline" id="job-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="jobs-list" class="jobs-list">
                        <!-- Jobs will be populated here -->
                    </div>
                </div>
            </div>
            
            <!-- Notifications Panel -->
            <div class="panel notifications-panel" data-panel="notifications">
                <div class="panel-header">
                    <h3>Notifications</h3>
                    <div class="panel-controls">
                        <button class="btn btn-sm btn-outline" id="clear-notifications">Clear</button>
                        <button class="btn btn-sm btn-outline" id="notification-settings">⚙</button>
                    </div>
                </div>
                <div class="panel-content">
                    <div id="notifications-list" class="notifications-list">
                        <!-- Notifications will be populated here -->
                    </div>
                </div>
            </div>
        `;
    }
    
    initializePanels() {
        // Initialize each panel with its functionality
        this.components.panels = {
            header: document.querySelector('[data-panel="header"]'),
            market: document.querySelector('[data-panel="market"]'),
            priceChart: document.querySelector('[data-panel="price-chart"]'),
            distributionChart: document.querySelector('[data-panel="distribution-chart"]'),
            performanceChart: document.querySelector('[data-panel="performance-chart"]'),
            strategies: document.querySelector('[data-panel="strategies"]'),
            models: document.querySelector('[data-panel="models"]'),
            tradeMonitor: document.querySelector('[data-panel="trade-monitor"]'),
            jobs: document.querySelector('[data-panel="jobs"]'),
            notifications: document.querySelector('[data-panel="notifications"]')
        };
    }
    
    setupDarkTheme() {
        // Add Bloomberg-style dark theme CSS
        const style = document.createElement('style');
        style.textContent = `
            .bloomberg-theme {
                --bg-primary: #1a1a1a;
                --bg-secondary: #2d2d2d;
                --bg-tertiary: #404040;
                --text-primary: #ffffff;
                --text-secondary: #cccccc;
                --text-muted: #888888;
                --accent-primary: #00d4aa;
                --accent-secondary: #ff6b35;
                --accent-warning: #ffd700;
                --accent-danger: #ff4757;
                --accent-success: #2ed573;
                --border-color: #404040;
                --shadow-color: rgba(0, 0, 0, 0.5);
            }
            
            .dashboard-grid {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                grid-template-rows: auto 1fr 1fr 1fr;
                gap: 8px;
                padding: 8px;
                height: 100vh;
                background: var(--bg-primary);
                color: var(--text-primary);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            .panel {
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                box-shadow: 0 2px 4px var(--shadow-color);
                overflow: hidden;
            }
            
            .panel-header {
                background: var(--bg-tertiary);
                padding: 8px 12px;
                border-bottom: 1px solid var(--border-color);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .panel-header h3 {
                margin: 0;
                font-size: 14px;
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .panel-content {
                padding: 12px;
                height: calc(100% - 40px);
                overflow: auto;
            }
            
            .header-panel {
                grid-column: 1 / -1;
                grid-row: 1;
            }
            
            .market-panel {
                grid-column: 1;
                grid-row: 2;
            }
            
            .price-chart {
                grid-column: 2;
                grid-row: 2;
            }
            
            .distribution-chart {
                grid-column: 3;
                grid-row: 2;
            }
            
            .performance-chart {
                grid-column: 1;
                grid-row: 3;
            }
            
            .strategies {
                grid-column: 2;
                grid-row: 3;
            }
            
            .models {
                grid-column: 3;
                grid-row: 3;
            }
            
            .trade-monitor {
                grid-column: 1;
                grid-row: 4;
            }
            
            .jobs {
                grid-column: 2;
                grid-row: 4;
            }
            
            .notifications {
                grid-column: 3;
                grid-row: 4;
            }
            
            .btn {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                padding: 4px 8px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
            }
            
            .btn:hover {
                background: var(--accent-primary);
                color: var(--bg-primary);
            }
            
            .btn-primary {
                background: var(--accent-primary);
                color: var(--bg-primary);
            }
            
            .btn-success {
                background: var(--accent-success);
                color: var(--bg-primary);
            }
            
            .btn-outline {
                background: transparent;
                border-color: var(--border-color);
            }
            
            .form-control {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            
            .table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .table th,
            .table td {
                padding: 4px 8px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
                font-size: 11px;
            }
            
            .table th {
                background: var(--bg-tertiary);
                font-weight: 600;
                color: var(--text-secondary);
            }
            
            .chart-container {
                width: 100%;
                height: 100%;
                min-height: 200px;
            }
            
            .status-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 6px;
            }
            
            .status-indicator.connected {
                background: var(--accent-success);
            }
            
            .status-indicator.disconnected {
                background: var(--accent-danger);
            }
            
            .status-indicator.connecting {
                background: var(--accent-warning);
            }
        `;
        document.head.appendChild(style);
    }
    
    setupEventListeners() {
        // Symbol search
        const symbolSearch = document.getElementById('symbol-search');
        if (symbolSearch) {
            symbolSearch.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.searchSymbol(symbolSearch.value);
                }
            });
        }
        
        // Timeframe selector
        const timeframeSelect = document.getElementById('timeframe-select');
        if (timeframeSelect) {
            timeframeSelect.value = this.state.currentTimeframe;
            timeframeSelect.addEventListener('change', (e) => {
                this.state.currentTimeframe = e.target.value;
                localStorage.setItem('fq_timeframe', e.target.value);
                this.updateCharts();
            });
        }
        
        // Strategy selector
        const strategySelect = document.getElementById('strategy-select');
        if (strategySelect) {
            strategySelect.addEventListener('change', (e) => {
                this.state.currentStrategy = e.target.value;
                localStorage.setItem('fq_strategy', e.target.value);
                this.updateStrategyDetails();
            });
        }
        
        // Action buttons
        const runBacktestBtn = document.getElementById('run-backtest-btn');
        if (runBacktestBtn) {
            runBacktestBtn.addEventListener('click', () => this.runBacktest());
        }
        
        const paperTradeBtn = document.getElementById('paper-trade-btn');
        if (paperTradeBtn) {
            paperTradeBtn.addEventListener('click', () => this.startPaperTrading());
        }
        
        const trainModelBtn = document.getElementById('train-model');
        if (trainModelBtn) {
            trainModelBtn.addEventListener('click', () => this.trainModel());
        }
        
        // Refresh buttons
        const refreshButtons = document.querySelectorAll('[id$="-refresh"]');
        refreshButtons.forEach(btn => {
            btn.addEventListener('click', () => this.refreshData(btn.id.replace('-refresh', '')));
        });
    }
    
    setupHotkeys() {
        document.addEventListener('keydown', (e) => {
            // S - Focus symbol search
            if (e.key === 's' && !e.ctrlKey && !e.altKey) {
                e.preventDefault();
                const symbolSearch = document.getElementById('symbol-search');
                if (symbolSearch) {
                    symbolSearch.focus();
                    symbolSearch.select();
                }
            }
            
            // B - Run backtest
            if (e.key === 'b' && !e.ctrlKey && !e.altKey) {
                e.preventDefault();
                this.runBacktest();
            }
            
            // T - Toggle paper trading
            if (e.key === 't' && !e.ctrlKey && !e.altKey) {
                e.preventDefault();
                this.togglePaperTrading();
            }
            
            // R - Refresh all data
            if (e.key === 'r' && !e.ctrlKey && !e.altKey) {
                e.preventDefault();
                this.refreshAllData();
            }
        });
    }
    
    initializeNotifications() {
        this.components.notifications = {
            container: document.getElementById('notifications-list'),
            count: 0
        };
        
        // Create notification system
        this.showNotification('Dashboard initialized', 'info');
    }
    
    initializeDraggablePanels() {
        // Initialize draggable panels using GridStack.js or similar
        // This is a placeholder for the draggable functionality
        console.log('Draggable panels initialized (placeholder)');
    }
    
    async loadInitialData() {
        try {
            // Try to load data from API first
            await this.loadDataFromAPI();
        } catch (error) {
            console.warn('API data loading failed, falling back to mock data:', error);
            this.state.isMockMode = true;
            this.loadMockData();
        }
        
        // Populate UI with loaded data
        this.populateMarketData();
        this.populateStrategies();
        this.populateModels();
        this.populateJobs();
    }
    
    async loadDataFromAPI() {
        const endpoints = [
            { key: 'symbols', url: '/futurequant/data/symbols' },
            { key: 'strategies', url: '/futurequant/strategies' },
            { key: 'models', url: '/futurequant/models' },
            { key: 'jobs', url: '/futurequant/jobs' }
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await this.apiCall(endpoint.url);
                if (response.success) {
                    this.data[endpoint.key] = response.data || response.results || [];
                }
            } catch (error) {
                console.warn(`Failed to load ${endpoint.key}:`, error);
            }
        }
    }
    
    loadMockData() {
        this.data.symbols = [...this.mockData.symbols];
        this.data.strategies = [...this.mockData.strategies];
        this.data.models = [...this.mockData.models];
        this.data.jobs = [
            { id: 1, name: 'Model Training', status: 'running', progress: 75, type: 'training' },
            { id: 2, name: 'Backtest Analysis', status: 'completed', progress: 100, type: 'backtest' },
            { id: 3, name: 'Data Update', status: 'pending', progress: 0, type: 'data' }
        ];
    }
    
    async apiCall(endpoint, options = {}) {
        const url = `${this.config.apiBaseUrl}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        let lastError;
        for (let attempt = 1; attempt <= this.config.maxRetries; attempt++) {
            try {
                const response = await fetch(url, config);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                lastError = error;
                if (attempt < this.config.maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * attempt));
                }
            }
        }
        
        throw lastError;
    }
    
    populateMarketData() {
        const tbody = document.getElementById('market-ticker-body');
        if (!tbody) return;
        
        tbody.innerHTML = this.data.symbols.map(symbol => `
            <tr class="market-row" data-symbol="${symbol.ticker}">
                <td><strong>${symbol.ticker}</strong><br><small>${symbol.name}</small></td>
                <td class="price-cell">${symbol.price.toFixed(2)}</td>
                <td class="change-cell ${symbol.change >= 0 ? 'positive' : 'negative'}">
                    ${symbol.change >= 0 ? '+' : ''}${symbol.change.toFixed(2)} (${symbol.changePercent.toFixed(2)}%)
                </td>
                <td>${symbol.volume.toLocaleString()}</td>
                <td>${symbol.bid.toFixed(2)} / ${symbol.ask.toFixed(2)}</td>
            </tr>
        `).join('');
        
        // Add click handlers for symbol selection
        tbody.querySelectorAll('.market-row').forEach(row => {
            row.addEventListener('click', () => {
                const symbol = row.dataset.symbol;
                this.selectSymbol(symbol);
            });
        });
    }
    
    populateStrategies() {
        const select = document.getElementById('strategy-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select Strategy</option>' +
            this.data.strategies.map(strategy => 
                `<option value="${strategy.id}">${strategy.name}</option>`
            ).join('');
        
        // Set current strategy if available
        if (this.state.currentStrategy) {
            select.value = this.state.currentStrategy;
            this.updateStrategyDetails();
        }
    }
    
    populateModels() {
        const container = document.getElementById('models-list');
        if (!container) return;
        
        container.innerHTML = this.data.models.map(model => `
            <div class="model-item" data-model-id="${model.id}">
                <div class="model-header">
                    <h4>${model.name}</h4>
                    <span class="model-status status-${model.status}">${model.status}</span>
                </div>
                <p>${model.description}</p>
                <div class="model-metrics">
                    <span>Accuracy: ${model.accuracy}</span>
                    <span>Training: ${model.trainingTime}</span>
                </div>
            </div>
        `).join('');
    }
    
    populateJobs() {
        const container = document.getElementById('jobs-list');
        if (!container) return;
        
        container.innerHTML = this.data.jobs.map(job => `
            <div class="job-item" data-job-id="${job.id}">
                <div class="job-header">
                    <h4>${job.name}</h4>
                    <span class="job-status status-${job.status}">${job.status}</span>
                </div>
                <div class="job-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${job.progress}%"></div>
                    </div>
                    <span>${job.progress}%</span>
                </div>
                <small>Type: ${job.type}</small>
            </div>
        `).join('');
    }
    
    selectSymbol(symbol) {
        this.state.currentSymbol = symbol;
        localStorage.setItem('fq_symbol', symbol);
        
        // Update UI
        const symbolSearch = document.getElementById('symbol-search');
        if (symbolSearch) {
            symbolSearch.value = symbol;
        }
        
        // Update charts
        this.updateCharts();
        
        // Show notification
        this.showNotification(`Selected symbol: ${symbol}`, 'info');
    }
    
    searchSymbol(query) {
        if (!query.trim()) return;
        
        const symbol = query.trim().toUpperCase();
        if (this.data.symbols.find(s => s.ticker === symbol)) {
            this.selectSymbol(symbol);
        } else {
            this.showNotification(`Symbol ${symbol} not found`, 'warning');
        }
    }
    
    updateStrategyDetails() {
        const container = document.getElementById('strategy-details');
        if (!container || !this.state.currentStrategy) return;
        
        const strategy = this.data.strategies.find(s => s.id == this.state.currentStrategy);
        if (!strategy) return;
        
        container.innerHTML = `
            <div class="strategy-info">
                <h4>${strategy.name}</h4>
                <p>${strategy.description}</p>
                <div class="strategy-metrics">
                    <div class="metric">
                        <label>Risk Level:</label>
                        <span class="risk-${strategy.risk.toLowerCase()}">${strategy.risk}</span>
                    </div>
                    <div class="metric">
                        <label>Expected Return:</label>
                        <span>${strategy.expectedReturn}</span>
                    </div>
                    <div class="metric">
                        <label>Max Drawdown:</label>
                        <span>${strategy.maxDrawdown}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    initializeCharts() {
        // Initialize Chart.js charts for each panel
        this.components.charts = {
            price: this.createPriceChart(),
            distribution: this.createDistributionChart(),
            performance: this.createPerformanceChart()
        };
    }
    
    createPriceChart() {
        const ctx = document.getElementById('price-chart-container');
        if (!ctx) return null;
        
        // Create canvas for chart
        const canvas = document.createElement('canvas');
        ctx.appendChild(canvas);
        
        // This would be replaced with actual Chart.js implementation
        console.log('Price chart initialized');
        return canvas;
    }
    
    createDistributionChart() {
        const ctx = document.getElementById('distribution-chart-container');
        if (!ctx) return null;
        
        const canvas = document.createElement('canvas');
        ctx.appendChild(canvas);
        
        console.log('Distribution chart initialized');
        return canvas;
    }
    
    createPerformanceChart() {
        const ctx = document.getElementById('performance-chart-container');
        if (!ctx) return null;
        
        const canvas = document.createElement('canvas');
        ctx.appendChild(canvas);
        
        console.log('Performance chart initialized');
        return canvas;
    }
    
    updateCharts() {
        // Update charts with new data
        console.log('Updating charts for symbol:', this.state.currentSymbol);
        // This would contain actual chart update logic
    }
    
    setupWebSocket() {
        try {
            this.ws = new WebSocket(this.config.wsBaseUrl);
            
            this.ws.onopen = () => {
                this.state.isConnected = true;
                this.updateConnectionStatus('connected');
                this.showNotification('WebSocket connected', 'success');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                this.state.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.showNotification('WebSocket disconnected', 'warning');
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.warn('WebSocket not available:', error);
            this.updateConnectionStatus('disconnected');
        }
    }
    
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connection-indicator');
        const text = document.getElementById('connection-text');
        
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
        
        if (text) {
            const statusTexts = {
                connected: 'Connected',
                disconnected: 'Disconnected',
                connecting: 'Connecting...',
                error: 'Error'
            };
            text.textContent = statusTexts[status] || 'Unknown';
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'price_update':
                this.updatePriceData(data.symbol, data.price, data.change);
                break;
            case 'signal_update':
                this.updateSignalData(data.symbol, data.signals);
                break;
            case 'trade_update':
                this.updateTradeData(data.trades);
                break;
            case 'job_update':
                this.updateJobData(data.jobs);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    updatePriceData(symbol, price, change) {
        const row = document.querySelector(`[data-symbol="${symbol}"]`);
        if (!row) return;
        
        const priceCell = row.querySelector('.price-cell');
        const changeCell = row.querySelector('.change-cell');
        
        if (priceCell) priceCell.textContent = price.toFixed(2);
        if (changeCell) {
            changeCell.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}`;
            changeCell.className = `change-cell ${change >= 0 ? 'positive' : 'negative'}`;
        }
    }
    
    updateSignalData(symbol, signals) {
        // Update distribution chart with new signals
        console.log('Updating signals for:', symbol, signals);
    }
    
    updateTradeData(trades) {
        // Update trade monitor with new trades
        console.log('Updating trades:', trades);
    }
    
    updateJobData(jobs) {
        // Update job status with new data
        this.data.jobs = jobs;
        this.populateJobs();
    }
    
    startDataRefresh() {
        setInterval(() => {
            if (!this.state.isConnected) {
                this.refreshAllData();
            }
        }, this.config.refreshInterval);
    }
    
    async refreshAllData() {
        try {
            await this.loadDataFromAPI();
            this.populateMarketData();
            this.populateStrategies();
            this.populateModels();
            this.populateJobs();
            this.state.lastUpdate = new Date();
        } catch (error) {
            console.warn('Data refresh failed:', error);
        }
    }
    
    async refreshData(type) {
        try {
            switch (type) {
                case 'market':
                    await this.loadDataFromAPI();
                    this.populateMarketData();
                    break;
                case 'jobs':
                    await this.loadDataFromAPI();
                    this.populateJobs();
                    break;
                default:
                    console.log('Unknown refresh type:', type);
            }
        } catch (error) {
            console.warn(`${type} refresh failed:`, error);
        }
    }
    
    async runBacktest() {
        if (!this.state.currentStrategy) {
            this.showNotification('Please select a strategy first', 'warning');
            return;
        }
        
        try {
            this.showNotification('Running backtest...', 'info');
            
            // This would call the actual backtest API
            const response = await this.apiCall('/quantitative-analysis/vectorbt-backtest', {
                method: 'POST',
                body: JSON.stringify({
                    strategy_id: this.state.currentStrategy,
                    start_date: '2024-01-01',
                    end_date: '2024-12-31',
                    symbols: [this.state.currentSymbol],
                    strategy_type: 'momentum'
                })
            });
            
            if (response.success) {
                this.showNotification('Backtest completed successfully', 'success');
                // Update performance chart with results
                this.updatePerformanceChart(response.results);
            } else {
                this.showNotification('Backtest failed: ' + response.error, 'error');
            }
            
        } catch (error) {
            console.error('Backtest failed:', error);
            this.showNotification('Backtest failed: ' + error.message, 'error');
        }
    }
    
    startPaperTrading() {
        if (!this.state.currentStrategy) {
            this.showNotification('Please select a strategy first', 'warning');
            return;
        }
        
        this.showNotification('Starting paper trading session...', 'info');
        // This would start paper trading
    }
    
    togglePaperTrading() {
        // Toggle paper trading on/off
        this.showNotification('Paper trading toggled', 'info');
    }
    
    async trainModel() {
        try {
            this.showNotification('Starting model training...', 'info');
            
            // This would call the model training API
            const response = await this.apiCall('/futurequant/models/train', {
                method: 'POST',
                body: JSON.stringify({
                    model_type: 'transformer',
                    symbol: this.state.currentSymbol,
                    parameters: {}
                })
            });
            
            if (response.success) {
                this.showNotification('Model training started', 'success');
            } else {
                this.showNotification('Model training failed: ' + response.error, 'error');
            }
            
        } catch (error) {
            console.error('Model training failed:', error);
            this.showNotification('Model training failed: ' + error.message, 'error');
        }
    }
    
    updatePerformanceChart(results) {
        // Update performance chart with backtest results
        console.log('Updating performance chart with:', results);
    }
    
    showNotification(message, type = 'info') {
        if (!this.components.notifications) return;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add to notifications panel
        if (this.components.notifications.container) {
            this.components.notifications.container.appendChild(notification);
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            });
        }
        
        this.components.notifications.count++;
    }
    
    loadUserPreferences() {
        // Load user preferences from localStorage
        const preferences = {
            symbol: localStorage.getItem('fq_symbol'),
            timeframe: localStorage.getItem('fq_timeframe'),
            strategy: localStorage.getItem('fq_strategy'),
            theme: localStorage.getItem('fq_theme') || 'dark',
            layout: localStorage.getItem('fq_layout') || 'default'
        };
        
        // Apply preferences
        if (preferences.symbol) {
            this.selectSymbol(preferences.symbol);
        }
        
        if (preferences.timeframe) {
            this.state.currentTimeframe = preferences.timeframe;
            const timeframeSelect = document.getElementById('timeframe-select');
            if (timeframeSelect) {
                timeframeSelect.value = preferences.timeframe;
            }
        }
        
        if (preferences.strategy) {
            this.state.currentStrategy = preferences.strategy;
            const strategySelect = document.getElementById('strategy-select');
            if (strategySelect) {
                strategySelect.value = preferences.strategy;
                this.updateStrategyDetails();
            }
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM ready, initializing FutureQuant Enhanced Dashboard...');
    window.futureQuantDashboard = new FutureQuantEnhancedDashboard();
});

// Export for global access
window.FutureQuantEnhancedDashboard = FutureQuantEnhancedDashboard;
