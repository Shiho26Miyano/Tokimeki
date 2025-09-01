# Railway Deployment Guide for Tokimeki

## Current Issues & Solutions

### 1. Port Configuration Fixed
- **Problem**: Port mismatch between `main.py` (8080) and Dockerfile (8000)
- **Solution**: Updated `main.py` to use port 8000 and made Dockerfile use Railway's `$PORT` environment variable

### 2. Health Check Endpoint Added
- **Problem**: Dockerfile expected `/health` endpoint that didn't exist
- **Solution**: Added health check endpoint in `app/main.py`

### 3. Range Error Fix Implemented
- **Problem**: "You reached the start of the range" error in Lean service
- **Solution**: Added comprehensive validation in `app/services/futurequant/lean_service.py`

## Railway Configuration

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Environment Variables
Set these in Railway dashboard:

```
ENVIRONMENT=production
DEBUG=false
PORT=8000
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url
OPENROUTER_API_KEY=your_api_key
```

## Deployment Steps

### 1. Commit and Push Changes
```bash
git add .
git commit -m "Fix Railway deployment issues"
git push origin main
```

### 2. Railway CLI Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

### 3. Railway Dashboard Deployment
1. Go to [Railway Dashboard](https://railway.app)
2. Select your project
3. Go to Deployments tab
4. Click "Deploy" button
5. Monitor the build logs for any errors

## Troubleshooting

### If Still Getting 502 Errors

1. **Check Build Logs**
   - Go to Railway dashboard → Deployments → Latest deployment
   - Check build logs for Python errors

2. **Check Runtime Logs**
   - Go to Railway dashboard → Deployments → Latest deployment
   - Check runtime logs for application errors

3. **Common Issues**
   - **Memory Limit**: Railway has memory limits, ensure your app doesn't exceed them
   - **Build Timeout**: Large dependencies might cause build timeouts
   - **Port Binding**: Ensure the app binds to `0.0.0.0` and uses `$PORT`

### Debug Commands

Add these to your Railway environment variables for debugging:
```
DEBUG=true
LOG_LEVEL=DEBUG
```

### Health Check
Test if your app is running:
```bash
curl https://your-app.railway.app/health
```

## Performance Optimization

### 1. Reduce Dependencies
Consider removing heavy dependencies for production:
```python
# Comment out in requirements.txt if not needed
# pytorch-lightning==2.1.3
# mlflow==2.8.1
# vectorbt==0.28.1
```

### 2. Use Lighter Alternatives
```python
# Instead of full PyTorch
# torch==2.3.1
torch-cpu==2.3.1

# Instead of full scikit-learn
scikit-learn-intelex==1.4.2
```

### 3. Optimize Dockerfile
```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder
# ... build dependencies

FROM python:3.11-slim as runtime
# ... copy only runtime files
```

## Monitoring

### 1. Railway Metrics
- CPU usage
- Memory usage
- Network I/O
- Response times

### 2. Application Logs
- FastAPI logs
- Custom application logs
- Error tracking

### 3. Health Checks
- `/health` endpoint
- Database connectivity
- External service dependencies

## Rollback Strategy

If deployment fails:
1. Go to Railway dashboard → Deployments
2. Find the last working deployment
3. Click "Deploy" on that version
4. Investigate the failed deployment logs

## Support

If issues persist:
1. Check Railway status: https://status.railway.app
2. Railway Discord: https://discord.gg/railway
3. Railway documentation: https://docs.railway.app
