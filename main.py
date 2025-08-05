#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.7.8
Minimal version for debugging deployment
"""
import os
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.7.11-emergency"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - minimal version"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "minimal",
        "debug": "Container startup test"
    })

# Health endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "service": "agricultural-core"
    })

# Startup event
@app.on_event("startup")
async def startup_event():
    """Minimal startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Minimal version")
    logger.info("Container started successfully!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)