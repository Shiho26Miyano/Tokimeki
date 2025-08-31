#!/usr/bin/env python3
"""
Demo script for FutureQuant Paper Trading with Real Market Data
Shows how to start a session, place trades, and see real-time P&L
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def demo_paper_trading():
    """Demonstrate paper trading with real market data"""
    try:
        print("🚀 FutureQuant Paper Trading Demo")
        print("=" * 50)
        print("This demo shows how paper trading works with real Yahoo Finance data")
        print()
        
        # Import services
        from app.services.futurequant.paper_broker_service import FutureQuantPaperBrokerService
        from app.services.futurequant.market_data_service import market_data_service
        
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        print("📊 Step 1: Getting current market data...")
        print("-" * 30)
        
        # Get current prices for demo symbols
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        prices = await market_data_service.get_batch_prices(symbols)
        
        for symbol, price in prices.items():
            if price:
                print(f"   {symbol}: ${price:.2f}")
            else:
                print(f"   {symbol}: Price unavailable")
        
        print()
        print("🎯 Step 2: Starting paper trading session...")
        print("-" * 30)
        
        # Start a paper trading session
        session_result = await paper_broker.start_paper_trading(
            user_id=1,  # Demo user
            strategy_id=1,  # Demo strategy
            initial_capital=100000,  # $100k starting capital
            symbols=symbols
        )
        
        if session_result['success']:
            session_id = session_result['session_id']
            print(f"   ✅ Session started: {session_id}")
            print(f"   💰 Initial capital: ${session_result['session_info']['initial_capital']:,.2f}")
            print(f"   📈 Strategy: {session_result['session_info']['strategy_name']}")
        else:
            print(f"   ❌ Failed to start session: {session_result['error']}")
            return
        
        print()
        print("📈 Step 3: Placing sample trades...")
        print("-" * 30)
        
        # Place some sample trades
        trades = [
            {'symbol': 'AAPL', 'side': 'buy', 'quantity': 100},
            {'symbol': 'MSFT', 'side': 'buy', 'quantity': 50},
            {'symbol': 'GOOGL', 'side': 'buy', 'quantity': 75}
        ]
        
        for trade in trades:
            try:
                # Get current price for the symbol
                current_price = await market_data_service.get_current_price(trade['symbol'])
                if current_price:
                    # Place the order
                    order_result = await paper_broker.place_order(
                        session_id=session_id,
                        symbol=trade['symbol'],
                        side=trade['side'],
                        quantity=trade['quantity'],
                        order_type='market'
                    )
                    
                    if order_result['success']:
                        print(f"   ✅ {trade['side'].upper()} {trade['quantity']} {trade['symbol']} @ ${current_price:.2f}")
                    else:
                        print(f"   ❌ Failed to place {trade['symbol']} order: {order_result['error']}")
                else:
                    print(f"   ❌ Unable to get price for {trade['symbol']}")
                    
            except Exception as e:
                print(f"   ❌ Error placing {trade['symbol']} order: {str(e)}")
        
        print()
        print("📊 Step 4: Getting real-time session status...")
        print("-" * 30)
        
        # Get current session status
        status_result = await paper_broker.get_session_status(session_id)
        
        if status_result['success']:
            status = status_result
            print(f"   💰 Current capital: ${status['current_capital']:,.2f}")
            print(f"   📈 Current P&L: ${status['current_pnl']:,.2f}")
            print(f"   📊 Current return: {status['current_return']:.2f}%")
            print(f"   💵 Cash: ${status['cash']:,.2f}")
            print(f"   📈 Positions value: ${status['positions_value']:,.2f}")
            print(f"   🔢 Total trades: {status['total_trades']}")
            
            # Show positions
            if status['positions']:
                print("\n   📋 Current Positions:")
                for symbol, position in status['positions'].items():
                    side_emoji = "📈" if position['side'] == 'long' else "📉"
                    pnl_emoji = "🟢" if position.get('position_pnl', 0) >= 0 else "🔴"
                    print(f"      {side_emoji} {symbol} ({position['side']}): {position['quantity']} @ ${position['entry_price']:.2f}")
                    if 'position_pnl' in position:
                        print(f"         {pnl_emoji} P&L: ${position['position_pnl']:,.2f}")
        else:
            print(f"   ❌ Failed to get status: {status_result['error']}")
        
        print()
        print("📊 Step 5: Getting real-time dashboard data...")
        print("-" * 30)
        
        # Get dashboard data
        dashboard_result = await paper_broker.get_real_time_dashboard_data(session_id)
        
        if dashboard_result['success']:
            dashboard = dashboard_result['dashboard_data']
            print(f"   💰 Account balance: ${dashboard['account_balance']:,.2f}")
            print(f"   📈 Current P&L: ${dashboard['current_pnl']:,.2f}")
            print(f"   📊 Daily P&L: ${dashboard['daily_pnl']:,.2f}")
            print(f"   🔢 Open positions: {dashboard['open_positions']}")
            print(f"   🎯 Win rate: {dashboard['win_rate']:.1f}%")
            print(f"   📈 Total trades: {dashboard['total_trades']}")
            
            # Show recent trades
            if dashboard['recent_trades']:
                print("\n   📋 Recent Trades:")
                for trade in dashboard['recent_trades'][-3:]:  # Last 3 trades
                    pnl_emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
                    print(f"      {pnl_emoji} {trade['symbol']} ({trade['side']}): ${trade['pnl']:,.2f}")
        else:
            print(f"   ❌ Failed to get dashboard data: {dashboard_result['error']}")
        
        print()
        print("🔄 Step 6: Simulating price changes...")
        print("-" * 30)
        
        # Simulate some price changes to see P&L updates
        print("   📈 Simulating AAPL price increase...")
        
        # Get updated status after some time
        await asyncio.sleep(2)
        
        updated_status = await paper_broker.get_session_status(session_id)
        if updated_status['success']:
            print(f"   💰 Updated capital: ${updated_status['current_capital']:,.2f}")
            print(f"   📈 Updated P&L: ${updated_status['current_pnl']:,.2f}")
            print(f"   📊 Updated return: {updated_status['current_return']:.2f}%")
        
        print()
        print("🛑 Step 7: Stopping paper trading session...")
        print("-" * 30)
        
        # Stop the session
        stop_result = await paper_broker.stop_paper_trading(session_id)
        
        if stop_result['success']:
            print("   ✅ Session stopped successfully")
            if 'summary' in stop_result:
                summary = stop_result['summary']
                print(f"   📊 Final capital: ${summary['final_capital']:,.2f}")
                print(f"   📈 Total return: {summary['total_return']:.2f}%")
                print(f"   🔢 Total trades: {summary['total_trades']}")
                print(f"   🎯 Win rate: {summary['win_rate']:.1f}%")
        else:
            print(f"   ❌ Failed to stop session: {stop_result['error']}")
        
        print()
        print("=" * 50)
        print("🎉 Paper Trading Demo Completed!")
        print()
        print("💡 Key Takeaways:")
        print("   • Real-time market data from Yahoo Finance")
        print("   • Live P&L calculations based on current prices")
        print("   • Position tracking with real market values")
        print("   • Risk management and order execution")
        print("   • Comprehensive trading session management")
        print()
        print("🚀 Next Steps:")
        print("   • Open paper-trading-dashboard.html for live dashboard")
        print("   • Start your own paper trading session")
        print("   • Test different strategies with virtual money")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async demo
    asyncio.run(demo_paper_trading())
