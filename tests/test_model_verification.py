#!/usr/bin/env python3
"""
Test script to verify that all listed models work with OpenRouter API
"""

import asyncio
import httpx
import json
import os
from typing import List, Dict, Any

# Models to test
MODELS_TO_TEST = {
    "mistral-small": "mistralai/mistral-small-3.2-24b-instruct:free",
    "deepseek-r1": "deepseek/deepseek-r1-0528:free",
    "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct:free",
    "llama-3.1-405b": "meta-llama/llama-3.1-405b-instruct:free",
    "phi-3-mini": "microsoft/phi-3-mini-128k-instruct:free"
}

async def test_model(model_id: str, model_name: str, api_key: str) -> Dict[str, Any]:
    """Test a single model with a simple prompt"""
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-repo",
        "X-Title": "Model Test"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": "Hello! Please respond with 'Model test successful' to verify this model is working."}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "model": model_name,
                    "status": "SUCCESS",
                    "response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "usage": result.get("usage", {}),
                    "model_used": result.get("model", "")
                }
            else:
                return {
                    "model": model_name,
                    "status": "FAILED",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response": None
                }
                
    except Exception as e:
        return {
            "model": model_name,
            "status": "ERROR",
            "error": str(e),
            "response": None
        }

async def test_all_models():
    """Test all models and report results"""
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set!")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-api-key-here'")
        return
    
    print("🔍 Testing all listed models with OpenRouter API...")
    print("=" * 60)
    
    results = []
    
    for model_name, model_id in MODELS_TO_TEST.items():
        print(f"\n🧪 Testing {model_name} ({model_id})...")
        result = await test_model(model_id, model_name, api_key)
        results.append(result)
        
        if result["status"] == "SUCCESS":
            print(f"✅ {model_name}: SUCCESS")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Usage: {result['usage']}")
        else:
            print(f"❌ {model_name}: FAILED")
            print(f"   Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] != "SUCCESS"]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n✅ WORKING MODELS:")
        for result in successful:
            print(f"   • {result['model']}")
    
    if failed:
        print("\n❌ FAILED MODELS:")
        for result in failed:
            print(f"   • {result['model']}: {result['error']}")
    
    # Save detailed results to file
    with open("model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved to: model_test_results.json")

if __name__ == "__main__":
    asyncio.run(test_all_models()) 