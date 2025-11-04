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
            chartData: {},
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
            const url = `/api/v1/consumeroptions/dashboard/oi-change?symbol=${selectedTicker}&strike_band_pct=0.2&expiries=8&combine_cp=true`;
            
            console.log('Fetching OI change data from:', url);
            const response = await fetch(url);
            
            if (!response.ok) {
                // Try to get the actual error message from the response
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
        const { oiChangeData } = this.state;
        
        if (!oiChangeData || !oiChangeData.matrix || !oiChangeData.expiries || !oiChangeData.strikes) {
            return;
        }
        
        // Check if Plotly is available
        if (typeof Plotly === 'undefined') {
            console.warn('Plotly is not available. Waiting...');
            setTimeout(() => this.renderHeatmap(), 100);
            return;
        }
        
        const matrix = oiChangeData.matrix;
        const expiries = oiChangeData.expiries;
        const strikes = oiChangeData.strikes;
        
        // Format expiry dates for display (e.g., "2024-11-09" -> "11-09")
        const formattedExpiries = expiries.map(exp => {
            const date = new Date(exp);
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${month}-${day}`;
        });
        
        // Format strikes for display
        const formattedStrikes = strikes.map(s => String(s));
        
        // Find min and max values for color scale
        const flatMatrix = matrix.flat();
        const minValue = Math.min(...flatMatrix);
        const maxValue = Math.max(...flatMatrix);
        
        // Create heatmap data
        const heatmapData = [{
            z: matrix,
            x: formattedStrikes,
            y: formattedExpiries,
            type: 'heatmap',
            colorscale: [
                [0, 'rgb(75, 0, 130)'],      // Dark purple for negative/low values
                [0.33, 'rgb(25, 25, 112)'],  // Midnight blue
                [0.5, 'rgb(0, 128, 128)'],  // Teal
                [0.66, 'rgb(144, 238, 144)'], // Light green
                [0.83, 'rgb(255, 255, 0)'],  // Yellow
                [1, 'rgb(255, 215, 0)']      // Gold for high positive values
            ],
            colorbar: {
                title: {
                    text: 'Δ OI (contracts)',
                    font: { size: 12 }
                },
                len: 0.8
            },
            hovertemplate: '<b>Expiry:</b> %{y}<br><b>Strike:</b> %{x}<br><b>Δ OI:</b> %{z}<extra></extra>',
            text: matrix.map(row => row.map(val => val.toString())),
            texttemplate: '%{text}',
            textfont: { size: 10 },
            showscale: true
        }];
        
        const layout = {
            title: {
                text: 'Open Interest Change',
                font: { size: 18, weight: 'bold' }
            },
            xaxis: {
                title: 'Strike',
                side: 'bottom',
                type: 'category',
                automargin: true
            },
            yaxis: {
                title: 'Expiry',
                type: 'category',
                automargin: true
            },
            height: 500,
            margin: { l: 80, r: 50, t: 60, b: 80 },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white'
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['select2d', 'lasso2d']
        };
        
        // Render the heatmap
        Plotly.newPlot('oi-heatmap-chart', heatmapData, layout, config);
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
                
                {/* Charts Grid - 3 per row, 9 total */}
                <div className="row g-4">
                    {/* Row 1 */}
                    <div className="col-md-4">
                        <div className="card shadow-sm">
                            <div className="card-body">
                                <div id="oi-heatmap-chart" style={{ minHeight: '500px' }}></div>
                            </div>
                        </div>
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 2', 'chart-2')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 3', 'chart-3')}
                    </div>
                    
                    {/* Row 2 */}
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 4', 'chart-4')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 5', 'chart-5')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 6', 'chart-6')}
                    </div>
                    
                    {/* Row 3 */}
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 7', 'chart-7')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 8', 'chart-8')}
                    </div>
                    <div className="col-md-4">
                        {this.renderPlaceholderChart('Chart 9', 'chart-9')}
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

