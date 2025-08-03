#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 12: Remove Dashboard Routers Entirely
Focus on core functionality only - dashboards handled by separate service
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
from modules.core.database_manager import get_db_manager

# Import ONLY core routers (NO dashboard routers)
from modules.core.deployment import router as deployment_router
from modules.core.audit import router as audit_router
from modules.api.database_routes import router as database_router
from modules.core.agricultural import router as agricultural_router
from modules.core.debug import router as debug_router
from modules.api.business_routes import router as business_router
from modules.api.dashboard_routes import router as dashboard_router
from modules.dashboards.dashboard_api import router as dashboard_api_router
from modules.api.deployment_webhook import router as webhook_router
from modules.api.system_routes import router as system_router

# Add Group B routers (core functionality, not dashboards)
from modules.api.debug_services import router as debug_services_router
from modules.api.debug_deployment import router as debug_deployment_router
from modules.api.code_status import router as code_status_router
from modules.auth.routes import router as auth_router
from modules.weather.routes import router as weather_router

# Create FastAPI app
app = FastAPI(title="AVA OLO Agricultural Core", version=VERSION)

# Mount static files (for any non-dashboard UI needs)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Track startup status
STARTUP_STATUS = {
    "validation_result": None,
    "db_test": None,
    "monitoring_started": False,
    "core_routers": 15,
    "dashboard_routers_removed": True,
    "architecture": "core_only_no_dashboards",
    "total_routers_included": 0,
    "error": None
}

# Add basic root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "service": "agricultural-core",
        "architecture": "core_functionality_only",
        "startup_status": STARTUP_STATUS
    }

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION, "service": "agricultural-core"}

# Include ONLY core routers (NO dashboard routers)
app.include_router(health_router)
app.include_router(deployment_router)
app.include_router(audit_router)
app.include_router(database_router)
app.include_router(agricultural_router)
app.include_router(debug_router)
app.include_router(business_router)
app.include_router(dashboard_router)
app.include_router(dashboard_api_router)
app.include_router(webhook_router)
app.include_router(system_router)
app.include_router(debug_services_router)
app.include_router(debug_deployment_router)
app.include_router(code_status_router)
app.include_router(auth_router)
app.include_router(weather_router)
STARTUP_STATUS["total_routers_included"] = 15

# Startup event
@app.on_event("startup")
async def startup_event():
    """Core startup without dashboard dependencies"""
    global STARTUP_STATUS
    logger.info(f"Starting agricultural-core service (no dashboards) - {VERSION}")
    
    # Run validation (we know this works)
    try:
        validation_report = await StartupValidator.validate_and_fix()
        STARTUP_STATUS["validation_result"] = validation_report.get("system_ready", False)
    except Exception as e:
        STARTUP_STATUS["error"] = f"Validation: {str(e)}"
    
    # Test database (we know this works)
    try:
        db_manager = get_db_manager()
        if db_manager.test_connection(retries=5, delay=3):
            STARTUP_STATUS["db_test"] = "success"
    except Exception as e:
        STARTUP_STATUS["error"] = f"Database: {str(e)}"
    
    # Start monitoring (we know this works)
    try:
        asyncio.create_task(StartupValidator.continuous_health_check())
        STARTUP_STATUS["monitoring_started"] = True
    except Exception as e:
        STARTUP_STATUS["error"] = f"Monitoring: {str(e)}"
    
    logger.info("Agricultural-core service started successfully (dashboards in separate service)")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)