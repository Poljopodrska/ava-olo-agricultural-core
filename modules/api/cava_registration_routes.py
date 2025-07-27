#!/usr/bin/env python3
"""
CAVA Registration API Routes
Intelligent registration endpoints using GPT-3.5
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from modules.cava.cava_registration_engine import get_cava_registration_engine

logger = logging.getLogger(__name__)

router = APIRouter()

# Get CAVA registration engine
cava_registration = get_cava_registration_engine()

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class SessionStatusResponse(BaseModel):
    session_exists: bool
    fields_collected: Optional[Dict[str, bool]] = None
    completed: Optional[bool] = None
    farmer_id: Optional[int] = None
    conversation_length: Optional[int] = None
    language: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

@router.post("/api/v1/registration/initialize")
async def initialize_registration_session(request: dict):
    """Initialize a new registration session with auto-greeting"""
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Initialize session with greeting
        cava_registration.sessions[session_id] = {
            'first_name': None,
            'last_name': None,
            'wa_phone_number': None,
            'password': None,
            'password_confirmation': None,
            'language': None,
            'conversation_history': [{
                'role': 'assistant',
                'content': "Hi! I'm AVA, let me help you register. What is your name? 😊",
                'timestamp': datetime.utcnow().isoformat()
            }],
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"🔄 Initialized registration session: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "greeting": "Hi! I'm AVA, let me help you register. What is your name? 😊"
        }
        
    except Exception as e:
        logger.error(f"❌ Session initialization error: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization error: {str(e)}")

@router.post("/api/v1/registration/cava")
async def cava_registration_chat(request: ChatMessageRequest):
    """CAVA-powered registration endpoint"""
    try:
        logger.info(f"🤖 CAVA Registration: session={request.session_id}, message_length={len(request.message)}")
        
        # Process with CAVA
        result = await cava_registration.process_registration_message(
            request.session_id,
            request.message
        )
        
        logger.info(f"📊 Registration result: success={result.get('success', False)}, complete={result.get('registration_complete', False)}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ CAVA Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@router.get("/api/v1/registration/status/{session_id}")
async def registration_status(session_id: str) -> SessionStatusResponse:
    """Check registration progress"""
    try:
        status = cava_registration.get_session_status(session_id)
        return SessionStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

@router.delete("/api/v1/registration/session/{session_id}")
async def clear_registration_session(session_id: str):
    """Clear registration session"""
    try:
        cleared = cava_registration.clear_session(session_id)
        return {
            "success": cleared,
            "message": "Session cleared" if cleared else "Session not found"
        }
        
    except Exception as e:
        logger.error(f"❌ Session clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")

@router.get("/api/v1/registration/test-connection")
async def test_registration_connection():
    """Test CAVA registration system"""
    try:
        # Test basic functionality
        test_session = "test-" + str(hash("test"))
        
        result = await cava_registration.process_registration_message(
            test_session,
            "test connection"
        )
        
        # Clean up test session
        cava_registration.clear_session(test_session)
        
        return {
            "success": True,
            "cava_connected": result.get('ai_connected', False),
            "model_used": result.get('model_used', 'fallback'),
            "message": "CAVA registration system is operational"
        }
        
    except Exception as e:
        logger.error(f"❌ Connection test error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "CAVA registration system has issues"
        }

@router.post("/api/v1/registration/demo")
async def demo_registration():
    """Demo registration flow for testing"""
    try:
        demo_session = "demo-" + str(hash("demo"))
        
        # Simulate demo conversation
        demo_messages = [
            "I want to register",
            "My name is Peter Horvat",
            "+38641234567",
            "mypassword123",
            "mypassword123"
        ]
        
        conversation = []
        for message in demo_messages:
            result = await cava_registration.process_registration_message(
                demo_session,
                message
            )
            
            conversation.append({
                "user": message,
                "cava": result.get('response', 'No response'),
                "collected": result.get('collected_fields', {}),
                "complete": result.get('registration_complete', False)
            })
            
            if result.get('registration_complete'):
                break
        
        # Get final status
        final_status = cava_registration.get_session_status(demo_session)
        
        return {
            "success": True,
            "conversation": conversation,
            "final_status": final_status,
            "farmer_id": final_status.get('farmer_id'),
            "message": "Demo registration completed successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        raise HTTPException(status_code=500, detail=f"Demo error: {str(e)}")