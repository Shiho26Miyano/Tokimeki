// MNQ Investment Dashboard - Separate JavaScript file
// This file is completely independent and won't interfere with existing functionality

console.log('MNQ Dashboard JavaScript loaded');

// Global variables for MNQ dashboard
let mnqData = null;

// Display current date range information
function updateDateRangeInfo() {
    const startDateInput = document.getElementById('mnq-start-date');
    const endDateInput = document.getElementById('mnq-end-date');
    
    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        const start = new Date(startDateInput.value);
        const end = new Date(endDateInput.value);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const diffYears = (diffDays / 365.25).toFixed(1);
        
        // Find or create the date range info element
        let dateRangeInfo = document.getElementById('mnq-date-range-info');
        if (!dateRangeInfo) {
            dateRangeInfo = document.createElement('div');
            dateRangeInfo.id = 'mnq-date-range-info';
            dateRangeInfo.className = 'mt-2';
            dateRangeInfo.style.fontSize = '0.875rem';
            
            // Insert after the date inputs
            const dateInputsRow = startDateInput.closest('.row');
            if (dateInputsRow) {
                dateInputsRow.parentNode.insertBefore(dateRangeInfo, dateInputsRow.nextSibling);
            }
        }
        
        // Update the info text
        const remainingDays = (365 * 5) - diffDays;
        dateRangeInfo.innerHTML = `
            <small class="text-info">
                <i class="fas fa-calendar-alt"></i> 
                Current range: ${diffDays} days (${diffYears} years). 
                ${remainingDays > 0 ? `You can extend by up to ${remainingDays} more days.` : 'Maximum 5-year range reached.'}
            </small>
        `;
    }
}

// Validate date range (max 5 years)
function validateDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const maxDays = 365 * 5; // 5 years maximum
    
    if (diffDays > maxDays) {
        return {
            valid: false,
            message: `Date range cannot exceed 5 years (${maxDays} days). Current selection: ${diffDays} days.`
        };
    }
    
    if (start >= end) {
        return {
            valid: false,
            message: 'Start date must be before end date.'
        };
    }
    
    return { valid: true };
}

// Initialize MNQ dashboard
function initializeMNQDashboard() {
    console.log('Initializing MNQ dashboard...');
    
    try {
        // Set default dates - 1 year ago to today
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        const startDateInput = document.getElementById('mnq-start-date');
        const endDateInput = document.getElementById('mnq-end-date');
        const calculateBtn = document.getElementById('mnq-calculate-btn');
        const resetBtn = document.getElementById('mnq-reset-btn');
        
        if (startDateInput && endDateInput) {
            // Set default dates (1 year back to today)
            startDateInput.value = oneYearAgo.toISOString().split('T')[0];
            endDateInput.value = today.toISOString().split('T')[0];
            console.log('Default dates set to 1 year ago');
            
            // Update date range info display
            updateDateRangeInfo();
            
            // Fetch the maximum available date range from backend to set constraints
            fetchMaxAvailableDateRange();
            
            // Add event listeners for date changes
            startDateInput.addEventListener('change', function() {
                console.log('Start date changed to:', this.value);
                const endDate = endDateInput.value;
                
                if (endDate) {
                    const validation = validateDateRange(this.value, endDate);
                    if (!validation.valid) {
                        showMNQError(validation.message);
                        return;
                    }
                    hideMNQError();
                    updateDateRangeInfo();
                    // Auto-calculate if both dates are set
                    showAutoCalculationIndicator();
                    setTimeout(() => calculateMNQInvestment(), 100);
                }
            });
            
            endDateInput.addEventListener('change', function() {
                console.log('End date changed to:', this.value);
                const startDate = startDateInput.value;
                
                if (startDate) {
                    const validation = validateDateRange(startDate, this.value);
                    if (!validation.valid) {
                        showMNQError(validation.message);
                        return;
                    }
                    hideMNQError();
                    updateDateRangeInfo();
                    // Auto-calculate if both dates are set
                    showAutoCalculationIndicator();
                    setTimeout(() => calculateMNQInvestment(), 100);
                }
            });
            
            // Add event listeners for weekly amount changes
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
        
        // Validate date range (max 5 years)
        const validation = validateDateRange(startDate, endDate);
        if (!validation.valid) {
            throw new Error(validation.message);
        }
        
        // Start MNQ calculation and AI preparation in parallel
        console.log('Starting parallel processing: MNQ calculation + AI preparation');
        
        // Start MNQ calculation
        const mnqPromise = fetch('/api/v1/mnq/calculate', {
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

        // Start diagnostic analysis preparation in parallel (using estimated data)
        const aiPromise = prepareDiagnosticAnalysis(weeklyAmount, startDate, endDate);

        // Wait for MNQ results first (display immediately)
        console.log('Waiting for MNQ calculation results...');
        const response = await mnqPromise;
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to calculate MNQ performance');
        }
        
        const data = await response.json();
        mnqData = data;
        
        // Display MNQ results immediately
        console.log('MNQ results received, updating UI immediately');
        updateMNQPerformanceCards(data);
        updateMNQMetrics(data);
        updateMNQWeeklyTable(data);
        showMNQResults(true);
        
        // Fetch and display optimal amounts
        console.log('Fetching optimal amounts...');
        
        // Show progress indicator for optimal amounts
        const topByPercentage = document.getElementById('top-by-percentage');
        const topByAmount = document.getElementById('top-by-amount');
        
        if (topByPercentage) {
            topByPercentage.innerHTML = '<div class="list-group-item text-center text-info py-3">🔄 Calculating optimal amounts with $10 step size...</div>';
        }
        if (topByAmount) {
            topByAmount.innerHTML = '<div class="list-group-item text-center text-info py-3">🔄 Calculating optimal amounts with $10 step size...</div>';
        }
        
        try {
            const optimalResponse = await fetch('/api/v1/mnq/optimal-amounts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate,
                    min_amount: 100,
                    max_amount: 10000,
                    step_size: 10,
                    top_n: 5,
                    sort_key: "total_return",
                    descending: true
                }),
                signal: AbortSignal.timeout(300000) // 5 minute timeout
            });
            
            console.log('Optimal response status:', optimalResponse.status);
            console.log('Optimal response headers:', optimalResponse.headers);
            
            if (optimalResponse.ok) {
                const optimalData = await optimalResponse.json();
                console.log('Optimal amounts received:', optimalData);
                console.log('Data type:', typeof optimalData);
                console.log('Data keys:', Object.keys(optimalData));
                console.log('Success flag:', optimalData.success);
                console.log('Top by percentage:', optimalData.top_by_percentage);
                console.log('Top by profit:', optimalData.top_by_profit);
                
                if (optimalData.success && (optimalData.top_by_percentage || optimalData.top_by_profit)) {
                    updateOptimalAmounts(optimalData);
                } else {
                    console.error('Optimal data missing required fields:', optimalData);
                    // Show error in UI
                    const topByPercentage = document.getElementById('top-by-percentage');
                    const topByAmount = document.getElementById('top-by-amount');
                    
                    if (topByPercentage) {
                        topByPercentage.innerHTML = '<div class="list-group-item text-center text-danger py-3">Error: No optimal data received</div>';
                    }
                    if (topByAmount) {
                        topByAmount.innerHTML = '<div class="list-group-item text-center text-danger py-3">Error: No optimal data received</div>';
                    }
                }
            } else {
                const errorText = await optimalResponse.text();
                console.error('Failed to fetch optimal amounts. Status:', optimalResponse.status, 'Response:', errorText);
                
                // Show error in UI with details
                const topByPercentage = document.getElementById('top-by-percentage');
                const topByAmount = document.getElementById('top-by-amount');
                
                let errorDisplay = `API Error: ${optimalResponse.status}`;
                try {
                    const errorData = JSON.parse(errorText);
                    if (errorData.detail) {
                        errorDisplay += ` - ${errorData.detail}`;
                    }
                } catch (e) {
                    if (errorText) {
                        errorDisplay += ` - ${errorText}`;
                    }
                }
                
                if (topByPercentage) {
                    topByPercentage.innerHTML = `<div class="list-group-item text-center text-danger py-3">${errorDisplay}</div>`;
                }
                if (topByAmount) {
                    topByAmount.innerHTML = `<div class="list-group-item text-center text-danger py-3">${errorDisplay}</div>`;
                }
            }
        } catch (optimalError) {
            console.error('Error fetching optimal amounts:', optimalError);
            
            // Show error in UI
            const topByPercentage = document.getElementById('top-by-percentage');
            const topByAmount = document.getElementById('top-by-amount');
            
            let errorMessage = 'Network Error: Failed to fetch';
            if (optimalError.name === 'TimeoutError') {
                errorMessage = 'Calculation Timeout: Please try with a larger step size';
            } else if (optimalError.name === 'AbortError') {
                errorMessage = 'Request Aborted: Please try again';
            }
            
            if (topByPercentage) {
                topByPercentage.innerHTML = `<div class="list-group-item text-center text-danger py-3">${errorMessage}</div>`;
            }
            if (topByAmount) {
                topByAmount.innerHTML = `<div class="list-group-item text-center text-danger py-3">${errorMessage}</div>`;
            }
        }
        
        // Now generate diagnostic analysis with real data (non-blocking)
        console.log('Starting diagnostic analysis with real data...');
        generateDiagnosticEventAnalysis(data);
        
        // Wait for diagnostic analysis to complete in background (non-blocking)
        aiPromise.then(aiResult => {
            if (aiResult) {
                console.log('Background diagnostic analysis completed');
            }
        }).catch(aiError => {
            console.log('Background diagnostic analysis completed separately');
        });
        
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
    
    // Reset to default dates (1 year ago to today)
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    const startDateInput = document.getElementById('mnq-start-date');
    const endDateInput = document.getElementById('mnq-end-date');
    
    if (startDateInput && endDateInput) {
        startDateInput.value = oneYearAgo.toISOString().split('T')[0];
        endDateInput.value = today.toISOString().split('T')[0];
        console.log('MNQ defaults reset to 1 year ago');
        
        // Update date range info display
        updateDateRangeInfo();
    }
    
    // Hide results
    showMNQResults(false);
    
    console.log('MNQ defaults reset to 1 year ago');
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
            
            // Update min/max attributes for date inputs to set constraints
            const startDateInput = document.getElementById('mnq-start-date');
            const endDateInput = document.getElementById('mnq-end-date');
            
            if (startDateInput && endDateInput) {
                // Set constraints without overwriting current values
                startDateInput.min = dateRange.earliest_available;
                startDateInput.max = dateRange.latest_available;
                endDateInput.min = dateRange.earliest_available;
                endDateInput.max = dateRange.latest_available;
                
                console.log(`Date constraints set: ${dateRange.earliest_available} to ${dateRange.latest_available}`);
                console.log(`Maximum range: ${dateRange.max_range_weeks} weeks (${dateRange.max_range_days} days)`);
                
                // Auto-calculate with the current date range (preserving user's default choice)
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
        // Keep default dates (1 year back to today) if backend fails
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

// Diagnostic Event Analysis Functions
async function generateDiagnosticEventAnalysis(data) {
    try {
        console.log('Generating diagnostic event analysis with data:', data);
        
        // Only proceed if we have complete data
        if (!data || !data.total_invested || !data.performance_metrics) {
            console.log('Incomplete data, skipping AI analysis');
            const combinedAnalysis = document.getElementById('ai-combined-analysis');
            if (combinedAnalysis) {
                combinedAnalysis.innerHTML = 'Waiting for complete calculation results...';
            }
            return;
        }
        
        // Start timer and show loading state
        const startTime = Date.now();
        const timerElement = document.getElementById('ai-analysis-timer');
        const spinnerElement = document.getElementById('ai-analysis-spinner');
        const refreshBtn = document.getElementById('ai-refresh-btn');
        
        // Show spinner and disable refresh button
        if (spinnerElement) spinnerElement.style.display = 'inline-block';
        if (refreshBtn) refreshBtn.disabled = true;
        
        const timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            if (timerElement) {
                timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
        
        // Show loading state
        const combinedAnalysis = document.getElementById('ai-combined-analysis');
        if (combinedAnalysis) {
            combinedAnalysis.innerHTML = '<div class="d-flex align-items-center gap-2"><div class="spinner-border spinner-border-sm text-primary"></div> Analyzing market events and identifying worst week...</div>';
        }
        
        // Prepare data for AI analysis using actual calculation results
        const analysisData = {
            weekly_amount: parseFloat(document.getElementById('mnq-weekly-amount').value) || 1000,
            start_date: document.getElementById('mnq-start-date').value,
            end_date: document.getElementById('mnq-end-date').value,
            total_invested: data.total_invested || 0,
            current_value: data.current_value || 0,
            total_return: data.total_return || 0,
            cagr: data.performance_metrics?.cagr || 0,
            volatility: data.performance_metrics?.volatility || 0,
            sharpe_ratio: data.performance_metrics?.sharpe_ratio || 0,
            max_drawdown: data.performance_metrics?.max_drawdown || 0,
            win_rate: data.performance_metrics?.win_rate || 0,
            profit_factor: data.performance_metrics?.profit_factor || 0,
            total_contracts: data.total_contracts || 0,
            total_weeks: data.total_weeks || 0,
            weekly_breakdown: data.weekly_breakdown || []
        };
        
        console.log('AI Analysis Data:', analysisData);
        
        // Generate diagnostic analysis using Python backend
        const analysisResult = await callPythonBackendAnalysis(analysisData);
        
        // Update UI with diagnostic analysis (display HTML directly)
        if (combinedAnalysis && analysisResult) {
            // Display HTML content directly since we're now returning HTML
            combinedAnalysis.innerHTML = analysisResult;
        }
        
        // Stop timer and hide loading state
        clearInterval(timerInterval);
        const totalTime = Math.floor((Date.now() - startTime) / 1000);
        const finalMinutes = Math.floor(totalTime / 60);
        const finalSeconds = totalTime % 60;
        if (timerElement) {
            timerElement.textContent = `${finalMinutes.toString().padStart(2, '0')}:${finalSeconds.toString().padStart(2, '0')}`;
        }
        
        // Hide spinner and enable refresh button
        if (spinnerElement) spinnerElement.style.display = 'none';
        if (refreshBtn) refreshBtn.disabled = false;
        
        console.log('AI analysis completed');
        
    } catch (error) {
        console.error('Error generating AI analysis:', error);
        
        // Fallback to static analysis if AI fails
        const combinedAnalysis = document.getElementById('ai-combined-analysis');
        if (combinedAnalysis) {
            combinedAnalysis.innerHTML = 'AI analysis unavailable. Your DCA strategy shows typical futures trading patterns with margin management and risk controls. Review the performance metrics above for insights.';
        }
        
        // Reset timer on error
        const timerElement = document.getElementById('ai-analysis-timer');
        if (timerElement) {
            timerElement.textContent = '00:00';
        }
    }
}

async function callPythonBackendAnalysis(analysisData) {
    try {
        console.log('Calling Python backend for diagnostic analysis...');
        
        // Call Python backend diagnostic analysis endpoint
        const response = await fetch('/api/v1/mnq/generate-diagnostic-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                weekly_amount: analysisData.weekly_amount,
                start_date: analysisData.start_date,
                end_date: analysisData.end_date,
                total_weeks: analysisData.total_weeks,
                total_invested: analysisData.total_invested,
                current_value: analysisData.current_value,
                total_return: analysisData.total_return,
                cagr: analysisData.cagr,
                volatility: analysisData.volatility,
                sharpe_ratio: analysisData.sharpe_ratio,
                max_drawdown: analysisData.max_drawdown,
                win_rate: analysisData.win_rate,
                profit_factor: analysisData.profit_factor,
                total_contracts: analysisData.total_contracts
            })
        });
        
        if (!response.ok) {
            throw new Error(`Python backend error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Python backend analysis response:', data);
        
        if (data.success) {
            return data.analysis;
        } else {
            // Use fallback analysis if AI failed
            return data.analysis || 'Analysis generation failed. Please review the performance metrics above for insights.';
        }
        
    } catch (error) {
        console.error('Python backend analysis failed:', error);
        // Fallback to local analysis if backend fails
        return generateStructuredAnalysis(analysisData);
    }
}

function generateStructuredAnalysis(data) {
    try {
        console.log('Generating analysis for data:', data);
        
        // Extract data with fallbacks
        const weeklyAmount = data.weekly_amount || 1000;
        const totalWeeks = data.total_weeks || 0;
        const totalInvested = data.total_invested || 0;
        const currentValue = data.current_value || 0;
        const totalReturn = data.total_return || 0;
        const cagr = data.cagr || 0;
        const volatility = data.volatility || 0;
        const sharpeRatio = data.sharpe_ratio || 0;
        const maxDrawdown = data.max_drawdown || 0;
        const winRate = data.win_rate || 0;
        const profitFactor = data.profit_factor || 0;
        const totalContracts = data.total_contracts || 0;
        
        // Calculate time period
        const startDate = new Date(data.start_date || new Date().toISOString().split('T')[0]);
        const endDate = new Date(data.end_date || new Date().toISOString().split('T')[0]);
        const days = (endDate - startDate) / (1000 * 60 * 60 * 24);
        const years = days / 365.25;
        
        // Executive Summary (≤120 words)
        const summary = `**Executive Summary**\n` +
            `Analysis of weekly $${weeklyAmount.toLocaleString()} investment over ${totalWeeks} weeks (${years.toFixed(1)} years). ` +
            `Total invested: $${totalInvested.toLocaleString()}, Current value: $${currentValue.toLocaleString()}, ` +
            `Return: ${totalReturn.toFixed(2)}%, CAGR: ${cagr.toFixed(2)}%. ` +
            `Strategy uses Dollar-Cost Averaging (DCA) into MNQ futures with controlled position sizing and risk management.`;
        
        // Key Metrics Table
        const metrics = `\n**Key Performance Metrics**\n` +
            `| Metric | Value |\n` +
            `|--------|-------|\n` +
            `| Total Return | ${totalReturn.toFixed(2)}% |\n` +
            `| CAGR | ${cagr.toFixed(2)}% |\n` +
            `| Volatility | ${volatility.toFixed(2)}% |\n` +
            `| Sharpe Ratio | ${sharpeRatio.toFixed(2)} |\n` +
            `| Max Drawdown | ${maxDrawdown.toFixed(2)}% |\n` +
            `| Win Rate | ${winRate.toFixed(2)}% |\n` +
            `| Profit Factor | ${profitFactor.toFixed(2)} |\n` +
            `| Total Contracts | ${totalContracts.toFixed(1)} |`;
        
        // Strategy Insights
        const insights = `\n**Strategy Insights**\n` +
            `• **DCA Effectiveness**: ${totalReturn > 0 ? 'Positive' : 'Negative'} returns over ${totalWeeks} weeks\n` +
            `• **Risk Management**: ${maxDrawdown > 25 ? 'High' : maxDrawdown > 10 ? 'Moderate' : 'Low'} volatility with ${maxDrawdown.toFixed(2)}% max drawdown\n` +
            `• **Contract Accumulation**: ${totalContracts.toFixed(1)} contracts accumulated through systematic weekly investments\n` +
            `• **Performance Drivers**: ${totalReturn > 0 ? 'Market appreciation and timing' : 'Market decline and volatility'} impacted overall returns`;
        
        // Action Items
        const action = `\n**Action**\n` +
            `• **Test Different Amounts**: Use the "Find Optimal Amounts" feature to discover the best weekly investment amounts\n` +
            `• **Compare Time Periods**: Analyze performance across different market cycles and volatility periods`;
        
        // Risk & Method
        const risk = `\n**Risk & Method**\n` +
            `• **Leverage Risk**: Futures trading involves significant leverage; max drawdowns can exceed 50%\n` +
            `• **Backtest Assumptions**: Results based on historical data; past performance doesn't guarantee future results`;
        
        // Metrics Footnote
        const footnote = `\n**Metrics Footnote**\n` +
            `Sharpe ratio calculated from weekly time-weighted returns, annualized by √52. ` +
            `Maximum drawdown measured on equity path. Returns calculated as percentage of total contributed capital.`;
        
        return summary + metrics + insights + action + risk + footnote;
        
    } catch (error) {
        console.error('Error in generateStructuredAnalysis:', error);
        return `**Analysis Generation Error**\nUnable to generate analysis due to: ${error.message}\n\nPlease review the performance metrics above for insights.`;
    }
}

// Prepare diagnostic analysis in parallel with MNQ calculation
async function prepareDiagnosticAnalysis(weeklyAmount, startDate, endDate) {
    try {
        console.log('Preparing diagnostic analysis in parallel...');
        
        // Estimate some data for early diagnostic preparation
        const estimatedData = {
            weekly_amount: weeklyAmount,
            start_date: startDate,
            end_date: endDate,
            total_weeks: Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24 * 7)),
            // Use conservative estimates for diagnostic preparation
            estimated_total_invested: weeklyAmount * 52, // Assume 52 weeks
            estimated_current_value: weeklyAmount * 52 * 0.95, // Assume slight loss
            estimated_return: -5.0, // Conservative estimate
            estimated_volatility: 15.0, // Typical market volatility
            estimated_max_drawdown: 20.0 // Conservative drawdown estimate
        };
        
        // Generate preliminary analysis
        const preliminaryAnalysis = generateStructuredAnalysis(estimatedData);
        
        if (preliminaryAnalysis) {
            console.log('Preliminary diagnostic analysis prepared');
            return preliminaryAnalysis;
        }
        
        return null;
    } catch (error) {
        console.log('Preliminary diagnostic preparation failed (non-critical):', error);
        return null;
    }
}

// Manual refresh function for diagnostic analysis
function refreshDiagnosticAnalysis() {
    const calculateBtn = document.getElementById('mnq-calculate-btn');
    if (calculateBtn && !calculateBtn.disabled) {
        calculateBtn.click(); // This will trigger a new calculation and diagnostic analysis
    }
}

// Update optimal amounts display
function updateOptimalAmounts(data) {
    console.log('Updating optimal amounts display with data:', data);
    
    // Update left column: By Return %
    const topByPercentage = document.getElementById('top-by-percentage');
    if (topByPercentage && data.top_by_percentage) {
        topByPercentage.innerHTML = '';
        data.top_by_percentage.forEach((item, index) => {
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            listItem.innerHTML = `
                <div>
                    <strong>${index + 1}.</strong> $${item.weekly_amount.toLocaleString()}
                </div>
                <span class="badge bg-primary rounded-pill">${item.total_return.toFixed(2)}%</span>
            `;
            topByPercentage.appendChild(listItem);
        });
    }
    
    // Update right column: By Dollar Profit (best absolute returns)
    const topByAmount = document.getElementById('top-by-amount');
    if (topByAmount && data.top_by_profit) {
        topByAmount.innerHTML = '';
        data.top_by_profit.forEach((item, index) => {
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            listItem.innerHTML = `
                <div>
                    <strong>${index + 1}.</strong> $${item.weekly_amount.toLocaleString()}
                </div>
                <span class="badge bg-success rounded-pill">$${item.dollar_profit.toFixed(2)}</span>
            `;
            topByAmount.appendChild(listItem);
        });
    }
    
    console.log('Optimal amounts display updated');
}