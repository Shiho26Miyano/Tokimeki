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
            console.log('Current hostname:', window.location.hostname);
            console.log('Current protocol:', window.location.protocol);
            console.log('Current port:', window.location.port);
            
            const response = await fetch('/api/v1/', {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('API health check passed:', data);
                
                // Check if consumeroptions endpoints are available
                if (data.endpoints?.consumeroptions) {
                    console.log('✅ Consumer options endpoints available:', data.endpoints.consumeroptions);
                } else {
                    console.warn('⚠️ Consumer options endpoints not found in API info');
                    console.log('Available endpoints:', Object.keys(data.endpoints || {}));
                }
            } else {
                console.warn(`❌ API health check failed: ${response.status}`);
                const errorText = await response.text();
                console.warn('Error details:', errorText);
            }
            
            // Additional check specifically for consumeroptions endpoint
            try {
                const testResponse = await fetch('/api/v1/consumeroptions/dashboard/data/COST?days=1', {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' }
                });
                console.log(`Consumer Options endpoint test: ${testResponse.status}`);
                if (!testResponse.ok) {
                    const errorText = await testResponse.text();
                    console.warn('Consumer Options endpoint error:', errorText);
                }
            } catch (testError) {
                console.error('Consumer Options endpoint test failed:', testError);
            }
            
        } catch (error) {
            console.error('API health check error:', error);
            console.error('This suggests the FastAPI server may not be running or accessible');
        }
    }

    async loadRealData() {
        try {
            console.log(`Loading real data for ${this.currentTicker}...`);
            console.log(`Environment: ${window.location.hostname}`);
            this.showLoading(true);

            // Call the consumeroptions dashboard API with retry logic
            const apiUrl = `/api/v1/consumeroptions/dashboard/data/${this.currentTicker}?days=60&_t=${Date.now()}`;
            console.log(`Making API call to: ${apiUrl}`);
            
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                // Add timeout for Railway
                signal: AbortSignal.timeout(30000) // 30 second timeout
            });
            
            console.log(`API response status: ${response.status}`);
            console.log(`API response headers:`, Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API error response:`, errorText);
                
                if (response.status === 404) {
                    throw new Error(`API endpoint not found: ${apiUrl}. Check if consumeroptions endpoints are properly registered.`);
                } else if (response.status === 500) {
                    console.error(`Server error details:`, errorText);
                    throw new Error(`Server error: ${errorText}`);
                } else {
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
            }
            
            const data = await response.json();
            console.log('Real data loaded successfully:', data);
            
            // Enhanced debugging for Railway
            console.log('=== API Response Debug Info ===');
            console.log('Chain data length:', data.chain_data?.contracts?.length || 0);
            console.log('Call/Put ratios present:', !!data.call_put_ratios);
            console.log('IV term structure length:', data.iv_term_structure?.length || 0);
            console.log('Unusual activity length:', data.unusual_activity?.length || 0);
            
            if (data.chain_data?.contracts?.length > 0) {
                console.log('Sample contract data:', data.chain_data.contracts[0]);
            }
            if (data.call_put_ratios) {
                console.log('Call/Put ratios data:', data.call_put_ratios);
            }
            if (data.iv_term_structure?.length > 0) {
                console.log('Sample IV term data:', data.iv_term_structure[0]);
            }

            // Validate data before processing
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid API response format');
            }

            // Process the API response
            this.processAPIData(data);

        } catch (error) {
            console.error('Error loading real data:', error);
            console.error('Error stack:', error.stack);
            
            // Enhanced error handling for Railway deployment
            let errorMessage = 'Unknown error occurred';
            
            if (error.name === 'AbortError') {
                errorMessage = 'Request timeout - API took too long to respond';
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = 'Network error: Cannot connect to server';
            } else if (error.message.includes('404')) {
                errorMessage = 'Consumer Options API endpoints not found. Check deployment.';
            } else if (error.message.includes('500')) {
                errorMessage = `Server error: ${error.message}`;
            } else {
                errorMessage = `API Error: ${error.message}`;
            }
            
            this.showError(errorMessage);
            
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

        console.log('Processed API data:', {
            chainLength: this.chain.length,
            unusualCount: this.unusual.length,
            callPutRatios: this.callPut,
            sampleContract: this.chain[0],
            sampleIVTerm: this.ivTerm[0]
        });

        // Render the dashboard with the processed data
        this.render();
    }

    initializeEmptyData() {
        console.warn('Initializing empty data structures due to API failure');
        
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
        
        // For Railway deployment, try to show a helpful message
        console.log('Data initialization complete. Dashboard will show empty state.');
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
        }, 100);
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

                <!-- Right Column: IV Term Structure + Underlying -->
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <!-- IV Term Structure -->
                    <div style="
                        background: white;
                        border-radius: 12px;
                        border: 1px solid #e2e8f0;
                        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    ">
                        <div style="padding: 1rem; border-bottom: 1px solid #e2e8f0;">
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0;">IV Term Structure</h3>
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
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0;">Underlying (Daily)</h3>
                        </div>
                        <div style="padding: 1rem;">
                            <div id="underlying-chart" style="height: 180px;"></div>
                            <p style="margin-top: 0.5rem; font-size: 0.625rem; color: #64748b;">Candles/RSI can replace this area chart.</p>
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
                
                <!-- Area chart -->
                <g transform="translate(${margin.left}, ${margin.top})">
                    <path d="${areaPath}" fill="url(#areaGradient)"/>
                    <path d="${linePath}" fill="none" stroke="#3b82f6" stroke-width="2"/>
                </g>
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
