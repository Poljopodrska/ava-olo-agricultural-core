#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.8.4
Bare minimum - no module imports
"""
import os
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
VERSION = "v4.8.4"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - bare minimum"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "bare-minimum"
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION
    })

# Simple API health endpoint
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
    """Bare minimum startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Bare minimum")
    logger.info("No module imports - testing container startup")
    logger.info("Container started successfully!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)