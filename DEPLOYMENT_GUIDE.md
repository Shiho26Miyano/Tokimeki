# FutureQuant Enhanced Trading Platform - Deployment Guide

This guide covers deploying the enhanced FutureQuant trading platform with Bloomberg-style UI, real-time data streaming, and quantitative analysis capabilities.

## Overview

The enhanced FutureQuant platform includes:
- **Bloomberg-style UI** with dark theme and grid layout
- **Real-time WebSocket streaming** for live data updates
- **Quantitative analysis integration** (VectorBT, QF-Lib, Lean)
- **Containerized deployment** with Docker
- **Scalable architecture** with PostgreSQL and Redis

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Dashboard)   │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Redis Cache   │    │   MLflow        │
│   (Real-time)   │    │   (Sessions)    │    │   (ML Models)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

## Quick Start with Docker

### 1. Clone and Setup

```bash
git clone <repository-url>
cd FutureQuant
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://futurequant:password@localhost:5432/futurequant
REDIS_URL=redis://localhost:6379

# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# API Keys (if needed)
YAHOO_FINANCE_API_KEY=your-api-key
ALPHA_VANTAGE_API_KEY=your-api-key

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=futurequant
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f futurequant

# Check service status
docker-compose ps
```

### 4. Access the Platform

- **Dashboard**: http://localhost:8000/static/futurequant-enhanced.html
- **API Documentation**: http://localhost:8000/docs
- **MLflow**: http://localhost:5000
- **Database**: localhost:5432
- **Redis**: localhost:6379

## Manual Deployment

### 1. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/futurequant"
export REDIS_URL="redis://localhost:6379"

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Database Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql  # macOS

# Create database and user
sudo -u postgres psql
CREATE DATABASE futurequant;
CREATE USER futurequant WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE futurequant TO futurequant;
\q

# Run migrations
alembic upgrade head
```

### 3. Redis Setup

```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Start Redis
sudo systemctl start redis-server  # Ubuntu/Debian
brew services start redis  # macOS
```

## Production Deployment

### 1. Docker Production

```bash
# Build production image
docker build -t futurequant:production .

# Run with production settings
docker run -d \
  --name futurequant-prod \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379 \
  futurequant:production
```

### 2. Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: futurequant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: futurequant
  template:
    metadata:
      labels:
        app: futurequant
    spec:
      containers:
      - name: futurequant
        image: futurequant:production
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: futurequant-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: futurequant-service
spec:
  selector:
    app: futurequant
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Cloud Deployment

#### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Render

```bash
# Connect GitHub repository
# Render will auto-deploy on push to main branch
```

#### AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag futurequant:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/futurequant:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/futurequant:latest

# Deploy to ECS
aws ecs create-service --cluster futurequant-cluster --service-name futurequant-service --task-definition futurequant-task
```

## Configuration

### 1. Dashboard Configuration

Edit `static/futurequant-dashboard-enhanced.js`:

```javascript
this.config = {
    apiBaseUrl: process.env.API_BASE_URL || '/api/v1',
    wsBaseUrl: process.env.WS_BASE_URL || 'ws://localhost:8000/ws',
    refreshInterval: 5000,
    maxRetries: 3,
    retryDelay: 1000,
    enableMockMode: process.env.ENABLE_MOCK_MODE === 'true',
    enableHotkeys: true,
    enableNotifications: true,
    enableDraggablePanels: true
};
```

### 2. API Configuration

Edit `app/core/config.py`:

```python
class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://localhost/futurequant"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key"
    access_token_expire_minutes: int = 30
    
    # External APIs
    yahoo_finance_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "futurequant"
    
    class Config:
        env_file = ".env"
```

### 3. WebSocket Configuration

Edit `app/api/v1/endpoints/websocket.py`:

```python
class ConnectionManager:
    def __init__(self):
        self.max_connections = int(os.getenv('MAX_WS_CONNECTIONS', '1000'))
        self.heartbeat_interval = int(os.getenv('WS_HEARTBEAT_INTERVAL', '30'))
        self.active_connections: Dict[str, List[WebSocket]] = {
            "price_updates": [],
            "signal_updates": [],
            "trade_updates": [],
            "job_updates": []
        }
```

## Monitoring and Logging

### 1. Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis
```

### 2. Logging

```python
# Configure logging in app/core/config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('futurequant.log'),
        logging.StreamHandler()
    ]
)
```

### 3. Metrics

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Add to FastAPI app
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security

### 1. Authentication

```python
# JWT token authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return username
```

### 2. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/data")
@limiter.limit("100/minute")
async def get_data(request: Request):
    return {"data": "example"}
```

## Troubleshooting

### 1. Common Issues

#### Dashboard not loading
```bash
# Check browser console for errors
# Verify static files are served correctly
curl http://localhost:8000/static/futurequant-enhanced.html

# Check CORS configuration
# Verify WebSocket connection
```

#### Database connection issues
```bash
# Test database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Check database logs
docker-compose logs db

# Verify environment variables
echo $DATABASE_URL
```

#### WebSocket connection issues
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8000/ws

# Check WebSocket logs
docker-compose logs futurequant | grep WebSocket

# Verify firewall settings
```

### 2. Performance Issues

```bash
# Monitor resource usage
docker stats

# Check database performance
docker exec -it <db-container> psql -U futurequant -d futurequant -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis memory usage
docker exec -it <redis-container> redis-cli info memory
```

### 3. Log Analysis

```bash
# View application logs
docker-compose logs -f futurequant

# Search for errors
docker-compose logs futurequant | grep -i error

# Monitor real-time logs
docker-compose logs -f --tail=100 futurequant
```

## Scaling

### 1. Horizontal Scaling

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  futurequant:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 2. Load Balancing

```nginx
# nginx.conf
upstream futurequant_backend {
    server futurequant:8000;
    server futurequant:8001;
    server futurequant:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://futurequant_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Database Scaling

```yaml
# Add read replicas
services:
  db-read:
    image: postgres:15
    environment:
      - POSTGRES_DB=futurequant
      - POSTGRES_USER=futurequant
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_read_data:/var/lib/postgresql/data
    command: postgres -c hot_standby=on
```

## Backup and Recovery

### 1. Database Backup

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec <db-container> pg_dump -U futurequant futurequant > $BACKUP_DIR/backup_$DATE.sql

# Restore from backup
docker exec -i <db-container> psql -U futurequant -d futurequant < backup_20240101_120000.sql
```

### 2. Configuration Backup

```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    .env \
    app/core/config.py \
    docker-compose.yml \
    nginx.conf
```

### 3. Disaster Recovery

```bash
# Create recovery script
#!/bin/bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d db
sleep 30
docker exec -i <db-container> psql -U futurequant -d futurequant < latest_backup.sql

# Restart services
docker-compose up -d
```

## Support and Maintenance

### 1. Regular Maintenance

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up old containers and images
docker system prune -f
```

### 2. Monitoring Setup

```bash
# Set up monitoring with Prometheus and Grafana
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Documentation

- Keep API documentation updated
- Document configuration changes
- Maintain deployment procedures
- Record troubleshooting steps

## Conclusion

The enhanced FutureQuant platform provides a robust, scalable solution for quantitative trading with a professional Bloomberg-style interface. Follow this deployment guide to ensure successful deployment and operation.

For additional support:
- Check the troubleshooting section
- Review logs for error details
- Consult the API documentation
- Refer to the quantitative analysis README
