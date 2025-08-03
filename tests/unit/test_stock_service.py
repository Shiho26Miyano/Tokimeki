#!/usr/bin/env python3
"""
Test script for enhanced AI service with stock analysis
"""
import asyncio
import httpx
from app.services.cache_service import AsyncCacheService
from app.services.stock_service import AsyncStockService
from app.services.ai_service import AsyncAIService

async def test_stock_analysis():
    """Test the enhanced AI service with stock analysis"""
    
    # Initialize services
    cache_service = AsyncCacheService()
    stock_service = AsyncStockService(cache_service)
    
    # Create HTTP client
    async with httpx.AsyncClient() as http_client:
        ai_service = AsyncAIService(http_client, cache_service, stock_service)
        
        # Test questions
        test_questions = [
            "How would you use Monte Carlo simulation to estimate the probability that Tesla's stock price will exceed $1,000 in the next 12 months?",
            "What is the current performance of MSFT stock?",
            "Analyze TSLA stock performance and risk metrics",
            "How is GOOGL performing recently?",
            "What's the risk assessment for NVDA stock?"
        ]
        
        print("🤖 Enhanced AI Service with Stock Analysis Test")
        print("=" * 60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📊 Test {i}: {question}")
            print("-" * 40)
            
            try:
                result = await ai_service.chat_with_stock_analysis(
                    message=question,
                    model="mistral-small",
                    temperature=0.7,
                    max_tokens=1500
                )
                
                print(f"✅ Response: {result['response'][:200]}...")
                
                if "stock_analysis" in result:
                    analysis = result["stock_analysis"]
                    print(f"📈 Symbol Analyzed: {result.get('symbol_analyzed')}")
                    print(f"📊 Total Return: {analysis['metrics']['total_return_percent']}%")
                    print(f"📈 7-Day Return: {analysis['metrics']['week_return_percent']}%")
                    print(f"📉 Max Drawdown: {analysis['metrics']['max_drawdown_percent']}%")
                    print(f"⚡ Volatility: {analysis['metrics']['volatility']}%")
                    print(f"📋 Risk Level: {analysis['summary']['risk_assessment']}")
                    print(f"🏆 Performance: {analysis['summary']['performance_rating']}")
                else:
                    print("ℹ️ No stock analysis performed (no stock symbol detected)")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_stock_analysis()) 