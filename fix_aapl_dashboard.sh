#!/bin/bash

echo "🔧 AAPL Analysis Dashboard Fix Script"
echo "====================================="
echo ""

# Check if POLYGON_API_KEY is set
if [ -z "$POLYGON_API_KEY" ]; then
    echo "⚠️  POLYGON_API_KEY is not set!"
    echo ""
    echo "The AAPL Analysis Dashboard requires a Polygon.io API key to fetch stock data."
    echo ""
    echo "To fix this:"
    echo "1. Get a free API key from: https://polygon.io/"
    echo "2. Set the environment variable:"
    echo "   export POLYGON_API_KEY='your-api-key-here'"
    echo ""
    echo "Or add it to your shell profile:"
    echo "   echo 'export POLYGON_API_KEY=\"your-api-key-here\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    echo ""
else
    echo "✅ POLYGON_API_KEY is set!"
fi

# Check if the server is running
echo "Checking if the server is running..."
if curl -s http://localhost:8000/api/v1/aapl-analysis/health > /dev/null 2>&1; then
    echo "✅ Server is running and AAPL API is accessible"
else
    echo "❌ Server is not running or AAPL API is not accessible"
    echo ""
    echo "To start the server:"
    echo "   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
fi

# Test the API endpoint
echo ""
echo "Testing AAPL API endpoint..."
response=$(curl -s "http://localhost:8000/api/v1/aapl-analysis/prices/AAPL?start_date=2024-09-01&end_date=2024-09-28" 2>/dev/null)
if [ $? -eq 0 ] && echo "$response" | grep -q "ticker"; then
    echo "✅ AAPL API is working and returning data"
    echo "   Sample response: $(echo "$response" | head -c 100)..."
else
    echo "❌ AAPL API is not responding correctly"
    echo "   Response: $response"
fi

echo ""
echo "🔍 Troubleshooting Tips:"
echo "========================"
echo ""
echo "1. If the dashboard shows 'Loading...' forever:"
echo "   - Check browser console (F12) for JavaScript errors"
echo "   - Try the debug page: http://localhost:8000/static/aapl-debug.html"
echo ""
echo "2. If you see 'Component Loading Error':"
echo "   - The React components may not be loading properly"
echo "   - Check your internet connection (CDN resources)"
echo "   - Try refreshing the page"
echo ""
echo "3. If you see 'React Loading Error':"
echo "   - React libraries from CDN are not loading"
echo "   - Check your internet connection"
echo "   - Try a different browser"
echo ""
echo "4. Common fixes:"
echo "   - Reload the page (Ctrl+R or Cmd+R)"
echo "   - Clear browser cache"
echo "   - Try incognito/private browsing mode"
echo "   - Check browser console for detailed error messages"
echo ""
echo "📱 Quick Links:"
echo "==============="
echo "Main Dashboard: http://localhost:8000/"
echo "Debug Page:     http://localhost:8000/static/aapl-debug.html"
echo "API Health:     http://localhost:8000/api/v1/aapl-analysis/health"
echo "API Docs:       http://localhost:8000/docs"
echo ""
