/**
 * ETF Dashboard — React UI Implementation
 * Purpose: Display comprehensive ETF analysis dashboard
 * Styling: Tailwind + shadcn/ui components
 * Charts: recharts
 * Backend: ETF API endpoints
 */

class ETFDashboard {
    constructor() {
        console.log('ETFDashboard constructor called');
        this.currentSymbol = 'SPY';
        this.sampleSymbols = ['SPY', 'QQQ', 'VOO', 'VTI', 'IWM'];
        this.data = null;
        this.refreshInterval = null;
        this.searchResults = [];
        this.showSearchResults = false;
        
        this.init();
    }

    async init() {
        console.log('Initializing ETF Dashboard...');
        this.setupEventListeners();
        await this.loadDashboardData();
        this.render();
        this.startAutoRefresh();
    }

    async loadDashboardData() {
        try {
            console.log(`Loading dashboard data for ${this.currentSymbol}...`);
            this.showLoading(true);

            const response = await fetch('/api/v1/etf/dashboard/data', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: this.currentSymbol,
                    date_range_days: 365
                })
            });

            console.log(`API response status: ${response.status}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API error response:`, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log('Dashboard data loaded successfully:', data);
            console.log('Basic info:', data.basic_info);
            console.log('Price data length:', data.price_data?.length || 0);
            console.log('Holdings length:', data.top_holdings?.length || 0);
            
            // Validate data structure
            if (!data.basic_info) {
                console.warn('No basic_info in response, creating default');
                data.basic_info = {
                    symbol: this.currentSymbol,
                    name: this.currentSymbol,
                    current_price: null
                };
            }
            
            this.data = data;
            this.processData();
            
            // If no price data, try to show helpful message
            if (!data.price_data || data.price_data.length === 0) {
                console.warn('No price data available - this may take a moment to load');
            }

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError(`Error: ${error.message}`);
            this.data = null;
        } finally {
            this.showLoading(false);
        }
    }

    processData() {
        // Data is already in the correct format from API
        // Just ensure we have all necessary fields
        if (!this.data) return;

        // Ensure arrays exist
        if (!this.data.price_data) this.data.price_data = [];
        if (!this.data.top_holdings) this.data.top_holdings = [];
        if (!this.data.dividend_history) this.data.dividend_history = [];
        if (!this.data.technical_indicators) this.data.technical_indicators = [];
        if (!this.data.sector_distribution) this.data.sector_distribution = [];
        if (!this.data.industry_distribution) this.data.industry_distribution = [];
    }

    handleSymbolChange() {
        const input = document.getElementById('symbol-input');
        if (input) {
            const newSymbol = input.value.trim().toUpperCase();
            if (newSymbol && newSymbol !== this.currentSymbol) {
                this.currentSymbol = newSymbol;
                this.loadDashboardData().then(() => this.render());
            }
        }
    }

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.id === 'refresh-btn') {
                this.loadDashboardData().then(() => this.render());
            }
            
            // Close search results when clicking outside
            if (!e.target.closest('.etf-search-container')) {
                this.showSearchResults = false;
                this.renderSearchResults();
            }
        });
        
        // Search input event
        document.addEventListener('input', (e) => {
            if (e.target.id === 'symbol-input') {
                const query = e.target.value.trim();
                if (query.length >= 1) {
                    this.searchETFs(query);
                } else {
                    this.showSearchResults = false;
                    this.renderSearchResults();
                }
            }
        });
    }
    
    async searchETFs(query) {
        try {
            const response = await fetch(`/api/v1/etf/search?query=${encodeURIComponent(query)}&limit=10`);
            if (response.ok) {
                const data = await response.json();
                this.searchResults = data.results || [];
                this.showSearchResults = true;
                this.renderSearchResults();
            }
        } catch (error) {
            console.error('Error searching ETFs:', error);
        }
    }
    
    renderSearchResults() {
        const container = document.getElementById('etf-search-results');
        if (!container) return;
        
        if (!this.showSearchResults || this.searchResults.length === 0) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'block';
        container.innerHTML = `
            <div style="
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                max-height: 300px;
                overflow-y: auto;
                z-index: 1000;
                margin-top: 4px;
            ">
                ${this.searchResults.map(etf => `
                    <div 
                        onclick="window.etfDashboard.selectETF('${etf.ticker}')"
                        style="
                            padding: 12px 16px;
                            cursor: pointer;
                            border-bottom: 1px solid #f1f5f9;
                            transition: background-color 0.2s;
                        "
                        onmouseover="this.style.backgroundColor='#f8fafc'"
                        onmouseout="this.style.backgroundColor='white'"
                    >
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 4px;">${etf.ticker}</div>
                        <div style="font-size: 0.875rem; color: #64748b;">${etf.name || ''}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    selectETF(symbol) {
        this.currentSymbol = symbol.toUpperCase();
        const input = document.getElementById('symbol-input');
        if (input) {
            input.value = symbol.toUpperCase();
        }
        this.showSearchResults = false;
        this.renderSearchResults();
        this.loadDashboardData().then(() => this.render());
    }

    startAutoRefresh() {
        // Refresh every 60 seconds
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData().then(() => this.render());
        }, 60000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showLoading(show) {
        const container = document.getElementById('etf-dashboard');
        if (!container) return;

        if (show) {
            container.innerHTML = `
                <div class="min-h-screen flex items-center justify-center">
                    <div class="text-center">
                        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                        <h2 class="text-xl font-semibold text-gray-700">Loading ETF Dashboard...</h2>
                        <p class="text-gray-500 mt-2">Fetching data for ${this.currentSymbol}</p>
                    </div>
                </div>
            `;
        }
    }

    showError(message) {
        const container = document.getElementById('etf-dashboard');
        if (!container) return;

        container.innerHTML = `
            <div class="min-h-screen flex items-center justify-center">
                <div class="text-center max-w-md">
                    <div class="text-red-600 mb-4">
                        <i data-lucide="alert-circle" class="w-16 h-16 mx-auto"></i>
                    </div>
                    <h2 class="text-xl font-semibold text-gray-700 mb-2">Error Loading Data</h2>
                    <p class="text-gray-500">${message}</p>
                    <button 
                        id="retry-btn"
                        onclick="window.etfDashboard.loadDashboardData().then(() => window.etfDashboard.render())"
                        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        `;
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    render() {
        console.log('Rendering ETF Dashboard...');
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
        
        // Render charts after DOM is updated
        setTimeout(() => {
            console.log('Rendering charts, price_data length:', this.data.price_data?.length || 0);
            this.renderCharts();
            this.renderSearchResults(); // Render search results if needed
            if (window.lucide) {
                window.lucide.createIcons();
            }
        }, 500); // Increased timeout to ensure DOM is ready
    }

    getDashboardHTML() {
        const basicInfo = this.data.basic_info || {};
        const riskMetrics = this.data.risk_metrics || {};
        const latestIndicator = this.data.technical_indicators && this.data.technical_indicators.length > 0 
            ? this.data.technical_indicators[this.data.technical_indicators.length - 1] 
            : null;

        return `
            <div class="min-h-screen bg-gray-50" style="padding: 2rem;">
                <div class="mx-auto max-w-7xl">
                    ${this.getHeaderHTML()}
                    ${this.getBasicInfoCardsHTML(basicInfo)}
                    ${this.getPriceChartHTML()}
                    ${this.getHoldingsSectionHTML()}
                    ${this.getRiskMetricsHTML(riskMetrics)}
                    ${this.getTechnicalIndicatorsHTML(latestIndicator)}
                    ${this.getDistributionChartsHTML()}
                    ${this.getDividendHistoryHTML()}
                    ${this.getFooterHTML()}
                </div>
            </div>
        `;
    }

    getHeaderHTML() {
        return `
            <div style="margin-bottom: 1.5rem;">
                <div style="margin-bottom: 1rem;">
                    <h1 style="font-size: 1.875rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">ETF Dashboard</h1>
                    <p style="color: #64748b; font-size: 0.75rem; margin: 0;">${this.data.data_source || 'yfinance'} • Real-time data</p>
                </div>
                
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <div class="etf-search-container" style="position: relative; display: flex; align-items: center; gap: 8px;">
                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Symbol:</label>
                        <div style="position: relative;">
                            <input 
                                type="text" 
                                id="symbol-input" 
                                value="${this.currentSymbol}" 
                                placeholder="Search ETF (e.g., SPY, QQQ)"
                                style="
                                    background: white;
                                    border: 1px solid #e2e8f0;
                                    border-radius: 8px;
                                    padding: 10px 14px;
                                    font-size: 14px;
                                    font-weight: 600;
                                    color: #1e293b;
                                    min-width: 200px;
                                    max-width: 300px;
                                    text-transform: uppercase;
                                " 
                                onkeypress="if(event.key === 'Enter') { window.etfDashboard.handleSymbolChange(); }"
                            >
                            <div id="etf-search-results" style="display: none;"></div>
                        </div>
                        <button 
                            onclick="window.etfDashboard.handleSymbolChange()"
                            class="btn-primary"
                            style="padding: 10px 16px; border-radius: 8px; cursor: pointer;"
                        >
                            Load
                        </button>
                    </div>
                    
                    <button 
                        id="refresh-btn"
                        class="btn-outline"
                        style="padding: 10px 16px; border-radius: 8px; cursor: pointer;"
                    >
                        <i data-lucide="refresh-cw" style="width: 16px; height: 16px; display: inline-block;"></i>
                        Refresh
                    </button>
                </div>
            </div>
        `;
    }

    getBasicInfoCardsHTML(basicInfo) {
        if (!basicInfo) {
            basicInfo = {};
        }
        
        // Try to get price from price_data if basic_info doesn't have it
        let currentPrice = basicInfo.current_price || 0;
        let previousClose = basicInfo.previous_close || 0;
        let dayChange = basicInfo.day_change || 0;
        let dayChangePercent = basicInfo.day_change_percent || 0;
        
        // If no price in basic_info, try to get from price_data
        if (currentPrice === 0 && this.data.price_data && this.data.price_data.length > 0) {
            const latest = this.data.price_data[this.data.price_data.length - 1];
            currentPrice = latest.close || 0;
            if (this.data.price_data.length > 1) {
                previousClose = this.data.price_data[this.data.price_data.length - 2].close || currentPrice;
                dayChange = currentPrice - previousClose;
                dayChangePercent = previousClose > 0 ? (dayChange / previousClose * 100) : 0;
            }
        }
        
        const isPositive = dayChange >= 0;
        const name = basicInfo.name || basicInfo.symbol || this.currentSymbol || '—';

        return `
            <div style="margin-bottom: 1rem;">
                <h2 style="font-size: 1.25rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">${name}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Current Price</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b;">
                        ${currentPrice > 0 ? `$${currentPrice.toFixed(2)}` : '—'}
                    </div>
                    ${currentPrice > 0 && (dayChange !== 0 || dayChangePercent !== 0) ? `
                    <div style="font-size: 0.875rem; color: ${isPositive ? '#16a34a' : '#dc2626'}; margin-top: 0.25rem;">
                        ${isPositive ? '+' : ''}${dayChange.toFixed(2)} (${isPositive ? '+' : ''}${dayChangePercent.toFixed(2)}%)
                    </div>
                    ` : ''}
                </div>
                
                <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Assets Under Management</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b;">
                        ${basicInfo.aum ? `$${(basicInfo.aum / 1e9).toFixed(1)}B` : '—'}
                    </div>
                </div>
                
                <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Expense Ratio</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b;">
                        ${basicInfo.expense_ratio ? `${(basicInfo.expense_ratio * 100).toFixed(2)}%` : '—'}
                    </div>
                </div>
                
                <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Dividend Yield</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b;">
                        ${basicInfo.dividend_yield ? `${(basicInfo.dividend_yield * 100).toFixed(2)}%` : '—'}
                    </div>
                </div>
            </div>
        `;
    }

    getPriceChartHTML() {
        return `
            <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Price History</h2>
                <div id="price-chart" style="height: 400px;"></div>
            </div>
        `;
    }

    getHoldingsSectionHTML() {
        const holdings = this.data.top_holdings || [];
        const totalHoldings = this.data.total_holdings_count || 0;
        const concentration = this.data.holdings_concentration || 0;

        return `
            <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">
                    Top Holdings
                    <span style="font-size: 0.875rem; font-weight: 400; color: #64748b; margin-left: 0.5rem;">
                        (${holdings.length} of ${totalHoldings} total, ${concentration.toFixed(1)}% concentration)
                    </span>
                </h2>
                <div class="overflow-x-auto">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <th style="text-align: left; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Symbol</th>
                                <th style="text-align: left; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Name</th>
                                <th style="text-align: right; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Weight</th>
                                <th style="text-align: right; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Price</th>
                                <th style="text-align: right; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${holdings.map(holding => `
                                <tr style="border-bottom: 1px solid #f1f5f9;">
                                    <td style="padding: 0.75rem; font-weight: 600; color: #1e293b;">${holding.symbol || '—'}</td>
                                    <td style="padding: 0.75rem; color: #64748b;">${holding.name || '—'}</td>
                                    <td style="padding: 0.75rem; text-align: right; color: #1e293b;">${holding.weight ? `${holding.weight.toFixed(2)}%` : '—'}</td>
                                    <td style="padding: 0.75rem; text-align: right; color: #1e293b;">${holding.price ? `$${holding.price.toFixed(2)}` : '—'}</td>
                                    <td style="padding: 0.75rem; text-align: right; color: ${(holding.day_change_percent || 0) >= 0 ? '#16a34a' : '#dc2626'};">
                                        ${holding.day_change_percent ? `${holding.day_change_percent >= 0 ? '+' : ''}${holding.day_change_percent.toFixed(2)}%` : '—'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    getRiskMetricsHTML(riskMetrics) {
        return `
            <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Risk Metrics</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Volatility (1Y)</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${riskMetrics.volatility_1y ? `${riskMetrics.volatility_1y.toFixed(2)}%` : '—'}
                        </div>
                    </div>
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Beta</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${riskMetrics.beta ? riskMetrics.beta.toFixed(2) : '—'}
                        </div>
                    </div>
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Sharpe Ratio</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${riskMetrics.sharpe_ratio ? riskMetrics.sharpe_ratio.toFixed(2) : '—'}
                        </div>
                    </div>
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Max Drawdown</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${riskMetrics.max_drawdown ? `${riskMetrics.max_drawdown.toFixed(2)}%` : '—'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getTechnicalIndicatorsHTML(indicator) {
        if (!indicator) return '';

        return `
            <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Technical Indicators</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">RSI (14)</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${indicator.rsi_14 ? indicator.rsi_14.toFixed(2) : '—'}
                        </div>
                    </div>
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">MACD</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${indicator.macd ? indicator.macd.toFixed(4) : '—'}
                        </div>
                    </div>
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">SMA 20</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${indicator.sma_20 ? `$${indicator.sma_20.toFixed(2)}` : '—'}
                        </div>
                    </div>
                    <div>
                        <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">SMA 50</h3>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b;">
                            ${indicator.sma_50 ? `$${indicator.sma_50.toFixed(2)}` : '—'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getDistributionChartsHTML() {
        const sectors = this.data.sector_distribution || [];
        const industries = this.data.industry_distribution || [];

        return `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem;">
                <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Sector Distribution</h2>
                    <div id="sector-chart" style="height: 300px;"></div>
                </div>
                
                <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Industry Distribution</h2>
                    <div id="industry-chart" style="height: 300px;"></div>
                </div>
            </div>
        `;
    }

    getDividendHistoryHTML() {
        const dividends = this.data.dividend_history || [];
        
        if (dividends.length === 0) return '';

        return `
            <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem;">Dividend History</h2>
                <div class="overflow-x-auto">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <th style="text-align: left; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Date</th>
                                <th style="text-align: right; padding: 0.75rem; font-size: 0.875rem; font-weight: 500; color: #64748b;">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${dividends.slice(0, 10).map(dividend => `
                                <tr style="border-bottom: 1px solid #f1f5f9;">
                                    <td style="padding: 0.75rem; color: #64748b;">${dividend.date}</td>
                                    <td style="padding: 0.75rem; text-align: right; color: #1e293b; font-weight: 600;">$${dividend.amount.toFixed(4)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    getFooterHTML() {
        return `
            <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; text-align: center; color: #64748b; font-size: 0.75rem;">
                <p>ETF Dashboard • Data source: ${this.data.data_source || 'yfinance'} • Last updated: ${new Date().toLocaleString()}</p>
            </div>
        `;
    }

    renderCharts() {
        // Wait a bit to ensure all scripts are loaded
        const checkAndRender = () => {
            // Check if Recharts is available (might be loaded as window.Recharts or Recharts)
            const hasRecharts = (typeof Recharts !== 'undefined') || (typeof window !== 'undefined' && window.Recharts);
            
            if (!hasRecharts) {
                console.warn('Recharts not yet loaded, waiting...');
                // Try to load it dynamically as fallback
                if (!document.querySelector('script[src*="recharts"]')) {
                    const script = document.createElement('script');
                    script.src = 'https://unpkg.com/recharts@2.8.0/umd/Recharts.js';
                    script.onload = () => {
                        console.log('Recharts loaded dynamically');
                        window.Recharts = Recharts || window.Recharts;
                        this.renderPriceChart();
                        this.renderSectorChart();
                        this.renderIndustryChart();
                    };
                    script.onerror = () => {
                        console.error('Failed to load Recharts dynamically');
                    };
                    document.head.appendChild(script);
                } else {
                    // Script exists but not loaded yet, wait a bit more
                    setTimeout(checkAndRender, 200);
                }
                return;
            }

            // Use Recharts from window or global scope
            window.Recharts = window.Recharts || Recharts;
            console.log('Recharts available, rendering charts');
            
            this.renderPriceChart();
            this.renderSectorChart();
            this.renderIndustryChart();
        };
        
        // Start checking
        checkAndRender();
    }

    renderPriceChart() {
        const priceData = this.data.price_data || [];
        console.log('Rendering price chart, data length:', priceData.length);
        console.log('Price data sample:', priceData.slice(0, 3));
        
        if (priceData.length === 0) {
            console.warn('No price data available for chart');
            const chartContainer = document.getElementById('price-chart');
            if (chartContainer) {
                chartContainer.innerHTML = '<p style="text-align: center; color: #64748b; padding: 2rem;">No price history data available</p>';
            }
            return;
        }

        const chartContainer = document.getElementById('price-chart');
        if (!chartContainer) {
            console.error('Price chart container not found');
            return;
        }

        // Check if Recharts is available - try multiple ways
        let RechartsLib = null;
        
        // Try window.Recharts first (most common for UMD builds)
        if (typeof window !== 'undefined' && window.Recharts) {
            RechartsLib = window.Recharts;
            console.log('Found Recharts in window.Recharts');
        }
        // Try global Recharts
        else if (typeof Recharts !== 'undefined') {
            RechartsLib = Recharts;
            window.Recharts = Recharts; // Store for future use
            console.log('Found Recharts in global scope');
        }
        // Try to access via window object with different casing
        else if (typeof window !== 'undefined') {
            if (window['Recharts']) {
                RechartsLib = window['Recharts'];
                console.log('Found Recharts via window["Recharts"]');
            } else if (window['recharts']) {
                RechartsLib = window['recharts'];
                window.Recharts = RechartsLib;
                console.log('Found Recharts via window["recharts"]');
            }
        }
        
        if (!RechartsLib) {
            console.error('Recharts is not loaded');
            console.error('Available globals with "chart":', Object.keys(window).filter(k => k.toLowerCase().includes('chart')));
            console.error('React available:', typeof React !== 'undefined');
            console.error('ReactDOM available:', typeof ReactDOM !== 'undefined');
            
            // Show helpful error message
            chartContainer.innerHTML = `
                <div style="text-align: center; color: #dc2626; padding: 2rem;">
                    <p style="margin-bottom: 1rem;">Chart library not loaded.</p>
                    <p style="font-size: 0.875rem; color: #64748b;">Please check browser console for details.</p>
                    <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        Refresh Page
                    </button>
                </div>
            `;
            return;
        }

        // Store in window for future use
        window.Recharts = RechartsLib;
        
        const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } = RechartsLib;

        // Process data - handle different date formats
        const data = priceData.map((bar, index) => {
            let dateStr;
            try {
                // Handle different date formats
                if (typeof bar.date === 'string') {
                    // Try parsing ISO date string
                    const date = new Date(bar.date);
                    dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                } else if (bar.date instanceof Date) {
                    dateStr = bar.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                } else {
                    // Fallback to index
                    dateStr = `Day ${index + 1}`;
                }
            } catch (e) {
                console.warn('Error parsing date:', bar.date, e);
                dateStr = `Day ${index + 1}`;
            }
            
            return {
                date: dateStr,
                close: parseFloat(bar.close) || 0,
                fullDate: bar.date // Keep original for tooltip
            };
        }).filter(d => d.close > 0); // Filter out invalid data

        if (data.length === 0) {
            console.warn('No valid price data after processing');
            chartContainer.innerHTML = '<p style="text-align: center; color: #64748b; padding: 2rem;">No valid price data available</p>';
            return;
        }

        console.log('Processed chart data length:', data.length);
        console.log('Chart data sample:', data.slice(0, 3));

        try {
            const chart = React.createElement(ResponsiveContainer, { width: "100%", height: 400 },
                React.createElement(LineChart, { data: data, margin: { top: 5, right: 20, left: 10, bottom: 5 } },
                    React.createElement(CartesianGrid, { strokeDasharray: "3 3" }),
                    React.createElement(XAxis, { 
                        dataKey: "date", 
                        tick: { fontSize: 12 },
                        angle: -45,
                        textAnchor: "end",
                        height: 80
                    }),
                    React.createElement(YAxis, { 
                        tick: { fontSize: 12 },
                        domain: ['dataMin', 'dataMax']
                    }),
                    React.createElement(Tooltip, { 
                        contentStyle: { backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' },
                        formatter: (value) => `$${value.toFixed(2)}`,
                        labelFormatter: (label) => `Date: ${label}`
                    }),
                    React.createElement(Line, { 
                        type: "monotone", 
                        dataKey: "close", 
                        stroke: "#3b82f6", 
                        strokeWidth: 2,
                        dot: false,
                        activeDot: { r: 6 }
                    })
                )
            );

            const root = ReactDOM.createRoot(chartContainer);
            root.render(chart);
            console.log('Price chart rendered successfully');
        } catch (error) {
            console.error('Error rendering price chart:', error);
            chartContainer.innerHTML = `<p style="text-align: center; color: #dc2626; padding: 2rem;">Error rendering chart: ${error.message}</p>`;
        }
    }

    renderSectorChart() {
        const sectors = this.data.sector_distribution || [];
        if (sectors.length === 0) return;

        const chartContainer = document.getElementById('sector-chart');
        if (!chartContainer) return;

        const { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } = Recharts;

        const data = sectors.map(s => ({ name: s.sector, value: s.weight }));

        const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

        const chart = React.createElement(ResponsiveContainer, { width: "100%", height: 300 },
            React.createElement(PieChart,
                React.createElement(Pie,
                    {
                        data: data,
                        cx: "50%",
                        cy: "50%",
                        labelLine: false,
                        label: ({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`,
                        outerRadius: 80,
                        fill: "#8884d8",
                        dataKey: "value"
                    },
                    data.map((entry, index) => React.createElement(Cell, { key: `cell-${index}`, fill: COLORS[index % COLORS.length] }))
                ),
                React.createElement(Tooltip),
                React.createElement(Legend)
            )
        );

        const root = ReactDOM.createRoot(chartContainer);
        root.render(chart);
    }

    renderIndustryChart() {
        const industries = this.data.industry_distribution || [];
        if (industries.length === 0) return;

        const chartContainer = document.getElementById('industry-chart');
        if (!chartContainer) return;

        const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } = Recharts;

        const data = industries.slice(0, 10).map(i => ({ name: i.industry, value: i.weight }));

        const chart = React.createElement(ResponsiveContainer, { width: "100%", height: 300 },
            React.createElement(BarChart, { data: data },
                React.createElement(CartesianGrid, { strokeDasharray: "3 3" }),
                React.createElement(XAxis, { dataKey: "name", angle: -45, textAnchor: "end", height: 100, tick: { fontSize: 10 } }),
                React.createElement(YAxis, { tick: { fontSize: 12 } }),
                React.createElement(Tooltip),
                React.createElement(Bar, { dataKey: "value", fill: "#3b82f6" })
            )
        );

        const root = ReactDOM.createRoot(chartContainer);
        root.render(chart);
    }
}

// Initialize dashboard when ETF tab is shown (handled in index.html)
// The dashboard will be initialized when the tab is activated

