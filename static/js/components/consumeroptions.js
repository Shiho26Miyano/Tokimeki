/**
 * Consumer Options Dashboard — React UI Implementation
 * ---------------------------------------------------
 * Purpose: Implement the exact React UI design provided by user
 * Styling: Tailwind + shadcn/ui components
 * Charts: recharts
 * Backend: consumeroptions API endpoints
 */

class ConsumerOptionsReactDashboard {
    constructor() {
        console.log('ConsumerOptionsReactDashboard constructor called');
        this.currentTicker = 'COST';
        this.sampleTickers = ['COST', 'WMT', 'TGT', 'AMZN', 'AAPL'];
        this.onlyUnusual = false;
        this.tooltipsSetup = false;
        
        // Initialize formatPct utility
        this.formatPct = (x) => (x == null ? "—" : `${(x * 100).toFixed(1)}%`);
        this.init();
    }


    async init() {
        console.log('Initializing Consumer Options Dashboard...');
        this.setupEventListeners();
        
        // First check if the API is available
        await this.checkAPIHealth();
        
        await this.loadRealData();
        this.render();
    }

    async checkAPIHealth() {
        try {
            console.log('Checking API health...');
            const response = await fetch('/api/v1/', {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('API health check passed:', data);
                
                // Check if consumeroptions endpoints are available
                if (data.endpoints?.consumeroptions) {
                    console.log('Consumer options endpoints available:', data.endpoints.consumeroptions);
                } else {
                    console.warn('Consumer options endpoints not found in API info');
                }
            } else {
                console.warn(`API health check failed: ${response.status}`);
            }
        } catch (error) {
            console.error('API health check error:', error);
            console.error('This suggests the FastAPI server may not be running');
        }
    }

    async loadRealData() {
        try {
            console.log(`Loading real data for ${this.currentTicker}...`);
            this.showLoading(true);

            // Call the consumeroptions dashboard API
            const apiUrl = `/api/v1/consumeroptions/dashboard/data/${this.currentTicker}?days=60`;
            console.log(`Making API call to: ${apiUrl}`);
            
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
            });
            
            console.log(`API response status: ${response.status}`);
            console.log(`API response headers:`, response.headers);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API error response:`, errorText);
                
                if (response.status === 404) {
                    throw new Error(`API endpoint not found: ${apiUrl}`);
                } else if (response.status === 500) {
                    throw new Error(`Server error: ${errorText}`);
                } else {
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
            }
            
            const data = await response.json();
            console.log('Real data loaded successfully:', data);
            
            // Debug: Log the structure of received data
            if (data.chain_data?.contracts?.length > 0) {
                console.log('Sample contract data:', data.chain_data.contracts[0]);
            }
            if (data.call_put_ratios) {
                console.log('Call/Put ratios data:', data.call_put_ratios);
            }
            if (data.iv_term_structure?.length > 0) {
                console.log('Sample IV term data:', data.iv_term_structure[0]);
            }

            // Process the API response
            this.processAPIData(data);

        } catch (error) {
            console.error('Error loading real data:', error);
            
            // Check if it's a network error
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                this.showError(`Network error: Cannot connect to server. Please ensure the FastAPI server is running on the correct port.`);
            } else {
                this.showError(`API Error: ${error.message}`);
            }
            
            // Initialize empty data structures when API fails
            this.initializeEmptyData();
        } finally {
            this.showLoading(false);
        }
    }

    processAPIData(data) {
        // Process chain data with field mapping
        const rawChain = data.chain_data?.contracts || [];
        this.chain = rawChain.map(contract => ({
            ...contract,
            // Map field names for frontend compatibility
            iv: contract.implied_volatility,
            last: contract.last_price,
            day_volume: contract.day_volume || 0,
            day_oi: contract.day_oi || 0
        }));
        
        // Process IV term structure with proper field mapping
        const rawIVTerm = data.iv_term_structure || [];
        this.ivTerm = rawIVTerm.map(point => ({
            ...point,
            // Ensure proper field mapping for IV term structure
            iv_median: point.median_iv || point.iv_median,
            expiry: point.expiry
        }));
        
        // Process underlying data
        this.underlying = data.underlying_data || [];

        // Calculate call/put ratios from real data with better error handling
        const apiCallPutRatios = data.call_put_ratios;
        console.log('Processing call/put ratios:', apiCallPutRatios);
        
        if (apiCallPutRatios && typeof apiCallPutRatios === 'object') {
            this.callPut = {
                volRatio: apiCallPutRatios.volume_ratio || null,
                oiRatio: apiCallPutRatios.oi_ratio || null,
                totalOI: (apiCallPutRatios.call_oi || 0) + (apiCallPutRatios.put_oi || 0),
                medianIV: apiCallPutRatios.median_iv || null,
                callVolume: apiCallPutRatios.call_volume || 0,
                putVolume: apiCallPutRatios.put_volume || 0,
                callOI: apiCallPutRatios.call_oi || 0,
                putOI: apiCallPutRatios.put_oi || 0,
                sentiment: apiCallPutRatios.sentiment || 'Neutral',
                confidence: apiCallPutRatios.confidence || 0
            };
            
            console.log('Processed callPut data:', this.callPut);
        } else {
            console.warn('No valid call_put_ratios data found:', apiCallPutRatios);
            this.callPut = {
                volRatio: null,
                oiRatio: null,
                totalOI: 0,
                medianIV: null,
                callVolume: 0,
                putVolume: 0,
                callOI: 0,
                putOI: 0,
                sentiment: 'Neutral',
                confidence: 0
            };
        }

        // Process unusual activity
        this.unusual = data.unusual_activity || [];

        // Process new chart data
        this.oiHeatmapData = data.oi_heatmap_data || {};
        this.deltaDistributionData = data.delta_distribution_data || {};

        console.log('Processed API data:', {
            chainLength: this.chain.length,
            unusualCount: this.unusual.length,
            callPutRatios: this.callPut,
            sampleContract: this.chain[0],
            sampleIVTerm: this.ivTerm[0],
            oiHeatmapData: this.oiHeatmapData,
            deltaDistributionData: this.deltaDistributionData
        });

        // Render the dashboard with the processed data
        this.render();
    }

    initializeEmptyData() {
        // Initialize empty data structures when API fails
        this.chain = [];
        this.ivTerm = [];
        this.underlying = [];
        
        this.callPut = {
            volRatio: null,
            oiRatio: null,
            totalOI: 0,
            medianIV: null,
            callVolume: 0,
            putVolume: 0,
            callOI: 0,
            putOI: 0,
            sentiment: 'Neutral',
            confidence: 0
        };

        this.unusual = [];
        this.oiHeatmapData = {};
        this.deltaDistributionData = {};
    }

    setupEventListeners() {
        // Use event delegation for dynamically created elements
        document.addEventListener('change', (e) => {
            if (e.target.id === 'ticker-select') {
                this.currentTicker = e.target.value;
                this.loadRealData().then(() => this.render());
            }
            
            if (e.target.id === 'unusual-filter') {
                this.onlyUnusual = e.target.checked;
                this.renderChainTable();
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.id === 'export-btn') {
                this.exportData();
            }
            
            if (e.target.id === 'refresh-btn') {
                this.loadRealData().then(() => this.render());
            }
        });
    }

    render() {
        console.log('Rendering Consumer Options Dashboard...');
        const container = document.getElementById('consumeroptions-dashboard');
        if (!container) {
            console.error('Dashboard container not found');
            return;
        }

        container.innerHTML = this.getReactUIHTML();
        
        // Render charts after DOM is updated, only if we have data
        setTimeout(() => {
            if (this.chain.length > 0 || this.ivTerm.length > 0 || this.underlying.length > 0) {
                this.renderCharts();
            }
            this.setupTooltips();
        }, 200);
    }

    getReactUIHTML() {
        // Beautiful UI implementation matching the screenshots
        const displayRows = this.onlyUnusual ? this.unusual : this.chain;
        const hasData = this.chain.length > 0 || this.ivTerm.length > 0 || this.underlying.length > 0;

        return `
            <div class="min-h-screen bg-gray-50" style="padding: 2rem;">
                <div class="mx-auto max-w-7xl">
                    ${this.getHeaderHTML()}
                    ${hasData ? this.getKPICardsHTML() : ''}
                    ${hasData ? this.getMainGridHTML(displayRows) : this.getEmptyStateHTML()}
                    ${this.getFooterHTML()}
                </div>
            </div>
        `;
    }

    getHeaderHTML() {
        return `
            <div style="margin-bottom: 1.5rem;">
                <!-- Title Row -->
                <div style="margin-bottom: 1rem;">
                    <h1 style="font-size: 1.875rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem; line-height: 1.2;">Consumer Options Sentiment</h1>
                    <p style="color: #64748b; font-size: 0.75rem; margin: 0;">Polygon Options Starter • 15‑min delayed • 2y history</p>
                </div>
                
                <!-- Controls Row - Single Line -->
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex-wrap: wrap;
                ">
                    <!-- Ticker Selector -->
                    <select id="ticker-select" style="
                        background: white;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 10px 14px;
                        font-size: 14px;
                        font-weight: 600;
                        color: #1e293b;
                        min-width: 80px;
                        cursor: pointer;
                        box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.06);
                        transition: all 0.2s;
                    " onmouseover="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 4px 8px 0 rgb(59 130 246 / 0.15)'" onmouseout="this.style.borderColor='#e2e8f0'; this.style.boxShadow='0 2px 4px 0 rgb(0 0 0 / 0.06)'">
                        ${this.sampleTickers.map(t => 
                            `<option value="${t}" ${t === this.currentTicker ? 'selected' : ''}>${t}</option>`
                        ).join('')}
                    </select>
                    
                    <!-- Export CSV Button -->
                    <button id="export-btn" style="
                        background: #3b82f6;
                        border: 1px solid #3b82f6;
                        border-radius: 8px;
                        padding: 10px 16px;
                        font-size: 14px;
                        font-weight: 500;
                        color: white;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        box-shadow: 0 2px 4px 0 rgb(59 130 246 / 0.25);
                        transition: all 0.2s;
                    " onmouseover="this.style.backgroundColor='#2563eb'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px 0 rgb(59 130 246 / 0.35)'" onmouseout="this.style.backgroundColor='#3b82f6'; this.style.transform='translateY(0px)'; this.style.boxShadow='0 2px 4px 0 rgb(59 130 246 / 0.25)'">
                        <i data-lucide="download" style="width: 16px; height: 16px;"></i>
                        Export CSV
                    </button>
                </div>
            </div>
        `;
    }

    getKPICardsHTML() {
        return `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                <!-- Call/Put Volume Card -->
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 1rem;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                ">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Call/Put Volume</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">
                        ${this.callPut.volRatio !== null && this.callPut.volRatio !== undefined ? this.callPut.volRatio.toFixed(2) : "—"}
                    </div>
                    <div style="
                        display: inline-flex;
                        align-items: center;
                        gap: 0.25rem;
                        padding: 0.125rem 0.5rem;
                        border-radius: 9999px;
                        font-size: 0.625rem;
                        font-weight: 500;
                        ${(this.callPut.volRatio !== null && this.callPut.volRatio > 1) ? 
                            'background: #dcfce7; color: #166534;' : 
                            'background: #f1f5f9; color: #475569;'
                        }
                    ">
                        <i data-lucide="${(this.callPut.volRatio !== null && this.callPut.volRatio > 1) ? 'trending-up' : 'trending-down'}" style="width: 10px; height: 10px;"></i>
                        ${(this.callPut.volRatio !== null && this.callPut.volRatio > 1) ? 'Bullish' : 'Bearish/Neutral'}
                    </div>
                </div>
                
                <!-- Call/Put OI Card -->
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 1rem;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                ">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Call/Put OI</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.25rem;">
                        ${this.callPut.oiRatio !== null && this.callPut.oiRatio !== undefined ? this.callPut.oiRatio.toFixed(2) : "—"}
                    </div>
                    <p style="font-size: 0.625rem; color: #64748b;">Total OI: ${(this.callPut.totalOI || 0).toLocaleString()}</p>
                </div>
                
                <!-- Median IV Card -->
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 1rem;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                ">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Median IV (chain)</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.25rem;">
                        ${this.formatPct(this.callPut.medianIV)}
                    </div>
                    <p style="font-size: 0.625rem; color: #64748b;">Across ${this.chain.length} contracts</p>
                </div>
                
                <!-- Unusual Flags Card -->
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 1rem;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                ">
                    <h3 style="font-size: 0.75rem; font-weight: 500; color: #64748b; margin-bottom: 0.5rem;">Unusual Flags</h3>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">
                        ${this.unusual.length}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.375rem;">
                        <input type="checkbox" id="unusual-filter" ${this.onlyUnusual ? 'checked' : ''} style="
                            width: 14px;
                            height: 14px;
                            border-radius: 3px;
                            border: 1px solid #d1d5db;
                            cursor: pointer;
                        ">
                        <label for="unusual-filter" style="font-size: 0.625rem; color: #64748b; cursor: pointer;">Show only unusual</label>
                    </div>
                </div>
            </div>
        `;
    }

    getMainGridHTML(displayRows) {
        return `
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1rem;">
                <!-- Left Column: Option Chain Overview -->
                <div style="
                    background: white;
                    border-radius: 12px;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    overflow: hidden;
                ">
                    <div style="padding: 1rem; border-bottom: 1px solid #e2e8f0;">
                        <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0;">Option Chain Overview</h3>
                    </div>
                    <div style="overflow-x: auto;">
                        ${this.getChainTableHTML(displayRows)}
                    </div>
                </div>

                <!-- Right Column: Charts -->
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <!-- How to Read Charts Together Guide -->
                    <div style="
                        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                        border-radius: 12px;
                        border: 1px solid #cbd5e1;
                        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                        padding: 1rem;
                        margin-bottom: 0.5rem;
                    ">
                        <h4 style="font-size: 0.875rem; font-weight: 600; color: #1e293b; margin: 0 0 0.5rem 0; display: flex; align-items: center;">
                            📊 How to Read Them Together
                            <span style="
                                margin-left: 0.5rem;
                                background: #3b82f6;
                                color: white;
                                padding: 2px 6px;
                                border-radius: 4px;
                                font-size: 0.625rem;
                                font-weight: 500;
                            ">Hover over chart titles for details</span>
                        </h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.75rem; color: #475569;">
                            <div>
                                <strong style="color: #1e293b;">Bullish Scenario:</strong><br>
                                • Stock trending up<br>
                                • Green OI clusters at higher strikes<br>
                                • Right-side delta peak (calls)
                            </div>
                            <div>
                                <strong style="color: #1e293b;">Bearish Scenario:</strong><br>
                                • Stock trending down<br>
                                • Green OI clusters at lower strikes<br>
                                • Left-side delta peak (puts)
                            </div>
                        </div>
                    </div>
                    <!-- IV Term Structure -->
                    <div style="
                        background: white;
                        border-radius: 12px;
                        border: 1px solid #e2e8f0;
                        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    ">
                        <div style="padding: 1rem; border-bottom: 1px solid #e2e8f0;">
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0; position: relative; display: inline-block; cursor: help;" 
                                id="iv-term-tooltip-trigger">
                                IV Term Structure
                                <span id="iv-term-tooltip" style="
                                    position: absolute;
                                    background: #1e293b;
                                    color: white;
                                    padding: 8px 12px;
                                    border-radius: 6px;
                                    font-size: 0.75rem;
                                    font-weight: 400;
                                    white-space: normal;
                                    max-width: 300px;
                                    z-index: 1000;
                                    opacity: 0;
                                    pointer-events: none;
                                    transition: opacity 0.2s;
                                    top: -60px;
                                    left: 0;
                                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                                ">
                                    Shows how implied volatility changes across different expiration dates. Higher IV = more expensive options. Look for normal upward curves (healthy) or inverted curves (near-term fear).
                                </span>
                            </h3>
                        </div>
                        <div style="padding: 1rem;">
                            <div id="iv-term-chart" style="height: 180px;"></div>
                            <p style="margin-top: 0.5rem; font-size: 0.625rem; color: #64748b;">Median IV per expiry for next 8 expirations.</p>
                        </div>
                    </div>

                    <!-- Underlying Daily -->
                    <div style="
                        background: white;
                        border-radius: 12px;
                        border: 1px solid #e2e8f0;
                        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    ">
                        <div style="padding: 1rem; border-bottom: 1px solid #e2e8f0;">
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0; position: relative; display: inline-block; cursor: help;" 
                                id="underlying-tooltip-trigger">
                                Underlying (Daily)
                                <span id="underlying-tooltip" style="
                                    position: absolute;
                                    background: #1e293b;
                                    color: white;
                                    padding: 8px 12px;
                                    border-radius: 6px;
                                    font-size: 0.75rem;
                                    font-weight: 400;
                                    white-space: normal;
                                    max-width: 300px;
                                    z-index: 1000;
                                    opacity: 0;
                                    pointer-events: none;
                                    transition: opacity 0.2s;
                                    top: -60px;
                                    left: 0;
                                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                                ">
                                    Shows the actual stock price movement over time. Look for trends, support/resistance levels, and volatility patterns. This provides context for all your options decisions.
                                </span>
                            </h3>
                        </div>
                        <div style="padding: 1rem;">
                            <div id="underlying-chart" style="height: 180px;"></div>
                            <p style="margin-top: 0.5rem; font-size: 0.625rem; color: #64748b;">Candles/RSI can replace this area chart.</p>
                        </div>
                    </div>

                    <!-- Open Interest Change Heatmap -->
                    <div style="
                        background: white;
                        border-radius: 12px;
                        border: 1px solid #e2e8f0;
                        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    ">
                        <div style="padding: 1rem; border-bottom: 1px solid #e2e8f0;">
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0; position: relative; display: inline-block; cursor: help;" 
                                id="oi-change-tooltip-trigger">
                                Open Interest Change
                                <span id="oi-change-tooltip" style="
                                    position: absolute;
                                    background: #1e293b;
                                    color: white;
                                    padding: 8px 12px;
                                    border-radius: 6px;
                                    font-size: 0.75rem;
                                    font-weight: 400;
                                    white-space: normal;
                                    max-width: 300px;
                                    z-index: 1000;
                                    opacity: 0;
                                    pointer-events: none;
                                    transition: opacity 0.2s;
                                    top: -60px;
                                    left: 0;
                                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                                ">
                                    Heatmap showing how much open interest changed from yesterday. Green/Yellow = more contracts opened, Purple/Blue = contracts closed. Shows where "smart money" is positioning.
                                </span>
                            </h3>
                        </div>
                        <div style="padding: 1rem;">
                            <div id="oi-heatmap-chart" style="height: 350px; width: 100%; overflow: visible;"></div>
                        </div>
                    </div>

                    <!-- Delta Distribution -->
                    <div style="
                        background: white;
                        border-radius: 12px;
                        border: 1px solid #e2e8f0;
                        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    ">
                        <div style="padding: 1rem; border-bottom: 1px solid #e2e8f0;">
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0; position: relative; display: inline-block; cursor: help;" 
                                id="delta-dist-tooltip-trigger">
                                Delta Distribution
                                <span id="delta-dist-tooltip" style="
                                    position: absolute;
                                    background: #1e293b;
                                    color: white;
                                    padding: 8px 12px;
                                    border-radius: 6px;
                                    font-size: 0.75rem;
                                    font-weight: 400;
                                    white-space: normal;
                                    max-width: 300px;
                                    z-index: 1000;
                                    opacity: 0;
                                    pointer-events: none;
                                    transition: opacity 0.2s;
                                    top: -60px;
                                    left: 0;
                                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                                ">
                                    Shows how many contracts exist at different delta levels. Left side = put options (bearish), right side = call options (bullish). Peaks show where most trading activity is concentrated.
                                </span>
                            </h3>
                        </div>
                        <div style="padding: 1rem;">
                            <div id="delta-distribution-chart" style="height: 350px; width: 100%; overflow: visible;"></div>
                            <p style="margin-top: 0.5rem; font-size: 0.625rem; color: #64748b;">Contracts (weighted) by delta value.</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getChainTableHTML(displayRows) {
        if (displayRows.length === 0) {
            return '<div style="text-align: center; padding: 2rem; color: #64748b;">No contracts found</div>';
        }

        return `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Contract</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Expiry</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Type</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Strike</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">IV</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Δ</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Γ</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Θ</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Vega</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Last</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Vol</th>
                        <th style="padding: 0.5rem 0.75rem; text-align: left; font-size: 0.625rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">OI</th>
                    </tr>
                </thead>
                <tbody>
                    ${displayRows.map((r, index) => `
                        <tr style="
                            border-bottom: 1px solid #f1f5f9;
                            transition: background-color 0.2s;
                        " onmouseover="this.style.backgroundColor='#f8fafc'" onmouseout="this.style.backgroundColor='transparent'">
                            <td style="padding: 0.5rem 0.75rem; font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace; font-size: 0.625rem; color: #1e293b; font-weight: 500;">${r.contract}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.expiry}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569; text-transform: capitalize; font-weight: 500;">${r.type}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #1e293b; font-weight: 500;">${r.strike}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #1e293b; font-weight: 500;">${this.formatPct(r.iv || r.implied_volatility)}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.delta ? r.delta.toFixed(2) : '—'}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.gamma ? r.gamma.toFixed(3) : '—'}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.theta ? r.theta.toFixed(3) : '—'}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.vega ? r.vega.toFixed(3) : '—'}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #1e293b; font-weight: 500;">${r.last || r.last_price ? (r.last || r.last_price).toFixed(2) : '—'}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.day_volume || '—'}</td>
                            <td style="padding: 0.5rem 0.75rem; font-size: 0.75rem; color: #475569;">${r.day_oi || '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    getEmptyStateHTML() {
        return `
            <div style="
                background: white;
                border-radius: 12px;
                padding: 3rem;
                text-align: center;
                border: 1px solid #e2e8f0;
                box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                margin: 2rem 0;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="font-size: 1.25rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">
                    No Data Available
                </h3>
                <p style="color: #64748b; margin-bottom: 2rem;">
                    Unable to load options data for ${this.currentTicker}. Please check your API connection and try again.
                </p>
                <button onclick="window.consumerOptionsDashboard.loadRealData().then(() => window.consumerOptionsDashboard.render())" 
                        style="
                            background: #3b82f6;
                            color: white;
                            padding: 0.75rem 1.5rem;
                            border-radius: 8px;
                            border: none;
                            font-weight: 500;
                            cursor: pointer;
                            transition: all 0.2s;
                        "
                        onmouseover="this.style.backgroundColor='#2563eb'"
                        onmouseout="this.style.backgroundColor='#3b82f6'">
                    🔄 Retry Loading Data
                </button>
            </div>
        `;
    }

    getFooterHTML() {
        return `
            <div style="margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0;">
                <div style="font-size: 0.75rem; color: #64748b; text-align: center;">
                    <p>Real-time consumer options analytics powered by Polygon API. Data refreshed every 60 seconds.</p>
                </div>
            </div>
        `;
    }

    renderCharts() {
        console.log('Rendering charts...');
        this.renderIVTermChart();
        this.renderUnderlyingChart();
        this.renderOIChangeHeatmap();
        this.renderDeltaDistribution();
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    renderIVTermChart() {
        const container = document.getElementById('iv-term-chart');
        if (!container) {
            console.log('IV Term chart container not available');
            return;
        }

        // Create a beautiful line chart visualization
        const chartData = this.ivTerm.map(point => ({
            expiry: point.expiry.slice(5), // Show MM-DD
            iv: (point.iv_median || point.median_iv || 0) * 100
        })).filter(point => point.iv > 0); // Filter out invalid IV values

        // Create SVG chart
        const width = container.clientWidth || 300;
        const height = 220;
        const margin = { top: 20, right: 30, bottom: 40, left: 50 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        // Calculate scales
        const maxIV = Math.max(...chartData.map(d => d.iv));
        const minIV = Math.min(...chartData.map(d => d.iv));
        const ivRange = maxIV - minIV;
        const yMin = Math.max(0, minIV - ivRange * 0.1);
        const yMax = maxIV + ivRange * 0.1;

        // Create path for line
        const points = chartData.map((d, i) => {
            const x = (i / (chartData.length - 1)) * chartWidth;
            const y = chartHeight - ((d.iv - yMin) / (yMax - yMin)) * chartHeight;
            return `${x},${y}`;
        });
        const pathData = `M${points.join('L')}`;

        container.innerHTML = `
            <svg width="100%" height="${height}" style="overflow: visible;">
                <!-- Grid lines -->
                ${[0, 0.25, 0.5, 0.75, 1].map(ratio => `
                    <line x1="${margin.left}" y1="${margin.top + ratio * chartHeight}" 
                          x2="${margin.left + chartWidth}" y2="${margin.top + ratio * chartHeight}" 
                          stroke="#f1f5f9" stroke-width="1"/>
                `).join('')}
                
                <!-- Y-axis labels -->
                ${[0, 0.25, 0.5, 0.75, 1].map(ratio => {
                    const value = yMax - ratio * (yMax - yMin);
                    return `
                        <text x="${margin.left - 10}" y="${margin.top + ratio * chartHeight + 5}" 
                              text-anchor="end" font-size="12" fill="#64748b">
                            ${value.toFixed(0)}%
                        </text>
                    `;
                }).join('')}
                
                <!-- X-axis labels -->
                ${chartData.map((d, i) => `
                    <text x="${margin.left + (i / (chartData.length - 1)) * chartWidth}" 
                          y="${height - 10}" 
                          text-anchor="middle" font-size="10" fill="#64748b">
                        ${d.expiry}
                    </text>
                `).join('')}
                
                <!-- Line chart -->
                <g transform="translate(${margin.left}, ${margin.top})">
                    <path d="${pathData}" fill="none" stroke="#3b82f6" stroke-width="2"/>
                    
                    <!-- Data points -->
                    ${chartData.map((d, i) => {
                        const x = (i / (chartData.length - 1)) * chartWidth;
                        const y = chartHeight - ((d.iv - yMin) / (yMax - yMin)) * chartHeight;
                        return `
                            <circle cx="${x}" cy="${y}" r="4" fill="#3b82f6" stroke="white" stroke-width="2">
                                <title>${d.expiry}: ${d.iv.toFixed(1)}%</title>
                            </circle>
                        `;
                    }).join('')}
                </g>
            </svg>
        `;
    }

    renderUnderlyingChart() {
        const container = document.getElementById('underlying-chart');
        if (!container) {
            console.log('Underlying chart container not available');
            return;
        }

        // Use recent 30 days for better visualization
        const recent = this.underlying.slice(-30);
        const minPrice = Math.min(...recent.map(d => d.close));
        const maxPrice = Math.max(...recent.map(d => d.close));
        const priceRange = maxPrice - minPrice;
        const yMin = minPrice - priceRange * 0.1;
        const yMax = maxPrice + priceRange * 0.1;

        // Create SVG area chart
        const width = container.clientWidth || 300;
        const height = 220;
        const margin = { top: 20, right: 30, bottom: 40, left: 50 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        // Create area path
        const points = recent.map((d, i) => {
            const x = (i / (recent.length - 1)) * chartWidth;
            const y = chartHeight - ((d.close - yMin) / (yMax - yMin)) * chartHeight;
            return `${x},${y}`;
        });
        
        const areaPath = `M0,${chartHeight}L${points.join('L')}L${chartWidth},${chartHeight}Z`;
        const linePath = `M${points.join('L')}`;

        container.innerHTML = `
            <svg width="100%" height="${height}" style="overflow: visible;">
                <defs>
                    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.3"/>
                        <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.05"/>
                    </linearGradient>
                </defs>
                
                <!-- Grid lines -->
                ${[0, 0.25, 0.5, 0.75, 1].map(ratio => `
                    <line x1="${margin.left}" y1="${margin.top + ratio * chartHeight}" 
                          x2="${margin.left + chartWidth}" y2="${margin.top + ratio * chartHeight}" 
                          stroke="#f1f5f9" stroke-width="1"/>
                `).join('')}
                
                <!-- Y-axis labels -->
                ${[0, 0.25, 0.5, 0.75, 1].map(ratio => {
                    const value = yMax - ratio * (yMax - yMin);
                    return `
                        <text x="${margin.left - 10}" y="${margin.top + ratio * chartHeight + 5}" 
                              text-anchor="end" font-size="12" fill="#64748b">
                            $${value.toFixed(0)}
                        </text>
                    `;
                }).join('')}
                
                <!-- X-axis labels -->
                ${recent.map((d, i) => {
                    if (i % Math.ceil(recent.length / 5) === 0) { // Show every 5th label
                        const x = margin.left + (i / (recent.length - 1)) * chartWidth;
                        // Generate date based on index (recent data is last 30 days)
                        const daysAgo = recent.length - 1 - i;
                        const date = new Date();
                        date.setDate(date.getDate() - daysAgo);
                        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                        return `
                            <text x="${x}" y="${height - 10}" 
                                  text-anchor="middle" font-size="10" fill="#64748b">
                                ${dateStr}
                            </text>
                        `;
                    }
                    return '';
                }).join('')}
                
                <!-- Area chart -->
                <g transform="translate(${margin.left}, ${margin.top})">
                    <path d="${areaPath}" fill="url(#areaGradient)"/>
                    <path d="${linePath}" fill="none" stroke="#3b82f6" stroke-width="2"/>
                </g>
            </svg>
        `;
    }

    renderOIChangeHeatmap() {
        const container = document.getElementById('oi-heatmap-chart');
        if (!container) {
            console.log('OI Heatmap chart container not available');
            return;
        }

        const data = this.oiHeatmapData;
        if (!data || !data.expiries || !data.strikes || !data.delta_oi) {
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: #64748b;">No OI change data available</div>';
            return;
        }

        const { expiries, strikes, delta_oi, min_delta, max_delta } = data;
        
        // Create SVG heatmap
        const containerWidth = container.clientWidth || 400;
        const width = Math.min(containerWidth, 450);
        const height = 350;
        const margin = { top: 30, right: 80, bottom: 80, left: 50 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        const cellWidth = chartWidth / strikes.length;
        const cellHeight = chartHeight / expiries.length;

        // Color scale function (viridis-like: dark purple/blue to bright yellow/green)
        const getColor = (value) => {
            const normalized = (value - min_delta) / (max_delta - min_delta);
            
            // Viridis color scheme approximation
            if (normalized < 0.1) return '#440154'; // Dark purple
            if (normalized < 0.2) return '#482777'; // Purple
            if (normalized < 0.3) return '#3f4a8a'; // Blue-purple
            if (normalized < 0.4) return '#31688e'; // Blue
            if (normalized < 0.5) return '#26828e'; // Blue-green
            if (normalized < 0.6) return '#1f9e89'; // Teal
            if (normalized < 0.7) return '#35b779'; // Green
            if (normalized < 0.8) return '#6ece58'; // Light green
            if (normalized < 0.9) return '#b5de2b'; // Yellow-green
            return '#fde725'; // Bright yellow
        };

        // Create heatmap cells
        const cells = [];
        for (let i = 0; i < expiries.length; i++) {
            for (let j = 0; j < strikes.length; j++) {
                const value = delta_oi[i][j];
                const x = margin.left + j * cellWidth;
                const y = margin.top + i * cellHeight;
                
                cells.push(`
                    <rect x="${x}" y="${y}" width="${cellWidth}" height="${cellHeight}" 
                          fill="${getColor(value)}" stroke="#e2e8f0" stroke-width="0.5">
                        <title>${expiries[i]} | ${strikes[j]} | Δ OI: ${value}</title>
                    </rect>
                `);
            }
        }

        // Create axis labels with better spacing and wrapping
        const strikeLabels = strikes.map((strike, i) => {
            const x = margin.left + i * cellWidth + cellWidth/2;
            const y = height - 25;
            return `
                <text x="${x}" 
                      y="${y}" 
                      text-anchor="middle" 
                      font-size="11" 
                      fill="#374151" 
                      font-weight="500"
                      transform="rotate(-45, ${x}, ${y})">
                    ${strike}
                </text>
            `;
        }).join('');

        const expiryLabels = expiries.map((expiry, i) => {
            const x = margin.left - 10;
            const y = margin.top + i * cellHeight + cellHeight/2;
            return `
                <text x="${x}" 
                      y="${y}" 
                      text-anchor="end" 
                      font-size="10" 
                      fill="#64748b" 
                      dominant-baseline="middle">
                    ${expiry}
                </text>
            `;
        }).join('');

        // Create color legend
        const legendWidth = Math.min(140, chartWidth * 0.35);
        const legendHeight = 20;
        const legendX = margin.left + chartWidth - legendWidth - 5;
        const legendY = margin.top;

        const legendGradient = Array.from({length: 20}, (_, i) => {
            const value = min_delta + (i / 19) * (max_delta - min_delta);
            const color = getColor(value);
            return `<stop offset="${i/19}" stop-color="${color}"/>`;
        }).join('');

        container.innerHTML = `
            <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow: visible; max-width: 100%;">
                <defs>
                    <linearGradient id="heatmapGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        ${legendGradient}
                    </linearGradient>
                </defs>
                
                <!-- Heatmap cells -->
                ${cells.join('')}
                
                <!-- Axis labels -->
                ${strikeLabels}
                ${expiryLabels}
                
                <!-- Axis titles -->
                <text x="${margin.left + chartWidth/2}" 
                      y="${height - 10}" 
                      text-anchor="middle" 
                      font-size="11" 
                      font-weight="600" 
                      fill="#374151">Strike</text>
                <text x="${margin.left + chartWidth + 15}" 
                      y="${margin.top + chartHeight/2}" 
                      text-anchor="middle" 
                      font-size="11" 
                      font-weight="600" 
                      fill="#374151" 
                      transform="rotate(-90, ${margin.left + chartWidth + 15}, ${margin.top + chartHeight/2})">Expiry</text>
                
                <!-- Color legend -->
                <rect x="${legendX}" y="${legendY}" width="${legendWidth}" height="${legendHeight}" 
                      fill="url(#heatmapGradient)" stroke="#e2e8f0"/>
                <text x="${legendX}" y="${legendY - 5}" font-size="10" font-weight="600" fill="#374151">Δ OI (contracts)</text>
                <text x="${legendX}" y="${legendY + legendHeight + 15}" font-size="8" fill="#64748b">${min_delta}</text>
                <text x="${legendX + legendWidth}" y="${legendY + legendHeight + 15}" font-size="8" fill="#64748b" text-anchor="end">${max_delta}</text>
            </svg>
        `;
    }

    renderDeltaDistribution() {
        const container = document.getElementById('delta-distribution-chart');
        if (!container) {
            console.log('Delta Distribution chart container not available');
            return;
        }

        const data = this.deltaDistributionData;
        if (!data || !data.bins || !data.counts) {
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: #64748b;">No delta distribution data available</div>';
            return;
        }

        const { bins, counts, bin_centers, max_count } = data;
        
        // Create SVG histogram
        const containerWidth = container.clientWidth || 400;
        const width = Math.min(containerWidth, 450);
        const height = 350;
        const margin = { top: 30, right: 40, bottom: 80, left: 50 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        const barWidth = chartWidth / (bins.length - 1);
        const maxHeight = chartHeight * 0.9;

        // Create bars
        const bars = counts.map((count, i) => {
            const barHeight = (count / max_count) * maxHeight;
            const x = margin.left + i * barWidth;
            const y = margin.top + maxHeight - barHeight;
            
            return `
                <rect x="${x}" y="${y}" width="${barWidth * 0.8}" height="${barHeight}" 
                      fill="#ff7f0e" stroke="white" stroke-width="1">
                    <title>Delta: ${bin_centers[i]?.toFixed(2) || 'N/A'} | Contracts: ${count}</title>
                </rect>
            `;
        }).join('');

        // Create x-axis labels with better spacing
        const xLabels = bin_centers.map((center, i) => {
            if (i % 3 === 0) { // Show every third label to avoid crowding
                const x = margin.left + i * barWidth + barWidth/2;
                return `
                    <text x="${x}" 
                          y="${height - 25}" 
                          text-anchor="middle" 
                          font-size="11" 
                          fill="#374151"
                          font-weight="500">
                        ${center?.toFixed(1) || 'N/A'}
                    </text>
                `;
            }
            return '';
        }).join('');

        // Create y-axis labels with better formatting
        const yLabels = [0, 0.25, 0.5, 0.75, 1].map(ratio => {
            const value = Math.round(ratio * max_count);
            const y = margin.top + maxHeight - (ratio * maxHeight);
            const formattedValue = value >= 1000 ? `${(value/1000).toFixed(1)}k` : value.toString();
            return `
                <text x="${margin.left - 10}" 
                      y="${y + 3}" 
                      text-anchor="end" 
                      font-size="10" 
                      fill="#64748b">
                    ${formattedValue}
                </text>
            `;
        }).join('');

        // Create grid lines
        const gridLines = [0, 0.25, 0.5, 0.75, 1].map(ratio => {
            const y = margin.top + maxHeight - (ratio * maxHeight);
            return `
                <line x1="${margin.left}" y1="${y}" x2="${margin.left + chartWidth}" y2="${y}" 
                      stroke="#f1f5f9" stroke-width="1"/>
            `;
        }).join('');

        container.innerHTML = `
            <svg width="100%" height="${height}" style="overflow: visible;">
                <!-- Grid lines -->
                ${gridLines}
                
                <!-- Bars -->
                ${bars}
                
                <!-- Axis labels -->
                ${xLabels}
                ${yLabels}
                
                <!-- Axis titles -->
                <text x="${margin.left + chartWidth/2}" 
                      y="${height - 10}" 
                      text-anchor="middle" 
                      font-size="11" 
                      font-weight="600" 
                      fill="#374151">Delta</text>
                <text x="${margin.left + chartWidth + 15}" 
                      y="${margin.top + chartHeight/2}" 
                      text-anchor="middle" 
                      font-size="11" 
                      font-weight="600" 
                      fill="#374151" 
                      transform="rotate(-90, ${margin.left + chartWidth + 15}, ${margin.top + chartHeight/2})">Contracts (weighted)</text>
            </svg>
        `;
    }

    renderChainTable() {
        const displayRows = this.onlyUnusual ? this.unusual : this.chain;
        const container = document.getElementById('chain-table-container');
        if (container) {
            container.innerHTML = this.getChainTableHTML(displayRows);
        }
    }

    setupTooltips() {
        if (this.tooltipsSetup) {
            console.log('Tooltips already set up');
            return;
        }
        
        console.log('Setting up tooltips...');
        
        // Use event delegation to handle tooltips
        const container = document.getElementById('consumeroptions-dashboard');
        if (!container) {
            console.log('Container not found for tooltips');
            return;
        }

        container.addEventListener('mouseenter', (e) => {
            if (e.target.id === 'iv-term-tooltip-trigger') {
                const tooltip = document.getElementById('iv-term-tooltip');
                if (tooltip) {
                    console.log('IV tooltip mouseenter');
                    tooltip.style.opacity = '1';
                }
            } else if (e.target.id === 'underlying-tooltip-trigger') {
                const tooltip = document.getElementById('underlying-tooltip');
                if (tooltip) {
                    console.log('Underlying tooltip mouseenter');
                    tooltip.style.opacity = '1';
                }
            } else if (e.target.id === 'oi-change-tooltip-trigger') {
                const tooltip = document.getElementById('oi-change-tooltip');
                if (tooltip) {
                    console.log('OI tooltip mouseenter');
                    tooltip.style.opacity = '1';
                }
            } else if (e.target.id === 'delta-dist-tooltip-trigger') {
                const tooltip = document.getElementById('delta-dist-tooltip');
                if (tooltip) {
                    console.log('Delta tooltip mouseenter');
                    tooltip.style.opacity = '1';
                }
            }
        }, true);

        container.addEventListener('mouseleave', (e) => {
            if (e.target.id === 'iv-term-tooltip-trigger') {
                const tooltip = document.getElementById('iv-term-tooltip');
                if (tooltip) {
                    console.log('IV tooltip mouseleave');
                    tooltip.style.opacity = '0';
                }
            } else if (e.target.id === 'underlying-tooltip-trigger') {
                const tooltip = document.getElementById('underlying-tooltip');
                if (tooltip) {
                    console.log('Underlying tooltip mouseleave');
                    tooltip.style.opacity = '0';
                }
            } else if (e.target.id === 'oi-change-tooltip-trigger') {
                const tooltip = document.getElementById('oi-change-tooltip');
                if (tooltip) {
                    console.log('OI tooltip mouseleave');
                    tooltip.style.opacity = '0';
                }
            } else if (e.target.id === 'delta-dist-tooltip-trigger') {
                const tooltip = document.getElementById('delta-dist-tooltip');
                if (tooltip) {
                    console.log('Delta tooltip mouseleave');
                    tooltip.style.opacity = '0';
                }
            }
        }, true);
        
        this.tooltipsSetup = true;
        console.log('Tooltips setup complete');
    }

    showLoading(show) {
        const container = document.getElementById('consumeroptions-dashboard');
        if (!container) return;

        if (show) {
            container.innerHTML = `
                <div class="min-h-screen flex items-center justify-center bg-gray-50">
                    <div class="text-center">
                        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                        <h2 class="text-xl font-semibold text-gray-700 mb-2">Loading Consumer Options Data...</h2>
                        <p class="text-gray-500">Fetching real-time data from Polygon API via consumeroptions service</p>
                    </div>
                </div>
            `;
        }
    }

    showError(message) {
        const container = document.getElementById('consumeroptions-dashboard');
        if (!container) return;

        container.innerHTML = `
            <div class="min-h-screen flex items-center justify-center bg-gray-50">
                <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
                    <div class="mb-6">
                        <div class="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                            <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                            </svg>
                        </div>
                        <h2 class="text-2xl font-bold text-gray-900 mb-2">API Connection Error</h2>
                        <p class="text-gray-600">${message}</p>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4 mb-6">
                        <h3 class="font-semibold text-gray-900 mb-2">Possible solutions:</h3>
                        <ul class="text-sm text-gray-600 text-left space-y-1">
                            <li>• Check if the FastAPI server is running</li>
                            <li>• Verify the POLYGON_API_KEY is set in environment</li>
                            <li>• Check consumeroptions service endpoints</li>
                            <li>• Ensure ticker symbol is valid</li>
                        </ul>
                    </div>
                    
                    <div class="space-y-3">
                        <button onclick="window.consumerOptionsDashboard.loadRealData().then(() => window.consumerOptionsDashboard.render())" 
                                class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                            🔄 Retry Connection
                        </button>
                    </div>
                </div>
            </div>
        `;
    }



    exportData() {
        const displayRows = this.onlyUnusual ? this.unusual : this.chain;
        
        if (displayRows.length === 0) {
            alert('No data to export');
            return;
        }

        const csv = this.convertToCSV(displayRows);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentTicker}_options_chain_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    convertToCSV(contracts) {
        const headers = [
            'Contract', 'Expiry', 'Type', 'Strike', 'IV', 'Delta', 'Gamma', 
            'Theta', 'Vega', 'Last Price', 'Volume', 'Open Interest'
        ];
        
        const rows = contracts.map(c => [
            c.contract,
            c.expiry,
            c.type,
            c.strike,
            c.iv,
            c.delta,
            c.gamma,
            c.theta,
            c.vega,
            c.last,
            c.day_volume,
            c.day_oi
        ]);

        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }
}

// Initialize dashboard when DOM is loaded
let consumerOptionsDashboard;

function initializeConsumerOptionsDashboard() {
    console.log('Initializing Consumer Options Dashboard - React UI Design');
    const container = document.getElementById('consumeroptions-dashboard');
    
    if (!consumerOptionsDashboard && container) {
        consumerOptionsDashboard = new ConsumerOptionsReactDashboard();
    } else if (consumerOptionsDashboard) {
        consumerOptionsDashboard.loadRealData().then(() => consumerOptionsDashboard.render());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Consumer Options Dashboard: DOM loaded, initializing React UI...');
    
    // Small delay to ensure all resources are loaded
    setTimeout(() => {
        initializeConsumerOptionsDashboard();
    }, 500);
});

// Export for global access
window.ConsumerOptionsReactDashboard = ConsumerOptionsReactDashboard;
window.initializeConsumerOptionsDashboard = initializeConsumerOptionsDashboard;
