#!/usr/bin/env python3
"""
Database initialization script for Trading Simulation System
Creates all required simulation tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import engine, Base
from app.models.simulation_models import (
    PricesDaily, OptionsSnapshotDaily, FeaturesDaily, SignalsDaily,
    Trades, PortfolioDaily, StrategyMetadata, RegimeStates
)

def create_simulation_tables():
    """Create all simulation database tables"""
    print("Creating simulation database tables...")
    try:
        # Import all models to ensure they're registered with Base
        from app.models import simulation_models
        
        # Create all tables - this will create all tables registered with Base
        Base.metadata.create_all(bind=engine)
        print("✓ Simulation database tables created successfully")
        print("\nCreated tables:")
        print("  - prices_daily")
        print("  - options_snapshot_daily")
        print("  - features_daily")
        print("  - signals_daily")
        print("  - trades")
        print("  - portfolio_daily")
        print("  - strategy_metadata")
        print("  - regime_states")
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Main initialization function"""
    print("🚀 Initializing Trading Simulation Database...")
    print("=" * 50)
    
    try:
        create_simulation_tables()
        
        print("=" * 50)
        print("✅ Simulation database initialization completed successfully!")
        print("You can now run the daily pipeline to generate signals.")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

