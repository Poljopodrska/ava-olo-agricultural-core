#!/usr/bin/env python3
"""
AVA OLO Agricultural Core Service with Constitutional Design
Serves the main business dashboard and agricultural interfaces
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys
from datetime import datetime
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version info
VERSION = "v2.5.0-constitutional"
BUILD_ID = "const-design-2025"

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Core",
    description="Constitutional Design System Implementation",
    version=VERSION
)

# Mount static files for design system
app.mount("/shared", StaticFiles(directory="shared"), name="shared")
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'Y<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Redirect to business dashboard"""
    return templates.TemplateResponse("business_dashboard_constitutional.html", {
        "request": request,
        "version": VERSION
    })

@app.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard(request: Request):
    """Business Dashboard with Constitutional Design"""
    return templates.TemplateResponse("business_dashboard_constitutional.html", {
        "request": request,
        "version": VERSION
    })

@app.get("/api/stats/overview")
async def stats_overview():
    """Get real statistics from database"""
    conn = get_db_connection()
    if not conn:
        return JSONResponse(status_code=503, content={"error": "Database unavailable"})
    
    try:
        with conn.cursor() as cursor:
            # Get total farmers
            cursor.execute("SELECT COUNT(*) as count FROM farmers")
            farmers_count = cursor.fetchone()['count']
            
            # Get total hectares
            cursor.execute("SELECT SUM(total_hectares) as total FROM farmers")
            total_hectares = cursor.fetchone()['total'] or 0
            
            # Get conversation count
            cursor.execute("SELECT COUNT(*) as count FROM ava_conversations")
            conversations = cursor.fetchone()['count']
            
            return {
                "total_farmers": farmers_count,
                "total_hectares": float(total_hectares),
                "total_conversations": conversations,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": VERSION,
        "build_id": BUILD_ID,
        "service": "agricultural-core",
        "constitutional_design": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/monitoring", response_class=HTMLResponse)
async def monitoring_dashboard(request: Request):
    """Monitoring Dashboard"""
    # Create a simple monitoring page with constitutional design
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO Monitoring</title>
        <link rel="stylesheet" href="/shared/design-system/css/design-system.css">
        <link rel="stylesheet" href="/shared/design-system/css/typography.css">
        <link rel="stylesheet" href="/shared/design-system/css/components.css">
    </head>
    <body>
        <header class="ava-header">
            <div class="logo">
                <img src="/shared/design-system/assets/logo-white.svg" alt="AVA OLO">
            </div>
            <nav>
                <a href="/">Home</a>
                <a href="/business-dashboard">Business</a>
                <a href="/monitoring">Monitoring</a>
            </nav>
            <div class="version-display">{VERSION}</div>
        </header>
        
        <main class="container" style="padding-top: var(--space-xl);">
            <h1>System Monitoring</h1>
            <div class="card">
                <h2>Real-time Metrics</h2>
                <p>System monitoring dashboard with constitutional design.</p>
                <div class="alert alert-success">
                    All systems operational
                </div>
            </div>
        </main>
        
        <script src="/shared/design-system/js/accessibility.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/database-dashboard", response_class=HTMLResponse)
async def database_dashboard(request: Request):
    """Database Dashboard"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AVA OLO Database</title>
        <link rel="stylesheet" href="/shared/design-system/css/design-system.css">
        <link rel="stylesheet" href="/shared/design-system/css/typography.css">
        <link rel="stylesheet" href="/shared/design-system/css/components.css">
    </head>
    <body>
        <header class="ava-header">
            <div class="logo">
                <img src="/shared/design-system/assets/logo-white.svg" alt="AVA OLO">
            </div>
            <nav>
                <a href="/">Home</a>
                <a href="/business-dashboard">Business</a>
                <a href="/monitoring">Monitoring</a>
                <a href="/database-dashboard">Database</a>
            </nav>
            <div class="version-display">{VERSION}</div>
        </header>
        
        <main class="container" style="padding-top: var(--space-xl);">
            <h1>Database Explorer</h1>
            <div class="card">
                <h2>Farmer Database</h2>
                <p>Explore and manage agricultural data with constitutional design.</p>
                <button class="btn btn-primary">View Farmers</button>
            </div>
        </main>
        
        <script src="/shared/design-system/js/accessibility.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# Serve logo directly
@app.get("/logo.svg")
async def get_logo():
    """Serve AVA OLO logo"""
    return FileResponse("shared/design-system/assets/logo-white.svg", media_type="image/svg+xml")

# Serve favicon
@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon"""
    return FileResponse("shared/design-system/assets/favicon.svg", media_type="image/svg+xml")

if __name__ == "__main__":
    import uvicorn
    print(f"🌾 Starting AVA OLO Agricultural Core {VERSION}")
    print("📐 Constitutional Design System Active")
    print("🚀 Server running on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)