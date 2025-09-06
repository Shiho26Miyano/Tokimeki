import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Bell, Activity, AlertTriangle, CheckCircle, Info, X, Filter } from 'lucide-react';
import useStore from '../store/useStore';
import { formatDistanceToNow } from 'date-fns';

const AlertsFeedContainer = styled.div`
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  margin-top: 1.5rem;
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

const FilterControls = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const FilterButton = styled.button`
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

const ClearButton = styled.button`
  background: transparent;
  color: #9ca3af;
  border: 1px solid #333;
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    background: #333;
    color: #ffffff;
  }
`;

const FeedContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  max-height: 400px;
  overflow-y: auto;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const FeedSection = styled.div`
  display: flex;
  flex-direction: column;
`;

const SectionTitle = styled.h4`
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ItemsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
`;

const AlertItem = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1rem;
  border-left: 4px solid ${props => {
    switch (props.level) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#22c55e';
      case 'info': return '#3b82f6';
      default: return '#6b7280';
    }
  }};
  border: 1px solid #333;
  transition: all 0.3s ease;
  position: relative;

  &:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }
`;

const AlertHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
`;

const AlertType = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: ${props => {
    switch (props.level) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#22c55e';
      case 'info': return '#3b82f6';
      default: return '#6b7280';
    }
  }};
`;

const AlertTime = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
  white-space: nowrap;
`;

const AlertMessage = styled.div`
  font-size: 0.875rem;
  color: #ffffff;
  line-height: 1.4;
  margin-bottom: 0.5rem;
`;

const AlertDetails = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const DismissButton = styled.button`
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s ease;

  &:hover {
    color: #ffffff;
    background: #333;
  }
`;

const ActivityItem = styled.div`
  background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid #333;
  transition: all 0.3s ease;

  &:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }
`;

const ActivityHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
`;

const ActivityType = styled.div`
  font-size: 0.875rem;
  font-weight: 600;
  color: #00d4ff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ActivityTime = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
`;

const ActivityMessage = styled.div`
  font-size: 0.875rem;
  color: #ffffff;
  line-height: 1.4;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
  font-style: italic;
`;

const AlertsFeed = () => {
  const { alerts, activity, addAlert, addActivity } = useStore();
  const [filter, setFilter] = useState('all');
  const [dismissedAlerts, setDismissedAlerts] = useState(new Set());

  // Mock data generation
  useEffect(() => {
    const generateMockAlerts = () => {
      const alertTypes = [
        { type: 'VaR Alert', level: 'high', message: 'VaR threshold exceeded for ES position' },
        { type: 'Volatility', level: 'medium', message: 'High volatility detected in NQ futures' },
        { type: 'Correlation', level: 'low', message: 'Correlation between ES and NQ increased' },
        { type: 'System', level: 'info', message: 'Backtest completed successfully' },
        { type: 'Risk', level: 'high', message: 'Portfolio drawdown approaching limit' }
      ];

      const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
      const alert = {
        id: Date.now() + Math.random(),
        type: randomAlert.type,
        level: randomAlert.level,
        message: randomAlert.message,
        timestamp: new Date(),
        symbol: ['ES', 'NQ', 'RTY'][Math.floor(Math.random() * 3)]
      };

      addAlert(alert);
    };

    const generateMockActivity = () => {
      const activityTypes = [
        { type: 'TRADE', message: 'ES position opened at $4,250.50' },
        { type: 'SIGNAL', message: 'Buy signal generated for NQ futures' },
        { type: 'BACKTEST', message: 'Strategy backtest completed' },
        { type: 'RISK', message: 'Risk parameters updated' },
        { type: 'SYSTEM', message: 'Market data connection restored' }
      ];

      const randomActivity = activityTypes[Math.floor(Math.random() * activityTypes.length)];
      const activityItem = {
        id: Date.now() + Math.random(),
        type: randomActivity.type,
        message: randomActivity.message,
        timestamp: new Date()
      };

      addActivity(activityItem);
    };

    // Generate initial data
    for (let i = 0; i < 5; i++) {
      generateMockAlerts();
      generateMockActivity();
    }

    // Generate new data periodically
    const alertInterval = setInterval(generateMockAlerts, 30000); // Every 30 seconds
    const activityInterval = setInterval(generateMockActivity, 45000); // Every 45 seconds

    return () => {
      clearInterval(alertInterval);
      clearInterval(activityInterval);
    };
  }, [addAlert, addActivity]);

  const getAlertIcon = (level) => {
    switch (level) {
      case 'high': return <AlertTriangle size={14} />;
      case 'medium': return <AlertTriangle size={14} />;
      case 'low': return <CheckCircle size={14} />;
      case 'info': return <Info size={14} />;
      default: return <Bell size={14} />;
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (dismissedAlerts.has(alert.id)) return false;
    if (filter === 'all') return true;
    return alert.level === filter;
  });

  const handleDismissAlert = (alertId) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
  };

  const handleClearAll = () => {
    setDismissedAlerts(new Set());
  };

  return (
    <AlertsFeedContainer>
      <Header>
        <Title>
          <Bell size={20} />
          Alerts & Activity Feed
        </Title>
        <FilterControls>
          <FilterButton 
            active={filter === 'all'} 
            onClick={() => setFilter('all')}
          >
            All
          </FilterButton>
          <FilterButton 
            active={filter === 'high'} 
            onClick={() => setFilter('high')}
          >
            High
          </FilterButton>
          <FilterButton 
            active={filter === 'medium'} 
            onClick={() => setFilter('medium')}
          >
            Medium
          </FilterButton>
          <FilterButton 
            active={filter === 'low'} 
            onClick={() => setFilter('low')}
          >
            Low
          </FilterButton>
          <ClearButton onClick={handleClearAll}>
            <X size={14} />
            Clear
          </ClearButton>
        </FilterControls>
      </Header>

      <FeedContainer>
        <FeedSection>
          <SectionTitle>
            <AlertTriangle size={16} />
            Alerts ({filteredAlerts.length})
          </SectionTitle>
          <ItemsList>
            {filteredAlerts.length === 0 ? (
              <EmptyState>No alerts to display</EmptyState>
            ) : (
              filteredAlerts.slice(0, 10).map(alert => (
                <AlertItem key={alert.id} level={alert.level}>
                  <AlertHeader>
                    <AlertType level={alert.level}>
                      {getAlertIcon(alert.level)}
                      {alert.type}
                    </AlertType>
                    <DismissButton onClick={() => handleDismissAlert(alert.id)}>
                      <X size={12} />
                    </DismissButton>
                  </AlertHeader>
                  <AlertMessage>{alert.message}</AlertMessage>
                  <AlertDetails>
                    <span>{alert.symbol}</span>
                    <AlertTime>
                      {formatDistanceToNow(alert.timestamp, { addSuffix: true })}
                    </AlertTime>
                  </AlertDetails>
                </AlertItem>
              ))
            )}
          </ItemsList>
        </FeedSection>

        <FeedSection>
          <SectionTitle>
            <Activity size={16} />
            Recent Activity ({activity.length})
          </SectionTitle>
          <ItemsList>
            {activity.length === 0 ? (
              <EmptyState>No activity to display</EmptyState>
            ) : (
              activity.slice(0, 10).map(item => (
                <ActivityItem key={item.id}>
                  <ActivityHeader>
                    <ActivityType>{item.type}</ActivityType>
                    <ActivityTime>
                      {formatDistanceToNow(item.timestamp, { addSuffix: true })}
                    </ActivityTime>
                  </ActivityHeader>
                  <ActivityMessage>{item.message}</ActivityMessage>
                </ActivityItem>
              ))
            )}
          </ItemsList>
        </FeedSection>
      </FeedContainer>
    </AlertsFeedContainer>
  );
};

export default AlertsFeed;
