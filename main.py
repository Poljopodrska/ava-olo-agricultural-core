#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - HOTFIX v4.7.2
Temporarily disables new routers to fix deployment issue
"""
import asyncio
import os
import json
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Core imports
from modules.core.config import config, constitutional_deployment_completion
from modules.core.translations import TranslationDict
from modules.core.database_manager import get_db_manager
from modules.core.startup_validator import StartupValidator
from modules.core.deploy_notifier import DeploymentNotifier

# Route imports
from modules.api.health_routes import router as health_router
from modules.api.database_routes import router as database_router
from modules.api.cascade_migration import router as cascade_router
from modules.api.farmer_query import router as farmer_query_router
from modules.api.simple_cleanup import router as simple_cleanup_router
from modules.api.system_routes import router as system_router
from modules.api.debug_services import router as debug_router
from modules.api.deployment_routes import router as deployment_router
from modules.api.emergency_routes import router as emergency_router
from modules.api.dashboard_routes import router as dashboard_routes
from modules.api.dashboard_auth import router as dashboard_auth_router
from modules.api.dashboard_chat_routes import router as dashboard_chat_router
from modules.api.chat_routes import router as chat_router
from modules.api.chat_history_routes import router as chat_history_router
from modules.api.deployment_webhook import router as deploy_webhook_router
from modules.auth.routes import router as auth_router
from modules.api.weather_routes import router as weather_router
from modules.api.farmer_dashboard_routes import router as farmer_dashboard_router
from modules.api.cava_registration_routes import router as cava_router
from modules.whatsapp.routes import router as whatsapp_router
# TEMPORARILY DISABLED TO FIX DEPLOYMENT
# from modules.api.task_management_routes import router as task_management_router
# from modules.api.debug_edi_kante import router as debug_edi_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.7.3"

# Initialize startup status
STARTUP_STATUS = {
    "version": VERSION,
    "started": False,
    "db_test": None,
    "validation_result": None,
    "monitoring_started": False,
    "error": None,
    "total_routers_included": 20  # Reduced from 22
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info(f"Starting {VERSION} lifespan context")
    yield
    logger.info(f"Shutting down {VERSION}")

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Session middleware for auth
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key-here"),
    session_cookie="ava_session",
    max_age=7200
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - production version"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/health"
    })

# Landing page
@app.get("/landing")
async def landing(request: Request):
    """Redirect to farmer dashboard"""
    return RedirectResponse(url="/farmer/dashboard", status_code=307)

# Include all routers
app.include_router(health_router, tags=["health"])
app.include_router(database_router)
app.include_router(cascade_router)
app.include_router(farmer_query_router)
app.include_router(simple_cleanup_router)
app.include_router(system_router)
app.include_router(debug_router)
app.include_router(deployment_router)
app.include_router(emergency_router)
app.include_router(dashboard_routes)
app.include_router(dashboard_auth_router)
app.include_router(dashboard_chat_router)
app.include_router(deploy_webhook_router)
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(farmer_dashboard_router)
app.include_router(cava_router)
app.include_router(chat_router)
app.include_router(chat_history_router)
app.include_router(whatsapp_router)
# TEMPORARILY DISABLED
# app.include_router(task_management_router)
# app.include_router(debug_edi_router)
STARTUP_STATUS["total_routers_included"] = 20

# Startup event
@app.on_event("startup")
async def startup_event():
    """Core startup for production with 20 routers and basic auth"""
    global STARTUP_STATUS
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} with 20 routers and basic auth protection")
    
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
    
    logger.info(f"AVA OLO Agricultural Core ready - {VERSION} Production with Basic Auth")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)