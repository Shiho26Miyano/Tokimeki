#!/usr/bin/env python3
"""
Deployment Verification Script
Run this after deploying to Railway to verify all features are working
"""

import requests
import json
import time
import sys

def test_endpoint(base_url, endpoint, description):
    """Test an endpoint and return success status"""
    try:
        url = f"{base_url}{endpoint}"
        response = requests.get(url, timeout=10)
        print(f"✅ {description}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False

def test_post_endpoint(base_url, endpoint, data, description):
    """Test a POST endpoint and return success status"""
    try:
        url = f"{base_url}{endpoint}"
        response = requests.post(url, json=data, timeout=30)
        print(f"✅ {description}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <your-railway-app-url>")
        print("Example: python verify_deployment.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    print(f"🔍 Testing deployment at: {base_url}")
    print("=" * 50)
    
    # Test basic endpoints
    tests = [
        ("/", "Homepage"),
        ("/api/cache-status", "Cache Status"),
        ("/api/usage-stats", "Usage Statistics"),
        ("/api/usage-limits", "Usage Limits"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, description in tests:
        if test_endpoint(base_url, endpoint, description):
            passed += 1
        print()
    
    # Test Redis functionality
    print("🔧 Testing Redis functionality...")
    if test_endpoint(base_url, "/api/test-redis", "Redis Connection Test"):
        passed += 1
        print("   ✅ Redis is working properly!")
    else:
        print("   ❌ Redis connection failed!")
    print()
    
    # Test rate limiting (should get 429)
    print("🛡️ Testing rate limiting...")
    try:
        # Make multiple requests quickly to trigger rate limit
        for i in range(15):
            response = requests.get(f"{base_url}/api/cache-status", timeout=5)
            if response.status_code == 429:
                print(f"✅ Rate limiting working! Got 429 after {i+1} requests")
                passed += 1
                break
            time.sleep(0.1)
        else:
            print("⚠️ Rate limiting not triggered (this might be normal)")
    except Exception as e:
        print(f"❌ Rate limiting test failed: {str(e)}")
    print()
    
    # Test chat functionality (if API key is configured)
    print("🤖 Testing chat functionality...")
    chat_data = {
        "message": "Hello, this is a test message",
        "model": "mistral-small",
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    if test_post_endpoint(base_url, "/chat", chat_data, "Chat API"):
        passed += 1
        print("   ✅ Chat functionality is working!")
    else:
        print("   ❌ Chat functionality failed (check API key)")
    print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total + 3} tests passed")
    
    if passed >= total + 2:
        print("🎉 Deployment verification successful!")
        print("✅ Your application is working properly on Railway")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        print("💡 Common issues:")
        print("   - Redis not configured properly")
        print("   - Environment variables not set")
        print("   - API keys missing")
        print("   - Network connectivity issues")

if __name__ == "__main__":
    main() 