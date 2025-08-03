"""
API dependencies and utilities
"""
from fastapi import Depends, HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Common dependency functions
async def verify_api_key(api_key: Optional[str] = None):
    """Verify API key if required"""
    if api_key is None:
        return True
    # Add API key verification logic here if needed
    return True

async def get_current_user():
    """Get current user (placeholder for authentication)"""
    # Add user authentication logic here if needed
    return {"user_id": "anonymous"}

async def validate_request_data(data: dict):
    """Validate request data"""
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request data is required"
        )
    return data 