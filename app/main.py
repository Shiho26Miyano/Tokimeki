import os
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from app.core.config import settings
from app.core.middleware import setup_middleware
from app.core.dependencies import get_cache_service, get_usage_service, get_ai_service, get_stock_service
from app.api.v1.api import api_router
from app.services.ai_service import AsyncAIService
from app.services.stock_service import AsyncStockService
from app.services.usage_service import AsyncUsageService
from app.services.cache_service import AsyncCacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def auto_cleanup_models():
    """Automatically clean up old model files on server startup"""
    try:
        import re
        from datetime import datetime
        from pathlib import Path
        
        logger.info("Starting automatic model cleanup...")
        
        # Define the models directory
        models_dir = Path("models")
        
        if not models_dir.exists():
            logger.info("Models directory not found, skipping cleanup")
            return
        
        # Find all .joblib files
        model_files = list(models_dir.glob("*.joblib"))
        
        if not model_files:
            logger.info("No model files found, skipping cleanup")
            return
        
        logger.info(f"Found {len(model_files)} model files for cleanup")
        
        # Group models by type (symbol_modeltype_horizon)
        model_groups = {}
        
        for model_file in model_files:
            # Parse filename: ES=F_transformer_0.5m_20250831_224805.joblib
            filename = model_file.name
            
            # Use regex to extract parts more reliably
            pattern = r'^(.+)_(\d{8}_\d{6})\.joblib$'
            match = re.match(pattern, filename)
            
            if match:
                base_id = match.group(1)  # e.g., ES=F_transformer_0.5m
                timestamp_str = match.group(2)  # e.g., 20250831_224805
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if base_id not in model_groups:
                        model_groups[base_id] = []
                    
                    model_groups[base_id].append({
                        'file': model_file,
                        'timestamp': timestamp,
                        'filename': filename
                    })
                    
                except ValueError:
                    logger.warning(f"Could not parse timestamp from {filename}")
                    continue
            else:
                logger.warning(f"Could not parse filename format: {filename}")
                continue
        
        logger.info(f"Grouped into {len(model_groups)} model types")
        
        # For each group, keep only the most recent model
        total_removed = 0
        total_kept = 0
        
        for base_id, models in model_groups.items():
            if len(models) > 1:
                # Sort by timestamp (newest first)
                models.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Keep the newest one
                newest = models[0]
                older_models = models[1:]
                
                logger.info(f"{base_id}: Keeping {newest['filename']} (newest)")
                
                # Remove older models
                for old_model in older_models:
                    try:
                        os.remove(old_model['file'])
                        logger.info(f"Removed old model: {old_model['filename']}")
                        total_removed += 1
                    except OSError as e:
                        logger.error(f"Error removing {old_model['filename']}: {e}")
                
                total_kept += 1
            else:
                # Only one model of this type, keep it
                logger.info(f"{base_id}: Keeping {models[0]['filename']} (only one)")
                total_kept += 1
        
        logger.info(f"Model cleanup completed: {total_kept} kept, {total_removed} removed")
        
        # Show remaining models
        remaining_files = list(models_dir.glob("*.joblib"))
        if remaining_files:
            logger.info(f"Remaining models ({len(remaining_files)}):")
            for model_file in sorted(remaining_files):
                logger.info(f"  {model_file.name}")
                
    except Exception as e:
        logger.error(f"Error during automatic model cleanup: {e}")
        # Don't fail startup if cleanup fails

# Get the absolute path to the static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
logger.info(f"Static directory path: {STATIC_DIR}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Tokimeki FastAPI - Async AI and Stock Analysis Platform",
    version="1.0.0",
    debug=settings.debug
)

# Setup middleware
setup_middleware(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting Tokimeki FastAPI application...")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API key configured: {bool(settings.openrouter_api_key)}")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"Port: {os.getenv('PORT', '8000')}")
        
        # Auto-cleanup old models on startup (non-blocking)
        try:
            await auto_cleanup_models()
        except Exception as cleanup_error:
            logger.warning(f"Model cleanup failed (non-critical): {cleanup_error}")
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Don't raise the error - let the app start even if cleanup fails
        logger.warning("Continuing with startup despite errors...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    logger.info("Shutting down Tokimeki FastAPI application...")
    from .core.dependencies import cleanup_http_client
    await cleanup_http_client()

# Mount static files with cache busting
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Add middleware to prevent caching of static files
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Add favicon route
@app.get("/favicon.ico")
async def favicon():
    try:
        favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
        logger.info(f"Serving favicon from: {favicon_path}")
        return FileResponse(favicon_path)
    except Exception as e:
        logger.error(f"Error serving favicon: {e}")
        return JSONResponse(status_code=404, content={"error": "Favicon not found"})

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    """Simple health check that responds immediately"""
    try:
        return {"status": "healthy", "timestamp": time.time(), "service": "Tokimeki"}
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}

# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")


# Root endpoint - serve the main HTML page (using absolute path)
@app.get("/")
async def root():
    try:
        index_path = os.path.join(STATIC_DIR, "index.html")
        logger.info(f"Serving index.html from: {index_path}")
        response = FileResponse(index_path)
        # Aggressive cache busting to ensure updated JavaScript loads
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Last-Modified"] = "Thu, 01 Jan 1970 00:00:00 GMT"
        response.headers["ETag"] = f'"{int(time.time())}"'
        return response
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": "Failed to serve main page", "details": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 