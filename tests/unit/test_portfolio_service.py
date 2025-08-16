import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.portfolio_service import PortfolioService, PortfolioState

@pytest.fixture
def portfolio_service():
    return PortfolioService()

@pytest.fixture
def sample_state():
    """Sample portfolio state for testing"""
    return {
        "tickers": ["SPY", "QQQ"],
        "primary": "SPY",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "fee_bps": 1.0,
        "slip_bps": 2.0,
        "agent_log": []
    }

@pytest.fixture
def mock_price_data():
    """Mock price data for testing"""
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    np.random.seed(42)
    
    # Generate realistic price data
    returns = np.random.normal(0.0005, 0.02, len(dates))
    prices = 100 * (1 + returns).cumprod()
    
    return pd.DataFrame({
        'Close': prices
    }, index=dates)

class TestPortfolioService:
    
    def test_service_initialization(self, portfolio_service):
        """Test portfolio service initialization"""
        assert portfolio_service is not None
        assert isinstance(portfolio_service.state, dict)
    
    def test_log_function(self, portfolio_service):
        """Test logging functionality"""
        portfolio_service.log("Test message")
        assert len(portfolio_service.state["agent_log"]) == 1
        assert "Test message" in portfolio_service.state["agent_log"][0]
    
    def test_calculate_atr(self, portfolio_service):
        """Test ATR calculation"""
        prices = pd.Series([100, 101, 99, 102, 98, 103, 97, 104])
        atr = portfolio_service._calculate_atr(prices, period=3)
        
        assert len(atr) == len(prices)
        assert not atr.isna().all()  # Should have some non-NaN values
    
    def test_calculate_rsi(self, portfolio_service):
        """Test RSI calculation"""
        prices = pd.Series([100, 101, 99, 102, 98, 103, 97, 104])
        rsi = portfolio_service._calculate_rsi(prices, period=3)
        
        assert len(rsi) == len(prices)
        assert not rsi.isna().all()
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()
    
    def test_calculate_bollinger_bands(self, portfolio_service):
        """Test Bollinger Bands calculation"""
        prices = pd.Series([100, 101, 99, 102, 98, 103, 97, 104])
        upper, lower = portfolio_service._calculate_bollinger_bands(prices, period=3)
        
        assert len(upper) == len(prices)
        assert len(lower) == len(prices)
        # Upper band should generally be above lower band
        valid_data = ~(upper.isna() | lower.isna())
        if valid_data.any():
            assert (upper[valid_data] >= lower[valid_data]).all()
    
    def test_backtest_calculation(self, portfolio_service):
        """Test backtest calculation"""
        # Create sample data
        dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
        np.random.seed(42)
        
        # Generate price data
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = 100 * (1 + returns).cumprod()
        
        # Generate position data (simple buy and hold)
        position = pd.Series(1.0, index=dates)
        
        # Run backtest
        result = portfolio_service._run_backtest(prices, position, 1.0, 2.0)
        
        # Check required keys
        required_keys = [
            'returns', 'equity', 'drawdown', 'annual_return',
            'annual_volatility', 'sharpe_ratio', 'max_drawdown',
            'win_rate', 'total_return', 'calmar_ratio'
        ]
        
        for key in required_keys:
            assert key in result
        
        # Check data types and basic logic
        assert isinstance(result['equity'], pd.Series)
        assert isinstance(result['drawdown'], pd.Series)
        assert isinstance(result['sharpe_ratio'], (int, float, np.number))
        assert isinstance(result['max_drawdown'], (int, float, np.number))
        
        # Basic sanity checks
        assert result['max_drawdown'] <= 0  # Drawdown should be negative
        assert result['win_rate'] >= 0 and result['win_rate'] <= 1  # Win rate should be 0-1
    
    @pytest.mark.asyncio
    async def test_data_agent(self, portfolio_service, sample_state):
        """Test data agent functionality"""
        # Mock the yfinance download to avoid external API calls
        import yfinance as yf
        
        # Create mock data
        dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
        mock_data = pd.DataFrame({
            'Close': {
                'SPY': pd.Series(100 + np.random.randn(len(dates)).cumsum(), index=dates),
                'QQQ': pd.Series(150 + np.random.randn(len(dates)).cumsum(), index=dates)
            }
        })
        
        # Mock yfinance.download
        original_download = yf.download
        yf.download = lambda *args, **kwargs: mock_data
        
        try:
            result = await portfolio_service.data_agent(sample_state)
            
            # Check that data was loaded
            assert "prices" in result
            assert "features" in result
            assert len(result["agent_log"]) > 0
            
            # Check features structure
            for ticker in ["SPY", "QQQ"]:
                if ticker in result["features"]:
                    features = result["features"][ticker]
                    required_features = ["close", "returns", "ma_fast", "ma_slow", "volatility_20"]
                    for feature in required_features:
                        assert feature in features
        
        finally:
            # Restore original function
            yf.download = original_download
    
    @pytest.mark.asyncio
    async def test_research_agent(self, portfolio_service, sample_state):
        """Test research agent functionality"""
        # First run data agent to get features
        sample_state["prices"] = pd.DataFrame({
            'SPY': pd.Series(100 + np.random.randn(100).cumsum()),
            'QQQ': pd.Series(150 + np.random.randn(100).cumsum())
        })
        
        sample_state["features"] = {
            "SPY": pd.DataFrame({
                "close": pd.Series(100 + np.random.randn(100).cumsum()),
                "volatility_20": pd.Series(np.random.uniform(0.1, 0.3, 100))
            })
        }
        
        result = await portfolio_service.research_agent(sample_state)
        
        # Check that regime and thesis were generated
        assert "regime" in result
        assert "thesis" in result
        assert isinstance(result["regime"], str)
        assert isinstance(result["thesis"], list)
        assert len(result["thesis"]) > 0
    
    @pytest.mark.asyncio
    async def test_strategy_agent(self, portfolio_service, sample_state):
        """Test strategy agent functionality"""
        # Set up required state
        sample_state["regime"] = "Bull"
        sample_state["features"] = {
            "SPY": pd.DataFrame({
                "ma_fast": pd.Series(100 + np.random.randn(100).cumsum()),
                "ma_slow": pd.Series(100 + np.random.randn(100).cumsum()),
                "volatility_20": pd.Series(np.random.uniform(0.1, 0.3, 100))
            })
        }
        
        result = await portfolio_service.strategy_agent(sample_state)
        
        # Check that strategy parameters and position were generated
        assert "strategy_params" in result
        assert "position" in result
        assert isinstance(result["strategy_params"], dict)
        assert isinstance(result["position"], dict)
        
        # Check strategy parameters
        params = result["strategy_params"]
        assert "type" in params
        assert "fast_ma" in params
        assert "slow_ma" in params
        assert "position_size" in params
    
    @pytest.mark.asyncio
    async def test_risk_agent(self, portfolio_service, sample_state):
        """Test risk agent functionality"""
        # Set up required state
        sample_state["primary"] = "SPY"
        sample_state["features"] = {
            "SPY": pd.DataFrame({
                "close": pd.Series(100 + np.random.randn(100).cumsum()),
                "volatility_20": pd.Series(np.random.uniform(0.1, 0.3, 100))
            })
        }
        sample_state["position"] = {
            "SPY": pd.Series(np.random.choice([-0.5, 0, 1.0], 100))
        }
        
        result = await portfolio_service.risk_agent(sample_state)
        
        # Check that backtest results and risk notes were generated
        assert "backtest_results" in result
        assert "risk_notes" in result
        assert isinstance(result["backtest_results"], dict)
        assert isinstance(result["risk_notes"], list)
        assert len(result["risk_notes"]) > 0
    
    @pytest.mark.asyncio
    async def test_execution_agent(self, portfolio_service, sample_state):
        """Test execution agent functionality"""
        # Set up required state
        sample_state["primary"] = "SPY"
        sample_state["strategy_params"] = {"type": "Momentum", "fast_ma": 10, "slow_ma": 30}
        sample_state["position"] = {"SPY": pd.Series([1.0] * 100)}
        sample_state["features"] = {
            "SPY": pd.DataFrame({
                "close": pd.Series(100 + np.random.randn(100).cumsum()),
                "atr_20": pd.Series(np.random.uniform(1, 5, 100))
            })
        }
        sample_state["regime"] = "Bull"
        
        result = await portfolio_service.execution_agent(sample_state)
        
        # Check that trade plan was generated
        assert "trade_plan" in result
        assert isinstance(result["trade_plan"], list)
        assert len(result["trade_plan"]) > 0
        
        # Check trade plan content
        plan = result["trade_plan"]
        assert any("Asset:" in item for item in plan)
        assert any("Strategy:" in item for item in plan)
        assert any("Position Size:" in item for item in plan)

if __name__ == "__main__":
    pytest.main([__file__])
