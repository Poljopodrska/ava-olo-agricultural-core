#!/usr/bin/env python3
"""
AVA OLO Agricultural Core v4.0.1
Fixed production release with 19 working routers
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

# Configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.api.health_routes import router as health_router

# Startup modules
from modules.core.startup_validator import StartupValidator
from modules.core.api_key_manager import APIKeyManager
from modules.core.database_manager import get_db_manager

# Core routers
from modules.api.deployment_routes import router as deployment_router, audit_router
from modules.api.database_routes import router as database_router, agricultural_router, debug_router
from modules.api.business_routes import router as business_router
from modules.api.dashboard_routes import router as dashboard_router, api_router as dashboard_api_router
from modules.api.deployment_webhook import router as webhook_router
from modules.api.system_routes import router as system_router
from modules.api.debug_services import router as debug_services_router
from modules.api.debug_deployment import router as debug_deployment_router
from modules.api.code_status import router as code_status_router
from modules.auth.routes import router as auth_router
from modules.weather.routes import router as weather_router

# CAVA routers
from modules.cava.routes import router as cava_router

# Chat routers
from modules.api.chat_routes import router as chat_router
from modules.api.chat_history_routes import router as chat_history_router

# WhatsApp integration
from modules.whatsapp.webhook_handler import router as whatsapp_router

# Create FastAPI app
app = FastAPI(title="AVA OLO Agricultural Core", version=VERSION)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Track startup status
STARTUP_STATUS = {
    "validation_result": None,
    "db_test": None,
    "monitoring_started": False,
    "total_routers_included": 0,
    "phase": "production",
    "error": None
}

# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "startup_status": STARTUP_STATUS
    }

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Include all routers
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
app.include_router(cava_router)
app.include_router(chat_router)
app.include_router(chat_history_router)
app.include_router(whatsapp_router)
STARTUP_STATUS["total_routers_included"] = 19

# Startup event
@app.on_event("startup")
async def startup_event():
    """Core startup for production with 19 routers"""
    global STARTUP_STATUS
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} with 19 routers")
    
    # Run validation
    try:
        validation_report = await StartupValidator.validate_and_fix()
        STARTUP_STATUS["validation_result"] = validation_report.get("system_ready", False)
    except Exception as e:
        STARTUP_STATUS["error"] = f"Validation: {str(e)}"
    
    # Test database
    try:
        db_manager = get_db_manager()
        if db_manager.test_connection(retries=5, delay=3):
            STARTUP_STATUS["db_test"] = "success"
    except Exception as e:
        STARTUP_STATUS["error"] = f"Database: {str(e)}"
    
    # Start monitoring
    try:
        asyncio.create_task(StartupValidator.continuous_health_check())
        STARTUP_STATUS["monitoring_started"] = True
    except Exception as e:
        STARTUP_STATUS["error"] = f"Monitoring: {str(e)}"
    
    logger.info("AVA OLO Agricultural Core ready - v4.0.1 Production")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)