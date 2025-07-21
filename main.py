#!/usr/bin/env python3
"""
AVA OLO Monitoring Dashboards - Modularized Main Application
Version: v2.3.0-ecs-ready
Refactored for AWS ECS deployment with modules under 100KB
"""
import uvicorn
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

# Import configuration
from modules.core.config import VERSION, BUILD_ID, constitutional_deployment_completion, config
from modules.core.database_manager import get_db_manager

# Import API routers
from modules.api.deployment_routes import router as deployment_router, audit_router
from modules.api.database_routes import router as database_router, agricultural_router, debug_router
from modules.api.health_routes import router as health_router
from modules.api.business_routes import router as business_router
from modules.api.dashboard_routes import router as dashboard_router, api_router as dashboard_api_router
from modules.api.deployment_webhook import router as webhook_router

# Import dashboard modules
from modules.dashboards.agronomic import router as agronomic_router
from modules.dashboards.business import router as business_dashboard_router
from modules.dashboards.health import router as health_dashboard_router
from modules.dashboards.database import router as database_dashboard_router
from modules.dashboards.deployment import router as deployment_dashboard_router, api_router as deployment_api_router
from modules.dashboards.feature_status import router as feature_status_router

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Monitoring Dashboards",
    version=VERSION,
    description="Monitoring dashboards for AVA OLO agricultural system"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(deployment_router)
app.include_router(audit_router)
app.include_router(database_router)
app.include_router(agricultural_router)
app.include_router(debug_router)
app.include_router(health_router)
app.include_router(business_router)
app.include_router(dashboard_router)
app.include_router(dashboard_api_router)
app.include_router(agronomic_router)
app.include_router(business_dashboard_router)
app.include_router(health_dashboard_router)
app.include_router(database_dashboard_router)
app.include_router(deployment_dashboard_router)
app.include_router(deployment_api_router)
app.include_router(feature_status_router)
app.include_router(webhook_router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print(f"🚀 Starting AVA OLO Monitoring Dashboards {VERSION}")
    print(f"📦 Build ID: {BUILD_ID}")
    
    # Initialize database connection pool
    db_manager = get_db_manager()
    if db_manager.test_connection():
        print("✅ Database connection established")
    else:
        print("⚠️ Database connection failed - running in degraded mode")
    
    # Constitutional deployment completion
    constitutional_deployment_completion()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - landing page"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="app-version" content="{VERSION}">
        <title>AVA OLO - Agricultural Monitoring Panel</title>
        <link rel="stylesheet" href="/static/css/constitutional-design-v3.css">
    </head>
    <body>
        <nav class="ava-nav">
            <a href="/" class="ava-nav-brand">🌾 AVA OLO</a>
            <div class="ava-nav-items">
                <a href="/dashboards/deployment" class="ava-nav-link">System Status</a>
                <a href="/dashboards/health" class="ava-nav-link">System Health</a>
            </div>
        </nav>
        
        <main id="main-content" class="ava-dashboard-container">
            <h1 class="ava-text-center ava-mb-lg">Agricultural Monitoring Panel</h1>
            <p class="ava-text-center ava-mb-2xl" style="font-size: var(--ava-font-size-large); color: var(--ava-brown-muted);">
                Comprehensive monitoring system for the Bulgarian mango cooperative
            </p>
            
            <div class="ava-dashboard-grid">
                <a href="/dashboards/business" class="ava-dashboard-button">
                    <span class="icon">📊</span>
                    <span class="label">Business Dashboard</span>
                </a>
                <a href="/dashboards/database" class="ava-dashboard-button">
                    <span class="icon">🗄️</span>
                    <span class="label">Database Dashboard</span>
                </a>
                <a href="/dashboards/health" class="ava-dashboard-button">
                    <span class="icon">🏥</span>
                    <span class="label">Health Dashboard</span>
                </a>
                <a href="/dashboards/deployment" class="ava-dashboard-button">
                    <span class="icon">🚀</span>
                    <span class="label">Deployment Dashboard</span>
                </a>
                <a href="/dashboards/agronomic" class="ava-dashboard-button">
                    <span class="icon">🌾</span>
                    <span class="label">Agronomic Dashboard</span>
                </a>
                <a href="/dashboards/cost" class="ava-dashboard-button">
                    <span class="icon">💰</span>
                    <span class="label">Cost Dashboard</span>
                </a>
            </div>
        </main>
        
        <script src="/static/js/constitutional-interactions.js"></script>
        <script>
            window.AVA_VERSION = '{VERSION}';
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health_check():
    """Health check endpoint for ALB"""
    db_manager = get_db_manager()
    db_healthy = db_manager.test_connection()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "service": "monitoring-dashboards"
    }

@app.get("/version")
async def get_version():
    """Get current version"""
    return {"version": VERSION, "build_id": BUILD_ID}

@app.get("/deployment-method")
async def deployment_method():
    """Test endpoint to verify automatic webhook deployment"""
    return {
        "method": "automatic-webhook",
        "manual_commands_needed": False,
        "version": VERSION,
        "message": "Monitoring dashboards deployed automatically via webhook!",
        "test_id": "v3.3.8-webhook-verification"
    }

# Add remaining dashboard placeholders
@app.get("/database-dashboard", response_class=HTMLResponse)
async def database_dashboard():
    """Database dashboard placeholder"""
    return HTMLResponse(f"""
    <html>
    <head><title>Database Dashboard</title></head>
    <body>
        <h1>Database Dashboard</h1>
        <p>Version: {VERSION}</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

@app.get("/health-dashboard", response_class=HTMLResponse)
async def health_dashboard():
    """Health dashboard placeholder"""
    return HTMLResponse(f"""
    <html>
    <head><title>Health Dashboard</title></head>
    <body>
        <h1>Health Dashboard</h1>
        <p>Version: {VERSION}</p>
        <p><a href="/api/v1/health/system-status">System Status</a></p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

@app.get("/ui-dashboard", response_class=HTMLResponse)
async def ui_dashboard():
    """UI dashboard placeholder"""
    return HTMLResponse(f"""
    <html>
    <head><title>UI Dashboard</title></head>
    <body>
        <h1>UI Dashboard</h1>
        <p>Version: {VERSION}</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

# Redirect legacy endpoints
@app.get("/deployment-verify")
async def deployment_verify_redirect():
    """Redirect to new deployment verify endpoint"""
    return RedirectResponse(url="/api/deployment/verify")

if __name__ == "__main__":
    # Report deployment version
    constitutional_deployment_completion()
    
    # Run the application
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info"
    )