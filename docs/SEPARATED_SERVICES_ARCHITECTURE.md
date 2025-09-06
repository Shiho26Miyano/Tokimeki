# Separated Services Architecture

## Overview

The FutureExploratorium has been successfully separated from the existing FutureQuant backend service, creating two independent but complementary services:

1. **FutureQuant** - Core futures trading backend service
2. **FutureExploratorium** - Advanced orchestration and analytics service

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Application                        │
│                     (app/main.py)                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ FutureQuant │ │FutureExplor-│ │   Other     │
│   Service   │ │   atorium   │ │  Services   │
│             │ │   Service   │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │
        │             │ (orchestrates)
        │             ▼
        │     ┌─────────────┐
        │     │ FutureQuant │
        │     │  Services   │
        │     │ (as deps)   │
        │     └─────────────┘
        │
        ▼
┌─────────────┐
│  Database   │
│  (Shared)   │
└─────────────┘
```

## Service Separation Details

### 1. FutureQuant Service (Existing)
**Location**: `app/services/futurequant/`
**API Endpoints**: `/api/v1/futurequant/*`
**Dashboard**: `/futurequant`

**Core Components**:
- Data Service
- Feature Service
- Model Service
- Signal Service
- Backtest Service
- Paper Trading Service
- Unified Service
- Market Data Service

**Responsibilities**:
- Core futures trading functionality
- Data ingestion and management
- Model training and deployment
- Signal generation
- Backtesting
- Paper trading simulation

### 2. FutureExploratorium Service (New - Independent)
**Location**: `app/services/futureexploratorium/`
**API Endpoints**: `/api/v1/futureexploratorium/*`
**Dashboard**: `/futureexploratorium`

**Core Components**:
- Core Service (orchestration)
- Dashboard Service
- Market Intelligence Service
- Analytics Service
- Strategy Service

**Responsibilities**:
- Service orchestration and coordination
- Advanced analytics and intelligence
- Real-time monitoring and dashboards
- Strategy optimization
- Cross-service insights

## Directory Structure

```
app/
├── services/
│   ├── futurequant/           # Original FutureQuant services
│   │   ├── data_service.py
│   │   ├── feature_service.py
│   │   ├── model_service.py
│   │   ├── signal_service.py
│   │   ├── backtest_service.py
│   │   ├── paper_broker_service.py
│   │   ├── unified_quant_service.py
│   │   └── market_data_service.py
│   └── futureexploratorium/   # New independent service
│       ├── __init__.py
│       ├── core_service.py
│       ├── dashboard_service.py
│       ├── market_intelligence_service.py
│       ├── analytics_service.py
│       └── strategy_service.py
├── api/
│   └── v1/
│       └── endpoints/
│           ├── futurequant/   # Original FutureQuant endpoints
│           │   ├── data.py
│           │   ├── features.py
│           │   ├── models.py
│           │   ├── signals.py
│           │   ├── backtests.py
│           │   └── paper_trading.py
│           └── futureexploratorium/  # New independent endpoints
│               ├── __init__.py
│               ├── core.py
│               ├── dashboard.py
│               ├── analytics.py
│               └── strategy.py
```

## API Endpoints

### FutureQuant Endpoints (Unchanged)
- `/api/v1/futurequant/data/*` - Data management
- `/api/v1/futurequant/features/*` - Feature engineering
- `/api/v1/futurequant/models/*` - Model management
- `/api/v1/futurequant/signals/*` - Signal generation
- `/api/v1/futurequant/backtests/*` - Backtesting
- `/api/v1/futurequant/paper-trading/*` - Paper trading

### FutureExploratorium Endpoints (New)
- `/api/v1/futureexploratorium/core/*` - Core orchestration
- `/api/v1/futureexploratorium/dashboard/*` - Dashboard and monitoring
- `/api/v1/futureexploratorium/analytics/*` - Advanced analytics
- `/api/v1/futureexploratorium/strategy/*` - Strategy management

## Service Dependencies

### FutureExploratorium → FutureQuant
FutureExploratorium uses FutureQuant services as external dependencies:

```python
# FutureExploratorium imports FutureQuant services
from app.services.futurequant.data_service import FutureQuantDataService
from app.services.futurequant.feature_service import FutureQuantFeatureService
from app.services.futurequant.model_service import FutureQuantModelService
# ... etc
```

### Database Sharing
Both services share the same database models and connection:
- `app/models/trading_models.py` - Shared database models
- `app/models/database.py` - Shared database connection

## Key Benefits of Separation

### 1. **Independence**
- FutureExploratorium can be developed, deployed, and scaled independently
- No modifications to existing FutureQuant functionality
- Clear separation of concerns

### 2. **Modularity**
- Each service has its own API endpoints
- Independent service configuration
- Separate error handling and logging

### 3. **Scalability**
- Services can be scaled independently
- Different deployment strategies possible
- Resource allocation per service

### 4. **Maintainability**
- Clear boundaries between services
- Independent testing and debugging
- Easier code organization

### 5. **Flexibility**
- FutureExploratorium can be extended without affecting FutureQuant
- New features can be added to either service independently
- Service-specific optimizations possible

## Service Communication

### Orchestration Pattern
FutureExploratorium orchestrates FutureQuant services:

```python
# FutureExploratorium orchestrates FutureQuant
class FutureExploratoriumCoreService:
    def __init__(self):
        # Import FutureQuant services as dependencies
        self.futurequant_data = FutureQuantDataService()
        self.futurequant_models = FutureQuantModelService()
        # ... etc
    
    async def run_comprehensive_analysis(self):
        # Orchestrate multiple FutureQuant services
        data_result = await self.futurequant_data.ingest_data(...)
        model_result = await self.futurequant_models.train_model(...)
        # ... etc
```

### Data Flow
1. **Request** → FutureExploratorium API
2. **Orchestration** → FutureExploratorium coordinates FutureQuant services
3. **Execution** → FutureQuant services perform core operations
4. **Aggregation** → FutureExploratorium aggregates and enhances results
5. **Response** → Enhanced response with orchestration context

## Configuration

### Service-Specific Configuration
Each service can have its own configuration:

```python
# FutureExploratorium configuration
self.platform_config = {
    "name": "FutureExploratorium",
    "version": "1.0.0",
    "service_type": "independent",
    "dependencies": ["FutureQuant"]
}

# FutureQuant configuration (unchanged)
# Existing configuration remains intact
```

### Environment Variables
- Shared: Database connection, MLflow, Redis
- FutureQuant specific: FutureQuant-specific settings
- FutureExploratorium specific: Orchestration settings

## Deployment Considerations

### Single Application Deployment
Both services run in the same FastAPI application:
- Shared resources (database, Redis, MLflow)
- Single deployment unit
- Shared middleware and configuration

### Future Microservices Deployment
The architecture supports future microservices deployment:
- Services can be extracted to separate applications
- API Gateway can route requests
- Service discovery and communication patterns

## Testing Strategy

### Independent Testing
- FutureQuant tests remain unchanged
- FutureExploratorium tests focus on orchestration
- Integration tests verify service communication

### Test Structure
```
tests/
├── futurequant/           # Existing FutureQuant tests
│   ├── test_data_service.py
│   ├── test_model_service.py
│   └── ...
└── futureexploratorium/   # New FutureExploratorium tests
    ├── test_core_service.py
    ├── test_dashboard_service.py
    └── ...
```

## Monitoring and Observability

### Service-Specific Metrics
- FutureQuant: Core trading metrics
- FutureExploratorium: Orchestration and analytics metrics
- Cross-service: Communication and dependency metrics

### Logging
- Service-specific log namespaces
- Clear identification of service context
- Correlation IDs for request tracing

## Future Enhancements

### Service Evolution
- FutureQuant: Core trading functionality improvements
- FutureExploratorium: Advanced analytics and AI features
- Independent evolution paths

### New Services
- Additional specialized services can be added
- Clear integration patterns established
- Consistent architecture principles

## Migration Path

### Phase 1: Separation (Completed)
- ✅ Create independent FutureExploratorium service
- ✅ Separate API endpoints
- ✅ Independent service configuration
- ✅ Orchestration layer

### Phase 2: Enhancement (Future)
- Advanced analytics features
- AI/ML integration
- Real-time streaming
- Advanced monitoring

### Phase 3: Microservices (Future)
- Service extraction
- Independent deployment
- Service mesh integration
- Advanced scaling

## Conclusion

The separation of FutureExploratorium from FutureQuant creates a clean, maintainable, and scalable architecture that:

1. **Preserves** all existing FutureQuant functionality
2. **Adds** advanced orchestration and analytics capabilities
3. **Enables** independent development and deployment
4. **Supports** future architectural evolution
5. **Maintains** clear separation of concerns

This architecture provides the foundation for a robust, scalable futures trading platform that can evolve independently while maintaining the reliability and functionality of the core FutureQuant service.
