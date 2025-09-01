#!/usr/bin/env python3
"""
Database initialization script for FutureQuant Trader
Creates all required tables and adds some sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import init_db, engine
from app.models.trading_models import Base, Symbol, Strategy, Model
from sqlalchemy.orm import Session
from app.models.database import SessionLocal

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

def add_sample_symbols():
    """Add some sample futures symbols"""
    print("Adding sample symbols...")
    db = SessionLocal()
    
    try:
        # Check if symbols already exist
        existing = db.query(Symbol).count()
        if existing > 0:
            print(f"✓ {existing} symbols already exist, skipping...")
            return
        
        # Add sample futures symbols
        symbols = [
            Symbol(
                ticker="ES=F",
                venue="CME",
                asset_class="Equity",
                point_value=50.0,
                tick_size=0.25,
                timezone="America/Chicago"
            ),
            Symbol(
                ticker="NQ=F",
                venue="CME",
                asset_class="Equity",
                point_value=20.0,
                tick_size=0.25,
                timezone="America/Chicago"
            ),
            Symbol(
                ticker="CL=F",
                venue="NYMEX",
                asset_class="Energy",
                point_value=1000.0,
                tick_size=0.01,
                timezone="America/New_York"
            ),
            Symbol(
                ticker="GC=F",
                venue="COMEX",
                asset_class="Metals",
                point_value=100.0,
                tick_size=0.1,
                timezone="America/New_York"
            ),
            Symbol(
                ticker="ZB=F",
                venue="CBOT",
                asset_class="Interest_Rate",
                point_value=1000.0,
                tick_size=0.03125,
                timezone="America/Chicago"
            )
        ]
        
        db.add_all(symbols)
        db.commit()
        print(f"✓ Added {len(symbols)} sample symbols")
        
    except Exception as e:
        print(f"✗ Error adding symbols: {e}")
        db.rollback()
    finally:
        db.close()

def add_sample_strategies():
    """Add some sample trading strategies"""
    print("Adding sample strategies...")
    db = SessionLocal()
    
    try:
        # Check if strategies already exist
        existing = db.query(Strategy).count()
        if existing > 0:
            print(f"✓ {existing} strategies already exist, skipping...")
            return
        
        # Add sample strategies
        strategies = [
            Strategy(
                name="Moving Average Crossover",
                description="Simple moving average crossover strategy",
                params={
                    "fast_period": 10,
                    "slow_period": 20,
                    "position_size": 0.1
                }
            ),
            Strategy(
                name="Mean Reversion",
                description="Bollinger Bands mean reversion strategy",
                params={
                    "period": 20,
                    "std_dev": 2.0,
                    "position_size": 0.1
                }
            ),
            Strategy(
                name="Momentum",
                description="RSI-based momentum strategy",
                params={
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                    "position_size": 0.1
                }
            )
        ]
        
        db.add_all(strategies)
        db.commit()
        print(f"✓ Added {len(strategies)} sample strategies")
        
    except Exception as e:
        print(f"✗ Error adding strategies: {e}")
        db.rollback()
    finally:
        db.close()

def add_sample_models():
    """Add some sample ML models"""
    print("Adding sample models...")
    db = SessionLocal()
    
    try:
        # Check if models already exist
        existing = db.query(Model).count()
        if existing > 0:
            print(f"✓ {existing} models already exist, skipping...")
            return
        
        # Add sample models
        models = [
            Model(
                name="LSTM_Price_Predictor",
                description="LSTM model for price prediction",
                artifact_uri="models/lstm_price_predictor_v1",
                params={
                    "layers": [64, 32],
                    "dropout": 0.2,
                    "sequence_length": 60
                },
                status="active"
            ),
            Model(
                name="RandomForest_Volatility",
                description="Random Forest for volatility prediction",
                artifact_uri="models/rf_volatility_v1",
                params={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5
                },
                status="active"
            )
        ]
        
        db.add_all(models)
        db.commit()
        print(f"✓ Added {len(models)} sample models")
        
    except Exception as e:
        print(f"✗ Error adding models: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing FutureQuant Trader Database...")
    print("=" * 50)
    
    try:
        # Create tables
        create_tables()
        
        # Add sample data
        add_sample_symbols()
        add_sample_strategies()
        add_sample_models()
        
        print("=" * 50)
        print("✅ Database initialization completed successfully!")
        print("You can now start training models and running backtests.")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
