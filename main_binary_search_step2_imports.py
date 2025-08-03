#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 2: Test Problematic Imports
Testing startup validator and API key manager imports
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

# TEST PROBLEMATIC IMPORTS FROM STARTUP
try:
    from modules.core.startup_validator import StartupValidator
    STARTUP_VALIDATOR_AVAILABLE = True
except Exception as e:
    STARTUP_VALIDATOR_AVAILABLE = False
    logger.error(f"Failed to import StartupValidator: {e}")

try:
    from modules.core.api_key_manager import APIKeyManager
    API_KEY_MANAGER_AVAILABLE = True
except Exception as e:
    API_KEY_MANAGER_AVAILABLE = False
    logger.error(f"Failed to import APIKeyManager: {e}")

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add ONLY health router
app.include_router(health_router)

# Add basic root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "binary_search": "step2_test_imports",
        "startup_validator": STARTUP_VALIDATOR_AVAILABLE,
        "api_key_manager": API_KEY_MANAGER_AVAILABLE
    }

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Minimal startup
@app.on_event("startup")
async def startup_event():
    """Minimal startup"""
    logger.info(f"Starting binary search step 2 imports test - {VERSION}")
    logger.info(f"StartupValidator available: {STARTUP_VALIDATOR_AVAILABLE}")
    logger.info(f"APIKeyManager available: {API_KEY_MANAGER_AVAILABLE}")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)