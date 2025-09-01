#!/bin/bash

# Auto-cleanup script for old model files
# This script can be run manually or added to cron for automatic cleanup

echo "Starting automatic model cleanup at $(date)"

# Change to the project directory
cd "$(dirname "$0")/.."

# Run the cleanup script
python3 scripts/cleanup_old_models.py

echo "Model cleanup completed at $(date)"
echo "----------------------------------------"
