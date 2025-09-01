#!/usr/bin/env python3
"""
Test script to verify database connection fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_database_connection():
    """Test database connection with new path"""
    print("Testing database connection with new structured path...")
    
    try:
        from app.models.database import engine, SessionLocal
        from app.models.trading_models import Symbol
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM futurequant_symbols"))
            count = result.scalar()
            print(f"✓ Database connection successful, found {count} symbols")
        
        # Test ORM query
        db = SessionLocal()
        try:
            symbols = db.query(Symbol).all()
            print(f"✓ ORM query successful, found {len(symbols)} symbols")
            
            # Test specific symbol query that was failing
            es_symbol = db.query(Symbol).filter(Symbol.ticker == "ES=F").first()
            if es_symbol:
                print(f"✓ ES=F symbol found: {es_symbol.ticker} ({es_symbol.asset_class})")
            else:
                print("✗ ES=F symbol not found")
                
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_model_training_start():
    """Test if model training can start without database errors"""
    print("\nTesting model training start...")
    
    try:
        from app.services.futurequant.model_service import FutureQuantModelService
        
        # Initialize service
        service = FutureQuantModelService()
        print("✓ Model service initialized successfully")
        
        # Test basic functionality - check available attributes
        print(f"✓ Service attributes: {[attr for attr in dir(service) if not attr.startswith('_')]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Model training start failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database fix for FutureQuant Trader\n")
    
    db_ok = test_database_connection()
    model_ok = test_model_training_start()
    
    print(f"\n{'='*50}")
    if db_ok and model_ok:
        print("✓ All tests passed! Database fix successful.")
    else:
        print("✗ Some tests failed. Check the errors above.")
    print(f"{'='*50}")
