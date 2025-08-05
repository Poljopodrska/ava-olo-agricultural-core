#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.8.0
Ultra minimal test version
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
VERSION = "v4.8.0-minimal-test"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - minimal test"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "minimal-test"
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION
    })

# Startup event
@app.on_event("startup")
async def startup_event():
    """Minimal startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Minimal Test")
    logger.info("Container started successfully!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)