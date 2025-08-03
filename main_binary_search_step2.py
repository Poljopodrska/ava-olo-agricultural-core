#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 2: First Half of Modules
Adding database manager + first set of API routers + dashboard modules + auth
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
from modules.core.database_manager import get_db_manager
from modules.core.version_badge_middleware import VersionBadgeMiddleware
from modules.api.health_routes import router as health_router

# Import API routers - FIRST HALF
from modules.api.deployment_routes import router as deployment_router, audit_router
from modules.api.database_routes import router as database_router, agricultural_router, debug_router
from modules.api.business_routes import router as business_router
from modules.api.dashboard_routes import router as dashboard_router, api_router as dashboard_api_router
from modules.api.deployment_webhook import router as webhook_router
from modules.api.system_routes import router as system_router
from modules.api.debug_services import router as debug_services_router
from modules.api.debug_deployment import router as debug_deployment_router
from modules.api.code_status import router as code_status_router

# Import dashboard modules
from modules.dashboards.agronomic import router as agronomic_router
from modules.dashboards.business import router as business_dashboard_router
from modules.dashboards.health import router as health_dashboard_router
from modules.dashboards.database import router as database_dashboard_router
from modules.dashboards.deployment import router as deployment_dashboard_router, api_router as deployment_api_router
from modules.dashboards.feature_status import router as feature_status_router

# Import auth module
from modules.auth.routes import router as auth_router

# Import weather module
from modules.weather.routes import router as weather_router

# Create FastAPI app
app = FastAPI(title="AVA OLO Monitoring Dashboards", version=VERSION)

# Add middleware
app.add_middleware(VersionBadgeMiddleware)

# Add routers
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
app.include_router(agronomic_router)
app.include_router(business_dashboard_router)
app.include_router(health_dashboard_router)
app.include_router(database_dashboard_router)
app.include_router(deployment_dashboard_router)
app.include_router(deployment_api_router)
app.include_router(feature_status_router)
app.include_router(auth_router)
app.include_router(weather_router)

# Add basic root endpoint
@app.get("/")
async def root():
    return {"status": "running", "version": VERSION, "binary_search": "step2_first_half"}

# Minimal startup
@app.on_event("startup")
async def startup_event():
    """Minimal startup"""
    logger.info(f"Starting binary search step 2 - {VERSION}")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)