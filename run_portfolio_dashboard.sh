#!/bin/bash

# Portfolio Dashboard Launcher Script

echo "🚀 Portfolio Manager Dashboard Launcher"
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if FastAPI backend is running
echo "🔌 Checking backend connection..."
if curl -s http://localhost:8000/api/v1/test > /dev/null; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend is not running on localhost:8000"
    echo "   Please start the FastAPI backend first:"
    echo "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "   Or run in a separate terminal:"
    echo "   ./run_local.sh"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Launch Streamlit dashboard
echo "🎯 Launching Portfolio Dashboard..."
echo "   Dashboard will open in your browser at http://localhost:8501"
echo "   Press Ctrl+C to stop the dashboard"
echo ""

streamlit run portfolio_dashboard.py --server.port 8501 --server.address localhost
