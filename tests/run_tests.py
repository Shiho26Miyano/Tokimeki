#!/usr/bin/env python3
"""
Test runner script for Tokimeki project
"""
import subprocess
import sys
import os

def run_tests(test_type="all"):
    """Run tests based on type"""
    
    if test_type == "unit":
        print("🧪 Running unit tests...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/unit/", "-v"])
    elif test_type == "integration":
        print("🔗 Running integration tests...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/integration/", "-v"])
    elif test_type == "e2e":
        print("🏁 Running end-to-end tests...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/e2e/", "-v"])
    elif test_type == "performance":
        print("⚡ Running performance tests...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/performance/", "-v"])
    elif test_type == "model-comparison":
        print("🤖 Running model comparison test...")
        subprocess.run([sys.executable, "tests/unit/test_model_comparison.py"])
    elif test_type == "all":
        print("🎯 Running all tests...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    else:
        print(f"❌ Unknown test type: {test_type}")
        print("Available types: unit, integration, e2e, performance, model-comparison, all")
        return False
    
    return True

if __name__ == "__main__":
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    success = run_tests(test_type)
    sys.exit(0 if success else 1) 