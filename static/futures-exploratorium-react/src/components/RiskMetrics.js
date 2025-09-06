import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Shield, AlertTriangle, TrendingUp, Activity, AlertCircle } from 'lucide-react';
import Plot from 'react-plotly.js';
import useStore from '../store/useStore';

const RiskMetricsContainer = styled.div`
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
  position: relative;
`;

const MetricValue = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => {
    if (props.level === 'high') return '#ef4444';
    if (props.level === 'medium') return '#f59e0b';
    if (props.level === 'low') return '#22c55e';
    return '#ffffff';
  }};
  margin-bottom: 0.25rem;
`;

const MetricLabel = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const AlertBadge = styled.div`
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
`;

const ChartSection = styled.div`
  margin-bottom: 1.5rem;
`;

const ChartContainer = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid #333;
  height: 300px;
`;

const ChartTitle = styled.div`
  font-size: 0.875rem;
  color: #9ca3af;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const AlertsList = styled.div`
  max-height: 200px;
  overflow-y: auto;
`;

const AlertItem = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border-left: 4px solid ${props => {
    switch (props.level) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  }};
  border: 1px solid #333;
`;

const AlertHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
`;

const AlertType = styled.div`
  font-size: 0.75rem;
  font-weight: 600;
  color: ${props => {
    switch (props.level) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  }};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const AlertTime = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
`;

const AlertMessage = styled.div`
  font-size: 0.875rem;
  color: #ffffff;
`;

const RiskMetrics = () => {
  const { riskMetrics } = useStore();
  const [correlationData, setCorrelationData] = useState(null);

  useEffect(() => {
    // Generate correlation matrix data
    const symbols = ['ES', 'NQ', 'RTY', 'CL', 'GC'];
    const correlationMatrix = {};
    
    symbols.forEach(symbol1 => {
      correlationMatrix[symbol1] = {};
      symbols.forEach(symbol2 => {
        if (symbol1 === symbol2) {
          correlationMatrix[symbol1][symbol2] = 1.0;
        } else {
          // Generate realistic correlation values
          correlationMatrix[symbol1][symbol2] = Math.random() * 0.8 - 0.4;
        }
      });
    });

    // Prepare data for Plotly heatmap
    const z = symbols.map(symbol1 => 
      symbols.map(symbol2 => correlationMatrix[symbol1][symbol2])
    );

    setCorrelationData({
      z,
      x: symbols,
      y: symbols,
      type: 'heatmap',
      colorscale: [
        [0, '#ef4444'],
        [0.5, '#f59e0b'],
        [1, '#22c55e']
      ],
      showscale: true,
      colorbar: {
        title: 'Correlation',
        titleside: 'right',
        tickmode: 'array',
        tickvals: [-1, -0.5, 0, 0.5, 1],
        ticktext: ['-1', '-0.5', '0', '0.5', '1']
      }
    });
  }, []);

  const formatPercent = (value) => {
    if (value === 0 || value === null || value === undefined) return '0.00%';
    return `${(value * 100).toFixed(2)}%`;
  };

  const getRiskLevel = (value, thresholds) => {
    if (value >= thresholds.high) return 'high';
    if (value >= thresholds.medium) return 'medium';
    return 'low';
  };

  const getVaRLevel = (value) => getRiskLevel(value, { high: 0.05, medium: 0.03 });
  const getVolatilityLevel = (value) => getRiskLevel(value, { high: 0.3, medium: 0.2 });
  const getDrawdownLevel = (value) => getRiskLevel(Math.abs(value), { high: 0.1, medium: 0.05 });

  // Mock alerts data
  const alerts = [
    {
      id: 1,
      type: 'VaR Alert',
      level: 'high',
      message: 'VaR exceeded threshold for ES position',
      timestamp: new Date(Date.now() - 5 * 60 * 1000)
    },
    {
      id: 2,
      type: 'Volatility',
      level: 'medium',
      message: 'High volatility detected in NQ futures',
      timestamp: new Date(Date.now() - 15 * 60 * 1000)
    },
    {
      id: 3,
      type: 'Correlation',
      level: 'low',
      message: 'Correlation between ES and NQ increased',
      timestamp: new Date(Date.now() - 30 * 60 * 1000)
    }
  ];

  const plotlyConfig = {
    displayModeBar: false,
    responsive: true
  };

  const plotlyLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#ffffff' },
    xaxis: { 
      color: '#9ca3af',
      gridcolor: '#333',
      zerolinecolor: '#333'
    },
    yaxis: { 
      color: '#9ca3af',
      gridcolor: '#333',
      zerolinecolor: '#333'
    }
  };

  return (
    <RiskMetricsContainer>
      <Header>
        <Title>
          <Shield size={20} />
          Risk Metrics
        </Title>
      </Header>

      <MetricsGrid>
        <MetricCard>
          <MetricValue level={getVaRLevel(riskMetrics.var95)}>
            {formatPercent(riskMetrics.var95)}
          </MetricValue>
          <MetricLabel>VaR 95%</MetricLabel>
          {getVaRLevel(riskMetrics.var95) === 'high' && <AlertBadge>!</AlertBadge>}
        </MetricCard>
        
        <MetricCard>
          <MetricValue level={getVolatilityLevel(riskMetrics.volatility)}>
            {formatPercent(riskMetrics.volatility)}
          </MetricValue>
          <MetricLabel>Volatility</MetricLabel>
          {getVolatilityLevel(riskMetrics.volatility) === 'high' && <AlertBadge>!</AlertBadge>}
        </MetricCard>
        
        <MetricCard>
          <MetricValue>
            {formatPercent(riskMetrics.var95 * 2)}
          </MetricValue>
          <MetricLabel>Expected Shortfall</MetricLabel>
        </MetricCard>
        
        <MetricCard>
          <MetricValue>
            {formatPercent(riskMetrics.var95 * 0.5)}
          </MetricValue>
          <MetricLabel>Conditional VaR</MetricLabel>
        </MetricCard>
      </MetricsGrid>

      <ChartSection>
        <ChartTitle>
          <Activity size={14} />
          Correlation Heatmap
        </ChartTitle>
        <ChartContainer>
          {correlationData && (
            <Plot
              data={[correlationData]}
              layout={{
                ...plotlyLayout,
                title: {
                  text: 'Asset Correlation Matrix',
                  font: { color: '#ffffff', size: 14 }
                },
                width: '100%',
                height: 250,
                margin: { l: 50, r: 50, t: 40, b: 50 }
              }}
              config={plotlyConfig}
              style={{ width: '100%', height: '100%' }}
            />
          )}
        </ChartContainer>
      </ChartSection>

      <ChartTitle>
        <AlertCircle size={14} />
        Risk Alerts
      </ChartTitle>
      <AlertsList>
        {alerts.map(alert => (
          <AlertItem key={alert.id} level={alert.level}>
            <AlertHeader>
              <AlertType level={alert.level}>{alert.type}</AlertType>
              <AlertTime>
                {alert.timestamp.toLocaleTimeString()}
              </AlertTime>
            </AlertHeader>
            <AlertMessage>{alert.message}</AlertMessage>
          </AlertItem>
        ))}
      </AlertsList>
    </RiskMetricsContainer>
  );
};

export default RiskMetrics;
