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
    // Auto-fetch charts when companies or metric/range/window are changed
    if (stockSelect) {
        stockSelect.addEventListener('change', function() {
            window.fetchStockTrends();
        });
    }
    
    // Auto-fetch volatility analysis when volatility stock selector changes
    const volatilityStockSelect = document.getElementById('volatility-stock-select');
    if (volatilityStockSelect) {
        volatilityStockSelect.addEventListener('change', function() {
            fetchAndRenderVolatilityCorrelation();
        });
    }
    const metricSelect = document.getElementById('metric-select');
    const rangeSelect = document.getElementById('range-select');
    const windowSelect = document.getElementById('window-select');
    if (metricSelect) {
        metricSelect.addEventListener('change', function() {
            window.fetchStockTrends();
        });
    }
    if (rangeSelect) {
        rangeSelect.addEventListener('change', function() {
            window.fetchStockTrends();
        });
    }
    if (windowSelect) {
        windowSelect.addEventListener('change', function() {
            window.fetchStockTrends();
        });
    }

    // Initialize chat functionality
    document.addEventListener('DOMContentLoaded', function() {
        // ... existing code ...
    });
});

// Store last fetched data and chart state
window._marketOvertimeState = {
    data: null,
    startIdx: null,
    endIdx: null,
    windowSize: null,
    metric: null,
    yScale: 'linear',
    highlightInfo: null
};

window.fetchStockTrends = function() {
    const select = document.getElementById('stock-select');
    const symbols = Array.from(select.selectedOptions).map(opt => opt.value);
    // Default to 3 years (1095 days)
    const range = 1095;
    if (!symbols.length) {
        document.getElementById('stock-trends-result').innerText = 'Please select at least one company.';
        d3.select('#d3-stock-chart').selectAll('*').remove();
        d3.select('#market-slider').selectAll('*').remove();
        return;
    }
    document.getElementById('stock-trends-result').innerText = 'Loading...';
    let url = `/stocks/history?symbols=${symbols.join(',')}&days=${range}`;
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
            const firstKey = Object.keys(matchedData)[0];
            const allDates = matchedData[firstKey].dates;
            setupMarketOvertimeSlider(allDates, (startIdx, endIdx) => {
                window._marketOvertimeState.data = matchedData;
                window._marketOvertimeState.startIdx = startIdx;
                window._marketOvertimeState.endIdx = endIdx;
                renderD3StockHistoryChart(matchedData, startIdx, endIdx);
            });
        })
        .catch((err) => {
            console.error('Error fetching stock trends:', err);
            document.getElementById('stock-trends-result').innerText = 'Error connecting to server.';
            d3.select('#d3-stock-chart').selectAll('*').remove();
            d3.select('#market-slider').selectAll('*').remove();
        });
};

function renderD3StockHistoryChart(data, startIdx, endIdx) {
    d3.select('#d3-stock-chart').selectAll('*').remove();
    const stocks = Object.keys(data);
    if (stocks.length === 0) return;
    const margin = {top: 30, right: 30, bottom: 60, left: 70};
    const chartDiv = document.getElementById('d3-stock-chart');
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
    svg.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', fullWidth)
        .attr('height', fullHeight)
        .attr('fill', '#fff');
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
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
                closes: info.closes.slice(startIdx, endIdx+1),
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
    // Draw lines only (no highlight)
    allSeries.forEach((series, i) => {
        g.append('path')
            .datum(series.values)
            .attr('fill', 'none')
            .attr('stroke', color(series.symbol))
            .attr('stroke-width', 2.5)
            .attr('d', line);
        // Add label at the end of each line
        g.append('text')
            .datum(series.values[series.values.length - 1])
            .attr('transform', d => `translate(${x(d.date)},${y(d.close)})`)
            .attr('x', 5)
            .attr('dy', '0.35em')
            .style('font-size', '13px')
            .style('font-family', 'Inter, Roboto, Arial, sans-serif')
            .style('font-weight', 700)
            .style('fill', color(series.symbol))
            .text(series.symbol);
    });
    // --- Tooltip logic for Market Overtime ---
    const tooltip = d3.select('#d3-stock-chart')
        .append('div')
        .attr('class', 'd3-tooltip')
        .style('position', 'absolute')
        .style('background', '#fff')
        .style('border', '1px solid #183153')
        .style('border-radius', '8px')
        .style('padding', '10px 14px')
        .style('pointer-events', 'none')
        .style('font-size', '1rem')
        .style('color', '#183153')
        .style('box-shadow', '0 2px 8px rgba(24,49,83,0.13)')
        .style('display', 'none');
    svg.append('rect')
        .attr('x', margin.left)
        .attr('y', margin.top)
        .attr('width', width)
        .attr('height', height)
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .on('mousemove', function(event) {
            const [mx] = d3.pointer(event, this);
            const x0 = x.invert(mx - margin.left);
            // Find closest point across all series
            let closest = null, minDist = Infinity;
            allSeries.forEach(series => {
                series.values.forEach(d => {
                    const dist = Math.abs(d.date - x0);
                    if (dist < minDist) {
                        minDist = dist;
                        closest = { ...d, symbol: series.symbol };
                    }
                });
            });
            if (!closest) return;
            g.selectAll('.hover-dot').remove();
            g.append('circle')
                .attr('class', 'hover-dot')
                .attr('cx', x(closest.date))
                .attr('cy', y(closest.close))
                .attr('r', 6)
                .attr('fill', color(closest.symbol))
                .attr('stroke', '#183153')
                .attr('stroke-width', 2);
            let html = `<b>${d3.timeFormat('%Y-%m-%d')(closest.date)}</b><br>`;
            html += `Symbol: <b>${closest.symbol}</b><br>`;
            html += `Price: <b>${closest.close.toFixed(2)}</b>`;
            tooltip.html(html)
                .style('left', (event.offsetX + 30) + 'px')
                .style('top', (event.offsetY - 30) + 'px')
                .style('display', 'block');
        })
        .on('mouseleave', function() {
            tooltip.style('display', 'none');
            g.selectAll('.hover-dot').remove();
        });
}

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

window.resetStockTrendsSection = function() {
    // Reset all filters to default
    const stockSelect = document.getElementById('stock-select');
    if (stockSelect && stockSelect.choices) {
        stockSelect.choices.clearStore();
    } else if (stockSelect) {
        Array.from(stockSelect.options).forEach(opt => opt.selected = false);
    }
    document.getElementById('metric-select').value = 'std';
    document.getElementById('range-select').value = '1095';
    document.getElementById('window-select').value = '20';
    // Clear chart, legend, and result
    d3.select('#d3-stock-chart').selectAll('*').remove();
    d3.select('#d3-metric-chart').selectAll('*').remove();
    d3.select('#market-slider').selectAll('*').remove();
    document.getElementById('stock-trends-result').innerText = '';
    document.getElementById('market-legend').innerHTML = '';
    // Clear cache/state
    window._marketOvertimeState = {
        data: null,
        startIdx: null,
        endIdx: null,
        windowSize: null,
        metric: null,
        yScale: 'linear',
        highlightInfo: null
    };
};

// --- Event-Driven Volatility Explorer ---
window._volatilityChartState = {
    data: null,
    range: null // [startIdx, endIdx]
};

function fetchAndRenderVolatilityCorrelation() {
    // Use the selected company from #volatility-stock-select
    const stockSelect = document.getElementById('volatility-stock-select');
    if (!stockSelect || !stockSelect.value) {
        document.getElementById('volatility-correlation-chart').innerHTML = 'Please select a company above.';
        return;
    }
    const symbol = stockSelect.value;
    // Get window and years from UI
    const windowInput = document.getElementById('vol-window');
    const yearsInput = document.getElementById('vol-years');
    const regimeWindowInput = document.getElementById('regime-window');
    const windowSize = windowInput ? parseInt(windowInput.value) || 30 : 30;
    const years = yearsInput ? parseInt(yearsInput.value) || 2 : 2;
    const regimeWindow = regimeWindowInput ? parseInt(regimeWindowInput.value) || 30 : 30;
    
    const today = new Date();
    const start = new Date();
    start.setFullYear(today.getFullYear() - years);
    const start_date = start.toISOString().split('T')[0];
    const end_date = today.toISOString().split('T')[0];
    
    const chartDiv = document.getElementById('volatility-correlation-chart');
    chartDiv.innerHTML = 'Loading volatility data...';
    
    // Fetch volatility data
    fetch(`/volatility_event_correlation?symbol=${symbol}&start_date=${start_date}&end_date=${end_date}&window=${windowSize}`)
        .then(res => res.json())
        .then(data => {
            chartDiv.innerHTML = '';
            window._volatilityChartState.data = data;
            // Initialize slider to full range
            if (data.dates && data.dates.length > 0) {
                setupVolatilityRangeSlider(data.dates);
                window._volatilityChartState.range = [0, data.dates.length - 1];
            }
            renderVolatilityCorrelationChart(data);
            
            // Now fetch regime analysis
            return fetch('/volatility_regime/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    symbol: symbol, 
                    window: regimeWindow, 
                    period: `${years}y` 
                })
            });
        })
        .then(res => res.json())
        .then(regimeData => {
            if (regimeData.error) {
                console.warn('Regime analysis error:', regimeData.error);
                return;
            }
            displayRegimeAnalysis(regimeData);
        })
        .catch((err) => {
            console.error('Error:', err);
            chartDiv.innerHTML = 'Error fetching data.';
        });
}

function setupVolatilityRangeSlider(dates) {
    const slider = document.getElementById('volatility-range-slider');
    if (slider.noUiSlider) slider.noUiSlider.destroy();
    d3.select('#volatility-range-slider').selectAll('*').remove();
    if (!dates || dates.length === 0) return;
    const minTime = new Date(dates[0]).getTime();
    const maxTime = new Date(dates[dates.length-1]).getTime();
    noUiSlider.create(slider, {
        start: [minTime, maxTime],
        connect: true,
        range: { min: minTime, max: maxTime },
        step: 24 * 60 * 60 * 1000,
        tooltips: [
            { to: v => new Date(parseInt(v)).toISOString().split('T')[0] },
            { to: v => new Date(parseInt(v)).toISOString().split('T')[0] }
        ]
    });
    slider.noUiSlider.on('update', function(values) {
        const startIdx = dates.findIndex(d => new Date(d).getTime() >= parseInt(values[0]));
        let endIdx = dates.findIndex(d => new Date(d).getTime() >= parseInt(values[1]));
        if (endIdx === -1) endIdx = dates.length - 1;
        window._volatilityChartState.range = [startIdx, endIdx];
        document.getElementById('volatility-range-start').textContent = 'Start: ' + dates[startIdx];
        document.getElementById('volatility-range-end').textContent = 'End: ' + dates[endIdx];
        renderVolatilityCorrelationChart(window._volatilityChartState.data);
    });
    // Set initial label values
    document.getElementById('volatility-range-start').textContent = 'Start: ' + dates[0];
    document.getElementById('volatility-range-end').textContent = 'End: ' + dates[dates.length-1];
}

function renderVolatilityCorrelationChart(data) {
    d3.select('#volatility-correlation-chart').selectAll('*').remove();
    if (!data || !data.dates || data.dates.length === 0) return;
    const margin = {top: 30, right: 60, bottom: 60, left: 70};
    const chartDiv = document.getElementById('volatility-correlation-chart');
    const fullWidth = chartDiv.clientWidth || 700;
    const fullHeight = chartDiv.clientHeight || 340;
    const width = fullWidth - margin.left - margin.right;
    const height = fullHeight - margin.top - margin.bottom;
    const svg = d3.select('#volatility-correlation-chart')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${fullWidth} ${fullHeight}`);
    svg.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', fullWidth)
        .attr('height', fullHeight)
        .attr('fill', '#fff');
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    // Use slider range if set
    let range = window._volatilityChartState.range;
    let startIdx = 0, endIdx = data.dates.length - 1;
    if (range && Array.isArray(range)) {
        startIdx = Math.max(0, range[0]);
        endIdx = Math.min(data.dates.length - 1, range[1]);
    }
    // Slice data for visible range
    const dates = data.dates.slice(startIdx, endIdx + 1).map(d3.timeParse('%Y-%m-%d'));
    const vol = data.volatility.slice(startIdx, endIdx + 1);
    const eventTitles = (data.event_titles || []).slice(startIdx, endIdx + 1);
    // X scale
    const x = d3.scaleTime()
        .domain(d3.extent(dates))
        .range([0, width]);
    // Y scale for volatility
    const yLeft = d3.scaleLinear()
        .domain([0, d3.max(vol.filter(v => v !== null)) * 1.2])
        .range([height, 0]);
    // Draw full volatility line in blue
    const line = d3.line()
        .defined((d, i) => vol[i] !== null)
        .x((d, i) => x(dates[i]))
        .y((d, i) => yLeft(vol[i]));
    g.append('path')
        .datum(vol)
        .attr('fill', 'none')
        .attr('stroke', '#183153')
        .attr('stroke-width', 2.5)
        .attr('d', line);
    // Overlay highlight segment for lowest volatility window (same thickness as main line)
    let highlightStart = -1, highlightEnd = -1, highlightDates = [], highlightVols = [];
    let highlightLabelX, highlightLabelY, highlightLabelText;
    let highlightStartDate, highlightEndDate;
    if (data.min_vol_date && data.volatility && data.dates) {
        const windowSize = (data.volatility.length - data.volatility.filter(v => v === null).length) > 0 ? (data.volatility.findIndex(v => v !== null) + 1) : 10;
        const minIdx = data.dates.findIndex(d => d === data.min_vol_date);
        if (minIdx !== -1 && windowSize > 1) {
            highlightStart = Math.max(startIdx, minIdx - windowSize + 1);
            highlightEnd = Math.min(endIdx, minIdx);
            if (highlightEnd >= highlightStart) {
                highlightVols = vol.slice(highlightStart - startIdx, highlightEnd - startIdx + 1);
                highlightDates = dates.slice(highlightStart - startIdx, highlightEnd - startIdx + 1);
                highlightStartDate = data.dates[highlightStart];
                highlightEndDate = data.dates[highlightEnd];
                const highlightLine = d3.line()
                    .defined((d, i) => highlightVols[i] !== null)
                    .x((d, i) => x(highlightDates[i]))
                    .y((d, i) => yLeft(highlightVols[i]));
                g.append('path')
                    .datum(highlightVols)
                    .attr('fill', 'none')
                    .attr('stroke', '#ff9800')
                    .attr('stroke-width', 2.5)
                    .attr('opacity', 0.95)
                    .attr('d', highlightLine);
                // Find the horizontal center and highest point of the highlight segment
                let minY = highlightVols[0];
                let maxY = highlightVols[0];
                for (let i = 1; i < highlightVols.length; i++) {
                    if (highlightVols[i] < minY) minY = highlightVols[i];
                    if (highlightVols[i] > maxY) maxY = highlightVols[i];
                }
                // Center X between start and end of highlight segment
                let centerIdx = Math.floor((highlightDates.length - 1) / 2);
                let labelX = x(highlightDates[centerIdx]);
                let labelY = yLeft(maxY) - 40; // 40px above the highest point of the orange line
                labelX = Math.max(labelX, 60); // Clamp to left
                labelX = Math.min(labelX, width - 100); // Clamp to right
                labelY = Math.max(labelY, 20); // Clamp to top
                highlightLabelX = labelX;
                highlightLabelY = labelY;
                highlightLabelText = 'Lowest Volatility';
                // Draw background rectangle for label
                const textPadding = 4;
                const tempText = g.append('text')
                    .attr('x', highlightLabelX)
                    .attr('y', highlightLabelY)
                    .attr('font-size', '0.95rem')
                    .attr('font-weight', 700)
                    .attr('fill', '#ff9800')
                    .text(highlightLabelText);
                const textWidth = tempText.node().getBBox().width;
                const textHeight = tempText.node().getBBox().height;
                tempText.remove();
                g.append('rect')
                    .attr('x', highlightLabelX - textPadding)
                    .attr('y', highlightLabelY - textHeight + textPadding)
                    .attr('width', textWidth + 2 * textPadding)
                    .attr('height', textHeight + 2 * textPadding)
                    .attr('fill', '#fff')
                    .attr('opacity', 0.85)
                    .lower();
                g.append('text')
                    .attr('x', highlightLabelX)
                    .attr('y', highlightLabelY)
                    .attr('font-size', '0.95rem')
                    .attr('font-weight', 700)
                    .attr('fill', '#ff9800')
                    .text(highlightLabelText);
            }
        }
    }
    // Axes
    g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSizeOuter(0));
    g.append('g')
        .call(d3.axisLeft(yLeft).ticks(6))
        .append('text')
        .attr('fill', '#183153')
        .attr('x', -40)
        .attr('y', -10)
        .attr('text-anchor', 'start')
        .attr('font-size', '1rem')
        .attr('font-weight', 600)
        .text('Volatility');
    // --- Tooltip logic ---
    const tooltip = d3.select('#volatility-correlation-chart')
        .append('div')
        .attr('class', 'd3-tooltip')
        .style('position', 'absolute')
        .style('background', '#fff')
        .style('border', '1px solid #183153')
        .style('border-radius', '8px')
        .style('padding', '10px 14px')
        .style('pointer-events', 'none')
        .style('font-size', '1rem')
        .style('color', '#183153')
        .style('box-shadow', '0 2px 8px rgba(24,49,83,0.13)')
        .style('display', 'none');
    // Add invisible rect for mouse tracking
    svg.append('rect')
        .attr('x', margin.left)
        .attr('y', margin.top)
        .attr('width', width)
        .attr('height', height)
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .on('mousemove', function(event) {
            const [mx] = d3.pointer(event, this);
            const x0 = x.invert(mx - margin.left);
            let idx = d3.bisector(d => d).left(dates, x0, 1) - 1;
            idx = Math.max(0, Math.min(idx, dates.length - 1));
            if (!dates[idx]) return;
            // Highlight point
            g.selectAll('.hover-dot').remove();
            g.append('circle')
                .attr('class', 'hover-dot')
                .attr('cx', x(dates[idx]))
                .attr('cy', yLeft(vol[idx]))
                .attr('r', 6)
                .attr('fill', '#ff9800')
                .attr('stroke', '#183153')
                .attr('stroke-width', 2);
            // Tooltip content
            let html = `<b>${d3.timeFormat('%Y-%m-%d')(dates[idx])}</b><br>`;
            html += `Volatility: <b>${vol[idx] !== null ? vol[idx].toFixed(4) : 'N/A'}</b><br>`;
            // Always show the lowest volatility window date range
            if (highlightStartDate && highlightEndDate) {
                html += `<span style='color:#ff9800'><b>Lowest Volatility Window:</b><br>${highlightStartDate} to ${highlightEndDate}</span><br>`;
            }
            // Always show news titles for this date
            if (eventTitles && eventTitles[idx] && eventTitles[idx].length > 0) {
                html += '<hr style="margin:4px 0;">';
                html += '<b>News headlines:</b><ul style="margin:0 0 0 1em;padding:0;">';
                eventTitles[idx].slice(0,3).forEach(title => {
                    html += `<li>${title}</li>`;
                });
                html += '</ul>';
            }
            tooltip.html(html)
                .style('left', (event.offsetX + 30) + 'px')
                .style('top', (event.offsetY - 30) + 'px')
                .style('display', 'block');
        })
        .on('mouseleave', function() {
            tooltip.style('display', 'none');
            g.selectAll('.hover-dot').remove();
        });
}

// Function to display regime analysis results
function displayRegimeAnalysis(regimeData) {
    const resultsDiv = document.getElementById('regime-analysis-results');
    const statsDiv = document.getElementById('regime-statistics');
    const periodsDiv = document.getElementById('regime-periods');
    
    if (!resultsDiv || !statsDiv || !periodsDiv) return;
    
    resultsDiv.style.display = 'block';
    
    // Display current regime info
    const currentInfo = document.createElement('div');
    currentInfo.className = 'alert alert-info mb-3';
    currentInfo.innerHTML = `
        <strong>${regimeData.symbol} - Current Regime: </strong>
        <span class="badge bg-primary">${regimeData.current_regime}</span><br>
        <small>Current Volatility: ${regimeData.current_volatility}% | Window: ${regimeData.rolling_window} days | Period: ${regimeData.analysis_period}</small>
    `;
    resultsDiv.insertBefore(currentInfo, resultsDiv.firstChild);
    
    // Display regime statistics
    statsDiv.innerHTML = '';
    Object.entries(regimeData.regime_statistics).forEach(([regime, stats]) => {
        const getRegimeColor = (regime) => {
            switch (regime) {
                case 'Low Volatility': return '#10b981';
                case 'Medium Volatility': return '#f59e0b';
                case 'High Volatility': return '#ef4444';
                case 'Extreme Volatility': return '#7c3aed';
                default: return '#6b7280';
            }
        };
        
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-3 mb-3';
        card.innerHTML = `
            <div class="card h-100" style="border-left: 4px solid ${getRegimeColor(regime)}">
                <div class="card-body">
                    <h6 class="card-title">${regime}</h6>
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Count</small>
                            <div class="fw-bold">${stats.count}</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Avg Vol</small>
                            <div class="fw-bold">${stats.avg_volatility}%</div>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-6">
                            <small class="text-muted">Min-Max</small>
                            <div class="fw-bold">${stats.min_volatility}%-${stats.max_volatility}%</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Time %</small>
                            <div class="fw-bold">${stats.percentage_of_time}%</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        statsDiv.appendChild(card);
    });
    
    // Display regime periods
    periodsDiv.innerHTML = `
        <h6 class="mb-3">Regime Periods</h6>
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Regime</th>
                        <th>Avg Volatility</th>
                        <th>Duration (days)</th>
                    </tr>
                </thead>
                <tbody>
                    ${regimeData.regime_periods.map(period => `
                        <tr>
                            <td>${period.start_date}</td>
                            <td>${period.end_date}</td>
                            <td>${period.regime}</td>
                            <td>${period.avg_volatility}%</td>
                            <td>${period.duration_days}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

window.fetchTweetVolatilityAnalysis = function() {
    const resultDiv = document.getElementById('tweet-volatility-result');
    resultDiv.innerHTML = 'Loading HuggingFace tweet_eval sample...';
    fetch('/hf_tweeteval_sample')
        .then(res => res.json())
        .then(data => {
            resultDiv.innerHTML = `<pre style='font-size:1.05rem;color:#183153;background:#f7f7fa;padding:0.7em;border-radius:8px;'>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(err => {
            resultDiv.innerHTML = `<span style='color:#c00;'>Error: ${err}</span>`;
        });
};

// --- React Tweet Sentiment Component ---
(function() {
  const e = React.createElement;

  function TweetSentiment() {
    const [text, setText] = React.useState("");
    const [result, setResult] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [model, setModel] = React.useState("mistral-small");
    const modelExplanations = {
      "distilbert-base-uncased-finetuned-sst-2-english": "DistilBERT is a lightweight, fast transformer model fine-tuned on SST-2 for general English sentiment analysis.",
      "nreimers/TinyBERT_L-4_H-312_A-12-SST2": "TinyBERT (NReimers) is a compact transformer model fine-tuned on SST-2 for efficient English sentiment analysis.",
      "cardiffnlp/twitter-roberta-base-sentiment-latest": "Twitter-RoBERTa is a RoBERTa model specifically trained for sentiment analysis on tweets and social media text."
    };

    const placeholderText = "Today I watch a movie called Whiplash. Love the quote There are no two words in the English language more harmful than 'good job.'";

    const handleSubmit = async (ev, customText) => {
      if (ev) ev.preventDefault();
      setLoading(true);
      setError(null);
      setResult(null);
      try {
        let toAnalyze = typeof customText === 'string' ? customText : text;
        const usedPlaceholder = !toAnalyze || !toAnalyze.trim();
        if (usedPlaceholder) {
          toAnalyze = placeholderText;
        }
        const resp = await fetch("/analyze_tweet", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: toAnalyze })
        });
        if (!resp.ok) throw new Error("API error");
        const data = await resp.json();
        setResult(data);
        if (!usedPlaceholder) {
          setText(toAnalyze);
        }
      } catch (err) {
        setError("Could not analyze tweet. Try again.");
      } finally {
        setLoading(false);
      }
    };

    return e('div', { className: 'card shadow-sm p-4', style: { maxWidth: 500, margin: '0 auto' } },
      e('h3', { className: 'card-title mb-3', style: { color: '#183153' } }, 'Human Sentiment Explorer'),
      e('div', { style: { color: '#888', fontSize: '0.97em', marginBottom: '0.7em' } }, 'Model: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)'),
      e('form', { onSubmit: handleSubmit },
        e('div', { className: 'mb-3' },
          e('label', { htmlFor: 'model-select', className: 'form-label', style: { fontWeight: 500 } }, 'Choose model:'),
          e('select', {
            id: 'model-select',
            className: 'form-select',
            value: model,
            onChange: ev => setModel(ev.target.value),
            style: { maxWidth: 350, marginBottom: 8 }
          },
            e('option', { value: 'distilbert-base-uncased-finetuned-sst-2-english' }, 'DistilBERT (default)'),
            e('option', { value: 'nreimers/TinyBERT_L-4_H-312_A-12-SST2' }, 'TinyBERT (NReimers, SST-2)'),
            e('option', { value: 'cardiffnlp/twitter-roberta-base-sentiment-latest' }, 'Twitter-RoBERTa (CardiffNLP)')
          ),
          e('div', { style: { color: '#888', fontSize: '0.97em', marginTop: 2, minHeight: 24 } }, modelExplanations[model])
        ),
        e('div', { className: 'mb-3' },
          e('label', { htmlFor: 'tweet-input', className: 'form-label' }, 'Enter your sentence:'),
          e('textarea', {
            id: 'tweet-input',
            className: 'form-control',
            rows: 2,
            value: text,
            onChange: ev => setText(ev.target.value),
            placeholder: placeholderText
          })
        ),
        e('button', { type: 'submit', className: 'btn btn-dark-bbg', disabled: loading }, loading ? 'Analyzing...' : 'Analyze')
      ),
      error && e('div', { className: 'alert alert-danger mt-3' }, error),
      result && e('div', { className: 'alert alert-info mt-3' },
        e('div', null, e('b', null, 'Sentiment: '), result.label),
        e('div', null, e('b', null, 'Confidence: '), (result.confidence * 100).toFixed(1) + '%'),
        (() => {
          const match = result.explanation && result.explanation.match(/Top contributing words: (.*)\./);
          if (match && match[1]) {
            const stopwords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'of', 'for', 'with', 'is', 'it', 'this', 'that', 'these', 'those', 'as', 'by', 'from', 'be', 'are', 'was', 'were', 'word', 'words', 'i', 'you', 'he', 'she', 'they', 'we', 'me', 'my', 'your', 'his', 'her', 'their', 'our', 'so', 'do', 'does', 'did', 'not', 'no', 'yes', 'can', 'will', 'just', 'have', 'has', 'had', 'been', 'being', 'am', 'up', 'down', 'out', 'about', 'into', 'over', 'after', 'before', 'more', 'most', 'some', 'such', 'only', 'own', 'same', 'other', 'than', 'too', 'very', 's', 't', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn']);
            const words = match[1].replace(/'/g, '').split(',').map(w => w.trim()).filter(w => w && w !== '[CLS]' && !stopwords.has(w.toLowerCase()));
            if (words.length > 0) {
              const sentiment = result.label.toLowerCase();
              let reason = '';
              if (sentiment === 'positive') {
                reason = `The model thinks this is positive because it sees ${words.join(', ')} as happy or enjoyable words.`;
              } else if (sentiment === 'negative') {
                reason = `The model thinks this is negative because it sees ${words.join(', ')} as unhappy or problematic words.`;
              } else {
                reason = `The model thinks this is neutral because it sees ${words.join(', ')} as neither strongly positive nor negative.`;
              }
              return e('div', { className: 'mt-2', style: { color: '#183153', fontStyle: 'italic', fontSize: '0.98em' } }, reason);
            }
          }
          return null;
        })(),
        result.similar_example && (() => {
          // Check overlap between user input and example
          const userWords = new Set(text.toLowerCase().split(/\s+/));
          const exampleWords = new Set(result.similar_example.text.toLowerCase().split(/\s+/));
          const overlap = Array.from(userWords).filter(w => exampleWords.has(w)).length;
          if (overlap > 0) {
            return e('div', { className: 'mt-3', style: { background: '#f7f7fa', borderRadius: '8px', padding: '0.7em', border: '1px solid #e0e0e0' } },
              e('div', { style: { fontWeight: 600, color: '#183153' } }, 'Similar example from dataset:'),
              e('div', { style: { color: '#222', marginTop: '0.2em' } }, `"${result.similar_example.text}"`),
              e('div', { style: { color: '#888', fontSize: '0.97em', marginTop: '0.1em' } }, `Label: ${result.similar_example.label}`)
            );
          }
          return null;
        })()
      )
    );
  }

  const root = document.getElementById('react-tweet-sentiment');
  if (root && window.React && window.ReactDOM) {
    ReactDOM.createRoot(root).render(React.createElement(TweetSentiment));
  }
})();

// Hedge Fund Signal Tool Component
(function() {
  const e = React.createElement;

  function HedgeFundTool() {
    const [companies, setCompanies] = React.useState([]);
    const [symbol, setSymbol] = React.useState('');
    const [strategy, setStrategy] = React.useState('trend');
    const [period, setPeriod] = React.useState('1y');
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState(null);
    const [error, setError] = React.useState(null);

    // Fetch companies and run initial analysis
    React.useEffect(() => {
      fetch('/available_companies')
        .then(res => {
          if (!res.ok) {
            throw new Error(`Server responded with ${res.status}`);
          }
          return res.json();
        })
        .then(data => {
          if (Array.isArray(data) && data.length > 0) {
            setCompanies(data);
            const initialSymbol = data.find(c => c.symbol === 'AAPL') ? 'AAPL' : data[0].symbol;
            setSymbol(initialSymbol);
            // Trigger analysis with the initial symbol
            handleAnalyze(null, { symbol: initialSymbol, strategy: 'trend', period: '1y' });
          } else {
            setError('Could not fetch company list.');
          }
        })
        .catch(() => setError('Could not fetch company list.'));
    }, []); // Empty dependency array means this runs once on mount

    const strategies = [
      { value: 'trend', label: 'Trend Following' },
      { value: 'mean_reversion', label: 'Mean Reversion' },
      { value: 'momentum', label: 'Momentum' }
    ];

    const periods = [
      { value: '3mo', label: '3M' },
      { value: '6mo', label: '6M' },
      { value: '1y', label: '1Y' },
      { value: '2y', label: '2Y' },
      { value: '5y', label: '5Y' }
    ];
    
    const popularSymbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'];

    const handleAnalyze = async (ev, manualParams) => {
      if (ev) ev.preventDefault();
      const params = manualParams || { symbol: symbol.toUpperCase(), strategy, period };
      if (!params.symbol) return;

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const resp = await fetch('/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        });
        
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Analysis failed');
        setResult(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    const getSignalClass = (signal) => {
      if (signal === 1) return 'signal-buy';
      if (signal === -1) return 'signal-sell';
      return 'signal-hold';
    };

    const getSignalText = (signal) => {
      if (signal === 1) return 'BUY';
      if (signal === -1) return 'SELL';
      return 'HOLD';
    };

    const Metric = ({ title, value, isPercentage = false }) => {
      const numValue = parseFloat(value);
      const colorClass = isNaN(numValue) ? '' : (numValue >= 0 ? 'text-success' : 'text-danger');
      return e('div', { className: 'metric' },
        e('div', { className: 'metric-title' }, title),
        e('div', { className: `metric-value ${colorClass}` }, `${value}${isPercentage ? '%' : ''}`)
      );
    };

    return e('div', { className: 'hedge-fund-tool' },
      e('style', null, `
        .hedge-fund-tool { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .hf-header { margin-bottom: 20px; }
        .hf-header h2 { font-size: 22px; font-weight: 600; color: #1a202c; }
        .hf-header p { font-size: 15px; color: #718096; }
        .hf-controls { display: flex; gap: 16px; align-items: flex-end; margin-bottom: 20px; flex-wrap: wrap; }
        .hf-control-group { flex: 1; min-width: 120px; }
        .hf-control-group label { font-weight: 500; font-size: 14px; margin-bottom: 6px; color: #4a5568; }
        .hf-control-group .form-control, .hf-control-group .form-select { font-size: 15px; }
        .hf-symbol-pills { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
        .hf-symbol-pills span { background: #edf2f7; color: #4a5568; font-size: 12px; padding: 4px 8px; border-radius: 12px; cursor: pointer; transition: all 0.2s; }
        .hf-symbol-pills span:hover { background: #e2e8f0; }
        .hf-analyze-btn { font-weight: 500; padding: 10px 20px; font-size: 15px; }
        
        .hf-results { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; align-items: start; }
        .hf-signal-card { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; text-align: center; }
        .hf-signal-card .signal-title { font-size: 14px; font-weight: 500; color: #718096; margin-bottom: 12px; }
        .signal-badge { font-size: 24px; font-weight: 700; padding: 8px 24px; border-radius: 8px; color: #fff; }
        .signal-buy { background: #2f855a; box-shadow: 0 4px 14px rgba(47, 133, 90, 0.3); }
        .signal-sell { background: #c53030; box-shadow: 0 4px 14px rgba(197, 48, 48, 0.3); }
        .signal-hold { background: #718096; box-shadow: 0 4px 14px rgba(113, 128, 150, 0.3); }
        .signal-price { font-size: 18px; font-weight: 500; color: #2d3748; margin-top: 12px; }
        .signal-date { font-size: 13px; color: #a0aec0; margin-top: 4px; }

        .hf-metrics-card { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; }
        .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .metric { text-align: center; }
        .metric-title { font-size: 14px; color: #718096; margin-bottom: 4px; }
        .metric-value { font-size: 20px; font-weight: 600; }
        .hf-summary { margin-top: 20px; font-size: 14px; background: #ebf8ff; color: #1c3d5a; border-radius: 8px; padding: 12px; }

        @media (max-width: 768px) {
          .hf-results { grid-template-columns: 1fr; }
          .hf-controls { flex-direction: column; align-items: stretch; }
        }
      `),
      
      e('div', { className: 'hf-header' },
        e('h2', null, 'Trading Strategy Backtester'),
        e('p', null, 'Analyze stock performance using technical trading strategies.')
      ),

      e('div', {
        className: 'alert alert-warning',
        role: 'alert',
        style: { fontSize: '14px', padding: '10px 15px', marginTop: '0', marginBottom: '20px' }
      }, 'This project is for educational and research purposes only.'),

      e('form', { className: 'hf-controls', onSubmit: handleAnalyze },
        e('div', { className: 'hf-control-group', style: { flex: '1.5' } },
          e('label', { htmlFor: 'hf-symbol' }, 'Company'),
          e('select', { 
            id: 'hf-symbol', 
            className: 'form-select', 
            value: symbol, 
            onChange: ev => setSymbol(ev.target.value) 
          },
            companies.map(company => e('option', { key: company.symbol, value: company.symbol }, `${company.name} (${company.symbol})`))
          ),
          e('div', { className: 'hf-symbol-pills' }, 
            popularSymbols.map(s => e('span', { key: s, onClick: () => setSymbol(s) }, s))
          )
        ),
        e('div', { className: 'hf-control-group' },
          e('label', { htmlFor: 'hf-strategy' }, 'Strategy'),
          e('select', { id: 'hf-strategy', className: 'form-select', value: strategy, onChange: ev => setStrategy(ev.target.value) },
            strategies.map(s => e('option', { key: s.value, value: s.value }, s.label))
          )
        ),
        e('div', { className: 'hf-control-group' },
          e('label', { htmlFor: 'hf-period' }, 'Period'),
          e('select', { id: 'hf-period', className: 'form-select', value: period, onChange: ev => setPeriod(ev.target.value) },
            periods.map(p => e('option', { key: p.value, value: p.value }, p.label))
          )
        ),
        e('button', { type: 'submit', className: 'btn btn-primary hf-analyze-btn', disabled: loading || !symbol }, loading ? 'Analyzing...' : 'Analyze')
      ),

      error && e('div', { className: 'alert alert-danger' }, error),

      loading && !result && e('div', { className: 'text-center p-5' }, e('div', { className: 'spinner-border', role: 'status' })),

      result && e('div', { className: 'hf-results' },
        e('div', { className: 'hf-signal-card' },
          e('div', { className: 'signal-title' }, 'Latest Signal'),
          e('div', { className: `signal-badge ${getSignalClass(result.latest_signals.signal)}` }, getSignalText(result.latest_signals.signal)),
          e('div', { className: 'signal-price' }, `$${result.latest_signals.price.toFixed(2)}`),
          e('div', { className: 'signal-date' }, `as of ${result.latest_signals.date}`)
        ),
        e('div', { className: 'hf-metrics-card' },
          e('div', { className: 'metrics-grid' },
            Metric({ title: 'Total Return', value: result.metrics.total_return }),
            Metric({ title: 'Sharpe Ratio', value: result.metrics.sharpe_ratio }),
            Metric({ title: 'Max Drawdown', value: result.metrics.max_drawdown }),
            Metric({ title: 'Value at Risk (95%)', value: result.metrics.var_95 })
          ),
          e('div', { className: 'hf-summary' },
            `Backtest for `, e('strong', null, `${result.symbol}`), ` using a `, e('strong', null, `${strategy.replace('_', ' ')}`), ` strategy over the past `, e('strong', null, `${period}.`)
          )
        )
      )
    );
  }

  const root = document.getElementById('react-hedge-fund-tool');
  if (root && window.React && window.ReactDOM) {
    ReactDOM.createRoot(root).render(React.createElement(HedgeFundTool));
  }
})();

// Investment Playbooks Tool Component
(function() {
  const e = React.createElement;

  function InvestmentPlaybooksTool() {
    const [playbooks, setPlaybooks] = React.useState([]);
    const [companies, setCompanies] = React.useState([]);
    const [selectedPlaybook, setSelectedPlaybook] = React.useState('');
    const [symbol, setSymbol] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState(null);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
      fetch('/playbooks')
        .then(res => {
          if (!res.ok) throw new Error(`Server responded with ${res.status}`);
          return res.json();
        })
        .then(data => {
          if (Array.isArray(data)) {
            setPlaybooks(data);
            if (data.length > 0) setSelectedPlaybook(data[0].name);
          } else {
            throw new Error('Received invalid playbook data from server.');
          }
        })
        .catch(err => {
          console.error("Error fetching playbooks:", err);
          setError('Could not fetch playbooks. Please ensure the server is running and the route is available.');
        });

      fetch('/available_companies')
        .then(res => {
            if (!res.ok) throw new Error(`Server responded with ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (Array.isArray(data)) {
                setCompanies(data);
                if (data.length > 0) setSymbol(data[0].symbol);
            } else {
                throw new Error('Received invalid company data from server.');
            }
        })
        .catch(err => {
            console.error("Error fetching companies:", err);
            setError(prev => prev ? `${prev} And could not fetch companies.` : 'Could not fetch companies.');
        });
    }, []);

    const handleAnalyze = async (ev) => {
      if (ev) ev.preventDefault();
      if (!symbol || !selectedPlaybook) return;

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const resp = await fetch('/analyze_playbook', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: symbol.toUpperCase(), playbook_name: selectedPlaybook })
        });
        
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Analysis failed');
        setResult(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    const currentPlaybook = playbooks.find(p => p.name === selectedPlaybook);

    const metricExplanations = {
      "debt_to_equity": "Debt-to-Equity: This ratio compares a company's total liabilities to its shareholder equity. A high value can be a sign of high risk.",
      "eps_growth": "EPS Growth: This is the quarter-over-quarter growth in the company's Earnings Per Share. A positive value shows that the company's profitability is growing.",
      "operating_cash_flow": "Operating Cash Flow: This is the cash generated from the company's core business operations. A large, positive number is a strong sign of financial health.",
      "pe_ratio": "P/E Ratio: The Price-to-Earnings ratio compares the company's stock price to its earnings per share. A high P/E suggests that investors have high expectations for future growth.",
      "profit_margin": "Profit Margin: This shows how much profit the company makes for every dollar of revenue. A high profit margin indicates a very profitable business.",
      "roe": "ROE (Return on Equity): This measures how effectively the company uses shareholder investments to generate profit. A high ROE signals efficient management."
    };

    return e('div', { className: 'investment-agent-tool', style: { maxWidth: '800px', margin: '0 auto' } },
      e('form', { className: 'row g-3 align-items-end mb-4', onSubmit: handleAnalyze },
        e('div', { className: 'col-md-5' },
          e('label', { htmlFor: 'playbook-select', className: 'form-label' }, 'Select Playbook'),
          e('select', { id: 'playbook-select', className: 'form-select', value: selectedPlaybook, onChange: ev => setSelectedPlaybook(ev.target.value) },
            playbooks.map(playbook => e('option', { key: playbook.name, value: playbook.name }, playbook.name))
          )
        ),
        e('div', { className: 'col-md-4' },
          e('label', { htmlFor: 'agent-symbol', className: 'form-label' }, 'Stock Symbol'),
          e('select', { id: 'agent-symbol', className: 'form-select', value: symbol, onChange: ev => setSymbol(ev.target.value) },
            companies.map(company => e('option', { key: company.symbol, value: company.symbol }, `${company.name} (${company.symbol})`))
          )
        ),
        e('div', { className: 'col-md-3' },
          e('button', { type: 'submit', className: 'btn btn-primary w-100', disabled: loading || !symbol || !selectedPlaybook }, loading ? 'Analyzing...' : 'Analyze')
        )
      ),

      currentPlaybook && e('div', { className: 'card bg-light mb-4' },
        e('div', { className: 'card-body' },
          e('h5', { className: 'card-title' }, currentPlaybook.name),
          e('h6', { className: 'card-subtitle mb-2 text-muted' }, currentPlaybook.role),
          e('p', { className: 'card-text' }, e('strong', null, 'Philosophy: '), currentPlaybook.philosophy)
        )
      ),

      error && e('div', { className: 'alert alert-danger' }, error),

      loading && e('div', { className: 'text-center p-5' }, e('div', { className: 'spinner-border', role: 'status' })),

      result && e('div', { className: 'card' },
        e('div', { className: 'card-header' }, `Analysis for ${symbol} by ${result.playbook.name}`),
        e('div', { className: 'card-body' },
          e('h5', { className: 'card-title' }, `Decision: ${result.decision}`),
          e('p', { className: 'card-text' }, e('strong', null, 'Reasons:')),
          e('ul', { className: 'list-group list-group-flush' },
            result.reasons.map((reason, i) => e('li', { key: i, className: 'list-group-item' }, reason))
          ),
          e('hr'),
          e('p', { className: 'card-text mt-3' }, e('strong', null, 'Key Metrics:')),
          e('ul', { className: 'list-group list-group-flush' },
            Object.entries(result.stock_data).map(([key, value]) => 
              e('li', { key: key, className: 'list-group-item' },
                e('div', { className: 'tooltip-container' },
                  `${key.replace(/_/g, ' ')}:`,
                  e('span', { className: 'tooltip-text' }, metricExplanations[key])
                ),
                ` ${value !== null ? parseFloat(value).toFixed(2) : 'N/A'}`
              )
            )
          )
        )
      )
    );
  }

  const root = document.getElementById('react-investment-playbooks-tool');
  if (root && window.React && window.ReactDOM) {
    ReactDOM.createRoot(root).render(React.createElement(InvestmentPlaybooksTool));
  }
})();

// DeepSeek Chatbot Component
(function() {
  const e = React.createElement;

  function DeepSeekChatbot() {
    const [message, setMessage] = React.useState("Show Apple stock's performance by checking how much return it gave for the risk taken and how much it fell from its highest point with specific days performance");
    const [conversation, setConversation] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [model, setModel] = React.useState("mistral-small");
    const [temperature, setTemperature] = React.useState(0.7);
    const [maxTokens, setMaxTokens] = React.useState(1000);
    const [apiStatus, setApiStatus] = React.useState(null);
    const [hasShownDemo, setHasShownDemo] = React.useState(false);
    const [activeTab, setActiveTab] = React.useState('chat');

    // Model Performance Comparison state
    const [comparisonPrompt, setComparisonPrompt] = React.useState("Explain the concept of machine learning in simple terms");
    const [selectedModels, setSelectedModels] = React.useState(["mistral-small", "deepseek-r1", "qwen3-8b"]);
    const [comparisonLoading, setComparisonLoading] = React.useState(false);
    const [comparisonResults, setComparisonResults] = React.useState(null);
    const [comparisonError, setComparisonError] = React.useState(null);

    const availableModels = [
      { value: "mistral-small", label: "Mistral Small", description: "General conversation and analysis" },
      { value: "deepseek-r1", label: "DeepSeek R1", description: "Specialized for coding and programming" },
      { value: "qwen3-8b", label: "Qwen 3 8B", description: "Optimized for mathematical problems" },
      { value: "gemma-3n", label: "Gemma 3N", description: "Google's efficient model" },
      { value: "kimi-k2", label: "Kimi K2", description: "Moonshot's conversational model" }
    ];

    const models = [
      { value: "mistral-small", label: "Mistral Small", description: "General conversation and analysis" },
      { value: "deepseek-r1", label: "DeepSeek R1", description: "Specialized for coding and programming" },
      { value: "qwen3-8b", label: "Qwen 3 8B", description: "Optimized for mathematical problems" },
      { value: "gemma-3n", label: "Gemma 3N", description: "Google's efficient model" },
      { value: "kimi-k2", label: "Kimi K2", description: "Moonshot's conversational model" }
    ];

    // Check API status and show demo on component mount
    React.useEffect(() => {
      fetch('/health')
        .then(res => res.json())
        .then(data => {
          setApiStatus(data.api_configured);
          // Show demo if API is configured and we haven't shown it yet
          if (data.api_configured && !hasShownDemo) {
            setTimeout(() => {
              handleSubmit(null, "Show Apple stock's performance by checking how much return it gave for the risk taken and how much it fell from its highest point with specific days performance");
              setHasShownDemo(true);
            }, 1000);
          }
        })
        .catch(() => {
          setApiStatus(false);
        });
    }, [hasShownDemo]);

    const handleSubmit = async (ev) => {
      ev.preventDefault();
      if (!message.trim() || loading) return;

      const userMessage = message.trim();
      setMessage("");
      setLoading(true);
      setError(null);

      // Add user message to conversation
      const newConversation = [...conversation, { role: "user", content: userMessage }];
      setConversation(newConversation);

      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            model: model,
            temperature: temperature,
            max_tokens: maxTokens,
            history: newConversation
          })
        });

        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to get response');
        }

        // Add AI response to conversation
        setConversation(prev => [...prev, { role: "assistant", content: data.response }]);
      } catch (err) {
        setError(err.message);
        // Remove the user message if there was an error
        setConversation(prev => prev.slice(0, -1));
      } finally {
        setLoading(false);
      }
    };

    const clearConversation = () => {
      setConversation([]);
      setError(null);
    };

    // Model Performance Comparison functions
    const handleCompare = async (ev) => {
      ev.preventDefault();
      if (!comparisonPrompt.trim() || selectedModels.length === 0) return;

      setComparisonLoading(true);
      setComparisonError(null);
      setComparisonResults(null);

      try {
        const response = await fetch('/compare_models', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: comparisonPrompt.trim(),
            models: selectedModels,
            temperature: temperature,
            max_tokens: maxTokens
          })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Comparison failed');
        setComparisonResults(data);
      } catch (err) {
        setComparisonError(err.message);
      } finally {
        setComparisonLoading(false);
      }
    };

    const toggleModel = (modelValue) => {
      setSelectedModels(prev => 
        prev.includes(modelValue) 
          ? prev.filter(m => m !== modelValue)
          : [...prev, modelValue]
      );
    };

    const getModelDisplayName = (modelValue) => {
      const model = availableModels.find(m => m.value === modelValue);
      return model ? model.label : modelValue;
    };

    const formatMessage = (content) => {
      // Simple markdown-like formatting
      return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    };

    return e('div', { className: 'deepseek-chatbot', style: { maxWidth: '1200px', margin: '0 auto' } },
      e('style', null, `
        .deepseek-chatbot { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .chat-header { margin-bottom: 20px; }
        .chat-header h2 { font-size: 22px; font-weight: 600; color: #1a202c; margin-bottom: 8px; }
        .chat-header p { font-size: 15px; color: #718096; }
        .chat-controls { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
        .control-group { flex: 1; min-width: 150px; }
        .control-group label { font-weight: 500; font-size: 14px; margin-bottom: 6px; color: #4a5568; display: block; }
        .control-group .form-control, .control-group .form-select { font-size: 15px; }
        .chat-messages { height: 400px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #f8fafc; }
        .message { margin-bottom: 16px; padding: 12px; border-radius: 8px; }
        .message.user { background: #183153; color: white; margin-left: 20px; }
        .message.assistant { background: white; border: 1px solid #e2e8f0; margin-right: 20px; }
        .message-content { line-height: 1.5; }
        .message-content code { background: #f1f5f9; padding: 2px 4px; border-radius: 4px; font-family: 'Courier New', monospace; }
        .chat-input { display: flex; gap: 12px; }
        .chat-input textarea { flex: 1; resize: vertical; min-height: 60px; }
        .api-status { padding: 8px 12px; border-radius: 6px; font-size: 14px; margin-bottom: 16px; }
        .api-status.success { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .api-status.error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        .api-status.warning { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .tab-nav { display: flex; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; }
        .tab-nav button { background: none; border: none; padding: 12px 20px; font-size: 16px; font-weight: 500; color: #718096; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; }
        .tab-nav button.active { color: #183153; border-bottom-color: #183153; }
        .tab-nav button:hover { color: #183153; }
        .model-checkboxes { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
        .model-checkbox { display: flex; align-items: center; gap: 6px; }
        .model-checkbox input { margin: 0; }
        .model-checkbox label { font-size: 14px; color: #4a5568; }
        .summary-stats { background: #e6fffa; border: 1px solid #9ae6b4; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
        .summary-stats h4 { margin-bottom: 12px; color: #22543d; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 18px; font-weight: 600; color: #22543d; }
        .stat-label { font-size: 12px; color: #718096; margin-top: 4px; }
        .comparison-table { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .comparison-table th { background: #183153 !important; color: white; font-weight: 600; padding: 12px 8px; }
        .comparison-table td { padding: 12px 8px; vertical-align: middle; }
        .comparison-table .table-success { background-color: #d1fae5 !important; }
        .comparison-table .table-danger { background-color: #fee2e2 !important; }
        .comparison-table .badge { font-size: 0.75rem; }
        .comparison-table .fw-bold { color: #183153; }
      `),

      // Header
      e('div', { className: 'chat-header' },
        e('h2', null, '🤖 Chatbot'),
        e('p', null, 'Powered by AI models via OpenRouter API')
      ),

      // API Status
      apiStatus === true && e('div', { className: 'api-status success' }, '✅ API Connected'),
      apiStatus === false && e('div', { className: 'api-status error' }, '❌ API Not Configured - Please set OPENROUTER_API_KEY'),
      apiStatus === null && e('div', { className: 'api-status warning' }, '⏳ Checking API Status...'),

      // Tab Navigation
      e('div', { className: 'tab-nav' },
        e('button', {
          className: activeTab === 'chat' ? 'active' : '',
          onClick: () => setActiveTab('chat')
        }, '💬 Chat'),
        e('button', {
          className: activeTab === 'comparison' ? 'active' : '',
          onClick: () => setActiveTab('comparison')
        }, '🏁 Model Performance Comparison')
      ),

      // Chat Tab Content
      activeTab === 'chat' && e('div', null,
        // Controls
      e('div', { className: 'chat-controls' },
        e('div', { className: 'control-group' },
          e('label', null, 'Model:'),
          e('select', {
            className: 'form-select',
            value: model,
            onChange: ev => setModel(ev.target.value)
          }, models.map(m => e('option', { key: m.value, value: m.value }, m.label)))
        ),
        e('div', { className: 'control-group' },
          e('label', null, 'Temperature:'),
          e('input', {
            type: 'range',
            className: 'form-control',
            min: '0',
            max: '2',
            step: '0.1',
            value: temperature,
            onChange: ev => setTemperature(parseFloat(ev.target.value))
          })
        ),
        e('div', { className: 'control-group' },
          e('label', null, 'Max Tokens:'),
          e('input', {
            type: 'number',
            className: 'form-control',
            min: '100',
            max: '4000',
            value: maxTokens,
            onChange: ev => setMaxTokens(parseInt(ev.target.value))
          })
        )
      ),

      // Parameter display
      e('div', { style: { fontSize: '14px', color: '#666', marginBottom: '16px' } },
        `Temperature: ${temperature} | Max Tokens: ${maxTokens}`
      ),

      // Messages
      e('div', { className: 'chat-messages' },
        conversation.length === 0 ? 
          e('div', { style: { textAlign: 'center', color: '#666', marginTop: '50px' } },
            e('div', { style: { marginBottom: '20px' } },
              e('h5', { style: { color: '#183153', marginBottom: '10px' } }, '🧪 Welcome to Model Evaluation!'),
              e('p', { style: { fontSize: '14px', lineHeight: '1.5' } }, 
                'Test and compare AI models with your questions.'
              )
            ),
            e('div', { style: { background: '#f8f9fa', padding: '15px', borderRadius: '8px', border: '1px solid #e9ecef' } },
              e('p', { style: { margin: '0', fontSize: '14px', color: '#6c757d' } },
                e('strong', null, '💡 Tip: '), 
                'The demo will automatically show you Apple stock analysis with performance metrics using Mistral Small model.'
              )
            )
          ) :
          conversation.map((msg, index) => 
            e('div', { 
              key: index, 
              className: `message ${msg.role}`,
              style: { textAlign: msg.role === 'user' ? 'right' : 'left' }
            },
              e('div', { 
                className: 'message-content',
                dangerouslySetInnerHTML: { __html: formatMessage(msg.content) }
              })
            )
          ),
        loading && e('div', { className: 'message assistant', style: { textAlign: 'left' } },
          e('div', { className: 'message-content' }, '🤔 Thinking...')
        )
      ),

      // Error display
      error && e('div', { className: 'alert alert-danger mb-3' }, error),

      // Input and buttons
      e('div', { className: 'chat-input' },
        e('textarea', {
          className: 'form-control',
          placeholder: 'Type your message here...',
          value: message,
          onChange: ev => setMessage(ev.target.value),
          onKeyPress: ev => ev.key === 'Enter' && !ev.shiftKey && handleSubmit(ev)
        }),
        e('div', { style: { display: 'flex', flexDirection: 'column', gap: '8px' } },
          e('button', {
            className: 'btn btn-dark-bbg',
            onClick: handleSubmit,
            disabled: loading || !message.trim() || apiStatus === false
          }, loading ? 'Sending...' : 'Send'),
          e('button', {
            className: 'btn btn-outline-secondary',
            onClick: clearConversation,
            disabled: conversation.length === 0
          }, 'Clear Chat')
        )
      )
      ),

      // Comparison Tab Content
      activeTab === 'comparison' && e('div', null,
        e('div', { className: 'mb-3' },
          e('label', { htmlFor: 'comparison-prompt', className: 'form-label' }, 'Test Prompt:'),
          e('textarea', {
            id: 'comparison-prompt',
            className: 'form-control',
            rows: 3,
            value: comparisonPrompt,
            onChange: ev => setComparisonPrompt(ev.target.value),
            placeholder: 'Enter a prompt to test all selected models...'
          })
        ),

        e('div', { className: 'mb-3' },
          e('label', { className: 'form-label' }, 'Select Models to Compare:'),
          e('div', { className: 'model-checkboxes' },
            availableModels.map(model => 
              e('div', { key: model.value, className: 'model-checkbox' },
                e('input', {
                  type: 'checkbox',
                  id: `model-${model.value}`,
                  checked: selectedModels.includes(model.value),
                  onChange: () => toggleModel(model.value)
                }),
                e('label', { htmlFor: `model-${model.value}` }, model.label)
              )
            )
          )
        ),

        e('div', { className: 'row g-3 mb-3' },
          e('div', { className: 'col-md-6' },
            e('label', { className: 'form-label' }, 'Temperature:'),
            e('input', {
              type: 'range',
              className: 'form-control',
              min: '0',
              max: '2',
              step: '0.1',
              value: temperature,
              onChange: ev => setTemperature(parseFloat(ev.target.value))
            }),
            e('small', { className: 'text-muted' }, `Current: ${temperature}`)
          ),
          e('div', { className: 'col-md-6' },
            e('label', { className: 'form-label' }, 'Max Tokens:'),
            e('input', {
              type: 'number',
              className: 'form-control',
              min: '100',
              max: '4000',
              value: maxTokens,
              onChange: ev => setMaxTokens(parseInt(ev.target.value))
            })
          )
        ),

        e('button', {
          type: 'submit',
          className: 'btn btn-primary',
          onClick: handleCompare,
          disabled: comparisonLoading || selectedModels.length === 0 || !comparisonPrompt.trim()
        }, comparisonLoading ? '🔄 Comparing Models...' : '🏁 Start Comparison'),

        comparisonError && e('div', { className: 'alert alert-danger mt-3' }, comparisonError),

        comparisonResults && e('div', { className: 'mt-4' },
          e('div', { className: 'summary-stats' },
            e('h4', null, '📊 Comparison Summary'),
            e('div', { className: 'stats-grid' },
              e('div', { className: 'stat-item' },
                e('div', { className: 'stat-value' }, comparisonResults.summary.successful_models),
                e('div', { className: 'stat-label' }, 'Successful Models')
              ),
              e('div', { className: 'stat-item' },
                e('div', { className: 'stat-value' }, `${comparisonResults.summary.avg_response_time.toFixed(2)}s`),
                e('div', { className: 'stat-label' }, 'Avg Response Time')
              ),
              e('div', { className: 'stat-item' },
                e('div', { className: 'stat-value' }, Math.round(comparisonResults.summary.avg_token_count)),
                e('div', { className: 'stat-label' }, 'Avg Tokens Used')
              ),
              e('div', { className: 'stat-item' },
                e('div', { className: 'stat-value' }, getModelDisplayName(comparisonResults.summary.fastest_model)),
                e('div', { className: 'stat-label' }, 'Fastest Model')
              )
            )
          ),

          e('h4', { style: { marginBottom: '16px', color: '#1a202c' } }, '📋 Performance Comparison Table'),

          e('div', { className: 'table-responsive' },
            e('table', { className: 'table table-striped table-hover comparison-table' },
              e('thead', { className: 'table-dark' },
                e('tr', null,
                  e('th', null, 'Model'),
                  e('th', null, 'Status'),
                  e('th', null, 'Response Time'),
                  e('th', null, 'Tokens'),
                  e('th', null, 'Words'),
                  e('th', null, 'Avg Word Length'),
                  e('th', null, 'Response Preview')
                )
              ),
              e('tbody', null,
                comparisonResults.results.map((result, index) => 
                  e('tr', { key: result.model, className: result.success ? 'table-success' : 'table-danger' },
                    e('td', { className: 'fw-bold' }, getModelDisplayName(result.model)),
                    e('td', null, 
                      result.success ? 
                        e('span', { className: 'badge bg-success' }, '✅ Success') :
                        e('span', { className: 'badge bg-danger' }, '❌ Failed')
                    ),
                    e('td', null, result.success ? `${result.response_time.toFixed(2)}s` : '-'),
                    e('td', null, result.success ? result.token_count : '-'),
                    e('td', null, result.success ? result.word_count : '-'),
                    e('td', null, result.success ? result.avg_word_length.toFixed(1) : '-'),
                    e('td', { className: 'text-muted', style: { maxWidth: '300px' } },
                      result.success && result.response ? 
                        (result.response.length > 100 ? 
                          `${result.response.substring(0, 100)}...` : 
                          result.response
                        ) : 
                        (result.error || 'N/A')
                    )
                  )
                )
              )
            )
          )
        )
      )
    );
  }

  const root = document.getElementById('react-deepseek-chatbot');
  if (root && window.React && window.ReactDOM) {
    ReactDOM.createRoot(root).render(React.createElement(DeepSeekChatbot));
  }
})();




  
// --- AI Platform Comparables Interactivity ---
(function() {
    // Simple in-browser filtering, sorting, and chip logic
    const table = document.getElementById('ai-platform-table');
    const search = document.getElementById('ai-platform-search');
    const chips = document.querySelectorAll('.filter-chip');
    let currentCategory = null;
    let currentSort = null;
    let sortAsc = true;

    function filterTable() {
        const query = (search.value || '').toLowerCase();
        Array.from(table.tBodies[0].rows).forEach(row => {
            const text = row.innerText.toLowerCase();
            const matchesSearch = text.includes(query);
            const matchesCategory = !currentCategory || row.getAttribute('data-category') === currentCategory;
            row.style.display = (matchesSearch && matchesCategory) ? '' : 'none';
        });
    }
    search && search.addEventListener('input', filterTable);
    chips.forEach(chip => {
        chip.addEventListener('click', function() {
            if (currentCategory === chip.dataset.category) {
                currentCategory = null;
                chips.forEach(c => c.classList.remove('active'));
            } else {
                currentCategory = chip.dataset.category;
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
            }
            filterTable();
        });
    });
    // Sortable columns
    Array.from(table.tHead.rows[0].cells).forEach((th, idx) => {
        if (!th.hasAttribute('data-sort')) return;
        th.style.cursor = 'pointer';
        th.addEventListener('click', function() {
            const rows = Array.from(table.tBodies[0].rows).filter(r => r.style.display !== 'none');
            rows.sort((a, b) => {
                const aText = a.cells[idx].innerText.toLowerCase();
                const bText = b.cells[idx].innerText.toLowerCase();
                if (aText < bText) return sortAsc ? -1 : 1;
                if (aText > bText) return sortAsc ? 1 : -1;
                return 0;
            });
            sortAsc = currentSort === idx ? !sortAsc : true;
            currentSort = idx;
            rows.forEach(row => table.tBodies[0].appendChild(row));
        });
    });
    // Chart placeholder (future: Chart.js integration)
    if (window.Chart) {
        const ctx = document.getElementById('ai-platform-chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['OpenRouter', 'Together.ai', 'Hugging Face', 'Fireworks.ai', 'Groq API', 'Anyscale', 'Ollama', 'Vercel AI SDK', 'LangChain', 'Helicone', 'PromptLayer'],
                datasets: [{
                    label: 'Relative Popularity (Demo)',
                    data: [90, 70, 95, 60, 50, 40, 30, 35, 60, 45, 40],
                    backgroundColor: '#27457c',
                }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    }
})();
  