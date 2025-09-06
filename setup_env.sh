#!/bin/bash

# Setup script for local development environment
echo "Setting up local environment for Tokimeki..."

# Check if OPENROUTER_API_KEY is already set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "OPENROUTER_API_KEY is not set in your environment."
    echo ""
    echo "To set it up, run one of these commands:"
    echo ""
    echo "Option 1 - Export for current session:"
    echo "export OPENROUTER_API_KEY='sk-or-your-actual-key-here'"
    echo ""
    echo "Option 2 - Add to your shell profile (permanent):"
    echo "echo 'export OPENROUTER_API_KEY=\"sk-or-your-actual-key-here\"' >> ~/.zshrc"
    echo "source ~/.zshrc"
    echo ""
    echo "Option 3 - Create a .env file:"
    echo "echo 'OPENROUTER_API_KEY=sk-or-your-actual-key-here' > .env"
    echo ""
    echo "After setting the API key, restart your server with:"
    echo "python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo "✅ OPENROUTER_API_KEY is already set!"
    echo "Key length: ${#OPENROUTER_API_KEY}"
fi
