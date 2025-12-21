"""
Test strategy determinism - same inputs should produce same outputs
"""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock

from app.services.simulation import VolatilityRegimeStrategy
from app.models.simulation_models import FeaturesDaily, PricesDaily


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def sample_features():
    """Sample features for testing"""
    features = Mock(spec=FeaturesDaily)
    features.rv20 = 0.25
    features.rv60 = 0.30
    features.atr14 = 2.5
    features.rv20_pct = 75.0
    features.atr14_pct = 65.0
    features.iv_median_pct = 70.0
    features.iv_slope = 0.5
    features.cp_vol_ratio = 1.1
    features.cp_oi_ratio = 1.15
    return features


def test_strategy_determinism_same_inputs(mock_db, sample_features):
    """Test that same inputs produce same signal"""
    strategy = VolatilityRegimeStrategy()
    
    target_date = date.today()
    symbol = "AAPL"
    
    # Mock price data query
    mock_price = Mock(spec=PricesDaily)
    mock_price.close = 150.0
    mock_price.date = target_date
    
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        mock_price
    ]
    
    # Generate signal twice with same inputs
    signal1 = strategy.generate_signal(mock_db, symbol, target_date, sample_features)
    signal2 = strategy.generate_signal(mock_db, symbol, target_date, sample_features)
    
    # Should be identical
    assert signal1['signal'] == signal2['signal']
    assert signal1['target_position'] == signal2['target_position']
    assert signal1['reason_json']['regime']['on'] == signal2['reason_json']['regime']['on']


def test_regime_gate_deterministic(mock_db, sample_features):
    """Test that regime gate is deterministic"""
    strategy = VolatilityRegimeStrategy()
    
    # Test regime check multiple times
    regime1, rules1 = strategy._check_regime(sample_features)
    regime2, rules2 = strategy._check_regime(sample_features)
    
    assert regime1 == regime2
    assert rules1 == rules2


def test_position_sizing_deterministic(mock_db, sample_features):
    """Test that position sizing is deterministic"""
    strategy = VolatilityRegimeStrategy()
    
    sizing1 = strategy._compute_position_sizing(sample_features, "LONG")
    sizing2 = strategy._compute_position_sizing(sample_features, "LONG")
    
    assert sizing1 == sizing2
    assert sizing1['target_position'] == sizing2['target_position']


def test_regime_off_always_flat(mock_db):
    """Test that when regime is OFF, signal is always FLAT"""
    strategy = VolatilityRegimeStrategy()
    
    # Create features with regime OFF
    features = Mock(spec=FeaturesDaily)
    features.rv20_pct = 50.0  # Below threshold
    features.atr14_pct = 50.0  # Below threshold
    features.iv_median_pct = 50.0  # Below threshold
    features.iv_slope = -0.5  # Negative
    
    target_date = date.today()
    symbol = "AAPL"
    
    signal = strategy.generate_signal(mock_db, symbol, target_date, features)
    
    assert signal['signal'] == 'FLAT'
    assert signal['target_position'] == 0.0
    assert signal['reason_json']['regime']['on'] is False

