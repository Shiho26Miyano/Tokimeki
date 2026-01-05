/**
 * AAPL Weekly Investment Tracker - Spreadsheet Style
 * Shows weekly investments and PnL tracking
 */

// Wait for React to be available before defining the component
(function() {
    'use strict';
    
    function defineComponent() {
        if (typeof React === 'undefined' || typeof React.Component === 'undefined') {
            console.log('React not available yet for AAPLWeeklyTracker, retrying in 100ms...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining AAPLWeeklyTracker component...');

class AAPLWeeklyTracker extends React.Component {
    constructor(props) {
        super(props);
        
        // Calculate default dates (1 year ago to today)
        const today = new Date();
        const oneYearAgo = new Date(today);
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        this.state = {
            // Investment parameters
            weeklyAmount: 1000,
            startDate: oneYearAgo.toISOString().split('T')[0],
            endDate: today.toISOString().split('T')[0],
            
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
            totalShares: 0,
            
            // Options summary
            totalOptionTrades: 0,
            totalOptionPnL: 0,
            optionWinRate: 0
        };
        
        this.loadWeeklyData = this.loadWeeklyData.bind(this);
        this.loadOptionsData = this.loadOptionsData.bind(this);
        this.handleParameterChange = this.handleParameterChange.bind(this);
    }
    
    componentDidMount() {
        console.log('AAPL Weekly Tracker mounted');
        console.log('Initial strategy:', this.state.selectedStrategy);
        console.log('Weekly amount:', this.state.weeklyAmount);
        
        // Load data based on selected strategy
        if (this.state.selectedStrategy === 'options') {
            this.loadOptionsData();
        } else {
            this.loadWeeklyData();
        }
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
            
            // Generate weekly investment data
            const weeklyData = this.generateWeeklyInvestments(data.data);
            
            // Calculate summary
            const summary = this.calculateSummary(weeklyData);
            
            this.setState({
                weeklyData,
                ...summary,
                loading: false
            });
            
        } catch (error) {
            console.error('Error loading weekly data:', error);
            this.setState({
                error: error.message,
                loading: false
            });
        }
    }
    
    generateWeeklyInvestments(priceData) {
        const { weeklyAmount } = this.state;
        const weeklyInvestments = [];
        
        // Group prices by week (assuming Tuesday investments)
        const startDate = new Date(this.state.startDate);
        let currentDate = new Date(startDate);
        let weekNumber = 1;
        
        // Find first Tuesday
        while (currentDate.getDay() !== 2) { // 2 = Tuesday
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        while (currentDate <= new Date(this.state.endDate)) {
            // Find price for this date (or closest available)
            const targetDate = currentDate.toISOString().split('T')[0];
            const priceEntry = this.findClosestPrice(targetDate, priceData);
            
            if (priceEntry) {
                const sharesBought = weeklyAmount / priceEntry.close;
                const currentPrice = priceData[priceData.length - 1]?.close || priceEntry.close;
                const currentValue = sharesBought * currentPrice;
                const pnl = currentValue - weeklyAmount;
                const pnlPercent = (pnl / weeklyAmount) * 100;
                
                weeklyInvestments.push({
                    week: weekNumber,
                    date: targetDate,
                    investmentAmount: weeklyAmount,
                    sharePrice: priceEntry.close,
                    sharesBought: sharesBought,
                    currentPrice: currentPrice,
                    currentValue: currentValue,
                    pnl: pnl,
                    pnlPercent: pnlPercent,
                    cumulativeInvested: weekNumber * weeklyAmount,
                    cumulativeShares: 0, // Will calculate below
                    cumulativeValue: 0,  // Will calculate below
                    cumulativePnL: 0     // Will calculate below
                });
            }
            
            // Move to next Tuesday
            currentDate.setDate(currentDate.getDate() + 7);
            weekNumber++;
        }
        
        // Calculate cumulative values
        let cumulativeShares = 0;
        weeklyInvestments.forEach((investment, index) => {
            cumulativeShares += investment.sharesBought;
            investment.cumulativeShares = cumulativeShares;
            investment.cumulativeValue = cumulativeShares * investment.currentPrice;
            investment.cumulativePnL = investment.cumulativeValue - investment.cumulativeInvested;
        });
        
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
            totalShares: lastEntry.cumulativeShares
        };
    }
    
    async loadOptionsData() {
        this.setState({ loading: true, error: null });
        
        try {
            // Generate mock options data based on weekly investment amount
            const mockOptionsData = this.generateMockOptionsData();
            
            if (mockOptionsData.length === 0) {
                console.warn('No options trades generated. Check date range.');
                this.setState({
                    optionsData: [],
                    totalOptionTrades: 0,
                    totalOptionPnL: 0,
                    optionWinRate: 0,
                    loading: false
                });
                return;
            }
            
            const optionsSummary = this.calculateOptionsSummary(mockOptionsData);
            
            console.log('Options summary:', optionsSummary);
            console.log('Options data sample:', mockOptionsData.slice(0, 3));
            
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
        // Generate mock weekly options trades based on weekly investment amount
        const trades = [];
        const { weeklyAmount, startDate, endDate } = this.state;
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        // Find first Tuesday (same as stock investment strategy)
        let currentDate = new Date(start);
        while (currentDate.getDay() !== 2) { // 2 = Tuesday
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        let tradeId = 1;
        
        // Generate one trade per week (every Tuesday)
        while (currentDate <= end) {
            const isWin = Math.random() > 0.4; // 60% win rate
            
            // Calculate P&L based on weekly investment amount
            // Options typically have higher volatility, so P&L can range from -100% to +300% of investment
            const pnlMultiplier = isWin 
                ? Math.random() * 2.0 + 0.5   // Win: 50% to 250% return
                : -(Math.random() * 0.8 + 0.2); // Loss: -20% to -100% of investment
            
            const pnl = weeklyAmount * pnlMultiplier;
            const premium = Math.abs(pnl) * 0.1; // Premium is roughly 10% of absolute P&L
            
            // Generate realistic strike price (around current stock price ± 20%)
            const baseStrike = 220; // Approximate AAPL price
            const strike = baseStrike + (Math.random() - 0.5) * 40; // ±$20 range
            
            trades.push({
                id: tradeId++,
                date: currentDate.toISOString().split('T')[0],
                type: Math.random() > 0.5 ? 'CALL' : 'PUT',
                strike: Math.round(strike * 100) / 100, // Round to 2 decimals
                premium: Math.round(premium * 100) / 100,
                pnl: Math.round(pnl * 100) / 100,
                isWin: isWin,
                contracts: Math.ceil(weeklyAmount / premium) || 1 // Calculate contracts based on premium
            });
            
            // Move to next Tuesday
            currentDate.setDate(currentDate.getDate() + 7);
        }
        
        console.log(`Generated ${trades.length} mock options trades for weekly investment of $${weeklyAmount}`);
        return trades;
    }
    
    calculateOptionsSummary(optionsData) {
        if (optionsData.length === 0) {
            return { totalTrades: 0, totalPnL: 0, winRate: 0 };
        }
        
        const totalTrades = optionsData.length;
        const totalPnL = optionsData.reduce((sum, trade) => sum + trade.pnl, 0);
        const wins = optionsData.filter(trade => trade.isWin).length;
        const winRate = wins / totalTrades;
        
        return { totalTrades, totalPnL, winRate };
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
    
    renderStockSummary() {
        const { totalInvested, currentValue, totalPnL, totalShares } = this.state;
        
        return React.createElement('div', { key: 'summary', className: 'row mb-4' }, [
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
        ]);
    }
    
    renderOptionsSummary() {
        const { totalOptionTrades, totalOptionPnL, optionWinRate } = this.state;
        
        return React.createElement('div', { key: 'summary', className: 'row mb-4' }, [
            React.createElement('div', { key: 'trades', className: 'col-md-3' }, [
                React.createElement('div', { className: 'card bg-light' }, [
                    React.createElement('div', { className: 'card-body text-center' }, [
                        React.createElement('h5', { className: 'card-title text-muted' }, 'Total Trades'),
                        React.createElement('h3', { className: 'text-primary' }, totalOptionTrades)
                    ])
                ])
            ]),
            React.createElement('div', { key: 'winrate', className: 'col-md-3' }, [
                React.createElement('div', { className: 'card bg-light' }, [
                    React.createElement('div', { className: 'card-body text-center' }, [
                        React.createElement('h5', { className: 'card-title text-muted' }, 'Win Rate'),
                        React.createElement('h3', { className: 'text-info' }, `${(optionWinRate * 100).toFixed(1)}%`)
                    ])
                ])
            ]),
            React.createElement('div', { key: 'pnl', className: 'col-md-3' }, [
                React.createElement('div', { className: 'card bg-light' }, [
                    React.createElement('div', { className: 'card-body text-center' }, [
                        React.createElement('h5', { className: 'card-title text-muted' }, 'Total P&L'),
                        React.createElement('h3', { 
                            className: totalOptionPnL >= 0 ? 'text-success' : 'text-danger' 
                        }, this.formatCurrency(totalOptionPnL))
                    ])
                ])
            ]),
            React.createElement('div', { key: 'avgpnl', className: 'col-md-3' }, [
                React.createElement('div', { className: 'card bg-light' }, [
                    React.createElement('div', { className: 'card-body text-center' }, [
                        React.createElement('h5', { className: 'card-title text-muted' }, 'Avg P&L/Trade'),
                        React.createElement('h3', { 
                            className: 'text-secondary' 
                        }, totalOptionTrades > 0 ? this.formatCurrency(totalOptionPnL / totalOptionTrades) : '$0.00')
                    ])
                ])
            ])
        ]);
    }
    
    renderStockTable() {
        const { weeklyData } = this.state;
        
        return React.createElement('div', { key: 'table', className: 'row' }, [
            React.createElement('div', { className: 'col-12' }, [
                React.createElement('div', { className: 'card' }, [
                    React.createElement('div', { className: 'card-header' }, [
                        React.createElement('h5', { className: 'mb-0' }, '📈 Weekly Stock Investment Details')
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
                                            React.createElement('td', { key: 'cumInvested' }, this.formatCurrency(week.cumulativeInvested)),
                                            React.createElement('td', { key: 'cumValue' }, this.formatCurrency(week.cumulativeValue)),
                                            React.createElement('td', { 
                                                key: 'cumPnL',
                                                className: week.cumulativePnL >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold'
                                            }, this.formatCurrency(week.cumulativePnL))
                                        ])
                                    )
                                )
                            ])
                        ])
                    ])
                ])
            ])
        ]);
    }
    
    renderOptionsTable() {
        const { optionsData } = this.state;
        
        return React.createElement('div', { key: 'table', className: 'row' }, [
            React.createElement('div', { className: 'col-12' }, [
                React.createElement('div', { className: 'card' }, [
                    React.createElement('div', { className: 'card-header' }, [
                        React.createElement('h5', { className: 'mb-0' }, '📊 Weekly Options Trading Details')
                    ]),
                    React.createElement('div', { className: 'card-body p-0' }, [
                        React.createElement('div', { className: 'table-responsive' }, [
                            React.createElement('table', { className: 'table table-striped table-hover mb-0' }, [
                                React.createElement('thead', { className: 'table-dark' }, [
                                    React.createElement('tr', {}, [
                                        React.createElement('th', {}, 'Trade #'),
                                        React.createElement('th', {}, 'Date'),
                                        React.createElement('th', {}, 'Type'),
                                        React.createElement('th', {}, 'Strike'),
                                        React.createElement('th', {}, 'Premium'),
                                        React.createElement('th', {}, 'Contracts'),
                                        React.createElement('th', {}, 'P&L'),
                                        React.createElement('th', {}, 'Result')
                                    ])
                                ]),
                                React.createElement('tbody', {}, 
                                    optionsData.map((trade, index) => 
                                        React.createElement('tr', { key: index }, [
                                            React.createElement('td', { key: 'id' }, trade.id),
                                            React.createElement('td', { key: 'date' }, trade.date),
                                            React.createElement('td', { key: 'type' }, trade.type),
                                            React.createElement('td', { key: 'strike' }, this.formatCurrency(trade.strike)),
                                            React.createElement('td', { key: 'premium' }, this.formatCurrency(trade.premium)),
                                            React.createElement('td', { key: 'contracts' }, trade.contracts),
                                            React.createElement('td', { 
                                                key: 'pnl',
                                                className: trade.pnl >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold'
                                            }, this.formatCurrency(trade.pnl)),
                                            React.createElement('td', { key: 'result' }, 
                                                React.createElement('span', {
                                                    className: `badge ${trade.isWin ? 'bg-success' : 'bg-danger'}`
                                                }, trade.isWin ? 'WIN' : 'LOSS')
                                            )
                                        ])
                                    )
                                )
                            ])
                        ])
                    ])
                ])
            ])
        ]);
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
                React.createElement('div', { key: 'title', className: 'col-md-6' }, [
                    React.createElement('h2', { className: 'text-primary' }, '🍎 AAPL Weekly Investment Tracker'),
                    React.createElement('p', { className: 'text-muted' }, 
                        this.state.selectedStrategy === 'stock' 
                            ? 'Dollar-Cost Averaging with Weekly PnL Tracking'
                            : 'Weekly Options Trading Strategy'
                    )
                ]),
                React.createElement('div', { key: 'strategy-selector', className: 'col-md-3' }, [
                    React.createElement('label', { className: 'form-label' }, 'Strategy:'),
                    React.createElement('select', {
                        className: 'form-select',
                        value: this.state.selectedStrategy,
                        onChange: (e) => {
                            this.setState({ selectedStrategy: e.target.value });
                            // Load appropriate data when strategy changes
                            if (e.target.value === 'options' && this.state.optionsData.length === 0) {
                                this.loadOptionsData();
                            }
                        }
                    }, [
                        React.createElement('option', { key: 'stock', value: 'stock' }, '📈 Stock DCA'),
                        React.createElement('option', { key: 'options', value: 'options' }, '📊 Weekly Options')
                    ])
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
                        onClick: () => {
                            // Reload data when weekly amount changes
                            if (this.state.selectedStrategy === 'stock') {
                                this.loadWeeklyData();
                            } else {
                                this.loadOptionsData();
                            }
                        }
                    }, 'Update')
                ])
            ]),
            
            // Summary Cards - Show different metrics based on strategy
            this.state.selectedStrategy === 'stock' ? this.renderStockSummary() : this.renderOptionsSummary(),
            
            // Data Table - Show different tables based on strategy
            this.state.selectedStrategy === 'stock' ? this.renderStockTable() : this.renderOptionsTable()
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
