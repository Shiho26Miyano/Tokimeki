#!/usr/bin/env python3
"""
Test script to verify automatic model cleanup on server startup
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

async def test_startup_cleanup():
    """Test the startup cleanup function"""
    print("Testing automatic model cleanup on startup...")
    
    try:
        from app.main import auto_cleanup_models
        
        # Create some test model files
        models_dir = "models"
        os.makedirs(models_dir, exist_ok=True)
        
        # Create test files with different timestamps
        test_files = [
            "ES=F_transformer_0.5m_20250831_220000.joblib",
            "ES=F_transformer_0.5m_20250831_221000.joblib", 
            "ES=F_transformer_0.5m_20250831_222000.joblib",
            "ES=F_transformer_0.5m_20250831_223000.joblib"
        ]
        
        print(f"Creating {len(test_files)} test model files...")
        for filename in test_files:
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"Test model: {filename}")
        
        print("Test files created:")
        for filename in os.listdir(models_dir):
            print(f"  {filename}")
        
        # Run the cleanup function
        print("\nRunning automatic cleanup...")
        await auto_cleanup_models()
        
        # Check results
        print("\nAfter cleanup:")
        remaining_files = os.listdir(models_dir)
        if remaining_files:
            for filename in remaining_files:
                print(f"  {filename}")
        else:
            print("  No files remaining")
        
        print(f"\nCleanup test completed. {len(remaining_files)} files remaining.")
        
        # Clean up test files
        for filename in remaining_files:
            if filename.startswith("ES=F_transformer_0.5m_20250831_22"):
                os.remove(os.path.join(models_dir, filename))
                print(f"Removed test file: {filename}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_startup_cleanup())
