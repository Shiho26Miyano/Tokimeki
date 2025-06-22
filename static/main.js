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
    // Use the first selected company from #stock-select
    const stockSelect = document.getElementById('stock-select');
    const symbols = Array.from(stockSelect.selectedOptions).map(opt => opt.value);
    if (!symbols.length) {
        document.getElementById('volatility-correlation-chart').innerHTML = 'Please select a company above.';
        return;
    }
    const symbol = symbols[0];
    // Get window and years from UI
    const windowInput = document.getElementById('vol-window');
    const yearsInput = document.getElementById('vol-years');
    const windowSize = windowInput ? parseInt(windowInput.value) || 10 : 10;
    const years = yearsInput ? parseInt(yearsInput.value) || 2 : 2;
    const today = new Date();
    const start = new Date();
    start.setFullYear(today.getFullYear() - years);
    const start_date = start.toISOString().split('T')[0];
    const end_date = today.toISOString().split('T')[0];
    const chartDiv = document.getElementById('volatility-correlation-chart');
    chartDiv.innerHTML = 'Loading...';
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
        })
        .catch(() => {
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
    const eventCount = data.event_count.slice(startIdx, endIdx + 1);
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
    // Event count as bars (optional)
    const barWidth = Math.max(1, width / dates.length * 0.7);
    g.selectAll('.event-bar')
        .data(eventCount)
        .enter()
        .append('rect')
        .attr('class', 'event-bar')
        .attr('x', (d, i) => x(dates[i]) - barWidth/2)
        .attr('y', (d, i) => yLeft((vol[i] !== null ? 0 : null)))
        .attr('width', barWidth)
        .attr('height', (d, i) => d > 0 ? 8 : 0)
        .attr('fill', '#2196f3')
        .attr('opacity', 0.25);
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
            html += `Event count: <b>${eventCount[idx]}</b><br>`;
            // Always show the lowest volatility window date range
            if (highlightStartDate && highlightEndDate) {
                html += `<span style='color:#ff9800'><b>Lowest Volatility Window:</b><br>${highlightStartDate} to ${highlightEndDate}</span><br>`;
            }
            // Always show news titles for this date, even if event count is N/A
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
    const [model, setModel] = React.useState("distilbert-base-uncased-finetuned-sst-2-english");
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

// ... existing code ...
(function() {
  const e = React.createElement;

  function SpeechRecorder() {
    const models = [
      { value: 'HuggingFaceH4/zephyr-7b-beta', label: 'Zephyr-7B (HF4)' },
      { value: 'mistralai/Mistral-7B-v0.1', label: 'Mistral-7B' },
      { value: 'google/gemma-7b-it', label: 'Gemma-7B (Google)' }
    ];
    const [model, setModel] = React.useState(models[0].value);
    const [recording, setRecording] = React.useState(false);
    const [transcript, setTranscript] = React.useState("");
    const [error, setError] = React.useState(null);
    const [result, setResult] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [timer, setTimer] = React.useState(0);
    const recognitionRef = React.useRef(null);
    const timerRef = React.useRef(null);

    React.useEffect(() => {
      if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        setError('Speech recognition is not supported in this browser.');
        return;
      }
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          interimTranscript += event.results[i][0].transcript;
        }
        setTranscript(interimTranscript);
      };
      recognition.onerror = (event) => {
        setError('Speech recognition error: ' + event.error);
        setRecording(false);
        clearInterval(timerRef.current);
        setTimer(0);
      };
      recognition.onend = () => {
        setRecording(false);
        clearInterval(timerRef.current);
        setTimer(0);
      };
      recognitionRef.current = recognition;
    }, []);

    const handleAsk = () => {
      setError(null);
      setTranscript("");
      setResult(null);
      if (recognitionRef.current) {
        recognitionRef.current.start();
        setRecording(true);
        setTimer(60);
        const startTime = Date.now();
        timerRef.current = setInterval(() => {
          const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
          const remainingSeconds = Math.max(0, 60 - elapsedSeconds);
          setTimer(remainingSeconds);
          if (remainingSeconds <= 0) {
            if (recognitionRef.current) recognitionRef.current.stop();
            clearInterval(timerRef.current);
          }
        }, 100); // Update more frequently for smoother countdown
      }
    };
    const handleSend = async () => {
      setError(null);
      setResult(null);
      setLoading(true);
      try {
        const resp = await fetch('/analyze_speech_request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: transcript, model })
        });
        const data = await resp.json();
        if (!resp.ok || data.error) throw new Error(data.error || 'Analysis failed');
        setResult(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    React.useEffect(() => {
      return () => clearInterval(timerRef.current);
    }, []);

    return e('div', { className: 'card shadow-sm p-2 mb-2', style: { maxWidth: 340, margin: '0 auto', background: '#f7f7fa', border: '1px solid #e0e0e0', fontSize: '0.97em' } },
      e('div', { className: 'mb-2', style: { fontWeight: 600, color: '#183153', fontSize: '1.01em' } }, 'Ask your question'),
      e('div', { style: { color: '#666', fontSize: '0.9em', marginBottom: '0.8em' } }, 'e.g. "What is the current stock price of Apple (AAPL)?" or "Show me Tesla\'s (TSLA) stock performance over the last 7 days"'),

      e('div', { className: 'mb-2' },
        e('label', { htmlFor: 'model-select', className: 'form-label', style: { fontWeight: 500, fontSize: '0.97em', color: '#183153', marginRight: 6 } }, 'Model:'),
        e('select', {
          id: 'model-select',
          className: 'form-select',
          value: model,
          onChange: ev => setModel(ev.target.value),
          style: { maxWidth: 200, display: 'inline-block', fontSize: '0.97em' }
        },
          models.map(m => e('option', { key: m.value, value: m.value }, m.label))
        )
      ),
      error && e('div', { className: 'alert alert-danger mb-2', style: { fontSize: '0.97em', padding: '0.4em 0.7em' } }, error),
      e('div', { className: 'd-flex gap-2 mb-2' },
        e('button', {
          className: 'btn btn-dark-bbg',
          onClick: handleAsk,
          disabled: recording,
          style: { fontSize: '0.97em', padding: '0.32em 0.9em' }
        }, recording ? 'Listening...' : 'Ask your question'),
        e('button', {
          className: 'btn btn-outline-secondary',
          onClick: handleSend,
          disabled: !transcript || loading,
          style: { fontSize: '0.97em', padding: '0.32em 0.9em' }
        }, loading ? 'Analyzing...' : 'Send')
      ),
      (recording || transcript) && e('div', { className: 'mb-2', style: { color: '#183153', background: '#fff', borderRadius: 8, padding: '0.5em', border: '1px solid #e0e0e0', fontSize: '0.98em', minHeight: 32 } }, transcript || (recording ? 'Listening...' : '')),
      result && e('div', { className: 'alert alert-info mt-2', style: { fontSize: '0.97em', padding: '0.4em 0.7em' } },
        result.answer && e('div', null, e('b', null, 'Answer: '), result.answer)
      ),
      recording && e('div', { className: 'mb-1', style: { color: '#b85c00', fontSize: '0.97em' } }, `You have ${timer}s to speak...`)
    );
  }

  const root = document.getElementById('react-speech-recorder');
  if (root && window.React && window.ReactDOM) {
    ReactDOM.createRoot(root).render(React.createElement(SpeechRecorder));
  }
})();

// Hedge Fund Signal Tool Component
(function() {
  const e = React.createElement;

  function HedgeFundTool() {
    const [symbol, setSymbol] = React.useState('AAPL');
    const [strategy, setStrategy] = React.useState('trend');
    const [period, setPeriod] = React.useState('1y');
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState(null);
    const [error, setError] = React.useState(null);

    // Initial analysis on load
    React.useEffect(() => {
      handleAnalyze(null, { symbol: 'AAPL', strategy: 'trend', period: '1y' });
    }, []);

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

      e('form', { className: 'hf-controls', onSubmit: handleAnalyze },
        e('div', { className: 'hf-control-group', style: { flex: '1.5' } },
          e('label', { htmlFor: 'hf-symbol' }, 'Stock Symbol'),
          e('input', { id: 'hf-symbol', type: 'text', className: 'form-control', value: symbol, onChange: ev => setSymbol(ev.target.value.toUpperCase()), placeholder: 'e.g. AAPL' }),
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
            Metric({ title: 'Total Return', value: result.metrics.total_return, isPercentage: true }),
            Metric({ title: 'Sharpe Ratio', value: result.metrics.sharpe_ratio }),
            Metric({ title: 'Max Drawdown', value: result.metrics.max_drawdown, isPercentage: true }),
            Metric({ title: 'Value at Risk (95%)', value: result.metrics.var_95, isPercentage: true })
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
  