"""
AVA OLO Mock WhatsApp Interface - Port 8006
Clean interface for testing WhatsApp-like conversations with farmers
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Mock WhatsApp Interface",
    description="WhatsApp-like interface for farmer conversations",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

async def get_api_gateway_data(endpoint: str) -> Dict[str, Any]:
    """Get data from API Gateway"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"http://localhost:8000{endpoint}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway returned status {response.status_code}")
                return {"error": f"API returned status {response.status_code}"}
    except Exception as e:
        logger.error(f"Failed to connect to API Gateway: {str(e)}")
        return {"error": str(e)}

async def send_message_to_api(farmer_id: int, message: str) -> Dict[str, Any]:
    """Send message via API Gateway"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/query",
                json={
                    "query": message,
                    "farmer_id": farmer_id,
                    "context": {"interface": "whatsapp_mock"}
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway returned status {response.status_code}")
                return {"error": f"API returned status {response.status_code}"}
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Mock WhatsApp interface home"""
    # Get farmers list
    farmers_data = await get_api_gateway_data("/api/v1/farmers")
    farmers = farmers_data.get("farmers", []) if "error" not in farmers_data else []
    
    return templates.TemplateResponse("whatsapp_mock.html", {
        "request": request,
        "farmers": farmers,
        "selected_farmer": None,
        "conversations": [],
        "message": None
    })

@app.get("/farmer/{farmer_id}", response_class=HTMLResponse)
async def get_farmer_conversations(request: Request, farmer_id: int):
    """Get conversations for specific farmer"""
    # Get farmers list
    farmers_data = await get_api_gateway_data("/api/v1/farmers")
    farmers = farmers_data.get("farmers", []) if "error" not in farmers_data else []
    
    # Get selected farmer
    selected_farmer = next((f for f in farmers if f["id"] == farmer_id), None)
    
    # Get conversations for this farmer
    conversations_data = await get_api_gateway_data(f"/api/v1/conversations/farmer/{farmer_id}")
    conversations = conversations_data.get("conversations", []) if "error" not in conversations_data else []
    
    return templates.TemplateResponse("whatsapp_mock.html", {
        "request": request,
        "farmers": farmers,
        "selected_farmer": selected_farmer,
        "conversations": conversations,
        "message": None
    })

@app.post("/send_message", response_class=HTMLResponse)
async def send_message(request: Request, farmer_id: int = Form(...), message: str = Form(...)):
    """Send message to farmer"""
    # Send message via API Gateway
    result = await send_message_to_api(farmer_id, message)
    
    # Get updated data
    farmers_data = await get_api_gateway_data("/api/v1/farmers")
    farmers = farmers_data.get("farmers", []) if "error" not in farmers_data else []
    
    selected_farmer = next((f for f in farmers if f["id"] == farmer_id), None)
    
    conversations_data = await get_api_gateway_data(f"/api/v1/conversations/farmer/{farmer_id}")
    conversations = conversations_data.get("conversations", []) if "error" not in conversations_data else []
    
    return templates.TemplateResponse("whatsapp_mock.html", {
        "request": request,
        "farmers": farmers,
        "selected_farmer": selected_farmer,
        "conversations": conversations,
        "message": result.get("answer", "Message sent successfully") if "error" not in result else f"Error: {result['error']}"
    })

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "service": "Mock WhatsApp Interface",
        "status": "healthy",
        "port": 8006,
        "purpose": "WhatsApp-like interface for farmer conversations"
    }

if __name__ == "__main__":
    import uvicorn
    print("📱 Starting AVA OLO Mock WhatsApp Interface on port 8006")
    uvicorn.run(app, host="0.0.0.0", port=8006)