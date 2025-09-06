import React from 'react';
import styled from 'styled-components';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import useStore from '../store/useStore';

const MarketOverviewContainer = styled.div`
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

const SymbolsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
`;

const SymbolCard = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #333;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    border-color: #00d4ff;
  }

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #00d4ff 0%, #ff6b35 100%);
  }
`;

const SymbolHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const SymbolName = styled.div`
  font-size: 1.1rem;
  font-weight: 600;
  color: #ffffff;
`;

const SymbolDescription = styled.div`
  font-size: 0.875rem;
  color: #9ca3af;
`;

const PriceSection = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const Price = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: #ffffff;
`;

const ChangeContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
`;

const Change = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: ${props => props.positive ? '#22c55e' : '#ef4444'};
  display: flex;
  align-items: center;
  gap: 0.25rem;
`;

const ChangePercent = styled.div`
  font-size: 0.875rem;
  color: ${props => props.positive ? '#22c55e' : '#ef4444'};
`;

const SparklineContainer = styled.div`
  height: 60px;
  width: 100%;
  margin-top: 0.75rem;
`;

const VolumeInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #333;
`;

const VolumeLabel = styled.span`
  font-size: 0.75rem;
  color: #9ca3af;
`;

const VolumeValue = styled.span`
  font-size: 0.875rem;
  color: #ffffff;
  font-weight: 500;
`;

const MarketOverview = () => {
  const { marketData, setExpandedSymbol, expandedSymbol } = useStore();

  const symbols = [
    { key: 'ES', name: 'ES', description: 'S&P 500 E-mini' },
    { key: 'NQ', name: 'NQ', description: 'Nasdaq E-mini' },
    { key: 'RTY', name: 'RTY', description: 'Russell 2000 E-mini' }
  ];

  const formatPrice = (price) => {
    if (price === 0 || price === null || price === undefined) return 'N/A';
    return price.toFixed(2);
  };

  const formatChange = (change) => {
    if (change === 0 || change === null || change === undefined) return 'N/A';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}`;
  };

  const formatChangePercent = (changePercent) => {
    if (changePercent === 0 || changePercent === null || changePercent === undefined) return 'N/A';
    const sign = changePercent >= 0 ? '+' : '';
    return `${sign}${changePercent.toFixed(2)}%`;
  };

  const formatVolume = (volume) => {
    if (volume === 0 || volume === null || volume === undefined) return 'N/A';
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  const generateSparklineData = (symbolData) => {
    if (!symbolData.sparkline || symbolData.sparkline.length === 0) {
      // Generate mock data if no real data
      const data = [];
      const basePrice = symbolData.price || 4000;
      for (let i = 0; i < 20; i++) {
        data.push({
          value: basePrice + (Math.random() - 0.5) * 100,
          time: i
        });
      }
      return data;
    }
    return symbolData.sparkline.map((value, index) => ({
      value,
      time: index
    }));
  };

  const handleSymbolClick = (symbol) => {
    setExpandedSymbol(expandedSymbol === symbol ? null : symbol);
  };

  return (
    <MarketOverviewContainer>
      <Header>
        <Title>
          <BarChart3 size={20} />
          Market Overview
        </Title>
      </Header>
      
      <SymbolsGrid>
        {symbols.map((symbol) => {
          const data = marketData[symbol.key];
          const isPositive = data.change >= 0;
          const sparklineData = generateSparklineData(data);
          
          return (
            <SymbolCard 
              key={symbol.key}
              onClick={() => handleSymbolClick(symbol.key)}
            >
              <SymbolHeader>
                <div>
                  <SymbolName>{symbol.name}</SymbolName>
                  <SymbolDescription>{symbol.description}</SymbolDescription>
                </div>
              </SymbolHeader>
              
              <PriceSection>
                <Price>${formatPrice(data.price)}</Price>
                <ChangeContainer>
                  <Change positive={isPositive}>
                    {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                    {formatChange(data.change)}
                  </Change>
                  <ChangePercent positive={isPositive}>
                    {formatChangePercent(data.changePercent)}
                  </ChangePercent>
                </ChangeContainer>
              </PriceSection>
              
              <SparklineContainer>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sparklineData}>
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={isPositive ? '#22c55e' : '#ef4444'}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 3, fill: isPositive ? '#22c55e' : '#ef4444' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </SparklineContainer>
              
              <VolumeInfo>
                <VolumeLabel>Volume</VolumeLabel>
                <VolumeValue>{formatVolume(data.volume)}</VolumeValue>
              </VolumeInfo>
            </SymbolCard>
          );
        })}
      </SymbolsGrid>
    </MarketOverviewContainer>
  );
};

export default MarketOverview;
