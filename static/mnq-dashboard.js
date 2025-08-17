// MNQ Investment Dashboard - Separate JavaScript file
// This file is completely independent and won't interfere with existing functionality

console.log('MNQ Dashboard JavaScript loaded');

// Global variables for MNQ dashboard
let mnqData = null;

// Initialize MNQ dashboard
function initializeMNQDashboard() {
    console.log('Initializing MNQ dashboard...');
    
    try {
        // Set default dates
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        const startDateInput = document.getElementById('mnq-start-date');
        const endDateInput = document.getElementById('mnq-end-date');
        const calculateBtn = document.getElementById('mnq-calculate-btn');
        const resetBtn = document.getElementById('mnq-reset-btn');
        
                            if (startDateInput && endDateInput) {
                        // First set default dates (1 year back to today)
                        startDateInput.value = oneYearAgo.toISOString().split('T')[0];
                        endDateInput.value = today.toISOString().split('T')[0];
                        console.log('Default dates set');
                        
                        // Then fetch the maximum available date range from backend
                        fetchMaxAvailableDateRange();
                        
                        // Add event listeners for date changes
                        startDateInput.addEventListener('change', function() {
                            console.log('Start date changed to:', this.value);
                            // Auto-calculate if both dates are set
                            if (endDateInput.value) {
                                showAutoCalculationIndicator();
                                setTimeout(() => calculateMNQInvestment(), 100);
                            }
                        });
                        
                        endDateInput.addEventListener('change', function() {
                            console.log('End date changed to:', this.value);
                            // Auto-calculate if both dates are set
                            if (startDateInput.value) {
                                showAutoCalculationIndicator();
                                setTimeout(() => calculateMNQInvestment(), 100);
                            }
                        });
                        
                        // Add event listener for weekly amount changes
                        const weeklyAmountInput = document.getElementById('mnq-weekly-amount');
                        if (weeklyAmountInput) {
                            let calculationTimeout;
                            weeklyAmountInput.addEventListener('input', function() {
                                console.log('Weekly amount changed to:', this.value);
                                // Clear previous timeout to prevent rapid calculations
                                clearTimeout(calculationTimeout);
                                // Auto-calculate if both dates are set (with 500ms delay)
                                if (startDateInput.value && endDateInput.value) {
                                    calculationTimeout = setTimeout(() => {
                                        showAutoCalculationIndicator();
                                        calculateMNQInvestment();
                                    }, 500);
                                }
                            });
                        }
                        
                        console.log('All parameter change listeners added');
                    } else {
                        console.warn('Date inputs not found');
                    }
        
        if (calculateBtn && resetBtn) {
            // Remove existing event listeners to prevent duplicates
            calculateBtn.replaceWith(calculateBtn.cloneNode(true));
            resetBtn.replaceWith(resetBtn.cloneNode(true));
            
            // Get fresh references
            const newCalculateBtn = document.getElementById('mnq-calculate-btn');
            const newResetBtn = document.getElementById('mnq-reset-btn');
            
            // Add event listeners
            newCalculateBtn.addEventListener('click', calculateMNQInvestment);
            newResetBtn.addEventListener('click', resetMNQDefaults);
            
            console.log('Event listeners added');
        } else {
            console.warn('Buttons not found');
        }
        
        console.log('MNQ dashboard initialized successfully');
    } catch (error) {
        console.error('Error initializing MNQ dashboard:', error);
    }
}

// Calculate MNQ investment performance
async function calculateMNQInvestment() {
    console.log('Calculating MNQ investment performance...');
    
    // Show loading state
    showMNQLoading(true);
    hideMNQError();
    
    try {
        // Get parameters
        const weeklyAmount = parseFloat(document.getElementById('mnq-weekly-amount').value);
        const startDate = document.getElementById('mnq-start-date').value;
        const endDate = document.getElementById('mnq-end-date').value;
        
        // Validate inputs
        if (!weeklyAmount || weeklyAmount < 100 || weeklyAmount > 10000) {
            throw new Error('Weekly amount must be between $100 and $10,000');
        }
        if (!startDate || !endDate) {
            throw new Error('Please select both start and end dates');
        }
        if (new Date(startDate) >= new Date(endDate)) {
            throw new Error('Start date must be before end date');
        }
        
        // Make API call
        const response = await fetch('/api/v1/mnq/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                weekly_amount: weeklyAmount,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to calculate MNQ performance');
        }
        
        const data = await response.json();
        mnqData = data;
        
        // Update UI
        updateMNQPerformanceCards(data);
        updateMNQMetrics(data);
        updateMNQWeeklyTable(data);
        
        // Show results
        showMNQResults(true);
        
        console.log('MNQ calculation completed successfully');
        
    } catch (error) {
        console.error('MNQ calculation error:', error);
        showMNQError(error.message);
    } finally {
        showMNQLoading(false);
    }
}

// Update performance summary table
function updateMNQPerformanceCards(data) {
    console.log('Updating performance summary table with data:', data);
    
    // Show the performance summary table
    const performanceTable = document.getElementById('mnq-performance-cards');
    if (performanceTable) {
        performanceTable.style.display = 'block';
    }
    
    // Update summary values
    const totalInvested = document.getElementById('mnq-total-invested');
    const currentValue = document.getElementById('mnq-current-value');
    const totalReturn = document.getElementById('mnq-total-return');
    const cagr = document.getElementById('mnq-cagr');
    
    if (totalInvested) totalInvested.textContent = `$${data.total_invested.toLocaleString()}`;
    if (currentValue) currentValue.textContent = `$${data.current_value.toLocaleString()}`;
    if (totalReturn) totalReturn.textContent = `${data.total_return.toFixed(2)}%`;
    if (cagr) cagr.textContent = `${data.performance_metrics.cagr.toFixed(2)}%`;
    
    console.log('Performance summary table updated');
}

// Update performance metrics in the summary table
function updateMNQMetrics(data) {
    console.log('Updating performance metrics with data:', data);
    
    const metrics = data.performance_metrics;
    
    // Update all metrics in the summary table
    const volatility = document.getElementById('mnq-volatility');
    const maxDrawdown = document.getElementById('mnq-max-drawdown');
    const sharpe = document.getElementById('mnq-sharpe');
    const winRate = document.getElementById('mnq-win-rate');
    const profitFactor = document.getElementById('mnq-profit-factor');
    const totalContracts = document.getElementById('mnq-total-contracts');
    const totalWeeks = document.getElementById('mnq-total-weeks');
    const avgPrice = document.getElementById('mnq-avg-price');
    
    if (volatility) volatility.textContent = `${metrics.volatility.toFixed(2)}%`;
    if (maxDrawdown) maxDrawdown.textContent = `${metrics.max_drawdown.toFixed(2)}%`;
    if (sharpe) sharpe.textContent = metrics.sharpe_ratio.toFixed(2);
    if (winRate) winRate.textContent = `${metrics.win_rate.toFixed(2)}%`;
    if (profitFactor) profitFactor.textContent = metrics.profit_factor.toFixed(2);
    if (totalContracts) totalContracts.textContent = (data.total_contracts || 0).toFixed(4);
    if (totalWeeks) totalWeeks.textContent = data.total_weeks;
    
    // Calculate average price
    if (data.weekly_breakdown && data.weekly_breakdown.length > 0) {
        const totalPrice = data.weekly_breakdown.reduce((sum, week) => sum + week.price, 0);
        const avgPriceValue = totalPrice / data.weekly_breakdown.length;
        if (avgPrice) avgPrice.textContent = `$${avgPriceValue.toFixed(2)}`;
    }
    
    console.log('Performance metrics updated');
}



// Update weekly breakdown table
function updateMNQWeeklyTable(data) {
    const tbody = document.getElementById('mnq-weekly-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!data.weekly_breakdown || data.weekly_breakdown.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">No data available</td></tr>';
        return;
    }
    
    data.weekly_breakdown.forEach(week => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${week.week}</td>
            <td>${week.date}</td>
            <td>$${week.price.toFixed(2)}</td>
            <td>$${week.investment.toLocaleString()}</td>
            <td>${week.contracts_bought}</td>
            <td>${week.total_contracts}</td>
            <td>$${week.total_invested.toLocaleString()}</td>
            <td>$${week.current_value.toLocaleString()}</td>
            <td class="${week.pnl >= 0 ? 'text-success' : 'text-danger'}">$${week.pnl.toLocaleString()}</td>
            <td class="${week.return_pct >= 0 ? 'text-success' : 'text-danger'}">${week.return_pct.toFixed(2)}%</td>
        `;
        tbody.appendChild(row);
    });
}

// Reset MNQ defaults
function resetMNQDefaults() {
    document.getElementById('mnq-weekly-amount').value = 1000;
    
    // Reset to maximum available date range
    fetchMaxAvailableDateRange();
    
    // Hide results
    showMNQResults(false);
    
    console.log('MNQ defaults reset to maximum available range');
}

// Show/hide loading state
function showMNQLoading(show) {
    document.getElementById('mnq-loading').style.display = show ? 'block' : 'none';
}

// Show/hide error message
function showMNQError(message) {
    const errorDiv = document.getElementById('mnq-error');
    const errorMessage = document.getElementById('mnq-error-message');
    
    if (message) {
        errorMessage.textContent = message;
        errorDiv.style.display = 'block';
    } else {
        errorDiv.style.display = 'none';
    }
}

// Hide error message
function hideMNQError() {
    document.getElementById('mnq-error').style.display = 'none';
}

// Fetch maximum available date range from backend
async function fetchMaxAvailableDateRange() {
    try {
        console.log('Fetching maximum available date range...');
        
        const response = await fetch('/api/v1/mnq/date-range');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.success && data.data) {
            const dateRange = data.data;
            console.log('Available date range:', dateRange);
            
            // Update date inputs with maximum available range
            const startDateInput = document.getElementById('mnq-start-date');
            const endDateInput = document.getElementById('mnq-end-date');
            
            if (startDateInput && endDateInput) {
                startDateInput.value = dateRange.earliest_available;
                endDateInput.value = dateRange.latest_available;
                
                // Update min/max attributes for date inputs
                startDateInput.min = dateRange.earliest_available;
                startDateInput.max = dateRange.latest_available;
                endDateInput.min = dateRange.earliest_available;
                endDateInput.max = dateRange.latest_available;
                
                console.log(`Date range updated: ${dateRange.earliest_available} to ${dateRange.latest_available}`);
                console.log(`Maximum range: ${dateRange.max_range_weeks} weeks (${dateRange.max_range_days} days)`);
                
                // Auto-calculate with the new date range
                setTimeout(() => {
                    if (startDateInput.value && endDateInput.value) {
                        showAutoCalculationIndicator();
                        calculateMNQInvestment();
                    }
                }, 500);
            }
        } else {
            console.warn('Failed to get date range data');
        }
    } catch (error) {
        console.error('Error fetching date range:', error);
        // Fall back to default dates (1 year back to today)
        console.log('Using default date range (1 year back to today)');
    }
}

// Show auto-calculation indicator
function showAutoCalculationIndicator() {
    const calculateBtn = document.getElementById('mnq-calculate-btn');
    if (calculateBtn) {
        const originalText = calculateBtn.textContent;
        calculateBtn.textContent = '🔄 Auto-calculating...';
        calculateBtn.disabled = true;
        
        // Reset button text after calculation completes
        setTimeout(() => {
            calculateBtn.textContent = originalText;
            calculateBtn.disabled = false;
        }, 2000);
    }
}

// Show/hide results
function showMNQResults(show) {
    const performanceCards = document.getElementById('mnq-performance-cards');
    if (performanceCards) performanceCards.style.display = show ? 'block' : 'none';
}

// Initialize MNQ dashboard when tab is shown
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up MNQ dashboard...');
    
    // Wait for DOM to be fully ready
    setTimeout(() => {
        const mnqTab = document.getElementById('mnq-dashboard-tab');
        if (mnqTab) {
            mnqTab.addEventListener('shown.bs.tab', function() {
                console.log('MNQ tab shown, initializing dashboard...');
                initializeMNQDashboard();
            });
        } else {
            console.warn('MNQ tab not found');
        }
        
        // Also initialize if MNQ tab is already active
        if (document.getElementById('mnq-dashboard-tab')?.classList.contains('active')) {
            console.log('MNQ tab already active, initializing...');
            initializeMNQDashboard();
        }
    }, 100);
});

console.log('MNQ Dashboard JavaScript setup complete');
