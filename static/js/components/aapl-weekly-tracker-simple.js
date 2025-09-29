/**
 * AAPL Weekly Investment Tracker - Simple Version
 * Simplified version without template literals to avoid syntax issues
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
                    loading: false,
                    error: null,
                    
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
            }
            
            async loadWeeklyData() {
                this.setState({ loading: true, error: null });
                
                try {
                    // Get stock price data for the period - using string concatenation instead of template literals
                    const url = '/api/v1/aapl-analysis/prices/AAPL?start_date=' + this.state.startDate + '&end_date=' + this.state.endDate;
                    const response = await fetch(url);
                    
                    if (!response.ok) {
                        throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                    }
                    
                    const data = await response.json();
                    console.log('Stock data received:', data);
                    
                    // Generate weekly investment data
                    const weeklyData = this.generateWeeklyInvestments(data.data);
                    
                    // Calculate summary
                    const summary = this.calculateSummary(weeklyData);
                    
                    this.setState(Object.assign({
                        weeklyData: weeklyData,
                        loading: false
                    }, summary));
                    
                } catch (error) {
                    console.error('Error loading weekly data:', error);
                    this.setState({
                        loading: false,
                        error: error.message
                    });
                }
            }
            
            generateWeeklyInvestments(priceData) {
                const weeklyInvestments = [];
                const weeklyAmount = this.state.weeklyAmount;
                
                // Sort price data by date
                const sortedPrices = priceData.sort(function(a, b) {
                    return new Date(a.timestamp) - new Date(b.timestamp);
                });
                
                // Get current price (latest available)
                const currentPrice = sortedPrices.length > 0 ? sortedPrices[sortedPrices.length - 1].close : 0;
                
                const startDate = new Date(this.state.startDate);
                const endDate = new Date(this.state.endDate);
                
                let currentDate = new Date(startDate);
                let week = 1;
                let cumulativeInvested = 0;
                let cumulativeShares = 0;
                
                while (currentDate <= endDate) {
                    // Find the closest trading day
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
                            week: week,
                            date: currentDate.toLocaleDateString(),
                            investmentAmount: weeklyAmount,
                            sharePrice: priceEntry.close,
                            sharesBought: sharesBought,
                            currentPrice: currentPrice,
                            currentValue: currentValue,
                            pnl: pnl,
                            pnlPercent: pnlPercent,
                            cumulativeInvested: cumulativeInvested,
                            cumulativeValue: cumulativeValue,
                            cumulativePnL: cumulativePnL
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
                
                for (let i = 0; i < priceData.length; i++) {
                    const price = priceData[i];
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
                let totalShares = 0;
                for (let i = 0; i < weeklyData.length; i++) {
                    totalShares += weeklyData[i].sharesBought;
                }
                
                return {
                    totalInvested: lastEntry.cumulativeInvested,
                    currentValue: lastEntry.cumulativeValue,
                    totalPnL: lastEntry.cumulativePnL,
                    totalShares: totalShares
                };
            }
            
            handleParameterChange(event) {
                const target = event.target;
                const name = target.name;
                const value = target.value;
                
                const newState = {};
                newState[name] = value;
                this.setState(newState);
            }
            
            formatCurrency(amount) {
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD'
                }).format(amount);
            }
            
            formatPercent(percent) {
                const sign = percent >= 0 ? '+' : '';
                return sign + percent.toFixed(2) + '%';
            }
            
            formatShares(shares) {
                return shares.toFixed(4);
            }
            
            render() {
                const state = this.state;
                const weeklyData = state.weeklyData;
                const loading = state.loading;
                const error = state.error;
                const totalInvested = state.totalInvested;
                const currentValue = state.currentValue;
                const totalPnL = state.totalPnL;
                const totalShares = state.totalShares;
                
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
                
                const self = this;
                
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
                                    value: state.weeklyAmount,
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
                                                    React.createElement('th', {}, 'Cumulative P&L')
                                                ])
                                            ]),
                                            React.createElement('tbody', {}, 
                                                weeklyData.map(function(week, index) {
                                                    return React.createElement('tr', { key: index }, [
                                                        React.createElement('td', { key: 'week' }, week.week),
                                                        React.createElement('td', { key: 'date' }, week.date),
                                                        React.createElement('td', { key: 'investment' }, self.formatCurrency(week.investmentAmount)),
                                                        React.createElement('td', { key: 'sharePrice' }, self.formatCurrency(week.sharePrice)),
                                                        React.createElement('td', { key: 'shares' }, self.formatShares(week.sharesBought)),
                                                        React.createElement('td', { key: 'currentPrice' }, self.formatCurrency(week.currentPrice)),
                                                        React.createElement('td', { key: 'currentValue' }, self.formatCurrency(week.currentValue)),
                                                        React.createElement('td', { 
                                                            key: 'pnl',
                                                            className: week.pnl >= 0 ? 'text-success' : 'text-danger'
                                                        }, self.formatCurrency(week.pnl)),
                                                        React.createElement('td', { 
                                                            key: 'cumulativePnL',
                                                            className: week.cumulativePnL >= 0 ? 'text-success' : 'text-danger'
                                                        }, self.formatCurrency(week.cumulativePnL))
                                                    ]);
                                                })
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
