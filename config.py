#!/usr/bin/env python3
"""
Simple configuration file for the FastAPI app
You can edit this file to set your API keys
"""

import os

# Set your OpenRouter API key here
# Get it from: https://openrouter.ai/
OPENROUTER_API_KEY = "your_openrouter_api_key_here"

# Set environment variable
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

print(f"API Key configured: {'Yes' if OPENROUTER_API_KEY != 'your_openrouter_api_key_here' else 'No'}")
print(f"API Key length: {len(OPENROUTER_API_KEY)}") 