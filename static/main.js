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
            document.getElementById('lc-result').innerHTML =
                `<b>Result:</b> ${data.result}<br><br>` +
                `<b>Python Code:</b><br><pre style='background:#f7f7f7;padding:10px;border-radius:6px;overflow-x:auto;'>${data.code}</pre>` +
                `<b>Time Complexity:</b> ${data.time_complexity}<br>` +
                `<b>Space Complexity:</b> ${data.space_complexity}<br>` +
                `<b>Explanation:</b> ${data.explanation}`;
        }
    } catch (e) {
        document.getElementById('lc-result').innerText = 'Failed to calculate.';
    }
}
// Initialize input visibility
updateLcInputs(); 