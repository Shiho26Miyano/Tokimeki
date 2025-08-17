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

        // Start AI analysis preparation in parallel (using estimated data)
        const aiPromise = prepareAIAnalysis(weeklyAmount, startDate, endDate);

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
        
        // Now generate AI analysis with real data (non-blocking)
        console.log('Starting AI analysis with real data...');
        generateAIStrategyAnalysis(data);
        
        // Wait for AI analysis to complete in background (non-blocking)
        aiPromise.then(aiResult => {
            if (aiResult) {
                console.log('Background AI analysis completed');
            }
        }).catch(aiError => {
            console.log('Background AI analysis completed separately');
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

// AI Strategy Analysis Functions
async function generateAIStrategyAnalysis(data) {
    try {
        console.log('Generating AI strategy analysis with data:', data);
        
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
            combinedAnalysis.innerHTML = '<div class="d-flex align-items-center gap-2"><div class="spinner-border spinner-border-sm text-primary"></div> AI analyzing your strategy and performance...</div>';
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
        
        // Generate AI analysis using Python backend
        const analysisResult = await callPythonBackendAnalysis(analysisData);
        
        // Update UI with AI analysis (render markdown)
        if (combinedAnalysis && analysisResult) {
            // Convert markdown to HTML if showdown is available
            if (typeof showdown !== 'undefined') {
                const converter = new showdown.Converter();
                const html = converter.makeHtml(analysisResult);
                combinedAnalysis.innerHTML = html;
            } else {
                // Fallback to plain text if showdown not available
                combinedAnalysis.innerHTML = analysisResult.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            }
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
        console.log('Calling Python backend for AI analysis...');
        
        // Call Python backend analysis endpoint
        const response = await fetch('/api/v1/mnq/generate-analysis', {
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

// Prepare AI analysis in parallel with MNQ calculation
async function prepareAIAnalysis(weeklyAmount, startDate, endDate) {
    try {
        console.log('Preparing AI analysis in parallel...');
        
        // Estimate some data for early AI preparation
        const estimatedData = {
            weekly_amount: weeklyAmount,
            start_date: startDate,
            end_date: endDate,
            total_weeks: Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24 * 7)),
            // Use conservative estimates for AI preparation
            estimated_total_invested: weeklyAmount * 52, // Assume 52 weeks
            estimated_current_value: weeklyAmount * 52 * 0.95, // Assume slight loss
            estimated_return: -5.0, // Conservative estimate
            estimated_volatility: 15.0, // Typical market volatility
            estimated_max_drawdown: 20.0 // Conservative drawdown estimate
        };
        
        // Generate preliminary analysis
        const preliminaryAnalysis = generateStructuredAnalysis(estimatedData);
        
        if (preliminaryAnalysis) {
            console.log('Preliminary analysis prepared');
            return preliminaryAnalysis;
        }
        
        return null;
    } catch (error) {
        console.log('Preliminary AI preparation failed (non-critical):', error);
        return null;
    }
}

// Manual refresh function for strategy analysis
function refreshAIAnalysis() {
    const calculateBtn = document.getElementById('mnq-calculate-btn');
    if (calculateBtn && !calculateBtn.disabled) {
        calculateBtn.click(); // This will trigger a new calculation and AI analysis
    }
}
