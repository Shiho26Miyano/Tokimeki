# Railway Deployment Guide with Redis

## 🚀 **Step 1: Add Redis Service**

1. **In your Railway dashboard:**
   - Go to your project
   - Click "New Service"
   - Select "Redis" from the database options
   - Railway will automatically provision a Redis instance

2. **Connect Redis to your app:**
   - In your app service, go to "Variables" tab
   - Add the Redis connection URL from the Redis service
   - The variable should be named: `REDIS_URL`

## 🔧 **Step 2: Environment Variables**

Add these environment variables to your Railway app:

```bash
# Redis Configuration
REDIS_URL=redis://your-railway-redis-url:port
CACHE_ENABLED=true
CACHE_TTL=300

# Usage Limits
DAILY_REQUEST_LIMIT=1000
HOURLY_REQUEST_LIMIT=100
MONTHLY_REQUEST_LIMIT=10000

# Rate Limiting
RATE_LIMIT_DAILY=200
RATE_LIMIT_HOURLY=50

# OpenRouter API
OPENROUTER_API_KEY=your_api_key_here
```

## 📊 **Step 3: Verify Redis Connection**

After deployment, check these endpoints:

1. **Cache Status**: `https://your-app.railway.app/api/cache-status`
2. **Usage Stats**: `https://your-app.railway.app/api/usage-stats`
3. **Monitoring Dashboard**: Check the 📊 Monitoring tab in your app

## 🔍 **Step 4: Testing Redis Functionality**

### **Test 1: Cache Hit/Miss**
- Make the same API request twice
- First request should be slower (cache miss)
- Second request should be faster (cache hit)
- Check logs for "💾 Cached result" and "✅ Cache hit" messages

### **Test 2: Rate Limiting**
- Make multiple rapid requests
- Should see rate limit warnings in UI
- Check for HTTP 429 responses

### **Test 3: Usage Tracking**
- Make several API calls
- Check monitoring dashboard for updated stats
- Verify cost tracking is working

## 🛠️ **Step 5: Troubleshooting**

### **If Redis Connection Fails:**
1. Check `REDIS_URL` environment variable
2. Verify Redis service is running in Railway
3. Check Railway logs for connection errors
4. Ensure Redis service is in the same project as your app

### **If Caching Not Working:**
1. Verify `CACHE_ENABLED=true`
2. Check `/api/cache-status` endpoint
3. Look for cache-related log messages
4. Test with simple API calls

### **If Rate Limiting Not Working:**
1. Check rate limit environment variables
2. Verify Flask-Limiter is properly configured
3. Test with rapid requests
4. Check for 429 status codes

## 📈 **Step 6: Monitoring**

### **Railway Dashboard:**
- Monitor Redis service usage
- Check memory and CPU usage
- View connection metrics

### **Application Monitoring:**
- Use the 📊 Monitoring tab
- Check usage statistics
- Monitor cost tracking
- View cache hit rates

## 💰 **Step 7: Cost Optimization**

### **Redis Usage:**
- Monitor Redis memory usage
- Set appropriate TTL values
- Clear cache periodically if needed

### **API Usage:**
- Track costs per model
- Monitor rate limit usage
- Optimize request patterns

## 🔒 **Step 8: Security**

### **Redis Security:**
- Railway Redis is automatically secured
- Connection uses Railway's internal network
- No public access to Redis instance

### **Environment Variables:**
- Keep API keys secure
- Use Railway's secret management
- Don't commit sensitive data to git

## 📝 **Step 9: Deployment Checklist**

- [ ] Redis service added to Railway
- [ ] `REDIS_URL` environment variable set
- [ ] All environment variables configured
- [ ] Application deployed successfully
- [ ] Cache status endpoint working
- [ ] Rate limiting functional
- [ ] Usage tracking active
- [ ] Monitoring dashboard accessible
- [ ] Cost tracking operational 