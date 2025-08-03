#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 3: Test Startup Logic
Testing the actual startup validation logic
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

# Import startup modules
from modules.core.startup_validator import StartupValidator
from modules.core.api_key_manager import APIKeyManager

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add ONLY health router
app.include_router(health_router)

# Track startup status
STARTUP_STATUS = {
    "validation_attempted": False,
    "validation_result": None,
    "api_key_info": None,
    "error": None
}

# Add basic root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "binary_search": "step3_test_startup_logic",
        "startup_status": STARTUP_STATUS
    }

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Test the actual startup logic
@app.on_event("startup")
async def startup_event():
    """Test the startup validation logic"""
    global STARTUP_STATUS
    logger.info(f"Starting binary search step 3 startup test - {VERSION}")
    
    try:
        # Test StartupValidator
        logger.info("Testing StartupValidator.validate_and_fix()...")
        STARTUP_STATUS["validation_attempted"] = True
        validation_report = await StartupValidator.validate_and_fix()
        STARTUP_STATUS["validation_result"] = validation_report
        logger.info(f"Validation result: {validation_report}")
    except Exception as e:
        logger.error(f"StartupValidator failed: {e}")
        STARTUP_STATUS["error"] = f"StartupValidator: {str(e)}"
    
    try:
        # Test APIKeyManager
        logger.info("Testing APIKeyManager.get_diagnostic_info()...")
        api_key_info = APIKeyManager.get_diagnostic_info()
        STARTUP_STATUS["api_key_info"] = api_key_info
        logger.info(f"API Key info: {api_key_info}")
    except Exception as e:
        logger.error(f"APIKeyManager failed: {e}")
        STARTUP_STATUS["error"] = f"APIKeyManager: {str(e)}"
    
    # Do NOT start continuous health check - that might cause issues
    # asyncio.create_task(StartupValidator.continuous_health_check())
    
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)