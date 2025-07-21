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
        <title>AVA OLO Monitoring Dashboards</title>
        <link rel="stylesheet" href="/static/css/constitutional-design-system-v2.css">
        <style>
            body {{
                font-family: var(--font-primary);
                margin: 0;
                padding: 40px 20px;
                background-color: var(--color-bg-primary);
                min-height: 100vh;
                position: relative;
            }}
            .container {{
                background: var(--color-bg-white);
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: var(--color-agri-green);
                margin-bottom: 30px;
                text-align: center;
                font-size: var(--font-title);
            }}
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}
            .dashboard-button {{
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 24px 20px;
                background: var(--primary-olive);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                text-align: center;
                transition: all 0.3s ease;
                min-height: 100px;
                font-size: var(--font-size-base);
            }}
            .dashboard-button:hover {{
                background: var(--dark-olive);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .dashboard-button .icon {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .dashboard-button .label {{
                font-weight: 500;
                font-size: var(--font-size-base);
            }}
            .version-display {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                font-size: 14px;
                color: var(--medium-gray);
                background: rgba(255, 255, 255, 0.9);
                padding: 8px 16px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            @media (max-width: 768px) {{
                .dashboard-grid {{
                    grid-template-columns: 1fr 1fr;
                }}
                .container {{
                    padding: 20px;
                }}
                h1 {{
                    font-size: 24px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌾 AVA OLO Monitoring Dashboards</h1>
            
            <div class="dashboard-grid">
                <a href="/dashboards/business" class="dashboard-button">
                    <span class="icon">📊</span>
                    <span class="label">Business Dashboard</span>
                </a>
                <a href="/dashboards/database" class="dashboard-button">
                    <span class="icon">🗄️</span>
                    <span class="label">Database Dashboard</span>
                </a>
                <a href="/dashboards/health" class="dashboard-button">
                    <span class="icon">🏥</span>
                    <span class="label">Health Dashboard</span>
                </a>
                <a href="/dashboards/deployment" class="dashboard-button">
                    <span class="icon">🚀</span>
                    <span class="label">Deployment Dashboard</span>
                </a>
                <a href="/dashboards/agronomic" class="dashboard-button">
                    <span class="icon">🌾</span>
                    <span class="label">Agronomic Dashboard</span>
                </a>
                <a href="/dashboards/cost" class="dashboard-button">
                    <span class="icon">💰</span>
                    <span class="label">Cost Dashboard</span>
                </a>
            </div>
        </div>
        
        <div class="version-display">
            v{VERSION.split('-')[0]}
        </div>
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