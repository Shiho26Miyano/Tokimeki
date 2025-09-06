import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { X, BarChart3, TrendingUp, Volume2 } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import useStore from '../store/useStore';
import apiService from '../services/api';

const ChartModal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  padding: 2rem;
`;

const ChartContainer = styled.div`
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #333;
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const ChartHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const ChartTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ChartControls = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const ControlButton = styled.button`
  background: ${props => props.active ? '#00d4ff' : 'transparent'};
  color: ${props => props.active ? '#000000' : '#9ca3af'};
  border: 1px solid ${props => props.active ? '#00d4ff' : '#333'};
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    background: ${props => props.active ? '#00d4ff' : '#333'};
    color: ${props => props.active ? '#000000' : '#ffffff'};
  }
`;

const CloseButton = styled.button`
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  
  &:hover {
    color: #ffffff;
    background: #333;
  }
`;

const ChartContent = styled.div`
  flex: 1;
  min-height: 400px;
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid #333;
`;

const ChartInfo = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
`;

const InfoCard = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #333;
  text-align: center;
`;

const InfoValue = styled.div`
  font-size: 1.25rem;
  font-weight: 700;
  color: ${props => props.positive ? '#22c55e' : props.negative ? '#ef4444' : '#ffffff'};
  margin-bottom: 0.25rem;
`;

const InfoLabel = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #9ca3af;
  font-size: 1rem;
`;

const DetailedChart = ({ symbol, isOpen, onClose }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState('1d');
  const [chartType, setChartType] = useState('candlestick');
  const { marketData } = useStore();

  useEffect(() => {
    if (isOpen && symbol) {
      loadChartData();
    }
  }, [isOpen, symbol, timeframe]);

  const loadChartData = async () => {
    setLoading(true);
    try {
      const data = await apiService.getChartData(symbol, timeframe, 200);
      if (data.success) {
        setChartData(data.data);
      } else {
        // Generate mock data if API fails
        setChartData(generateMockData());
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
      setChartData(generateMockData());
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = () => {
    const data = [];
    const basePrice = marketData[symbol]?.price || 4000;
    let currentPrice = basePrice;
    const now = new Date();
    
    for (let i = 0; i < 200; i++) {
      const timestamp = new Date(now.getTime() - (199 - i) * 60 * 60 * 1000); // Hourly data
      const change = (Math.random() - 0.5) * 0.02; // ±1% change
      const open = currentPrice;
      const close = currentPrice * (1 + change);
      const high = Math.max(open, close) * (1 + Math.random() * 0.01);
      const low = Math.min(open, close) * (1 - Math.random() * 0.01);
      const volume = Math.random() * 1000000;
      
      data.push({
        timestamp: timestamp.toISOString(),
        open,
        high,
        low,
        close,
        volume
      });
      
      currentPrice = close;
    }
    
    return data;
  };

  const prepareChartData = () => {
    if (!chartData) return [];
    
    return chartData.map(d => ({
      time: new Date(d.timestamp).toLocaleTimeString(),
      close: d.close,
      volume: d.volume,
      high: d.high,
      low: d.low
    }));
  };

  const getCurrentPrice = () => {
    if (!chartData || chartData.length === 0) return 0;
    return chartData[chartData.length - 1].close;
  };

  const getPriceChange = () => {
    if (!chartData || chartData.length < 2) return 0;
    const current = chartData[chartData.length - 1].close;
    const previous = chartData[chartData.length - 2].close;
    return ((current - previous) / previous) * 100;
  };

  const getVolume = () => {
    if (!chartData || chartData.length === 0) return 0;
    return chartData[chartData.length - 1].volume;
  };

  const getHigh = () => {
    if (!chartData) return 0;
    return Math.max(...chartData.map(d => d.high));
  };

  const getLow = () => {
    if (!chartData) return 0;
    return Math.min(...chartData.map(d => d.low));
  };


  if (!isOpen) return null;

  const currentPrice = getCurrentPrice();
  const priceChange = getPriceChange();
  const isPositive = priceChange >= 0;

  return (
    <ChartModal onClick={onClose}>
      <ChartContainer onClick={(e) => e.stopPropagation()}>
        <ChartHeader>
          <ChartTitle>
            <BarChart3 size={20} />
            {symbol} - Detailed Chart
          </ChartTitle>
          <ChartControls>
            <ControlButton
              active={timeframe === '1d'}
              onClick={() => setTimeframe('1d')}
            >
              1D
            </ControlButton>
            <ControlButton
              active={timeframe === '7d'}
              onClick={() => setTimeframe('7d')}
            >
              7D
            </ControlButton>
            <ControlButton
              active={timeframe === '30d'}
              onClick={() => setTimeframe('30d')}
            >
              30D
            </ControlButton>
            <ControlButton
              active={chartType === 'candlestick'}
              onClick={() => setChartType('candlestick')}
            >
              <BarChart3 size={14} />
              Candles
            </ControlButton>
            <ControlButton
              active={chartType === 'line'}
              onClick={() => setChartType('line')}
            >
              <TrendingUp size={14} />
              Line
            </ControlButton>
            <CloseButton onClick={onClose}>
              <X size={16} />
            </CloseButton>
          </ChartControls>
        </ChartHeader>

        <ChartContent>
          {loading ? (
            <LoadingSpinner>Loading chart data...</LoadingSpinner>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={prepareChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="time" 
                  stroke="#9ca3af"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#9ca3af"
                  fontSize={12}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
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
                    name === 'close' ? 'Price' : name
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#00d4ff"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#00d4ff' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartContent>

        <ChartInfo>
          <InfoCard>
            <InfoValue positive={isPositive}>
              ${currentPrice.toFixed(2)}
            </InfoValue>
            <InfoLabel>Current Price</InfoLabel>
          </InfoCard>
          
          <InfoCard>
            <InfoValue positive={isPositive}>
              {isPositive ? '+' : ''}{priceChange.toFixed(2)}%
            </InfoValue>
            <InfoLabel>Change</InfoLabel>
          </InfoCard>
          
          <InfoCard>
            <InfoValue>
              ${getHigh().toFixed(2)}
            </InfoValue>
            <InfoLabel>24h High</InfoLabel>
          </InfoCard>
          
          <InfoCard>
            <InfoValue>
              ${getLow().toFixed(2)}
            </InfoValue>
            <InfoLabel>24h Low</InfoLabel>
          </InfoCard>
          
          <InfoCard>
            <InfoValue>
              {getVolume().toLocaleString()}
            </InfoValue>
            <InfoLabel>Volume</InfoLabel>
          </InfoCard>
        </ChartInfo>
      </ChartContainer>
    </ChartModal>
  );
};

export default DetailedChart;
