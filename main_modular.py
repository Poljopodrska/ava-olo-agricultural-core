#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - Modularized Main Application
Version: v3.3.0-ecs-ready
Refactored for AWS ECS deployment with modules under 100KB
"""
import uvicorn
import os
import sys
import traceback
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
from modules.core.config import (
    VERSION, BUILD_ID, CAVA_VERSION, 
    constitutional_deployment_completion, 
    emergency_log, config
)
from modules.core.deployment_manager import get_deployment_manager

# Import API routers
from modules.api.deployment_routes import router as deployment_router
from modules.api.cava_routes import router as cava_router
from modules.api.query_routes import router as query_router
from modules.api.web_routes import router as web_router

# Log startup
emergency_log(f"=== MODULAR DEPLOYMENT STARTUP {VERSION} ===")
emergency_log(f"Build ID: {BUILD_ID}")
emergency_log(f"CAVA Version: {CAVA_VERSION}")
emergency_log(f"Python version: {sys.version}")
emergency_log(f"Working directory: {os.getcwd()}")

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Core API",
    version=VERSION,
    description=f"AI-powered agricultural assistant for Eastern European farmers (CAVA: {CAVA_VERSION})"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    emergency_log("Static files mounted")

# Include routers
app.include_router(deployment_router)
app.include_router(cava_router)
app.include_router(query_router)
app.include_router(web_router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    emergency_log("FastAPI startup event triggered")
    
    # Generate deployment manifest
    try:
        deployment_manager = get_deployment_manager()
        manifest = deployment_manager.generate_deployment_manifest(VERSION)
        emergency_log(f"Deployment manifest generated: {manifest.get('service')}")
    except Exception as e:
        emergency_log(f"Warning: Could not generate manifest: {e}")
    
    # Constitutional deployment completion
    constitutional_deployment_completion()
    
    # Log available endpoints
    emergency_log("Available endpoints:")
    for route in app.routes:
        if hasattr(route, 'path'):
            emergency_log(f"  - {route.path}")

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "status": "ok",
        "version": VERSION,
        "cava_version": CAVA_VERSION,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Report deployment version
    constitutional_deployment_completion()
    
    # Get port from environment
    port = int(os.getenv("PORT", 8080))
    emergency_log(f"Starting uvicorn server on port: {port}")
    
    try:
        # Run the application
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info"
        )
    except Exception as e:
        emergency_log(f"❌ Uvicorn failed to start: {e}")
        traceback.print_exc()
        sys.exit(1)