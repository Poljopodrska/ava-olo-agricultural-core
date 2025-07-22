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
import os
from datetime import datetime

from modules.chat.openai_chat import get_openai_chat
from modules.auth.routes import get_current_farmer
from modules.core.database_manager import get_db_manager
from modules.location.location_service import LocationService
from modules.weather.service import weather_service

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
    """Get enhanced farmer context for chat"""
    try:
        db_manager = get_db_manager()
        
        # Get farmer's location
        location_service = LocationService()
        location_data = await location_service.get_farmer_location(farmer_id)
        
        # Get farmer's fields with last task
        query = """
        SELECT f.field_id, f.name, f.size_hectares, f.crop_type,
               t.task_description, t.completed_at
        FROM fields f
        LEFT JOIN LATERAL (
            SELECT task_description, completed_at
            FROM field_tasks
            WHERE field_id = f.field_id
            ORDER BY completed_at DESC
            LIMIT 1
        ) t ON true
        WHERE f.farmer_id = %s
        ORDER BY f.name
        """
        
        result = db_manager.execute_query(query, (farmer_id,))
        
        fields = []
        if result and result.get('rows'):
            for row in result['rows']:
                last_task = "No tasks yet"
                if row[4]:  # task_description exists
                    days_ago = (datetime.now() - row[5]).days if row[5] else 0
                    last_task = f"{row[4]} ({days_ago} days ago)"
                
                fields.append({
                    "id": row[0],
                    "name": row[1] or f"Field {row[0]}",
                    "hectares": float(row[2]) if row[2] else 0,
                    "crop": row[3] or "Not planted",
                    "last_task": last_task
                })
        
        # Format location from location data
        location_display = "Unknown location"
        lat, lon = None, None
        if location_data:
            city = location_data.get('city', '')
            country = location_data.get('country', '')
            if city and country:
                location_display = f"{city}, {country}"
            elif city:
                location_display = city
            # Get coordinates for weather
            lat = location_data.get('lat')
            lon = location_data.get('lon')
        
        # Get current weather
        weather_data = None
        if lat and lon:
            weather_data = await weather_service.get_current_weather(lat, lon)
        else:
            # Use Ljubljana as default
            weather_data = await weather_service.get_current_weather()
        
        context = {
            "fields": fields,
            "location": location_display,
            "local_time": datetime.now().strftime("%H:%M"),
            "local_date": datetime.now().strftime("%B %d, %Y")
        }
        
        # Add weather data to context
        if weather_data:
            context["weather"] = weather_data.get('description', 'Unknown')
            context["temperature"] = weather_data.get('raw_temp', 'Unknown')
            context["humidity"] = weather_data.get('raw_humidity', 'Unknown')
            context["weather_proof"] = weather_data.get('proof', {})
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting farmer context: {e}")
        return {
            "fields": [],
            "location": "Unknown",
            "local_time": datetime.now().strftime("%H:%M"),
            "local_date": datetime.now().strftime("%B %d, %Y")
        }

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

@router.get("/status")
async def chat_status():
    """Get chat service connection status"""
    try:
        chat_service = get_openai_chat()
        
        return {
            "connected": chat_service.connected,
            "has_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "api_key_prefix": os.getenv("OPENAI_API_KEY", "")[:7] + "..." if os.getenv("OPENAI_API_KEY") else None,
            "model": chat_service.model,
            "temperature": 0.85,
            "max_history": chat_service.max_history
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "connected": False,
            "has_api_key": False,
            "error": str(e)
        }

@router.get("/debug")
async def chat_debug():
    """Debug endpoint to check chat configuration"""
    try:
        chat_service = get_openai_chat()
        api_key = os.getenv("OPENAI_API_KEY", "")
        
        return {
            "api_key_configured": bool(api_key),
            "api_key_length": len(api_key) if api_key else 0,
            "api_key_prefix": api_key[:7] + "..." if api_key else None,
            "api_key_suffix": "..." + api_key[-4:] if api_key else None,
            "temperature": 0.85,
            "presence_penalty": 0.6,
            "frequency_penalty": 0.3,
            "model": chat_service.model,
            "connected": chat_service.connected,
            "conversation_count": len(chat_service.conversations),
            "max_history": chat_service.max_history,
            "environment": "production" if os.getenv("ENVIRONMENT") == "production" else "development"
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {
            "error": str(e),
            "api_key_configured": False,
            "connected": False
        }