#!/usr/bin/env python3
"""
Chat History Routes for Farmer Dashboard
Provides chat message history filtering and farmer-specific data
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List, Dict
from modules.core.database_manager import get_db_manager
from modules.core.simple_db import execute_simple_query
from modules.auth.routes import get_current_farmer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat-history"])

@router.get("/history")
async def get_farmer_chat_history(request: Request, limit: int = 100):
    """Get last N chat messages for authenticated farmer"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get farmer's WhatsApp number (which is their username)
        farmer_query = """
        SELECT COALESCE(whatsapp_number, wa_phone_number) as whatsapp_number
        FROM farmers 
        WHERE id = %s
        """
        
        farmer_result = execute_simple_query(farmer_query, (farmer['farmer_id'],))
        
        # Every farmer MUST have a WhatsApp number since it's their username
        if farmer_result.get('success') and farmer_result.get('rows') and farmer_result['rows'][0][0]:
            wa_phone_number = farmer_result['rows'][0][0]
            logger.info(f"Found WhatsApp for farmer {farmer['farmer_id']}: {wa_phone_number}")
        else:
            # Auto-fix: Set WhatsApp number if missing
            logger.warning(f"Farmer {farmer['farmer_id']} has no WhatsApp number, auto-fixing...")
            
            # Get username to use as WhatsApp if it looks like a phone
            username_query = "SELECT COALESCE(whatsapp_number, wa_phone_number) FROM farmers WHERE id = %s"
            username_result = execute_simple_query(username_query, (farmer['farmer_id'],))
            
            if username_result.get('success') and username_result.get('rows'):
                username = username_result['rows'][0][0]
                if username and username.startswith('+'):
                    wa_phone_number = username
                else:
                    wa_phone_number = f"+38640{str(farmer['farmer_id']).zfill(6)}"
            else:
                wa_phone_number = f"+38640{str(farmer['farmer_id']).zfill(6)}"
            
            # Update farmer record with the WhatsApp number
            update_query = "UPDATE farmers SET whatsapp_number = %s WHERE id = %s"
            execute_simple_query(update_query, (wa_phone_number, farmer['farmer_id']))
            
            # Also update any old messages
            old_format = f"+farmer_{farmer['farmer_id']}"
            msg_update_query = "UPDATE chat_messages SET wa_phone_number = %s WHERE wa_phone_number = %s"
            execute_simple_query(msg_update_query, (wa_phone_number, old_format))
            
            logger.info(f"Auto-fixed WhatsApp for farmer {farmer['farmer_id']}: {wa_phone_number}")
        
        logger.info(f"Looking for messages with wa_phone_number: {wa_phone_number}")
        
        # Get chat messages filtered by farmer's WhatsApp number
        # Using subquery to get last N messages in correct order (oldest to newest)
        query = """
        SELECT role, content, timestamp FROM (
            SELECT 
                role,
                content,
                timestamp
            FROM chat_messages
            WHERE wa_phone_number = %s
            ORDER BY timestamp DESC
            LIMIT %s
        ) AS recent_messages
        ORDER BY timestamp ASC
        """
        
        result = execute_simple_query(query, (wa_phone_number, limit))
        
        messages = []
        if result.get('success') and result.get('rows'):
            for row in result['rows']:
                messages.append({
                    "role": row[0],
                    "content": row[1],
                    "timestamp": row[2].isoformat() if row[2] else None
                })
        
        return {
            "status": "success",
            "data": {
                "messages": messages,
                "farmer_id": farmer['farmer_id'],
                "farmer_name": farmer['name'],
                "wa_phone_number": wa_phone_number,
                "total_messages": len(messages)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        # Return empty history instead of failing
        return {
            "status": "success",
            "data": {
                "messages": [],
                "farmer_id": farmer.get('farmer_id') if farmer else None,
                "message": "Error retrieving chat history"
            }
        }

@router.get("/farmer-context")
async def get_farmer_context_for_chat(request: Request):
    """Get farmer context for personalized chat responses"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        db_manager = get_db_manager()
        
        # Get farmer details
        farmer_query = """
        SELECT 
            farmer_id,
            name,
            email,
            whatsapp_number,
            created_at
        FROM farmers 
        WHERE farmer_id = %s
        """
        
        farmer_result = await db_manager.execute_query(farmer_query, (farmer['farmer_id'],))
        
        farmer_data = None
        if farmer_result and len(farmer_result) > 0:
            row = farmer_result[0]
            farmer_data = {
                "farmer_id": row[0],
                "name": row[1],
                "email": row[2],
                "whatsapp_number": row[3],
                "created_at": row[4].isoformat() if row[4] else None
            }
        
        # Get farmer's fields
        fields_query = """
        SELECT 
            field_id,
            name,
            size_hectares,
            crop_type,
            status
        FROM fields
        WHERE farmer_id = %s
        ORDER BY name
        """
        
        fields_result = await db_manager.execute_query(fields_query, (farmer['farmer_id'],))
        
        fields = []
        if fields_result:
            for row in fields_result:
                fields.append({
                    "id": row[0],
                    "name": row[1] or f"Field {row[0]}",
                    "hectares": float(row[2]) if row[2] else 0,
                    "crop": row[3] or "Not planted",
                    "status": row[4] or "active"
                })
        
        return {
            "status": "success",
            "data": {
                "farmer": farmer_data,
                "fields": fields,
                "summary": {
                    "total_fields": len(fields),
                    "total_hectares": sum(f['hectares'] for f in fields)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting farmer context: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving farmer context")

@router.post("/send-message")
async def send_farmer_message(request: Request):
    """Send a message as authenticated farmer and get AI response"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get request body
        body = await request.json()
        message = body.get("content", "").strip()
        
        if not message:
            raise HTTPException(status_code=400, detail="Message content required")
        
        # Get farmer's WhatsApp number
        db_manager = get_db_manager()
        farmer_query = """
        SELECT whatsapp_number 
        FROM farmers 
        WHERE farmer_id = %s
        """
        
        farmer_result = await db_manager.execute_query(farmer_query, (farmer['farmer_id'],))
        
        if not farmer_result or len(farmer_result) == 0:
            raise HTTPException(status_code=404, detail="Farmer WhatsApp number not found")
        
        wa_phone_number = farmer_result[0][0]
        
        # Import chat functionality
        from modules.api.chat_routes import chat_message_endpoint
        
        # Call the existing chat endpoint with farmer context
        chat_request = {
            "content": message,
            "wa_phone_number": wa_phone_number,
            "farmer_id": farmer['farmer_id']
        }
        
        response = await chat_message_endpoint(chat_request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending farmer message: {e}")
        raise HTTPException(status_code=500, detail="Error sending message")