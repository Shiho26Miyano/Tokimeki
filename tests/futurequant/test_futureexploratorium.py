"""
Tests for FutureExploratorium service
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.futurequant.futureexploratorium_service import FutureExploratoriumService
from app.services.futurequant.dashboard_service import FutureExploratoriumDashboardService
from app.services.futurequant.market_intelligence_service import FutureExploratoriumMarketIntelligenceService

class TestFutureExploratoriumService:
    """Test FutureExploratoriumService"""
    
    @pytest.fixture
    def service(self):
        return FutureExploratoriumService()
    
    @pytest.mark.asyncio
    async def test_get_platform_overview(self, service):
        """Test platform overview"""
        with patch('app.models.database.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock database queries
            mock_db.query.return_value.filter.return_value.count.return_value = 5
            
            result = await service.get_platform_overview()
            
            assert result["success"] is True
            assert "platform" in result
            assert "statistics" in result
            assert "recent_activity" in result
            assert "system_health" in result
            assert "market_overview" in result
    
    @pytest.mark.asyncio
    async def test_run_comprehensive_analysis(self, service):
        """Test comprehensive analysis"""
        symbols = ["ES=F", "NQ=F"]
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        analysis_types = ["data_ingestion", "feature_engineering"]
        
        with patch.object(service.data_service, 'ingest_data') as mock_data:
            with patch.object(service.feature_service, 'compute_features') as mock_features:
                mock_data.return_value = {"success": True, "results": {}}
                mock_features.return_value = {"success": True, "features_count": 10}
                
                result = await service.run_comprehensive_analysis(
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    analysis_types=analysis_types
                )
                
                assert result["success"] is True
                assert result["symbols"] == symbols
                assert result["date_range"]["start"] == start_date
                assert result["date_range"]["end"] == end_date
                assert "data_ingestion" in result["results"]
                assert "feature_engineering" in result["results"]
    
    @pytest.mark.asyncio
    async def test_get_strategy_performance_summary(self, service):
        """Test strategy performance summary"""
        with patch('app.models.database.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock backtest query
            mock_backtest = Mock()
            mock_backtest.strategy_id = 1
            mock_backtest.strategy.name = "Test Strategy"
            mock_backtest.metrics = {
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.05,
                "win_rate": 0.6
            }
            mock_backtest.start_date.isoformat.return_value = "2024-01-01"
            mock_backtest.end_date.isoformat.return_value = "2024-01-31"
            
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_backtest]
            
            result = await service.get_strategy_performance_summary()
            
            assert result["success"] is True
            assert "summary" in result
            assert result["summary"]["total_strategies"] == 1
            assert len(result["summary"]["performance_metrics"]) == 1

class TestDashboardService:
    """Test FutureExploratoriumDashboardService"""
    
    @pytest.fixture
    def dashboard_service(self):
        return FutureExploratoriumDashboardService()
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_dashboard_data(self, dashboard_service):
        """Test comprehensive dashboard data"""
        with patch.object(dashboard_service, '_get_market_overview') as mock_market:
            with patch.object(dashboard_service, '_get_strategy_performance') as mock_performance:
                with patch.object(dashboard_service, '_get_risk_metrics') as mock_risk:
                    with patch.object(dashboard_service, '_get_active_sessions') as mock_sessions:
                        with patch.object(dashboard_service, '_get_system_status') as mock_system:
                            with patch.object(dashboard_service, '_get_recent_activity') as mock_activity:
                                with patch.object(dashboard_service, '_get_alerts_and_notifications') as mock_alerts:
                                    mock_market.return_value = {"major_futures": {}}
                                    mock_performance.return_value = {}
                                    mock_risk.return_value = {}
                                    mock_sessions.return_value = {}
                                    mock_system.return_value = {}
                                    mock_activity.return_value = []
                                    mock_alerts.return_value = []
                                    
                                    result = await dashboard_service.get_comprehensive_dashboard_data()
                                    
                                    assert result["success"] is True
                                    assert "dashboard" in result
                                    assert "market_overview" in result["dashboard"]
                                    assert "strategy_performance" in result["dashboard"]
                                    assert "risk_metrics" in result["dashboard"]
                                    assert "active_sessions" in result["dashboard"]
                                    assert "system_status" in result["dashboard"]
                                    assert "recent_activity" in result["dashboard"]
                                    assert "alerts" in result["dashboard"]
    
    @pytest.mark.asyncio
    async def test_get_chart_data(self, dashboard_service):
        """Test chart data retrieval"""
        with patch('app.models.database.get_db') as mock_get_db:
            # Mock database session
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock symbol query
            mock_symbol = Mock()
            mock_symbol.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = mock_symbol
            
            # Mock bars query
            mock_bar = Mock()
            mock_bar.timestamp = "2024-01-01T00:00:00"
            mock_bar.open = 100.0
            mock_bar.high = 105.0
            mock_bar.low = 95.0
            mock_bar.close = 102.0
            mock_bar.volume = 1000
            
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_bar]
            
            result = await dashboard_service.get_chart_data("ES=F", "1d", 10)
            
            assert result["success"] is True
            assert result["symbol"] == "ES=F"
            assert result["timeframe"] == "1d"
            assert "data" in result
            assert len(result["data"]) == 1

class TestMarketIntelligenceService:
    """Test FutureExploratoriumMarketIntelligenceService"""
    
    @pytest.fixture
    def intelligence_service(self):
        return FutureExploratoriumMarketIntelligenceService()
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_market_intelligence(self, intelligence_service):
        """Test comprehensive market intelligence"""
        symbols = ["ES=F", "NQ=F"]
        analysis_depth = "standard"
        
        with patch.object(intelligence_service, '_get_market_sentiment') as mock_sentiment:
            with patch.object(intelligence_service, '_get_technical_analysis') as mock_technical:
                with patch.object(intelligence_service, '_get_fundamental_analysis') as mock_fundamental:
                    with patch.object(intelligence_service, '_get_risk_assessment') as mock_risk:
                        with patch.object(intelligence_service, '_get_market_regime_analysis') as mock_regime:
                            with patch.object(intelligence_service, '_get_correlation_analysis') as mock_correlation:
                                with patch.object(intelligence_service, '_get_volatility_analysis') as mock_volatility:
                                    with patch.object(intelligence_service, '_calculate_overall_score') as mock_score:
                                        with patch.object(intelligence_service, '_generate_intelligence_recommendations') as mock_recommendations:
                                            mock_sentiment.return_value = {"overall_market_sentiment": {"score": 0.5}}
                                            mock_technical.return_value = {"market_technical_score": 0.6}
                                            mock_fundamental.return_value = {}
                                            mock_risk.return_value = {"overall_risk_level": "medium"}
                                            mock_regime.return_value = {"dominant_regime": "trending"}
                                            mock_correlation.return_value = {}
                                            mock_volatility.return_value = {}
                                            mock_score.return_value = 0.7
                                            mock_recommendations.return_value = []
                                            
                                            result = await intelligence_service.get_comprehensive_market_intelligence(
                                                symbols=symbols,
                                                analysis_depth=analysis_depth
                                            )
                                            
                                            assert result["success"] is True
                                            assert result["symbols"] == symbols
                                            assert result["analysis_depth"] == analysis_depth
                                            assert "intelligence" in result
                                            assert "sentiment_analysis" in result["intelligence"]
                                            assert "technical_analysis" in result["intelligence"]
                                            assert "fundamental_analysis" in result["intelligence"]
                                            assert "risk_assessment" in result["intelligence"]
                                            assert "market_regime" in result["intelligence"]
                                            assert "correlation_analysis" in result["intelligence"]
                                            assert "volatility_analysis" in result["intelligence"]
                                            assert "overall_score" in result["intelligence"]
                                            assert "recommendations" in result["intelligence"]

if __name__ == "__main__":
    pytest.main([__file__])
