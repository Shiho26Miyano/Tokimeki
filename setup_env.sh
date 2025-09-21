#!/bin/bash

# Setup script for local development environment
echo "Setting up local environment for Tokimeki..."
echo "=============================================="

# Function to check and setup API key
check_api_key() {
    local key_name=$1
    local key_value=$2
    local description=$3
    local get_url=$4
    
    echo ""
    echo "Checking $key_name..."
    echo "Description: $description"
    
    if [ -z "$key_value" ]; then
        echo "❌ $key_name is not set in your environment."
        echo ""
        echo "To set it up, run one of these commands:"
        echo ""
        echo "Option 1 - Export for current session:"
        echo "export $key_name='your-actual-key-here'"
        echo ""
        echo "Option 2 - Add to your shell profile (permanent):"
        echo "echo 'export $key_name=\"your-actual-key-here\"' >> ~/.zshrc"
        echo "source ~/.zshrc"
        echo ""
        echo "Option 3 - Create a .env file:"
        echo "echo '$key_name=your-actual-key-here' >> .env"
        if [ ! -z "$get_url" ]; then
            echo ""
            echo "Get your API key from: $get_url"
        fi
    else
        echo "✅ $key_name is already set!"
        echo "Key length: ${#key_value}"
        echo "Key preview: ${key_value:0:10}..."
    fi
}

# Check all required API keys
check_api_key "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY" "Required for AI services and chat functionality" "https://openrouter.ai/"

check_api_key "OPENWEATHER_API_KEY" "$OPENWEATHER_API_KEY" "Required for weather analysis in Mini Golf Strategy" "https://openweathermap.org/api"

check_api_key "GOLFCOURSE_API_KEY" "$GOLFCOURSE_API_KEY" "Required for golf course data in Mini Golf Strategy" "https://golfcourseapi.com/"

# Optional API keys
echo ""
echo "=============================================="
echo "OPTIONAL API KEYS (for enhanced features):"
echo "=============================================="

check_api_key "FUTUREQUANT_DATABASE_URL" "$FUTUREQUANT_DATABASE_URL" "Database URL for FutureQuant (defaults to SQLite)" ""

check_api_key "MLFLOW_TRACKING_URI" "$MLFLOW_TRACKING_URI" "MLflow tracking URI for model management" ""

check_api_key "REDIS_URL" "$REDIS_URL" "Redis URL for caching (optional)" ""

# Summary
echo ""
echo "=============================================="
echo "SETUP SUMMARY:"
echo "=============================================="

required_keys=("OPENROUTER_API_KEY" "OPENWEATHER_API_KEY" "GOLFCOURSE_API_KEY")
all_required_set=true

for key in "${required_keys[@]}"; do
    eval "key_value=\$$key"
    if [ -z "$key_value" ]; then
        echo "❌ $key - NOT SET"
        all_required_set=false
    else
        echo "✅ $key - SET"
    fi
done

echo ""
if [ "$all_required_set" = true ]; then
    echo "🎉 All required API keys are configured!"
    echo ""
    echo "To start the server:"
    echo "python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo "⚠️  Some required API keys are missing. Please set them up before running the server."
fi

echo ""
echo "For more information, see the documentation in docs/"
