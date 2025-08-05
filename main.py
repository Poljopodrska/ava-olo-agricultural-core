#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.11.6
Add session middleware and static files back
"""
import os
import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.11.6"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION
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

# API health endpoint
@app.get("/api/v1/health")
async def api_health():
    """API health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "service": "agricultural-core",
        "timestamp": datetime.now().isoformat()
    })

# Farmer dashboard endpoint
@app.get("/farmer/dashboard")
async def farmer_dashboard(request: Request):
    """Farmer dashboard"""
    return JSONResponse(content={
        "message": "Farmer Dashboard",
        "version": VERSION,
        "language": request.query_params.get("lang", "en")
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)