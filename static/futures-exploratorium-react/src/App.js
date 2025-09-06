import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

// Components
import Header from './components/Header';
import MarketOverview from './components/MarketOverview';
import StrategyPerformance from './components/StrategyPerformance';
import RiskMetrics from './components/RiskMetrics';
import AlertsFeed from './components/AlertsFeed';
import DetailedChart from './components/DetailedChart';

// Services
import useStore from './store/useStore';
import apiService from './services/api';
import websocketService from './services/websocket';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  color: #ffffff;
`;

const MainContent = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  
  @media (max-width: 768px) {
    padding: 1rem;
  }
`;

const DashboardGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const FullWidthSection = styled.div`
  grid-column: 1 / -1;
`;

const LoadingOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
`;

const LoadingContent = styled.div`
  text-align: center;
  color: #ffffff;
`;

const LoadingSpinner = styled.div`
  width: 50px;
  height: 50px;
  border: 3px solid #333;
  border-top: 3px solid #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const ErrorMessage = styled.div`
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
  font-weight: 500;
`;

const App = () => {
  const {
    systemHealth,
    marketData,
    strategyPerformance,
    riskMetrics,
    isConnected,
    setSystemHealth,
    setMarketData,
    setStrategyPerformance,
    setRiskMetrics,
    setConnected,
    setLastUpdate,
    addAlert,
    addActivity
  } = useStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSymbol, setExpandedSymbol] = useState(null);

  // Initialize app data
  useEffect(() => {
    const initializeApp = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load initial data
        const [healthData, marketData, performanceData, riskData] = await Promise.allSettled([
          apiService.getHealthCheck(),
          apiService.getMarketOverview(),
          apiService.getStrategyPerformance(),
          apiService.getRiskMetrics()
        ]);

        // Update system health
        if (healthData.status === 'fulfilled' && healthData.value.success) {
          setSystemHealth({
            status: healthData.value.health.status,
            score: 0.95, // Mock score
            uptime: healthData.value.health.uptime,
            lastUpdate: new Date()
          });
        }

        // Update market data
        if (marketData.status === 'fulfilled' && marketData.value.success) {
          const market = marketData.value.market_overview;
          setMarketData({
            ES: {
              price: market.ES?.price || 4250.50,
              change: market.ES?.change || 12.50,
              changePercent: market.ES?.change_percent || 0.29,
              volume: market.ES?.volume || 1500000,
              sparkline: market.ES?.sparkline || []
            },
            NQ: {
              price: market.NQ?.price || 14500.25,
              change: market.NQ?.change || -25.75,
              changePercent: market.NQ?.change_percent || -0.18,
              volume: market.NQ?.volume || 800000,
              sparkline: market.NQ?.sparkline || []
            },
            RTY: {
              price: market.RTY?.price || 1850.75,
              change: market.RTY?.change || 8.25,
              changePercent: market.RTY?.change_percent || 0.45,
              volume: market.RTY?.volume || 450000,
              sparkline: market.RTY?.sparkline || []
            }
          });
        }

        // Update strategy performance
        if (performanceData.status === 'fulfilled' && performanceData.value.success) {
          const perf = performanceData.value.performance;
          setStrategyPerformance({
            pnl: perf?.pnl || 1250.75,
            sharpe: perf?.sharpe_ratio || 1.85,
            drawdown: perf?.max_drawdown || -0.08,
            winRate: perf?.win_rate || 0.68,
            equityCurve: perf?.equity_curve || [],
            isRunningBacktest: false
          });
        }

        // Update risk metrics
        if (riskData.status === 'fulfilled' && riskData.value.success) {
          const risk = riskData.value.risk_metrics;
          setRiskMetrics({
            var95: risk?.var_95 || 0.025,
            volatility: risk?.volatility || 0.18,
            correlationMatrix: risk?.correlation_matrix || {},
            alerts: risk?.alerts || []
          });
        }

        setLastUpdate(new Date());
        setLoading(false);

      } catch (error) {
        console.error('Error initializing app:', error);
        setError('Failed to load application data. Please refresh the page.');
        setLoading(false);
      }
    };

    initializeApp();
  }, [setSystemHealth, setMarketData, setStrategyPerformance, setRiskMetrics, setLastUpdate]);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      websocketService.connect();
      
      // Subscribe to WebSocket events
      const unsubscribeConnected = websocketService.subscribe('connected', (connected) => {
        setConnected(connected);
        if (connected) {
          toast.success('Connected to real-time data feed');
        } else {
          toast.error('Disconnected from real-time data feed');
        }
      });

      const unsubscribeMarketData = websocketService.subscribeToMarketData((data) => {
        setMarketData(prev => ({
          ...prev,
          [data.symbol]: {
            ...prev[data.symbol],
            price: data.price,
            change: data.change,
            changePercent: data.changePercent,
            volume: data.volume,
            sparkline: [...(prev[data.symbol]?.sparkline || []).slice(-19), data.price]
          }
        }));
      });

      const unsubscribeAlerts = websocketService.subscribeToAlerts((alert) => {
        addAlert({
          id: Date.now() + Math.random(),
          type: alert.type,
          level: alert.level,
          message: alert.message,
          timestamp: new Date(),
          symbol: alert.symbol
        });
        toast.error(`Alert: ${alert.message}`);
      });

      const unsubscribePerformance = websocketService.subscribeToPerformance((performance) => {
        setStrategyPerformance(prev => ({
          ...prev,
          pnl: performance.pnl,
          sharpe: performance.sharpe,
          drawdown: performance.drawdown,
          winRate: performance.winRate
        }));
      });

      const unsubscribeSystemHealth = websocketService.subscribeToSystemHealth((health) => {
        setSystemHealth(prev => ({
          ...prev,
          status: health.status,
          score: health.score,
          uptime: health.uptime
        }));
      });

      // Cleanup function
      return () => {
        unsubscribeConnected();
        unsubscribeMarketData();
        unsubscribeAlerts();
        unsubscribePerformance();
        unsubscribeSystemHealth();
        websocketService.disconnect();
      };
    };

    const cleanup = connectWebSocket();
    return cleanup;
  }, [setConnected, setMarketData, addAlert, setStrategyPerformance, setSystemHealth]);

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [healthData, marketData] = await Promise.allSettled([
          apiService.getHealthCheck(),
          apiService.getMarketOverview()
        ]);

        if (healthData.status === 'fulfilled' && healthData.value.success) {
          setSystemHealth(prev => ({
            ...prev,
            status: healthData.value.health.status,
            lastUpdate: new Date()
          }));
        }

        if (marketData.status === 'fulfilled' && marketData.value.success) {
          const market = marketData.value.market_overview;
          setMarketData(prev => ({
            ...prev,
            ES: {
              ...prev.ES,
              price: market.ES?.price || prev.ES.price,
              change: market.ES?.change || prev.ES.change,
              changePercent: market.ES?.change_percent || prev.ES.changePercent
            },
            NQ: {
              ...prev.NQ,
              price: market.NQ?.price || prev.NQ.price,
              change: market.NQ?.change || prev.NQ.change,
              changePercent: market.NQ?.change_percent || prev.NQ.changePercent
            },
            RTY: {
              ...prev.RTY,
              price: market.RTY?.price || prev.RTY.price,
              change: market.RTY?.change || prev.RTY.change,
              changePercent: market.RTY?.change_percent || prev.RTY.changePercent
            }
          }));
        }

        setLastUpdate(new Date());
      } catch (error) {
        console.error('Error refreshing data:', error);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [setSystemHealth, setMarketData, setLastUpdate]);

  if (loading) {
    return (
      <LoadingOverlay>
        <LoadingContent>
          <LoadingSpinner />
          <div>Loading Futures Exploratorium...</div>
        </LoadingContent>
      </LoadingOverlay>
    );
  }

  return (
    <AppContainer>
      <Header />
      
      <MainContent>
        {error && <ErrorMessage>{error}</ErrorMessage>}
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <DashboardGrid>
            <MarketOverview />
            <StrategyPerformance />
            <RiskMetrics />
          </DashboardGrid>
          
          <FullWidthSection>
            <AlertsFeed />
          </FullWidthSection>
        </motion.div>
      </MainContent>

      <DetailedChart 
        symbol={expandedSymbol}
        isOpen={!!expandedSymbol}
        onClose={() => setExpandedSymbol(null)}
      />
    </AppContainer>
  );
};

export default App;
