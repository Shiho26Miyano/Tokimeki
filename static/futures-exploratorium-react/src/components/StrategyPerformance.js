import React, { useState } from 'react';
import styled from 'styled-components';
import { TrendingUp, TrendingDown, Play, Loader, Target, Shield, AlertTriangle } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import useStore from '../store/useStore';
import apiService from '../services/api';
import toast from 'react-hot-toast';

const StrategyPerformanceContainer = styled.div`
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const Title = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const BacktestButton = styled.button`
  background: linear-gradient(135deg, #00d4ff 0%, #ff6b35 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.3);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 212, 255, 0.4);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
`;

const MetricCard = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  border: 1px solid #333;
`;

const MetricValue = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.positive ? '#22c55e' : props.negative ? '#ef4444' : '#ffffff'};
  margin-bottom: 0.25rem;
`;

const MetricLabel = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ChartContainer = styled.div`
  height: 200px;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid #333;
`;

const ChartTitle = styled.div`
  font-size: 0.875rem;
  color: #9ca3af;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const BacktestModal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
`;

const ModalContent = styled.div`
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #333;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const ModalTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 1.5rem;
  
  &:hover {
    color: #ffffff;
  }
`;

const FormGroup = styled.div`
  margin-bottom: 1rem;
`;

const Label = styled.label`
  display: block;
  font-size: 0.875rem;
  color: #9ca3af;
  margin-bottom: 0.5rem;
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #333;
  border-radius: 8px;
  background: #2a2a2a;
  color: #ffffff;
  font-size: 0.875rem;
  
  &:focus {
    outline: none;
    border-color: #00d4ff;
  }
`;

const DateInput = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #333;
  border-radius: 8px;
  background: #2a2a2a;
  color: #ffffff;
  font-size: 0.875rem;
  
  &:focus {
    outline: none;
    border-color: #00d4ff;
  }
`;

const StrategyPerformance = () => {
  const { strategyPerformance, setRunningBacktest } = useStore();
  const [showBacktestModal, setShowBacktestModal] = useState(false);
  const [backtestConfig, setBacktestConfig] = useState({
    symbols: ['ES=F'],
    startDate: '2024-01-01',
    endDate: '2024-12-31'
  });

  const formatCurrency = (value) => {
    if (value === 0 || value === null || value === undefined) return '$0.00';
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${Math.abs(value).toFixed(2)}`;
  };

  const formatPercent = (value) => {
    if (value === 0 || value === null || value === undefined) return '0.00%';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value, decimals = 2) => {
    if (value === 0 || value === null || value === undefined) return '0.00';
    return value.toFixed(decimals);
  };

  const generateEquityCurveData = () => {
    if (strategyPerformance.equityCurve && strategyPerformance.equityCurve.length > 0) {
      return strategyPerformance.equityCurve;
    }
    
    // Generate mock equity curve data
    const data = [];
    const baseValue = 100000;
    let currentValue = baseValue;
    
    for (let i = 0; i < 30; i++) {
      const change = (Math.random() - 0.5) * 0.02; // ±1% daily change
      currentValue *= (1 + change);
      data.push({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: currentValue,
        pnl: currentValue - baseValue
      });
    }
    
    return data;
  };

  const handleRunBacktest = async () => {
    setRunningBacktest(true);
    setShowBacktestModal(false);
    
    try {
      const result = await apiService.runBacktest(
        backtestConfig.symbols,
        backtestConfig.startDate,
        backtestConfig.endDate
      );
      
      if (result.success) {
        toast.success('Backtest completed successfully!');
        // Update strategy performance with results
        // This would typically come from the API response
      } else {
        toast.error('Backtest failed: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      toast.error('Backtest failed: ' + error.message);
    } finally {
      setRunningBacktest(false);
    }
  };

  const equityCurveData = generateEquityCurveData();

  return (
    <>
      <StrategyPerformanceContainer>
        <Header>
          <Title>
            <TrendingUp size={20} />
            Strategy Performance
          </Title>
          <BacktestButton 
            onClick={() => setShowBacktestModal(true)}
            disabled={strategyPerformance.isRunningBacktest}
          >
            {strategyPerformance.isRunningBacktest ? (
              <Loader size={16} className="pulse" />
            ) : (
              <Play size={16} />
            )}
            {strategyPerformance.isRunningBacktest ? 'Running...' : 'Run Backtest'}
          </BacktestButton>
        </Header>

        <MetricsGrid>
          <MetricCard>
            <MetricValue positive={strategyPerformance.pnl >= 0}>
              {formatCurrency(strategyPerformance.pnl)}
            </MetricValue>
            <MetricLabel>PnL</MetricLabel>
          </MetricCard>
          
          <MetricCard>
            <MetricValue>
              {formatNumber(strategyPerformance.sharpe)}
            </MetricValue>
            <MetricLabel>Sharpe Ratio</MetricLabel>
          </MetricCard>
          
          <MetricCard>
            <MetricValue negative={strategyPerformance.drawdown < 0}>
              {formatPercent(strategyPerformance.drawdown)}
            </MetricValue>
            <MetricLabel>Max Drawdown</MetricLabel>
          </MetricCard>
          
          <MetricCard>
            <MetricValue>
              {formatPercent(strategyPerformance.winRate)}
            </MetricValue>
            <MetricLabel>Win Rate</MetricLabel>
          </MetricCard>
        </MetricsGrid>

        <ChartContainer>
          <ChartTitle>
            <Target size={14} />
            Equity Curve
          </ChartTitle>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={equityCurveData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis 
                stroke="#9ca3af"
                fontSize={12}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: '8px',
                  color: '#ffffff'
                }}
                formatter={(value, name) => [
                  `$${value.toFixed(2)}`,
                  name === 'value' ? 'Portfolio Value' : 'PnL'
                ]}
                labelFormatter={(label) => `Date: ${new Date(label).toLocaleDateString()}`}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#00d4ff"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#00d4ff' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </StrategyPerformanceContainer>

      {showBacktestModal && (
        <BacktestModal onClick={() => setShowBacktestModal(false)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>Run Backtest</ModalTitle>
              <CloseButton onClick={() => setShowBacktestModal(false)}>×</CloseButton>
            </ModalHeader>
            
            <FormGroup>
              <Label>Symbols</Label>
              <Select
                multiple
                value={backtestConfig.symbols}
                onChange={(e) => setBacktestConfig({
                  ...backtestConfig,
                  symbols: Array.from(e.target.selectedOptions, option => option.value)
                })}
              >
                <option value="ES=F">ES (S&P 500)</option>
                <option value="NQ=F">NQ (Nasdaq)</option>
                <option value="RTY=F">RTY (Russell 2000)</option>
                <option value="CL=F">CL (Crude Oil)</option>
                <option value="GC=F">GC (Gold)</option>
              </Select>
            </FormGroup>
            
            <FormGroup>
              <Label>Start Date</Label>
              <DateInput
                type="date"
                value={backtestConfig.startDate}
                onChange={(e) => setBacktestConfig({
                  ...backtestConfig,
                  startDate: e.target.value
                })}
              />
            </FormGroup>
            
            <FormGroup>
              <Label>End Date</Label>
              <DateInput
                type="date"
                value={backtestConfig.endDate}
                onChange={(e) => setBacktestConfig({
                  ...backtestConfig,
                  endDate: e.target.value
                })}
              />
            </FormGroup>
            
            <BacktestButton onClick={handleRunBacktest} style={{ width: '100%', justifyContent: 'center' }}>
              <Play size={16} />
              Run Backtest
            </BacktestButton>
          </ModalContent>
        </BacktestModal>
      )}
    </>
  );
};

export default StrategyPerformance;
