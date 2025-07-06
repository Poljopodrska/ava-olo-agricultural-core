"""
AVA OLO Main Dashboard - Port 8001 
Central hub connecting all services (restored from yesterday's working version)
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Main Dashboard",
    description="Central hub for all AVA OLO services",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard home - restored working UI"""
    return templates.TemplateResponse("main_dashboard.html", {
        "request": request,
        "services": [
            {
                "name": "Test UI",
                "description": "Simple testing interface before WhatsApp integration",
                "port": 8002,
                "url": "http://localhost:8002",
                "icon": "🧪",
                "status": "active"
            },
            {
                "name": "Agronomic Dashboard", 
                "description": "Expert monitoring and conversation approval",
                "port": 8003,
                "url": "http://localhost:8003",
                "icon": "🌾",
                "status": "active"
            },
            {
                "name": "Business KPIs",
                "description": "Business metrics and performance indicators", 
                "port": 8004,
                "url": "http://localhost:8004",
                "icon": "📊",
                "status": "active"
            },
            {
                "name": "Database Explorer",
                "description": "User-friendly database exploration and export",
                "port": 8005,
                "url": "http://localhost:8005", 
                "icon": "🗃️",
                "status": "active"
            }
        ]
    })

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "service": "Main Dashboard",
        "status": "healthy",
        "port": 8001,
        "purpose": "Central hub for all AVA OLO services"
    }

if __name__ == "__main__":
    import uvicorn
    print("🏠 Starting AVA OLO Main Dashboard on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)