"""
Main entry point for Railway deployment
This file imports the FastAPI app from app.main
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    import os
    from app.core.config import settings
    
    # Try multiple port sources in order of priority
    port = None
    if os.getenv("PORT"):
        try:
            port = int(os.getenv("PORT"))
        except ValueError:
            pass
    
    if port is None:
        port = getattr(settings, 'port', 8000)
    
    print(f"Starting app on port: {port}")
    print(f"Railway PORT env var: {os.getenv('PORT', 'Not set')}")
    print(f"Settings port: {getattr(settings, 'port', 'Not set')}")
    uvicorn.run(app, host="0.0.0.0", port=port) 