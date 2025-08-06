#!/usr/bin/env python3
"""
Global authentication middleware that actually works
Forces authentication on ALL routes except explicitly public ones
"""
import secrets
from typing import Optional, Callable
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBasicCredentials
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import base64

# Hardcoded users for basic auth
BASIC_AUTH_USERS = {
    "Peter": "Semillon",
    "Tine": "Vitovska"
}

# Public paths that don't require auth
PUBLIC_PATHS = [
    "/",  # Landing page
    "/auth/signin",
    "/auth/register", 
    "/auth/logout",
    "/health",
    "/static",
    "/favicon.ico",
    "/debug/signin-test",  # Debug endpoint for signin troubleshooting
    "/debug/minimal-signin",  # Minimal signin test
    "/debug/auth-state",  # Debug auth state
    "/api/v1/debug/check-edi-kante",  # Edi Kante fields check endpoint
    "/api/v1/whatsapp/webhook",  # WhatsApp webhook needs to be public
    "/farmer/dashboard",  # Farmer dashboard - has its own auth via require_auth
    "/farmer/api",  # Farmer API endpoints - have their own auth
    "/diagnostic/ip-check",  # IP detection diagnostic - public for testing
]

class GlobalAuthMiddleware(BaseHTTPMiddleware):
    """Global authentication middleware that properly intercepts ALL requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process each request and enforce authentication"""
        
        # Get the path
        path = str(request.url.path)
        
        # Check if path is public
        is_public = False
        for public_path in PUBLIC_PATHS:
            if path == public_path or path.startswith(public_path + "/"):
                is_public = True
                break
        
        # If public, allow through
        if is_public:
            response = await call_next(request)
            return response
        
        # Otherwise, require authentication
        auth_header = request.headers.get("authorization")
        
        # If no auth header, return 401 with WWW-Authenticate to trigger browser prompt
        if not auth_header:
            return Response(
                content="Authentication required",
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Basic realm="AVA OLO Protected Area", charset="UTF-8"'
                }
            )
        
        # Check if it's Basic auth
        if not auth_header.lower().startswith("basic "):
            return Response(
                content="Invalid authentication method",
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Basic realm="AVA OLO Protected Area", charset="UTF-8"'
                }
            )
        
        # Decode credentials
        try:
            # Get the encoded part after "Basic "
            encoded = auth_header[6:]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return Response(
                content="Invalid authentication format",
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Basic realm="AVA OLO Protected Area", charset="UTF-8"'
                }
            )
        
        # Verify credentials
        correct_password = BASIC_AUTH_USERS.get(username)
        if not correct_password or not secrets.compare_digest(password, correct_password):
            return Response(
                content="Invalid username or password",
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Basic realm="AVA OLO Protected Area", charset="UTF-8"'
                }
            )
        
        # Authentication successful - add username to request state
        request.state.authenticated_user = username
        
        # Continue with the request
        response = await call_next(request)
        return response