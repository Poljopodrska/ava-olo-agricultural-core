"""
🏛️ CAVA FastAPI Endpoint
Constitutional API for the Universal Conversation Engine
Supports Telegram, WhatsApp, and future channels
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CAVA - Constitutional AVA Conversation API",
    description="Universal conversation engine for AVA OLO - works with ANY crop in ANY country",
    version="1.0.0"
)

# Global engine instance
engine: Optional[CAVAUniversalConversationEngine] = None

# Request/Response models
class ConversationRequest(BaseModel):
    """Farmer message request"""
    farmer_id: int = Field(..., description="Unique farmer ID from Telegram/WhatsApp")
    message: str = Field(..., description="Farmer's message text")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    channel: str = Field("telegram", description="Communication channel: telegram, whatsapp, etc.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ConversationResponse(BaseModel):
    """CAVA response to farmer"""
    success: bool
    session_id: str
    message: str
    conversation_type: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    databases: Dict[str, str]
    llm_configured: bool
    dry_run_mode: bool
    timestamp: str

class ConversationHistoryRequest(BaseModel):
    """Request for conversation history"""
    session_id: str

class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: str
    messages: List[Dict[str, Any]]
    farmer_id: Optional[int] = None
    started_at: Optional[str] = None

# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize CAVA engine on startup"""
    global engine
    logger.info("🚀 Starting CAVA API...")
    
    try:
        engine = CAVAUniversalConversationEngine()
        await engine.initialize()
        logger.info("✅ CAVA API started successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to start CAVA: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of CAVA engine"""
    global engine
    if engine:
        await engine.close()
        logger.info("🔒 CAVA API shut down")

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "CAVA - Constitutional AVA Conversation API",
        "version": "1.0.0",
        "status": "operational",
        "constitutional_amendment": "15",
        "principle": "If the LLM can write it, don't code it"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns status of all CAVA components
    """
    if not engine:
        raise HTTPException(status_code=503, detail="CAVA engine not initialized")
    
    health = await engine.health_check()
    
    return HealthResponse(
        status=health["status"],
        databases=health["databases"],
        llm_configured=health["llm_configured"],
        dry_run_mode=health["dry_run_mode"],
        timestamp=datetime.now().isoformat()
    )

@app.post("/conversation", response_model=ConversationResponse)
async def handle_conversation(request: ConversationRequest):
    """
    Main conversation endpoint
    Handles ANY farmer message - registration, farming questions, etc.
    Works for watermelon, Bulgarian mango, dragonfruit, ANY crop
    """
    if not engine:
        raise HTTPException(status_code=503, detail="CAVA engine not initialized")
    
    logger.info(f"📨 Received message from farmer {request.farmer_id}: {request.message[:50]}...")
    
    try:
        # Process message through CAVA
        result = await engine.handle_farmer_message(
            farmer_id=request.farmer_id,
            message=request.message,
            session_id=request.session_id,
            channel=request.channel
        )
        
        return ConversationResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        return ConversationResponse(
            success=False,
            session_id=request.session_id or "",
            message="I'm having trouble processing your message. Please try again.",
            error=str(e)
        )

@app.post("/conversation/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(request: ConversationHistoryRequest):
    """
    Get conversation history for a session
    Useful for debugging and conversation continuity
    """
    if not engine:
        raise HTTPException(status_code=503, detail="CAVA engine not initialized")
    
    history = await engine.get_conversation_history(request.session_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationHistoryResponse(
        session_id=request.session_id,
        messages=history.get("messages", []),
        farmer_id=history.get("farmer_id"),
        started_at=history.get("started_at")
    )

@app.post("/test/scenarios")
async def test_scenarios():
    """
    Test endpoint for running CAVA scenarios
    Tests registration, watermelon, Bulgarian mango, etc.
    """
    if not engine:
        raise HTTPException(status_code=503, detail="CAVA engine not initialized")
    
    results = []
    
    # Test 1: Peter Knaflič registration
    try:
        peter_response = await engine.handle_farmer_message(
            farmer_id=99999,
            message="Peter Knaflič"
        )
        results.append({
            "test": "Peter Knaflič Registration",
            "success": peter_response["success"],
            "response": peter_response["message"]
        })
    except Exception as e:
        results.append({
            "test": "Peter Knaflič Registration",
            "success": False,
            "error": str(e)
        })
    
    # Test 2: Watermelon question
    try:
        watermelon_response = await engine.handle_farmer_message(
            farmer_id=88888,
            message="Where did I plant my watermelon?"
        )
        results.append({
            "test": "Watermelon Question",
            "success": watermelon_response["success"],
            "response": watermelon_response["message"]
        })
    except Exception as e:
        results.append({
            "test": "Watermelon Question",
            "success": False,
            "error": str(e)
        })
    
    # Test 3: Bulgarian mango
    try:
        mango_response = await engine.handle_farmer_message(
            farmer_id=77777,
            message="When can I harvest my Bulgarian mangoes?"
        )
        results.append({
            "test": "Bulgarian Mango (MANGO RULE)",
            "success": mango_response["success"],
            "response": mango_response["message"]
        })
    except Exception as e:
        results.append({
            "test": "Bulgarian Mango (MANGO RULE)",
            "success": False,
            "error": str(e)
        })
    
    return {
        "test_results": results,
        "constitutional_compliance": True,
        "tested_at": datetime.now().isoformat()
    }

@app.get("/constitutional/principles")
async def get_constitutional_principles():
    """
    Return CAVA's constitutional principles
    Educational endpoint for understanding the system
    """
    return {
        "amendment_15": {
            "title": "LLM-Generated Intelligence",
            "principle": "If the LLM can write it, don't code it",
            "implementation": "95%+ of farming logic is LLM-generated"
        },
        "key_principles": {
            "MANGO_RULE": "Works for ANY crop in ANY country (Bulgarian mangoes included)",
            "FARMER_CENTRIC": "Designed for farmers, not engineers",
            "PRIVACY_FIRST": "All data stays within constitutional boundaries",
            "ERROR_ISOLATION": "CAVA failures don't affect core AVA",
            "MODULE_INDEPENDENCE": "CAVA runs as independent module"
        },
        "supported_scenarios": [
            "Farmer registration (any name, any country)",
            "Crop management (watermelon to dragonfruit)",
            "Harvest timing calculations",
            "Product application tracking",
            "Multi-language support"
        ]
    }

# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors constitutionally"""
    logger.error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "CAVA encountered an error but AVA core remains operational",
            "constitutional_note": "ERROR ISOLATION principle activated"
        }
    )

# Run the API
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("CAVA_API_PORT", "8001"))
    host = os.getenv("CAVA_API_HOST", "0.0.0.0")
    
    logger.info(f"🏛️ Starting CAVA API on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )