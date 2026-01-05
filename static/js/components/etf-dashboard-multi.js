/**
 * ETF Dashboard - Multi-ETF Comparison
 * Based on reference design with exact functionality
 * White background theme
 */
class ETFDashboardMulti {
    constructor() {
        console.log('ETFDashboardMulti constructor called');
        this.defaultETFs = ['VOO', 'SPY', 'QQQ', 'ARKK', 'TECL', 'XLK', 'SCHD', 'GLD', 'SOXX', 'VTWG'];
        this.etfData = [];
        this.state = {
            window: '3Y',
            benchmark: 'SPY',
            sort: 'score',
            filter: '',
            pinned: new Set(['VOO', 'QQQ', 'TECL']), // Default pinned (shown in charts)
            selected: 'VOO',
            profileIndex: 0
        };
        this.charts = {
            growth: null,
            drawdown: null,
            scatter: null
        };
        
        this.init();
    }

    getDataSourcesSummary() {
        if (this.etfData.length === 0) return 'Loading...';
        const sources = new Set();
        this.etfData.forEach(d => {
            if (d.dataSource) {
                sources.add(d.dataSource);
            }
        });
        const sourceList = Array.from(sources);
        if (sourceList.length === 0) return 'Unknown';
        if (sourceList.length === 1) return sourceList[0] === 'polygon' ? 'Polygon.io' : 'Yahoo Finance';
        return 'Polygon.io + Yahoo Finance';
    }

    async init() {
        console.log('Initializing Multi-ETF Dashboard...');
        this.setupEventListeners();
        await this.loadAllETFs();
        this.render();
    }

    async loadAllETFs(days = 1095) {
        try {
            console.log(`Loading data for all ETFs (${days} days)...`);
            this.showLoading(true);

            // Load data for all default ETFs concurrently
            const promises = this.defaultETFs.map(symbol => 
                this.fetchETFData(symbol, days).catch(err => {
                    console.error(`Error loading ${symbol}:`, err);
                    return null;
                })
            );

            const results = await Promise.all(promises);
            this.etfData = results.filter(r => r !== null);
            
            // Calculate composite scores
            this.calculateCompositeScores();
            
            console.log(`Loaded ${this.etfData.length} ETFs`);
        } catch (error) {
            console.error('Error loading ETFs:', error);
            this.showError(`Error: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    async fetchETFData(symbol, days = 1095) {
        try {
            const response = await fetch('/api/v1/etf/dashboard/data', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    date_range_days: days
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Extract and calculate metrics
            const basicInfo = data.basic_info || {};
            const priceData = data.price_data || [];
            const riskMetrics = data.risk_metrics || {};
            
            // Calculate metrics from price data
            let cagr = 0, volatility = 0, sharpe = 0, sortino = 0, maxDD = 0, calmar = 0;
            
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
                    
                    // Calculate downside deviation for Sortino
                    const downsideReturns = returns.filter(r => r < 0);
                    const downsideVariance = downsideReturns.length > 0 
                        ? downsideReturns.reduce((sum, r) => sum + Math.pow(r, 2), 0) / downsideReturns.length
                        : 0;
                    const downsideVol = Math.sqrt(downsideVariance * 252);
                    
                    // Sharpe and Sortino ratios
                    const riskFreeRate = 0.02;
                    sharpe = volatility > 0 ? (cagr - riskFreeRate) / volatility : 0;
                    sortino = downsideVol > 0 ? (cagr - riskFreeRate) / downsideVol : 0;
                }

                // Calculate max drawdown
                let peak = startPrice;
                for (const bar of priceData) {
                    peak = Math.max(peak, bar.close);
                    const drawdown = (bar.close - peak) / peak;
                    maxDD = Math.min(maxDD, drawdown);
                }
                
                // Calmar ratio
                calmar = maxDD !== 0 ? cagr / Math.abs(maxDD) : 0;
            }

            // Get beta from risk metrics or calculate
            const beta = riskMetrics.beta || 1.0;
            const trackingError = riskMetrics.tracking_error || 0.02;
            
            // Extract other metrics
            const expense = basicInfo.expense_ratio || 0.001;
            const aum = basicInfo.aum || 0;
            const volume = basicInfo.avg_volume || basicInfo.volume || 0;
            const currentPrice = basicInfo.current_price || 0;
            const dollarVolume = (currentPrice * volume) / 1e9; // Convert to billions
            const spread = basicInfo.bid_ask_spread || 0.01;

            const result = {
                t: symbol,
                name: basicInfo.name || symbol,
                asset: this.getAssetClass(symbol),
                cagr: cagr,
                vol: volatility,
                sharpe: sharpe,
                sortino: sortino,
                mdd: maxDD,
                calmar: calmar,
                beta: beta,
                te: trackingError,
                expense: expense,
                aum: aum / 1e9, // Convert to billions
                dv: dollarVolume,
                spread: spread,
                priceData: priceData,
                currentPrice: currentPrice,
                dataSource: data.data_source || 'unknown' // Track data source
            };
            
            console.log(`Fetched ${symbol}: ${priceData.length} price points, data source: ${result.dataSource}`);
            return result;
        } catch (error) {
            console.error(`Error fetching data for ${symbol}:`, error);
            return null;
        }
    }

    getAssetClass(symbol) {
        const assetMap = {
            'VOO': 'Equity US Large Cap',
            'SPY': 'Equity US Large',
            'QQQ': 'Equity US Tech',
            'ARKK': 'Equity US Innovation',
            'TECL': 'Equity US Tech Leveraged',
            'XLK': 'Equity US Technology',
            'SCHD': 'Equity US Dividend',
            'GLD': 'Commodity Gold',
            'SOXX': 'Equity US Semiconductor',
            'VTWG': 'Equity US Small Growth'
        };
        return assetMap[symbol] || 'Unknown';
    }

    calculateCompositeScores() {
        if (this.etfData.length === 0) return;

        // Score weights
        const W = { perf: 0.30, risk: 0.25, eff: 0.25, cost: 0.10, liq: 0.10 };

        // Calculate z-scores
        const zScores = (items, key, invert = false) => {
            const vals = items.map(d => d[key]).filter(v => !isNaN(v) && v !== null);
            if (vals.length === 0) return items.map(() => 0);
            
            const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
            const sd = Math.sqrt(vals.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / vals.length) || 1;
            
            return items.map(d => {
                const val = d[key];
                if (isNaN(val) || val === null) return 0;
                const z = (val - mean) / sd;
                return invert ? -z : z;
            });
        };

        const zCAGR = zScores(this.etfData, 'cagr');
        const zVol = zScores(this.etfData, 'vol', true);
        const zMDD = zScores(this.etfData, 'mdd'); // mdd is negative; higher (less negative) is better
        const zShar = zScores(this.etfData, 'sharpe');
        const zSor = zScores(this.etfData, 'sortino');
        const zCal = zScores(this.etfData, 'calmar');
        const zExp = zScores(this.etfData, 'expense', true);
        const zDV = zScores(this.etfData, 'dv');
        const zSpr = zScores(this.etfData, 'spread', true);

        this.etfData.forEach((d, i) => {
            const perf = zCAGR[i];
            const risk = 0.55 * zMDD[i] + 0.45 * zVol[i];
            const eff = 0.45 * zShar[i] + 0.35 * zSor[i] + 0.20 * zCal[i];
            const cost = zExp[i];
            const liq = 0.65 * zDV[i] + 0.35 * zSpr[i];
            const scoreZ = W.perf * perf + W.risk * risk + W.eff * eff + W.cost * cost + W.liq * liq;

            // Map z to 0~100
            d.score = Math.round(Math.max(0, Math.min(100, 50 + scoreZ * 12)));
            d._sub = { perf, risk, eff, cost, liq };
        });
    }

    setupEventListeners() {
        // Remove old listeners to prevent duplicates
        const windowSel = document.getElementById('etf-window-sel');
        const benchSel = document.getElementById('etf-bench-sel');
        const sortSel = document.getElementById('etf-sort-sel');
        const searchInput = document.getElementById('etf-search-input');
        const resetBtn = document.getElementById('etf-reset-btn');

        // Window selector
        if (windowSel) {
            // Remove existing listeners by cloning
            const newWindowSel = windowSel.cloneNode(true);
            windowSel.parentNode.replaceChild(newWindowSel, windowSel);
            newWindowSel.addEventListener('change', (e) => {
                this.state.window = e.target.value;
                const days = e.target.value === '1Y' ? 365 : e.target.value === '3Y' ? 1095 : e.target.value === '5Y' ? 1825 : 3650;
                this.loadAllETFs(days).then(() => this.render());
            });
            // Restore value
            newWindowSel.value = this.state.window || '3Y';
        }

        // Benchmark selector
        if (benchSel) {
            const newBenchSel = benchSel.cloneNode(true);
            benchSel.parentNode.replaceChild(newBenchSel, benchSel);
            newBenchSel.addEventListener('change', (e) => {
                this.state.benchmark = e.target.value;
                this.render();
            });
            newBenchSel.value = this.state.benchmark || 'SPY';
        }

        // Sort selector
        if (sortSel) {
            const newSortSel = sortSel.cloneNode(true);
            sortSel.parentNode.replaceChild(newSortSel, sortSel);
            newSortSel.addEventListener('change', (e) => {
                this.state.sort = e.target.value;
                this.render();
            });
            newSortSel.value = this.state.sort || 'score';
        }

        // Search input
        if (searchInput) {
            const newSearchInput = searchInput.cloneNode(true);
            searchInput.parentNode.replaceChild(newSearchInput, searchInput);
            newSearchInput.addEventListener('input', (e) => {
                this.state.filter = e.target.value;
                this.render();
            });
            newSearchInput.value = this.state.filter || '';
        }

        // Add ETF button with search suggestions
        const addBtn = document.getElementById('etf-add-btn');
        const addInput = document.getElementById('etf-add-input');
        if (addBtn && addInput) {
            const newAddBtn = addBtn.cloneNode(true);
            const newAddInput = addInput.cloneNode(true);
            addBtn.parentNode.replaceChild(newAddBtn, addBtn);
            addInput.parentNode.replaceChild(newAddInput, addInput);
            
            // Create suggestions dropdown
            const suggestionsContainer = document.createElement('div');
            suggestionsContainer.id = 'etf-add-suggestions';
            suggestionsContainer.style.cssText = 'position: absolute; background: white; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-height: 200px; overflow-y: auto; z-index: 1000; display: none; margin-top: 4px;';
            newAddInput.parentNode.style.position = 'relative';
            newAddInput.parentNode.appendChild(suggestionsContainer);
            
            let searchTimeout = null;
            let suggestions = [];
            
            const showSuggestions = (results) => {
                if (results.length === 0) {
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                
                suggestionsContainer.innerHTML = results.map(etf => `
                    <div class="etf-suggestion-item" data-symbol="${etf.symbol}" 
                         style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f1f5f9; 
                                ${this.state.pinned.has(etf.symbol) ? 'opacity: 0.5;' : ''}">
                        <div style="font-weight: 500; color: #1e293b;">${etf.symbol}</div>
                        <div style="font-size: 11px; color: #64748b;">${etf.name || ''}</div>
                    </div>
                `).join('');
                
                suggestionsContainer.style.display = 'block';
                
                // Add click handlers
                suggestionsContainer.querySelectorAll('.etf-suggestion-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const symbol = item.getAttribute('data-symbol');
                        newAddInput.value = symbol;
                        suggestionsContainer.style.display = 'none';
                        handleAdd();
                    });
                });
            };
            
            // Search for ETFs as user types
            newAddInput.addEventListener('input', async (e) => {
                const query = e.target.value.trim().toUpperCase();
                
                if (searchTimeout) clearTimeout(searchTimeout);
                
                if (query.length < 1) {
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                
                searchTimeout = setTimeout(async () => {
                    try {
                        const response = await fetch(`/api/v1/etf/search?query=${encodeURIComponent(query)}&limit=5`);
                        if (response.ok) {
                            const data = await response.json();
                            suggestions = data.results || [];
                            showSuggestions(suggestions);
                        }
                    } catch (error) {
                        console.error('Error searching ETFs:', error);
                    }
                }, 300);
            });
            
            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!newAddInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                    suggestionsContainer.style.display = 'none';
                }
            });
            
            const handleAdd = async () => {
                const symbol = newAddInput.value.trim().toUpperCase();
                if (!symbol) return;
                
                suggestionsContainer.style.display = 'none';
                
                // Check if already added
                if (this.state.pinned.has(symbol)) {
                    alert(`${symbol} is already added`);
                    newAddInput.value = '';
                    return;
                }
                
                // Check if already in etfData
                const existing = this.etfData.find(d => d.t === symbol);
                if (existing) {
                    this.state.pinned.add(symbol);
                    this.state.selected = symbol;
                    this.render();
                    newAddInput.value = '';
                    return;
                }
                
                // Add to pinned and load data
                this.state.pinned.add(symbol);
                this.state.selected = symbol;
                newAddInput.value = '';
                newAddInput.disabled = true;
                newAddBtn.disabled = true;
                newAddBtn.textContent = 'Loading...';
                
                try {
                    const days = this.state.window === '1Y' ? 365 : this.state.window === '3Y' ? 1095 : this.state.window === '5Y' ? 1825 : 3650;
                    const newData = await this.fetchETFData(symbol, days);
                    if (newData) {
                        this.etfData.push(newData);
                        this.calculateCompositeScores();
                        this.render();
                    } else {
                        this.state.pinned.delete(symbol);
                        alert(`Failed to load data for ${symbol}. Please check if the ticker is correct.`);
                    }
                } catch (error) {
                    this.state.pinned.delete(symbol);
                    alert(`Error loading ${symbol}: ${error.message}`);
                } finally {
                    newAddInput.disabled = false;
                    newAddBtn.disabled = false;
                    newAddBtn.textContent = 'Add';
                }
            };
            
            newAddBtn.addEventListener('click', handleAdd);
            newAddInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (suggestions.length > 0 && suggestionsContainer.style.display !== 'none') {
                        // Use first suggestion
                        const firstItem = suggestionsContainer.querySelector('.etf-suggestion-item');
                        if (firstItem) {
                            firstItem.click();
                        }
                    } else {
                        handleAdd();
                    }
                }
            });
        }
        
        // Reset button
        if (resetBtn) {
            const newResetBtn = resetBtn.cloneNode(true);
            resetBtn.parentNode.replaceChild(newResetBtn, resetBtn);
            newResetBtn.addEventListener('click', () => {
                this.state = {
                    window: '3Y',
                    benchmark: 'SPY',
                    sort: 'score',
                    filter: '',
                    pinned: new Set(['VOO', 'QQQ', 'TECL']), // Default pinned (shown in charts)
                    selected: 'VOO',
                    tab: 'overview',
                    profileIndex: 0
                };
                this.loadAllETFs(1095).then(() => this.render());
            });
        }

        // Tab switching - use event delegation to avoid re-binding
        const tabContainer = document.querySelector('.etf-tabs');
        if (tabContainer) {
            // Remove old listener if exists
            if (this._tabClickHandler) {
                tabContainer.removeEventListener('click', this._tabClickHandler);
            }
            this._tabClickHandler = (e) => {
                if (e.target.classList.contains('etf-tab')) {
                    const tab = e.target.getAttribute('data-tab');
                    this.state.tab = tab;
                    this.setTab(tab);
                }
            };
            tabContainer.addEventListener('click', this._tabClickHandler);
        }
    }

    setTab(tab) {
        ['overview', 'compare', 'risk', 'costliq', 'notes'].forEach(id => {
            const section = document.getElementById(`etf-section-${id}`);
            if (section) {
                section.classList.toggle('etf-hidden', id !== tab);
            }
        });

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
                <button onclick="window.etfDashboard.loadAllETFs().then(() => window.etfDashboard.render())" 
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

        if (this.etfData.length === 0) {
            this.showError('No ETF data available');
            return;
        }

        container.innerHTML = this.getDashboardHTML();
        
        setTimeout(() => {
            this.renderPinLegend();
            this.renderKPITable();
            this.renderQuickProfile();
            this.renderCharts();
            this.renderCompareTable();
            this.renderRiskTable();
            this.renderCostLiqTable();
            // Re-bind event listeners after DOM is updated
            this.setupEventListeners();
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
            .etf-table tbody tr.pinned {
                background: rgba(59, 130, 246, 0.05);
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
            .etf-rank {
                opacity: 0.8;
                font-size: 11px;
                color: #94a3b8;
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
                        <div style="font-size: 1.5rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">ETF Evaluation Dashboard <span class="etf-badge">Live</span></div>
                        <div class="etf-small" style="color: #64748b;">
                            ${this.etfData.length} ETFs • 
                            Data: ${this.getDataSourcesSummary()} • 
                            Real-time
                        </div>
                    </div>
                </div>

                <div class="etf-controls">
                    <div class="etf-row">
                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Window:</label>
                        <select id="etf-window-sel">
                            <option value="1Y">1Y</option>
                            <option value="3Y" selected>3Y</option>
                            <option value="5Y">5Y</option>
                            <option value="MAX">MAX</option>
                        </select>

                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Benchmark:</label>
                        <select id="etf-bench-sel">
                            <option value="SPY" selected>SPY</option>
                            <option value="AGG">AGG</option>
                            <option value="CUSTOM">Custom</option>
                        </select>

                        <label style="font-size: 14px; font-weight: 500; color: #475569;">Sort:</label>
                        <select id="etf-sort-sel">
                            <option value="score" selected>Composite Score</option>
                            <option value="cagr">CAGR</option>
                            <option value="sharpe">Sharpe</option>
                            <option value="mdd">Max Drawdown</option>
                            <option value="expense">Expense Ratio</option>
                            <option value="liquidity">Liquidity</option>
                        </select>

                        <input id="etf-search-input" type="search" placeholder="Filter tickers (e.g. QQQ)" style="width: 200px;" />
                        <input id="etf-add-input" type="text" placeholder="Add ETF (e.g. SPY)" style="width: 150px;" />
                        <button class="primary" id="etf-add-btn" style="padding: 6px 12px;">Add</button>
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
        return `
            <section id="etf-section-overview" class="etf-grid cols-12">
                <div class="etf-card" style="grid-column: span 12;">
                    <div class="etf-row">
                        <h3 style="margin: 0;">KPI Ribbon (click ticker to pin)</h3>
                        <div class="etf-spacer"></div>
                        <div id="etf-pin-legend"></div>
                    </div>
                    <div id="etf-kpi-table" style="margin-top: 10px;"></div>
                </div>

                <div class="etf-card" style="grid-column: span 8;">
                    <div class="etf-row">
                        <h3 style="margin: 0;">Normalized Growth (100 = start)</h3>
                        <div class="etf-spacer"></div>
                        <span class="etf-small">Toggle pinned ETFs for clarity</span>
                    </div>
                    <div style="position: relative; height: 400px;">
                        <canvas id="etf-chart-growth"></canvas>
                    </div>
                </div>

                <div class="etf-card" style="grid-column: span 4;">
                    <h3>ETF Quick Profile</h3>
                    <div id="etf-quick-profile" class="etf-small"></div>
                </div>

                <div class="etf-card" style="grid-column: span 6;">
                    <h3>Drawdown Curve</h3>
                    <div style="position: relative; height: 320px;">
                        <canvas id="etf-chart-dd"></canvas>
                    </div>
                </div>

                <div class="etf-card" style="grid-column: span 6;">
                    <div class="etf-row">
                        <h3 style="margin: 0;">Risk vs Return (bubble size = AUM)</h3>
                        <div class="etf-spacer"></div>
                        <span class="etf-small etf-mono">x=Vol • y=CAGR</span>
                    </div>
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
                    <div class="etf-row">
                        <h3 style="margin: 0;">Metrics Matrix (ranked)</h3>
                        <div class="etf-spacer"></div>
                        <span class="etf-small">Ranks: 1 is best. For Max Drawdown & Expense, lower is better.</span>
                    </div>
                    <div id="etf-compare-table" style="overflow: auto; border-radius: 14px; border: 1px solid #e2e8f0; margin-top: 10px;"></div>
                </div>
            </section>
        `;
    }

    getRiskSectionHTML() {
        return `
            <section id="etf-section-risk" class="etf-grid cols-12 etf-hidden">
                <div class="etf-card" style="grid-column: span 7;">
                    <h3>Tail Risk Snapshot</h3>
                    <div id="etf-risk-table"></div>
                </div>
                <div class="etf-card" style="grid-column: span 5;">
                    <h3>Top Drawdown Episodes</h3>
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
                    <h3>Liquidity Diagnostics</h3>
                    <div id="etf-liq-table"></div>
                </div>
            </section>
        `;
    }

    getNotesSectionHTML() {
        return `
            <section id="etf-section-notes" class="etf-grid cols-12 etf-hidden">
                <div class="etf-card" style="grid-column: span 12;">
                    <h3>Metric Dictionary (click metric in Compare for quick help)</h3>
                    <div class="etf-small" style="line-height: 1.6;">
                        <div><span class="etf-mono">CAGR</span>: Annualized compound growth rate (区间依赖强)</div>
                        <div><span class="etf-mono">Vol</span>: Annualized volatility (标准差年化)</div>
                        <div><span class="etf-mono">Sharpe</span>: (Return - Rf) / Vol（非正态下会误导）</div>
                        <div><span class="etf-mono">Sortino</span>: (Return - Rf) / DownsideVol（更关注下行）</div>
                        <div><span class="etf-mono">Max Drawdown</span>: Maximum peak-to-trough decline（单样本偏差大）</div>
                        <div><span class="etf-mono">Calmar</span>: CAGR / |Max Drawdown|（风险约束友好）</div>
                        <div><span class="etf-mono">Tracking Error</span>: Relative volatility vs benchmark（指数跟踪能力）</div>
                        <div><span class="etf-mono">Expense Ratio</span>: Management fee（长期复利杀伤）</div>
                        <div><span class="etf-mono">Spread</span>: Bid-ask spread（交易成本核心）</div>
                    </div>
                </div>
            </section>
        `;
    }

    renderPinLegend() {
        const container = document.getElementById('etf-pin-legend');
        if (!container) return;

        container.innerHTML = '';
        Array.from(this.state.pinned).forEach(t => {
            const pill = document.createElement('span');
            pill.className = 'etf-pill etf-mono';
            pill.textContent = `${t} ✕`;
            pill.title = 'Click to unpin';
            pill.onclick = () => {
                this.state.pinned.delete(t);
                if (this.state.pinned.size === 0) this.state.pinned.add('VOO');
                this.render();
            };
            container.appendChild(pill);
        });
    }

    rank(items, key, higherBetter = true) {
        const arr = items.map(d => ({ t: d.t, v: d[key] }));
        arr.sort((a, b) => higherBetter ? b.v - a.v : a.v - b.v);
        const map = new Map();
        arr.forEach((x, i) => map.set(x.t, i + 1));
        return map;
    }

    fmtPct(x) {
        if (x == null || isNaN(x)) return '—';
        return (x * 100).toFixed(2) + '%';
    }

    fmtNum(x) {
        if (x == null || isNaN(x)) return '—';
        return Math.abs(x) >= 100 ? x.toFixed(0) : x.toFixed(2);
    }

    renderKPITable() {
        const container = document.getElementById('etf-kpi-table');
        if (!container || this.etfData.length === 0) return;

        const f = this.state.filter.trim().toUpperCase();
        let items = this.etfData.filter(d => !f || d.t.includes(f));

        // Sort
        const sortKey = this.state.sort;
        if (sortKey === 'score') items.sort((a, b) => b.score - a.score);
        if (sortKey === 'cagr') items.sort((a, b) => b.cagr - a.cagr);
        if (sortKey === 'sharpe') items.sort((a, b) => b.sharpe - a.sharpe);
        if (sortKey === 'mdd') items.sort((a, b) => b.mdd - a.mdd); // less negative = better
        if (sortKey === 'expense') items.sort((a, b) => a.expense - b.expense);
        if (sortKey === 'liquidity') items.sort((a, b) => b.dv - a.dv);

        const rkScore = this.rank(items, 'score', true);
        const rkCagr = this.rank(items, 'cagr', true);
        const rkVol = this.rank(items, 'vol', false);
        const rkShar = this.rank(items, 'sharpe', true);
        const rkMdd = this.rank(items, 'mdd', true);
        const rkExp = this.rank(items, 'expense', false);
        const rkDV = this.rank(items, 'dv', true);

        const header = `
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Score</th>
                    <th>CAGR</th>
                    <th>Vol</th>
                    <th>Sharpe</th>
                    <th>Sortino</th>
                    <th>Max DD</th>
                    <th>Calmar</th>
                    <th>Expense</th>
                    <th>AUM ($B)</th>
                    <th>Dollar Vol ($B/day)</th>
                    <th>Spread ($)</th>
                </tr>
            </thead>
        `;

        const rows = items.map(d => {
            const isPin = this.state.pinned.has(d.t);
            const scoreCls = d.score >= 70 ? 'etf-pos' : d.score >= 50 ? 'etf-neu' : 'etf-neg';
            return `
                <tr class="${isPin ? 'pinned' : ''}">
                    <td class="etf-mono"><span class="etf-pill" title="Click to pin/unpin" data-pin="${d.t}">${d.t}</span></td>
                    <td>${d.name}<div class="etf-small">${d.asset} • ${d.dataSource === 'polygon' ? 'Polygon.io' : d.dataSource === 'yfinance' ? 'Yahoo Finance' : 'Unknown'}</div></td>
                    <td class="${scoreCls} etf-mono" style="font-weight: 600;">${d.score} <span class="etf-rank">(#${rkScore.get(d.t)})</span></td>
                    <td class="etf-mono">${this.fmtPct(d.cagr)} <span class="etf-rank">(#${rkCagr.get(d.t)})</span></td>
                    <td class="etf-mono">${this.fmtPct(d.vol)} <span class="etf-rank">(#${rkVol.get(d.t)})</span></td>
                    <td class="etf-mono">${d.sharpe.toFixed(2)} <span class="etf-rank">(#${rkShar.get(d.t)})</span></td>
                    <td class="etf-mono">${d.sortino.toFixed(2)}</td>
                    <td class="etf-mono">${this.fmtPct(d.mdd)} <span class="etf-rank">(#${rkMdd.get(d.t)})</span></td>
                    <td class="etf-mono">${d.calmar.toFixed(2)}</td>
                    <td class="etf-mono">${this.fmtPct(d.expense)} <span class="etf-rank">(#${rkExp.get(d.t)})</span></td>
                    <td class="etf-mono">${this.fmtNum(d.aum)}</td>
                    <td class="etf-mono">${this.fmtNum(d.dv)} <span class="etf-rank">(#${rkDV.get(d.t)})</span></td>
                    <td class="etf-mono">${d.spread.toFixed(2)}</td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <div class="etf-kpi-ribbon">
                <table class="etf-table" style="min-width: 1100px;">
                    ${header}
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;

        // Pin click handlers
        container.querySelectorAll('[data-pin]').forEach(node => {
            node.onclick = () => {
                const t = node.getAttribute('data-pin');
                if (this.state.pinned.has(t)) {
                    this.state.pinned.delete(t);
                } else {
                    this.state.pinned.add(t);
                }
                this.state.selected = t;
                this.render();
            };
        });
    }

    renderQuickProfile() {
        const container = document.getElementById('etf-quick-profile');
        if (!container || this.etfData.length === 0) return;

        // Get all pinned ETFs
        const pinnedETFs = Array.from(this.state.pinned)
            .map(t => this.etfData.find(d => d.t === t))
            .filter(Boolean);
        
        if (pinnedETFs.length === 0) return;

        // Initialize profile index if not exists
        if (this.state.profileIndex === undefined) {
            this.state.profileIndex = 0;
        }
        
        // Ensure index is within bounds
        this.state.profileIndex = Math.max(0, Math.min(this.state.profileIndex, pinnedETFs.length - 1));
        
        const currentETF = pinnedETFs[this.state.profileIndex];
        const currentIndex = this.state.profileIndex;
        const totalCount = pinnedETFs.length;

        container.innerHTML = `
            <div class="etf-row" style="margin-bottom: 12px;">
                <div class="etf-pill etf-mono">${currentETF.t}</div>
                <div class="etf-spacer"></div>
                <div class="etf-badge">Score ${currentETF.score}/100</div>
            </div>
            
            ${totalCount > 1 ? `
            <div class="etf-row" style="margin-bottom: 12px; justify-content: center; gap: 8px;">
                <button id="etf-profile-prev" class="etf-profile-nav" ${currentIndex === 0 ? 'disabled' : ''} 
                        style="padding: 4px 12px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; cursor: pointer; font-size: 12px; color: #475569; ${currentIndex === 0 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                    ← Prev
                </button>
                <span class="etf-small" style="padding: 4px 12px; color: #64748b;">
                    ${currentIndex + 1} / ${totalCount}
                </span>
                <button id="etf-profile-next" class="etf-profile-nav" ${currentIndex === totalCount - 1 ? 'disabled' : ''}
                        style="padding: 4px 12px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; cursor: pointer; font-size: 12px; color: #475569; ${currentIndex === totalCount - 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                    Next →
                </button>
            </div>
            ` : ''}
            
            <div style="margin-top: 10px;">
                <div><b>${currentETF.name}</b></div>
                <div class="etf-small">${currentETF.asset}</div>
                <div class="etf-small" style="margin-top: 4px; color: #3b82f6;">
                    Data Source: ${currentETF.dataSource === 'polygon' ? 'Polygon.io (Real-time)' : currentETF.dataSource === 'yfinance' ? 'Yahoo Finance' : 'Unknown'}
                </div>
            </div>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 12px 0;" />
            <div class="etf-small">
                <div><span class="etf-mono">CAGR</span> ${this.fmtPct(currentETF.cagr)} • <span class="etf-mono">Vol</span> ${this.fmtPct(currentETF.vol)}</div>
                <div><span class="etf-mono">Sharpe</span> ${currentETF.sharpe.toFixed(2)} • <span class="etf-mono">Sortino</span> ${currentETF.sortino.toFixed(2)}</div>
                <div><span class="etf-mono">MaxDD</span> ${this.fmtPct(currentETF.mdd)} • <span class="etf-mono">Calmar</span> ${currentETF.calmar.toFixed(2)}</div>
                <div><span class="etf-mono">Expense</span> ${this.fmtPct(currentETF.expense)} • <span class="etf-mono">Spread</span> $${currentETF.spread.toFixed(2)}</div>
                <div><span class="etf-mono">AUM</span> $${this.fmtNum(currentETF.aum)}B • <span class="etf-mono">DollarVol</span> $${this.fmtNum(currentETF.dv)}B/day</div>
            </div>
            
            ${totalCount > 1 ? `
            <div style="margin-top: 12px; display: flex; gap: 4px; justify-content: center; flex-wrap: wrap;">
                ${pinnedETFs.map((etf, idx) => `
                    <button class="etf-profile-dot" data-index="${idx}" 
                            style="width: 8px; height: 8px; border-radius: 50%; border: none; 
                                   background: ${idx === currentIndex ? '#3b82f6' : '#cbd5e1'}; 
                                   cursor: pointer; padding: 0;">
                    </button>
                `).join('')}
            </div>
            ` : ''}
        `;
        
        // Add event listeners for navigation
        const prevBtn = document.getElementById('etf-profile-prev');
        const nextBtn = document.getElementById('etf-profile-next');
        const dots = container.querySelectorAll('.etf-profile-dot');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.state.profileIndex > 0) {
                    this.state.profileIndex--;
                    this.renderQuickProfile();
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.state.profileIndex < pinnedETFs.length - 1) {
                    this.state.profileIndex++;
                    this.renderQuickProfile();
                }
            });
        }
        
        dots.forEach((dot, idx) => {
            dot.addEventListener('click', () => {
                this.state.profileIndex = idx;
                this.renderQuickProfile();
            });
        });
        
        // Add keyboard navigation
        if (!this._profileKeyHandler) {
            this._profileKeyHandler = (e) => {
                if (e.key === 'ArrowLeft' && this.state.profileIndex > 0) {
                    this.state.profileIndex--;
                    this.renderQuickProfile();
                } else if (e.key === 'ArrowRight' && this.state.profileIndex < pinnedETFs.length - 1) {
                    this.state.profileIndex++;
                    this.renderQuickProfile();
                }
            };
            document.addEventListener('keydown', this._profileKeyHandler);
        }
    }

    genSeries(etf) {
        // Use ONLY real price data - no fake data generation
        const priceData = etf.priceData || [];
        if (priceData.length === 0) {
            // Return empty if no real data
            return { norm: [], dd: [], dates: [], dateObjects: [] };
        }
        
        // Filter and sort data by date
        const validData = priceData
            .filter(bar => bar && bar.close && bar.close > 0 && bar.date)
            .map(bar => ({
                date: new Date(bar.date),
                close: parseFloat(bar.close),
                original: bar
            }))
            .sort((a, b) => a.date - b.date);
        
        if (validData.length === 0) {
            return { norm: [], dd: [], dates: [], dateObjects: [] };
        }
        
        // Remove duplicates by date (keep latest)
        const uniqueData = [];
        const dateMap = new Map();
        validData.forEach(item => {
            const dateKey = item.date.toISOString().split('T')[0];
            if (!dateMap.has(dateKey) || item.date > dateMap.get(dateKey).date) {
                dateMap.set(dateKey, item);
            }
        });
        dateMap.forEach(item => uniqueData.push(item));
        uniqueData.sort((a, b) => a.date - b.date);
        
        // Extract prices and dates
        const prices = uniqueData.map(item => item.close);
        const dateObjects = uniqueData.map(item => item.date);
        
        // Filter out extreme outliers (more than 5 standard deviations - more lenient)
        // Only filter if we have enough data points
        if (prices.length > 20) {
            const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
            const variance = prices.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / prices.length;
            const stdDev = Math.sqrt(variance);
            
            // Only filter if standard deviation is reasonable (not too small)
            if (stdDev > 0 && mean > 0) {
                const filtered = [];
                const filteredDates = [];
                
                prices.forEach((price, idx) => {
                    const zScore = Math.abs((price - mean) / stdDev);
                    // Use 5 standard deviations instead of 3 to be more lenient
                    if (zScore < 5) {
                        filtered.push(price);
                        filteredDates.push(dateObjects[idx]);
                    }
                });
                
                // Only use filtered if we keep >90% of data (more strict requirement)
                if (filtered.length > prices.length * 0.9) {
                    prices.splice(0, prices.length, ...filtered);
                    dateObjects.splice(0, dateObjects.length, ...filteredDates);
                }
            }
        }
        
        // Apply simple moving average to smooth data (window of 5 days)
        const smoothWindow = Math.min(5, Math.floor(prices.length / 10));
        const smoothedPrices = [];
        for (let i = 0; i < prices.length; i++) {
            const start = Math.max(0, i - smoothWindow);
            const end = Math.min(prices.length, i + smoothWindow + 1);
            const window = prices.slice(start, end);
            const avg = window.reduce((a, b) => a + b, 0) / window.length;
            smoothedPrices.push(avg);
        }
        
        // Normalize to starting value of 100
        const basePrice = smoothedPrices[0] || prices[0];
        if (basePrice <= 0) {
            return { norm: [], dd: [], dates: [], dateObjects: [] };
        }
        
        const normalized = smoothedPrices.map(p => (p / basePrice) * 100);
        
        // Calculate drawdowns
        let peak = normalized[0];
        const drawdowns = normalized.map(p => {
            peak = Math.max(peak, p);
            return ((p - peak) / peak) * 100;
        });
        
        // Format dates for display
        const dates = dateObjects.map(date => 
            date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        );
        
        return { 
            norm: normalized, 
            dd: drawdowns, 
            dates: dates,
            dateObjects: dateObjects
        };
    }

    renderCharts() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js not loaded');
            return;
        }

        if (this.etfData.length === 0) return;

        const pinned = Array.from(this.state.pinned)
            .map(t => {
                const found = this.etfData.find(d => d.t === t);
                if (!found) {
                    console.warn(`ETF ${t} is pinned but not found in etfData`);
                }
                return found;
            })
            .filter(Boolean);

        if (pinned.length === 0) {
            console.warn('No pinned ETFs found in data');
            return;
        }
        
        console.log(`Rendering charts for ${pinned.length} pinned ETFs:`, pinned.map(d => d.t));

        // Get unified date range from all pinned ETFs
        const allDates = new Set();
        pinned.forEach(d => {
            const s = this.genSeries(d);
            if (s.dateObjects && s.dateObjects.length > 0) {
                s.dateObjects.forEach(date => {
                    allDates.add(date.getTime());
                });
            }
        });
        
        // Sort dates and create labels
        const sortedDates = Array.from(allDates).sort((a, b) => a - b);
        const labels = sortedDates.map(timestamp => {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

        // Growth chart
        const growthCtx = document.getElementById('etf-chart-growth');
        if (growthCtx) {
            if (this.charts.growth) this.charts.growth.destroy();
            
            // Create datasets with proper color mapping
            const growthDatasets = [];
            pinned.forEach((d, originalIdx) => {
                const s = this.genSeries(d);
                if (s.norm.length === 0 || !s.dateObjects || s.dateObjects.length === 0) {
                    console.warn(`ETF ${d.t} has no valid data for chart: norm.length=${s.norm.length}, dateObjects.length=${s.dateObjects ? s.dateObjects.length : 0}`);
                    return; // Skip if no real data
                }
                
                console.log(`ETF ${d.t}: ${s.norm.length} data points, date range: ${s.dateObjects[0].toLocaleDateString()} to ${s.dateObjects[s.dateObjects.length-1].toLocaleDateString()}`);
                
                // Align data with unified date range using interpolation
                const alignedData = [];
                const dateMap = new Map();
                s.dateObjects.forEach((date, i) => {
                    dateMap.set(date.getTime(), s.norm[i]);
                });
                
                // Check if this ETF's date range overlaps with the unified range
                const etfMinDate = s.dateObjects[0].getTime();
                const etfMaxDate = s.dateObjects[s.dateObjects.length - 1].getTime();
                const unifiedMinDate = sortedDates[0];
                const unifiedMaxDate = sortedDates[sortedDates.length - 1];
                
                sortedDates.forEach(timestamp => {
                    if (dateMap.has(timestamp)) {
                        // Exact match
                        alignedData.push(dateMap.get(timestamp));
                    } else if (timestamp < etfMinDate) {
                        // Before ETF's data range - use first value
                        alignedData.push(s.norm[0]);
                    } else if (timestamp > etfMaxDate) {
                        // After ETF's data range - use last value
                        alignedData.push(s.norm[s.norm.length - 1]);
                    } else {
                        // Within range - interpolate between nearest points
                        const targetDate = new Date(timestamp);
                        let beforeIdx = -1;
                        let afterIdx = -1;
                        
                        for (let i = 0; i < s.dateObjects.length; i++) {
                            if (s.dateObjects[i] <= targetDate) {
                                beforeIdx = i;
                            }
                            if (s.dateObjects[i] >= targetDate && afterIdx === -1) {
                                afterIdx = i;
                                break;
                            }
                        }
                        
                        if (beforeIdx >= 0 && afterIdx >= 0 && beforeIdx !== afterIdx) {
                            // Linear interpolation
                            const beforeDate = s.dateObjects[beforeIdx].getTime();
                            const afterDate = s.dateObjects[afterIdx].getTime();
                            const ratio = (timestamp - beforeDate) / (afterDate - beforeDate);
                            const interpolated = s.norm[beforeIdx] + (s.norm[afterIdx] - s.norm[beforeIdx]) * ratio;
                            alignedData.push(interpolated);
                        } else if (beforeIdx >= 0) {
                            alignedData.push(s.norm[beforeIdx]);
                        } else if (afterIdx >= 0) {
                            alignedData.push(s.norm[afterIdx]);
                        } else {
                            // Fallback: use nearest value
                            const nearestIdx = Math.round((timestamp - etfMinDate) / (etfMaxDate - etfMinDate) * (s.norm.length - 1));
                            alignedData.push(s.norm[Math.max(0, Math.min(s.norm.length - 1, nearestIdx))]);
                        }
                    }
                });
                
                // Count valid data points
                const validCount = alignedData.filter(v => v !== null && !isNaN(v)).length;
                console.log(`ETF ${d.t}: aligned ${alignedData.length} points, ${validCount} valid`);
                
                // Only skip if we have less than 10% valid data
                if (validCount < alignedData.length * 0.1) {
                    console.warn(`ETF ${d.t}: too few valid data points (${validCount}/${alignedData.length}), skipping`);
                    return;
                }
                
                // Use original index for color to maintain consistency
                const colorIdx = originalIdx % colors.length;
                console.log(`ETF ${d.t}: adding to chart with color index ${colorIdx} (${colors[colorIdx]})`);
                
                // Ensure data is valid (no NaN or Infinity)
                const cleanData = alignedData.map(v => {
                    if (v === null || v === undefined || isNaN(v) || !isFinite(v)) {
                        return null;
                    }
                    return v;
                });
                
                // Use different line styles for better distinction
                // VOO and SPY are very similar (both track S&P 500), so use different styles
                const lineStyle = d.t === 'SPY' ? [5, 5] : undefined; // Dashed line for SPY
                const lineWidth = d.t === 'SPY' ? 2.5 : 2; // Slightly thicker for SPY
                
                growthDatasets.push({
                    label: `${d.t} (${d.dataSource || 'unknown'})`,
                    data: cleanData,
                    borderColor: colors[colorIdx],
                    backgroundColor: colors[colorIdx] + '20',
                    borderWidth: lineWidth,
                    borderDash: lineStyle, // Dashed line for SPY to distinguish from VOO
                    pointRadius: 0,
                    tension: 0.3, // Increased tension for smoother curves
                    spanGaps: true, // Connect across null values
                    hidden: false // Explicitly set to visible
                });
            });
            
            if (growthDatasets.length === 0) {
                growthCtx.parentElement.innerHTML = '<p style="text-align: center; color: #64748b; padding: 2rem;">No price data available for chart</p>';
                return;
            }

            // Debug: Log dataset information
            console.log(`Creating chart with ${growthDatasets.length} datasets:`, growthDatasets.map(d => ({
                label: d.label,
                dataLength: d.data.length,
                borderColor: d.borderColor,
                firstValue: d.data[0],
                lastValue: d.data[d.data.length - 1],
                sampleValues: d.data.slice(0, 5).concat(d.data.slice(-5))
            })));
            
            // Verify all datasets have valid data
            growthDatasets.forEach((ds, idx) => {
                const validCount = ds.data.filter(v => v !== null && !isNaN(v) && isFinite(v)).length;
                console.log(`Dataset ${idx} (${ds.label}): ${validCount}/${ds.data.length} valid values`);
                if (validCount === 0) {
                    console.error(`Dataset ${idx} (${ds.label}) has NO valid data!`);
                }
            });

            this.charts.growth = new Chart(growthCtx, {
                type: 'line',
                data: { labels: labels.length > 0 ? labels : growthDatasets[0].data.map((_, i) => `Day ${i + 1}`), datasets: growthDatasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true,
                            labels: { color: '#64748b', font: { size: 12 } },
                            onClick: (e, legendItem, legend) => {
                                // Allow toggling datasets
                                const index = legendItem.datasetIndex;
                                const chart = legend.chart;
                                const meta = chart.getDatasetMeta(index);
                                meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null;
                                chart.update();
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            mode: 'index',
                            intersect: false
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    scales: {
                        x: {
                            ticks: { color: '#64748b', font: { size: 11 } },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false }
                        },
                        y: {
                            ticks: { color: '#64748b', font: { size: 11 } },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false }
                        }
                    }
                }
            });
        }

        // Drawdown chart
        const ddCtx = document.getElementById('etf-chart-dd');
        if (ddCtx) {
            if (this.charts.drawdown) this.charts.drawdown.destroy();
            
            // Create drawdown datasets with proper color mapping
            const ddDatasets = [];
            pinned.forEach((d, originalIdx) => {
                const s = this.genSeries(d);
                if (s.dd.length === 0 || !s.dateObjects || s.dateObjects.length === 0) {
                    console.warn(`ETF ${d.t} has no valid drawdown data`);
                    return; // Skip if no real data
                }
                
                // Align data with unified date range using interpolation
                const alignedData = [];
                const dateMap = new Map();
                s.dateObjects.forEach((date, i) => {
                    dateMap.set(date.getTime(), s.dd[i]);
                });
                
                // Check if this ETF's date range overlaps with the unified range
                const etfMinDate = s.dateObjects[0].getTime();
                const etfMaxDate = s.dateObjects[s.dateObjects.length - 1].getTime();
                
                sortedDates.forEach(timestamp => {
                    if (dateMap.has(timestamp)) {
                        alignedData.push(dateMap.get(timestamp));
                    } else if (timestamp < etfMinDate) {
                        // Before ETF's data range - use first value
                        alignedData.push(s.dd[0]);
                    } else if (timestamp > etfMaxDate) {
                        // After ETF's data range - use last value
                        alignedData.push(s.dd[s.dd.length - 1]);
                    } else {
                        // Within range - interpolate
                        const targetDate = new Date(timestamp);
                        let beforeIdx = -1;
                        let afterIdx = -1;
                        
                        for (let i = 0; i < s.dateObjects.length; i++) {
                            if (s.dateObjects[i] <= targetDate) {
                                beforeIdx = i;
                            }
                            if (s.dateObjects[i] >= targetDate && afterIdx === -1) {
                                afterIdx = i;
                                break;
                            }
                        }
                        
                        if (beforeIdx >= 0 && afterIdx >= 0 && beforeIdx !== afterIdx) {
                            const beforeDate = s.dateObjects[beforeIdx].getTime();
                            const afterDate = s.dateObjects[afterIdx].getTime();
                            const ratio = (timestamp - beforeDate) / (afterDate - beforeDate);
                            const interpolated = s.dd[beforeIdx] + (s.dd[afterIdx] - s.dd[beforeIdx]) * ratio;
                            alignedData.push(interpolated);
                        } else if (beforeIdx >= 0) {
                            alignedData.push(s.dd[beforeIdx]);
                        } else if (afterIdx >= 0) {
                            alignedData.push(s.dd[afterIdx]);
                        } else {
                            // Fallback: use nearest value
                            const nearestIdx = Math.round((timestamp - etfMinDate) / (etfMaxDate - etfMinDate) * (s.dd.length - 1));
                            alignedData.push(s.dd[Math.max(0, Math.min(s.dd.length - 1, nearestIdx))]);
                        }
                    }
                });
                
                // Use original index for color to maintain consistency
                const colorIdx = originalIdx % colors.length;
                
                // Use different line styles for better distinction
                const lineStyle = d.t === 'SPY' ? [5, 5] : undefined; // Dashed line for SPY
                const lineWidth = d.t === 'SPY' ? 2.5 : 2; // Slightly thicker for SPY
                
                ddDatasets.push({
                    label: `${d.t} (${d.dataSource || 'unknown'})`,
                    data: alignedData,
                    borderColor: colors[colorIdx],
                    backgroundColor: colors[colorIdx] + '20',
                    borderWidth: lineWidth,
                    borderDash: lineStyle, // Dashed line for SPY to distinguish from VOO
                    pointRadius: 0,
                    tension: 0.3, // Increased tension for smoother curves
                    fill: true,
                    spanGaps: true
                });
            });
            
            if (ddDatasets.length === 0) {
                ddCtx.parentElement.innerHTML = '<p style="text-align: center; color: #64748b; padding: 2rem;">No price data available for chart</p>';
                return;
            }

            this.charts.drawdown = new Chart(ddCtx, {
                type: 'line',
                data: { labels: labels.length > 0 ? labels : ddDatasets[0].data.map((_, i) => `Day ${i + 1}`), datasets: ddDatasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#64748b', font: { size: 12 } } },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            callbacks: {
                                label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}%`
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#64748b', font: { size: 11 } },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false }
                        },
                        y: {
                            ticks: {
                                color: '#64748b',
                                callback: (v) => v.toFixed(1) + '%',
                                font: { size: 11 }
                            },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false }
                        }
                    }
                }
            });
        }

        // Scatter chart
        const scatterCtx = document.getElementById('etf-chart-scatter');
        if (scatterCtx) {
            if (this.charts.scatter) this.charts.scatter.destroy();
            
            const bubbleData = this.etfData.map(d => ({
                x: d.vol * 100,
                y: d.cagr * 100,
                r: Math.max(4, Math.min(22, Math.sqrt(d.aum) * 1.3)),
                t: d.t
            }));

            this.charts.scatter = new Chart(scatterCtx, {
                type: 'bubble',
                data: {
                    datasets: [{
                        label: 'ETFs',
                        data: bubbleData,
                        backgroundColor: bubbleData.map((_, i) => colors[i % colors.length] + '80'),
                        borderColor: bubbleData.map((_, i) => colors[i % colors.length]),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#64748b', font: { size: 12 } } },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            callbacks: {
                                label: (ctx) => {
                                    const p = ctx.raw;
                                    return `${p.t}: Vol ${p.x.toFixed(1)}% | CAGR ${p.y.toFixed(1)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Vol (%)',
                                color: '#64748b',
                                font: { size: 12, weight: '500' }
                            },
                            ticks: { color: '#64748b', font: { size: 11 } },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'CAGR (%)',
                                color: '#64748b',
                                font: { size: 12, weight: '500' }
                            },
                            ticks: { color: '#64748b', font: { size: 11 } },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawBorder: false }
                        }
                    },
                    onClick: (evt, els) => {
                        if (!els.length) return;
                        const idx = els[0].index;
                        const ticker = bubbleData[idx].t;
                        this.state.selected = ticker;
                        this.state.pinned.add(ticker);
                        this.render();
                    }
                }
            });
        }
    }

    renderCompareTable() {
        const container = document.getElementById('etf-compare-table');
        if (!container || this.etfData.length === 0) return;

        const f = this.state.filter.trim().toUpperCase();
        let items = this.etfData.filter(d => !f || d.t.includes(f));
        const cols = items.map(d => d.t);

        const rows = [
            { k: 'score', label: 'Composite Score', better: 'high', fmt: (d) => d.score },
            { k: 'cagr', label: 'CAGR', better: 'high', fmt: (d) => this.fmtPct(d.cagr) },
            { k: 'vol', label: 'Vol', better: 'low', fmt: (d) => this.fmtPct(d.vol) },
            { k: 'sharpe', label: 'Sharpe', better: 'high', fmt: (d) => d.sharpe.toFixed(2) },
            { k: 'sortino', label: 'Sortino', better: 'high', fmt: (d) => d.sortino.toFixed(2) },
            { k: 'mdd', label: 'Max Drawdown', better: 'low', fmt: (d) => this.fmtPct(d.mdd) },
            { k: 'calmar', label: 'Calmar', better: 'high', fmt: (d) => d.calmar.toFixed(2) },
            { k: 'beta', label: 'Beta vs Bench', better: 'mid', fmt: (d) => d.beta.toFixed(2) },
            { k: 'te', label: 'Tracking Error', better: 'low', fmt: (d) => this.fmtPct(d.te) },
            { k: 'expense', label: 'Expense Ratio', better: 'low', fmt: (d) => this.fmtPct(d.expense) },
            { k: 'aum', label: 'AUM ($B)', better: 'high', fmt: (d) => this.fmtNum(d.aum) },
            { k: 'dv', label: 'Dollar Volume ($B/day)', better: 'high', fmt: (d) => this.fmtNum(d.dv) },
            { k: 'spread', label: 'Spread ($)', better: 'low', fmt: (d) => d.spread.toFixed(2) }
        ];

        const rankMaps = {};
        rows.forEach(r => {
            let higherBetter = r.better === 'high';
            if (r.k === 'mdd' || r.k === 'vol' || r.k === 'te' || r.k === 'expense' || r.k === 'spread') higherBetter = false;
            if (r.k === 'beta') higherBetter = true;
            rankMaps[r.k] = this.rank(items, r.k === 'score' ? 'score' : r.k, higherBetter);
        });

        const thead = `
            <thead>
                <tr>
                    <th style="min-width: 220px;">Metric</th>
                    ${cols.map(c => `<th class="etf-mono">${c}</th>`).join('')}
                </tr>
            </thead>
        `;

        const tbody = rows.map(r => {
            return `
                <tr>
                    <td>
                        <b>${r.label}</b>
                        <div class="etf-small">Better: ${r.better === 'high' ? 'Higher' : r.better === 'low' ? 'Lower' : 'Depends'}</div>
                    </td>
                    ${items.map(d => {
                        const rk = rankMaps[r.k].get(d.t);
                        const cls = rk <= 3 ? 'etf-pos' : rk >= items.length - 2 ? 'etf-neg' : 'etf-neu';
                        const val = r.k === 'score' ? d.score : d[r.k];
                        const shown = r.k === 'score' ? d.score : r.fmt(d);
                        return `<td class="etf-mono ${cls}">${shown} <span class="etf-rank">(#${rk})</span></td>`;
                    }).join('')}
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="etf-table" style="min-width: 1100px;">
                ${thead}
                <tbody>${tbody}</tbody>
            </table>
        `;
    }

    renderRiskTable() {
        const container = document.getElementById('etf-risk-table');
        const episodesContainer = document.getElementById('etf-dd-episodes');
        if (!container || !episodesContainer || this.etfData.length === 0) return;

        const items = [...this.etfData].sort((a, b) => b.score - a.score);

        const head = `
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Data Source</th>
                    <th>Volatility (1Y)</th>
                    <th>Max Drawdown</th>
                    <th>Beta</th>
                    <th>Sharpe Ratio</th>
                </tr>
            </thead>
        `;

        const body = items.map(d => {
            return `
                <tr>
                    <td class="etf-mono"><span class="etf-pill" data-select="${d.t}">${d.t}</span></td>
                    <td class="etf-small">${d.dataSource === 'polygon' ? 'Polygon.io' : d.dataSource === 'yfinance' ? 'Yahoo Finance' : 'Unknown'}</td>
                    <td class="etf-mono">${this.fmtPct(d.vol)}</td>
                    <td class="etf-mono etf-neg">${this.fmtPct(d.mdd)}</td>
                    <td class="etf-mono">${d.beta.toFixed(2)}</td>
                    <td class="etf-mono">${d.sharpe.toFixed(2)}</td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="etf-table">
                ${head}
                <tbody>${body}</tbody>
            </table>
        `;

        // Drawdown episodes - only show if we have real price data
        const episodes = items
            .filter(d => d.priceData && d.priceData.length > 0)
            .map(d => {
                // Calculate actual drawdown episodes from price data
                const prices = d.priceData.map(bar => bar.close);
                const dates = d.priceData.map(bar => new Date(bar.date));
                
                let peak = prices[0];
                let peakIdx = 0;
                let maxDD = 0;
                let maxDDStart = dates[0];
                let maxDDTrough = dates[0];
                
                for (let i = 0; i < prices.length; i++) {
                    if (prices[i] > peak) {
                        peak = prices[i];
                        peakIdx = i;
                    }
                    const drawdown = (prices[i] - peak) / peak;
                    if (drawdown < maxDD) {
                        maxDD = drawdown;
                        maxDDStart = dates[peakIdx];
                        maxDDTrough = dates[i];
                    }
                }
                
                // Estimate recovery (simplified - find when price recovers to peak)
                let recoveryIdx = -1;
                for (let i = dates.indexOf(maxDDTrough); i < prices.length; i++) {
                    if (prices[i] >= peak) {
                        recoveryIdx = i;
                        break;
                    }
                }
                const toRec = recoveryIdx >= 0 ? Math.floor((dates[recoveryIdx] - maxDDTrough) / (1000 * 60 * 60 * 24)) : null;
                
                return {
                    t: d.t,
                    depth: maxDD * 100,
                    start: maxDDStart.toISOString().split('T')[0],
                    trough: maxDDTrough.toISOString().split('T')[0],
                    toRec: toRec !== null ? toRec : 'N/A'
                };
            })
            .sort((a, b) => b.depth - a.depth);

        if (episodes.length === 0) {
            episodesContainer.innerHTML = '<p class="etf-small" style="color: #64748b; padding: 1rem;">No drawdown episode data available (requires price history)</p>';
        } else {
            episodesContainer.innerHTML = `
                <table class="etf-table">
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>DD Depth</th>
                            <th>Start</th>
                            <th>Trough</th>
                            <th>Days to Recover</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${episodes.map(x => `
                            <tr>
                                <td class="etf-mono">${x.t}</td>
                                <td class="etf-mono">${x.depth.toFixed(1)}%</td>
                                <td class="etf-mono">${x.start}</td>
                                <td class="etf-mono">${x.trough}</td>
                                <td class="etf-mono">${x.toRec}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        // Click handlers
        [...container.querySelectorAll('[data-select]'), ...episodesContainer.querySelectorAll('[data-select]')].forEach(n => {
            n.onclick = () => {
                const t = n.getAttribute('data-select');
                this.state.selected = t;
                this.state.pinned.add(t);
                this.render();
            };
        });
    }

    renderCostLiqTable() {
        const costContainer = document.getElementById('etf-cost-table');
        const liqContainer = document.getElementById('etf-liq-table');
        if (!costContainer || !liqContainer || this.etfData.length === 0) return;

        const items = [...this.etfData].sort((a, b) => b.score - a.score);

        costContainer.innerHTML = `
            <table class="etf-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Data Source</th>
                        <th>Expense Ratio</th>
                        <th>Bid-Ask Spread</th>
                        <th>AUM ($B)</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map(d => {
                        return `
                            <tr>
                                <td class="etf-mono"><span class="etf-pill" data-select="${d.t}">${d.t}</span></td>
                                <td class="etf-small">${d.dataSource === 'polygon' ? 'Polygon.io' : d.dataSource === 'yfinance' ? 'Yahoo Finance' : 'Unknown'}</td>
                                <td class="etf-mono">${this.fmtPct(d.expense)}</td>
                                <td class="etf-mono">$${d.spread.toFixed(2)}</td>
                                <td class="etf-mono">${this.fmtNum(d.aum)}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;

        liqContainer.innerHTML = `
            <table class="etf-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Data Source</th>
                        <th>Dollar Vol ($B/day)</th>
                        <th>Spread ($)</th>
                        <th>Current Price</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map(d => {
                        return `
                            <tr>
                                <td class="etf-mono"><span class="etf-pill" data-select="${d.t}">${d.t}</span></td>
                                <td class="etf-small">${d.dataSource === 'polygon' ? 'Polygon.io' : d.dataSource === 'yfinance' ? 'Yahoo Finance' : 'Unknown'}</td>
                                <td class="etf-mono">${this.fmtNum(d.dv)}</td>
                                <td class="etf-mono">$${d.spread.toFixed(2)}</td>
                                <td class="etf-mono">${d.currentPrice ? `$${d.currentPrice.toFixed(2)}` : '—'}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;

        [...costContainer.querySelectorAll('[data-select]'), ...liqContainer.querySelectorAll('[data-select]')].forEach(n => {
            n.onclick = () => {
                const t = n.getAttribute('data-select');
                this.state.selected = t;
                this.state.pinned.add(t);
                this.render();
            };
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (typeof ETFDashboardMulti !== 'undefined') {
            window.etfDashboard = new ETFDashboardMulti();
        }
    });
} else {
    if (typeof ETFDashboardMulti !== 'undefined') {
        window.etfDashboard = new ETFDashboardMulti();
    }
}

