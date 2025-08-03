#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 9: Test Half of Dashboard Routers
Testing only first 3 dashboard routers to narrow down the problem
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

# Import first batch of routers (10) - we know these work
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

# Import ONLY first 3 dashboard routers
try:
    from modules.dashboards.agronomic import router as agronomic_router
    from modules.dashboards.business import router as business_dashboard_router
    from modules.dashboards.health import router as health_dashboard_router
    DASHBOARD_HALF_SUCCESS = True
    DASHBOARD_HALF_ERROR = None
except Exception as e:
    logger.error(f"Failed to import first half of dashboard routers: {e}")
    DASHBOARD_HALF_SUCCESS = False
    DASHBOARD_HALF_ERROR = str(e)

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Track startup status
STARTUP_STATUS = {
    "validation_result": None,
    "db_test": None,
    "monitoring_started": False,
    "first_batch_routers": 10,
    "dashboard_half_success": DASHBOARD_HALF_SUCCESS,
    "dashboard_half_error": DASHBOARD_HALF_ERROR,
    "total_routers_included": 0,
    "test_group": "A_dashboards_first_half",
    "error": None
}

# Add basic root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "binary_search": "step9_dashboards_first_half",
        "startup_status": STARTUP_STATUS
    }

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Include first batch of routers (we know these work)
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
STARTUP_STATUS["total_routers_included"] = 11

# Include first half of dashboard routers if imports succeeded
if DASHBOARD_HALF_SUCCESS:
    try:
        app.include_router(agronomic_router)
        app.include_router(business_dashboard_router)
        app.include_router(health_dashboard_router)
        STARTUP_STATUS["total_routers_included"] = 14
    except Exception as e:
        STARTUP_STATUS["error"] = f"Dashboard half router inclusion: {str(e)}"

# Minimal startup event
@app.on_event("startup")
async def startup_event():
    """Minimal startup for router testing"""
    global STARTUP_STATUS
    logger.info(f"Starting binary search step 9 dashboard half test - {VERSION}")
    
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
    
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)