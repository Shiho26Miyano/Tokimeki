"""
Trading Simulation Services
"""
from .feature_service import SimulationFeatureService
from .strategy_service import StrategyPlugin, VolatilityRegimeStrategy
from .simulation_service import SimulationService
from .pipeline_service import DailyPipelineService

# Optional import for data ingestion (may fail if dependencies are missing)
try:
    from .data_ingestion_service import SimulationDataIngestionService
    __all__ = [
        "SimulationFeatureService",
        "StrategyPlugin",
        "VolatilityRegimeStrategy",
        "SimulationService",
        "DailyPipelineService",
        "SimulationDataIngestionService",
    ]
except ImportError:
    # Data ingestion service not available (missing dependencies)
    __all__ = [
        "SimulationFeatureService",
        "StrategyPlugin",
        "VolatilityRegimeStrategy",
        "SimulationService",
        "DailyPipelineService",
    ]

