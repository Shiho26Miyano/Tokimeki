console.log('main.js loaded');

// Initialize time range sliders when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing components...');
    
    // Initialize time range sliders
    try {
        console.log('Initializing time range sliders...');
        initTimeRangeSliders();
        console.log('Time range sliders initialized successfully');
    } catch (e) {
        console.error('Error initializing time range sliders:', e);
    }
    
    // Update initial spans showing the date range
    const timeRangeSlider = document.getElementById('time-range-slider');
    const maxChangeTimeRangeSlider = document.getElementById('maxchange-time-range-slider');
    
    if (timeRangeSlider && timeRangeSlider.noUiSlider) {
        const values = timeRangeSlider.noUiSlider.get();
        const startDate = new Date(parseInt(values[0]));
        const endDate = new Date(parseInt(values[1]));
        
        document.getElementById('time-range-start').textContent = 'Start: ' + startDate.toISOString().split('T')[0];
        document.getElementById('time-range-end').textContent = 'End: ' + endDate.toISOString().split('T')[0];
        
        console.log(`Initial stock trends date range: ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}`);
    } else {
        console.warn('Stock trends slider not initialized properly');
    }
    
    if (maxChangeTimeRangeSlider && maxChangeTimeRangeSlider.noUiSlider) {
        const values = maxChangeTimeRangeSlider.noUiSlider.get();
        const startDate = new Date(parseInt(values[0]));
        const endDate = new Date(parseInt(values[1]));
        
        document.getElementById('maxchange-time-range-start').textContent = 'Start: ' + startDate.toISOString().split('T')[0];
        document.getElementById('maxchange-time-range-end').textContent = 'End: ' + endDate.toISOString().split('T')[0];
        
        console.log(`Initial max change date range: ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}`);
    } else {
        console.warn('Max change slider not initialized properly');
    }
    
    // Auto-fetch data when page loads (with a slight delay to ensure everything is initialized)
    setTimeout(() => {
        console.log("Auto-fetching initial stock data...");
        
        // Fetch initial stock trends data with full 3-year range
        fetchStockTrends(true);
    }, 500);
});

// Debounce function to limit how often a function can be called
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Function to initialize time range sliders
function initTimeRangeSliders() {
    // Calculate date ranges
    const today = new Date();
    const threeYearsAgo = new Date();
    threeYearsAgo.setFullYear(today.getFullYear() - 3);
    
    // For initial display, default to past month
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);
    
    // Format dates for display
    const formatDate = date => {
        return date.toISOString().split('T')[0]; // YYYY-MM-DD format
    };
    
    // Create debounced versions of our fetch functions
    const debouncedFetchStockTrends = debounce(fetchStockTrends, 500);
    const debouncedFetchMaxChange = debounce(fetchMaxChange, 500);
    
    // Initialize Stock Trends slider
    const timeRangeSlider = document.getElementById('time-range-slider');
    if (timeRangeSlider) {
        noUiSlider.create(timeRangeSlider, {
            start: [oneMonthAgo.getTime(), today.getTime()], // Default to past month
            connect: true,
            range: {
                'min': threeYearsAgo.getTime(), // Allow selecting up to 3 years
                'max': today.getTime()
            },
            step: 24 * 60 * 60 * 1000, // One day in milliseconds
            tooltips: [
                {
                    to: value => formatDate(new Date(parseInt(value)))
                },
                {
                    to: value => formatDate(new Date(parseInt(value)))
                }
            ]
        });
        
        // Update display spans when slider values change
        timeRangeSlider.noUiSlider.on('update', function(values, handle) {
            const dateStart = new Date(parseInt(values[0]));
            const dateEnd = new Date(parseInt(values[1]));
            
            document.getElementById('time-range-start').textContent = 'Start: ' + formatDate(dateStart);
            document.getElementById('time-range-end').textContent = 'End: ' + formatDate(dateEnd);
            
            // Update chart in real-time during slider movement for ultra-smooth updates
            updateStockTrendsChart(formatDate(dateStart), formatDate(dateEnd));
        });
    }
    
    // Initialize Max Change slider - also default to past month
    const maxChangeTimeRangeSlider = document.getElementById('maxchange-time-range-slider');
    if (maxChangeTimeRangeSlider) {
        noUiSlider.create(maxChangeTimeRangeSlider, {
            start: [oneMonthAgo.getTime(), today.getTime()], // Default to past month
            connect: true,
            range: {
                'min': threeYearsAgo.getTime(), // Allow selecting up to 3 years
                'max': today.getTime()
            },
            step: 24 * 60 * 60 * 1000, // One day in milliseconds
            tooltips: [
                {
                    to: value => formatDate(new Date(parseInt(value)))
                },
                {
                    to: value => formatDate(new Date(parseInt(value)))
                }
            ]
        });
        
        // Update display spans when slider values change
        maxChangeTimeRangeSlider.noUiSlider.on('update', function(values, handle) {
            const dateStart = new Date(parseInt(values[0]));
            const dateEnd = new Date(parseInt(values[1]));
            
            document.getElementById('maxchange-time-range-start').textContent = 'Start: ' + formatDate(dateStart);
            document.getElementById('maxchange-time-range-end').textContent = 'End: ' + formatDate(dateEnd);
        });
        
        // Add a 'change' event handler to fetch new data when slider is moved
        maxChangeTimeRangeSlider.noUiSlider.on('change', function(values, handle) {
            console.log("Max change slider changed, fetching new data...");
            // Call debounced fetchMaxChange to update the results with new date range
            debouncedFetchMaxChange();
        });
    }
}

// Store all fetched stock data globally to avoid repeated server calls
let stockTrendsData = {};

// Modified function to fetch and display stock trends
async function fetchStockTrends(initialLoad = false) {
    document.getElementById('stock-trends-result').innerText = 'Loading...';
    document.getElementById('stockChartMulti').style.display = 'none';
    const select = document.getElementById('stock-select');
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);

    if (selected.length === 0) {
        document.getElementById('stock-trends-result').innerHTML = 'Please select at least one stock to display.';
        return;
    }
    
    // Only get the full date range on initial load (3 years)
    // or when the selected stocks change
    let needToFetchData = initialLoad;
    for (const symbol of selected) {
        if (!stockTrendsData[symbol]) {
            needToFetchData = true;
            break;
        }
    }
    
    // If we need to fetch data, get the full 3 years
    if (needToFetchData) {
        console.log("Fetching full stock data from server...");
        
        // Use max date range for initial data fetch (3 years)
        const today = new Date();
        const threeYearsAgo = new Date();
        threeYearsAgo.setFullYear(today.getFullYear() - 3);
        
        const startDate = threeYearsAgo.toISOString().split('T')[0];
        const endDate = today.toISOString().split('T')[0];
        
        // Build URL with parameters
        let url = '/stocks/history';
        const params = new URLSearchParams();
        if (selected.length > 0) {
            params.append('symbols', selected.join(','));
        }
        params.append('start_date', startDate);
        params.append('end_date', endDate);
        
        // Append parameters to URL
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        console.log(`Fetching full stock data from URL: ${url}`);
        
        try {
            const res = await fetch(url);
            const data = await res.json();
            
            if (data.error) {
                console.error(`Error from server: ${data.error}`);
                document.getElementById('stock-trends-result').innerText = `Error: ${data.error}`;
                return;
            }
            
            console.log(`Received data for ${Object.keys(data).length} stocks`);
            
            // Store data globally
            for (const [name, info] of Object.entries(data)) {
                if (info.dates && info.closes) {
                    stockTrendsData[info.symbol] = {
                        name: name,
                        symbol: info.symbol,
                        dates: info.dates,
                        closes: info.closes
                    };
                }
            }
        } catch (e) {
            document.getElementById('stock-trends-result').innerText = 'Failed to fetch stock trends.';
            return;
        }
    }
    
    // Now filter the data based on the time range slider
    const slider = document.getElementById('time-range-slider');
    let startDate, endDate;
    
    if (slider && slider.noUiSlider) {
        const values = slider.noUiSlider.get();
        startDate = new Date(parseInt(values[0])).toISOString().split('T')[0];
        endDate = new Date(parseInt(values[1])).toISOString().split('T')[0];
        console.log(`Filtering stock data from ${startDate} to ${endDate}`);
    } else {
        console.warn("No slider or noUiSlider found");
        return;
    }
    
    // Filter the data by date range
    let filteredData = {};
    for (const symbol of selected) {
        if (stockTrendsData[symbol]) {
            const stockData = stockTrendsData[symbol];
            const dateRangeIndices = getDateRangeIndices(stockData.dates, startDate, endDate);
            
            if (dateRangeIndices) {
                filteredData[stockData.name] = {
                    symbol: stockData.symbol,
                    dates: stockData.dates.slice(dateRangeIndices.startIdx, dateRangeIndices.endIdx + 1),
                    closes: stockData.closes.slice(dateRangeIndices.startIdx, dateRangeIndices.endIdx + 1)
                };
            }
        }
    }
    
    // Display the filtered data
    displayStockTrendsData(filteredData, startDate, endDate);
}

// Helper function to get array indices for a date range
function getDateRangeIndices(dates, startDate, endDate) {
    if (!dates || dates.length === 0) return null;
    
    let startIdx = 0;
    let endIdx = dates.length - 1;
    
    // Find start index
    for (let i = 0; i < dates.length; i++) {
        if (dates[i] >= startDate) {
            startIdx = i;
            break;
        }
    }
    
    // Find end index
    for (let i = dates.length - 1; i >= 0; i--) {
        if (dates[i] <= endDate) {
            endIdx = i;
            break;
        }
    }
    
    // Make sure we have valid indices
    if (startIdx > endIdx) return null;
    return { startIdx, endIdx };
}

// Function to display the filtered data
function displayStockTrendsData(data, startDate, endDate) {
    // Reset prediction overlays and original data
    if (stockCharts['stockChartMulti']) {
        stockCharts['stockChartMulti'].data.datasets.forEach(ds => {
            if (ds._originalData) delete ds._originalData;
            ds.segment = undefined;
            ds.pointRadius = undefined;
            ds.pointBackgroundColor = undefined;
            ds.pointBorderColor = undefined;
            ds.pointBorderWidth = undefined;
        });
        if (stockCharts['stockChartMulti'].options.plugins &&
            stockCharts['stockChartMulti'].options.plugins.annotation &&
            stockCharts['stockChartMulti'].options.plugins.annotation.annotations) {
            delete stockCharts['stockChartMulti'].options.plugins.annotation.annotations['predictedLabel'];
        }
    }
    let msg = '';
    let chartData = [];
    let chartLabels = [];
    let first = true;
    let statsTable = '<table style="width:100%;margin-top:10px;font-size:0.98rem;text-align:center;border-collapse:collapse;"><tr><th>Stock</th><th>Open</th><th>High</th><th>Low</th><th>Close</th></tr>';
    let summaryMsg = '';
    
    for (const [name, info] of Object.entries(data)) {
        if (info.dates && info.closes && info.closes.length > 0) {
            msg += `<b>${name} (${info.symbol})</b><br>`;
            if (first) {
                chartLabels = info.dates;
                first = false;
            }
            // Calculate stats
            const open = info.closes[0];
            const close = info.closes[info.closes.length-1];
            const high = Math.max(...info.closes);
            const low = Math.min(...info.closes);
            const change = close - open;
            const changePct = (change / open) * 100;
            const color = change >= 0 ? 'green' : 'red';
            summaryMsg += `<div style="margin-bottom:6px;"><b>${name} (${info.symbol})</b>: <span style="color:${color}">${change>=0?'+':''}${change.toFixed(2)} (${changePct>=0?'+':''}${changePct.toFixed(2)}%)</span></div>`;
            statsTable += `<tr><td>${name} (${info.symbol})</td><td>${open.toFixed(2)}</td><td>${high.toFixed(2)}</td><td>${low.toFixed(2)}</td><td>${close.toFixed(2)}</td></tr>`;
            // Color line green/red, area fill, highlight latest point
            chartData.push({
                label: `${name} (${info.symbol})`,
                data: info.closes,
                borderColor: color,
                backgroundColor: color === 'green' ? 'rgba(76,175,80,0.12)' : 'rgba(233,30,99,0.12)',
                fill: true,
                tension: 0.3,
                pointRadius: info.closes.map((v,i)=>i===info.closes.length-1?6:0),
                pointBackgroundColor: info.closes.map((v,i)=>i===info.closes.length-1?color:'rgba(0,0,0,0)'),
                pointBorderColor: info.closes.map((v,i)=>i===info.closes.length-1?color:'rgba(0,0,0,0)'),
                pointBorderWidth: info.closes.map((v,i)=>i===info.closes.length-1?2:0)
            });
        } else {
            msg += `<b>${name} (${info.symbol}):</b> No data available for the selected date range<br>`;
        }
    }
    statsTable += '</table>';
    
    if (chartData.length > 0) {
        const scaleType = document.getElementById('scale-select').value;
        
        // Update chart title to show date range
        const chartTitle = startDate && endDate 
            ? `Stock Price Trend (${startDate} to ${endDate})`
            : 'Stock Price Trend (Past Month)';
            
        renderStockMultiChart('stockChartMulti', chartLabels, chartData, scaleType, chartTitle);
        document.getElementById('stockChartMulti').style.display = 'block';
    } else {
        document.getElementById('stock-trends-result').innerHTML = 'No data available for the selected stocks and date range.';
        return;
    }
    
    document.getElementById('stock-trends-result').innerHTML = summaryMsg + msg + statsTable;
}

function getStockColor(symbol, alpha=1) {
    const colors = {
        'GOOGL': 'rgba(33,150,243,ALPHA)',
        'NVDA': 'rgba(76,175,80,ALPHA)',
        'AAPL': 'rgba(255,193,7,ALPHA)',
        'MSFT': 'rgba(156,39,176,ALPHA)',
        'AMZN': 'rgba(255,87,34,ALPHA)',
        'META': 'rgba(0,188,212,ALPHA)',
        'TSLA': 'rgba(233,30,99,ALPHA)',
        'NFLX': 'rgba(121,85,72,ALPHA)',
        'AMD': 'rgba(205,220,57,ALPHA)',
        'INTC': 'rgba(63,81,181,ALPHA)',
        'BABA': 'rgba(255,152,0,ALPHA)'
    };
    return (colors[symbol] || 'rgba(33,33,33,ALPHA)').replace('ALPHA', alpha);
}
let stockCharts = {};
function renderStockMultiChart(canvasId, labels, datasets, scaleType='linear', chartTitle='') {
    if (stockCharts[canvasId]) {
        stockCharts[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId).getContext('2d');
    // Find high/low points for each dataset
    const annotationPlugins = [];
    let allValues = [];
    datasets.forEach(ds => {
        if (ds.data && ds.data.length > 0) {
            allValues = allValues.concat(ds.data);
            const maxVal = Math.max(...ds.data);
            const minVal = Math.min(...ds.data);
            const maxIdx = ds.data.indexOf(maxVal);
            const minIdx = ds.data.indexOf(minVal);
            // Add point annotation for high
            annotationPlugins.push({
                type: 'point',
                xValue: labels[maxIdx],
                yValue: maxVal,
                backgroundColor: 'red',
                radius: 6,
                borderColor: 'red',
                borderWidth: 2,
                label: {
                    display: true,
                    content: `High: ${maxVal.toFixed(2)}`,
                    position: 'top',
                    color: 'red',
                    font: { weight: 'bold' }
                }
            });
            // Add point annotation for low
            annotationPlugins.push({
                type: 'point',
                xValue: labels[minIdx],
                yValue: minVal,
                backgroundColor: 'blue',
                radius: 6,
                borderColor: 'blue',
                borderWidth: 2,
                label: {
                    display: true,
                    content: `Low: ${minVal.toFixed(2)}`,
                    position: 'bottom',
                    color: 'blue',
                    font: { weight: 'bold' }
                }
            });
        }
    });
    let suggestedMin = undefined, suggestedMax = undefined;
    if (allValues.length > 0) {
        const min = Math.min(...allValues);
        const max = Math.max(...allValues);
        const padding = (max - min) * 0.08;
        suggestedMin = min - padding;
        suggestedMax = max + padding;
    }
    stockCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            animation: 'none',
            plugins: {
                legend: { display: true, position: 'top', labels: { font: { size: 15 } } },
                title: { display: true, text: chartTitle, font: { size: 18 } },
                tooltip: { enabled: true, mode: 'index', intersect: false },
                annotation: {
                    annotations: annotationPlugins
                }
            },
            interaction: { mode: 'nearest', axis: 'x', intersect: false },
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Date', font: { size: 14 } },
                    ticks: {
                        autoSkip: false,
                        maxRotation: 0,
                        minRotation: 0,
                        callback: function(value, index, values) {
                            // Show only first, last, and every 5th date
                            if (index === 0 || index === labels.length - 1 || index % 5 === 0) {
                                return labels[index];
                            }
                            return '';
                        },
                        font: { size: 12 }
                    },
                    grid: { display: true, color: '#eee' }
                },
                y: {
                    beginAtZero: false,
                    type: scaleType,
                    title: { display: true, text: 'Price (USD)', font: { size: 14 } },
                    grid: { display: true, color: '#eee' },
                    ticks: { font: { size: 12 } },
                    suggestedMin: suggestedMin,
                    suggestedMax: suggestedMax
                }
            }
        },
        plugins: [window['ChartAnnotationPlugin']].filter(Boolean)
    });
}
function showStockTrendsSection() {
    document.getElementById('main-sections').style.display = 'none';
    document.getElementById('stock-trends-section').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function showMainSections() {
    document.getElementById('stock-trends-section').style.display = 'none';
    document.getElementById('main-sections').style.display = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
async function fetchMaxChange() {
    document.getElementById('maxchange-result').innerText = 'Loading...';
    const select = document.getElementById('maxchange-stock-select');
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);
    
    // Get date range from slider
    let startDate, endDate;
    const slider = document.getElementById('maxchange-time-range-slider');
    if (slider && slider.noUiSlider) {
        const values = slider.noUiSlider.get();
        startDate = new Date(parseInt(values[0])).toISOString().split('T')[0];
        endDate = new Date(parseInt(values[1])).toISOString().split('T')[0];
        console.log(`Fetching max change data from ${startDate} to ${endDate}`);
    } else {
        console.warn("No max change slider or noUiSlider found");
    }
    
    // Build URL with parameters
    let url = '/stocks/maxchange';
    const params = new URLSearchParams();
    if (selected.length > 0) {
        params.append('symbols', selected.join(','));
    }
    if (startDate) {
        params.append('start_date', startDate);
    }
    if (endDate) {
        params.append('end_date', endDate);
    }
    
    // Append parameters to URL
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    console.log(`Fetching max change data from URL: ${url}`);
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.error) {
            console.error(`Error from server: ${data.error}`);
            document.getElementById('maxchange-result').innerText = `Error: ${data.error}`;
            return;
        }
        
        console.log(`Received data for ${data.length} stocks`);
        
        // Create date range subtitle for the results
        let dateRangeInfo = '';
        if (startDate && endDate) {
            dateRangeInfo = `<div style="margin-bottom:10px;font-style:italic;color:#666;text-align:center;">Date range: ${startDate} to ${endDate}</div>`;
        }
        
        let table = `<table style='width:100%;margin-top:10px;font-size:0.97rem;text-align:center;border-collapse:collapse;'><tr><th>Rank</th><th>Stock</th><th>Max Abs Change</th><th>Start Date</th><th>End Date</th><th>Start Price</th><th>End Price</th></tr>`;
        data.forEach((item, idx) => {
            if (item.max_abs_sum !== undefined) {
                table += `<tr><td>${idx+1}</td><td>${item.name} (${item.symbol})</td><td>${item.max_abs_sum.toFixed(2)}</td><td>${item.start_date}</td><td>${item.end_date}</td><td>${item.start_price.toFixed(2)}</td><td>${item.end_price.toFixed(2)}</td></tr>`;
            } else {
                table += `<tr><td colspan='7'>${item.name} (${item.symbol}): ${item.error}</td></tr>`;
            }
        });
        table += '</table>';
        document.getElementById('maxchange-result').innerHTML = dateRangeInfo + table;
    } catch (e) {
        document.getElementById('maxchange-result').innerText = 'Failed to fetch ranking.';
    }
}
function updateLcInputs() {
    const problem = document.getElementById('lc-problem').value;
    document.getElementById('lc-k-div').style.display = (problem === '188') ? '' : 'none';
    document.getElementById('lc-fee-div').style.display = (problem === '714') ? '' : 'none';
}
let lcCodeLang = 'py';
let lcLastResult = { code: '', cpp_code: '', time_complexity: '', space_complexity: '', explanation: '', result: '' };
function setLcCodeLang(lang) {
    lcCodeLang = lang;
    // Update button styles
    document.getElementById('btn-py').style.background = lang === 'py' ? '#ff69b4' : '#eee';
    document.getElementById('btn-py').style.color = lang === 'py' ? '#fff' : '#333';
    document.getElementById('btn-cpp').style.background = lang === 'cpp' ? '#ff69b4' : '#eee';
    document.getElementById('btn-cpp').style.color = lang === 'cpp' ? '#fff' : '#333';
    // Update code display
    if (lcLastResult.code || lcLastResult.cpp_code) {
        let code = lcCodeLang === 'py' ? lcLastResult.code : lcLastResult.cpp_code;
        document.getElementById('lc-result').innerHTML =
            `<b>Result:</b> ${lcLastResult.result}<br><br>` +
            `<b>${lcCodeLang === 'py' ? 'Python' : 'C++'} Code:</b><br><pre style='background:#f7f7f7;padding:10px;border-radius:6px;overflow-x:auto;'>${code}</pre>` +
            `<b>Time Complexity:</b> ${lcLastResult.time_complexity}<br>` +
            `<b>Space Complexity:</b> ${lcLastResult.space_complexity}<br>` +
            `<b>Explanation:</b> ${lcLastResult.explanation}`;
    }
}
async function solveLcStock() {
    const problem = document.getElementById('lc-problem').value;
    const prices = document.getElementById('lc-prices').value.split(',').map(x => parseFloat(x.trim())).filter(x => !isNaN(x));
    const k = parseInt(document.getElementById('lc-k').value);
    const fee = parseFloat(document.getElementById('lc-fee').value);
    let body = { problem, prices };
    if (problem === '188') body.k = k;
    if (problem === '714') body.fee = fee;
    document.getElementById('lc-result').innerText = 'Testing endpoints...';
    
    // Add timestamp to prevent caching issues
    const cacheBuster = new Date().getTime();
    
    // Try the basic test endpoint first
    try {
        console.log("Testing POST endpoint at /test-post");
        const testRes = await fetch(`/test-post?_=${cacheBuster}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({test: true})
        });
        
        if (testRes.ok) {
            const testData = await testRes.json();
            console.log("Test endpoint works:", testData);
            document.getElementById('lc-result').innerText = 'Test endpoint works, attempting actual calculation...';
            
            // Now try our actual endpoints
            const endpoints = [
                '/stock-problems',
                '/leetcode/stock'
            ];
            
            for (const endpoint of endpoints) {
                try {
                    console.log(`Trying endpoint: ${endpoint}`);
                    const res = await fetch(`${endpoint}?_=${cacheBuster}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    
                    console.log(`${endpoint} response status:`, res.status);
                    
                    if (res.ok) {
                        const data = await res.json();
                        console.log(`${endpoint} response data:`, data);
                        
                        if (data.error) {
                            document.getElementById('lc-result').innerText = data.error;
                        } else {
                            lcLastResult = data;
                            setLcCodeLang(lcCodeLang); // Show selected code
                            console.log("Calculation successful from", endpoint);
                            return; // Success, exit function
                        }
                        return; // We got a response, exit function
                    } else {
                        console.error(`${endpoint} error:`, await res.text());
                    }
                } catch (e) {
                    console.error(`Error with ${endpoint}:`, e);
                }
            }
            
            // If we get here, all endpoints failed
            document.getElementById('lc-result').innerText = `All endpoints failed. Check server logs.`;
            
        } else {
            console.error("Test endpoint failed:", await testRes.text());
            document.getElementById('lc-result').innerText = `Test endpoint failed with status ${testRes.status}. Basic POST requests not working.`;
        }
    } catch (e) {
        console.error("Test fetch error:", e);
        document.getElementById('lc-result').innerText = `Failed basic test. Error: ${e.message}`;
    }
}
async function fetchStableChange() {
    document.getElementById('stable-cards').innerText = 'Loading...';
    const metricSel = document.getElementById('stable-metric').value;
    let metric = metricSel;
    let order = 'asc';
    if (metricSel === 'maxstd') { metric = 'std'; order = 'desc'; }
    if (metricSel === 'maxmeanabs') { metric = 'meanabs'; order = 'desc'; }
    const windowSize = document.getElementById('stable-window').value;
    const days = document.getElementById('stable-range').value;
    let url = `/stocks/stable?metric=${metric}&order=${order}&window=${windowSize}&days=${days}`;
    
    console.log("Fetching stable stocks from:", url);
    
    try {
        const res = await fetch(url);
        
        if (!res.ok) {
            document.getElementById('stable-cards').innerHTML = 
                `<div style="color:red;padding:10px;background:#ffeeee;border-radius:5px;">
                    Error fetching stable stocks: HTTP ${res.status} ${res.statusText}
                </div>`;
            console.error("Error response:", await res.text());
            return;
        }
        
        const data = await res.json();
        console.log("Stable stocks response:", data);
        
        if (!Array.isArray(data) || data.length === 0) {
            document.getElementById('stable-cards').innerHTML = 
                `<div style="padding:10px;background:#ffeeee;border-radius:5px;">
                    No stable stocks data found or empty response.
                </div>`;
            return;
        }
        
        // Check if we have an error in the first result
        if (data[0] && data[0].error && !data[0].symbol) {
            document.getElementById('stable-cards').innerHTML = 
                `<div style="color:red;padding:10px;background:#ffeeee;border-radius:5px;">
                    Server error: ${data[0].error}
                </div>`;
            return;
        }
        
        let cardsHtml = '';
        data.slice(0, 1).forEach((item, idx) => { // Only show top 1
            if (item.stability_score !== undefined) {
                const chartId = `stableChart${idx}`;
                const sliderId = `stableSlider${idx}`;
                const infoId = `stableInfo${idx}`;
                const windowLen = item.window_len;
                const allCloses = item.all_closes;
                const allDates = item.all_dates;
                const sliderMax = allCloses.length - 1;
                const sliderStart = item.window_start_idx;
                const sliderEnd = item.window_end_idx;
                cardsHtml += `
                <div style='display:flex;flex-direction:column;align-items:center;gap:0;margin-bottom:28px;background:#fafbfc;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);padding:18px 0;max-width:700px;margin-left:auto;margin-right:auto;'>
                    <div style='width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 0 0 0;'>
                        <canvas id='${chartId}' width='350' height='350' style='background:#fff;border-radius:8px;'></canvas>
                        <div id='${sliderId}' style='width:100%;margin-top:10px;'></div>
                        <div id='${chartId}-window' style='font-size:0.92em;color:#888;'>Window: ${item.start_date} ~ ${item.end_date}</div>
                    </div>
                    <div id='${infoId}' style='width:100%;max-width:600px;margin-top:18px;'>
                        <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                        <div style='margin-bottom:4px;'><b>Start:</b> ${item.start_date} <b>End:</b> ${item.end_date}</div>
                        <div style='margin-bottom:4px;'><b>Stability Score:</b> ${item.stability_score.toFixed(4)}</div>
                        <div style='margin-bottom:4px;'><b>Metric:</b> ${getMetricLabel(item.metric, item.order)}</div>
                        <div style='margin-bottom:4px;font-size:0.97em;color:#888;'>Window Prices: [${item.window_prices.map(x=>x.toFixed(2)).join(', ')}]</div>
                    </div>
                </div>
                `;
            } else {
                cardsHtml += `<div style='margin-bottom:18px;color:#c00;'>${item.name} (${item.symbol}): ${item.error}</div>`;
            }
        });
        document.getElementById('stable-cards').innerHTML = cardsHtml || '<div>No results found.</div>';
        // Render charts and slider logic
        data.slice(0, 1).forEach((item, idx) => {
            if (item.stability_score !== undefined) {
                const chartId = `stableChart${idx}`;
                const sliderId = `stableSlider${idx}`;
                const infoId = `stableInfo${idx}`;
                const windowLen = item.window_len;
                const allCloses = item.all_closes;
                const allDates = item.all_dates;
                const metric = item.metric;
                // Helper to update chart and info
                function updateWindow(startIdx) {
                    const windowPrices = allCloses.slice(startIdx, startIdx+windowLen);
                    const windowDates = allDates.slice(startIdx, startIdx+windowLen);
                    // Compute stability
                    let score = 0;
                    if (metric === 'meanabs') {
                        score = windowPrices.length > 1 ? windowPrices.slice(1).reduce((acc, v, i) => acc + Math.abs(v - windowPrices[i]), 0) / (windowPrices.length-1) : 0;
                    } else {
                        const changes = windowPrices.slice(1).map((v,i)=>v-windowPrices[i]);
                        score = changes.length > 0 ? Math.sqrt(changes.reduce((acc, v) => acc + v*v, 0) / changes.length) : 0;
                    }
                    // Update info
                    document.getElementById(infoId).innerHTML = `
                        <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                        <div style='margin-bottom:4px;'><b>Start:</b> ${windowDates[0]} <b>End:</b> ${windowDates[windowDates.length-1]}</div>
                        <div style='margin-bottom:4px;'><b>Stability Score:</b> ${score.toFixed(4)}</div>
                        <div style='margin-bottom:4px;'><b>Metric:</b> ${getMetricLabel(item.metric, item.order)}</div>
                        <div style='margin-bottom:4px;font-size:0.97em;color:#888;' title='${windowPrices.map(x=>x.toFixed(2)).join(", ") }'>Window Prices: [${formatWindowPrices(windowPrices)}]</div>
                    `;
                    document.getElementById(`${chartId}-window`).innerText = `Window: ${windowDates[0]} ~ ${windowDates[windowDates.length-1]}`;
                    // Update chart
                    if (windowPrices.length > 0 && window.myStableCharts && window.myStableCharts[chartId]) {
                        window.myStableCharts[chartId].data.labels = windowPrices.map((v,i)=>i+1);
                        window.myStableCharts[chartId].data.datasets[0].data = windowPrices;
                        window.myStableCharts[chartId].update();
                    }
                }
                // Initial chart
                const ctx = document.getElementById(chartId).getContext('2d');
                if (!window.myStableCharts) window.myStableCharts = {};
                window.myStableCharts[chartId] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: allCloses.slice(item.window_start_idx, item.window_start_idx+windowLen).map((v,i)=>i+1),
                        datasets: [{
                            label: 'Price',
                            data: allCloses.slice(item.window_start_idx, item.window_start_idx+windowLen),
                            borderColor: '#2196f3',
                            backgroundColor: 'rgba(33,150,243,0.08)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 2,
                            pointBackgroundColor: '#2196f3',
                        }]
                    },
                    options: {
                        responsive: false,
                        plugins: {
                            legend: { display: false },
                            title: { display: false },
                            tooltip: { enabled: true }
                        },
                        scales: {
                            x: { display: false },
                            y: { display: true, title: { display: false }, grid: { display: false } }
                        }
                    }
                });
                // Dual-handle slider using noUiSlider
                const sliderElem = document.getElementById(sliderId);
                noUiSlider.create(sliderElem, {
                    start: [item.window_start_idx, item.window_end_idx],
                    connect: true,
                    range: { min: 0, max: item.window_end_idx },
                    step: 1,
                    tooltips: [true, true],
                    format: {
                        to: v => Math.round(v),
                        from: v => Math.round(v)
                    }
                });
                sliderElem.noUiSlider.on('update', function(values) {
                    const startIdx = Number(values[0]);
                    const endIdx = Number(values[1]);
                    if (endIdx - startIdx < 1) return; // window must be at least 2
                    const windowPrices = allCloses.slice(startIdx, endIdx+1);
                    const windowDates = allDates.slice(startIdx, endIdx+1);
                    let score = 0;
                    if (item.metric === 'meanabs') {
                        score = windowPrices.length > 1 ? windowPrices.slice(1).reduce((acc, v, i) => acc + Math.abs(v - windowPrices[i]), 0) / (windowPrices.length-1) : 0;
                    } else {
                        const changes = windowPrices.slice(1).map((v,i)=>v-windowPrices[i]);
                        score = changes.length > 0 ? Math.sqrt(changes.reduce((acc, v) => acc + v*v, 0) / changes.length) : 0;
                    }
                    document.getElementById(infoId).innerHTML = `
                        <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                        <div style='margin-bottom:4px;'><b>Start:</b> ${windowDates[0]} <b>End:</b> ${windowDates[windowDates.length-1]}</div>
                        <div style='margin-bottom:4px;'><b>Stability Score:</b> ${score.toFixed(4)}</div>
                        <div style='margin-bottom:4px;'><b>Metric:</b> ${getMetricLabel(item.metric, item.order)}</div>
                        <div style='margin-bottom:4px;font-size:0.97em;color:#888;' title='${windowPrices.map(x=>x.toFixed(2)).join(", ") }'>Window Prices: [${formatWindowPrices(windowPrices)}]</div>
                    `;
                    document.getElementById(`${chartId}-window`).innerText = `Window: ${windowDates[0]} ~ ${windowDates[windowDates.length-1]}`;
                    // Update chart
                    if (windowPrices.length > 0 && window.myStableCharts && window.myStableCharts[chartId]) {
                        window.myStableCharts[chartId].data.labels = windowPrices.map((v,i)=>i+1);
                        window.myStableCharts[chartId].data.datasets[0].data = windowPrices;
                        window.myStableCharts[chartId].update();
                    }
                });
            }
        });
    } catch (e) {
        document.getElementById('stable-cards').innerText = 'Failed to fetch stable stocks.';
    }
}
// Initialize input visibility
updateLcInputs();
// Helper to render a single stable card (for explore)
function renderStableCard(item, idx, targetId, isExplorer = false) {
    try {
        if (!item || item.stability_score === undefined) {
            document.getElementById(targetId).innerHTML = `
                <div style="padding:12px;background:#eee;border-radius:5px;text-align:center;">
                    ${item && item.error ? 
                        `<span style="color:red">Error: ${item.error}</span>` : 
                        'No valid data available for this stock.'}
                </div>`;
            return;
        }
        
        const chartId = `${isExplorer ? 'explore' : ''}StableChart${idx}`;
        const sliderId = `${isExplorer ? 'explore' : ''}StableSlider${idx}`;
        const infoId = `${isExplorer ? 'explore' : ''}StableInfo${idx}`;
        const windowLen = item.window_len;
        const allCloses = item.all_closes;
        const allDates = item.all_dates;
        const sliderMax = allCloses.length - 1;
        const sliderStart = item.window_start_idx;
        const sliderEnd = item.window_end_idx;
        let cardHtml = '';
        
        // Check if we have all required data for rendering
        if (!allCloses || !Array.isArray(allCloses) || allCloses.length < windowLen ||
            !allDates || !Array.isArray(allDates) || allDates.length < windowLen) {
            document.getElementById(targetId).innerHTML = `
                <div style="padding:12px;background:#eee;border-radius:5px;text-align:center;">
                    <span style="color:red">Error: Incomplete data for chart rendering</span>
                </div>`;
            return;
        }
        
        if (isExplorer) {
            cardHtml = `
            <div style='display:flex;flex-direction:column;align-items:center;gap:0;margin-bottom:28px;background:#fafbfc;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);padding:18px 0;max-width:700px;margin-left:auto;margin-right:auto;'>
                <div style='width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 0 0 0;'>
                    <canvas id='${chartId}' width='350' height='350' style='background:#fff;border-radius:8px;'></canvas>
                    <div id='${sliderId}' style='width:100%;margin-top:10px;'></div>
                    <div id='${chartId}-window' style='font-size:0.92em;color:#888;'>Window: ${item.start_date} ~ ${item.end_date}</div>
                </div>
                <div id='${infoId}' style='width:100%;max-width:600px;margin-top:18px;'></div>
            </div>
            `;
        } else {
            cardHtml = `
            <div style='display:flex;flex-wrap:nowrap;align-items:stretch;gap:0;margin-bottom:28px;background:#fafbfc;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);padding:18px 0;max-width:700px;margin-left:auto;margin-right:auto;'>
                <div style='flex:1 1 220px;min-width:180px;max-width:260px;display:flex;flex-direction:column;justify-content:center;padding:0 24px 0 24px;'>
                    <div id='${infoId}'>
                    </div>
                </div>
                <div style='width:1px;background:#e0e0e0;margin:0 0;'></div>
                <div style='flex:2 1 320px;min-width:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 32px 0 32px;'>
                    <canvas id='${chartId}' width='260' height='110' style='background:#fff;border-radius:8px;'></canvas>
                    <div id='${sliderId}' style='width:100%;margin-top:10px;'></div>
                    <div id='${chartId}-window' style='font-size:0.92em;color:#888;'>Window: ${item.start_date} ~ ${item.end_date}</div>
                </div>
            </div>
            `;
        }
        document.getElementById(targetId).innerHTML = cardHtml;
        
        try {
            // Chart logic
            const ctx = document.getElementById(chartId).getContext('2d');
            if (!window.myStableCharts) window.myStableCharts = {};
            
            // Safely extract the data slice
            const startIdx = Math.min(sliderStart, allCloses.length - windowLen);
            const endIdx = Math.min(sliderEnd, allCloses.length - 1);
            
            window.myStableCharts[chartId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: allCloses.slice(startIdx, endIdx+1).map((v,i)=>i+1),
                    datasets: [{
                        label: 'Price',
                        data: allCloses.slice(startIdx, endIdx+1),
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33,150,243,0.08)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 2,
                        pointBackgroundColor: '#2196f3',
                    }]
                },
                options: {
                    responsive: false,
                    plugins: {
                        legend: { display: false },
                        title: { display: false },
                        tooltip: { enabled: true }
                    },
                    scales: {
                        x: { display: false },
                        y: { display: true, title: { display: false }, grid: { display: false } }
                    }
                }
            });
            
            // Fill the info box initially
            document.getElementById(infoId).innerHTML = `
                <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                <div style='margin-bottom:4px;'><b>Start:</b> ${item.start_date} <b>End:</b> ${item.end_date}</div>
                <div style='margin-bottom:4px;'><b>Stability Score:</b> ${item.stability_score.toFixed(4)}</div>
                <div style='margin-bottom:4px;'><b>Metric:</b> ${getMetricLabel(item.metric, item.order)}</div>
                <div style='margin-bottom:4px;font-size:0.97em;color:#888;' title='${item.window_prices.map(x=>x.toFixed(2)).join(", ") }'>Window Prices: [${formatWindowPrices(item.window_prices)}]</div>
            `;
            
            try {
                // Dual-handle slider using noUiSlider
                const sliderElem = document.getElementById(sliderId);
                if (typeof noUiSlider === 'undefined') {
                    console.error("noUiSlider library not available");
                    return;
                }
                
                noUiSlider.create(sliderElem, {
                    start: [sliderStart, sliderEnd],
                    connect: true,
                    range: { min: 0, max: sliderMax },
                    step: 1,
                    tooltips: [true, true],
                    format: {
                        to: v => Math.round(v),
                        from: v => Math.round(v)
                    }
                });
                
                // Update when slider changes
                sliderElem.noUiSlider.on('update', function(values) {
                    const startIdx = Number(values[0]);
                    const endIdx = Number(values[1]);
                    if (endIdx - startIdx < 1) return; // window must be at least 2
                    
                    // Safety check for valid indices
                    if (startIdx >= 0 && endIdx < allCloses.length && startIdx < endIdx) {
                        const windowPrices = allCloses.slice(startIdx, endIdx+1);
                        const windowDates = allDates.slice(startIdx, endIdx+1);
                        let score = 0;
                        if (item.metric === 'meanabs') {
                            score = windowPrices.length > 1 ? windowPrices.slice(1).reduce((acc, v, i) => acc + Math.abs(v - windowPrices[i]), 0) / (windowPrices.length-1) : 0;
                        } else {
                            const changes = windowPrices.slice(1).map((v,i)=>v-windowPrices[i]);
                            score = changes.length > 0 ? Math.sqrt(changes.reduce((acc, v) => acc + v*v, 0) / changes.length) : 0;
                        }
                        document.getElementById(infoId).innerHTML = `
                            <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                            <div style='margin-bottom:4px;'><b>Start:</b> ${windowDates[0]} <b>End:</b> ${windowDates[windowDates.length-1]}</div>
                            <div style='margin-bottom:4px;'><b>Stability Score:</b> ${score.toFixed(4)}</div>
                            <div style='margin-bottom:4px;'><b>Metric:</b> ${getMetricLabel(item.metric, item.order)}</div>
                            <div style='margin-bottom:4px;font-size:0.97em;color:#888;' title='${windowPrices.map(x=>x.toFixed(2)).join(", ") }'>Window Prices: [${formatWindowPrices(windowPrices)}]</div>
                        `;
                        document.getElementById(`${chartId}-window`).innerText = `Window: ${windowDates[0]} ~ ${windowDates[windowDates.length-1]}`;
                        
                        // Update chart
                        if (windowPrices.length > 0 && window.myStableCharts && window.myStableCharts[chartId]) {
                            window.myStableCharts[chartId].data.labels = windowPrices.map((v,i)=>i+1);
                            window.myStableCharts[chartId].data.datasets[0].data = windowPrices;
                            window.myStableCharts[chartId].update();
                        }
                    }
                });
            } catch (sliderError) {
                console.error("Error creating slider:", sliderError);
                document.getElementById(targetId).innerHTML += `
                    <div style="color:orange;margin-top:10px;text-align:center;">
                        Note: Interactive slider could not be initialized. Chart is still viewable.
                    </div>`;
            }
        } catch (chartError) {
            console.error("Error rendering chart:", chartError);
            document.getElementById(targetId).innerHTML = `
                <div style="padding:12px;background:#ffeeee;border-radius:5px;text-align:center;color:red;">
                    Error rendering chart: ${chartError.message}
                </div>`;
        }
    } catch (error) {
        console.error("Error in renderStableCard:", error);
        document.getElementById(targetId).innerHTML = `
            <div style="padding:12px;background:#ffeeee;border-radius:5px;text-align:center;color:red;">
                Failed to render card: ${error.message}
            </div>`;
    }
}
// Add event listener for explore-stock
window.addEventListener('DOMContentLoaded', function() {
    const exploreSelect = document.getElementById('explore-stock');
    const metricSelect = document.getElementById('stable-metric');
    const exploreMetricSelect = document.getElementById('explore-metric');
    const exploreRangeSelect = document.getElementById('explore-range');
    const exploreWindowSelect = document.getElementById('explore-window');
    // Remove all auto-fetch event listeners for explorer section
    // Only enable metric dropdown when all required fields are selected
    function updateExploreMetricState() {
        const stock = exploreSelect.value;
        const range = exploreRangeSelect.value;
        const windowSize = exploreWindowSelect.value;
        if (stock && range && windowSize) {
            exploreMetricSelect.disabled = false;
        } else {
            exploreMetricSelect.disabled = true;
        }
    }
    exploreSelect.addEventListener('change', function() {
        updateExploreMetricState();
    });
    exploreRangeSelect.addEventListener('change', function() {
        updateExploreMetricState();
    });
    exploreWindowSelect.addEventListener('change', function() {
        updateExploreMetricState();
    });
    exploreMetricSelect.addEventListener('change', function() {
        // Do not auto-fetch
    });
    // Initial state
    updateExploreMetricState();
    // Only fetch when Apply is clicked
    window.fetchAndShowExploreCard = function() {
        if (!exploreMetricSelect.disabled && exploreMetricSelect.value) {
            const symbol = exploreSelect.value;
            let metricSel = exploreMetricSelect.value;
            let metric = metricSel;
            let order = 'asc';
            if (metricSel === 'maxstd') { metric = 'std'; order = 'desc'; }
            if (metricSel === 'maxmeanabs') { metric = 'meanabs'; order = 'desc'; }
            const days = exploreRangeSelect.value;
            const windowSize = exploreWindowSelect.value;
            document.getElementById('explore-card').innerHTML = 'Loading...';
            
            const url = `/stocks/stable?metric=${metric}&order=${order}&symbol=${symbol}&window=${windowSize}&days=${days}`;
            console.log("Fetching stock stability data from:", url);
            
            fetch(url)
                .then(res => {
                    if (!res.ok) {
                        console.error("Error response:", res.status, res.statusText);
                        throw new Error(`HTTP error ${res.status}: ${res.statusText}`);
                    }
                    return res.json();
                })
                .then(data => {
                    console.log("Got data:", data);
                    if (Array.isArray(data) && data.length > 0) {
                        if (data[0].error) {
                            document.getElementById('explore-card').innerHTML = 
                                `<div style="color:red;padding:12px;background:#ffeeee;border-radius:5px;text-align:center;">
                                    ${data[0].error}
                                </div>`;
                        } else {
                            renderStableCard(data[0], 0, 'explore-card', true);
                        }
                    } else {
                        document.getElementById('explore-card').innerHTML = 
                            `<div style="padding:12px;background:#eee;border-radius:5px;text-align:center;">
                                No data found for ${symbol} with the current settings.
                            </div>`;
                    }
                })
                .catch(error => {
                    console.error("Error fetching stock data:", error);
                    document.getElementById('explore-card').innerHTML = 
                        `<div style="color:red;padding:12px;background:#ffeeee;border-radius:5px;text-align:center;">
                            Failed to fetch data: ${error.message}
                            <br><br>
                            <button onclick="fetchAndShowExploreCard()" style="background:#2196f3;color:#fff;border:none;padding:5px 16px;border-radius:5px;font-size:0.97rem;">Try Again</button>
                        </div>`;
                });
        } else {
            document.getElementById('explore-card').innerHTML = 
                `<div style="padding:12px;background:#eee;border-radius:5px;text-align:center;">
                    Please select a stock and stability metric first.
                </div>`;
        }
    };
    // Reset button resets all controls to default
    window.resetExplorerSection = function() {
        if (exploreSelect.options.length > 0) exploreSelect.selectedIndex = 0;
        exploreMetricSelect.selectedIndex = 0;
        exploreMetricSelect.disabled = true;
        exploreRangeSelect.selectedIndex = 4; // 3 years
        exploreWindowSelect.selectedIndex = 2; // 20 days
        document.getElementById('explore-card').innerHTML = '';
        updateExploreMetricState();
    };
    // Populate explorer-stock dropdown
    filterAndPopulateExplorerDropdown();
    const predictionRangeSelect = document.getElementById('prediction-range');
    predictionRangeSelect.addEventListener('change', function() {
        filterAndPopulatePredictionDropdown();
    });
    // Force-populate the explain-stock dropdown with tickers (independent from explorer)
    const explainSelect = document.getElementById('explain-stock');
    if (explainSelect) {
        explainSelect.innerHTML = '<option value="">-- Select --</option>';
        [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
            'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM',
            'SPY', 'QQQ', 'VOO', 'ARKK', 'EEM', 'XLF',
            'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F', 'MYM=F', 'M2K=F',
            'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F', 'ZS=F', 'ZW=F',
            'VX=F', 'BTC=F', 'ETH=F'
        ].forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            explainSelect.appendChild(opt);
        });
    }
    // Remove old cat-house-btn logic if present
    const catHeartBtn = document.getElementById('cat-heart-btn');
    if (catHeartBtn) {
        catHeartBtn.addEventListener('click', function() {
            const catHouseContent = document.getElementById('cat-house-content');
            if (catHouseContent) {
                catHouseContent.innerHTML = 'happy lover';
            }
        });
    }
    // Lab section logic
    const labSelect = document.getElementById('lab-ticker-select');
    const labExplanation = document.getElementById('lab-explanation');
    const labApplyBtn = document.getElementById('lab-apply-btn');
    if (labSelect && labExplanation && labApplyBtn) {
        labApplyBtn.addEventListener('click', async function() {
            const stock = labSelect.value;
            if (!stock) {
                labExplanation.innerHTML = '<span style="color:red">Please select a stock first.</span>';
                return;
            }
            labExplanation.innerHTML = 'Loading...';
            try {
                const res = await fetch('http://127.0.0.1:5001/explain_stability?stock=' + stock);
                const data = await res.json();
                labExplanation.innerHTML = data.explanation.replace(/\n/g, '<br>');
            } catch (e) {
                labExplanation.innerHTML = 'Error: ' + e.message;
            }
        });
    }
});
// Add spinner animation CSS
const style = document.createElement('style');
style.innerHTML = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(style);
function getMetricLabel(metric, order) {
    if (metric === 'std' && order === 'asc') {
        return 'Lowest Standard Deviation (Most Stable)';
    } else if (metric === 'std' && order === 'desc') {
        return 'Highest Standard Deviation (Most Unstable)';
    } else if (metric === 'meanabs' && order === 'asc') {
        return 'Lowest Mean Absolute Change (Most Stable)';
    } else if (metric === 'meanabs' && order === 'desc') {
        return 'Highest Mean Absolute Change (Most Unstable)';
    } else {
        return `${order === 'asc' ? 'Lowest' : 'Highest'} ${metric === 'std' ? 'Standard Deviation' : 'Mean Absolute Change'}`;
    }
}
function formatWindowPrices(windowPrices) {
    if (windowPrices.length <= 5) {
        return windowPrices.map(x => x.toFixed(2)).join(', ');
    } else {
        return `${windowPrices[0].toFixed(2)}, ${windowPrices[1].toFixed(2)}, ..., ${windowPrices[windowPrices.length-2].toFixed(2)}, ${windowPrices[windowPrices.length-1].toFixed(2)}`;
    }
}
const tickerDisplayNames = {
    'AAPL': 'Apple (AAPL)', 'MSFT': 'Microsoft (MSFT)', 'GOOGL': 'Google (GOOGL)', 'AMZN': 'Amazon (AMZN)', 'META': 'Meta (META)', 'NVDA': 'Nvidia (NVDA)', 'TSLA': 'Tesla (TSLA)', 'NFLX': 'Netflix (NFLX)', 'AMD': 'AMD (AMD)', 'INTC': 'Intel (INTC)',
    'BRK-B': 'Berkshire Hathaway (BRK-B)', 'JNJ': 'Johnson & Johnson (JNJ)', 'V': 'Visa (V)', 'JPM': 'JPMorgan Chase (JPM)', 'WMT': 'Walmart (WMT)', 'PG': 'Procter & Gamble (PG)', 'KO': 'Coca-Cola (KO)', 'XOM': 'Exxon Mobil (XOM)',
    'SPY': 'S&P 500 ETF (SPY)', 'QQQ': 'Nasdaq 100 ETF (QQQ)', 'VOO': 'S&P 500 ETF (VOO)', 'ARKK': 'ARK Innovation ETF (ARKK)', 'EEM': 'Emerging Markets ETF (EEM)', 'XLF': 'Financial Select Sector SPDR (XLF)',
    'ES=F': 'S&P 500 E-mini (ES=F)', 'NQ=F': 'Nasdaq 100 E-mini (NQ=F)', 'YM=F': 'Dow Jones E-mini (YM=F)', 'RTY=F': 'Russell 2000 E-mini (RTY=F)', 'MES=F': 'Micro E-mini S&P 500 (MES=F)', 'MNQ=F': 'Micro E-mini Nasdaq 100 (MNQ=F)', 'MYM=F': 'Micro E-mini Dow (MYM=F)', 'M2K=F': 'Micro E-mini Russell 2000 (M2K=F)',
    'GC=F': 'Gold (GC=F)', 'SI=F': 'Silver (SI=F)', 'CL=F': 'Crude Oil WTI (CL=F)', 'BZ=F': 'Brent Oil (BZ=F)', 'NG=F': 'Natural Gas (NG=F)', 'HG=F': 'Copper (HG=F)', 'ZC=F': 'Corn (ZC=F)', 'ZS=F': 'Soybeans (ZS=F)', 'ZW=F': 'Wheat (ZW=F)',
    'VX=F': 'VIX (VX=F)', 'BTC=F': 'Bitcoin Futures (BTC=F)', 'ETH=F': 'Ethereum Futures (ETH=F)'
};

function populateDropdown(selectId, tickers, allowEmpty=false) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = '';
    if (allowEmpty) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = '-- Select --';
        sel.appendChild(opt);
    }
    // Only add tickers that are not empty strings and are in the tickers list
    tickers.forEach(t => {
        if (!t) return; // skip empty
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = tickerDisplayNames[t] || t;
        sel.appendChild(opt);
    });
}
function resetStableSection() {
    document.getElementById('stable-metric').selectedIndex = 0;
    document.getElementById('stable-range').selectedIndex = 4; // 3 years
    document.getElementById('stable-window').selectedIndex = 2; // 20 days
    document.getElementById('stable-cards').innerHTML = '';
}
function resetExplorerSection() {
    const exploreStock = document.getElementById('explore-stock');
    if (exploreStock.options.length > 0) exploreStock.selectedIndex = 0;
    document.getElementById('explore-metric').selectedIndex = 0;
    document.getElementById('explore-metric').disabled = true;
    document.getElementById('explore-range').selectedIndex = 4; // 3 years
    document.getElementById('explore-window').selectedIndex = 2; // 20 days
    document.getElementById('explore-card').innerHTML = '';
}
async function filterAndPopulateExplorerDropdown() {
    const exploreSelect = document.getElementById('explore-stock');
    const exploreRangeSelect = document.getElementById('explore-range');
    const exploreWindowSelect = document.getElementById('explore-window');
    exploreSelect.innerHTML = '<option value="">Loading...</option>';
    const days = exploreRangeSelect.value;
    const windowSize = exploreWindowSelect.value;
    
    console.log("Fetching available tickers for Explorer...");
    
    try {
        // First try to fetch the list of available tickers
        const tickerRes = await fetch('/available_tickers');
        
        if (!tickerRes.ok) {
            console.error("Failed to fetch available tickers:", tickerRes.status, tickerRes.statusText);
            exploreSelect.innerHTML = '<option value="">Failed to load tickers</option>';
            return;
        }
        
        const tickers = await tickerRes.json();
        console.log(`Got ${tickers.length} available tickers`);
        
        if (!tickers || tickers.length === 0) {
            exploreSelect.innerHTML = '<option value="">No tickers available</option>';
            return;
        }
        
        // Process tickers in smaller batches to avoid overwhelming the server
        const BATCH_SIZE = 5;
        const validTickers = [];
        
        // Instead of testing each ticker, just use the list directly to speed things up
        populateDropdown('explore-stock', tickers, true);
        
        // If we want to validate each ticker (optional):
        /*
        exploreSelect.innerHTML = '<option value="">Validating tickers...</option>';
        
        for (let i = 0; i < tickers.length; i += BATCH_SIZE) {
            const batch = tickers.slice(i, i + BATCH_SIZE);
            await Promise.all(batch.map(async t => {
                try {
                    const url = `/stocks/stable?symbol=${t}&window=${windowSize}&days=${days}&metric=std&order=asc`;
                    const res = await fetch(url);
                    if (res.ok) {
                        const data = await res.json();
                        if (Array.isArray(data) && data.length > 0 && !data[0].error) {
                            validTickers.push(t);
                        }
                    }
                } catch (e) {
                    console.error(`Error validating ticker ${t}:`, e);
                }
            }));
            
            // Update status
            exploreSelect.innerHTML = `<option value="">Validated ${Math.min(i + BATCH_SIZE, tickers.length)}/${tickers.length} tickers...</option>`;
        }
        
        if (validTickers.length === 0) {
            exploreSelect.innerHTML = '<option value="">No valid tickers found</option>';
        } else {
            populateDropdown('explore-stock', validTickers, true);
        }
        */
    } catch (error) {
        console.error("Error in filterAndPopulateExplorerDropdown:", error);
        exploreSelect.innerHTML = '<option value="">Error loading tickers</option>';
    }
}
async function filterAndPopulatePredictionDropdown() {
    const predictionSelect = document.getElementById('prediction-stock');
    const predictionRangeSelect = document.getElementById('prediction-range');
    predictionSelect.innerHTML = '<option value="">Loading...</option>';
    const days = predictionRangeSelect.value;
    let tickers = [];
    try {
        tickers = await fetch(`/stocks/available_for_prediction?days=${days}`).then(res => res.json());
    } catch {
        predictionSelect.innerHTML = '<option value="">Failed to load</option>';
        return;
    }
    if (!tickers || tickers.length === 0) {
        predictionSelect.innerHTML = '<option value="">No stocks available</option>';
    } else {
        populateDropdown('prediction-stock', tickers, true);
    }
}
// Function to efficiently update the Stock Trends chart without recreating it
function updateStockTrendsChart(startDate, endDate) {
    // Skip if no chart exists yet or no data available
    if (!stockCharts['stockChartMulti'] || Object.keys(stockTrendsData).length === 0) {
        return;
    }
    
    const select = document.getElementById('stock-select');
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);
    
    if (selected.length === 0) {
        return;
    }
    
    console.log(`Directly updating chart for range ${startDate} to ${endDate}`);
    
    // Filter data for the selected range
    let filteredData = {};
    let allChartData = [];
    let chartLabels = [];
    let first = true;
    
    for (const symbol of selected) {
        if (stockTrendsData[symbol]) {
            const stockData = stockTrendsData[symbol];
            const dateRangeIndices = getDateRangeIndices(stockData.dates, startDate, endDate);
            
            if (dateRangeIndices) {
                const slicedDates = stockData.dates.slice(dateRangeIndices.startIdx, dateRangeIndices.endIdx + 1);
                const slicedCloses = stockData.closes.slice(dateRangeIndices.startIdx, dateRangeIndices.endIdx + 1);
                
                if (slicedCloses.length > 0) {
                    if (first) {
                        chartLabels = slicedDates;
                        first = false;
                    }
                    
                    // Calculate basic stats for visualization
                    const open = slicedCloses[0];
                    const close = slicedCloses[slicedCloses.length-1];
                    const color = close >= open ? 'green' : 'red';
                    
                    // Prepare data for chart
                    allChartData.push({
                        label: `${stockData.name} (${stockData.symbol})`,
                        data: slicedCloses,
                        borderColor: color,
                        backgroundColor: color === 'green' ? 'rgba(76,175,80,0.12)' : 'rgba(233,30,99,0.12)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: slicedCloses.map((v,i)=>i===slicedCloses.length-1?6:0),
                        pointBackgroundColor: slicedCloses.map((v,i)=>i===slicedCloses.length-1?color:'rgba(0,0,0,0)'),
                        pointBorderColor: slicedCloses.map((v,i)=>i===slicedCloses.length-1?color:'rgba(0,0,0,0)'),
                        pointBorderWidth: slicedCloses.map((v,i)=>i===slicedCloses.length-1?2:0)
                    });
                    
                    filteredData[stockData.name] = {
                        symbol: stockData.symbol,
                        dates: slicedDates,
                        closes: slicedCloses
                    };
                }
            }
        }
    }
    
    if (allChartData.length === 0 || chartLabels.length === 0) {
        return;
    }
    
    // Update the existing chart with new data
    const chart = stockCharts['stockChartMulti'];
    chart.data.labels = chartLabels;
    chart.data.datasets = allChartData;
    
    // Update chart title
    chart.options.plugins.title.text = `Stock Price Trend (${startDate} to ${endDate})`;
    
    // Update the chart (with animation duration of 0 for maximum smoothness)
    chart.update('none');
    
    // We only update the chart here - the stats table is only updated when fetchStockTrends is called
    // This makes the slider extremely responsive
}

function resetStockTrendsSection() {
    // Reset stock selection
    const select = document.getElementById('stock-select');
    if (select) {
        for (let i = 0; i < select.options.length; i++) {
            select.options[i].selected = false;
        }
    }
    
    // Reset Y-axis scale to default
    const scaleSelect = document.getElementById('scale-select');
    if (scaleSelect) {
        scaleSelect.selectedIndex = 0; // Linear
    }
    
    // Clear results and hide chart
    document.getElementById('stock-trends-result').innerHTML = '';
    document.getElementById('stockChartMulti').style.display = 'none';
    
    // Reset time range slider to default (past month)
    const slider = document.getElementById('time-range-slider');
    if (slider && slider.noUiSlider) {
        const today = new Date();
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(today.getMonth() - 1);
        slider.noUiSlider.set([oneMonthAgo.getTime(), today.getTime()]);
    }
}

function resetMaxChangeSection() {
    // Reset stock selection
    const select = document.getElementById('maxchange-stock-select');
    if (select) {
        for (let i = 0; i < select.options.length; i++) {
            select.options[i].selected = false;
        }
    }
    
    // Clear results
    document.getElementById('maxchange-result').innerHTML = '';
    
    // Reset time range slider to default (past month)
    const slider = document.getElementById('maxchange-time-range-slider');
    if (slider && slider.noUiSlider) {
        const today = new Date();
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(today.getMonth() - 1);
        slider.noUiSlider.set([oneMonthAgo.getTime(), today.getTime()]);
    }
}

function resetLcStockSection() {
    // Reset problem to first option
    const problemSelect = document.getElementById('lc-problem');
    if (problemSelect) {
        problemSelect.selectedIndex = 0;
        updateLcInputs(); // Update visibility of related inputs
    }
    
    // Clear prices input
    const pricesInput = document.getElementById('lc-prices');
    if (pricesInput) {
        pricesInput.value = '';
    }
    
    // Reset k to default
    const kInput = document.getElementById('lc-k');
    if (kInput) {
        kInput.value = '2';
    }
    
    // Reset fee to default
    const feeInput = document.getElementById('lc-fee');
    if (feeInput) {
        feeInput.value = '0';
    }
    
    // Clear results
    document.getElementById('lc-result').innerHTML = '';
}

// =============================================
// Mood Analyzer Functions
// =============================================

// Initialize the mood date picker with today's date
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default for mood entry
    const today = new Date();
    const formattedDate = today.toISOString().split('T')[0]; // YYYY-MM-DD format
    document.getElementById('mood-date').value = formattedDate;
    
    // Initialize mood score slider
    const moodScoreSlider = document.getElementById('mood-score');
    if (moodScoreSlider) {
        moodScoreSlider.addEventListener('input', function() {
            document.getElementById('mood-score-display').textContent = this.value;
        });
    }
    
    // Initialize mood time range slider
    initMoodTimeRangeSlider();
    
    // Fetch initial mood data
    setTimeout(() => {
        analyzeMood();
    }, 1000);
});

// Initialize the mood time range slider
function initMoodTimeRangeSlider() {
    // Calculate date ranges
    const today = new Date();
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(today.getMonth() - 3);
    
    // Format dates for display
    const formatDate = date => {
        return date.toISOString().split('T')[0]; // YYYY-MM-DD format
    };
    
    // Initialize Mood Analyzer slider
    const moodTimeRangeSlider = document.getElementById('mood-time-range-slider');
    if (moodTimeRangeSlider) {
        noUiSlider.create(moodTimeRangeSlider, {
            start: [threeMonthsAgo.getTime(), today.getTime()], // Default to past 3 months
            connect: true,
            range: {
                'min': new Date(today.getFullYear() - 2, today.getMonth(), today.getDate()).getTime(), // 2 years ago
                'max': today.getTime()
            },
            step: 24 * 60 * 60 * 1000, // One day in milliseconds
            tooltips: [
                {
                    to: value => formatDate(new Date(parseInt(value)))
                },
                {
                    to: value => formatDate(new Date(parseInt(value)))
                }
            ]
        });
        
        // Update display spans when slider values change
        moodTimeRangeSlider.noUiSlider.on('update', function(values, handle) {
            const dateStart = new Date(parseInt(values[0]));
            const dateEnd = new Date(parseInt(values[1]));
            
            document.getElementById('mood-time-range-start').textContent = 'Start: ' + formatDate(dateStart);
            document.getElementById('mood-time-range-end').textContent = 'End: ' + formatDate(dateEnd);
        });
    }
}

// Save a new mood entry
async function saveMoodEntry() {
    // Get values from form
    const date = document.getElementById('mood-date').value;
    const moodScore = parseInt(document.getElementById('mood-score').value);
    const moodNote = document.getElementById('mood-note').value;
    const tagsInput = document.getElementById('mood-tags').value;
    
    // Parse comma-separated tags and trim whitespace
    const tags = tagsInput.split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);
    
    // Validate inputs
    if (!date) {
        alert('Please select a date');
        return;
    }
    if (isNaN(moodScore) || moodScore < 1 || moodScore > 10) {
        alert('Please select a valid mood score between 1 and 10');
        return;
    }
    
    try {
        const response = await fetch('/mood/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date,
                mood_score: moodScore,
                mood_note: moodNote,
                tags: tags
            })
        });
        
        const data = await response.json();
        if (data.success) {
            // Reset form
            document.getElementById('mood-note').value = '';
            document.getElementById('mood-tags').value = '';
            document.getElementById('mood-score').value = 5;
            document.getElementById('mood-score-display').textContent = '5';
            
            // Refresh mood analysis
            analyzeMood();
            
            alert('Mood entry saved successfully!');
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving mood entry:', error);
        alert('Error saving mood entry. Please try again.');
    }
}

// Analyze mood data
async function analyzeMood() {
    try {
        // Show loading indicators
        document.getElementById('mood-stats').innerHTML = '<p>Loading statistics...</p>';
        document.getElementById('mood-entries').innerHTML = '<p>Loading entries...</p>';
        document.getElementById('moodChart').style.display = 'none';
        
        // Get date range from slider
        const moodTimeRangeSlider = document.getElementById('mood-time-range-slider');
        if (!moodTimeRangeSlider || !moodTimeRangeSlider.noUiSlider) {
            console.error('Mood time range slider not initialized');
            return;
        }
        
        const values = moodTimeRangeSlider.noUiSlider.get();
        const startDate = new Date(parseInt(values[0])).toISOString().split('T')[0];
        const endDate = new Date(parseInt(values[1])).toISOString().split('T')[0];
        
        // Fetch mood statistics
        const statsResponse = await fetch(`/mood/stats?start_date=${startDate}&end_date=${endDate}`);
        const statsData = await statsResponse.json();
        
        // Fetch mood entries
        const entriesResponse = await fetch(`/mood/entries?start_date=${startDate}&end_date=${endDate}`);
        const entriesData = await entriesResponse.json();
        
        // Display mood statistics
        displayMoodStats(statsData);
        
        // Display mood entries
        displayMoodEntries(entriesData.entries);
        
        // Create mood chart
        createMoodChart(statsData.mood_trend);
    } catch (error) {
        console.error('Error analyzing mood:', error);
        document.getElementById('mood-stats').innerHTML = '<p class="error">Error loading mood data</p>';
        document.getElementById('mood-entries').innerHTML = '';
    }
}

// Display mood statistics
function displayMoodStats(stats) {
    const statsContainer = document.getElementById('mood-stats');
    
    if (!stats.avg_mood && stats.top_tags.length === 0) {
        statsContainer.innerHTML = '<p>No mood data available for selected period</p>';
        return;
    }
    
    let html = '<div style="background:#f7f7fa;padding:15px;border-radius:8px;">';
    
    // Average mood
    const avgMood = stats.avg_mood ? parseFloat(stats.avg_mood).toFixed(1) : 'N/A';
    html += `<div style="margin-bottom:10px;">
        <h4 style="margin:0 0 5px 0;font-size:1rem;">Average Mood Score</h4>
        <div style="font-size:1.8rem;font-weight:bold;color:#2196f3;">${avgMood}</div>
    </div>`;
    
    // Top mentioned tags
    if (stats.top_tags && stats.top_tags.length > 0) {
        html += `<div>
            <h4 style="margin:0 0 5px 0;font-size:1rem;">Most Common Tags</h4>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">`;
        
        stats.top_tags.forEach(([tag, count]) => {
            html += `<span style="background:#e1f5fe;color:#0277bd;padding:4px 8px;border-radius:4px;font-size:0.9rem;">${tag} (${count})</span>`;
        });
        
        html += `</div>
        </div>`;
    }
    
    html += '</div>';
    statsContainer.innerHTML = html;
}

// Display mood entries list
function displayMoodEntries(entries) {
    const entriesContainer = document.getElementById('mood-entries');
    
    if (!entries || entries.length === 0) {
        entriesContainer.innerHTML = '<p>No mood entries found for selected period</p>';
        return;
    }
    
    let html = '<h4 style="margin:0 0 10px 0;font-size:1rem;">Mood Entries</h4>';
    
    entries.forEach(entry => {
        // Parse tags from JSON string
        let tags = [];
        try {
            tags = JSON.parse(entry.tags || '[]');
        } catch (e) {
            console.warn('Failed to parse tags:', e);
        }
        
        // Create a badge color based on mood score
        let badgeColor = '#64b5f6'; // Default blue
        if (entry.mood_score >= 8) badgeColor = '#66bb6a'; // Green for high scores
        else if (entry.mood_score <= 3) badgeColor = '#ef5350'; // Red for low scores
        else if (entry.mood_score <= 5) badgeColor = '#ffa726'; // Orange for medium-low scores
        
        html += `
        <div style="margin-bottom:10px;padding:12px;border:1px solid #eee;border-radius:6px;background:#fafafa;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div style="font-weight:bold;">${entry.date}</div>
                <div style="background:${badgeColor};color:white;padding:2px 8px;border-radius:12px;font-weight:bold;">${entry.mood_score}</div>
            </div>
            ${entry.mood_note ? `<div style="margin-bottom:8px;white-space:pre-line;">${entry.mood_note}</div>` : ''}
            ${tags.length > 0 ? `
                <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">
                    ${tags.map(tag => `<span style="background:#e1f5fe;color:#0277bd;padding:2px 6px;border-radius:4px;font-size:0.85rem;">${tag}</span>`).join('')}
                </div>
            ` : ''}
            <div style="text-align:right;margin-top:8px;">
                <button onclick="deleteMoodEntry(${entry.id})" style="background:none;border:none;color:#f44336;cursor:pointer;font-size:0.85rem;">Delete</button>
            </div>
        </div>
        `;
    });
    
    entriesContainer.innerHTML = html;
}

// Create mood trend chart
function createMoodChart(moodTrend) {
    if (!moodTrend || moodTrend.length === 0) {
        document.getElementById('moodChart').style.display = 'none';
        return;
    }
    
    const labels = moodTrend.map(item => item[0]);
    const data = moodTrend.map(item => item[1]);
    
    const ctx = document.getElementById('moodChart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.moodChartInstance) {
        window.moodChartInstance.destroy();
    }
    
    window.moodChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mood Score',
                data: data,
                borderColor: '#ff69b4',
                backgroundColor: 'rgba(255, 105, 180, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointBackgroundColor: '#ff69b4',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    min: 0,
                    max: 10,
                    title: {
                        display: true,
                        text: 'Mood Score'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    titleColor: '#333',
                    bodyColor: '#333',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].label;
                        },
                        label: function(context) {
                            return `Mood Score: ${context.raw}`;
                        }
                    }
                }
            }
        }
    });
    
    document.getElementById('moodChart').style.display = 'block';
}

// Delete a mood entry
async function deleteMoodEntry(id) {
    if (!confirm('Are you sure you want to delete this mood entry?')) {
        return;
    }
    
    try {
        const response = await fetch(`/mood/delete/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            // Refresh mood analysis
            analyzeMood();
            alert('Mood entry deleted successfully');
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting mood entry:', error);
        alert('Error deleting mood entry. Please try again.');
    }
}

// Predict Tomorrow's Move (ML Feature)
async function predictStockMove() {
    // Use the currently selected stock and its closes
    const select = document.getElementById('stock-select');
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);
    if (selected.length !== 1) {
        alert('Select exactly one stock for prediction.');
        return;
    }
    const stockData = stockTrendsData[selected[0]];
    if (!stockData || !stockData.closes || stockData.closes.length < 7) {
        alert('Not enough data for prediction.');
        return;
    }
    // Get the filtered data and labels from the chart (not mutated)
    const chart = stockCharts['stockChartMulti'];
    let basePrices, baseLabels;
    if (chart) {
        const datasetIdx = chart.data.datasets.findIndex(ds => ds.label.startsWith(stockData.name));
        if (datasetIdx !== -1) {
            basePrices = chart.data.datasets[datasetIdx].data.slice();
            baseLabels = chart.data.labels.slice();
        } else {
            basePrices = stockData.closes.slice();
            baseLabels = stockData.dates.slice();
        }
    } else {
        basePrices = stockData.closes.slice();
        baseLabels = stockData.dates.slice();
    }
    const daysInput = document.getElementById('predict-days');
    let daysAhead = 1;
    if (daysInput) {
        daysAhead = Math.max(1, Math.min(30, parseInt(daysInput.value) || 1));
    }
    const factorInput = document.getElementById('predict-factor');
    const manualFactor = factorInput ? factorInput.value : '';
    document.getElementById('stock-move-prediction').innerText = 'Predicting...';

    // Remove previous prediction overlays
    if (chart) {
        chart.data.datasets.forEach(ds => {
            ds.segment = undefined;
            ds.pointRadius = undefined;
            ds.pointBackgroundColor = undefined;
            ds.pointBorderColor = undefined;
            ds.pointBorderWidth = undefined;
        });
        if (chart.options.plugins &&
            chart.options.plugins.annotation &&
            chart.options.plugins.annotation.annotations) {
            delete chart.options.plugins.annotation.annotations['predictedLabel'];
        }
    }

    // Chain predictions for each day ahead
    let predPrices = basePrices.slice();
    let predLabels = baseLabels.slice();
    let predResults = [];
    for (let i = 0; i < daysAhead; i++) {
        const res = await fetch('/predict/stock-move', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prices: predPrices, window: 5, factor: manualFactor})
        });
        const data = await res.json();
        if (data.error) {
            document.getElementById('stock-move-prediction').innerText = data.error;
            return;
        }
        predResults.push(data);
        // Predict next value (use 1% move for visualization)
        const lastPrice = predPrices[predPrices.length-1];
        const predUp = data.prob_up > data.prob_down;
        const predChange = lastPrice * 0.01 * (predUp ? 1 : -1);
        const predictedPrice = lastPrice + predChange;
        predPrices.push(predictedPrice);
        // Add new label (next day)
        let lastDate = predLabels[predLabels.length-1];
        let nextDate;
        if (/\d{4}-\d{2}-\d{2}/.test(lastDate)) {
            const d = new Date(lastDate);
            d.setDate(d.getDate() + 1);
            nextDate = d.toISOString().split('T')[0];
        } else {
            nextDate = 'Predicted ' + (i+1);
        }
        predLabels.push(nextDate);
    }
    // Show prediction summary
    const lastResult = predResults[predResults.length-1];
    let factorLabel = '';
    if (manualFactor) {
        const factorMap = {
            covid: 'COVID-19 Pandemic',
            ukraine_war: 'Russia-Ukraine War',
            us_china_trade: 'US-China Trade War',
            tech_layoffs: 'Major Tech Layoffs',
            rate_hike: 'US Interest Rate Hike',
            bank_crisis: 'Banking Crisis',
            ai_boom: 'AI Boom',
            debt_ceiling: 'US Debt Ceiling Crisis',
            inflation: 'Inflation Surge',
            supply_chain: 'Supply Chain Crisis',
            rate_cut: 'Fed Rate Cut',
            stimulus: 'Major Stimulus Package',
            med_breakthrough: 'Breakthrough Medical News',
            peace_treaty: 'Peace Treaty Signed',
            tech_breakthrough: 'Tech Breakthrough',
            jobs_report: 'Strong Jobs Report',
            record_earnings: 'Record Corporate Earnings',
            trade_deal: 'Trade Deal Signed',
            inflation_drop: 'Inflation Drops Sharply',
            tax_cut: 'Major Tax Cut',
            recovery: 'Global Economic Recovery',
            confidence_surge: 'Consumer Confidence Surge'
        };
        factorLabel = ` (Factor: ${factorMap[manualFactor] || manualFactor})`;
    }
    document.getElementById('stock-move-prediction').innerText =
        `Probability Up: ${(lastResult.prob_up*100).toFixed(1)}% | Down: ${(lastResult.prob_down*100).toFixed(1)}%${factorLabel}`;

    // --- Add predicted points to the chart visually only ---
    if (chart) {
        const datasetIdx = chart.data.datasets.findIndex(ds => ds.label.startsWith(stockData.name));
        if (datasetIdx === -1) return;
        const ds = chart.data.datasets[datasetIdx];
        // Use a copy for overlay
        ds.data = predPrices;
        chart.data.labels = predLabels;
        // Dotted line for predicted segment(s)
        const baseLen = basePrices.length;
        ds.segment = {
            borderDash: ctx => ctx.p0DataIndex >= baseLen-1 ? [6, 6] : undefined,
            borderColor: ctx => ctx.p0DataIndex >= baseLen-1 ? (predResults[ctx.p0DataIndex-baseLen+1]?.prob_up > predResults[ctx.p0DataIndex-baseLen+1]?.prob_down ? '#388e3c' : '#d32f2f') : ds.borderColor
        };
        // Style predicted points
        ds.pointRadius = ds.data.map((v,i) => i >= baseLen ? (i===ds.data.length-1?7:4) : 0);
        ds.pointBackgroundColor = ds.data.map((v,i) => i >= baseLen ? (predResults[i-baseLen]?.prob_up > predResults[i-baseLen]?.prob_down ? '#388e3c' : '#d32f2f') : 'rgba(0,0,0,0)');
        ds.pointBorderColor = ds.pointBackgroundColor;
        ds.pointBorderWidth = ds.data.map((v,i) => i===ds.data.length-1?2:0);
        // Add a label annotation for the last predicted point
        if (chart.options.plugins && chart.options.plugins.annotation) {
            chart.options.plugins.annotation.annotations = chart.options.plugins.annotation.annotations || {};
            chart.options.plugins.annotation.annotations['predictedLabel'] = {
                type: 'label',
                xValue: predLabels[predLabels.length-1],
                yValue: predPrices[predPrices.length-1],
                backgroundColor: lastResult.prob_up > lastResult.prob_down ? '#388e3c' : '#d32f2f',
                color: '#fff',
                content: ['Predicted'],
                font: { weight: 'bold', size: 13 },
                position: 'center',
                padding: 6,
                borderRadius: 6,
                display: true
            };
        }
        chart.update();
    }
} 