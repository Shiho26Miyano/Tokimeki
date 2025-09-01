#!/usr/bin/env python3
"""
Test script for minimal deployment functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing package imports...")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✓ Uvicorn imported successfully")
    except ImportError as e:
        print(f"✗ Uvicorn import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"✗ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import numpy
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import pandas
        print("✓ Pandas imported successfully")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        import vectorbt
        print("✓ VectorBT imported successfully")
    except ImportError as e:
        print(f"✗ VectorBT import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from app.models.database import engine, SessionLocal
        from app.models.trading_models import Symbol
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM futurequant_symbols")
            count = result.scalar()
            print(f"✓ Database connection successful, found {count} symbols")
        
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_basic_functionality():
    """Test basic application functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from app.main import app
        print("✓ FastAPI app created successfully")
        
        # Test that we can access the app
        routes = [route.path for route in app.routes]
        print(f"✓ App has {len(routes)} routes")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Minimal Deployment Setup...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
        print("✓ Package imports test passed")
    else:
        print("✗ Package imports test failed")
    
    if test_database_connection():
        tests_passed += 1
        print("✓ Database connection test passed")
    else:
        print("✗ Database connection test failed")
    
    if test_basic_functionality():
        tests_passed += 1
        print("✓ Basic functionality test passed")
    else:
        print("✗ Basic functionality test failed")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Deployment setup is ready.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    main()
