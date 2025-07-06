"""
AVA OLO UI Service - Port 8002
Simple testing interface for queries before WhatsApp integration
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import httpx
import os
import sys
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO UI Service",
    description="Simple testing interface for agricultural queries",
    version="2.0.0"
)

# Setup templates for restored working UI
templates = Jinja2Templates(directory="services/templates")
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API Gateway URL
API_GATEWAY_URL = "http://localhost:8000"

async def query_api_gateway(query: str, farmer_id: Optional[int] = None) -> Dict[str, Any]:
    """Send query to modular API Gateway"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{API_GATEWAY_URL}/api/v1/query",
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
                return {
                    "success": False,
                    "answer": f"API Gateway error: {response.status_code}",
                    "metadata": {"source": "error"}
                }
                
    except Exception as e:
        logger.error(f"Failed to connect to API Gateway: {str(e)}")
        return {
            "success": False,
            "answer": f"Thank you for your question: '{query}'. API is currently unavailable - please try again later.",
            "metadata": {"source": "fallback", "error": str(e)}
        }

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main testing interface - restored working UI"""
    return templates.TemplateResponse("ui_dashboard.html", {
        "request": request, 
        "response": None,
        "title": "AVA OLO - Test Interface"
    })

@app.post("/", response_class=HTMLResponse)
async def process_query(request: Request, question: str = Form(...)):
    """Process form submission through restored UI"""
    logger.info(f"UI Test Query: {question}")
    
    # Process through API Gateway
    result = await query_api_gateway(question)
    response_text = result.get("answer", "No response received")
    
    # Add metadata info for testing
    metadata = result.get("metadata", {})
    if metadata:
        response_text += f"\n\n[Test Info: {metadata.get('source', 'unknown')}]"
    
    return templates.TemplateResponse("ui_dashboard.html", {
        "request": request,
        "response": response_text,
        "question": question,
        "title": "AVA OLO - Test Interface"
    })

@app.post("/ava", response_class=HTMLResponse)
async def form_post(request: Request, question: str = Form(...)):
    """Alternative POST endpoint for restored UI compatibility"""
    return await process_query(request, question)

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{API_GATEWAY_URL}/api/v1/health")
            api_healthy = response.status_code == 200
    except:
        api_healthy = False
    
    return {
        "service": "UI Testing Service",
        "status": "healthy",
        "api_gateway": "connected" if api_healthy else "disconnected",
        "port": 8002,
        "purpose": "Testing interface before WhatsApp integration"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "AVA OLO UI Service is running",
        "port": 8002,
        "purpose": "Agricultural query testing interface"
    }

if __name__ == "__main__":
    import uvicorn
    print("🌾 Starting AVA OLO UI Service on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)