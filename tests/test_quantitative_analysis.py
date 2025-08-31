"""
Tests for Quantitative Analysis Services
Tests VectorBT, QF-Lib, and Lean integration
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.futurequant.vectorbt_service import FutureQuantVectorBTService
from app.services.futurequant.qflib_service import FutureQuantQFLibService
from app.services.futurequant.lean_service import FutureQuantLeanService
from app.services.futurequant.unified_quant_service import FutureQuantUnifiedService

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = Mock()
    session.query.return_value.filter.return_value.first.return_value = Mock(
        id=1, ticker="ES=F", venue="CME", asset_class="Equity"
    )
    session.query.return_value.filter.return_value.all.return_value = [
        Mock(id=1, ticker="ES=F"),
        Mock(id=2, ticker="CL=F")
    ]
    return session

@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    data = []
    
    for date in dates:
        data.append({
            'timestamp': date,
            'symbol': 'ES=F',
            'open': 4000 + np.random.normal(0, 50),
            'high': 4050 + np.random.normal(0, 50),
            'low': 3950 + np.random.normal(0, 50),
            'close': 4000 + np.random.normal(0, 50),
            'volume': int(1000000 + np.random.normal(0, 100000))
        })
        data.append({
            'timestamp': date,
            'symbol': 'CL=F',
            'open': 80 + np.random.normal(0, 2),
            'high': 82 + np.random.normal(0, 2),
            'low': 78 + np.random.normal(0, 2),
            'close': 80 + np.random.normal(0, 2),
            'volume': int(500000 + np.random.normal(0, 50000))
        })
    
    return pd.DataFrame(data)

class TestVectorBTService:
    """Test VectorBT service functionality"""
    
    @pytest.fixture
    def service(self):
        return FutureQuantVectorBTService()
    
    @pytest.mark.asyncio
    async def test_run_vectorbt_backtest(self, service, mock_db_session):
        """Test VectorBT backtest execution"""
        with patch('app.services.futurequant.vectorbt_service.get_db') as mock_get_db:
            mock_get_db.return_value = iter([mock_db_session])
            
            # Mock price data
            with patch.object(service, '_get_price_data') as mock_get_data:
                mock_get_data.return_value = pd.DataFrame({
                    'ES=F': {
                        'close': pd.Series([4000, 4010, 4020, 4030, 4040]),
                        'high': pd.Series([4010, 4020, 4030, 4040, 4050]),
                        'low': pd.Series([3990, 4000, 4010, 4020, 4030])
                    }
                })
                
                result = await service.run_vectorbt_backtest(
                    strategy_id=1,
                    start_date="2024-01-01",
                    end_date="2024-01-05",
                    symbols=["ES=F"],
                    strategy_type="momentum"
                )
                
                assert result["success"] is True
                assert "backtest_id" in result
                assert result["strategy_type"] == "momentum"
    
    @pytest.mark.asyncio
    async def test_momentum_strategy(self, service):
        """Test momentum strategy implementation"""
        # Create sample price data
        price_data = pd.DataFrame({
            'ES=F': {
                'close': pd.Series([4000, 4010, 4020, 4030, 4040, 4050, 4060, 4070, 4080, 4090])
            }
        })
        
        with patch('vectorbt.Portfolio.from_signals') as mock_portfolio:
            mock_portfolio.return_value.stats.return_value = {
                'Total Return [%]': 2.5,
                'Sharpe Ratio': 1.2,
                'Max Drawdown [%]': -1.5,
                'Win Rate [%]': 65.0,
                'Profit Factor': 1.8,
                'Total Trades': 10
            }
            mock_portfolio.return_value.value.return_value.iloc[-1] = 102500
            mock_portfolio.return_value.drawdown.return_value.iloc[-1] = pd.Series([-0.015])
            
            result = await service._run_momentum_strategy(price_data)
            
            assert result["strategy_type"] == "momentum"
            assert result["total_return"] == 2.5
            assert result["sharpe_ratio"] == 1.2

class TestQFLibService:
    """Test QF-Lib service functionality"""
    
    @pytest.fixture
    def service(self):
        return FutureQuantQFLibService()
    
    @pytest.mark.asyncio
    async def test_run_qflib_analysis(self, service, mock_db_session):
        """Test QF-Lib analysis execution"""
        with patch('app.services.futurequant.qflib_service.get_db') as mock_get_db:
            mock_get_db.return_value = iter([mock_db_session])
            
            # Mock price data
            with patch.object(service, '_get_price_data') as mock_get_data:
                mock_get_data.return_value = pd.DataFrame({
                    'ES=F': [4000, 4010, 4020, 4030, 4040],
                    'CL=F': [80, 81, 82, 83, 84]
                }, index=pd.date_range('2024-01-01', periods=5))
                
                result = await service.run_qflib_analysis(
                    strategy_id=1,
                    start_date="2024-01-01",
                    end_date="2024-01-05",
                    symbols=["ES=F", "CL=F"],
                    analysis_type="risk_metrics"
                )
                
                assert result["success"] is True
                assert result["analysis_type"] == "risk_metrics"
    
    @pytest.mark.asyncio
    async def test_risk_metrics_calculation(self, service):
        """Test risk metrics calculation"""
        # Create sample price data
        price_data = pd.DataFrame({
            'ES=F': [4000, 4010, 4020, 4030, 4040, 4050],
            'CL=F': [80, 81, 82, 83, 84, 85]
        }, index=pd.date_range('2024-01-01', periods=6))
        
        result = await service._calculate_risk_metrics(price_data)
        
        assert "returns_analysis" in result
        assert "risk_metrics" in result
        assert "correlation_matrix" in result
        assert "betas" in result

class TestLeanService:
    """Test Lean service functionality"""
    
    @pytest.fixture
    def service(self):
        return FutureQuantLeanService()
    
    @pytest.mark.asyncio
    async def test_run_lean_backtest(self, service, mock_db_session):
        """Test Lean backtest execution"""
        with patch('app.services.futurequant.lean_service.get_db') as mock_get_db:
            mock_get_db.return_value = iter([mock_db_session])
            
            # Mock price data
            with patch.object(service, '_get_price_data') as mock_get_data:
                mock_get_data.return_value = pd.DataFrame({
                    'ES=F': {
                        'close': pd.Series([4000, 4010, 4020, 4030, 4040]),
                        'high': pd.Series([4010, 4020, 4030, 4040, 4050]),
                        'low': pd.Series([3990, 4000, 4010, 4020, 4030])
                    }
                })
                
                result = await service.run_lean_backtest(
                    strategy_id=1,
                    start_date="2024-01-01",
                    end_date="2024-01-05",
                    symbols=["ES=F"],
                    strategy_code="momentum_strategy"
                )
                
                assert result["success"] is True
                assert "backtest_id" in result
                assert "strategy_code" in result
    
    def test_signal_generation(self, service):
        """Test trading signal generation"""
        # Create sample price data
        price_data = pd.DataFrame({
            'ES=F': [4000, 4010, 4020, 4030, 4040, 4050, 4060, 4070, 4080, 4090]
        })
        
        strategy_params = {
            "lookback_period": 5,
            "momentum_threshold": 0.02
        }
        
        signals = service._generate_signals(price_data, strategy_params)
        
        assert "ES=F" in signals
        assert isinstance(signals["ES=F"], int)

class TestUnifiedService:
    """Test unified quantitative analysis service"""
    
    @pytest.fixture
    def service(self):
        return FutureQuantUnifiedService()
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, service):
        """Test comprehensive analysis execution"""
        # Mock the individual services
        service.vectorbt_service.run_vectorbt_backtest = AsyncMock(return_value={
            "success": True, "results": {"total_return": 2.5}
        })
        service.qflib_service.run_qflib_analysis = AsyncMock(return_value={
            "success": True, "results": {"risk_metrics": {}}
        })
        
        result = await service.run_comprehensive_analysis(
            strategy_id=1,
            start_date="2024-01-01",
            end_date="2024-01-05",
            symbols=["ES=F"],
            analysis_types=["momentum", "risk_metrics"]
        )
        
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert "unified_report" in result
    
    @pytest.mark.asyncio
    async def test_benchmark_comparison(self, service):
        """Test benchmark comparison functionality"""
        # Mock the individual services
        service.vectorbt_service.run_vectorbt_backtest = AsyncMock(return_value={
            "success": True, "results": {"total_return": 2.5}
        })
        service.qflib_service.run_qflib_analysis = AsyncMock(return_value={
            "success": True, "results": {}
        })
        service.lean_service.run_lean_backtest = AsyncMock(return_value={
            "success": True, "results": {"total_return": 2.0}
        })
        
        result = await service.run_benchmark_comparison(
            strategy_id=1,
            start_date="2024-01-01",
            end_date="2024-01-05",
            symbols=["ES=F"],
            benchmark_symbol="SPY"
        )
        
        assert result["success"] is True
        assert "benchmark_comparison" in result
        assert result["benchmark_symbol"] == "SPY"

@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete integration workflow"""
    # This test would test the complete workflow from data ingestion to analysis
    # In a real implementation, this would use actual data and test the full pipeline
    
    # Mock database and services
    with patch('app.services.futurequant.vectorbt_service.get_db') as mock_get_db:
        mock_get_db.return_value = iter([Mock()])
        
        # Test VectorBT service
        vectorbt_service = FutureQuantVectorBTService()
        
        # Test QF-Lib service
        qflib_service = FutureQuantQFLibService()
        
        # Test Lean service
        lean_service = FutureQuantLeanService()
        
        # Test unified service
        unified_service = FutureQuantUnifiedService()
        
        # All services should be properly initialized
        assert vectorbt_service is not None
        assert qflib_service is not None
        assert lean_service is not None
        assert unified_service is not None

if __name__ == "__main__":
    pytest.main([__file__])
