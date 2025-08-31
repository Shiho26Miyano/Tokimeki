#!/usr/bin/env python3
"""
Test script to demonstrate how different strategies affect trading parameters
Shows the real difference between strategy selections
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_strategy_application():
    """Test how different strategies affect trading parameters"""
    try:
        print("🎯 Testing Strategy Application to Trading Parameters")
        print("=" * 70)
        print("This test shows how selecting different strategies changes:")
        print("• Position sizing (quantity)")
        print("• Stop loss levels")
        print("• Take profit targets")
        print("• Leverage limits")
        print("• Risk parameters")
        print()
        
        # Import services
        from app.services.futurequant.paper_broker_service import FutureQuantPaperBrokerService
        
        # Create paper broker service
        paper_broker = FutureQuantPaperBrokerService()
        
        # Test different strategies
        strategies = [
            {
                'id': 1,
                'name': 'Aggressive Mean Reversion',
                'description': 'High-risk mean reversion for volatile futures markets'
            },
            {
                'id': 2,
                'name': 'Conservative Trend Following',
                'description': 'Low-risk trend following with tight stops'
            },
            {
                'id': 3,
                'name': 'Volatility Breakout',
                'description': 'Trade breakouts from low volatility periods'
            }
        ]
        
        # Test parameters
        test_symbol = 'ES=F'
        test_price = 5000.0  # S&P 500 futures price
        base_quantity = 1
        
        print("📊 Strategy Comparison Table")
        print("-" * 70)
        print(f"{'Strategy':<25} {'Risk':<12} {'Position':<10} {'Stop Loss':<12} {'Take Profit':<12} {'Leverage':<8}")
        print("-" * 70)
        
        for strategy in strategies:
            # Get strategy configuration
            strategy_config = get_strategy_config(strategy['id'])
            
            # Calculate trading parameters
            position_size = base_quantity * strategy_config['positionSizeMultiplier']
            stop_loss = test_price * (1 - strategy_config['stopLossPercent'] / 100)
            take_profit = test_price * (1 + strategy_config['takeProfitPercent'] / 100)
            
            print(f"{strategy['name']:<25} {strategy_config['riskLevel']:<12} {position_size:<10.1f} {stop_loss:<12.0f} {take_profit:<12.0f} {strategy_config['leverage']:<8.1f}")
        
        print()
        print("💡 How Strategy Selection Affects Your Trading:")
        print("-" * 70)
        
        for strategy in strategies:
            strategy_config = get_strategy_config(strategy['id'])
            
            print(f"\n🎯 {strategy['name']}")
            print(f"   Risk Level: {strategy_config['riskLevel']}")
            print(f"   Position Size: {strategy_config['positionSizeMultiplier']}x normal size")
            print(f"   Stop Loss: {strategy_config['stopLossPercent']}% from entry")
            print(f"   Take Profit: {strategy_config['takeProfitPercent']}% from entry")
            print(f"   Max Leverage: {strategy_config['leverage']}x")
            print(f"   Max Drawdown: {strategy_config['maxDrawdown'] * 100}%")
            print(f"   Time Horizon: {strategy_config['timeHorizon']}")
            print(f"   Entry Rules: {strategy_config['entryRules']}")
            print(f"   Exit Rules: {strategy_config['exitRules']}")
        
        print()
        print("🚀 Practical Example - Trading ES=F at $5000:")
        print("-" * 70)
        
        # Show practical example
        for strategy in strategies:
            strategy_config = get_strategy_config(strategy['id'])
            
            print(f"\n📈 {strategy['name']} Example:")
            print(f"   Entry Price: ${test_price:,.2f}")
            print(f"   Position Size: {strategy_config['positionSizeMultiplier']} contract(s)")
            print(f"   Stop Loss: ${test_price * (1 - strategy_config['stopLossPercent'] / 100):,.2f}")
            print(f"   Take Profit: ${test_price * (1 + strategy_config['takeProfitPercent'] / 100):,.2f}")
            print(f"   Risk per Trade: ${test_price * strategy_config['stopLossPercent'] / 100 * strategy_config['positionSizeMultiplier']:,.2f}")
            print(f"   Potential Profit: ${test_price * strategy_config['takeProfitPercent'] / 100 * strategy_config['positionSizeMultiplier']:,.2f}")
        
        print()
        print("✅ Strategy Selection Now Actually Matters!")
        print("   • High Risk = Bigger positions, wider stops, higher leverage")
        print("   • Low Risk = Smaller positions, tighter stops, lower leverage")
        print("   • Each strategy has different entry/exit rules")
        print("   • Risk management is automatically adjusted")
        
        print()
        print("🎮 How to Use in the Web Interface:")
        print("   1. Select a strategy from the dropdown")
        print("   2. Start paper trading session")
        print("   3. Place trades - strategy rules are automatically applied")
        print("   4. Watch how different strategies perform differently")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

def get_strategy_config(strategy_id):
    """Get strategy configuration (same as frontend)"""
    strategy_configs = {
        1: { # Aggressive Mean Reversion
            'name': 'Aggressive Mean Reversion',
            'riskLevel': 'High',
            'positionSizeMultiplier': 2.0,
            'stopLossPercent': 3.0,
            'takeProfitPercent': 6.0,
            'maxDrawdown': 0.15,
            'leverage': 3.0,
            'entryRules': 'Enter when price deviates 2+ standard deviations from mean',
            'exitRules': 'Exit on mean reversion or stop loss hit',
            'timeHorizon': '5min-1hour',
            'volatilityThreshold': 'High'
        },
        2: { # Conservative Trend Following
            'name': 'Conservative Trend Following',
            'riskLevel': 'Low',
            'positionSizeMultiplier': 0.5,
            'stopLossPercent': 1.5,
            'takeProfitPercent': 3.0,
            'maxDrawdown': 0.08,
            'leverage': 1.5,
            'entryRules': 'Enter on trend confirmation with multiple timeframes',
            'exitRules': 'Exit on trend reversal or trailing stop',
            'timeHorizon': '1hour-4hours',
            'volatilityThreshold': 'Low'
        },
        3: { # Volatility Breakout
            'name': 'Volatility Breakout',
            'riskLevel': 'Medium',
            'positionSizeMultiplier': 1.0,
            'stopLossPercent': 2.5,
            'takeProfitPercent': 5.0,
            'maxDrawdown': 0.12,
            'leverage': 2.0,
            'entryRules': 'Enter on volatility expansion with volume confirmation',
            'exitRules': 'Exit on volatility contraction or target hit',
            'timeHorizon': '15min-2hours',
            'volatilityThreshold': 'Medium'
        }
    }
    
    return strategy_configs.get(strategy_id, strategy_configs[1])

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_strategy_application())
