#!/usr/bin/env python3
"""
Simple configuration file for the FastAPI app
You can edit this file to set your API keys
"""

import os

# Get API keys from environment variables only
# Set them with: export OPENROUTER_API_KEY='your_key_here'
# Get OpenRouter key from: https://openrouter.ai/
# Get Polygon key from: https://polygon.io/
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Set environment variables (in case they're not already set)
if OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
if POLYGON_API_KEY:
    os.environ["POLYGON_API_KEY"] = POLYGON_API_KEY

print(f"OpenRouter API Key configured: {'Yes' if OPENROUTER_API_KEY else 'No'}")
print(f"OpenRouter API Key length: {len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 0}")
print(f"Polygon API Key configured: {'Yes' if POLYGON_API_KEY else 'No'}")
print(f"Polygon API Key length: {len(POLYGON_API_KEY) if POLYGON_API_KEY else 0}") 