"""
🏛️ API Gateway with CAVA Integration
All registration and conversation flows go through central CAVA service
"""

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
import os

# Import CAVA components
from implementation.cava.cava_central_service import get_cava_service
from implementation.cava.cava_registration_handler import (
    handle_registration_input,
    start_new_registration,
    check_registration_status
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO API with CAVA Integration",
    description="Centralized CAVA service for all conversations and registration",
    version="5.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Request/Response models
class RegistrationRequest(BaseModel):
    """Registration input from web form"""
    farmer_id: int = Field(..., description="Unique farmer identifier")
    message: str = Field(..., description="User input (name, phone, password, etc.)")
    session_id: Optional[str] = Field(None, description="Registration session ID")

class RegistrationResponse(BaseModel):
    """Response from CAVA registration"""
    success: bool
    message: str
    session_id: str
    completed: bool = False
    next_field: Optional[str] = None

class ConversationRequest(BaseModel):
    """General conversation request"""
    farmer_id: int
    message: str
    session_id: Optional[str] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize CAVA connection on startup"""
    logger.info("🚀 Starting API Gateway with CAVA...")
    cava = await get_cava_service()
    health = await cava.health_check()
    if not health:
        logger.error("❌ CAVA service not available!")
    else:
        logger.info("✅ CAVA service connected!")

# Health endpoint
@app.get("/health")
async def health_check():
    """Check health of API and CAVA service"""
    cava = await get_cava_service()
    cava_healthy = await cava.health_check()
    
    return {
        "status": "healthy" if cava_healthy else "degraded",
        "api": "healthy",
        "cava": "healthy" if cava_healthy else "unhealthy",
        "version": "5.0.0"
    }

# Registration endpoints
@app.post("/api/v1/register", response_model=RegistrationResponse)
async def register_farmer(request: RegistrationRequest):
    """
    Handle farmer registration through CAVA
    This endpoint is called by all signup forms
    """
    try:
        # Send to CAVA registration handler
        result = await handle_registration_input(
            farmer_id=request.farmer_id,
            user_input=request.message
        )
        
        # Determine if registration is complete
        completed = result.get("success", False) and \
                   ("complete" in result.get("message", "").lower() or 
                    "welcome" in result.get("message", "").lower() and 
                    "!" in result.get("message", ""))
        
        # Try to determine next field from response
        next_field = None
        message_lower = result.get("message", "").lower()
        if "phone" in message_lower:
            next_field = "phone"
        elif "password" in message_lower:
            next_field = "password"
        elif "name" in message_lower:
            next_field = "name"
        
        return RegistrationResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            session_id=result.get("session_id", ""),
            completed=completed,
            next_field=next_field
        )
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/register/start")
async def start_registration(farmer_id: int):
    """Start a new registration session"""
    try:
        result = await start_new_registration(farmer_id)
        return {
            "success": True,
            "message": result.get("message", "Welcome! Let's get you registered."),
            "session_id": result.get("session_id", "")
        }
    except Exception as e:
        logger.error(f"Start registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/register/status/{farmer_id}")
async def get_registration_status(farmer_id: int):
    """Check registration status for a farmer"""
    try:
        status = await check_registration_status(farmer_id)
        return status
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# General conversation endpoint
@app.post("/api/v1/chat")
async def chat_with_ava(request: ConversationRequest):
    """
    General chat endpoint for farming conversations
    Also uses CAVA but for non-registration chats
    """
    try:
        cava = await get_cava_service()
        result = await cava.send_message(
            farmer_id=request.farmer_id,
            message=request.message,
            session_id=request.session_id,
            channel="farming_chat"
        )
        return result
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Web UI endpoints
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Render home page with registration form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def registration_page(request: Request):
    """Render registration page"""
    return templates.TemplateResponse("register_cava.html", {"request": request})

@app.post("/register/submit")
async def submit_registration_form(
    request: Request,
    farmer_id: int = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Handle form submission from web UI"""
    try:
        # Process through CAVA
        result = await handle_registration_input(farmer_id, message)
        
        # Return JSON for AJAX or render template
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse(result)
        else:
            return templates.TemplateResponse(
                "register_cava.html",
                {
                    "request": request,
                    "response": result["message"],
                    "session_id": result.get("session_id"),
                    "completed": "complete" in result.get("message", "").lower()
                }
            )
            
    except Exception as e:
        logger.error(f"Form submission error: {str(e)}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse({"error": str(e)}, status_code=500)
        else:
            return templates.TemplateResponse(
                "register_cava.html",
                {"request": request, "error": str(e)}
            )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    cava = await get_cava_service()
    await cava.close()
    logger.info("🔒 API Gateway shut down")

if __name__ == "__main__":
    import uvicorn
    
    # First ensure CAVA is running
    logger.info("=" * 60)
    logger.info("🏛️ Starting API Gateway with CAVA Integration")
    logger.info("Make sure CAVA is running at http://localhost:8001")
    logger.info("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)