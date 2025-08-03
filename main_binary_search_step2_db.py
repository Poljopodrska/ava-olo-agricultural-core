#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 2: Add Database Manager ONLY
Testing if database connection is causing crashes
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

# Import configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.api.health_routes import router as health_router

# ADD ONLY DATABASE MANAGER
from modules.core.database_manager import get_db_manager

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add ONLY health router
app.include_router(health_router)

# Add basic root endpoint
@app.get("/")
async def root():
    return {"status": "running", "version": VERSION, "binary_search": "step2_database_only"}

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Add database test endpoint
@app.get("/db-test")
async def db_test():
    try:
        db = get_db_manager()
        # Just try to get the connection, don't execute queries
        return {"status": "database manager loaded", "db_available": db is not None}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Minimal startup - NO database initialization
@app.on_event("startup")
async def startup_event():
    """Minimal startup - no database init"""
    logger.info(f"Starting binary search step 2 DB test - {VERSION}")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)