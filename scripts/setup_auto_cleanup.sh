#!/bin/bash

# Setup script for automatic model cleanup
# This script sets up cron jobs to automatically clean up old models

echo "Setting up automatic model cleanup..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLEANUP_SCRIPT="$SCRIPT_DIR/auto_cleanup_models.sh"

echo "Project directory: $PROJECT_DIR"
echo "Cleanup script: $CLEANUP_SCRIPT"

# Check if cleanup script exists and is executable
if [ ! -x "$CLEANUP_SCRIPT" ]; then
    echo "Error: Cleanup script not found or not executable"
    exit 1
fi

# Create a temporary cron file
TEMP_CRON=$(mktemp)

# Export current cron jobs
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# FutureQuant Trader Auto Cleanup" > "$TEMP_CRON"

# Check if cleanup job already exists
if grep -q "auto_cleanup_models.sh" "$TEMP_CRON"; then
    echo "Cleanup job already exists in crontab"
    echo "Current crontab entries:"
    crontab -l | grep -E "(auto_cleanup|FutureQuant)"
else
    # Add cleanup job to run every hour
    echo "# Clean up old models every hour" >> "$TEMP_CRON"
    echo "0 * * * * $CLEANUP_SCRIPT >> $PROJECT_DIR/logs/model_cleanup.log 2>&1" >> "$TEMP_CRON"
    
    # Add cleanup job to run daily at 2 AM (keep only newest models)
    echo "# Daily cleanup - keep only newest models" >> "$TEMP_CRON"
    echo "0 2 * * * cd $PROJECT_DIR && python3 scripts/cleanup_old_models.py >> logs/model_cleanup.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    
    echo "Added cleanup jobs to crontab:"
    echo "  - Every hour: Basic cleanup"
    echo "  - Daily at 2 AM: Full cleanup (keep only newest)"
fi

# Clean up temporary file
rm "$TEMP_CRON"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

echo ""
echo "Automatic cleanup setup complete!"
echo ""
echo "Cron jobs installed:"
crontab -l | grep -E "(auto_cleanup|FutureQuant|cleanup_old_models)"
echo ""
echo "Logs will be written to: $PROJECT_DIR/logs/model_cleanup.log"
echo ""
echo "To manually run cleanup:"
echo "  python3 scripts/cleanup_old_models.py"
echo "  ./scripts/auto_cleanup_models.sh"
echo ""
echo "To remove cleanup jobs:"
echo "  crontab -e"
echo "  (then delete the FutureQuant cleanup lines)"
