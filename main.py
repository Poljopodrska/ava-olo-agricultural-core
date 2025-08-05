#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.12.0
Full working version with minimal routers
"""
import os
import sys
import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.12.0"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
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

# Import routers
routers_to_include = []

# Health router
try:
    from modules.api.health_routes_minimal import router as health_router
    routers_to_include.append(("health", health_router))
except Exception as e:
    logger.error(f"Failed to import health router: {e}")

# Auth router
try:
    from modules.auth.routes_simple import router as auth_router
    routers_to_include.append(("auth", auth_router))
except Exception as e:
    logger.error(f"Failed to import auth router: {e}")

# Weather router
try:
    from modules.api.weather_routes_minimal import router as weather_router
    routers_to_include.append(("weather", weather_router))
except Exception as e:
    logger.error(f"Failed to import weather router: {e}")

# Chat router
try:
    from modules.chat.routes_minimal import router as chat_router
    routers_to_include.append(("chat", chat_router))
except Exception as e:
    logger.error(f"Failed to import chat router: {e}")

# Task router
try:
    from modules.api.task_routes_minimal import router as task_router
    routers_to_include.append(("tasks", task_router))
except Exception as e:
    logger.error(f"Failed to import task router: {e}")

# Field router
try:
    from modules.api.field_routes_minimal import router as field_router
    routers_to_include.append(("fields", field_router))
except Exception as e:
    logger.error(f"Failed to import field router: {e}")

# Farmer dashboard router
try:
    from modules.api.farmer_dashboard_routes_minimal import router as dashboard_router
    routers_to_include.append(("dashboard", dashboard_router))
except Exception as e:
    logger.error(f"Failed to import dashboard router: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "language_detection": True,
            "field_management": True,
            "task_management": True,
            "chat_integration": True,
            "weather_monitoring": True,
            "google_maps_integration": True,
            "multi_language": ["en", "bg", "sl"]
        },
        "routers_loaded": [name for name, _ in routers_to_include]
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
    logger.info(f"All features restored with minimal routers")
    logger.info(f"Included routers: {[name for name, _ in routers_to_include]}")
    logger.info(f"AVA OLO Agricultural Core ready - {VERSION}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)