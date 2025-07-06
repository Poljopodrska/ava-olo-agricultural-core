print("✅ LOADING MODULAR AVA OLO UI FROM:", __file__)

import sys, os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
import httpx
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger(__name__)

# Simple fallback when API Gateway unavailable
async def fallback_response(query: str) -> Dict[str, Any]:
    """Simple fallback when modular backend is unavailable"""
    return {
        "success": False,
        "answer": f"Hvala na pitanju: '{query}'. Sustav je trenutno u održavanju. Molim pokušajte kasnije.",
        "metadata": {"source": "fallback", "language": "hr"}
    }

# Connect to API Gateway
async def query_api_gateway(query: str, farmer_id: Optional[int] = None) -> Dict[str, Any]:
    """Send query to modular API Gateway"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/query",
                json={
                    "query": query,
                    "farmer_id": farmer_id,
                    "context": {}
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway returned status {response.status_code}")
                return await fallback_response(query)
                
    except Exception as e:
        logger.error(f"Failed to connect to API Gateway: {str(e)}")
        return await fallback_response(query)

# ✅ Create FastAPI app
app = FastAPI()

# ✅ Setup templates and static
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ GET route: show the main dashboard (browser) - RESTORED WORKING UI
@app.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    print("✅ GET / triggered - serving restored main dashboard")
    # Serve the restored working dashboard as the main interface
    services = [
        {
            "name": "Test UI",
            "description": "Simple testing interface for farmer conversations",
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
        },
        {
            "name": "Mock WhatsApp",
            "description": "WhatsApp-like interface for farmer conversations",
            "port": 8006,
            "url": "http://localhost:8006", 
            "icon": "📱",
            "status": "active"
        },
        {
            "name": "Agronomic Approval",
            "description": "Expert dashboard for conversation approval",
            "port": 8007,
            "url": "http://localhost:8007", 
            "icon": "🌾",
            "status": "active"
        }
    ]
    return templates.TemplateResponse("main_dashboard.html", {
        "request": request,
        "services": services
    })

# ✅ GET route: show the form (browser) 
@app.get("/form", response_class=HTMLResponse)
@app.get("/ava", response_class=HTMLResponse)  # Add /ava route that was being requested
def form_get(request: Request):
    print("✅ GET /form or /ava triggered")
    return templates.TemplateResponse("form.html", {"request": request, "response": None})

# ✅ POST route: process form submission (browser) - UPDATED FOR MODULAR BACKEND
@app.post("/", response_class=HTMLResponse)
@app.post("/form", response_class=HTMLResponse)
@app.post("/ava", response_class=HTMLResponse)  # Add POST route for /ava
async def form_post(request: Request, question: str = Form(...)):
    print("✅ POST / or /form or /ava triggered — question:", question)
    
    # Use modular API Gateway
    result = await query_api_gateway(question)
    response_text = result.get("answer", "No response received")
    
    return templates.TemplateResponse("form.html", {
        "request": request,
        "response": response_text,
        "question": question
    })

# ✅ API: JSON endpoint for chatbot or curl/Postman - UPDATED FOR MODULAR BACKEND
class AskRequest(BaseModel):
    question: str
    farmer_id: Optional[int] = None

@app.post("/ask")
async def ask_api(request: AskRequest):
    print("✅ POST /ask triggered — question:", request.question)
    result = await query_api_gateway(request.question, request.farmer_id)
    return result

# ✅ Health check
@app.get("/health")
async def health_check():
    """Health check for UI and API Gateway connectivity"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8000/api/v1/health")
            api_healthy = response.status_code == 200
    except:
        api_healthy = False
    
    return {
        "ui_status": "healthy",
        "api_gateway_status": "healthy" if api_healthy else "unavailable",
        "message": "Modular AVA OLO UI is running" + (" with API Gateway" if api_healthy else " in fallback mode")
    }

# ✅ Dashboard routes (sophisticated UI)
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/dashboard/ui", response_class=HTMLResponse)
async def dashboard_ui(request: Request):
    """Sophisticated dashboard UI"""
    print("✅ GET /dashboard/ui triggered - serving monitoring dashboard")
    return templates.TemplateResponse("monitoring.html", {"request": request})

@app.get("/dashboard/conversations", response_class=HTMLResponse)
async def dashboard_conversations(request: Request):
    """Dashboard conversations view - the route that was being requested"""
    print("✅ GET /dashboard/conversations triggered")
    # For now, redirect to monitoring dashboard until we implement conversations view
    return templates.TemplateResponse("monitoring.html", {"request": request})

@app.get("/dashboard/api")
async def dashboard_api():
    """Dashboard API data endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8000/api/v1/business/summary")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
    
    return {"message": "Dashboard currently unavailable", "status": "fallback_mode"}

# ✅ Test endpoint
@app.get("/test123")
def test_route():
    return {"message": "✅ This is the REAL app.py!"}
