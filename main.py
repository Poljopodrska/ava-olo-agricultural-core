#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.8.6
Phase 1: Add static files mount with proper error handling
"""
import os
import sys
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.8.6"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
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
    """Root endpoint - phase 1"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "phase1",
        "phase": "Static files mounted"
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION
    })

# API health endpoint for compatibility
@app.get("/api/v1/health/")
async def api_health():
    """API health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "service": "agricultural-core"
    })

# Startup event
@app.on_event("startup")
async def startup_event():
    """Phase 1 startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Phase 1")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Static directory exists: {os.path.exists('static')}")
    logger.info("Phase 1: Static files mount complete")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)