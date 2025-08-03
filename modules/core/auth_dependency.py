#!/usr/bin/env python3
"""
Authentication dependency for protecting routes
"""
import secrets
from typing import Optional
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Security
security = HTTPBasic()

# Hardcoded users for basic auth
BASIC_AUTH_USERS = {
    "Peter": "Semillon",
    "Tine": "Vitovska"
}

def verify_credentials(credentials: HTTPBasicCredentials) -> bool:
    """Verify username and password"""
    correct_password = BASIC_AUTH_USERS.get(credentials.username)
    if not correct_password:
        return False
    
    # Compare passwords securely
    return secrets.compare_digest(credentials.password, correct_password)

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Dependency to require authentication"""
    if not verify_credentials(credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def optional_auth(credentials: Optional[HTTPBasicCredentials] = Depends(security)) -> Optional[str]:
    """Optional authentication - returns username if authenticated, None otherwise"""
    if credentials:
        if verify_credentials(credentials):
            return credentials.username
    return None