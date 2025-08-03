#!/usr/bin/env python3
"""
Basic authentication middleware for protecting the entire site
"""
import secrets
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse
import base64

# Security
security = HTTPBasic()

# Hardcoded users for basic auth
BASIC_AUTH_USERS = {
    "Peter": "Semillon",
    "Tine": "Vitovska"
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
        # ALWAYS print to verify middleware is being called
        path = request.url.path
        print(f"[AUTH MIDDLEWARE] Processing request to: {path}")
        
        # Check if path is public
        is_public = False
        for public_path in PUBLIC_PATHS:
            if path.startswith(public_path):
                is_public = True
                print(f"[AUTH MIDDLEWARE] Path {path} matches public path {public_path} - ALLOWING")
                break
        
        if is_public:
            response = await call_next(request)
            return response
        
        # Path is protected - require authentication
        print(f"[AUTH MIDDLEWARE] Path {path} is PROTECTED - checking authentication")
        auth_header = request.headers.get("Authorization")
        print(f"[AUTH MIDDLEWARE] Authorization header: {auth_header}")
        
        if not auth_header or not auth_header.startswith("Basic "):
            print(f"[AUTH MIDDLEWARE] NO VALID AUTH - BLOCKING REQUEST")
            return PlainTextResponse(
                content="Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="AVA OLO Protected Area"'}
            )
        
        try:
            # Decode basic auth
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded.split(":", 1)
            print(f"[AUTH MIDDLEWARE] Checking credentials for user: {username}")
            
            # Verify credentials
            credentials = HTTPBasicCredentials(username=username, password=password)
            if not verify_credentials(credentials):
                print(f"[AUTH MIDDLEWARE] INVALID CREDENTIALS for {username} - BLOCKING")
                return PlainTextResponse(
                    content="Invalid credentials",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="AVA OLO Protected Area"'}
                )
            
            # Success
            print(f"[AUTH MIDDLEWARE] VALID CREDENTIALS for {username} - ALLOWING")
            request.state.basic_auth_user = username
            response = await call_next(request)
            return response
            
        except Exception as e:
            print(f"[AUTH MIDDLEWARE] ERROR processing auth: {e} - BLOCKING")
            return PlainTextResponse(
                content="Authentication error",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="AVA OLO Protected Area"'}
            )