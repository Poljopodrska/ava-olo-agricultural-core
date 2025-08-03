#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 2: Add Core Infrastructure
Adding database, middleware, and core routers WITHOUT complex startup
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

# Add core infrastructure
from modules.core.database_manager import get_db_manager
from modules.core.version_badge_middleware import VersionBadgeMiddleware

# Add ONLY essential API routers (no complex ones)
from modules.api.system_routes import router as system_router
from modules.api.deployment_routes import router as deployment_router

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add middleware
app.add_middleware(VersionBadgeMiddleware)

# Add routers
app.include_router(health_router)
app.include_router(system_router)
app.include_router(deployment_router)

# Add basic root endpoint
@app.get("/")
async def root():
    return {"status": "running", "version": VERSION, "binary_search": "step2_smart_core"}

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# CRITICAL: Simple startup WITHOUT the complex validation/migration logic
@app.on_event("startup")
async def startup_event():
    """SIMPLE startup - no complex initialization"""
    logger.info(f"Starting binary search step 2 (smart) - {VERSION}")
    
    # Just test if we can create db manager instance
    try:
        db = get_db_manager()
        logger.info("Database manager created successfully")
    except Exception as e:
        logger.error(f"Database manager creation failed: {e}")
    
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)