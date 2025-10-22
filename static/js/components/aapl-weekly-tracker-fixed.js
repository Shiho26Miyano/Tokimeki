/**
 * AAPL Weekly Investment Tracker - Spreadsheet Style
 * Shows weekly investments and PnL tracking
 * Fixed version with proper React dependency checking
 */

// Wait for React to be available before defining the component
(function() {
    'use strict';
    
    function defineComponent() {
        if (typeof React === 'undefined' || typeof React.Component === 'undefined') {
            console.log('React not available yet, retrying in 100ms...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining AAPLWeeklyTracker component...');
        
        class AAPLWeeklyTracker extends React.Component {
            constructor(props) {
                super(props);
                
                this.state = {
                    // Investment parameters
                    weeklyAmount: 1000,
                    startDate: '2024-09-28',
                    endDate: '2025-09-28',
                    
                    // Data
                    weeklyData: [],
                    optionsData: [],
                    loading: false,
                    error: null,
                    selectedStrategy: 'options', // 'stock' or 'options'
                    
                    // Summary
                    totalInvested: 0,
                    currentValue: 0,
                    totalPnL: 0,
                    totalShares: 0
                };
                
                this.loadWeeklyData = this.loadWeeklyData.bind(this);
                this.handleParameterChange = this.handleParameterChange.bind(this);
            }
            
            componentDidMount() {
                console.log('AAPL Weekly Tracker mounted');
                this.loadWeeklyData();
                this.loadOptionsData(); // Load both datasets
            }
            
            async loadWeeklyData() {
                this.setState({ loading: true, error: null });
                
                try {
                    // Get stock price data for the period
                    const response = await fetch(`/api/v1/aapl-analysis/prices/AAPL?start_date=${this.state.startDate}&end_date=${this.state.endDate}`);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    console.log('Stock data received:', data);
                    
                    // Process weekly investment data
                    const weeklyData = this.generateWeeklyInvestments(data.data);
                    
                    // Calculate summary
                    const summary = this.calculateSummary(weeklyData);
                    
                    this.setState({
                        weeklyData,
                        loading: false,
                        ...summary
                    });
                    
                } catch (error) {
                    console.error('Error loading weekly data:', error);
                    this.setState({
                        loading: false,
                        error: error.message
                    });
                }
            }
            
            async loadOptionsData() {
                this.setState({ loading: true, error: null });
                
                try {
                    // Mock options data for demonstration
                    const mockOptionsData = this.generateMockOptionsData();
                    
                    const optionsSummary = this.calculateOptionsSummary(mockOptionsData);
                    
                    this.setState({
                        optionsData: mockOptionsData,
                        totalOptionTrades: optionsSummary.totalTrades,
                        totalOptionPnL: optionsSummary.totalPnL,
                        optionWinRate: optionsSummary.winRate,
                        loading: false
                    });
                } catch (error) {
                    console.error('Error loading options data:', error);
                    this.setState({ 
                        error: 'Failed to load options data. Please try again.',
                        loading: false
                    });
                }
            }
            
            generateMockOptionsData() {
                // Generate mock weekly options trading data
                const optionsData = [];
                const startDate = new Date(this.state.startDate);
                const endDate = new Date(this.state.endDate);
                
                let currentDate = new Date(startDate);
                let week = 1;
                
                while (currentDate <= endDate) {
                    // Find Tuesday for this week
                    while (currentDate.getDay() !== 2) {
                        currentDate.setDate(currentDate.getDate() + 1);
                    }
                    
                    if (currentDate <= endDate) {
                        const targetDate = currentDate.toISOString().split('T')[0];
                        
                        // Mock options trade
                        const strikePrice = 150 + (Math.random() - 0.5) * 20; // Around $150
                        const optionPrice = Math.random() * 5 + 1; // $1-6
                        const contracts = 1;
                        const totalCost = optionPrice * contracts * 100;
                        
                        // Mock P&L (simplified)
                        const pnl = (Math.random() - 0.4) * totalCost * 2; // Slight positive bias
                        
                        optionsData.push({
                            week: week,
                            date: targetDate,
                            strike: strikePrice.toFixed(2),
                            optionPrice: optionPrice.toFixed(2),
                            contracts: contracts,
                            totalCost: totalCost.toFixed(2),
                            pnl: pnl.toFixed(2),
                            pnlPercent: ((pnl / totalCost) * 100).toFixed(1),
                            status: pnl > 0 ? 'Win' : 'Loss'
                        });
                    }
                    
                    // Move to next week
                    currentDate.setDate(currentDate.getDate() + 7);
                    week++;
                }
                
                return optionsData;
            }
            
            calculateOptionsSummary(optionsData) {
                const totalTrades = optionsData.length;
                const totalPnL = optionsData.reduce((sum, trade) => sum + parseFloat(trade.pnl), 0);
                const winningTrades = optionsData.filter(trade => parseFloat(trade.pnl) > 0).length;
                const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
                
                return {
                    totalTrades,
                    totalPnL,
                    winRate
                };
            }
            
            generateWeeklyInvestments(priceData) {
                const weeklyInvestments = [];
                const { weeklyAmount } = this.state;
                
                // Sort price data by date
                const sortedPrices = priceData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                
                // Get current price (latest available)
                const currentPrice = sortedPrices[sortedPrices.length - 1]?.close || 0;
                
                const startDate = new Date(this.state.startDate);
                const endDate = new Date(this.state.endDate);
                
                let currentDate = new Date(startDate);
                let week = 1;
                let cumulativeInvested = 0;
                let cumulativeShares = 0;
                
                while (currentDate <= endDate) {
                    // Find the closest trading day (Tuesday preference)
                    const targetDate = currentDate.toISOString().split('T')[0];
                    const priceEntry = this.findClosestPrice(targetDate, sortedPrices);
                    
                    if (priceEntry) {
                        const sharesBought = weeklyAmount / priceEntry.close;
                        cumulativeInvested += weeklyAmount;
                        cumulativeShares += sharesBought;
                        
                        const currentValue = sharesBought * currentPrice;
                        const pnl = currentValue - weeklyAmount;
                        const pnlPercent = (pnl / weeklyAmount) * 100;
                        
                        const cumulativeValue = cumulativeShares * currentPrice;
                        const cumulativePnL = cumulativeValue - cumulativeInvested;
                        
                        weeklyInvestments.push({
                            week,
                            date: currentDate.toLocaleDateString(),
                            investmentAmount: weeklyAmount,
                            sharePrice: priceEntry.close,
                            sharesBought,
                            currentPrice,
                            currentValue,
                            pnl,
                            pnlPercent,
                            cumulativeInvested,
                            cumulativeValue,
                            cumulativePnL
                        });
                        
                        week++;
                    }
                    
                    // Move to next week
                    currentDate.setDate(currentDate.getDate() + 7);
                }
                
                return weeklyInvestments;
            }
            
            findClosestPrice(targetDate, priceData) {
                const target = new Date(targetDate);
                let closest = null;
                let minDiff = Infinity;
                
                for (const price of priceData) {
                    const priceDate = new Date(price.timestamp);
                    const diff = Math.abs(priceDate - target);
                    if (diff < minDiff) {
                        minDiff = diff;
                        closest = price;
                    }
                }
                
                return closest;
            }
            
            calculateSummary(weeklyData) {
                if (weeklyData.length === 0) {
                    return {
                        totalInvested: 0,
                        currentValue: 0,
                        totalPnL: 0,
                        totalShares: 0
                    };
                }
                
                const lastEntry = weeklyData[weeklyData.length - 1];
                return {
                    totalInvested: lastEntry.cumulativeInvested,
                    currentValue: lastEntry.cumulativeValue,
                    totalPnL: lastEntry.cumulativePnL,
                    totalShares: weeklyData.reduce((sum, entry) => sum + entry.sharesBought, 0)
                };
            }
            
            handleParameterChange(event) {
                const { name, value } = event.target;
                this.setState({ [name]: value });
            }
            
            formatCurrency(amount) {
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD'
                }).format(amount);
            }
            
            formatPercent(percent) {
                return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
            }
            
            formatShares(shares) {
                return shares.toFixed(4);
            }
            
            render() {
                const { weeklyData, loading, error, totalInvested, currentValue, totalPnL, totalShares } = this.state;
                
                if (loading) {
                    return React.createElement('div', { className: 'text-center p-4' }, [
                        React.createElement('div', { 
                            key: 'spinner',
                            className: 'spinner-border text-primary', 
                            role: 'status' 
                        }),
                        React.createElement('p', { 
                            key: 'text',
                            className: 'mt-3' 
                        }, 'Loading weekly investment data...')
                    ]);
                }
                
                if (error) {
                    return React.createElement('div', { className: 'alert alert-danger m-4' }, [
                        React.createElement('h4', { key: 'title' }, 'Error Loading Data'),
                        React.createElement('p', { key: 'message' }, error),
                        React.createElement('button', {
                            key: 'retry',
                            className: 'btn btn-primary',
                            onClick: this.loadWeeklyData
                        }, 'Retry')
                    ]);
                }
                
                return React.createElement('div', { className: 'container-fluid p-4' }, [
                    // Header
                    React.createElement('div', { key: 'header', className: 'row mb-4' }, [
                        React.createElement('div', { key: 'title', className: 'col-md-8' }, [
                            React.createElement('h2', { className: 'text-primary' }, '🍎 AAPL Weekly Investment Tracker'),
                            React.createElement('p', { className: 'text-muted' }, 'Dollar-Cost Averaging with Weekly PnL Tracking')
                        ]),
                        React.createElement('div', { key: 'controls', className: 'col-md-4' }, [
                            React.createElement('div', { className: 'mb-2' }, [
                                React.createElement('label', { className: 'form-label' }, 'Weekly Amount:'),
                                React.createElement('input', {
                                    type: 'number',
                                    className: 'form-control',
                                    name: 'weeklyAmount',
                                    value: this.state.weeklyAmount,
                                    onChange: this.handleParameterChange
                                })
                            ]),
                            React.createElement('button', {
                                className: 'btn btn-primary',
                                onClick: this.loadWeeklyData
                            }, 'Update')
                        ])
                    ]),
                    
                    // Summary Cards
                    React.createElement('div', { key: 'summary', className: 'row mb-4' }, [
                        React.createElement('div', { key: 'invested', className: 'col-md-3' }, [
                            React.createElement('div', { className: 'card bg-light' }, [
                                React.createElement('div', { className: 'card-body text-center' }, [
                                    React.createElement('h5', { className: 'card-title text-muted' }, 'Total Invested'),
                                    React.createElement('h3', { className: 'text-primary' }, this.formatCurrency(totalInvested))
                                ])
                            ])
                        ]),
                        React.createElement('div', { key: 'value', className: 'col-md-3' }, [
                            React.createElement('div', { className: 'card bg-light' }, [
                                React.createElement('div', { className: 'card-body text-center' }, [
                                    React.createElement('h5', { className: 'card-title text-muted' }, 'Current Value'),
                                    React.createElement('h3', { className: 'text-info' }, this.formatCurrency(currentValue))
                                ])
                            ])
                        ]),
                        React.createElement('div', { key: 'pnl', className: 'col-md-3' }, [
                            React.createElement('div', { className: 'card bg-light' }, [
                                React.createElement('div', { className: 'card-body text-center' }, [
                                    React.createElement('h5', { className: 'card-title text-muted' }, 'Total P&L'),
                                    React.createElement('h3', { 
                                        className: totalPnL >= 0 ? 'text-success' : 'text-danger' 
                                    }, this.formatCurrency(totalPnL))
                                ])
                            ])
                        ]),
                        React.createElement('div', { key: 'shares', className: 'col-md-3' }, [
                            React.createElement('div', { className: 'card bg-light' }, [
                                React.createElement('div', { className: 'card-body text-center' }, [
                                    React.createElement('h5', { className: 'card-title text-muted' }, 'Total Shares'),
                                    React.createElement('h3', { className: 'text-secondary' }, this.formatShares(totalShares))
                                ])
                            ])
                        ])
                    ]),
                    
                    // Weekly Data Table
                    React.createElement('div', { key: 'table', className: 'row' }, [
                        React.createElement('div', { className: 'col-12' }, [
                            React.createElement('div', { className: 'card' }, [
                                React.createElement('div', { className: 'card-header' }, [
                                    React.createElement('h5', { className: 'mb-0' }, 'Weekly Investment Details')
                                ]),
                                React.createElement('div', { className: 'card-body p-0' }, [
                                    React.createElement('div', { className: 'table-responsive' }, [
                                        React.createElement('table', { className: 'table table-striped table-hover mb-0' }, [
                                            React.createElement('thead', { className: 'table-dark' }, [
                                                React.createElement('tr', {}, [
                                                    React.createElement('th', {}, 'Week'),
                                                    React.createElement('th', {}, 'Date'),
                                                    React.createElement('th', {}, 'Investment'),
                                                    React.createElement('th', {}, 'Share Price'),
                                                    React.createElement('th', {}, 'Shares Bought'),
                                                    React.createElement('th', {}, 'Current Price'),
                                                    React.createElement('th', {}, 'Current Value'),
                                                    React.createElement('th', {}, 'Weekly P&L'),
                                                    React.createElement('th', {}, 'Weekly P&L %'),
                                                    React.createElement('th', {}, 'Cumulative Invested'),
                                                    React.createElement('th', {}, 'Cumulative Value'),
                                                    React.createElement('th', {}, 'Cumulative P&L')
                                                ])
                                            ]),
                                            React.createElement('tbody', {}, 
                                                weeklyData.map((week, index) => 
                                                    React.createElement('tr', { key: index }, [
                                                        React.createElement('td', { key: 'week' }, week.week),
                                                        React.createElement('td', { key: 'date' }, week.date),
                                                        React.createElement('td', { key: 'investment' }, this.formatCurrency(week.investmentAmount)),
                                                        React.createElement('td', { key: 'sharePrice' }, this.formatCurrency(week.sharePrice)),
                                                        React.createElement('td', { key: 'shares' }, this.formatShares(week.sharesBought)),
                                                        React.createElement('td', { key: 'currentPrice' }, this.formatCurrency(week.currentPrice)),
                                                        React.createElement('td', { key: 'currentValue' }, this.formatCurrency(week.currentValue)),
                                                        React.createElement('td', { 
                                                            key: 'pnl',
                                                            className: week.pnl >= 0 ? 'text-success' : 'text-danger'
                                                        }, this.formatCurrency(week.pnl)),
                                                        React.createElement('td', { 
                                                            key: 'pnlPercent',
                                                            className: week.pnlPercent >= 0 ? 'text-success' : 'text-danger'
                                                        }, this.formatPercent(week.pnlPercent)),
                                                        React.createElement('td', { key: 'cumulativeInvested' }, this.formatCurrency(week.cumulativeInvested)),
                                                        React.createElement('td', { key: 'cumulativeValue' }, this.formatCurrency(week.cumulativeValue)),
                                                        React.createElement('td', { 
                                                            key: 'cumulativePnL',
                                                            className: week.cumulativePnL >= 0 ? 'text-success' : 'text-danger'
                                                        }, this.formatCurrency(week.cumulativePnL))
                                                    ])
                                                )
                                            )
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ])
                ]);
            }
        }
        
        // Export for use in other components
        window.AAPLWeeklyTracker = AAPLWeeklyTracker;
        console.log('✅ AAPLWeeklyTracker component exported to window object');
    }
    
    // Start trying to define the component
    defineComponent();
})();
