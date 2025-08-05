#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.9.2
Ultra-minimal - bare FastAPI only
"""
import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.9.2"
BUILD_ID = "ultra-minimal"

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
    """Root endpoint"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    })

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info("Ultra-minimal version - FastAPI only")
    logger.info("Ready to serve")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)