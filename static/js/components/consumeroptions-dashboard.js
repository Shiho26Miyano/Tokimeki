/**
 * Consumer Options Dashboard
 * React component for visualizing consumer options data
 */

// Wait for React to be available before defining the component
(function() {
    'use strict';
    
    function defineComponent() {
        if (typeof React === 'undefined' || typeof React.Component === 'undefined') {
            console.log('React not available yet for ConsumerOptionsDashboard, retrying in 100ms...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining ConsumerOptionsDashboard component...');

class ConsumerOptionsDashboard extends React.Component {
    constructor(props) {
        super(props);
        
        this.state = {
            // Filter
            selectedTicker: 'AAPL',
            availableTickers: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'AMD'],
            
            // OI Change heatmap data
            oiChangeData: null,
            loading: false,
            error: null,
            
            // Chart state
            refreshKey: 0
        };
        
        this.handleTickerChange = this.handleTickerChange.bind(this);
        this.loadOIData = this.loadOIData.bind(this);
        this.renderHeatmap = this.renderHeatmap.bind(this);
    }
    
    componentDidMount() {
        console.log('Consumer Options Dashboard mounted');
        this.loadOIData();
    }
    
    componentDidUpdate(prevProps, prevState) {
        if (prevState.selectedTicker !== this.state.selectedTicker) {
            this.loadOIData();
        }
        
        // Re-render heatmap when data changes
        if (prevState.oiChangeData !== this.state.oiChangeData && this.state.oiChangeData) {
            setTimeout(() => this.renderHeatmap(), 100);
        }
        
        // Also trigger on refreshKey change
        if (prevState.refreshKey !== this.state.refreshKey && this.state.oiChangeData) {
            setTimeout(() => this.renderHeatmap(), 100);
        }
    }
    
    handleTickerChange(event) {
        this.setState({ 
            selectedTicker: event.target.value.toUpperCase(),
            oiChangeData: null,
            error: null
        });
    }
    
    async loadOIData() {
        this.setState({ loading: true, error: null });
        
        try {
            const { selectedTicker } = this.state;
            const url = `/api/v1/consumeroptions/dashboard/oi-change?symbol=${encodeURIComponent(selectedTicker)}&strike_band_pct=0.2&expiries=8&combine_cp=true`;
            
            console.log('Fetching OI change data from:', url);
            const response = await fetch(url);
            
            if (!response.ok) {
                let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMsg = errorData.detail;
                    } else if (errorData.error) {
                        errorMsg = errorData.error;
                    } else if (errorData.message) {
                        errorMsg = errorData.message;
                    }
                } catch (e) {
                    // If JSON parsing fails, use the status text
                }
                throw new Error(errorMsg);
            }
            
            const result = await response.json();
            console.log('OI change data received:', result);
            
            if (result.success && result.data) {
                this.setState({ 
                    oiChangeData: result.data,
                    loading: false,
                    refreshKey: this.state.refreshKey + 1
                });
            } else {
                throw new Error(result.error || 'Failed to load OI change data');
            }
        } catch (error) {
            console.error('Error loading OI change data:', error);
            this.setState({
                error: error.message,
                loading: false
            });
        }
    }
    
    renderHeatmap() {
        const container = document.getElementById('oi-heatmap-chart');
        if (!container) return;

        const { oiChangeData } = this.state;
        if (!oiChangeData || !oiChangeData.matrix || !oiChangeData.expiries || !oiChangeData.strikes) {
            container.innerHTML = '<div style="text-align:center;padding:2rem;color:#64748b;">No OI change data available</div>';
            return;
        }

        const matrix = oiChangeData.matrix;
        const expiries = oiChangeData.expiries;
        const strikes = oiChangeData.strikes;

        if (!Array.isArray(matrix) || !Array.isArray(matrix[0])) {
            container.innerHTML = '<div style="text-align:center;padding:2rem;color:#dc2626;">Invalid matrix data structure</div>';
            return;
        }

        const formattedExpiries = expiries.map((exp) => {
            const d = new Date(exp);
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${m}-${day}`;
        });

        const flat = matrix.flat();
        const min_delta = Math.min(...flat);
        const max_delta = Math.max(...flat);

        // viridis-like scale as a function -> returns hex
        const getColor = (value) => {
            if (max_delta === min_delta) return '#35b779'; // neutral if constant
            const t = Math.max(0, Math.min(1, (value - min_delta) / (max_delta - min_delta)));
            if (t < 0.1) return '#440154';
            if (t < 0.2) return '#482777';
            if (t < 0.3) return '#3f4a8a';
            if (t < 0.4) return '#31688e';
            if (t < 0.5) return '#26828e';
            if (t < 0.6) return '#1f9e89';
            if (t < 0.7) return '#35b779';
            if (t < 0.8) return '#6ece58';
            if (t < 0.9) return '#b5de2b';
            return '#fde725';
        };

        const width = Math.max(container.clientWidth || 800, 600);
        const height = 450;
        const margin = { top: 40, right: 100, bottom: 80, left: 60 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        const cellW = chartWidth / strikes.length;
        const cellH = chartHeight / expiries.length;

        // cells
        let cells = '';
        for (let i = 0; i < expiries.length; i++) {
            for (let j = 0; j < strikes.length; j++) {
                const v = matrix[i][j];
                const x = margin.left + j * cellW;
                const y = margin.top + i * cellH;
                const c = getColor(v);
                cells += `<rect x="${x}" y="${y}" width="${cellW}" height="${cellH}" fill="${c}" stroke="#e2e8f0" stroke-width="0.5">
        <title>Expiry: ${formattedExpiries[i]} | Strike: ${strikes[j]} | Δ OI: ${v} contracts</title>
      </rect>`;
            }
        }

        // x labels
        let xLabels = '';
        for (let i = 0; i < strikes.length; i++) {
            const x = margin.left + i * cellW + cellW / 2;
            const y = height - 25;
            xLabels += `<text x="${x}" y="${y}" text-anchor="middle" font-size="11" fill="#374151" font-weight="500"
      transform="rotate(-45, ${x}, ${y})">${strikes[i]}</text>`;
        }

        // y labels
        let yLabels = '';
        for (let i = 0; i < formattedExpiries.length; i++) {
            const x = margin.left - 10;
            const y = margin.top + i * cellH + cellH / 2;
            yLabels += `<text x="${x}" y="${y}" text-anchor="end" font-size="10" fill="#64748b" dominant-baseline="middle">${formattedExpiries[i]}</text>`;
        }

        // legend gradient stops
        const legendWidth = Math.min(140, chartWidth * 0.35);
        const legendHeight = 20;
        const legendX = margin.left + chartWidth - legendWidth - 5;
        const legendY = margin.top;
        let stops = '';
        for (let i = 0; i < 20; i++) {
            const v = min_delta + (i / 19) * (max_delta - min_delta);
            const col = getColor(v);
            stops += `<stop offset="${(i / 19)}" stop-color="${col}"/>`;
        }

        const sameNote = (max_delta === min_delta)
            ? `<text x="${legendX + legendWidth/2}" y="${legendY + legendHeight + 30}" font-size="9" fill="#dc2626" text-anchor="middle" font-weight="600">⚠ All values are ${min_delta === 0 ? 'zero' : 'the same'}</text>`
            : '';

        // Build matrix table HTML
        let tableHTML = '<div style="margin-top: 20px; overflow-x: auto;"><h5 style="margin-bottom: 10px; color: #374151; font-weight: 600;">Open Interest Change Matrix (Δ OI in contracts)</h5>';
        tableHTML += '<table style="border-collapse: collapse; width: 100%; font-size: 11px; background: white; border: 1px solid #e2e8f0;">';
        
        // Header row with strikes
        tableHTML += '<thead><tr>';
        tableHTML += '<th style="padding: 8px; background: #f8fafc; border: 1px solid #e2e8f0; text-align: left; font-weight: 600; color: #64748b; position: sticky; left: 0; z-index: 10; background: #f8fafc;">Expiry →<br/>Strike ↓</th>';
        for (let j = 0; j < strikes.length; j++) {
            tableHTML += `<th style="padding: 8px; background: #f8fafc; border: 1px solid #e2e8f0; text-align: center; font-weight: 600; color: #374151; min-width: 60px;">${strikes[j]}</th>`;
        }
        tableHTML += '</tr></thead>';
        
        // Data rows
        tableHTML += '<tbody>';
        for (let i = 0; i < expiries.length; i++) {
            tableHTML += '<tr>';
            tableHTML += `<td style="padding: 8px; background: #f8fafc; border: 1px solid #e2e8f0; text-align: center; font-weight: 600; color: #64748b; position: sticky; left: 0; z-index: 5; background: #f8fafc;">${formattedExpiries[i]}</td>`;
            for (let j = 0; j < strikes.length; j++) {
                const v = matrix[i][j];
                const c = getColor(v);
                // Color the cell background based on value
                const bgColor = max_delta === min_delta ? '#f0fdf4' : c;
                const textColor = v < 0 ? '#dc2626' : (v > 0 ? '#059669' : '#64748b');
                tableHTML += `<td style="padding: 8px; border: 1px solid #e2e8f0; text-align: center; background-color: ${bgColor}; color: ${textColor}; font-weight: ${v !== 0 ? '600' : '400'};">
                    ${v.toLocaleString()}
                </td>`;
            }
            tableHTML += '</tr>';
        }
        tableHTML += '</tbody></table></div>';

        container.innerHTML = `
  <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;max-width:100%;">
    <defs>
      <linearGradient id="heatmapGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        ${stops}
      </linearGradient>
    </defs>
    <text x="${margin.left}" y="20" font-size="16" font-weight="bold" fill="#374151">Open Interest Change</text>
    ${cells}
    ${xLabels}
    ${yLabels}
    <text x="${margin.left + chartWidth/2}" y="${height - 10}" text-anchor="middle" font-size="11" font-weight="600" fill="#374151">Strike</text>
    <text x="${margin.left + chartWidth + 15}" y="${margin.top + chartHeight/2}" text-anchor="middle" font-size="11" font-weight="600" fill="#374151"
      transform="rotate(-90, ${margin.left + chartWidth + 15}, ${margin.top + chartHeight/2})">Expiry</text>
    <rect x="${legendX}" y="${legendY}" width="${legendWidth}" height="${legendHeight}" fill="url(#heatmapGradient)" stroke="#e2e8f0" stroke-width="1"/>
    <text x="${legendX}" y="${legendY - 5}" font-size="10" font-weight="600" fill="#374151">Δ OI (contracts)</text>
    <text x="${legendX}" y="${legendY + legendHeight + 15}" font-size="8" fill="#64748b">${Math.round(min_delta)}</text>
    <text x="${legendX + legendWidth}" y="${legendY + legendHeight + 15}" font-size="8" fill="#64748b" text-anchor="end">${Math.round(max_delta)}</text>
    ${sameNote}
  </svg>
  ${tableHTML}`;
    }
    
    renderPlaceholderChart(title, id) {
        return (
            <div className="card shadow-sm" style={{ height: '500px' }}>
                <div className="card-body d-flex align-items-center justify-content-center">
                    <div className="text-center text-muted">
                        <h5>{title}</h5>
                        <p>Chart coming soon</p>
                    </div>
                </div>
            </div>
        );
    }
    
    render() {
        const { selectedTicker, availableTickers, loading, error, oiChangeData } = this.state;
        
        return (
            <div className="container-fluid p-4">
                <div className="row mb-4">
                    <div className="col-12">
                        <div className="card shadow-sm">
                            <div className="card-body">
                                <h4 className="card-title mb-3">Consumer Options Dashboard</h4>
                                
                                {/* Filter Section */}
                                <div className="row align-items-end">
                                    <div className="col-md-3">
                                        <label htmlFor="ticker-select" className="form-label">
                                            <strong>Select Option Ticker:</strong>
                                        </label>
                                        <select
                                            id="ticker-select"
                                            className="form-select"
                                            value={selectedTicker}
                                            onChange={this.handleTickerChange}
                                            disabled={loading}
                                        >
                                            {availableTickers.map(ticker => (
                                                <option key={ticker} value={ticker}>
                                                    {ticker}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="col-md-3">
                                        <button
                                            className="btn btn-primary"
                                            onClick={this.loadOIData}
                                            disabled={loading}
                                        >
                                            {loading ? (
                                                <>
                                                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                                    Loading...
                                                </>
                                            ) : (
                                                'Refresh Data'
                                            )}
                                        </button>
                                    </div>
                                    {oiChangeData && (
                                        <div className="col-md-6">
                                            <div className="text-end">
                                                <small className="text-muted">
                                                    Spot Price: <strong>${oiChangeData.spot?.toFixed(2)}</strong> | 
                                                    Trading Day: <strong>{oiChangeData.t}</strong> | 
                                                    Previous Day: <strong>{oiChangeData.t_minus_1}</strong>
                                                </small>
                                            </div>
                                        </div>
                                    )}
                                </div>
                                
                                {/* Error Display */}
                                {error && (
                                    <div className="alert alert-danger mt-3" role="alert">
                                        <strong>Error:</strong> {error}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Charts Grid */}
                <div className="row g-4">
                    {/* Open Interest Change Heatmap */}
                    <div className="col-md-12">
                        <div className="card shadow-sm">
                            <div className="card-body">
                                <div id="oi-heatmap-chart" style={{ minHeight: '500px' }}></div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Placeholder charts */}
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 2', 'chart-2')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 3', 'chart-3')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 4', 'chart-4')}
                    </div>
                </div>
            </div>
        );
    }
}

// Export component
if (typeof window !== 'undefined') {
    window.ConsumerOptionsDashboard = ConsumerOptionsDashboard;
    
    // Store root to avoid creating multiple roots
    let consumerOptionsRoot = null;
    
    // Auto-initialize if container exists
    const initializeDashboard = () => {
        const container = document.getElementById('consumeroptions-dashboard');
        if (!container || typeof ReactDOM === 'undefined') {
            return;
        }
        
        // Check if already initialized
        if (consumerOptionsRoot) {
            console.log('Consumer Options Dashboard already initialized');
            return;
        }
        
        console.log('Initializing Consumer Options Dashboard...');
        
        // Use React 18 createRoot if available, otherwise React 17 render
        if (ReactDOM.createRoot) {
            consumerOptionsRoot = ReactDOM.createRoot(container);
            consumerOptionsRoot.render(React.createElement(ConsumerOptionsDashboard));
        } else {
            ReactDOM.render(React.createElement(ConsumerOptionsDashboard), container);
        }
    };
    
    // Only initialize once when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboard);
    } else {
        // Small delay to ensure other scripts are loaded
        setTimeout(initializeDashboard, 100);
    }
}

        } // end defineComponent
        
        // Start trying to define the component
        defineComponent();
    })();
