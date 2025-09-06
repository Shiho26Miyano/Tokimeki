import React from 'react';
import styled from 'styled-components';
import { Activity, Wifi, WifiOff, AlertTriangle, CheckCircle } from 'lucide-react';
import useStore from '../store/useStore';

const HeaderContainer = styled.header`
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  border-bottom: 1px solid #333;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 100;
  
  @media (max-width: 768px) {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
  }
`;

const AppTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const AppName = styled.h1`
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff 0%, #ff6b35 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
`;

const ExperimentalBadge = styled.span`
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
`;

const SystemHealth = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 0.5rem;
  }
`;

const HealthIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: ${props => {
    switch (props.status) {
      case 'healthy': return 'rgba(34, 197, 94, 0.1)';
      case 'warning': return 'rgba(245, 158, 11, 0.1)';
      case 'error': return 'rgba(239, 68, 68, 0.1)';
      default: return 'rgba(107, 114, 128, 0.1)';
    }
  }};
  border: 1px solid ${props => {
    switch (props.status) {
      case 'healthy': return 'rgba(34, 197, 94, 0.3)';
      case 'warning': return 'rgba(245, 158, 11, 0.3)';
      case 'error': return 'rgba(239, 68, 68, 0.3)';
      default: return 'rgba(107, 114, 128, 0.3)';
    }
  }};
`;

const HealthIcon = styled.div`
  color: ${props => {
    switch (props.status) {
      case 'healthy': return '#22c55e';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  }};
`;

const HealthText = styled.span`
  font-weight: 500;
  color: ${props => {
    switch (props.status) {
      case 'healthy': return '#22c55e';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  }};
`;

const ConnectionStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: ${props => props.connected ? '#22c55e' : '#ef4444'};
  font-size: 0.875rem;
`;

const Header = () => {
  const { systemHealth, isConnected } = useStore();

  const getHealthStatus = () => {
    if (systemHealth.status === 'healthy' || systemHealth.status === 'Healthy') return 'healthy';
    if (systemHealth.status === 'warning' || systemHealth.status === 'Warning') return 'warning';
    if (systemHealth.status === 'error' || systemHealth.status === 'Error') return 'error';
    return 'loading';
  };

  const getHealthIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'error': return <AlertTriangle size={16} />;
      default: return <Activity size={16} className="pulse" />;
    }
  };

  const getHealthText = (status) => {
    switch (status) {
      case 'healthy': return 'Healthy';
      case 'warning': return 'Warning';
      case 'error': return 'Down';
      default: return 'Loading...';
    }
  };

  const healthStatus = getHealthStatus();

  return (
    <HeaderContainer>
      <AppTitle>
        <AppName>Futures Exploratorium</AppName>
        <ExperimentalBadge>Experimental</ExperimentalBadge>
      </AppTitle>
      
      <SystemHealth>
        <ConnectionStatus connected={isConnected}>
          {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
          {isConnected ? 'Connected' : 'Disconnected'}
        </ConnectionStatus>
        
        <HealthIndicator status={healthStatus}>
          <HealthIcon status={healthStatus}>
            {getHealthIcon(healthStatus)}
          </HealthIcon>
          <HealthText>{getHealthText(healthStatus)}</HealthText>
        </HealthIndicator>
      </SystemHealth>
    </HeaderContainer>
  );
};

export default Header;
