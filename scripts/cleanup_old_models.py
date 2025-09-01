#!/usr/bin/env python3
"""
Script to automatically clean up old model files
Keeps only the most recent model for each type and removes older versions
"""

import os
import glob
import re
from datetime import datetime
from pathlib import Path

def cleanup_old_models():
    """Clean up old model files, keeping only the most recent ones"""
    
    # Define the models directory
    models_dir = Path("models")
    
    if not models_dir.exists():
        print("Models directory not found")
        return
    
    print("Scanning for model files...")
    
    # Find all .joblib files
    model_files = list(models_dir.glob("*.joblib"))
    
    if not model_files:
        print("No model files found")
        return
    
    print(f"Found {len(model_files)} model files")
    
    # Group models by type (symbol_modeltype_horizon)
    model_groups = {}
    
    for model_file in model_files:
        # Parse filename: ES=F_transformer_0.5m_20250831_224805.joblib
        filename = model_file.name
        
        # Use regex to extract parts more reliably
        pattern = r'^(.+)_(\d{8}_\d{6})\.joblib$'
        match = re.match(pattern, filename)
        
        if match:
            base_id = match.group(1)  # e.g., ES=F_transformer_0.5m
            timestamp_str = match.group(2)  # e.g., 20250831_224805
            
            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if base_id not in model_groups:
                    model_groups[base_id] = []
                
                model_groups[base_id].append({
                    'file': model_file,
                    'timestamp': timestamp,
                    'filename': filename
                })
                
            except ValueError:
                print(f"Could not parse timestamp from {filename}")
                continue
        else:
            print(f"Could not parse filename format: {filename}")
            continue
    
    print(f"Grouped into {len(model_groups)} model types")
    
    # For each group, keep only the most recent model
    total_removed = 0
    total_kept = 0
    
    for base_id, models in model_groups.items():
        if len(models) > 1:
            # Sort by timestamp (newest first)
            models.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Keep the newest one
            newest = models[0]
            older_models = models[1:]
            
            print(f"\n{base_id}:")
            print(f"  Keeping: {newest['filename']} (newest)")
            
            # Remove older models
            for old_model in older_models:
                try:
                    os.remove(old_model['file'])
                    print(f"  Removed: {old_model['filename']}")
                    total_removed += 1
                except OSError as e:
                    print(f"  Error removing {old_model['filename']}: {e}")
            
            total_kept += 1
        else:
            # Only one model of this type, keep it
            print(f"\n{base_id}: Keeping {models[0]['filename']} (only one)")
            total_kept += 1
    
    print(f"\nCleanup complete!")
    print(f"Models kept: {total_kept}")
    print(f"Models removed: {total_removed}")
    
    # Show remaining models
    remaining_files = list(models_dir.glob("*.joblib"))
    if remaining_files:
        print(f"\nRemaining models ({len(remaining_files)}):")
        for model_file in sorted(remaining_files):
            print(f"  {model_file.name}")

def cleanup_by_age(days_old=7):
    """Remove models older than specified days"""
    
    models_dir = Path("models")
    
    if not models_dir.exists():
        print("Models directory not found")
        return
    
    cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
    
    print(f"Removing models older than {days_old} days...")
    
    model_files = list(models_dir.glob("*.joblib"))
    removed_count = 0
    
    for model_file in model_files:
        # Get file modification time
        mtime = model_file.stat().st_mtime
        
        if mtime < cutoff_date:
            try:
                os.remove(model_file)
                print(f"Removed old model: {model_file.name}")
                removed_count += 1
            except OSError as e:
                print(f"Error removing {model_file.name}: {e}")
    
    print(f"Removed {removed_count} old models")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--age":
        # Remove models by age
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cleanup_by_age(days)
    else:
        # Default cleanup: keep only newest of each type
        cleanup_old_models()
