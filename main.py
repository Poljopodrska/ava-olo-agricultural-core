#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.9.1
Back to working version - minimal with health and auth
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.9.1"
BUILD_ID = "minimal-working"

# Create simple health router
health_router = APIRouter(prefix="/api/v1/health", tags=["health"])

@health_router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "version": VERSION,
        "build_id": BUILD_ID,
        "timestamp": datetime.now().isoformat()
    })

# Create simple auth router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/signin")
async def signin_page():
    """Sign in endpoint"""
    return JSONResponse({
        "message": "Sign in page",
        "version": VERSION
    })

@auth_router.get("/register")
async def register_page():
    """Register endpoint"""
    return JSONResponse({
        "message": "Register page",
        "version": VERSION
    })

@auth_router.post("/signin")
async def signin_submit(request: Request):
    """Process sign-in"""
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

@auth_router.post("/register")
async def register_submit(request: Request):
    """Process registration"""
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

@auth_router.get("/logout")
async def logout():
    """Log out user"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="farmer_id")
    response.delete_cookie(key="farmer_name")
    return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info(f"Starting {VERSION} lifespan context")
    yield
    logger.info(f"Shutting down {VERSION}")

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key-here"),
    session_cookie="ava_session",
    max_age=7200
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("Static files mounted")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "operational",
        "routers": ["health", "auth", "static"]
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION
    })

# Include routers
app.include_router(health_router)
app.include_router(auth_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info("Minimal working version")
    logger.info("Ready to serve")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)