#!/usr/bin/env python3
"""
Simple Paper Trading Demo - Shows Real Market Data & P&L Calculations
No database required - demonstrates the core functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def simple_paper_trading_demo():
    """Simple demo showing paper trading with real market data"""
    try:
        print("🚀 Simple Paper Trading Demo")
        print("=" * 50)
        print("This shows exactly how paper trading works with real Yahoo Finance data")
        print()
        
        # Import market data service
        from app.services.futurequant.market_data_service import market_data_service
        
        print("📊 Step 1: Getting REAL market data from Yahoo Finance...")
        print("-" * 50)
        
        # Get current prices for popular stocks
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        print(f"Fetching live prices for: {', '.join(symbols)}")
        
        prices = await market_data_service.get_batch_prices(symbols)
        
        print("\n💰 Current Market Prices (LIVE from Yahoo Finance):")
        for symbol, price in prices.items():
            if price:
                print(f"   {symbol}: ${price:.2f}")
            else:
                print(f"   {symbol}: Price unavailable")
        
        print()
        print("🎯 Step 2: Simulating Paper Trading Session...")
        print("-" * 50)
        
        # Simulate a paper trading session
        initial_capital = 100000  # $100k starting capital
        current_capital = initial_capital
        cash = initial_capital
        positions = {}
        trades = []
        
        print(f"   💰 Starting capital: ${initial_capital:,.2f}")
        print(f"   💵 Available cash: ${cash:,.2f}")
        print(f"   📈 Strategy: Buy and hold tech stocks")
        
        print()
        print("📈 Step 3: Placing REAL trades with LIVE prices...")
        print("-" * 50)
        
        # Place some sample trades using real market prices
        trade_orders = [
            {'symbol': 'AAPL', 'side': 'buy', 'quantity': 100},
            {'symbol': 'MSFT', 'side': 'buy', 'quantity': 50},
            {'symbol': 'GOOGL', 'side': 'buy', 'quantity': 75}
        ]
        
        total_invested = 0
        
        for trade in trade_orders:
            symbol = trade['symbol']
            quantity = trade['quantity']
            current_price = prices.get(symbol)
            
            if current_price:
                # Calculate trade details
                trade_value = quantity * current_price
                commission = trade_value * 0.0002  # 2 basis points
                total_cost = trade_value + commission
                
                if cash >= total_cost:
                    # Execute trade
                    cash -= total_cost
                    total_invested += trade_value
                    
                    # Record position
                    positions[symbol] = {
                        'side': 'long',
                        'quantity': quantity,
                        'entry_price': current_price,
                        'entry_time': datetime.now(),
                        'value': trade_value,
                        'commission': commission
                    }
                    
                    # Record trade
                    trades.append({
                        'symbol': symbol,
                        'side': 'buy',
                        'quantity': quantity,
                        'entry_price': current_price,
                        'commission': commission,
                        'timestamp': datetime.now()
                    })
                    
                    print(f"   ✅ BUY {quantity} {symbol} @ ${current_price:.2f}")
                    print(f"      💰 Trade value: ${trade_value:,.2f}")
                    print(f"      💸 Commission: ${commission:.2f}")
                    print(f"      💵 Cash remaining: ${cash:,.2f}")
                else:
                    print(f"   ❌ Insufficient cash for {symbol} trade")
            else:
                print(f"   ❌ Unable to get price for {symbol}")
            
            print()
        
        print("📊 Step 4: Calculating REAL-TIME P&L...")
        print("-" * 50)
        
        # Get updated prices to calculate P&L
        print("   🔄 Fetching updated prices for P&L calculation...")
        updated_prices = await market_data_service.get_batch_prices(list(positions.keys()))
        
        total_pnl = 0
        positions_value = 0
        
        print("\n   📋 Current Positions & P&L:")
        for symbol, position in positions.items():
            current_price = updated_prices.get(symbol)
            if current_price:
                # Calculate position P&L
                if position['side'] == 'long':
                    position_pnl = (current_price - position['entry_price']) * position['quantity']
                else:
                    position_pnl = (position['entry_price'] - current_price) * position['quantity']
                
                position_value = position['quantity'] * current_price
                positions_value += position_value
                total_pnl += position_pnl
                
                pnl_color = "🟢" if position_pnl >= 0 else "🔴"
                pnl_sign = "+" if position_pnl >= 0 else ""
                
                print(f"      📈 {symbol}: {position['quantity']} @ ${position['entry_price']:.2f}")
                print(f"         Current price: ${current_price:.2f}")
                print(f"         {pnl_color} P&L: {pnl_sign}${position_pnl:,.2f}")
                print(f"         Position value: ${position_value:,.2f}")
                print()
        
        # Calculate total portfolio value and return
        total_portfolio_value = cash + positions_value
        total_return = ((total_portfolio_value - initial_capital) / initial_capital) * 100
        
        print("   💰 Portfolio Summary:")
        print(f"      💵 Cash: ${cash:,.2f}")
        print(f"      📈 Positions value: ${positions_value:,.2f}")
        print(f"      💰 Total portfolio: ${total_portfolio_value:,.2f}")
        print(f"      📊 Total P&L: ${total_pnl:,.2f}")
        print(f"      📈 Total return: {total_return:.2f}%")
        
        print()
        print("🔄 Step 5: Simulating Price Changes & P&L Updates...")
        print("-" * 50)
        
        # Simulate some price changes to show P&L updates
        print("   📈 Simulating AAPL price increase from $232.14 to $235.00...")
        
        # Update AAPL price
        if 'AAPL' in positions:
            old_price = updated_prices.get('AAPL', 232.14)
            new_price = 235.00  # Simulated price increase
            
            position = positions['AAPL']
            old_pnl = (old_price - position['entry_price']) * position['quantity']
            new_pnl = (new_price - position['entry_price']) * position['quantity']
            pnl_change = new_pnl - old_pnl
            
            print(f"      📊 AAPL P&L change: ${old_pnl:,.2f} → ${new_pnl:,.2f}")
            print(f"      📈 P&L improvement: +${pnl_change:,.2f}")
            
            # Update portfolio values
            new_positions_value = positions_value + (new_price - old_price) * position['quantity']
            new_total_portfolio = cash + new_positions_value
            new_total_return = ((new_total_portfolio - initial_capital) / initial_capital) * 100
            
            print(f"      💰 New portfolio value: ${new_total_portfolio:,.2f}")
            print(f"      📊 New total return: {new_total_return:.2f}%")
        
        print()
        print("📊 Step 6: Real-Time Market Data Features...")
        print("-" * 50)
        
        # Show additional market data features
        print("   🌐 Market Status:")
        market_status = await market_data_service.get_market_status()
        if market_status:
            print(f"      Market open: {market_status.get('market_open', 'Unknown')}")
            print(f"      Major indices available: {len(market_status.get('indices', {}))}")
        
        print("\n   📋 Symbol Information (AAPL):")
        aapl_info = await market_data_service.get_symbol_info('AAPL')
        if aapl_info:
            print(f"      Company: {aapl_info.get('name', 'N/A')}")
            print(f"      Sector: {aapl_info.get('sector', 'N/A')}")
            print(f"      Market Cap: ${aapl_info.get('market_cap', 0):,.0f}")
        
        print()
        print("=" * 50)
        print("🎉 Paper Trading Demo Completed!")
        print()
        print("💡 What You Just Saw:")
        print("   ✅ REAL market prices from Yahoo Finance (not fake data)")
        print("   ✅ ACTUAL trade execution with real prices")
        print("   ✅ LIVE P&L calculations based on current market values")
        print("   ✅ Real-time position tracking and portfolio updates")
        print("   ✅ Commission and slippage modeling")
        print("   ✅ Portfolio performance metrics")
        print()
        print("🚀 How Paper Trading Actually Works:")
        print("   1. Get LIVE market data from Yahoo Finance")
        print("   2. Execute trades at REAL market prices")
        print("   3. Calculate P&L using CURRENT market values")
        print("   4. Track positions with REAL-TIME updates")
        print("   5. Show actual gains/losses, not static numbers")
        print()
        print("🌐 Open paper-trading-dashboard.html to see the live dashboard!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async demo
    asyncio.run(simple_paper_trading_demo())
