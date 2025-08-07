#!/usr/bin/env python3
"""
Quick endpoint to check farmer's WhatsApp number
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from ..auth.routes import require_auth
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/farmer-phone")
async def get_farmer_phone(farmer: dict = Depends(require_auth)):
    """Get the farmer's WhatsApp number from database"""
    try:
        farmer_id = farmer.get('farmer_id')
        
        # Direct query to farmers table
        query = """
        SELECT farmer_id, name, whatsapp_number, email, username
        FROM farmers
        WHERE farmer_id = %s
        """
        result = execute_simple_query(query, (farmer_id,))
        
        if result.get('success') and result.get('rows'):
            row = result['rows'][0]
            whatsapp = row[2]
            
            # Check if there are messages with this WhatsApp number
            msg_count_query = """
            SELECT COUNT(*) FROM chat_messages WHERE wa_phone_number = %s
            """
            msg_result = execute_simple_query(msg_count_query, (whatsapp,)) if whatsapp else None
            msg_count = msg_result['rows'][0][0] if msg_result and msg_result.get('success') and msg_result.get('rows') else 0
            
            return JSONResponse(content={
                "success": True,
                "farmer_id": row[0],
                "name": row[1],
                "whatsapp_number": whatsapp,
                "email": row[3],
                "username": row[4],
                "messages_with_this_number": msg_count,
                "issue": "WhatsApp number is NULL or empty" if not whatsapp else None
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Farmer not found"
            })
            
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)