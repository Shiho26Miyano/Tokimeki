#!/usr/bin/env python3
"""
Test script for model comparison functionality
"""
import asyncio
import os
import sys
from app.services.ai_service import AsyncAIService
from app.services.cache_service import AsyncCacheService
import httpx

async def test_model_comparison():
    """Test the model comparison functionality"""
    print("🧪 Testing Model Comparison...")
    
    # Set up API key for testing
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set. Please set it in your environment.")
        return False
    
    try:
        # Create HTTP client
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=50,
                max_connections=200,
                keepalive_expiry=60.0
            ),
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=60.0
            ),
            http2=True,
            follow_redirects=True
        )
        
        # Create cache service
        cache_service = AsyncCacheService()
        
        # Create AI service
        ai_service = AsyncAIService(http_client, cache_service)
        
        print("✅ Services created successfully")
        
        # Test single model call first
        print("\n🔍 Testing single model call...")
        try:
            single_result = await ai_service.call_api(
                messages=[{"role": "user", "content": "Hello, how are you?"}],
                model="mistral-small",
                temperature=0.7,
                max_tokens=50
            )
            print(f"✅ Single model call successful: {len(single_result.get('choices', []))} choices")
        except Exception as e:
            print(f"❌ Single model call failed: {e}")
            return False
        
        # Test model comparison
        print("\n🏁 Testing model comparison...")
        try:
            comparison_results = await ai_service.compare_models(
                prompt="What is 2+2?",
                models=["mistral-small", "deepseek-chat"],
                temperature=0.7,
                max_tokens=100
            )
            
            print(f"✅ Model comparison successful!")
            print(f"📊 Results: {len(comparison_results)} models")
            
            for i, result in enumerate(comparison_results):
                model = result.get("model", "unknown")
                success = result.get("success", False)
                response = result.get("response", "")
                error = result.get("error", "")
                
                print(f"\n📋 Model {i+1}: {model}")
                print(f"   Status: {'✅ Success' if success else '❌ Failed'}")
                if success:
                    print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
                else:
                    print(f"   Error: {error}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model comparison failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    finally:
        # Clean up
        if 'http_client' in locals():
            await http_client.aclose()

if __name__ == "__main__":
    success = asyncio.run(test_model_comparison())
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1) 