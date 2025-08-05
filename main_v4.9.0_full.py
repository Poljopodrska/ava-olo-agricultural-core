#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.9.0
Full restoration with all routers
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates

# Core imports with error handling
try:
    from modules.core.config import constitutional_deployment_completion, VERSION as CONFIG_VERSION
except ImportError:
    CONFIG_VERSION = "v4.9.0"
    def constitutional_deployment_completion():
        print(f"Constitutional deployment complete: {CONFIG_VERSION}")

try:
    from modules.core.database_manager import get_db_manager
except ImportError:
    def get_db_manager():
        return None

# Import routers with fallbacks
try:
    from modules.api.health_routes import router as health_router
except ImportError:
    from modules.api.health_routes_simple import router as health_router

try:
    from modules.auth.routes import router as auth_router
except ImportError:
    from modules.auth.routes_minimal import router as auth_router

try:
    from modules.api.dashboard_routes import router as dashboard_router
except ImportError:
    dashboard_router = None

try:
    from modules.api.farmer_dashboard_routes import router as farmer_dashboard_router
except ImportError:
    farmer_dashboard_router = None

try:
    from modules.api.weather_routes import router as weather_router
except ImportError:
    weather_router = None

try:
    from modules.api.chat_routes import router as chat_router
except ImportError:
    chat_router = None

try:
    from modules.api.farmer_management_routes import router as farmer_management_router
except ImportError:
    farmer_management_router = None

try:
    from modules.api.twilio_routes import router as twilio_router
except ImportError:
    twilio_router = None

try:
    from modules.api.task_management_routes import router as task_management_router
except ImportError:
    task_management_router = None

try:
    from modules.api.debug_edi_kante import router as debug_edi_router
except ImportError:
    debug_edi_router = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = CONFIG_VERSION

# Templates
templates = Jinja2Templates(directory="templates")

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
try:
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
            "field_management": True,
            "task_management": True,
            "chat_integration": True,
            "weather_monitoring": True
        }
    })

# Landing page
@app.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page"""
    try:
        return templates.TemplateResponse("landing.html", {
            "request": request,
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Landing page error: {e}")
        return RedirectResponse(url="/farmer/dashboard")

# Include all routers with error handling
included_routers = []

try:
    app.include_router(health_router, tags=["health"])
    included_routers.append("health")
except Exception as e:
    logger.error(f"Failed to include health router: {e}")

try:
    app.include_router(auth_router)
    included_routers.append("auth")
except Exception as e:
    logger.error(f"Failed to include auth router: {e}")

if dashboard_router:
    try:
        app.include_router(dashboard_router)
        included_routers.append("dashboard")
    except Exception as e:
        logger.error(f"Failed to include dashboard router: {e}")

if farmer_dashboard_router:
    try:
        app.include_router(farmer_dashboard_router)
        included_routers.append("farmer_dashboard")
    except Exception as e:
        logger.error(f"Failed to include farmer dashboard router: {e}")

if weather_router:
    try:
        app.include_router(weather_router)
        included_routers.append("weather")
    except Exception as e:
        logger.error(f"Failed to include weather router: {e}")

if chat_router:
    try:
        app.include_router(chat_router)
        included_routers.append("chat")
    except Exception as e:
        logger.error(f"Failed to include chat router: {e}")

if task_management_router:
    try:
        app.include_router(task_management_router)
        included_routers.append("task_management")
    except Exception as e:
        logger.error(f"Failed to include task management router: {e}")

if farmer_management_router:
    try:
        app.include_router(farmer_management_router)
        included_routers.append("farmer_management")
    except Exception as e:
        logger.error(f"Failed to include farmer management router: {e}")

if twilio_router:
    try:
        app.include_router(twilio_router)
        included_routers.append("twilio")
    except Exception as e:
        logger.error(f"Failed to include twilio router: {e}")

if debug_edi_router:
    try:
        app.include_router(debug_edi_router)
        included_routers.append("debug_edi")
    except Exception as e:
        logger.error(f"Failed to include debug edi router: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info(f"Included routers: {included_routers}")
    
    # Test database
    try:
        db_manager = get_db_manager()
        if db_manager and hasattr(db_manager, 'test_connection'):
            if db_manager.test_connection(retries=2, delay=1):
                logger.info("Database connection successful")
            else:
                logger.warning("Database connection failed but continuing")
        else:
            logger.info("Database manager not available")
    except Exception as e:
        logger.error(f"Database test error: {e}")
    
    logger.info(f"AVA OLO Agricultural Core ready - {VERSION}")
    
    try:
        constitutional_deployment_completion()
    except Exception as e:
        logger.error(f"Constitutional completion error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)