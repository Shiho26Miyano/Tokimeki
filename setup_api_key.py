#!/usr/bin/env python3
"""
Script to help set up the OpenRouter API key
"""

import os
import sys

def setup_api_key():
    print("🚀 Setting up OpenRouter API Key for Tokimeki")
    print("=" * 50)
    
    # Check if API key is already set
    current_key = os.environ.get("OPENROUTER_API_KEY")
    if current_key and current_key != "your_openrouter_api_key_here":
        print(f"✅ API Key already configured (length: {len(current_key)})")
        return True
    
    print("❌ OpenRouter API key not configured")
    print("\nTo get your API key:")
    print("1. Go to https://openrouter.ai/")
    print("2. Sign up for an account")
    print("3. Get your API key from the dashboard")
    print("4. Set it using one of the methods below")
    
    print("\n📝 Methods to set the API key:")
    print("\nMethod 1 - Environment variable:")
    print("export OPENROUTER_API_KEY='your_actual_api_key_here'")
    
    print("\nMethod 2 - Edit config.py:")
    print("1. Open config.py")
    print("2. Replace 'your_openrouter_api_key_here' with your actual key")
    print("3. Run: python3 config.py")
    
    print("\nMethod 3 - Create .env file:")
    print("Create a .env file with:")
    print("OPENROUTER_API_KEY=your_actual_api_key_here")
    
    print("\nMethod 4 - Set in Railway dashboard (for deployment):")
    print("Add OPENROUTER_API_KEY environment variable")
    
    return False

if __name__ == "__main__":
    setup_api_key() 