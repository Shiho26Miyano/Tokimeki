#!/usr/bin/env python3
"""
Startup script for AAPL Analysis Dashboard
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.aapl_config import get_settings, validate_environment, print_config_summary


def setup_logging():
    """Setup logging configuration"""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "aapl_dashboard.log")
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce HTTP client noise


def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "httpx",
        "pydantic",
        "pydantic_settings"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main startup function"""
    print("🚀 Starting AAPL Analysis Dashboard...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Print configuration summary
    print_config_summary()
    
    # Validate environment
    try:
        validate_environment()
        logger.info("✅ Configuration validation passed")
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        print("\nPlease fix the configuration issues above before starting the dashboard.")
        sys.exit(1)
    
    # Get settings
    settings = get_settings()
    
    # Import and start the application
    try:
        import uvicorn
        from main import app
        
        logger.info(f"🌟 Starting AAPL Analysis Dashboard on {settings.host}:{settings.port}")
        print(f"\n📊 Dashboard will be available at:")
        print(f"   • Main API: http://{settings.host}:{settings.port}/api/v1/aapl-analysis/")
        print(f"   • Dashboard UI: http://{settings.host}:{settings.port}/static/aapl-analysis.html")
        print(f"   • API Docs: http://{settings.host}:{settings.port}/docs")
        print(f"   • Health Check: http://{settings.host}:{settings.port}/api/v1/aapl-analysis/health")
        print()
        
        # Start the server
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            workers=settings.workers,
            reload=settings.reload,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"❌ Failed to import required modules: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
