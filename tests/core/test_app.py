#!/usr/bin/env python3
"""
Simple test script for Tokimeki FastAPI application
Run this locally to test before deploying to Railway
"""

import requests
import time
import sys

def test_app():
    """Test the basic endpoints of the FastAPI app"""
    base_url = "http://localhost:8080"  # Updated to port 8080
    
    print("🧪 Testing Tokimeki FastAPI Application...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        print("1. Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test root endpoint
    try:
        print("2. Testing / endpoint...")
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("   ✅ Root endpoint passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Root endpoint error: {e}")
        return False
    
    # Test API status endpoint
    try:
        print("3. Testing /api/status endpoint...")
        response = requests.get(f"{base_url}/api/status", timeout=10)
        if response.status_code == 200:
            print("   ✅ API status endpoint passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ API status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API status endpoint error: {e}")
        return False
    
    # Test favicon
    try:
        print("4. Testing /favicon.ico endpoint...")
        response = requests.get(f"{base_url}/favicon.ico", timeout=10)
        if response.status_code == 200:
            print("   ✅ Favicon endpoint passed")
        else:
            print(f"   ❌ Favicon endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Favicon endpoint error: {e}")
        return False
    
    print("=" * 50)
    print("🎉 All tests passed! Application is working correctly.")
    return True

def main():
    """Main function"""
    print("🚀 Tokimeki FastAPI Test Suite")
    print("Make sure your application is running on localhost:8080")
    print("Run: python3 start_local.py")
    print()
    
    # Wait a moment for user to start the app
    input("Press Enter when your app is running, or Ctrl+C to cancel...")
    
    success = test_app()
    if success:
        print("\n✅ Application is ready for Railway deployment!")
        sys.exit(0)
    else:
        print("\n❌ Application has issues that need to be fixed before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
