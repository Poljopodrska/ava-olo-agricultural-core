#!/usr/bin/env python3
"""
AVA OLO Monitoring Dashboards - Modularized Main Application
Version: v2.3.0-ecs-ready
Refactored for AWS ECS deployment with modules under 100KB
"""
import uvicorn
import sys
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

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
from modules.api.system_routes import router as system_router

# Import dashboard modules
from modules.dashboards.agronomic import router as agronomic_router
from modules.dashboards.business import router as business_dashboard_router
from modules.dashboards.health import router as health_dashboard_router
from modules.dashboards.database import router as database_dashboard_router
from modules.dashboards.deployment import router as deployment_dashboard_router, api_router as deployment_api_router
from modules.dashboards.feature_status import router as feature_status_router

# Import auth module
from modules.auth.routes import router as auth_router

# Import weather module
from modules.weather.routes import router as weather_router

# Import CAVA module
from modules.cava.routes import router as cava_router

# Import fields module
from modules.fields.routes import router as fields_router

# Import chat module
from modules.chat.routes import router as chat_router

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Farmer Portal",
    version=VERSION,
    description="WhatsApp-style farmer portal with weather, chat, and farm management"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

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
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(cava_router)
app.include_router(fields_router)
app.include_router(chat_router)
app.include_router(system_router)

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
    
    # Check OpenAI configuration
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ WARNING: OPENAI_API_KEY not set. Chat functionality will be limited to mock responses.")
    else:
        print("✅ OpenAI API key configured")
    
    # Constitutional deployment completion
    constitutional_deployment_completion()

@app.get("/")
async def landing_page(request: Request):
    """Landing page with UNICORN TEST"""
    # Return HTML with unicorn for unmistakable verification
    from datetime import datetime
    return HTMLResponse(f"""
    <html>
    <body style="background: pink;">
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    z-index: 9999; background: white; padding: 20px; border: 5px solid red;">
            <h1 style="color: red; font-size: 48px;">🦄 UNICORN TEST v3.3.24 🦄</h1>
            <p style="font-size: 24px; color: green;">If you see this unicorn, deployment worked!</p>
            <p style="font-size: 32px; color: blue;">VERSION: {VERSION}</p>
            <p style="font-size: 20px;">Deployed at: {datetime.now()}</p>
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Unicorn-logo.svg/512px-Unicorn-logo.svg.png" 
                 style="width: 300px; height: 300px;">
        </div>
        <div style="text-align: center; margin-top: 100px;">
            <h1 style="font-size: 72px;">🦄 UNICORN TEST 🦄</h1>
            <h2>Version: {VERSION}</h2>
            <h3>If you see this pink page with unicorn, deployment worked!</h3>
            <p>Time: {datetime.now()}</p>
            <p><a href="/dashboard">Go to Dashboard</a></p>
        </div>
    </body>
    </html>
    """)

@app.get("/dashboard")
async def dashboard(request: Request):
    """Basic dashboard - placeholder for three-panel layout"""
    farmer_name = request.cookies.get("farmer_name", "Farmer")
    farmer_id = request.cookies.get("farmer_id")
    
    if not farmer_id:
        return RedirectResponse(url="/auth/signin", status_code=303)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "version": VERSION,
        "farmer_name": farmer_name
    })

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
    """Get current version with UNICORN TEST"""
    from datetime import datetime
    return {
        "version": VERSION,
        "build_id": BUILD_ID,
        "unicorn_test": "🦄 YES - DEPLOYMENT WORKED! 🦄",
        "actual_version": "3.3.24-unicorn-test",
        "deployment_timestamp": datetime.now().isoformat(),
        "big_unicorn": "🦄" * 50,
        "message": "IF YOU SEE THIS, IT'S NOT A CACHING ISSUE"
    }

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