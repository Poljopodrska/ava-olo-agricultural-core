#!/usr/bin/env python3
"""
Dashboard Chat Routes with Farmer-Specific Context
Provides chat functionality for authenticated farmers in the dashboard
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict
from modules.auth.routes import get_current_farmer
from modules.cava.chat_engine import get_cava_engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["dashboard-chat"])

class DashboardChatRequest(BaseModel):
    content: str

@router.post("/message")
async def dashboard_chat_message(chat_request: DashboardChatRequest, request: Request):
    """Send chat message with authenticated farmer context"""
    try:
        # Get authenticated farmer
        farmer = await get_current_farmer(request)
        if not farmer:
            return {
                "success": False,
                "connected": False,
                "response": "Please sign in to use chat",
                "error": "Not authenticated"
            }
        
        message = chat_request.content.strip()
        if not message:
            return {
                "success": False,
                "connected": True,
                "response": "Please provide a message",
                "error": "Empty message"
            }
        
        # Get farmer's detailed context
        farmer_context = await get_farmer_chat_context(farmer['farmer_id'])
        
        # Get farmer's WhatsApp number for storing messages
        wa_phone = farmer_context.get("whatsapp_number")
        if not wa_phone:
            # Use a default format if no WhatsApp number
            wa_phone = f"+farmer_{farmer['farmer_id']}"
        
        # Store user message in database using simple_db for reliability
        from modules.core.simple_db import execute_simple_query
        
        try:
            # Store user message
            store_user_msg = """
            INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
            VALUES (%s, %s, %s, NOW())
            """
            execute_simple_query(store_user_msg, (wa_phone, 'user', message))
        except Exception as e:
            logger.warning(f"Could not store user message: {e}")
        
        # Use CAVA engine for intelligent responses
        cava_engine = get_cava_engine()
        
        # Ensure engine is initialized
        if not cava_engine.initialized:
            await cava_engine.initialize()
        
        # Create session ID based on farmer
        session_id = f"farmer_{farmer['farmer_id']}_dashboard"
        
        # Get GPT response with farmer context
        result = await cava_engine.chat(
            session_id=session_id,
            message=message,
            farmer_context=farmer_context
        )
        
        response_text = result.get("response", "I'm here to help with your farming questions!")
        
        # Store assistant response in database
        try:
            store_assistant_msg = """
            INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
            VALUES (%s, %s, %s, NOW())
            """
            execute_simple_query(store_assistant_msg, (wa_phone, 'assistant', response_text))
        except Exception as e:
            logger.warning(f"Could not store assistant message: {e}")
        
        return {
            "success": True,
            "connected": True,
            "response": response_text,
            "model": result.get("model", "gpt-3.5-turbo"),
            "tokens_used": result.get("tokens_used", 0),
            "farmer_context_used": True,
            "farmer_name": farmer_context.get("farmer_name", farmer["name"])
        }
        
    except Exception as e:
        logger.error(f"Dashboard chat error for farmer {farmer.get('farmer_id') if farmer else 'unknown'}: {e}")
        return {
            "success": False,
            "connected": False,
            "response": "I'm having trouble connecting right now. Please try again in a moment.",
            "error": str(e)
        }

async def get_farmer_chat_context(farmer_id: int) -> Dict:
    """Get comprehensive farmer context for chat"""
    try:
        from modules.core.database_manager import get_db_manager
        
        db_manager = get_db_manager()
        
        # Get farmer details
        farmer_query = """
        SELECT 
            farmer_id,
            name,
            email,
            whatsapp_number
        FROM farmers 
        WHERE farmer_id = %s
        """
        
        farmer_result = await db_manager.execute_query(farmer_query, (farmer_id,))
        
        farmer_data = {}
        if farmer_result and len(farmer_result) > 0:
            row = farmer_result[0]
            farmer_data = {
                "farmer_id": row[0],
                "name": row[1],
                "email": row[2],
                "whatsapp_number": row[3]
            }
        
        # Get farmer's fields
        fields_query = """
        SELECT 
            id,
            field_name,
            area_ha
        FROM fields
        WHERE farmer_id = %s
        ORDER BY field_name
        """
        
        fields_result = await db_manager.execute_query(fields_query, (farmer_id,))
        
        fields = []
        if fields_result:
            for row in fields_result:
                fields.append({
                    "id": row[0],
                    "name": row[1] or f"Field {row[0]}",
                    "hectares": float(row[2]) if row[2] else 0
                })
        
        # Get recent chat history for context
        chat_query = """
        SELECT content, role
        FROM chat_messages
        WHERE wa_phone_number = %s
        ORDER BY timestamp DESC
        LIMIT 5
        """
        
        chat_history = []
        if farmer_data.get("whatsapp_number"):
            chat_result = await db_manager.execute_query(chat_query, (farmer_data["whatsapp_number"],))
            if chat_result:
                for row in chat_result:
                    chat_history.append({
                        "content": row[0],
                        "role": row[1]
                    })
        
        return {
            "farmer_name": farmer_data.get("name", "Farmer"),
            "farmer_id": farmer_id,
            "fields": fields,
            "recent_messages": chat_history,
            "summary": {
                "total_fields": len(fields),
                "total_hectares": sum(f['hectares'] for f in fields),
                "main_crops": list(set(f['crop'] for f in fields if f['crop'] != "Not planted"))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting farmer context for {farmer_id}: {e}")
        return {
            "farmer_name": "Farmer",
            "farmer_id": farmer_id,
            "fields": [],
            "recent_messages": [],
            "summary": {"total_fields": 0, "total_hectares": 0, "main_crops": []}
        }

@router.get("/status")
async def get_chat_status(request: Request):
    """Get chat connection status for authenticated farmer"""
    try:
        # Check if farmer is authenticated
        farmer = await get_current_farmer(request)
        if not farmer:
            return {
                "connected": False,
                "authenticated": False,
                "message": "Please sign in to use chat"
            }
        
        # Test CAVA engine connection
        cava_engine = get_cava_engine()
        
        if not cava_engine.initialized:
            await cava_engine.initialize()
        
        # Test actual OpenAI connection
        test_response = await cava_engine.chat(
            session_id=f"test_{farmer['farmer_id']}",
            message="test",
            farmer_context={"farmer_name": farmer["name"]}
        )
        
        if test_response and test_response.get("response"):
            return {
                "connected": True,
                "authenticated": True,
                "has_api_key": True,
                "farmer_name": farmer["name"],
                "model": "gpt-3.5-turbo",
                "message": "Connected to GPT-3.5"
            }
        else:
            return {
                "connected": False,
                "authenticated": True,
                "has_api_key": False,
                "farmer_name": farmer["name"],
                "message": "Chat AI is not connected"
            }
            
    except Exception as e:
        logger.error(f"Chat status check error: {e}")
        return {
            "connected": False,
            "authenticated": False,
            "has_api_key": False,
            "message": "Chat service unavailable",
            "error": str(e)
        }