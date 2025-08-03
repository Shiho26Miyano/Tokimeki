#!/usr/bin/env python3
"""
Deployment verification script for FastAPI version
Tests that all components can be imported and initialized correctly
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        # Test FastAPI app import
        from main import app
        print("✅ FastAPI app imported successfully")
        
        # Test core modules
        from app.core.config import settings
        print("✅ Config imported successfully")
        
        from app.core.dependencies import get_http_client, get_ai_service
        print("✅ Dependencies imported successfully")
        
        # Test services
        from app.services.ai_service import AsyncAIService
        print("✅ AI service imported successfully")
        
        from app.services.stock_service import AsyncStockService
        print("✅ Stock service imported successfully")
        
        from app.services.cache_service import AsyncCacheService
        print("✅ Cache service imported successfully")
        
        from app.services.usage_service import AsyncUsageService
        print("✅ Usage service imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_configuration():
    """Test app configuration"""
    print("\n🔍 Testing app configuration...")
    
    try:
        from main import app
        from app.core.config import settings
        
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        print(f"✅ Debug mode: {settings.debug}")
        print(f"✅ API key configured: {bool(settings.openrouter_api_key)}")
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"✅ Available routes: {len(routes)}")
        
        # Check critical routes exist
        critical_routes = ['/', '/health', '/chat', '/stocks/history']
        for route in critical_routes:
            if route in routes:
                print(f"✅ Route {route} exists")
            else:
                print(f"⚠️  Route {route} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment...")
    
    try:
        # Check Python version
        print(f"✅ Python version: {sys.version}")
        
        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        print(f"✅ Virtual environment: {in_venv}")
        
        # Check working directory
        print(f"✅ Working directory: {os.getcwd()}")
        
        # Check if main.py exists
        if os.path.exists('main.py'):
            print("✅ main.py exists")
        else:
            print("❌ main.py not found")
        
        # Check if Procfile exists
        if os.path.exists('Procfile'):
            print("✅ Procfile exists")
        else:
            print("❌ Procfile not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 FastAPI Deployment Verification")
    print("=" * 40)
    
    # Run all tests
    tests = [
        test_imports,
        test_app_configuration,
        test_environment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment should work.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 