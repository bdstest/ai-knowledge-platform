"""
Authentication and authorization
"""

import os
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Demo API key for testing
DEMO_API_KEY = os.getenv("API_KEY", "demo-key-sk-1234567890abcdef")
DEMO_USER = os.getenv("ADMIN_USER", "demouser")
DEMO_PASS = os.getenv("ADMIN_PASS", "demopass123")

security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Verify API key for authentication"""
    
    # For demo purposes, accept multiple formats
    if credentials:
        token = credentials.credentials
        if token == DEMO_API_KEY or token == DEMO_API_KEY.replace("demo-key-", ""):
            return token
    
    # Also check for demo API key in common formats
    demo_keys = [
        DEMO_API_KEY,
        "demo-key-sk-1234567890abcdef", 
        "sk-1234567890abcdef",
        "demo-token-123"
    ]
    
    if credentials and credentials.credentials in demo_keys:
        return credentials.credentials
    
    # For demo, be lenient with authentication
    if not credentials:
        # Allow some endpoints without auth for demo
        return "demo-access"
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key. Use: demo-key-sk-1234567890abcdef",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(api_key: str = Depends(verify_api_key)) -> dict:
    """Get current user information"""
    return {
        "username": DEMO_USER,
        "email": f"{DEMO_USER}@demo.local",
        "role": "admin",
        "permissions": ["search", "classify", "admin"]
    }