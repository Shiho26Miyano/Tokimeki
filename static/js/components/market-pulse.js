/**
 * Market Pulse Dashboard Component - Dual Signal Comparison
 * 
 * Displays Compute Agent vs Learning Agent Signal comparison for 10 stocks
 */
class MarketPulseDashboard {
    constructor() {
        this.apiBase = '/api/v1/market-pulse';
        this.updateInterval = null;
        
        this.init();
    }

    async init() {
        console.log('Initializing Market Pulse Dashboard...');
        this.setupEventListeners();
        await this.loadData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        const refreshBtn = document.getElementById('market-pulse-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData());
        }
    }

    async loadData() {
        try {
            await this.loadDualSignal();
        } catch (error) {
            console.error('Error loading market pulse data:', error);
            this.showError('Failed to load market pulse data');
        }
    }
    
    async loadDualSignal() {
        try {
            const response = await fetch(`${this.apiBase}/dual-signal`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Dual signal API response:', data);
            
            if (data.success && data.stocks && data.stocks.length > 0) {
                // 检查数据状态
                const dataStatus = data.data_status || {};
                const hasComputeData = dataStatus.compute_agent_available;
                const hasLearningData = dataStatus.learning_agent_available;
                
                if (!hasComputeData && !hasLearningData) {
                    this.showDualSignalError(
                        '⚠️ 数据未就绪: Compute Agent 和 Learning Agent 都还没有运行。' +
                        '<br>💡 请检查 Lambda 函数是否已部署并正常运行。'
                    );
                } else if (!hasComputeData) {
                    this.showDualSignalError(
                        '⚠️ Compute Agent 数据未就绪: 请检查 Compute Agent Lambda 是否正常运行。'
                    );
                } else if (!hasLearningData) {
                    // Learning Agent 每小时运行一次，这是正常的
                    this.renderDualSignalTable(data.stocks);
                    this.showDualSignalWarning(
                        'ℹ️ Learning Agent 数据尚未生成（每小时运行一次）。' +
                        '<br>Compute Agent 数据已显示。'
                    );
                } else {
                    this.renderDualSignalTable(data.stocks);
                }
            } else {
                this.showDualSignalError('No data available');
            }
        } catch (error) {
            console.error('Error loading dual signal data:', error);
            this.showDualSignalError(`Error: ${error.message}`);
        }
    }
    
    renderDualSignalTable(stocks) {
        const tbody = document.getElementById('dual-signal-table-body');
        if (!tbody) return;
        
        if (stocks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No data available</td></tr>';
            return;
        }
        
        tbody.innerHTML = stocks.map(stock => {
            const compute = stock.compute_agent || {};
            const learning = stock.learning_agent || {};
            const diff = stock.difference || {};
            const convergence = stock.convergence || {};
            
            const signalDiff = diff.signal_diff || 0;
            const r2Score = learning.r2_score || 0;
            const mae = learning.mae || 0;
            const iterations = learning.training_iterations || 0;
            const converged = learning.converged || false;
            const convergenceProgress = convergence.progress || 0;
            const convergenceStatus = convergence.status || '⏳';
            
            // Color coding for R²
            let r2Class = '';
            if (r2Score >= 0.9) r2Class = 'bg-success bg-opacity-25';
            else if (r2Score >= 0.7) r2Class = 'bg-warning bg-opacity-25';
            else r2Class = 'bg-danger bg-opacity-25';
            
            // Color coding for convergence
            const convergedClass = converged ? 'text-success fw-bold' : 'text-warning';
            
            return `
                <tr>
                    <td class="text-center fw-bold">${stock.ticker}</td>
                    <td class="text-end">${(compute.signal || 0).toFixed(4)}</td>
                    <td class="text-end">${(learning.signal || 0).toFixed(4)}</td>
                    <td class="text-end">${signalDiff >= 0 ? '+' : ''}${signalDiff.toFixed(4)}</td>
                    <td class="text-end ${r2Class}">${(r2Score * 100).toFixed(1)}%</td>
                    <td class="text-end">${mae.toFixed(4)}</td>
                    <td class="text-center">${iterations}</td>
                    <td class="text-center ${convergedClass}">${convergenceStatus}</td>
                    <td class="text-center">
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar ${converged ? 'bg-success' : 'bg-warning'}" 
                                 role="progressbar" 
                                 style="width: ${convergenceProgress}%"
                                 aria-valuenow="${convergenceProgress}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                                ${convergenceProgress}%
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    showDualSignalError(message = 'Error loading data') {
        const tbody = document.getElementById('dual-signal-table-body');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">${message}</td></tr>`;
        }
    }
    
    showDualSignalWarning(message) {
        // 在表格上方显示警告（如果存在警告区域）
        const warningElement = document.getElementById('dual-signal-warning');
        if (warningElement) {
            warningElement.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
        } else {
            console.warn(message);
        }
    }

    startAutoRefresh() {
        this.updateInterval = setInterval(() => {
            this.loadData();
        }, 30000); // 30 seconds
    }

    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    showError(message) {
        console.error(message);
    }

    destroy() {
        this.stopAutoRefresh();
    }
}

// Initialize Market Pulse Dashboard
let marketPulseDashboardInstance = null;

function initMarketPulseDashboard() {
    if (!marketPulseDashboardInstance) {
        const contentElement = document.getElementById('market-pulse-content');
        
        if (contentElement) {
            const tabElement = document.getElementById('market-pulse-tab');
            const isActive = tabElement && tabElement.classList.contains('active');
            
            if (isActive) {
                console.log('Initializing Market Pulse Dashboard (default tab)...');
                marketPulseDashboardInstance = new MarketPulseDashboard();
            } else {
                tabElement.addEventListener('shown.bs.tab', function() {
                    if (!marketPulseDashboardInstance) {
                        console.log('Initializing Market Pulse Dashboard...');
                        marketPulseDashboardInstance = new MarketPulseDashboard();
                    }
                }, { once: true });
            }
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMarketPulseDashboard);
} else {
    initMarketPulseDashboard();
}
