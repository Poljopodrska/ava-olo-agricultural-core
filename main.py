#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.8.5
Debug version - print environment info
"""
import os
import sys
import logging

print("=== CONTAINER STARTUP DEBUG ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print(f"Static dir exists: {os.path.exists('static')}")
print("=== END DEBUG ===")

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
VERSION = "v4.8.5"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - debug"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "debug",
        "python": sys.version,
        "cwd": os.getcwd()
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
    """Debug startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Debug")
    logger.info(f"Python: {sys.version}")
    logger.info(f"CWD: {os.getcwd()}")
    logger.info("Container started!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)