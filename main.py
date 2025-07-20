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
        <title>AVA OLO Monitoring Dashboards</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 40px;
                background-color: #f5f5f5;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .container {{
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 600px;
                width: 100%;
            }}
            h1 {{
                color: #2e7d32;
                margin-bottom: 30px;
                text-align: center;
            }}
            .version {{
                background: #e8f5e9;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin-bottom: 30px;
            }}
            .dashboard-links {{
                display: grid;
                gap: 10px;
            }}
            .dashboard-link {{
                display: block;
                padding: 15px 20px;
                background: #1976d2;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                text-align: center;
                transition: background 0.3s;
            }}
            .dashboard-link:hover {{
                background: #1565c0;
            }}
            .api-section {{
                margin-top: 30px;
                padding-top: 30px;
                border-top: 1px solid #ddd;
            }}
            .api-link {{
                display: inline-block;
                margin: 5px;
                padding: 8px 15px;
                background: #f5f5f5;
                color: #333;
                text-decoration: none;
                border-radius: 4px;
                font-size: 0.9em;
            }}
            .api-link:hover {{
                background: #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌾 AVA OLO Monitoring Dashboards</h1>
            
            <div class="version">
                <strong>Version:</strong> {VERSION}<br>
                <strong>Build ID:</strong> {BUILD_ID}
            </div>
            
            <div class="dashboard-links">
                <a href="/dashboards/" class="dashboard-link">
                    🏠 Dashboard Hub
                </a>
                <a href="/business-dashboard" class="dashboard-link">
                    📊 Legacy Business Dashboard
                </a>
                <a href="/dashboards/database" class="dashboard-link">
                    🗄️ New Database Dashboard
                </a>
                <a href="/dashboards/business" class="dashboard-link">
                    📈 New Business Dashboard
                </a>
                <a href="/dashboards/health" class="dashboard-link">
                    💚 New Health Dashboard
                </a>
            </div>
            
            <div class="api-section">
                <h3>API Endpoints</h3>
                <a href="/api/deployment/verify" class="api-link">Deployment Verify</a>
                <a href="/api/v1/health" class="api-link">Health Check</a>
                <a href="/api/v1/database/test" class="api-link">Database Test</a>
                <a href="/docs" class="api-link">API Documentation</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/version")
async def get_version():
    """Get current version"""
    return {"version": VERSION, "build_id": BUILD_ID}

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