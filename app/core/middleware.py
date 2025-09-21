"""
Middleware configuration for FastAPI application
"""
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
import time
import logging
from .config import settings

logger = logging.getLogger(__name__)

def setup_middleware(app):
    """Setup all middleware for the FastAPI app"""
    
    # CORS middleware (hardened)
    configured_origins = settings.cors_origins or ["*"]
    wildcard = "*" in configured_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins,
        # Per CORS spec, credentials must be disabled when using wildcard origins
        allow_credentials=False if wildcard else True,
        allow_methods=settings.cors_methods or ["GET", "POST", "OPTIONS"],
        allow_headers=settings.cors_headers or ["Content-Type", "Authorization"],
    )
    
    # Rate limiter
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response 