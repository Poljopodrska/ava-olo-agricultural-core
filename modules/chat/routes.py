#!/usr/bin/env python3
"""
Chat API routes
Handles chat endpoints for OpenAI integration
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

from modules.chat.openai_chat import get_openai_chat
from modules.auth.routes import get_current_farmer
from modules.core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ChatMessage(BaseModel):
    """Chat message model"""
    content: str

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    timestamp: str
    model: str

async def get_farmer_context(farmer_id: int) -> dict:
    """Get farmer context for chat"""
    try:
        db_manager = get_db_manager()
        
        # Get farmer's fields
        query = """
        SELECT field_id, name, size_hectares, crop_type
        FROM fields
        WHERE farmer_id = %s
        ORDER BY name
        """
        
        result = db_manager.execute_query(query, (farmer_id,))
        
        fields = []
        if result and result.get('rows'):
            for row in result['rows']:
                fields.append({
                    "id": row[0],
                    "name": row[1] or f"Field {row[0]}",
                    "hectares": float(row[2]) if row[2] else 0,
                    "crop": row[3] or "Not planted"
                })
        
        return {"fields": fields}
        
    except Exception as e:
        logger.error(f"Error getting farmer context: {e}")
        return {"fields": []}

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(request: Request, message: ChatMessage):
    """Send message to OpenAI and get response"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get or create session ID
        session_id = request.cookies.get("chat_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get farmer context
        farmer_context = await get_farmer_context(farmer['farmer_id'])
        
        # Get chat service
        chat_service = get_openai_chat()
        
        # Send message and get response
        response_data = await chat_service.send_message(
            session_id,
            message.content,
            farmer_context
        )
        
        # Create response with session cookie
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=response_data)
        response.set_cookie(
            key="chat_session_id",
            value=session_id,
            httponly=True,
            max_age=86400  # 24 hours
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat service error")

@router.post("/clear")
async def clear_chat(request: Request):
    """Clear chat history for current session"""
    try:
        session_id = request.cookies.get("chat_session_id")
        
        if session_id:
            chat_service = get_openai_chat()
            chat_service.clear_conversation(session_id)
        
        return {"success": True, "message": "Chat history cleared"}
        
    except Exception as e:
        logger.error(f"Clear chat error: {e}")
        raise HTTPException(status_code=500, detail="Error clearing chat")

@router.get("/health")
async def chat_health():
    """Check chat service health"""
    try:
        chat_service = get_openai_chat()
        
        return {
            "status": "healthy",
            "service": "chat",
            "api_key_configured": bool(chat_service.api_key),
            "model": chat_service.model
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "chat",
            "error": str(e)
        }