#!/usr/bin/env python3
"""
Basic authentication middleware for protecting the entire site
"""
import secrets
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import base64

# Security
security = HTTPBasic()

# Hardcoded users for basic auth
BASIC_AUTH_USERS = {
    "Peter": "Semillon",
    "Tine": "Viovska"
}

# Public paths that don't require auth
PUBLIC_PATHS = [
    "/",  # Will be landing page
    "/auth/signin",
    "/auth/register",
    "/auth/logout",
    "/api/v1/whatsapp/webhook",  # WhatsApp webhook needs to be public
    "/health",  # Health check for load balancer
    "/static",  # Static files
    "/favicon.ico",
    "/openapi.json",  # API docs
    "/docs",  # Swagger UI
    "/redoc"  # ReDoc
]

def verify_credentials(credentials: HTTPBasicCredentials) -> bool:
    """Verify username and password"""
    correct_password = BASIC_AUTH_USERS.get(credentials.username)
    if not correct_password:
        return False
    
    # Compare passwords securely
    return secrets.compare_digest(credentials.password, correct_password)

class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to require basic auth for all protected routes"""
    
    async def dispatch(self, request: Request, call_next):
        # Check if path is public
        path = request.url.path
        
        # Allow public paths
        for public_path in PUBLIC_PATHS:
            if path.startswith(public_path):
                response = await call_next(request)
                return response
        
        # Check for basic auth header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Basic "):
            # Return 401 with WWW-Authenticate header
            return Response(
                content="Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="AVA OLO Protected Area"'}
            )
        
        try:
            # Decode basic auth
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded.split(":", 1)
            
            # Verify credentials
            credentials = HTTPBasicCredentials(username=username, password=password)
            if not verify_credentials(credentials):
                return Response(
                    content="Invalid credentials",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="AVA OLO Protected Area"'}
                )
            
            # Add username to request state for logging
            request.state.basic_auth_user = username
            
        except Exception:
            return Response(
                content="Invalid authentication format",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="AVA OLO Protected Area"'}
            )
        
        # Continue with request
        response = await call_next(request)
        return response