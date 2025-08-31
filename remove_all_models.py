#!/usr/bin/env python3
"""
Remove all existing model files - use with caution!
"""

import os
import glob

def remove_all_models():
    """Remove all existing model files"""
    
    # Get all model files
    model_files = glob.glob("models/*.joblib")
    
    if not model_files:
        print("No model files found in models/ directory")
        return
    
    print(f"Found {len(model_files)} model files:")
    for file_path in model_files:
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        print(f"  - {filename} ({size} bytes)")
    
    # Confirm before proceeding
    print(f"\n⚠️  WARNING: This will delete ALL {len(model_files)} model files!")
    response = input("Are you sure you want to delete ALL models? Type 'DELETE ALL' to confirm: ")
    
    if response == "DELETE ALL":
        deleted_count = 0
        for file_path in model_files:
            try:
                os.remove(file_path)
                filename = os.path.basename(file_path)
                print(f"🗑️  Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {os.path.basename(file_path)}: {e}")
        
        print(f"\n🎯 All {deleted_count} model files have been removed!")
        
        # Verify directory is empty
        remaining = glob.glob("models/*.joblib")
        if not remaining:
            print("✅ Models directory is now clean")
        else:
            print(f"⚠️  {len(remaining)} files still remain")
    else:
        print("❌ Operation cancelled. No files were deleted.")

if __name__ == "__main__":
    print("🧹 FutureQuant - Remove ALL Models Tool")
    print("=" * 45)
    remove_all_models()
