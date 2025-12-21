"""
Test database write/read operations
"""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base
from app.models.simulation_models import (
    PricesDaily, FeaturesDaily, SignalsDaily, Trades,
    PortfolioDaily, StrategyMetadata, RegimeStates
)
from app.services.simulation import SimulationFeatureService


@pytest.fixture
def test_db():
    """Create in-memory test database"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_prices_daily_write_read(test_db):
    """Test writing and reading prices_daily"""
    price = PricesDaily(
        symbol="AAPL",
        date=date.today(),
        open=150.0,
        high=152.0,
        low=149.0,
        close=151.0,
        volume=1000000,
        adjusted_close=151.0
    )
    
    test_db.add(price)
    test_db.commit()
    
    # Read back
    retrieved = test_db.query(PricesDaily).filter(
        PricesDaily.symbol == "AAPL",
        PricesDaily.date == date.today()
    ).first()
    
    assert retrieved is not None
    assert retrieved.symbol == "AAPL"
    assert retrieved.close == 151.0
    assert retrieved.volume == 1000000


def test_features_daily_write_read(test_db):
    """Test writing and reading features_daily"""
    feature = FeaturesDaily(
        symbol="AAPL",
        date=date.today(),
        rv20=0.25,
        rv60=0.30,
        atr14=2.5,
        rv20_pct=75.0,
        atr14_pct=65.0,
        iv_median_pct=70.0
    )
    
    test_db.add(feature)
    test_db.commit()
    
    # Read back
    retrieved = test_db.query(FeaturesDaily).filter(
        FeaturesDaily.symbol == "AAPL",
        FeaturesDaily.date == date.today()
    ).first()
    
    assert retrieved is not None
    assert retrieved.rv20 == 0.25
    assert retrieved.rv20_pct == 75.0


def test_signals_daily_write_read(test_db):
    """Test writing and reading signals_daily"""
    signal = SignalsDaily(
        strategy_id="vol_regime_v1",
        symbol="AAPL",
        date=date.today(),
        signal="LONG",
        target_position=0.30,
        reason_json={"test": "data"}
    )
    
    test_db.add(signal)
    test_db.commit()
    
    # Read back
    retrieved = test_db.query(SignalsDaily).filter(
        SignalsDaily.strategy_id == "vol_regime_v1",
        SignalsDaily.symbol == "AAPL",
        SignalsDaily.date == date.today()
    ).first()
    
    assert retrieved is not None
    assert retrieved.signal == "LONG"
    assert retrieved.target_position == 0.30
    assert retrieved.reason_json == {"test": "data"}


def test_portfolio_daily_write_read(test_db):
    """Test writing and reading portfolio_daily"""
    portfolio = PortfolioDaily(
        strategy_id="vol_regime_v1",
        date=date.today(),
        nav=100000.0,
        cash=70000.0,
        positions_json={"AAPL": 200.0},
        daily_pnl=100.0,
        cumulative_pnl=1000.0,
        drawdown=0.02,
        max_drawdown=0.05
    )
    
    test_db.add(portfolio)
    test_db.commit()
    
    # Read back
    retrieved = test_db.query(PortfolioDaily).filter(
        PortfolioDaily.strategy_id == "vol_regime_v1",
        PortfolioDaily.date == date.today()
    ).first()
    
    assert retrieved is not None
    assert retrieved.nav == 100000.0
    assert retrieved.cash == 70000.0
    assert retrieved.positions_json == {"AAPL": 200.0}
    assert retrieved.daily_pnl == 100.0


def test_strategy_metadata_write_read(test_db):
    """Test writing and reading strategy_metadata"""
    metadata = StrategyMetadata(
        strategy_id="vol_regime_v1",
        name="Volatility Regime Strategy",
        version="1.0.0",
        params_json={"base_exposure": 0.30},
        description="Test strategy",
        is_active=True
    )
    
    test_db.add(metadata)
    test_db.commit()
    
    # Read back
    retrieved = test_db.query(StrategyMetadata).filter(
        StrategyMetadata.strategy_id == "vol_regime_v1"
    ).first()
    
    assert retrieved is not None
    assert retrieved.name == "Volatility Regime Strategy"
    assert retrieved.version == "1.0.0"
    assert retrieved.params_json == {"base_exposure": 0.30}


def test_regime_states_write_read(test_db):
    """Test writing and reading regime_states"""
    regime = RegimeStates(
        strategy_id="vol_regime_v1",
        symbol="AAPL",
        date=date.today(),
        regime_on=True,
        reasons_json={"test": "data"}
    )
    
    test_db.add(regime)
    test_db.commit()
    
    # Read back
    retrieved = test_db.query(RegimeStates).filter(
        RegimeStates.strategy_id == "vol_regime_v1",
        RegimeStates.symbol == "AAPL",
        RegimeStates.date == date.today()
    ).first()
    
    assert retrieved is not None
    assert retrieved.regime_on is True
    assert retrieved.reasons_json == {"test": "data"}


def test_feature_service_persist(test_db):
    """Test that feature service can persist features"""
    # Create some price data first
    price = PricesDaily(
        symbol="AAPL",
        date=date.today(),
        open=150.0,
        high=152.0,
        low=149.0,
        close=151.0,
        volume=1000000,
        adjusted_close=151.0
    )
    test_db.add(price)
    test_db.commit()
    
    # Use feature service to persist
    feature_service = SimulationFeatureService(test_db)
    
    features_dict = {
        'symbol': 'AAPL',
        'date': date.today(),
        'rv20': 0.25,
        'rv60': 0.30,
        'atr14': 2.5,
        'rv20_pct': 75.0
    }
    
    feature = feature_service.persist_features(features_dict)
    
    assert feature is not None
    assert feature.symbol == "AAPL"
    assert feature.rv20 == 0.25
    
    # Verify it's in database
    retrieved = test_db.query(FeaturesDaily).filter(
        FeaturesDaily.symbol == "AAPL",
        FeaturesDaily.date == date.today()
    ).first()
    
    assert retrieved is not None
    assert retrieved.rv20 == 0.25

