#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.11.4
Ultra-minimal version with NO router imports
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
VERSION = "v4.11.4"

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
        }
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

# Health router endpoints
@app.get("/api/v1/health")
async def api_health():
    """API health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "service": "agricultural-core",
        "timestamp": datetime.now().isoformat()
    })

# Auth endpoints
@app.post("/api/v1/auth/login")
async def login():
    """Simple login endpoint"""
    return JSONResponse(content={
        "success": True,
        "token": "test-token",
        "user": {"id": 1, "name": "Test User"}
    })

@app.post("/api/v1/auth/logout")
async def logout():
    """Simple logout endpoint"""
    return JSONResponse(content={"success": True})

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

# Farmer dashboard endpoint
@app.get("/farmer/dashboard")
async def farmer_dashboard(request: Request):
    """Farmer dashboard - minimal version"""
    try:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="templates")
        
        # Get language from query params or default
        language = request.query_params.get("lang", "en")
        
        # Basic translations
        translations = {
            "en": {
                "dashboard_title": "Farmer Dashboard",
                "welcome": "Welcome",
                "weather": "Weather",
                "fields": "Fields",
                "tasks": "Tasks"
            },
            "bg": {
                "dashboard_title": "Фермерско табло",
                "welcome": "Добре дошли",
                "weather": "Време",
                "fields": "Полета",
                "tasks": "Задачи"
            },
            "sl": {
                "dashboard_title": "Kmetijska nadzorna plošča",
                "welcome": "Dobrodošli",
                "weather": "Vreme",
                "fields": "Polja",
                "tasks": "Naloge"
            }
        }
        
        t = translations.get(language, translations["en"])
        
        return templates.TemplateResponse("farmer/dashboard.html", {
            "request": request,
            "version": VERSION,
            "language": language,
            "t": t,
            "farmer": {"name": "Farmer", "id": 1}
        })
    except Exception as e:
        logger.error(f"Farmer dashboard error: {e}")
        return JSONResponse({"error": "Dashboard temporarily unavailable"}, status_code=500)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info(f"Ultra-minimal version with NO router imports")
    logger.info(f"AVA OLO Agricultural Core ready - {VERSION}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)