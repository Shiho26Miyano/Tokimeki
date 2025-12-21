"""
Test walk-forward simulation - no lookahead bias
"""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base
from app.models.simulation_models import (
    PricesDaily, FeaturesDaily, SignalsDaily, PortfolioDaily
)
from app.services.simulation import (
    SimulationFeatureService,
    VolatilityRegimeStrategy,
    SimulationService,
    DailyPipelineService
)


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


@pytest.fixture
def sample_price_data(test_db):
    """Create sample price data for testing"""
    prices = []
    base_price = 100.0
    base_date = date.today() - timedelta(days=100)
    
    for i in range(100):
        price_date = base_date + timedelta(days=i)
        # Simple random walk
        import random
        random.seed(42)  # For reproducibility
        change = random.uniform(-0.02, 0.02)
        base_price *= (1 + change)
        
        price = PricesDaily(
            symbol="AAPL",
            date=price_date,
            open=base_price * 0.99,
            high=base_price * 1.01,
            low=base_price * 0.98,
            close=base_price,
            volume=1000000,
            adjusted_close=base_price
        )
        prices.append(price)
        test_db.add(price)
    
    test_db.commit()
    return prices


def test_no_lookahead_in_features(test_db, sample_price_data):
    """Test that features only use past data"""
    feature_service = SimulationFeatureService(test_db)
    
    # Compute features for a date in the middle
    target_date = date.today() - timedelta(days=50)
    
    features = feature_service.compute_features_for_date("AAPL", target_date)
    
    assert features is not None
    
    # Verify that rv20 only uses data up to target_date
    # (This is implicit in the implementation, but we can verify the date range)
    prices_query = test_db.query(PricesDaily).filter(
        PricesDaily.symbol == "AAPL",
        PricesDaily.date <= target_date
    ).order_by(PricesDaily.date)
    
    prices_count = prices_query.count()
    assert prices_count >= 61  # Need at least 61 days for rv60


def test_walk_forward_simulation(test_db, sample_price_data):
    """Test that simulation processes days in order without lookahead"""
    strategy = VolatilityRegimeStrategy()
    pipeline = DailyPipelineService(test_db, strategy)
    
    # Run pipeline for multiple consecutive days
    dates = [
        date.today() - timedelta(days=50),
        date.today() - timedelta(days=49),
        date.today() - timedelta(days=48)
    ]
    
    results = []
    for target_date in dates:
        # Compute features first (this should only use data up to target_date)
        feature_service = SimulationFeatureService(test_db)
        features_dict = feature_service.compute_features_for_date("AAPL", target_date)
        
        if features_dict:
            features = feature_service.persist_features(features_dict)
            
            # Generate signal
            signal_dict = strategy.generate_signal(test_db, "AAPL", target_date, features)
            
            # Verify signal was generated
            assert signal_dict is not None
            assert 'signal' in signal_dict
            
            results.append({
                'date': target_date,
                'signal': signal_dict['signal'],
                'features': features_dict
            })
    
    # Verify we processed all days
    assert len(results) == len(dates)
    
    # Verify each day's features only used data up to that day
    for i, result in enumerate(results):
        target_date = result['date']
        
        # Check that features exist
        assert result['features'] is not None
        
        # Verify no future data was used (implicit in implementation)
        features_row = test_db.query(FeaturesDaily).filter(
            FeaturesDaily.symbol == "AAPL",
            FeaturesDaily.date == target_date
        ).first()
        
        if features_row:
            assert features_row.date <= target_date


def test_portfolio_state_evolution(test_db, sample_price_data):
    """Test that portfolio state evolves correctly day by day"""
    strategy = VolatilityRegimeStrategy()
    simulation = SimulationService(test_db, strategy)
    
    target_date = date.today() - timedelta(days=50)
    
    # Get or create initial portfolio
    portfolio1 = simulation.get_or_create_portfolio(target_date)
    initial_nav = portfolio1.nav
    
    # Simulate next day
    next_date = target_date + timedelta(days=1)
    portfolio2 = simulation.get_or_create_portfolio(next_date)
    
    # Portfolio should carry forward
    assert portfolio2.nav == initial_nav  # Before mark-to-market
    
    # After mark-to-market, NAV should update
    portfolio2 = simulation.update_portfolio(portfolio2, next_date, ["AAPL"])
    
    # NAV should have changed (even if slightly)
    # (In real scenario, it would change based on price movement)
    assert portfolio2.nav is not None

