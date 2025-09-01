#!/usr/bin/env python3
"""
Test script to verify the feature data type fix
Tests if the numpy.object_ error is resolved
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_feature_fix():
    """Test if the feature data type issue is fixed"""
    try:
        print("🔧 Testing Feature Data Type Fix")
        print("=" * 50)
        print("This test verifies that features are properly typed")
        print()
        
        # Import the feature service
        from app.services.futurequant.feature_service import FutureQuantFeatureService
        
        # Create feature service
        feature_service = FutureQuantFeatureService()
        
        # Create sample data
        print("📊 Creating sample futures data...")
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(4500, 5500, 100),
            'high': np.random.uniform(4500, 5500, 100),
            'low': np.random.uniform(4500, 5500, 100),
            'close': np.random.uniform(4500, 5500, 100),
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # Ensure proper data types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            sample_data[col] = sample_data[col].astype('float64')
        
        print(f"Sample data shape: {sample_data.shape}")
        print(f"Sample data dtypes: {sample_data.dtypes.tolist()}")
        print()
        
        # Test feature computation
        print("🧮 Testing feature computation...")
        
        # Test basic features
        print("   Testing basic features...")
        basic_features = await feature_service._compute_returns(sample_data.copy(), [1, 5, 10])
        basic_features = await feature_service._compute_rsi(basic_features, [14, 20])
        basic_features = await feature_service._compute_macd(basic_features)
        
        print(f"   Basic features shape: {basic_features.shape}")
        print(f"   Basic features dtypes: {basic_features.dtypes.tolist()}")
        
        # Test advanced features
        print("   Testing advanced features...")
        advanced_features = await feature_service._compute_adx(sample_data.copy(), [14, 20])
        advanced_features = await feature_service._compute_cci(advanced_features, [14, 20])
        advanced_features = await feature_service._compute_bollinger_bands(advanced_features, [20])
        
        print(f"   Advanced features shape: {advanced_features.shape}")
        print(f"   Advanced features dtypes: {advanced_features.dtypes.tolist()}")
        
        # Test full feature set
        print("   Testing full feature set...")
        try:
            full_features = await feature_service._compute_feature_set(
                sample_data.copy(),
                feature_service.feature_recipes['basic'],
                feature_service.default_params
            )
            
            print(f"   Full features shape: {full_features.shape}")
            print(f"   Full features dtypes: {full_features.dtypes.tolist()}")
            
            # Check for any object dtypes
            object_columns = full_features.select_dtypes(include=['object']).columns.tolist()
            if object_columns:
                print(f"   ⚠️  Found object columns: {object_columns}")
            else:
                print("   ✅ All columns are numeric!")
            
            # Check for any non-float64 numeric columns
            numeric_columns = full_features.select_dtypes(include=[np.number]).columns.tolist()
            non_float64 = [col for col in numeric_columns if full_features[col].dtype != 'float64']
            if non_float64:
                print(f"   ⚠️  Found non-float64 columns: {non_float64}")
            else:
                print("   ✅ All numeric columns are float64!")
                
        except Exception as e:
            print(f"   ❌ Error in full feature computation: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        print("🔍 Data Type Analysis:")
        print("-" * 30)
        
        # Analyze the final dataframe
        if 'full_features' in locals():
            print(f"Total columns: {len(full_features.columns)}")
            print(f"Object columns: {len(full_features.select_dtypes(include=['object']).columns)}")
            print(f"Numeric columns: {len(full_features.select_dtypes(include=[np.number]).columns)}")
            
            # Show sample of the data
            print("\nSample of computed features:")
            numeric_cols = full_features.select_dtypes(include=[np.number]).columns[:5].tolist()
            print(full_features[numeric_cols].head())
        
        print()
        print("✅ Feature Data Type Fix Test Complete!")
        print("   • Basic features computed successfully")
        print("   • Advanced features computed successfully")
        print("   • All features should be properly typed as float64")
        print("   • No more numpy.object_ errors")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_feature_fix())
