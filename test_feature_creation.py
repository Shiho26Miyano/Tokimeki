#!/usr/bin/env python3
"""
Test script to isolate the Feature creation issue
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_feature_creation():
    """Test creating Feature objects to isolate the issue"""
    try:
        from app.models.trading_models import Feature
        from app.models.database import get_db
        from datetime import datetime
        
        print("Testing Feature creation...")
        
        # Test 1: Basic Feature creation
        feature1 = Feature(
            symbol_id=1,
            timestamp=datetime.now(),
            payload={"test": "value"}
        )
        print("✓ Basic Feature creation successful")
        
        # Test 2: Feature creation with more complex payload
        feature2 = Feature(
            symbol_id=1,
            timestamp=datetime.now(),
            payload={
                "feature_type": "technical_indicators",
                "sma_20": 100.0,
                "rsi": 50.0
            }
        )
        print("✓ Complex Feature creation successful")
        
        # Test 3: Try to create with invalid parameters (should fail)
        try:
            feature3 = Feature(
                symbol_id=1,
                timestamp=datetime.now(),
                feature_type="invalid",  # This should fail
                payload={"test": "value"}
            )
            print("✗ Invalid Feature creation should have failed")
        except TypeError as e:
            print(f"✓ Invalid Feature creation correctly failed: {e}")
        
        print("\nAll Feature creation tests passed!")
        
    except Exception as e:
        print(f"Error during Feature creation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_feature_creation())
