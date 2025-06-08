console.log('main.js loaded');
// main.js - Clean, robust version for three features only

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing components...');
    // --- Time Range Slider for Stock Price Trends ---
    const timeRangeSlider = document.getElementById('time-range-slider');
    if (timeRangeSlider) {
        console.log('Initializing time range slider...');
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(today.getMonth() - 1);
        // If month subtraction goes negative, adjust year and month
        if (oneMonthAgo.getMonth() > today.getMonth()) {
            oneMonthAgo.setFullYear(oneMonthAgo.getFullYear() - 1);
            oneMonthAgo.setMonth(12 + oneMonthAgo.getMonth());
        }
        noUiSlider.create(timeRangeSlider, {
            start: [oneMonthAgo.getTime(), today.getTime()],
            connect: true,
            range: {
                'min': oneYearAgo.getTime(),
                'max': today.getTime()
            },
            step: 24 * 60 * 60 * 1000,
            tooltips: [
                { to: v => new Date(parseInt(v)).toISOString().split('T')[0] },
                { to: v => new Date(parseInt(v)).toISOString().split('T')[0] }
            ]
        });
        timeRangeSlider.noUiSlider.on('update', function(values) {
            document.getElementById('time-range-start').textContent = 'Start: ' + new Date(parseInt(values[0])).toISOString().split('T')[0];
            document.getElementById('time-range-end').textContent = 'End: ' + new Date(parseInt(values[1])).toISOString().split('T')[0];
        });
        // Set initial label values
        document.getElementById('time-range-start').textContent = 'Start: ' + oneMonthAgo.toISOString().split('T')[0];
        document.getElementById('time-range-end').textContent = 'End: ' + today.toISOString().split('T')[0];
        console.log(`Initial stock trends date range: ${oneMonthAgo.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
    } else {
        console.warn('Stock trends slider not initialized properly');
    }

    // --- Populate Stock Stability Explorer select ---
    fetch('/available_tickers')
        .then(res => res.json())
        .then(tickers => {
            const select = document.getElementById('explore-stock');
            if (select && Array.isArray(tickers)) {
                select.innerHTML = '<option value="">-- Select --</option>';
                tickers.forEach(ticker => {
                    select.innerHTML += `<option value="${ticker}">${ticker}</option>`;
                });
                console.log('Populated explore-stock dropdown with tickers:', tickers);
            }
        });

    // --- Enable/disable Stability Metric select ---
    const exploreStock = document.getElementById('explore-stock');
    const exploreMetric = document.getElementById('explore-metric');
    if (exploreStock && exploreMetric) {
        exploreStock.addEventListener('change', function() {
            exploreMetric.disabled = !this.value;
        });
    }

    const stockSelect = document.getElementById('stock-select');
    if (stockSelect && typeof Choices !== 'undefined' && !stockSelect.classList.contains('choices-initialized')) {
        new Choices(stockSelect, {
            removeItemButton: true,
            searchResultLimit: 10,
            placeholder: true,
            placeholderValue: 'Select one or more companies',
            maxItemCount: 10,
            shouldSort: false,
            position: 'auto'
        });
        stockSelect.classList.add('choices-initialized');
    }
});

// --- Market Overtime (D3 line chart with time range slider) ---
function setupMarketOvertimeSlider(dates, onChange) {
    const marketSlider = document.getElementById('market-slider');
    if (marketSlider.noUiSlider) {
        marketSlider.noUiSlider.destroy();
    }
    d3.select('#market-slider').selectAll('*').remove();
    if (!dates || dates.length === 0) return;
    const minTime = new Date(dates[0]).getTime();
    const maxTime = new Date(dates[dates.length-1]).getTime();
    const defaultStart = new Date(dates[Math.max(0, dates.length-22)]).getTime(); // ~1 month
    const defaultEnd = maxTime;
    noUiSlider.create(marketSlider, {
        start: [defaultStart, defaultEnd],
        connect: true,
        range: { min: minTime, max: maxTime },
        step: 24 * 60 * 60 * 1000,
        tooltips: [
            { to: v => new Date(parseInt(v)).toISOString().split('T')[0] },
            { to: v => new Date(parseInt(v)).toISOString().split('T')[0] }
        ]
    });
    marketSlider.noUiSlider.on('update', function(values) {
        const startIdx = dates.findIndex(d => new Date(d).getTime() >= parseInt(values[0]));
        const endIdx = dates.findIndex(d => new Date(d).getTime() >= parseInt(values[1]));
        onChange(startIdx, endIdx === -1 ? dates.length-1 : endIdx);
    });
    // Initial call
    const startIdx = dates.findIndex(d => new Date(d).getTime() >= defaultStart);
    const endIdx = dates.length-1;
    onChange(startIdx, endIdx);
}

window.fetchStockTrends = function() {
    console.log('fetchStockTrends called');
    const select = document.getElementById('stock-select');
    const symbols = Array.from(select.selectedOptions).map(opt => opt.value);
    if (!symbols.length) {
        document.getElementById('stock-trends-result').innerText = 'Please select at least one company.';
        d3.select('#d3-stock-chart').selectAll('*').remove();
        d3.select('#market-slider').selectAll('*').remove();
        return;
    }
    document.getElementById('stock-trends-result').innerText = 'Loading...';
    // Fetch up to 1 year of data
    let url = `/stocks/history?symbols=${symbols.join(',')}&days=365`;
    fetch(url)
        .then(res => res.json())
        .then(data => {
            let matchedData = {};
            symbols.forEach(symbol => {
                const key = Object.keys(data).find(k => data[k].symbol === symbol && data[k].closes && data[k].closes.length > 0);
                if (key) {
                    matchedData[key] = data[key];
                }
            });
            if (Object.keys(matchedData).length === 0) {
                document.getElementById('stock-trends-result').innerText = 'No price data available.';
                d3.select('#d3-stock-chart').selectAll('*').remove();
                d3.select('#market-slider').selectAll('*').remove();
                return;
            }
            document.getElementById('stock-trends-result').innerText = '';
            // Use the dates from the first stock for the slider
            const firstKey = Object.keys(matchedData)[0];
            const allDates = matchedData[firstKey].dates;
            setupMarketOvertimeSlider(allDates, (startIdx, endIdx) => {
                renderD3MarketOvertimeChart(matchedData, startIdx, endIdx);
            });
        })
        .catch((err) => {
            console.error('Error fetching stock trends:', err);
            document.getElementById('stock-trends-result').innerText = 'Error connecting to server.';
            d3.select('#d3-stock-chart').selectAll('*').remove();
            d3.select('#market-slider').selectAll('*').remove();
        });
};

function renderD3MarketOvertimeChart(data, startIdx, endIdx) {
    d3.select('#d3-stock-chart').selectAll('*').remove();
    const stocks = Object.keys(data);
    if (stocks.length === 0) return;
    const margin = {top: 30, right: 30, bottom: 60, left: 70};
    const chartDiv = document.getElementById('d3-stock-chart');
    // Use the parent .chart-area for height if available
    const parent = chartDiv.closest('.chart-area') || chartDiv;
    const fullWidth = parent.clientWidth || 700;
    const fullHeight = parent.clientHeight || 340;
    const width = fullWidth - margin.left - margin.right;
    const height = fullHeight - margin.top - margin.bottom;
    const svg = d3.select('#d3-stock-chart')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${fullWidth} ${fullHeight}`);
    // White background
    svg.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', fullWidth)
        .attr('height', fullHeight)
        .attr('fill', '#fff');
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    // Prepare data for line chart
    let allSeries = [];
    stocks.forEach(name => {
        const info = data[name];
        if (info.dates && info.closes) {
            allSeries.push({
                symbol: info.symbol,
                name: name,
                values: info.dates.slice(startIdx, endIdx+1).map((date, i) => ({
                    date: d3.timeParse('%Y-%m-%d')(date),
                    close: +info.closes[startIdx + i],
                    rawDate: date
                })),
                open: info.closes[startIdx],
                close: info.closes[endIdx],
                dates: info.dates.slice(startIdx, endIdx+1)
            });
        }
    });
    if (allSeries.length === 0) return;
    const x = d3.scaleTime()
        .domain([
            d3.min(allSeries, s => d3.min(s.values, d => d.date)),
            d3.max(allSeries, s => d3.max(s.values, d => d.date))
        ])
        .range([0, width]);
    const y = d3.scaleLinear()
        .domain([
            d3.min(allSeries, s => d3.min(s.values, d => d.close)),
            d3.max(allSeries, s => d3.max(s.values, d => d.close))
        ])
        .nice()
        .range([height, 0]);
    // Gridlines
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat('')
        )
        .selectAll('line')
        .attr('stroke', '#e0e0e0');
    // Axes
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSizeOuter(0))
        .selectAll('text')
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-weight', 500)
        .style('fill', '#222');
    g.append('g')
        .call(d3.axisLeft(y).tickSizeOuter(0))
        .selectAll('text')
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-weight', 500)
        .style('fill', '#222');
    // X axis label
    g.append('text')
        .attr('text-anchor', 'middle')
        .attr('x', width / 2)
        .attr('y', height + 40)
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-size', '1rem')
        .style('fill', '#444')
        .text('Date');
    // Y axis label
    g.append('text')
        .attr('text-anchor', 'middle')
        .attr('transform', `rotate(-90)`)
        .attr('x', -height / 2)
        .attr('y', -50)
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-size', '1rem')
        .style('fill', '#444')
        .text('Price');
    // Color scale
    const color = d3.scaleOrdinal(d3.schemeCategory10);
    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.close));
    // Draw lines
    allSeries.forEach((series, i) => {
        g.append('path')
            .datum(series.values)
            .attr('fill', 'none')
            .attr('stroke', color(series.symbol))
            .attr('stroke-width', 2.5)
            .attr('d', line);
        // Add label at the end of each line, shift left if near right edge
        g.append('text')
            .datum(series.values[series.values.length - 1])
            .attr('transform', d => {
                const xPos = x(d.date);
                const rightEdge = width;
                return `translate(${xPos},${y(d.close)})`;
            })
            .attr('x', function(d) {
                const xPos = x(d.date);
                const rightEdge = width;
                return (xPos > rightEdge - 40) ? -40 : 5;
            })
            .attr('dy', '0.35em')
            .style('font-size', '13px')
            .style('font-family', 'Inter, Roboto, Arial, sans-serif')
            .style('font-weight', 700)
            .style('fill', color(series.symbol))
            .text(series.symbol);
    });
    // Tooltip for line chart: show date, open, close
    const focus = g.append('g').style('display', 'none');
    focus.append('circle').attr('r', 5).attr('fill', 'black');
    focus.append('rect')
        .attr('class', 'tooltip')
        .attr('width', 140)
        .attr('height', 54)
        .attr('x', 10)
        .attr('y', -32)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('fill', '#fff')
        .attr('stroke', '#333');
    g.append('rect')
        .attr('width', width)
        .attr('height', height)
        .style('fill', 'none')
        .style('pointer-events', 'all')
        .on('mouseover', () => focus.style('display', null))
        .on('mouseout', () => focus.style('display', 'none'))
        .on('mousemove', function(event) {
            const mouse = d3.pointer(event, this);
            const xm = x.invert(mouse[0]);
            let closest, minDist = Infinity, closestSeries;
            allSeries.forEach(series => {
                series.values.forEach((d, idx) => {
                    const dist = Math.abs(d.date - xm);
                    if (dist < minDist) {
                        minDist = dist;
                        closest = d;
                        closestSeries = series;
                        closest.idx = idx;
                    }
                });
            });
            if (closest && closestSeries) {
                focus.attr('transform', `translate(${x(closest.date)},${y(closest.close)})`);
                focus.selectAll('text').remove();
                focus.append('text').attr('x', 18).attr('y', -12).text(`Date: ${closest.rawDate}`).style('font-family', 'Inter, Roboto, Arial, sans-serif').style('font-size', '13px').style('font-weight', 500);
                focus.append('text').attr('x', 18).attr('y', 4).text(`Open: ${closestSeries.open.toFixed(2)}`).style('font-family', 'Inter, Roboto, Arial, sans-serif').style('font-size', '13px').style('font-weight', 500);
                focus.append('text').attr('x', 18).attr('y', 20).text(`Close: ${closestSeries.close.toFixed(2)}`).style('font-family', 'Inter, Roboto, Arial, sans-serif').style('font-size', '13px').style('font-weight', 500);
            }
        });
}

// --- Stock Stability Explorer: D3 chart with slider ---
function renderD3StabilityChart(dates, closes, windowStart, windowEnd) {
    d3.select('#d3-stability-chart').selectAll('*').remove();
    if (!dates || !closes || dates.length === 0) return;
    const margin = {top: 30, right: 30, bottom: 60, left: 70};
    const chartDiv = document.getElementById('d3-stability-chart');
    const parent = chartDiv.closest('.chart-area') || chartDiv;
    const fullWidth = parent.clientWidth || 700;
    const fullHeight = parent.clientHeight || 340;
    const width = fullWidth - margin.left - margin.right;
    const height = fullHeight - margin.top - margin.bottom;
    const svg = d3.select('#d3-stability-chart')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${fullWidth} ${fullHeight}`);
    // White background
    svg.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', fullWidth)
        .attr('height', fullHeight)
        .attr('fill', '#fff');
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    const parseDate = d3.timeParse('%Y-%m-%d');
    const x = d3.scaleTime()
        .domain([parseDate(dates[0]), parseDate(dates[dates.length-1])])
        .range([0, width]);
    const y = d3.scaleLinear()
        .domain([d3.min(closes), d3.max(closes)])
        .nice()
        .range([height, 0]);
    // Gridlines
    g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat('')
        )
        .selectAll('line')
        .attr('stroke', '#e0e0e0');
    // Axes
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSizeOuter(0))
        .selectAll('text')
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-weight', 500)
        .style('fill', '#222');
    g.append('g')
        .call(d3.axisLeft(y).tickSizeOuter(0))
        .selectAll('text')
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-weight', 500)
        .style('fill', '#222');
    // X axis label
    g.append('text')
        .attr('text-anchor', 'middle')
        .attr('x', width / 2)
        .attr('y', height + 40)
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-size', '1rem')
        .style('fill', '#444')
        .text('Date');
    // Y axis label
    g.append('text')
        .attr('text-anchor', 'middle')
        .attr('transform', `rotate(-90)`)
        .attr('x', -height / 2)
        .attr('y', -50)
        .style('font-family', 'Inter, Roboto, Arial, sans-serif')
        .style('font-size', '1rem')
        .style('fill', '#444')
        .text('Price');
    // Draw full line
    const lineData = dates.map((d, i) => ({date: parseDate(d), close: closes[i], rawDate: d}));
    g.append('path')
        .datum(lineData)
        .attr('fill', 'none')
        .attr('stroke', '#2196f3')
        .attr('stroke-width', 2.5)
        .attr('d', d3.line()
            .x(d => x(d.date))
            .y(d => y(d.close))
        );
    // Highlight window
    if (windowStart !== undefined && windowEnd !== undefined) {
        g.append('path')
            .datum(dates.slice(windowStart, windowEnd+1).map((d, i) => ({date: parseDate(d), close: closes[windowStart + i], rawDate: d})))
            .attr('fill', 'none')
            .attr('stroke', '#ff69b4')
            .attr('stroke-width', 4)
            .attr('d', d3.line()
                .x(d => x(d.date))
                .y(d => y(d.close))
            );
    }
    // Tooltip for line chart: show date, open, close
    const focus = g.append('g').style('display', 'none');
    focus.append('circle').attr('r', 5).attr('fill', 'black');
    focus.append('rect')
        .attr('class', 'tooltip')
        .attr('width', 140)
        .attr('height', 54)
        .attr('x', 10)
        .attr('y', -32)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('fill', '#fff')
        .attr('stroke', '#333');
    g.append('rect')
        .attr('width', width)
        .attr('height', height)
        .style('fill', 'none')
        .style('pointer-events', 'all')
        .on('mouseover', () => focus.style('display', null))
        .on('mouseout', () => focus.style('display', 'none'))
        .on('mousemove', function(event) {
            const mouse = d3.pointer(event, this);
            const xm = x.invert(mouse[0]);
            // Find closest index
            let minDist = Infinity, idx = 0;
            lineData.forEach((d, i) => {
                const dist = Math.abs(d.date - xm);
                if (dist < minDist) {
                    minDist = dist;
                    idx = i;
                }
            });
            const d = lineData[idx];
            if (d) {
                focus.attr('transform', `translate(${x(d.date)},${y(d.close)})`);
                // Open = first price in window, Close = last price in window
                const open = closes[windowStart];
                const close = closes[windowEnd];
                focus.selectAll('text').remove();
                focus.append('text').attr('x', 18).attr('y', -12).text(`Date: ${dates[idx]}`).style('font-family', 'Inter, Roboto, Arial, sans-serif').style('font-size', '13px').style('font-weight', 500);
                focus.append('text').attr('x', 18).attr('y', 4).text(`Open: ${open.toFixed(2)}`).style('font-family', 'Inter, Roboto, Arial, sans-serif').style('font-size', '13px').style('font-weight', 500);
                focus.append('text').attr('x', 18).attr('y', 20).text(`Close: ${close.toFixed(2)}`).style('font-family', 'Inter, Roboto, Arial, sans-serif').style('font-size', '13px').style('font-weight', 500);
            }
        });
}

// --- Stock Stability Explorer logic ---
window.fetchAndShowExploreCard = function() {
    const stock = document.getElementById('explore-stock').value;
    const metric = document.getElementById('explore-metric').value;
    const days = document.getElementById('explore-range').value;
    const windowSize = parseInt(document.getElementById('explore-window').value);
    if (!stock) {
        document.getElementById('explore-card').innerText = 'Please select a stock.';
        d3.select('#d3-stability-chart').selectAll('*').remove();
        d3.select('#stability-slider').selectAll('*').remove();
        return;
    }
    document.getElementById('explore-card').innerText = 'Loading...';
    fetch(`/stocks/history?symbols=${stock}&days=${days}`)
        .then(res => res.json())
        .then(data => {
            // Find the correct key
            const key = Object.keys(data).find(k => data[k].symbol === stock && data[k].closes && data[k].closes.length > 0);
            if (!key) {
                document.getElementById('explore-card').innerText = 'No data available.';
                d3.select('#d3-stability-chart').selectAll('*').remove();
                d3.select('#stability-slider').selectAll('*').remove();
                return;
            }
            const info = data[key];
            const closes = info.closes;
            const dates = info.dates;
            // Default window: last windowSize days
            let windowEnd = closes.length - 1;
            let windowStart = Math.max(0, windowEnd - windowSize + 1);
            renderD3StabilityChart(dates, closes, windowStart, windowEnd);
            // Add slider
            d3.select('#stability-slider').selectAll('*').remove();
            const sliderDiv = document.getElementById('stability-slider');
            if (sliderDiv.noUiSlider) {
                sliderDiv.noUiSlider.destroy();
            }
            noUiSlider.create(sliderDiv, {
                start: [windowStart, windowEnd],
                connect: true,
                range: { min: 0, max: closes.length - 1 },
                step: 1,
                tooltips: [true, true],
                format: {
                    to: v => Math.round(v),
                    from: v => Math.round(v)
                }
            });
            sliderDiv.noUiSlider.on('update', function(values) {
                windowStart = Number(values[0]);
                windowEnd = Number(values[1]);
                if (windowEnd - windowStart < 1) return;
                renderD3StabilityChart(dates, closes, windowStart, windowEnd);
                // Calculate and show stability metric
                let score = 0;
                if (metric === 'meanabs' || metric === 'maxmeanabs') {
                    const windowPrices = closes.slice(windowStart, windowEnd+1);
                    score = windowPrices.length > 1 ? windowPrices.slice(1).reduce((acc, v, i) => acc + Math.abs(v - windowPrices[i]), 0) / (windowPrices.length-1) : 0;
                } else {
                    const windowPrices = closes.slice(windowStart, windowEnd+1);
                    const changes = windowPrices.slice(1).map((v,i)=>v-windowPrices[i]);
                    score = changes.length > 0 ? Math.sqrt(changes.reduce((acc, v) => acc + v*v, 0) / changes.length) : 0;
                }
                document.getElementById('explore-card').innerHTML = `<b>Stability Score:</b> ${score.toFixed(4)}<br><b>Window:</b> ${dates[windowStart]} ~ ${dates[windowEnd]}`;
            });
            // Initial metric
            sliderDiv.noUiSlider.set([windowStart, windowEnd]);
        })
        .catch(() => {
            document.getElementById('explore-card').innerText = 'Error connecting to server.';
            d3.select('#d3-stability-chart').selectAll('*').remove();
            d3.select('#stability-slider').selectAll('*').remove();
        });
};

window.resetExplorerSection = function() {
    document.getElementById('explore-stock').selectedIndex = 0;
    document.getElementById('explore-card').innerText = '';
    document.getElementById('auto-stability-explanation').innerText = '';
};

// --- AI Poetry Generator ---
window.generatePoem = function() {
    const term = document.getElementById('poetry-term').value.trim();
    if (!term) {
        document.getElementById('poetry-result').innerText = 'Please enter a word or phrase.';
        return;
    }
    document.getElementById('poetry-result').innerText = 'Generating...';
    fetch('/poetry/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ term })
    })
    .then(res => res.json())
    .then(data => {
        if (data.poem) {
            document.getElementById('poetry-result').innerText = data.poem.join('\n');
            document.getElementById('poetry-attribution').innerText = data.source || '';
        } else {
            document.getElementById('poetry-result').innerText = data.error || 'Error generating poem.';
            document.getElementById('poetry-attribution').innerText = '';
        }
    })
    .catch(() => {
        document.getElementById('poetry-result').innerText = 'Error connecting to server.';
        document.getElementById('poetry-attribution').innerText = '';
    });
};
  