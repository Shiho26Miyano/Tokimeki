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
            selectedStrategy: 'stock', // 'stock' or 'options'
            
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
            // Mock options data for demonstration
            // In a real implementation, this would call your options API
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
        // Generate mock weekly options trades
        const trades = [];
        const startDate = new Date(this.state.startDate);
        const endDate = new Date(this.state.endDate);
        
        let currentDate = new Date(startDate);
        let tradeId = 1;
        
        while (currentDate <= endDate) {
            // Skip weekends
            if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) {
                const isWin = Math.random() > 0.4; // 60% win rate
                const pnl = isWin 
                    ? Math.random() * 200 + 50   // Win: $50-$250
                    : -(Math.random() * 150 + 25); // Loss: -$25 to -$175
                
                trades.push({
                    id: tradeId++,
                    date: currentDate.toISOString().split('T')[0],
                    type: Math.random() > 0.5 ? 'CALL' : 'PUT',
                    strike: 220 + Math.random() * 60, // Strike between $220-$280
                    premium: Math.abs(pnl) / 10,
                    pnl: pnl,
                    isWin: isWin,
                    contracts: 1
                });
            }
            
            // Move to next week
            currentDate.setDate(currentDate.getDate() + 7);
        }
        
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
                        onClick: this.loadWeeklyData
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
