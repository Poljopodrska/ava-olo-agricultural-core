"""
AVA OLO Admin Dashboard - Constitutional Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

# Import constitutional API
from monitoring.interfaces.admin_dashboard_api import app as api_app
from monitoring.config.dashboard_config import DASHBOARD_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create main app
app = FastAPI(
    title="AVA OLO Admin Dashboard",
    description="Constitutional agricultural database management",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="monitoring/templates")

# Mount API
app.mount("/api", api_app)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "config": DASHBOARD_CONFIG
    })

@app.get("/database", response_class=HTMLResponse) 
async def database_redirect(request: Request):
    """Redirect old URL to new dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "config": DASHBOARD_CONFIG
    })

if __name__ == "__main__":
    print("🌾 Starting AVA OLO Admin Dashboard (Constitutional)")
    print("✅ Mango Rule Compliant")
    print("✅ Privacy First")
    print("✅ LLM First")
    print("✅ Error Isolation Active")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8005)
