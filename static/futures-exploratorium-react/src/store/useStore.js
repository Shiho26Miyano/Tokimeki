import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

const useStore = create(
  subscribeWithSelector((set, get) => ({
    // System Health
    systemHealth: {
      status: 'loading',
      score: 0,
      uptime: '0%',
      lastUpdate: null
    },

    // Market Data
    marketData: {
      ES: { price: 0, change: 0, changePercent: 0, volume: 0, sparkline: [] },
      NQ: { price: 0, change: 0, changePercent: 0, volume: 0, sparkline: [] },
      RTY: { price: 0, change: 0, changePercent: 0, volume: 0, sparkline: [] }
    },

    // Strategy Performance
    strategyPerformance: {
      pnl: 0,
      sharpe: 0,
      drawdown: 0,
      winRate: 0,
      equityCurve: [],
      isRunningBacktest: false
    },

    // Risk Metrics
    riskMetrics: {
      var95: 0,
      volatility: 0,
      correlationMatrix: {},
      alerts: []
    },

    // Alerts & Activity
    alerts: [],
    activity: [],

    // UI State
    selectedSymbol: 'ES',
    expandedSymbol: null,
    isConnected: false,
    lastUpdate: null,

    // Actions
    updateSystemHealth: (health) => set({ systemHealth: health }),
    updateMarketData: (data) => set({ marketData: data }),
    updateStrategyPerformance: (performance) => set({ strategyPerformance: performance }),
    updateRiskMetrics: (metrics) => set({ riskMetrics: metrics }),
    addAlert: (alert) => set((state) => ({ 
      alerts: [alert, ...state.alerts.slice(0, 49)] 
    })),
    addActivity: (activity) => set((state) => ({ 
      activity: [activity, ...state.activity.slice(0, 49)] 
    })),
    setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
    setExpandedSymbol: (symbol) => set({ expandedSymbol: symbol }),
    setConnected: (connected) => set({ isConnected: connected }),
    setLastUpdate: (timestamp) => set({ lastUpdate: timestamp }),
    setRunningBacktest: (running) => set((state) => ({
      strategyPerformance: { ...state.strategyPerformance, isRunningBacktest: running }
    }))
  }))
);

export default useStore;
