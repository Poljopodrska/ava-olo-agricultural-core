#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 4: Add Database Operations
Testing database manager and migrations
"""
import uvicorn
import sys
import os
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates

# Set up logger
logger = logging.getLogger(__name__)

# Import configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.api.health_routes import router as health_router

# Import startup modules (we know these work)
from modules.core.startup_validator import StartupValidator
from modules.core.api_key_manager import APIKeyManager

# ADD DATABASE MANAGER
from modules.core.database_manager import get_db_manager

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add ONLY health router
app.include_router(health_router)

# Track startup status
STARTUP_STATUS = {
    "validation_result": None,
    "db_test": None,
    "migration_test": None,
    "error": None
}

# Add basic root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "binary_search": "step4_database_ops",
        "startup_status": STARTUP_STATUS
    }

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Test database operations
@app.on_event("startup")
async def startup_event():
    """Test database operations"""
    global STARTUP_STATUS
    logger.info(f"Starting binary search step 4 database test - {VERSION}")
    
    # Run validation (we know this works)
    try:
        validation_report = await StartupValidator.validate_and_fix()
        STARTUP_STATUS["validation_result"] = validation_report.get("system_ready", False)
    except Exception as e:
        STARTUP_STATUS["error"] = f"Validation: {str(e)}"
    
    # Test database connection with retry logic (from original)
    try:
        logger.info("Testing database connection...")
        db_manager = get_db_manager()
        if db_manager.test_connection(retries=5, delay=3):
            STARTUP_STATUS["db_test"] = "success"
            logger.info("Database connection established")
        else:
            STARTUP_STATUS["db_test"] = "failed"
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        STARTUP_STATUS["error"] = f"Database: {str(e)}"
    
    # Test migrations
    try:
        logger.info("Testing database migrations...")
        from modules.core.migration_runner import run_startup_migrations
        migration_result = run_startup_migrations()
        STARTUP_STATUS["migration_test"] = migration_result
        logger.info(f"Migration result: {migration_result}")
    except Exception as e:
        logger.error(f"Migration test failed: {e}")
        STARTUP_STATUS["error"] = f"Migration: {str(e)}"
    
    # Do NOT start continuous health check yet
    
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)