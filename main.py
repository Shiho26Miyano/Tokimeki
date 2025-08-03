"""
Main entry point for Railway deployment
This file imports the FastAPI app from app.main
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 