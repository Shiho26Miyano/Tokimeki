/**
 * ETF Dashboard - Redesigned based on reference
 * Uses Chart.js instead of Recharts
 * Dark theme with modern UI
 */
class ETFDashboard {
    constructor() {
        console.log('ETFDashboard constructor called');
        this.currentSymbol = 'SPY';
        this.data = null;
        this.charts = {
            growth: null,
            drawdown: null,
            scatter: null
        };
        this.state = {
            window: '1Y',
            benchmark: 'SPY',
            sort: 'score',
            filter: '',
            pinned: new Set(['SPY']),
            selected: 'SPY'
        };
        
        this.init();
    }

    async init() {
        console.log('Initializing ETF Dashboard...');
        this.setupEventListeners();
        await this.loadDashboardData(this.currentSymbol);
        this.render();
    }

    async loadDashboardData(symbol) {
        try {
            console.log(`Loading dashboard data for ${symbol}...`);
            this.showLoading(true);

            const response = await fetch('/api/v1/etf/dashboard/data', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    date_range_days: 365
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log('Dashboard data loaded:', data);
            
            this.data = data;
            this.processData();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError(`Error: ${error.message}`);
            this.data = null;
        } finally {
            this.showLoading(false);
        }
    }

    processData() {
        if (!this.data) return;
        
        // Ensure arrays exist
        if (!this.data.price_data) this.data.price_data = [];
        if (!this.data.top_holdings) this.data.top_holdings = [];
        if (!this.data.dividend_history) this.data.dividend_history = [];
        if (!this.data.technical_indicators) this.data.technical_indicators = [];
    }

    setupEventListeners() {
        // Window selector
        const windowSel = document.getElementById('etf-window-sel');
        if (windowSel) {
            windowSel.addEventListener('change', (e) => {
                this.state.window = e.target.value;
                this.updateDateRange();
            });
        }

        // Benchmark selector
        const benchSel = document.getElementById('etf-bench-sel');
        if (benchSel) {
            benchSel.addEventListener('change', (e) => {
                this.state.benchmark = e.target.value;
                this.render();
            });
        }

        // Sort selector
        const sortSel = document.getElementById('etf-sort-sel');
        if (sortSel) {
            sortSel.addEventListener('change', (e) => {
                this.state.sort = e.target.value;
                this.render();
            });
        }

        // Search input
        const searchInput = document.getElementById('etf-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.state.filter = e.target.value;
                this.render();
            });
        }

        // Reset button
        const resetBtn = document.getElementById('etf-reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.state = {
                    window: '1Y',
                    benchmark: 'SPY',
                    sort: 'score',
                    filter: '',
                    pinned: new Set(['SPY']),
                    selected: 'SPY'
                };
                if (windowSel) windowSel.value = '1Y';
                if (benchSel) benchSel.value = 'SPY';
                if (sortSel) sortSel.value = 'score';
                if (searchInput) searchInput.value = '';
                this.updateDateRange();
                this.render();
            });
        }

        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('etf-tab')) {
                const tab = e.target.getAttribute('data-tab');
                this.setTab(tab);
            }
        });

        // Symbol input
        const symbolInput = document.getElementById('etf-symbol-input');
        if (symbolInput) {
            symbolInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSymbolChange();
                }
            });
        }

        // Load button
        const loadBtn = document.getElementById('etf-load-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                this.handleSymbolChange();
            });
        }
    }

    handleSymbolChange() {
        const input = document.getElementById('etf-symbol-input');
        if (input) {
            const newSymbol = input.value.trim().toUpperCase();
            if (newSymbol && newSymbol !== this.currentSymbol) {
                this.currentSymbol = newSymbol;
                this.state.selected = newSymbol;
                this.state.pinned.add(newSymbol);
                this.loadDashboardData(newSymbol).then(() => this.render());
            }
        }
    }

    updateDateRange() {
        const daysMap = {
            '1Y': 365,
            '3Y': 1095,
            '5Y': 1825,
            'MAX': 3650
        };
        const days = daysMap[this.state.window] || 365;
        // Reload data with new range
        this.loadDashboardData(this.currentSymbol).then(() => this.render());
    }

    setTab(tab) {
        // Hide all sections
        ['overview', 'compare', 'risk', 'costliq', 'notes'].forEach(id => {
            const section = document.getElementById(`etf-section-${id}`);
            if (section) {
                section.classList.toggle('hidden', id !== tab);
            }
        });

        // Update tab buttons
        document.querySelectorAll('.etf-tab').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
        });
    }

    showLoading(isLoading) {
        const container = document.getElementById('etf-dashboard');
        if (!container) return;

        if (isLoading) {
            container.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; min-height: 400px; background: #f8fafc;">
                    <div style="text-align: center;">
                        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(59,130,246,0.3); border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                        <p style="margin-top: 16px; color: #64748b; font-size: 14px;">Loading ETF data...</p>
                    </div>
                </div>
            `;
        }
    }

    showError(message) {
        const container = document.getElementById('etf-dashboard');
        if (!container) return;
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #ef4444; background: #f8fafc;">
                <h3 style="color: #1e293b; margin-bottom: 0.5rem;">Error Loading Data</h3>
                <p style="color: #64748b;">${message}</p>
                <button onclick="window.etfDashboard.loadDashboardData(window.etfDashboard.currentSymbol).then(() => window.etfDashboard.render())" 
                        style="margin-top: 1rem; padding: 8px 16px; background: #3b82f6; border: 1px solid #3b82f6; color: white; border-radius: 8px; cursor: pointer; font-weight: 500;">
                    Retry
                </button>
            </div>
        `;
    }

    render() {
        const container = document.getElementById('etf-dashboard');
        if (!container) {
            console.error('Dashboard container not found');
            return;
        }

        if (!this.data) {
            this.showError('No data available');
            return;
        }

        container.innerHTML = this.getDashboardHTML();
        
        // Render after DOM is updated
        setTimeout(() => {
            this.renderKPITable();
            this.renderCharts();
            this.renderCompareTable();
            this.renderRiskTable();
            this.renderCostLiqTable();
        }, 100);
    }

    getDashboardHTML() {
        return `
            <div class="etf-wrap">
                ${this.getTopBarHTML()}
                ${this.getOverviewSectionHTML()}
                ${this.getCompareSectionHTML()}
                ${this.getRiskSectionHTML()}
                ${this.getCostLiqSectionHTML()}
                ${this.getNotesSectionHTML()}
            </div>
            <style>
                ${this.getStyles()}
            </style>
        `;
    }

    getStyles() {
        return `
            .etf-wrap {
                max-width: 1320px;
                margin: 0 auto;
                padding: 2rem;
                font-family: 'Inter', 'Roboto', Arial, sans-serif;
                background: #f8fafc;
                min-height: 100vh;
            }
            .etf-topbar {
                display: flex;
                gap: 12px;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                padding: 14px 16px;
                border: 1px solid #e2e8f0;
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
                position: sticky;
                top: 10px;
                z-index: 10;
                margin-bottom: 1.5rem;
            }
            .etf-brand {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 700;
                letter-spacing: .2px;
                color: #1e293b;
            }
            .etf-dot {
                width: 10px;
                height: 10px;
                border-radius: 999px;
                background: #3b82f6;
                box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
            }
            .etf-controls {
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }
            .etf-controls select,
            .etf-controls button,
            .etf-controls input[type="search"],
            .etf-controls input[type="text"] {
                background: white;
                border: 1px solid #e2e8f0;
                color: #1e293b;
                border-radius: 8px;
                padding: 8px 12px;
                outline: none;
                font-size: 14px;
            }
            .etf-controls select:focus,
            .etf-controls input:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            .etf-controls button {
                cursor: pointer;
                font-weight: 500;
            }
            .etf-controls button.primary {
                background: #1e293b;
                border-color: #1e293b;
                color: white;
            }
            .etf-controls button.primary:hover {
                background: #0f172a;
            }
            .etf-tabs {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            .etf-tab {
                padding: 8px 16px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                background: white;
                color: #64748b;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s;
            }
            .etf-tab:hover {
                background: #f1f5f9;
                color: #1e293b;
            }
            .etf-tab.active {
                background: #1e293b;
                border-color: #1e293b;
                color: white;
            }
            .etf-grid {
                display: grid;
                gap: 1.5rem;
                margin-top: 1.5rem;
            }
            .etf-grid.cols-12 {
                grid-template-columns: repeat(12, 1fr);
            }
            .etf-card {
                border: 1px solid #e2e8f0;
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            }
            .etf-card h3 {
                margin: 0 0 1rem 0;
                font-size: 1.125rem;
                color: #1e293b;
                font-weight: 600;
                letter-spacing: .2px;
            }
            .etf-kpi-ribbon {
                overflow: auto;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                background: white;
            }
            .etf-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }
            .etf-table th,
            .etf-table td {
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
                text-align: left;
            }
            .etf-table th {
                position: sticky;
                top: 0;
                background: #f8fafc;
                z-index: 1;
                color: #64748b;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .etf-table tbody tr:hover {
                background: #f8fafc;
            }
            .etf-pill {
                display: inline-flex;
                gap: 6px;
                align-items: center;
                padding: 4px 10px;
                border-radius: 999px;
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
            }
            .etf-pill:hover {
                background: #e2e8f0;
            }
            .etf-pos { color: #10b981; }
            .etf-neg { color: #ef4444; }
            .etf-neu { color: #64748b; }
            .etf-small {
                font-size: 12px;
                color: #64748b;
            }
            .etf-row {
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }
            .etf-spacer {
                flex: 1;
            }
            .etf-mono {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 13px;
            }
            .etf-hidden {
                display: none;
            }
            .etf-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 999px;
                border: 1px solid #3b82f6;
                color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
                font-size: 11px;
                font-weight: 500;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            @media (max-width: 980px) {
                .etf-grid.cols-12 {
                    grid-template-columns: 1fr;
                }
                .etf-card[style*="grid-column: span"] {
                    grid-column: span 12 !important;
                }
            }
        `;
    }

    getTopBarHTML() {
        return `
            <div class="etf-topbar">
                <div class="etf-brand">
                    <span class="etf-dot"></span>
                    <div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">ETF Dashboard <span class="etf-badge">Live</span></div>
                        <div class="etf-small" style="color: #64748b;">Polygon.io • Real-time data</div>
                    </div>
                </div>

                <div class="etf-controls">
                    <div class="etf-row">
                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Symbol:</label>
                        <input type="text" id="etf-symbol-input" value="${this.currentSymbol}" placeholder="SPY" style="width: 100px; text-transform: uppercase; font-weight: 600;" />
                        <button class="primary" id="etf-load-btn">Load</button>
                        
                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Window:</label>
                        <select id="etf-window-sel">
                            <option value="1Y" selected>1Y</option>
                            <option value="3Y">3Y</option>
                            <option value="5Y">5Y</option>
                            <option value="MAX">MAX</option>
                        </select>

                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Sort:</label>
                        <select id="etf-sort-sel">
                            <option value="score" selected>Score</option>
                            <option value="cagr">CAGR</option>
                            <option value="sharpe">Sharpe</option>
                            <option value="mdd">Max DD</option>
                        </select>

                        <input id="etf-search-input" type="search" placeholder="Filter..." style="width: 150px;" />
                        <button class="primary" id="etf-reset-btn">Reset</button>
                    </div>
                </div>

                <div class="etf-tabs">
                    <button class="etf-tab active" data-tab="overview">Overview</button>
                    <button class="etf-tab" data-tab="compare">Compare</button>
                    <button class="etf-tab" data-tab="risk">Risk</button>
                    <button class="etf-tab" data-tab="costliq">Cost & Liquidity</button>
                    <button class="etf-tab" data-tab="notes">Notes</button>
                </div>
            </div>
        `;
    }

    getOverviewSectionHTML() {
        const basicInfo = this.data.basic_info || {};
        return `
            <section id="etf-section-overview" class="etf-grid cols-12">
                <div class="etf-card" style="grid-column: span 12;">
                    <div class="etf-row">
                        <h3 style="margin: 0;">ETF Overview - ${basicInfo.name || this.currentSymbol}</h3>
                        <div class="etf-spacer"></div>
                    </div>
                    <div id="etf-kpi-table" style="margin-top: 10px;"></div>
                </div>

                <div class="etf-card" style="grid-column: span 8;">
                    <h3>Price History</h3>
                    <div style="position: relative; height: 400px;">
                        <canvas id="etf-chart-growth"></canvas>
                    </div>
                </div>

                <div class="etf-card" style="grid-column: span 4;">
                    <h3>Quick Profile</h3>
                    <div id="etf-quick-profile" class="etf-small"></div>
                </div>

                <div class="etf-card" style="grid-column: span 6;">
                    <h3>Drawdown</h3>
                    <div style="position: relative; height: 320px;">
                        <canvas id="etf-chart-dd"></canvas>
                    </div>
                </div>

                <div class="etf-card" style="grid-column: span 6;">
                    <h3>Risk vs Return</h3>
                    <div style="position: relative; height: 320px;">
                        <canvas id="etf-chart-scatter"></canvas>
                    </div>
                </div>
            </section>
        `;
    }

    getCompareSectionHTML() {
        return `
            <section id="etf-section-compare" class="etf-grid cols-12 etf-hidden">
                <div class="etf-card" style="grid-column: span 12;">
                    <h3>Metrics Comparison</h3>
                    <div id="etf-compare-table" style="overflow: auto; border-radius: 14px; border: 1px solid #223044; margin-top: 10px;"></div>
                </div>
            </section>
        `;
    }

    getRiskSectionHTML() {
        return `
            <section id="etf-section-risk" class="etf-grid cols-12 etf-hidden">
                <div class="etf-card" style="grid-column: span 7;">
                    <h3>Risk Metrics</h3>
                    <div id="etf-risk-table"></div>
                </div>
                <div class="etf-card" style="grid-column: span 5;">
                    <h3>Drawdown Episodes</h3>
                    <div id="etf-dd-episodes"></div>
                </div>
            </section>
        `;
    }

    getCostLiqSectionHTML() {
        return `
            <section id="etf-section-costliq" class="etf-grid cols-12 etf-hidden">
                <div class="etf-card" style="grid-column: span 6;">
                    <h3>Cost Breakdown</h3>
                    <div id="etf-cost-table"></div>
                </div>
                <div class="etf-card" style="grid-column: span 6;">
                    <h3>Liquidity</h3>
                    <div id="etf-liq-table"></div>
                </div>
            </section>
        `;
    }

    getNotesSectionHTML() {
        return `
            <section id="etf-section-notes" class="etf-grid cols-12 etf-hidden">
                <div class="etf-card" style="grid-column: span 12;">
                    <h3>Metric Dictionary</h3>
                    <div class="etf-small" style="line-height: 1.6;">
                        <div><span class="etf-mono">CAGR</span>: Annualized compound growth rate</div>
                        <div><span class="etf-mono">Vol</span>: Annualized volatility (standard deviation)</div>
                        <div><span class="etf-mono">Sharpe</span>: (Return - Rf) / Vol</div>
                        <div><span class="etf-mono">Max Drawdown</span>: Maximum peak-to-trough decline</div>
                        <div><span class="etf-mono">Beta</span>: Sensitivity to market movements</div>
                        <div><span class="etf-mono">Expense Ratio</span>: Annual management fee</div>
                    </div>
                </div>
            </section>
        `;
    }

    renderKPITable() {
        const container = document.getElementById('etf-kpi-table');
        if (!container || !this.data) return;

        const basicInfo = this.data.basic_info || {};
        const riskMetrics = this.data.risk_metrics || {};
        const priceData = this.data.price_data || [];

        // Calculate metrics
        let cagr = 0, volatility = 0, sharpe = 0, maxDD = 0;
        if (priceData.length > 0) {
            const startPrice = priceData[0].close;
            const endPrice = priceData[priceData.length - 1].close;
            const years = priceData.length / 252;
            if (years > 0 && startPrice > 0) {
                cagr = Math.pow(endPrice / startPrice, 1 / years) - 1;
            }

            // Calculate volatility
            const returns = [];
            for (let i = 1; i < priceData.length; i++) {
                returns.push((priceData[i].close - priceData[i-1].close) / priceData[i-1].close);
            }
            if (returns.length > 0) {
                const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
                const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
                volatility = Math.sqrt(variance * 252);
            }

            // Calculate max drawdown
            let peak = startPrice;
            let maxDrawdown = 0;
            for (const bar of priceData) {
                peak = Math.max(peak, bar.close);
                const drawdown = (bar.close - peak) / peak;
                maxDrawdown = Math.min(maxDrawdown, drawdown);
            }
            maxDD = maxDrawdown;

            // Sharpe ratio (simplified)
            const riskFreeRate = 0.02;
            sharpe = volatility > 0 ? (cagr - riskFreeRate) / volatility : 0;
        }

        const html = `
            <div class="etf-kpi-ribbon">
                <table class="etf-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="etf-mono">Current Price</td>
                            <td class="etf-mono">$${basicInfo.current_price ? basicInfo.current_price.toFixed(2) : '—'}</td>
                            <td>Latest trading price</td>
                        </tr>
                        <tr>
                            <td class="etf-mono">CAGR</td>
                            <td class="etf-mono ${cagr >= 0 ? 'etf-pos' : 'etf-neg'}">${(cagr * 100).toFixed(2)}%</td>
                            <td>Annualized return</td>
                        </tr>
                        <tr>
                            <td class="etf-mono">Volatility</td>
                            <td class="etf-mono">${(volatility * 100).toFixed(2)}%</td>
                            <td>Annualized volatility</td>
                        </tr>
                        <tr>
                            <td class="etf-mono">Sharpe Ratio</td>
                            <td class="etf-mono">${sharpe.toFixed(2)}</td>
                            <td>Risk-adjusted return</td>
                        </tr>
                        <tr>
                            <td class="etf-mono">Max Drawdown</td>
                            <td class="etf-mono etf-neg">${(maxDD * 100).toFixed(2)}%</td>
                            <td>Maximum decline from peak</td>
                        </tr>
                        <tr>
                            <td class="etf-mono">AUM</td>
                            <td class="etf-mono">${basicInfo.aum ? `$${(basicInfo.aum / 1e9).toFixed(1)}B` : '—'}</td>
                            <td>Assets under management</td>
                        </tr>
                        <tr>
                            <td class="etf-mono">Expense Ratio</td>
                            <td class="etf-mono">${basicInfo.expense_ratio ? (basicInfo.expense_ratio * 100).toFixed(2) + '%' : '—'}</td>
                            <td>Annual management fee</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        container.innerHTML = html;
    }

    renderQuickProfile() {
        const container = document.getElementById('etf-quick-profile');
        if (!container || !this.data) return;

        const basicInfo = this.data.basic_info || {};
        const riskMetrics = this.data.risk_metrics || {};

        container.innerHTML = `
            <div class="etf-row">
                <div class="etf-pill etf-mono">${this.currentSymbol}</div>
                <div class="etf-spacer"></div>
            </div>
            <div style="margin-top: 10px;">
                <div><b>${basicInfo.name || this.currentSymbol}</b></div>
                <div class="etf-small">${basicInfo.issuer || 'N/A'}</div>
            </div>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 12px 0;" />
            <div class="etf-small">
                <div><span class="etf-mono">Price</span> $${basicInfo.current_price ? basicInfo.current_price.toFixed(2) : '—'}</div>
                <div><span class="etf-mono">AUM</span> ${basicInfo.aum ? `$${(basicInfo.aum / 1e9).toFixed(1)}B` : '—'}</div>
                <div><span class="etf-mono">Expense</span> ${basicInfo.expense_ratio ? (basicInfo.expense_ratio * 100).toFixed(2) + '%' : '—'}</div>
                <div><span class="etf-mono">Dividend Yield</span> ${basicInfo.dividend_yield ? (basicInfo.dividend_yield * 100).toFixed(2) + '%' : '—'}</div>
            </div>
        `;
    }

    renderCharts() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js not loaded');
            return;
        }

        const priceData = this.data.price_data || [];
        if (priceData.length === 0) {
            console.warn('No price data for charts');
            return;
        }

        // Prepare data
        const labels = priceData.map((bar, i) => {
            const date = new Date(bar.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const prices = priceData.map(bar => bar.close);
        const normalized = prices.map(p => (p / prices[0]) * 100);

        // Calculate drawdown
        let peak = prices[0];
        const drawdowns = prices.map(p => {
            peak = Math.max(peak, p);
            return ((p - peak) / peak) * 100;
        });

        // Growth chart
        const growthCtx = document.getElementById('etf-chart-growth');
        if (growthCtx) {
            if (this.charts.growth) this.charts.growth.destroy();
            this.charts.growth = new Chart(growthCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: this.currentSymbol,
                        data: normalized,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { 
                                color: '#64748b',
                                font: { size: 12 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#e2e8f0',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        x: {
                            ticks: { 
                                color: '#64748b', 
                                maxRotation: 45,
                                font: { size: 11 }
                            },
                            grid: { 
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        },
                        y: {
                            ticks: { 
                                color: '#64748b',
                                font: { size: 11 }
                            },
                            grid: { 
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        }
                    }
                }
            });
        }

        // Drawdown chart
        const ddCtx = document.getElementById('etf-chart-dd');
        if (ddCtx) {
            if (this.charts.drawdown) this.charts.drawdown.destroy();
            this.charts.drawdown = new Chart(ddCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Drawdown',
                        data: drawdowns,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { 
                                color: '#64748b',
                                font: { size: 12 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#e2e8f0',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        x: {
                            ticks: { 
                                color: '#64748b', 
                                maxRotation: 45,
                                font: { size: 11 }
                            },
                            grid: { 
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        },
                        y: {
                            ticks: { 
                                color: '#64748b',
                                callback: (v) => v.toFixed(1) + '%',
                                font: { size: 11 }
                            },
                            grid: { 
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        }
                    }
                }
            });
        }

        // Scatter chart (risk vs return) - simplified for single ETF
        const scatterCtx = document.getElementById('etf-chart-scatter');
        if (scatterCtx && priceData.length > 0) {
            if (this.charts.scatter) this.charts.scatter.destroy();
            
            // Calculate metrics for scatter
            const returns = [];
            for (let i = 1; i < priceData.length; i++) {
                returns.push((priceData[i].close - priceData[i-1].close) / priceData[i-1].close);
            }
            const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
            const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
            const vol = Math.sqrt(variance * 252);
            const cagr = Math.pow(prices[prices.length - 1] / prices[0], 252 / priceData.length) - 1;

            this.charts.scatter = new Chart(scatterCtx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: this.currentSymbol,
                        data: [{
                            x: vol * 100,
                            y: cagr * 100
                        }],
                        backgroundColor: '#3b82f6',
                        borderColor: '#3b82f6',
                        pointRadius: 8,
                        pointHoverRadius: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { 
                                color: '#64748b',
                                font: { size: 12 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#e2e8f0',
                            borderWidth: 1,
                            callbacks: {
                                label: (ctx) => {
                                    return `${this.currentSymbol}: Vol ${ctx.raw.x.toFixed(1)}% | Return ${ctx.raw.y.toFixed(1)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Volatility (%)',
                                color: '#64748b',
                                font: { size: 12, weight: '500' }
                            },
                            ticks: { 
                                color: '#64748b',
                                font: { size: 11 }
                            },
                            grid: { 
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'CAGR (%)',
                                color: '#64748b',
                                font: { size: 12, weight: '500' }
                            },
                            ticks: { 
                                color: '#64748b',
                                font: { size: 11 }
                            },
                            grid: { 
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        }
                    }
                }
            });
        }

        this.renderQuickProfile();
    }

    renderCompareTable() {
        const container = document.getElementById('etf-compare-table');
        if (!container || !this.data) return;

        // For now, show single ETF metrics
        const basicInfo = this.data.basic_info || {};
        const riskMetrics = this.data.risk_metrics || {};
        const priceData = this.data.price_data || [];

        // Calculate metrics (same as KPI table)
        let cagr = 0, volatility = 0, sharpe = 0, maxDD = 0;
        if (priceData.length > 0) {
            const startPrice = priceData[0].close;
            const endPrice = priceData[priceData.length - 1].close;
            const years = priceData.length / 252;
            if (years > 0 && startPrice > 0) {
                cagr = Math.pow(endPrice / startPrice, 1 / years) - 1;
            }

            const returns = [];
            for (let i = 1; i < priceData.length; i++) {
                returns.push((priceData[i].close - priceData[i-1].close) / priceData[i-1].close);
            }
            if (returns.length > 0) {
                const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
                const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
                volatility = Math.sqrt(variance * 252);
            }

            let peak = startPrice;
            for (const bar of priceData) {
                peak = Math.max(peak, bar.close);
                const drawdown = (bar.close - peak) / peak;
                maxDD = Math.min(maxDD, drawdown);
            }

            const riskFreeRate = 0.02;
            sharpe = volatility > 0 ? (cagr - riskFreeRate) / volatility : 0;
        }

        container.innerHTML = `
            <table class="etf-table" style="min-width: 800px;">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>${this.currentSymbol}</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>CAGR</b></td>
                        <td class="etf-mono ${cagr >= 0 ? 'etf-pos' : 'etf-neg'}">${(cagr * 100).toFixed(2)}%</td>
                        <td class="etf-small">Annualized compound growth rate</td>
                    </tr>
                    <tr>
                        <td><b>Volatility</b></td>
                        <td class="etf-mono">${(volatility * 100).toFixed(2)}%</td>
                        <td class="etf-small">Annualized standard deviation</td>
                    </tr>
                    <tr>
                        <td><b>Sharpe Ratio</b></td>
                        <td class="etf-mono">${sharpe.toFixed(2)}</td>
                        <td class="etf-small">Risk-adjusted return</td>
                    </tr>
                    <tr>
                        <td><b>Max Drawdown</b></td>
                        <td class="etf-mono etf-neg">${(maxDD * 100).toFixed(2)}%</td>
                        <td class="etf-small">Maximum peak-to-trough decline</td>
                    </tr>
                    <tr>
                        <td><b>Beta</b></td>
                        <td class="etf-mono">${riskMetrics.beta ? riskMetrics.beta.toFixed(2) : '—'}</td>
                        <td class="etf-small">Sensitivity to market</td>
                    </tr>
                    <tr>
                        <td><b>Expense Ratio</b></td>
                        <td class="etf-mono">${basicInfo.expense_ratio ? (basicInfo.expense_ratio * 100).toFixed(2) + '%' : '—'}</td>
                        <td class="etf-small">Annual management fee</td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    renderRiskTable() {
        const container = document.getElementById('etf-risk-table');
        if (!container || !this.data) return;

        const riskMetrics = this.data.risk_metrics || {};
        const priceData = this.data.price_data || [];

        // Calculate additional risk metrics
        let var95 = 0, volatility = 0;
        if (priceData.length > 0) {
            const returns = [];
            for (let i = 1; i < priceData.length; i++) {
                returns.push((priceData[i].close - priceData[i-1].close) / priceData[i-1].close);
            }
            if (returns.length > 0) {
                const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
                const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
                volatility = Math.sqrt(variance * 252);
                var95 = -(volatility * 1.65 / Math.sqrt(252)) * 100;
            }
        }

        container.innerHTML = `
            <table class="etf-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>30-Day Volatility</td>
                        <td class="etf-mono">${riskMetrics.volatility_30d ? riskMetrics.volatility_30d.toFixed(2) + '%' : '—'}</td>
                    </tr>
                    <tr>
                        <td>60-Day Volatility</td>
                        <td class="etf-mono">${riskMetrics.volatility_60d ? riskMetrics.volatility_60d.toFixed(2) + '%' : '—'}</td>
                    </tr>
                    <tr>
                        <td>1-Year Volatility</td>
                        <td class="etf-mono">${(volatility * 100).toFixed(2)}%</td>
                    </tr>
                    <tr>
                        <td>VaR 95%</td>
                        <td class="etf-mono etf-neg">${var95.toFixed(2)}%</td>
                    </tr>
                    <tr>
                        <td>Beta</td>
                        <td class="etf-mono">${riskMetrics.beta ? riskMetrics.beta.toFixed(2) : '—'}</td>
                    </tr>
                    <tr>
                        <td>Sharpe Ratio</td>
                        <td class="etf-mono">${riskMetrics.sharpe_ratio ? riskMetrics.sharpe_ratio.toFixed(2) : '—'}</td>
                    </tr>
                    <tr>
                        <td>Max Drawdown</td>
                        <td class="etf-mono etf-neg">${riskMetrics.max_drawdown ? riskMetrics.max_drawdown.toFixed(2) + '%' : '—'}</td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    renderCostLiqTable() {
        const costContainer = document.getElementById('etf-cost-table');
        const liqContainer = document.getElementById('etf-liq-table');
        if (!costContainer || !liqContainer || !this.data) return;

        const basicInfo = this.data.basic_info || {};

        costContainer.innerHTML = `
            <table class="etf-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Expense Ratio</td>
                        <td class="etf-mono">${basicInfo.expense_ratio ? (basicInfo.expense_ratio * 100).toFixed(2) + '%' : '—'}</td>
                    </tr>
                    <tr>
                        <td>Bid-Ask Spread</td>
                        <td class="etf-mono">${basicInfo.bid_ask_spread ? `$${basicInfo.bid_ask_spread.toFixed(2)}` : '—'}</td>
                    </tr>
                </tbody>
            </table>
        `;

        liqContainer.innerHTML = `
            <table class="etf-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Average Volume</td>
                        <td class="etf-mono">${basicInfo.avg_volume ? basicInfo.avg_volume.toLocaleString() : '—'}</td>
                    </tr>
                    <tr>
                        <td>Current Volume</td>
                        <td class="etf-mono">${basicInfo.volume ? basicInfo.volume.toLocaleString() : '—'}</td>
                    </tr>
                    <tr>
                        <td>AUM</td>
                        <td class="etf-mono">${basicInfo.aum ? `$${(basicInfo.aum / 1e9).toFixed(1)}B` : '—'}</td>
                    </tr>
                </tbody>
            </table>
        `;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (typeof ETFDashboard !== 'undefined') {
            window.etfDashboard = new ETFDashboard();
        }
    });
} else {
    if (typeof ETFDashboard !== 'undefined') {
        window.etfDashboard = new ETFDashboard();
    }
}

