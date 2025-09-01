#!/usr/bin/env python3
"""
Test script for FutureQuant Market Data Service
Tests Yahoo Finance integration and real-time price fetching
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_market_data():
    """Test the market data service"""
    try:
        print("🧪 Testing FutureQuant Market Data Service...")
        print("=" * 50)
        
        # Import the market data service
        from app.services.futurequant.market_data_service import market_data_service
        
        # Test symbols
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', '^GSPC', 'ES=F']
        
        print(f"📊 Testing price fetching for symbols: {', '.join(test_symbols)}")
        print("-" * 50)
        
        # Test individual price fetching
        for symbol in test_symbols:
            try:
                price = await market_data_service.get_current_price(symbol)
                if price:
                    print(f"✅ {symbol}: ${price:.2f}")
                else:
                    print(f"❌ {symbol}: Unable to fetch price")
            except Exception as e:
                print(f"❌ {symbol}: Error - {str(e)}")
        
        print("\n" + "-" * 50)
        print("📈 Testing batch price fetching...")
        
        # Test batch price fetching
        try:
            batch_prices = await market_data_service.get_batch_prices(test_symbols)
            print(f"✅ Batch fetch successful: {len(batch_prices)} prices retrieved")
            for symbol, price in batch_prices.items():
                if price:
                    print(f"   {symbol}: ${price:.2f}")
                else:
                    print(f"   {symbol}: No price available")
        except Exception as e:
            print(f"❌ Batch fetch error: {str(e)}")
        
        print("\n" + "-" * 50)
        print("📋 Testing symbol info...")
        
        # Test symbol info
        try:
            symbol_info = await market_data_service.get_symbol_info('AAPL')
            if symbol_info:
                print("✅ AAPL symbol info retrieved:")
                for key, value in symbol_info.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ Unable to fetch AAPL symbol info")
        except Exception as e:
            print(f"❌ Symbol info error: {str(e)}")
        
        print("\n" + "-" * 50)
        print("📊 Testing historical data...")
        
        # Test historical data
        try:
            hist_data = await market_data_service.get_historical_data('AAPL', period='1d', interval='1h')
            if hist_data is not None and not hist_data.empty:
                print(f"✅ AAPL historical data retrieved: {len(hist_data)} data points")
                print(f"   Latest close: ${hist_data['Close'].iloc[-1]:.2f}")
                print(f"   Data range: {hist_data.index[0]} to {hist_data.index[-1]}")
            else:
                print("❌ Unable to fetch AAPL historical data")
        except Exception as e:
            print(f"❌ Historical data error: {str(e)}")
        
        print("\n" + "-" * 50)
        print("🌐 Testing market status...")
        
        # Test market status
        try:
            market_status = await market_data_service.get_market_status()
            if market_status:
                print("✅ Market status retrieved:")
                print(f"   Market open: {market_status.get('market_open', 'Unknown')}")
                print(f"   Indices: {len(market_status.get('indices', {}))} available")
                for index, data in market_status.get('indices', {}).items():
                    print(f"   {index}: ${data.get('price', 'N/A'):.2f}")
            else:
                print("❌ Unable to fetch market status")
        except Exception as e:
            print(f"❌ Market status error: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Market data service test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_market_data())
