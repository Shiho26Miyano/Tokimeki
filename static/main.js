// Custom JavaScript moved from index.html
async function fetchStockTrends() {
    document.getElementById('stock-trends-result').innerText = 'Loading...';
    document.getElementById('stockChartMulti').style.display = 'none';
    const select = document.getElementById('stock-select');
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);
    let url = '/stocks/history';
    if (selected.length > 0) {
        url += '?symbols=' + selected.join(',');
    }
    try {
        const res = await fetch(url);
        const data = await res.json();
        let msg = '';
        let chartData = [];
        let chartLabels = [];
        let first = true;
        let statsTable = '<table style="width:100%;margin-top:10px;font-size:0.98rem;text-align:center;border-collapse:collapse;"><tr><th>Stock</th><th>Open</th><th>High</th><th>Low</th><th>Close</th></tr>';
        let summaryMsg = '';
        for (const [name, info] of Object.entries(data)) {
            if (info.dates && info.closes) {
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
                msg += `<b>${name} (${info.symbol}):</b> ${info.error}<br>`;
            }
        }
        statsTable += '</table>';
        if (chartData.length > 0) {
            const scaleType = document.getElementById('scale-select').value;
            renderStockMultiChart('stockChartMulti', chartLabels, chartData, scaleType);
            document.getElementById('stockChartMulti').style.display = 'block';
        }
        document.getElementById('stock-trends-result').innerHTML = summaryMsg + msg + statsTable;
    } catch (e) {
        document.getElementById('stock-trends-result').innerText = 'Failed to fetch stock trends.';
    }
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
function renderStockMultiChart(canvasId, labels, datasets, scaleType='linear') {
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
            plugins: {
                legend: { display: true, position: 'top', labels: { font: { size: 15 } } },
                title: { display: true, text: 'Stock Price Trend (Past 1 Month)', font: { size: 18 } },
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
    let url = '/stocks/maxchange';
    if (selected.length > 0) {
        url += '?symbols=' + selected.join(',');
    }
    try {
        const res = await fetch(url);
        const data = await res.json();
        let table = `<table style='width:100%;margin-top:10px;font-size:0.97rem;text-align:center;border-collapse:collapse;'><tr><th>Rank</th><th>Stock</th><th>Max Abs Change</th><th>Start Date</th><th>End Date</th><th>Start Price</th><th>End Price</th></tr>`;
        data.forEach((item, idx) => {
            if (item.max_abs_sum !== undefined) {
                table += `<tr><td>${idx+1}</td><td>${item.name} (${item.symbol})</td><td>${item.max_abs_sum.toFixed(2)}</td><td>${item.start_date}</td><td>${item.end_date}</td><td>${item.start_price.toFixed(2)}</td><td>${item.end_price.toFixed(2)}</td></tr>`;
            } else {
                table += `<tr><td colspan='7'>${item.name} (${item.symbol}): ${item.error}</td></tr>`;
            }
        });
        table += '</table>';
        document.getElementById('maxchange-result').innerHTML = table;
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
    document.getElementById('lc-result').innerText = 'Calculating...';
    try {
        const res = await fetch('/leetcode/stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.error) {
            document.getElementById('lc-result').innerText = data.error;
        } else {
            lcLastResult = data;
            setLcCodeLang(lcCodeLang); // Show selected code
        }
    } catch (e) {
        document.getElementById('lc-result').innerText = 'Failed to calculate.';
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
    try {
        const res = await fetch(url);
        const data = await res.json();
        let cardsHtml = '';
        data.forEach((item, idx) => {
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
                <div style='display:flex;flex-wrap:nowrap;align-items:stretch;gap:0;margin-bottom:28px;background:#fafbfc;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);padding:18px 0;max-width:700px;margin-left:auto;margin-right:auto;'>
                    <div style='flex:1 1 220px;min-width:180px;max-width:260px;display:flex;flex-direction:column;justify-content:center;padding:0 24px 0 24px;'>
                        <div id='${infoId}'>
                            <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                            <div style='margin-bottom:4px;'><b>Start:</b> ${item.start_date} <b>End:</b> ${item.end_date}</div>
                            <div style='margin-bottom:4px;'><b>Stability Score:</b> ${item.stability_score.toFixed(4)}</div>
                            <div style='margin-bottom:4px;'><b>Metric:</b> ${item.metric === 'meanabs' ? 'Lowest Mean Absolute Change' : 'Lowest Standard Deviation'}</div>
                            <div style='margin-bottom:4px;font-size:0.97em;color:#888;'>Window Prices: [${item.window_prices.map(x=>x.toFixed(2)).join(', ')}]</div>
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
            } else {
                cardsHtml += `<div style='margin-bottom:18px;color:#c00;'>${item.name} (${item.symbol}): ${item.error}</div>`;
            }
        });
        document.getElementById('stable-cards').innerHTML = cardsHtml;
        // Render charts and slider logic
        data.forEach((item, idx) => {
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
                        <div style='margin-bottom:4px;'><b>Metric:</b> ${metric === 'meanabs' ? 'Lowest Mean Absolute Change' : 'Lowest Standard Deviation'}</div>
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
                        <div style='margin-bottom:4px;'><b>Metric:</b> ${item.metric === 'meanabs' ? 'Lowest Mean Absolute Change' : 'Lowest Standard Deviation'}</div>
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
    if (item.stability_score === undefined) {
        document.getElementById(targetId).innerHTML = `<div style='margin-bottom:18px;color:#c00;'>${item.name} (${item.symbol}): ${item.error}</div>`;
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
    let cardHtml = `
        <div style='display:flex;flex-wrap:nowrap;align-items:stretch;gap:0;margin-bottom:28px;background:#fafbfc;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);padding:18px 0;max-width:700px;margin-left:auto;margin-right:auto;'>
            <div style='flex:1 1 220px;min-width:180px;max-width:260px;display:flex;flex-direction:column;justify-content:center;padding:0 24px 0 24px;'>
                <div id='${infoId}'>
                    <div style='font-size:1.13rem;font-weight:bold;margin-bottom:6px;'>${item.name} <span style='font-size:0.98rem;color:#888;'>(${item.symbol})</span></div>
                    <div style='margin-bottom:4px;'><b>Start:</b> ${item.start_date} <b>End:</b> ${item.end_date}</div>
                    <div style='margin-bottom:4px;'><b>Stability Score:</b> ${item.stability_score.toFixed(4)}</div>
                    <div style='margin-bottom:4px;'><b>Metric:</b> ${item.metric === 'meanabs' ? 'Lowest Mean Absolute Change' : 'Lowest Standard Deviation'}</div>
                    <div style='margin-bottom:4px;font-size:0.97em;color:#888;' title='${item.window_prices.map(x=>x.toFixed(2)).join(", ") }'>Window Prices: [${formatWindowPrices(item.window_prices)}]</div>
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
    document.getElementById(targetId).innerHTML = cardHtml;
    // Chart logic
    const ctx = document.getElementById(chartId).getContext('2d');
    if (!window.myStableCharts) window.myStableCharts = {};
    window.myStableCharts[chartId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allCloses.slice(sliderStart, sliderEnd+1).map((v,i)=>i+1),
            datasets: [{
                label: 'Price',
                data: allCloses.slice(sliderStart, sliderEnd+1),
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
            <div style='margin-bottom:4px;'><b>Metric:</b> ${item.metric === 'meanabs' ? 'Lowest Mean Absolute Change' : 'Lowest Standard Deviation'}</div>
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
// Add event listener for explore-stock
window.addEventListener('DOMContentLoaded', function() {
    const exploreSelect = document.getElementById('explore-stock');
    const metricSelect = document.getElementById('stable-metric');
    const exploreMetricSelect = document.getElementById('explore-metric');
    const exploreRangeSelect = document.getElementById('explore-range');
    const exploreWindowSelect = document.getElementById('explore-window');
    function fetchAndShowExploreCard() {
        const symbol = exploreSelect.value;
        const metric = exploreMetricSelect.value;
        const days = exploreRangeSelect.value;
        const windowSize = exploreWindowSelect.value;
        if (!symbol) {
            document.getElementById('explore-card').innerHTML = '';
            return;
        }
        document.getElementById('explore-card').innerHTML = 'Loading...';
        fetch(`/stocks/stable?metric=${metric}&symbol=${symbol}&window=${windowSize}&days=${days}`)
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    renderStableCard(data[0], 0, 'explore-card', true);
                } else {
                    document.getElementById('explore-card').innerHTML = 'No data.';
                }
            })
            .catch(() => {
                document.getElementById('explore-card').innerHTML = 'Failed to fetch.';
            });
    }
    function fetchAndShowExploreCardWrapper() {
        // Only fetch if metric is enabled and selected
        if (!exploreMetricSelect.disabled && exploreMetricSelect.value) {
            fetchAndShowExploreCard();
        } else {
            document.getElementById('explore-card').innerHTML = '';
        }
    }
    exploreSelect.addEventListener('change', function() {
        updateExploreMetricState();
        fetchAndShowExploreCardWrapper();
    });
    exploreRangeSelect.addEventListener('change', function() {
        updateExploreMetricState();
        fetchAndShowExploreCardWrapper();
    });
    exploreWindowSelect.addEventListener('change', function() {
        updateExploreMetricState();
        fetchAndShowExploreCardWrapper();
    });
    exploreMetricSelect.addEventListener('change', fetchAndShowExploreCardWrapper);
    // Initial state
    updateExploreMetricState();
    metricSelect.addEventListener('change', function() {
        if (exploreSelect.value) fetchAndShowExploreCard();
    });
    fetch('/available_tickers').then(res => res.json()).then(tickers => {
        populateDropdown('stock-select', tickers);
        populateDropdown('maxchange-stock-select', tickers);
        populateDropdown('explore-stock', tickers, true);
    });
});
function formatWindowPrices(windowPrices) {
    if (windowPrices.length <= 5) {
        return windowPrices.map(x => x.toFixed(2)).join(', ');
    } else {
        return `${windowPrices[0].toFixed(2)}, ${windowPrices[1].toFixed(2)}, ..., ${windowPrices[windowPrices.length-2].toFixed(2)}, ${windowPrices[windowPrices.length-1].toFixed(2)}`;
    }
}
// Add logic to enable/disable metric dropdown in Stock Stability Explorer
function updateExploreMetricState() {
    const stock = document.getElementById('explore-stock').value;
    const range = document.getElementById('explore-range').value;
    const windowSize = document.getElementById('explore-window').value;
    const metricSelect = document.getElementById('explore-metric');
    if (stock && range && windowSize) {
        metricSelect.disabled = false;
    } else {
        metricSelect.disabled = true;
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
    tickers.forEach(t => {
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