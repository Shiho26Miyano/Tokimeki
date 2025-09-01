# 🚀 Local Development Guide for Tokimeki

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements-railway.txt
```

### 2. Start the Application
```bash
# Option A: Use the startup script (Recommended)
python3 start_local.py

# Option B: Use uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Access Your App
- **Local**: http://localhost:8080/
- **Network**: http://0.0.0.0:8080/
- **Health Check**: http://localhost:8080/health

## 🧪 Testing

### Test All Endpoints
```bash
python3 test_app.py
```

### Manual Testing
```bash
# Health check
curl http://localhost:8080/health

# Root endpoint
curl http://localhost:8080/

# API status
curl http://localhost:8080/api/status

# API version
curl http://localhost:8080/api/version
```

## 🔧 Configuration

### Port Configuration
- **Local Development**: Port 8080 (default)
- **Railway Deployment**: Port 8000 (via $PORT environment variable)

### Environment Variables
```bash
# Local development
export PORT=8080

# Railway deployment
export PORT=8000
```

## 📁 File Structure
```
Tokimeki/
├── app/
│   ├── main.py              # Main FastAPI application
│   └── core/
│       └── config.py        # Configuration settings
├── start_local.py           # Local development startup script
├── test_app.py              # Testing script
├── requirements-railway.txt # Minimal dependencies
└── Dockerfile               # Railway deployment
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>
```

### Import Errors
```bash
# Make sure you're in the right directory
cd /path/to/Tokimeki

# Install dependencies
pip install -r requirements-railway.txt
```

### Permission Issues
```bash
# Make scripts executable
chmod +x start_local.py
chmod +x test_app.py
```

## 🔄 Development Workflow

1. **Start the app**: `python3 start_local.py`
2. **Make changes** to your code
3. **Auto-reload** will restart the app automatically
4. **Test changes**: `python3 test_app.py`
5. **Deploy to Railway** when ready

## 📊 Expected Responses

### Health Check (`/health`)
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "service": "Tokimeki FastAPI",
  "version": "1.0.0"
}
```

### Root Endpoint (`/`)
```json
{
  "message": "Welcome to Tokimeki FastAPI",
  "status": "running",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "static": "/static"
  }
}
```

## 🎯 Next Steps

Once local development is working:
1. **Test all endpoints** using test_app.py
2. **Make your changes** and test locally
3. **Commit and push** your changes
4. **Deploy to Railway** for production testing

---

**Happy coding! 🚀**
