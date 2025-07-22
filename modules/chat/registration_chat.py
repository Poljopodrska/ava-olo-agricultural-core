#!/usr/bin/env python3
"""
Registration Chat - Uses same mechanism as dashboard chat
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import uuid
import logging
from datetime import datetime
from modules.chat.openai_chat import get_openai_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["registration-chat"])

class ChatMessage(BaseModel):
    """Chat message model"""
    content: str

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    timestamp: str
    model: str
    connected: bool = True

@router.post("/registration/message")
async def send_registration_message(request: Request, message: ChatMessage):
    """Send message for registration - same pattern as dashboard"""
    try:
        # Get or create session ID - EXACT same as dashboard
        session_id = request.cookies.get("chat_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Registration context instead of farmer context
        registration_context = {
            "purpose": "registration",
            "fields_needed": ["first_name", "last_name", "whatsapp"],
            "instructions": "Help the user register by collecting their first name, last name, and WhatsApp number through natural conversation.",
            "local_time": datetime.now().strftime("%H:%M"),
            "local_date": datetime.now().strftime("%B %d, %Y")
        }
        
        # Get chat service - EXACT same as dashboard
        chat_service = get_openai_chat()
        
        # Send message and get response - EXACT same pattern
        response_data = await chat_service.send_message(
            session_id,
            message.content,
            registration_context
        )
        
        # Create response with session cookie - EXACT same as dashboard
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=response_data)
        response.set_cookie(
            key="chat_session_id",
            value=session_id,
            httponly=True,
            max_age=86400  # 24 hours
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Registration chat error: {e}")
        # Return same format as dashboard on error
        return {
            "response": "I'm having trouble connecting. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "model": "error",
            "connected": False
        }

@router.get("/registration/status")
async def registration_chat_status():
    """Check registration chat service status - same as dashboard"""
    try:
        chat_service = get_openai_chat()
        
        return {
            "status": "healthy",
            "connected": bool(chat_service.api_key),
            "has_api_key": bool(chat_service.api_key),
            "api_key_prefix": chat_service.api_key[:8] + "..." if chat_service.api_key else "Not configured",
            "model": chat_service.model
        }
        
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "has_api_key": False,
            "api_key_prefix": "Error",
            "model": "none",
            "error": str(e)
        }