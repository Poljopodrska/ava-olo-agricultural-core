#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.10.2
Phase 3: Add auth router inline
"""
import os
import logging
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.10.2"
BUILD_ID = "auth-router-inline"

# Create simple health router
health_router = APIRouter(prefix="/api/v1/health", tags=["health"])

@health_router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "version": VERSION,
        "build_id": BUILD_ID,
        "timestamp": datetime.now().isoformat()
    })

# Create simple auth router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/signin")
async def signin_page():
    """Sign in endpoint"""
    return JSONResponse({
        "message": "Sign in page",
        "version": VERSION
    })

@auth_router.get("/register")
async def register_page():
    """Register endpoint"""
    return JSONResponse({
        "message": "Register page",
        "version": VERSION
    })

@auth_router.post("/signin")
async def signin_submit(request: Request):
    """Process sign-in"""
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

@auth_router.post("/register")
async def register_submit(request: Request):
    """Process registration"""
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

@auth_router.get("/logout")
async def logout():
    """Log out user"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="farmer_id")
    response.delete_cookie(key="farmer_name")
    return response

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
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
        "features": ["static_files", "health_router", "auth_router"],
        "timestamp": datetime.now().isoformat()
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

# Include routers
app.include_router(health_router)
app.include_router(auth_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup"""
    logger.info(f"Starting AVA OLO Agricultural Core {VERSION}")
    logger.info("Phase 3: Auth router added inline")
    logger.info("Ready to serve")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)