#!/usr/bin/env python3
"""
Debug endpoints for chat issues
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from ..auth.routes import get_current_farmer, require_auth
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/chat-debug")
async def debug_chat_data(farmer: dict = Depends(require_auth)):
    """Debug endpoint to check farmer's chat data"""
    try:
        farmer_id = farmer.get('farmer_id')
        
        # 1. Check farmer's WhatsApp number
        farmer_query = """
        SELECT farmer_id, name, whatsapp_number, username, email
        FROM farmers
        WHERE farmer_id = %s
        """
        farmer_result = execute_simple_query(farmer_query, (farmer_id,))
        
        farmer_info = {}
        if farmer_result.get('success') and farmer_result.get('rows'):
            row = farmer_result['rows'][0]
            farmer_info = {
                "farmer_id": row[0],
                "name": row[1],
                "whatsapp_number": row[2],
                "username": row[3],
                "email": row[4]
            }
        
        # 2. Check messages with exact WhatsApp number
        wa_phone = farmer_info.get('whatsapp_number')
        exact_messages = []
        if wa_phone:
            msg_query = """
            SELECT wa_phone_number, role, LEFT(content, 50), timestamp
            FROM chat_messages
            WHERE wa_phone_number = %s
            ORDER BY timestamp DESC
            LIMIT 5
            """
            msg_result = execute_simple_query(msg_query, (wa_phone,))
            if msg_result.get('success') and msg_result.get('rows'):
                exact_messages = [
                    {
                        "phone": row[0],
                        "role": row[1],
                        "content_preview": row[2],
                        "timestamp": row[3].isoformat() if row[3] else None
                    }
                    for row in msg_result['rows']
                ]
        
        # 3. Check messages with old format
        old_format = f"+farmer_{farmer_id}"
        old_msg_query = """
        SELECT wa_phone_number, role, LEFT(content, 50), timestamp
        FROM chat_messages
        WHERE wa_phone_number = %s
        ORDER BY timestamp DESC
        LIMIT 5
        """
        old_result = execute_simple_query(old_msg_query, (old_format,))
        old_messages = []
        if old_result.get('success') and old_result.get('rows'):
            old_messages = [
                {
                    "phone": row[0],
                    "role": row[1],
                    "content_preview": row[2],
                    "timestamp": row[3].isoformat() if row[3] else None
                }
                for row in old_result['rows']
            ]
        
        # 4. Check ALL messages for this farmer (any format)
        all_msg_query = """
        SELECT DISTINCT wa_phone_number, COUNT(*)
        FROM chat_messages
        WHERE wa_phone_number LIKE %s OR wa_phone_number LIKE %s
        GROUP BY wa_phone_number
        """
        all_result = execute_simple_query(all_msg_query, (f"%{farmer_id}%", f"%farmer%"))
        all_formats = []
        if all_result.get('success') and all_result.get('rows'):
            all_formats = [
                {"format": row[0], "count": row[1]}
                for row in all_result['rows']
            ]
        
        # 5. Get most recent messages regardless of phone number
        recent_query = """
        SELECT wa_phone_number, role, LEFT(content, 50), timestamp
        FROM chat_messages
        ORDER BY timestamp DESC
        LIMIT 10
        """
        recent_result = execute_simple_query(recent_query, ())
        recent_messages = []
        if recent_result.get('success') and recent_result.get('rows'):
            recent_messages = [
                {
                    "phone": row[0],
                    "role": row[1],
                    "content_preview": row[2],
                    "timestamp": row[3].isoformat() if row[3] else None
                }
                for row in recent_result['rows']
            ]
        
        return JSONResponse(content={
            "success": True,
            "farmer_info": farmer_info,
            "whatsapp_search": wa_phone,
            "old_format_search": old_format,
            "messages_with_exact_whatsapp": exact_messages,
            "messages_with_old_format": old_messages,
            "all_phone_formats_found": all_formats,
            "most_recent_messages_in_db": recent_messages,
            "debug": {
                "farmer_from_auth": farmer,
                "has_whatsapp": bool(wa_phone),
                "total_exact_messages": len(exact_messages),
                "total_old_format_messages": len(old_messages)
            }
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)