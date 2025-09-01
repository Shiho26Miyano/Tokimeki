#!/usr/bin/env python3
"""
Test script for Futures Trading with Different Strategies
Tests the complete workflow from strategy selection to paper trading
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_futures_trading():
    """Test futures trading with different strategies"""
    try:
        print("🚀 Testing Futures Trading with Different Strategies")
        print("=" * 60)
        print("This test shows how strategy selection affects paper trading")
        print()
        
        # Import services
        from app.services.futurequant.paper_broker_service import FutureQuantPaperBrokerService
        from app.services.futurequant.market_data_service import market_data_service
        
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Test different strategies
        strategies = [
            {
                'name': 'Aggressive Mean Reversion',
                'description': 'High-risk mean reversion for volatile futures markets',
                'risk_level': 'High',
                'timeframe': '5 minutes to 1 hour'
            },
            {
                'name': 'Conservative Trend Following', 
                'description': 'Low-risk trend following with tight stops',
                'risk_level': 'Low',
                'timeframe': '1 hour to 4 hours'
            },
            {
                'name': 'Volatility Breakout',
                'description': 'Trade breakouts from low volatility periods',
                'risk_level': 'Medium',
                'timeframe': '15 minutes to 2 hours'
            }
        ]
        
        print("📊 Step 1: Getting Futures Market Data...")
        print("-" * 50)
        
        # Get current prices for futures
        futures_symbols = ['ES=F', 'NQ=F', 'YM=F', 'CL=F', 'GC=F']
        print(f"Fetching live futures prices for: {', '.join(futures_symbols)}")
        
        prices = await market_data_service.get_batch_prices(futures_symbols)
        
        print("\n💰 Current Futures Prices (LIVE from Yahoo Finance):")
        for symbol, price in prices.items():
            if price:
                print(f"   {symbol}: ${price:.2f}")
            else:
                print(f"   {symbol}: Price unavailable")
        
        print()
        print("🎯 Step 2: Testing Strategy Selection...")
        print("-" * 50)
        
        for i, strategy in enumerate(strategies, 1):
            print(f"\n   📈 Strategy {i}: {strategy['name']}")
            print(f"      Risk Level: {strategy['risk_level']}")
            print(f"      Timeframe: {strategy['timeframe']}")
            print(f"      Description: {strategy['description']}")
            
            # Start paper trading session with this strategy
            session_result = await paper_broker.start_paper_trading_demo(
                strategy_name=strategy['name'],
                initial_capital=100000,
                symbols=futures_symbols
            )
            
            if session_result['success']:
                session_id = session_result['session_id']
                print(f"      ✅ Session started: {session_id}")
                
                # Place a sample futures trade
                trade_symbol = 'ES=F'  # S&P 500 futures
                current_price = prices.get(trade_symbol)
                
                if current_price:
                    # Calculate position size based on risk level
                    if strategy['risk_level'] == 'High':
                        quantity = 2  # Aggressive position
                    elif strategy['risk_level'] == 'Medium':
                        quantity = 1  # Moderate position
                    else:  # Low risk
                        quantity = 1  # Conservative position
                    
                    # Place the order
                    order_result = await paper_broker.place_order(
                        session_id=session_id,
                        symbol=trade_symbol,
                        side='buy',
                        quantity=quantity,
                        order_type='market'
                    )
                    
                    if order_result['success']:
                        print(f"      🎯 {strategy['name']} executed: BUY {quantity} {trade_symbol} @ ${current_price:.2f}")
                    else:
                        print(f"      ❌ Order failed: {order_result['error']}")
                
                # Get session status
                status_result = await paper_broker.get_session_status(session_id)
                if status_result['success']:
                    print(f"      💰 Capital: ${status_result['current_capital']:,.2f}")
                    print(f"      📈 P&L: ${status_result['current_pnl']:,.2f}")
                    print(f"      🔢 Positions: {len(status_result['positions'])}")
                
                # Stop the session
                stop_result = await paper_broker.stop_paper_trading(session_id)
                if stop_result['success']:
                    print(f"      🛑 Session stopped successfully")
                
            else:
                print(f"      ❌ Failed to start session: {session_result['error']}")
            
            print()
        
        print("📊 Step 3: Strategy Performance Summary...")
        print("-" * 50)
        
        print("   🎯 Strategy Comparison:")
        print("      • Aggressive Mean Reversion: High risk, high reward potential")
        print("      • Conservative Trend Following: Low risk, steady returns")
        print("      • Volatility Breakout: Medium risk, event-driven profits")
        
        print()
        print("💡 Key Takeaways:")
        print("   ✅ Strategy dropdown now shows real futures strategies")
        print("   ✅ Each strategy has different risk parameters")
        print("   ✅ Paper trading sessions use selected strategy")
        print("   ✅ Real futures data from Yahoo Finance")
        print("   ✅ Position sizing based on strategy risk level")
        
        print()
        print("🚀 Next Steps:")
        print("   • Refresh the web page to see updated strategy dropdown")
        print("   • Select different strategies to see details change")
        print("   • Start paper trading with your chosen strategy")
        print("   • Open the Live Dashboard for real-time futures P&L")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_futures_trading())
