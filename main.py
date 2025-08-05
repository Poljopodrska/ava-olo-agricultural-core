#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.11.1
Gradual restoration - essential routers only
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.11.1"

# Import config with fallback
try:
    from modules.core.config import VERSION as CONFIG_VERSION
    VERSION = CONFIG_VERSION
except ImportError:
    pass

# Import routers safely
routers_to_include = []

# Health router - use simple version
try:
    from modules.api.health_routes_simple import router as health_router
    routers_to_include.append(("health", health_router))
except ImportError:
    logger.warning("Failed to import simple health router")

# Auth router - use minimal version
try:
    from modules.auth.routes_minimal import router as auth_router
    routers_to_include.append(("auth", auth_router))
except ImportError:
    logger.warning("Failed to import minimal auth router")

# Farmer dashboard router
try:
    from modules.api.farmer_dashboard_routes import router as farmer_dashboard_router
    routers_to_include.append(("farmer_dashboard", farmer_dashboard_router))
except ImportError as e:
    logger.warning(f"Failed to import farmer dashboard router: {e}")

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

# Session middleware
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
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("Static files mounted")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "operational",
        "features": {
            "language_detection": True,
            "field_management": False,
            "task_management": False,
            "chat_integration": False,
            "weather_monitoring": False
        },
        "routers": [name for name, _ in routers_to_include]
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    })

# Landing page
@app.get("/landing")
async def landing_page(request: Request):
    """Landing page"""
    try:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="templates")
        return templates.TemplateResponse("landing.html", {
            "request": request,
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Landing page error: {e}")
        return RedirectResponse(url="/farmer/dashboard")

# Include all successfully imported routers
for router_name, router in routers_to_include:
    try:
        app.include_router(router)
        logger.info(f"Included {router_name} router")
    except Exception as e:
        logger.error(f"Failed to include {router_name} router: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info(f"Gradual restoration - essential routers only")
    logger.info(f"Included routers: {[name for name, _ in routers_to_include]}")
    logger.info(f"AVA OLO Agricultural Core ready - {VERSION}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)