#!/usr/bin/env python3
"""
Enhanced Stock AI Service Test
Tests the comprehensive stock analysis with yfinance data
"""
import asyncio
import httpx
from app.services.cache_service import AsyncCacheService
from app.services.stock_service import AsyncStockService
from app.services.ai_service import AsyncAIService

async def test_enhanced_stock_analysis():
    """Test the enhanced AI service with comprehensive stock analysis"""
    
    print("🚀 Enhanced Stock AI Service Test")
    print("=" * 60)
    
    # Initialize services
    cache_service = AsyncCacheService()
    stock_service = AsyncStockService(cache_service)
    
    # Create HTTP client
    async with httpx.AsyncClient() as http_client:
        ai_service = AsyncAIService(http_client, cache_service, stock_service)
        
        # Test comprehensive stock analysis questions
        test_questions = [
            "Analyze AAPL stock performance and provide investment recommendation",
            "What is the current valuation and financial health of MSFT?",
            "Show me a comprehensive analysis of TSLA including risk assessment",
            "Analyze NVDA stock with focus on growth prospects and valuation",
            "What are the key metrics and investment outlook for AMZN?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📊 Test {i}: {question}")
            print("-" * 50)
            
            try:
                # Test comprehensive stock analysis
                result = await ai_service.chat_with_stock_analysis(
                    message=question,
                    model="mistral-small",
                    temperature=0.7,
                    max_tokens=1500
                )
                
                if "stock_analysis" in result:
                    analysis = result["stock_analysis"]
                    symbol = result.get("symbol_analyzed", "Unknown")
                    
                    print(f"✅ Symbol Analyzed: {symbol}")
                    print(f"📈 Company: {analysis.get('company_name', 'N/A')}")
                    print(f"💰 Current Price: ${analysis.get('current_price', 0):.2f}")
                    print(f"📊 Market Cap: ${analysis.get('market_cap', 0):,.0f}")
                    print(f"📈 Total Return: {analysis.get('total_return', 0):.2f}%")
                    print(f"⚡ Volatility: {analysis.get('volatility', 0):.2f}%")
                    print(f"📊 P/E Ratio: {analysis.get('pe_ratio', 0):.2f}")
                    print(f"💵 Dividend Yield: {analysis.get('dividend_yield', 0):.2f}%")
                    print(f"📋 Sector: {analysis.get('sector', 'N/A')}")
                    print(f"🏭 Industry: {analysis.get('industry', 'N/A')}")
                    
                    print(f"\n🤖 AI Response:")
                    print(result.get("response", "No response")[:500] + "...")
                    
                else:
                    print("❌ No stock analysis performed")
                    print(f"🤖 Response: {result.get('response', 'No response')[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "="*60)

async def test_comprehensive_stock_data():
    """Test the comprehensive stock data fetching"""
    
    print("\n🔍 Testing Comprehensive Stock Data Fetching")
    print("=" * 60)
    
    cache_service = AsyncCacheService()
    stock_service = AsyncStockService(cache_service)
    
    test_symbols = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]
    
    for symbol in test_symbols:
        print(f"\n📊 Testing comprehensive data for {symbol}")
        print("-" * 40)
        
        try:
            comprehensive_data = await stock_service.get_comprehensive_stock_data(symbol)
            
            if comprehensive_data:
                company_info = comprehensive_data.get('company_info', {})
                market_data = comprehensive_data.get('market_data', {})
                historical_data = comprehensive_data.get('historical_data', {})
                financial_data = comprehensive_data.get('financial_data', {})
                analyst_data = comprehensive_data.get('analyst_data', {})
                
                print(f"✅ Company: {company_info.get('name', 'N/A')}")
                print(f"📋 Sector: {company_info.get('sector', 'N/A')}")
                print(f"🏭 Industry: {company_info.get('industry', 'N/A')}")
                print(f"👥 Employees: {company_info.get('employees', 'N/A'):,}")
                print(f"💰 Current Price: ${market_data.get('current_price', 0):.2f}")
                print(f"📊 Market Cap: ${market_data.get('market_cap', 0):,.0f}")
                print(f"📈 P/E Ratio: {market_data.get('pe_ratio', 0):.2f}")
                print(f"💵 Dividend Yield: {market_data.get('dividend_yield', 0):.2f}%")
                print(f"📊 Beta: {market_data.get('beta', 0):.2f}")
                print(f"📈 Total Return: {historical_data.get('percent_change', 0):.2f}%")
                print(f"⚡ Volatility: {historical_data.get('volatility', 0):.2f}%")
                
                # Test financial data extraction
                revenue_growth = ai_service._extract_revenue_growth(financial_data)
                profit_margins = ai_service._extract_profit_margins(financial_data)
                debt_levels = ai_service._extract_debt_levels(financial_data)
                recommendations = ai_service._extract_recommendations(analyst_data)
                price_targets = ai_service._extract_price_targets(analyst_data)
                
                print(f"📈 Revenue Growth: {revenue_growth}")
                print(f"💰 Profit Margins: {profit_margins}")
                print(f"💳 Debt Levels: {debt_levels}")
                print(f"📊 Analyst Recommendations: {recommendations}")
                print(f"🎯 Price Targets: {price_targets}")
                
            else:
                print(f"❌ No comprehensive data available for {symbol}")
                
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")

if __name__ == "__main__":
    # Set API key
    import os
    os.environ['OPENROUTER_API_KEY'] = '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'
    
    # Run tests
    asyncio.run(test_enhanced_stock_analysis())
    asyncio.run(test_comprehensive_stock_data()) 