#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.8.2
Phase 2: Add health router only
"""
import os
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Core imports
from modules.core.config import constitutional_deployment_completion
from modules.core.database_manager import get_db_manager

# Essential route imports
from modules.api.health_routes import router as health_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.8.2"

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
    """Root endpoint - phase 2"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "phase2",
        "routers": ["health", "static"],
        "phase": "Health router added"
    })

# Include health router only
app.include_router(health_router, tags=["health"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Phase 2 startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION} - Phase 2: Health router")
    
    # Test database
    try:
        db_manager = get_db_manager()
        if db_manager.test_connection(retries=2, delay=1):
            logger.info("Database connection successful")
        else:
            logger.warning("Database connection failed but continuing")
    except Exception as e:
        logger.error(f"Database test error: {e}")
    
    logger.info(f"AVA OLO Agricultural Core ready - {VERSION} Phase 2")
    constitutional_deployment_completion()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)