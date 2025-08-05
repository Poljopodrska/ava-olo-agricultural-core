#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.11.0
Full restoration with all routers and error handling
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.11.0"

# Import config with fallback
try:
    from modules.core.config import constitutional_deployment_completion, VERSION as CONFIG_VERSION
    VERSION = CONFIG_VERSION
except ImportError:
    def constitutional_deployment_completion():
        print(f"Constitutional deployment complete: {VERSION}")

# Import database manager with fallback
try:
    from modules.core.database_manager import get_db_manager
except ImportError:
    def get_db_manager():
        return None

# Import routers with error handling
routers_to_include = []

try:
    from modules.api.health_routes import router as health_router
    routers_to_include.append(("health", health_router))
except ImportError as e:
    logger.warning(f"Failed to import health router: {e}")

try:
    from modules.auth.routes import router as auth_router
    routers_to_include.append(("auth", auth_router))
except ImportError as e:
    logger.warning(f"Failed to import auth router: {e}")

try:
    from modules.api.dashboard_routes import router as dashboard_router
    routers_to_include.append(("dashboard", dashboard_router))
except ImportError as e:
    logger.warning(f"Failed to import dashboard router: {e}")

try:
    from modules.api.farmer_dashboard_routes import router as farmer_dashboard_router
    routers_to_include.append(("farmer_dashboard", farmer_dashboard_router))
except ImportError as e:
    logger.warning(f"Failed to import farmer dashboard router: {e}")

try:
    from modules.api.weather_routes import router as weather_router
    routers_to_include.append(("weather", weather_router))
except ImportError as e:
    logger.warning(f"Failed to import weather router: {e}")

try:
    from modules.api.chat_routes import router as chat_router
    routers_to_include.append(("chat", chat_router))
except ImportError as e:
    logger.warning(f"Failed to import chat router: {e}")

try:
    from modules.api.task_management_routes import router as task_management_router
    routers_to_include.append(("task_management", task_management_router))
except ImportError as e:
    logger.warning(f"Failed to import task management router: {e}")

try:
    from modules.fields.routes import router as fields_router
    routers_to_include.append(("fields", fields_router))
except ImportError as e:
    logger.warning(f"Failed to import fields router: {e}")

try:
    from modules.api.debug_edi_kante import router as debug_edi_router
    routers_to_include.append(("debug_edi", debug_edi_router))
except ImportError as e:
    logger.warning(f"Failed to import debug edi router: {e}")

try:
    from modules.api.cava_registration_routes import router as cava_router
    routers_to_include.append(("cava_registration", cava_router))
except ImportError as e:
    logger.warning(f"Failed to import cava registration router: {e}")

try:
    from modules.whatsapp.routes import router as whatsapp_router
    routers_to_include.append(("whatsapp", whatsapp_router))
except ImportError as e:
    logger.warning(f"Failed to import whatsapp router: {e}")

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
            "field_management": True,
            "task_management": True,
            "chat_integration": True,
            "weather_monitoring": True
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

# Import datetime after routers
from datetime import datetime

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info(f"Included routers: {[name for name, _ in routers_to_include]}")
    
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