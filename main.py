#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.8.8
Phase 3: Add minimal auth router
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

# Minimal module imports
from modules.auth.routes_minimal import router as auth_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.8.8"
BUILD_ID = "phase3"

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

@health_router.get("/simple")
async def simple_health():
    """Very simple health check"""
    return JSONResponse({
        "status": "ok",
        "version": VERSION
    })

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

# Session middleware for auth
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

# Mount static files with error handling
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("Static files mounted successfully")
    else:
        logger.warning("Static directory not found")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - phase 3"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "phase3",
        "phase": "Auth router added",
        "routers": ["health", "auth", "static"]
    })

# Basic health endpoint
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
    """Phase 3 startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Phase 3")
    logger.info("Health router active")
    logger.info("Auth router added")
    logger.info("Phase 3 ready")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)