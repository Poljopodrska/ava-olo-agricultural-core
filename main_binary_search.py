#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 1: Minimal Core Only
Testing with ONLY health endpoint
"""
import uvicorn
import sys
import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates

# Set up logger
logger = logging.getLogger(__name__)

# Import ONLY configuration and health routes
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.api.health_routes import router as health_router

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add ONLY health router
app.include_router(health_router)

# Add basic root endpoint
@app.get("/")
async def root():
    return {"status": "running", "version": VERSION, "binary_search": "step1_minimal"}

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Minimal startup
@app.on_event("startup")
async def startup_event():
    """Minimal startup"""
    logger.info(f"Starting minimal binary search version - {VERSION}")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)