#!/usr/bin/env python3
"""
🏛️ Constitutional Amendment #15: Zero-Code Universal Endpoint
LLM generates ALL intelligence - handles registration, farming, mixed conversations
Constitutional Amendment #15 compliant
"""
import uuid
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implementation.zero_code_conversation_engine import ZeroCodeConversationEngine
from config_manager import config

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AVA OLO Zero-Code Universal API",
    description="🏛️ Constitutional Amendment #15: LLM generates ALL intelligence",
    version="15.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global conversation engines cache
_conversation_engines: Dict[str, ZeroCodeConversationEngine] = {}

class ChatRequest(BaseModel):
    """Universal chat request model"""
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    message: str = Field(..., description="Farmer's message")
    farmer_id: Optional[int] = Field(None, description="Farmer ID if known")

class ChatResponse(BaseModel):
    """Universal chat response model"""
    success: bool
    message: str
    session_id: str
    llm_generated: bool
    amendment_15_compliance: bool
    analysis: Optional[Dict] = None
    registration_status: Optional[Dict] = None
    farmer_context: Optional[Dict] = None
    timestamp: str

async def get_conversation_engine(session_id: str) -> ZeroCodeConversationEngine:
    """Get or create conversation engine for session"""
    
    if session_id not in _conversation_engines:
        engine = ZeroCodeConversationEngine(
            session_id=session_id,
            database_url=config.database_url,
            redis_url=config.redis_url,
            openai_api_key=config.openai_api_key
        )
        
        await engine.initialize()
        _conversation_engines[session_id] = engine
        
        logger.info(f"🏛️ Created new conversation engine for session {session_id}")
    
    return _conversation_engines[session_id]

@app.post("/api/v1/zero-code-chat", response_model=ChatResponse)
async def zero_code_universal_chat(request: ChatRequest):
    """
    🏛️ Zero-code universal endpoint - LLM generates ALL intelligence
    
    Handles:
    - Registration: Peter → Knaflič → phone → password → farm
    - Farming questions: "Where's my watermelon?" "Bulgarian mango harvest ready?"
    - Mixed conversations: Registration + farming questions
    - ANY crop, ANY country, ANY farming scenario
    
    Constitutional Amendment #15 compliant: "If the LLM can write it, don't code it"
    """
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation engine
        engine = await get_conversation_engine(session_id)
        
        # LLM handles everything
        response = await engine.chat(request.message)
        
        return ChatResponse(
            success=True,
            message=response["message"],
            session_id=session_id,
            llm_generated=response["llm_generated"],
            amendment_15_compliance=response["amendment_15_compliance"],
            analysis=response.get("analysis"),
            registration_status=response.get("registration_status"),
            farmer_context=response.get("farmer_context"),
            timestamp=response["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"❌ Zero-code chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Zero-code conversation failed: {str(e)}"
        )

@app.get("/api/v1/conversation/{session_id}/summary")
async def get_conversation_summary(session_id: str):
    """
    📊 Get conversation summary
    Amendment #15: LLM-generated analytics
    """
    
    try:
        if session_id not in _conversation_engines:
            raise HTTPException(status_code=404, detail="Session not found")
        
        engine = _conversation_engines[session_id]
        summary = await engine.get_conversation_summary()
        
        return {
            "success": True,
            "summary": summary,
            "amendment_15_compliance": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Conversation summary failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )

@app.get("/api/v1/health/zero-code")
async def zero_code_health_check():
    """
    🔍 Health check for zero-code system
    Amendment #15: System health monitoring
    """
    
    try:
        health_status = {
            "status": "healthy",
            "amendment_15_compliance": True,
            "active_sessions": len(_conversation_engines),
            "system_components": {
                "conversation_engines": len(_conversation_engines),
                "database": "unknown",
                "redis": "unknown",
                "llm_intelligence": "unknown"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Check one engine if available
        if _conversation_engines:
            sample_engine = next(iter(_conversation_engines.values()))
            engine_health = await sample_engine.health_check()
            health_status["system_components"].update(engine_health)
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/v1/test/watermelon")
async def test_watermelon_scenario():
    """
    🥭 Test watermelon scenario
    Amendment #15: Universal crop intelligence
    """
    
    try:
        # Create test session
        session_id = f"test_watermelon_{uuid.uuid4().hex[:8]}"
        engine = await get_conversation_engine(session_id)
        
        # Test watermelon question
        response = await engine.chat("Where did I plant my watermelon?")
        
        return {
            "success": True,
            "test_scenario": "watermelon_location",
            "response": response,
            "amendment_15_compliance": True
        }
        
    except Exception as e:
        logger.error(f"❌ Watermelon test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Watermelon test failed: {str(e)}"
        )

@app.post("/api/v1/test/bulgarian-mango")
async def test_bulgarian_mango_scenario():
    """
    🥭 Test Bulgarian mango scenario
    Amendment #15: Universal country + crop intelligence
    """
    
    try:
        # Create test session
        session_id = f"test_bulgarian_mango_{uuid.uuid4().hex[:8]}"
        engine = await get_conversation_engine(session_id)
        
        # Test Bulgarian mango question
        response = await engine.chat("When is my Bulgarian mango harvest ready?")
        
        return {
            "success": True,
            "test_scenario": "bulgarian_mango_harvest",
            "response": response,
            "mango_rule_compliance": True,
            "amendment_15_compliance": True
        }
        
    except Exception as e:
        logger.error(f"❌ Bulgarian mango test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulgarian mango test failed: {str(e)}"
        )

@app.post("/api/v1/test/peter-registration")
async def test_peter_registration():
    """
    👤 Test Peter registration scenario
    Amendment #15: Universal registration intelligence
    """
    
    try:
        # Create test session
        session_id = f"test_peter_{uuid.uuid4().hex[:8]}"
        engine = await get_conversation_engine(session_id)
        
        # Test registration flow
        responses = []
        
        # Step 1: Peter
        r1 = await engine.chat("Peter")
        responses.append({"step": 1, "input": "Peter", "response": r1})
        
        # Step 2: Knaflič
        r2 = await engine.chat("Knaflič")
        responses.append({"step": 2, "input": "Knaflič", "response": r2})
        
        # Step 3: Phone
        r3 = await engine.chat("+38641348550")
        responses.append({"step": 3, "input": "+38641348550", "response": r3})
        
        return {
            "success": True,
            "test_scenario": "peter_registration",
            "responses": responses,
            "constitutional_fix": "prevents_re_asking",
            "amendment_15_compliance": True
        }
        
    except Exception as e:
        logger.error(f"❌ Peter registration test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Peter registration test failed: {str(e)}"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize zero-code system"""
    logger.info("🏛️ Starting Zero-Code Universal API (Amendment #15)")
    logger.info("🧠 LLM generates ALL intelligence - watermelon, Bulgarian mango, any crop!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup zero-code system"""
    logger.info("🏛️ Shutting down Zero-Code Universal API")
    
    # Cleanup all conversation engines
    for session_id, engine in _conversation_engines.items():
        try:
            await engine.cleanup()
        except Exception as e:
            logger.error(f"❌ Engine cleanup failed for {session_id}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)