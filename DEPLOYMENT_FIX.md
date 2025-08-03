# Railway Deployment Fix for FastAPI

## Problem
The FastAPI application was failing to deploy on Railway with the error:
```
Failed to find attribute 'app' in 'app'.
```

## Root Cause
The issue was caused by a conflict between the old Flask `app.py` file in the root directory and the new FastAPI application structure. Railway was trying to import `app:app` which was finding the Flask app instead of the FastAPI app.

## Solution

### 1. Created New Entry Point
Created `main.py` in the root directory to serve as the proper entry point for Railway:

```python
"""
Main entry point for Railway deployment
This file imports the FastAPI app from app.main
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 2. Updated Procfile
Changed the Procfile to use the new entry point:

```bash
# Before (incorrect)
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --timeout 300 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --log-level info

# After (correct)
web: gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --timeout 300 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --log-level info
```

### 3. Verified Dependencies
Ensured `requirements_fastapi.txt` contains all necessary dependencies:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
python-multipart==0.0.6
slowapi==0.1.9
pydantic-settings==2.1.0
redis==5.0.1
psutil==5.9.8
# ... other dependencies
```

## Deployment Steps

### 1. Local Testing
Before deploying, test locally:

```bash
# Activate virtual environment
source venv/bin/activate

# Test imports
python3 verify_deployment_fastapi.py

# Test server locally
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 2. Railway Deployment
1. Push changes to your repository
2. Railway will automatically detect the changes
3. The deployment should now work correctly

### 3. Verification
After deployment, test the endpoints:

```bash
# Health check
curl https://your-app.railway.app/health

# Test chat endpoint
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "include_stock_analysis": false}'
```

## File Structure
```
Tokimeki/
├── main.py                    # New entry point for Railway
├── Procfile                   # Updated to use main:app
├── requirements_fastapi.txt   # FastAPI dependencies
├── app/
│   ├── main.py               # FastAPI application
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── middleware.py
│   └── services/
│       ├── ai_service.py
│       ├── stock_service.py
│       ├── cache_service.py
│       └── usage_service.py
└── app.py                    # Old Flask app (can be ignored)
```

## Performance Optimizations Included

The deployment also includes the performance optimizations:

1. **Persistent HTTP Client**: Better connection pooling
2. **Optional Stock Analysis**: Faster responses for simple queries
3. **Timeout Handling**: Prevents hanging requests
4. **Enhanced Error Handling**: Better debugging

## Monitoring

### Health Check
```bash
curl https://your-app.railway.app/health
```

### Performance Stats
```bash
curl https://your-app.railway.app/api/performance-stats
```

### Test API Performance
```bash
curl https://your-app.railway.app/api/test-performance
```

## Troubleshooting

### If Deployment Still Fails

1. **Check Logs**: Look at Railway logs for specific error messages
2. **Verify Dependencies**: Ensure all packages in `requirements_fastapi.txt` are installed
3. **Test Locally**: Run `python3 verify_deployment_fastapi.py` locally
4. **Check Environment Variables**: Ensure `OPENROUTER_API_KEY` is set in Railway

### Common Issues

1. **Import Errors**: Make sure all modules can be imported
2. **Missing Dependencies**: Check if all packages are in requirements file
3. **Environment Variables**: Verify API keys are configured
4. **Port Issues**: Ensure the app listens on the correct port

## Migration Notes

- The old Flask `app.py` is still present but not used
- All FastAPI endpoints maintain the same URLs as the Flask version
- Performance is significantly improved with the optimizations
- Stock analysis is now optional for faster responses

## Next Steps

1. Deploy to Railway
2. Test all endpoints
3. Monitor performance
4. Configure environment variables (API keys)
5. Set up monitoring and alerts 