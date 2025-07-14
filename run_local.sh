#!/bin/bash

# Local development script for Tokimeki
# Make sure to set your OPENROUTER_API_KEY before running

echo "🚀 Starting Tokimeki locally..."

# Check if .env file exists
if [ -f .env ]; then
    echo "✅ Found .env file, loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Please create one or set OPENROUTER_API_KEY manually."
    echo "   See SETUP.md for instructions."
fi

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY not set!"
    echo "   Please set it in your .env file or export it manually."
    echo "   Get your key from: https://openrouter.ai/settings/keys"
    exit 1
fi

echo "✅ API key configured"
echo "🌐 Starting Flask app on http://localhost:8080"

# Start the Flask app
python app.py 