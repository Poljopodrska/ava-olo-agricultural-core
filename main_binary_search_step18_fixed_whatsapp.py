#!/usr/bin/env python3
"""
Binary Search Debug Version - Step 18: Fixed WhatsApp Webhook
Fixed WhatsApp webhook handler with safer Twilio imports
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

# Import working routers from v3.9.30 (21 routers)
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
from modules.cava.routes import router as cava_router
from modules.fields.routes import router as fields_router
from modules.chat.simple_registration import router as simple_registration_router
from modules.api.chat_routes import router as cava_chat_router
from modules.api.chat_history_routes import router as chat_history_router

# ADD Fixed WhatsApp webhook router - CRITICAL for farmer communication
try:
    from modules.whatsapp.webhook_handler import router as whatsapp_webhook_router
    WHATSAPP_SUCCESS = True
    WHATSAPP_ERROR = None
except Exception as e:
    logger.error(f"Failed to import WhatsApp webhook router: {e}")
    WHATSAPP_SUCCESS = False
    WHATSAPP_ERROR = str(e)

# Create FastAPI app
app = FastAPI(title="AVA OLO Agricultural Core", version=VERSION)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Track startup status
STARTUP_STATUS = {
    "validation_result": None,
    "db_test": None,
    "monitoring_started": False,
    "base_routers": 21,
    "whatsapp_success": WHATSAPP_SUCCESS,
    "whatsapp_error": WHATSAPP_ERROR,
    "total_routers_included": 0,
    "phase": "adding_fixed_whatsapp_webhook",
    "functionality": "farmer_communication_via_whatsapp",
    "critical_feature": "whatsapp_integration",
    "fix_applied": "safer_twilio_imports",
    "error": None
}

# Add basic root endpoint
@app.get("/")
async def root():
    return {
        "status": "running", 
        "version": VERSION, 
        "binary_search": "step18_fixed_whatsapp",
        "startup_status": STARTUP_STATUS
    }

# Add health endpoint for load balancer
@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

# Include all working routers from v3.9.30
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
app.include_router(fields_router)
app.include_router(simple_registration_router)
app.include_router(cava_chat_router)
app.include_router(chat_history_router)
STARTUP_STATUS["total_routers_included"] = 21

# Include WhatsApp webhook router if import succeeded
if WHATSAPP_SUCCESS:
    try:
        app.include_router(whatsapp_webhook_router)
        STARTUP_STATUS["total_routers_included"] = 22
        logger.info("Successfully included WhatsApp webhook router - farmer communication enabled")
    except Exception as e:
        STARTUP_STATUS["error"] = f"WhatsApp router inclusion: {str(e)}"
        logger.error(f"Failed to include WhatsApp router: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Core startup with fixed WhatsApp webhook functionality"""
    global STARTUP_STATUS
    logger.info(f"Starting with 21 base + 1 fixed WhatsApp webhook router - {VERSION}")
    
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
    
    logger.info("Core farmer portal with fixed WhatsApp integration ready")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)