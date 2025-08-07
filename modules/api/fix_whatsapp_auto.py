#!/usr/bin/env python3
"""
Auto-fix WhatsApp numbers for farmers without them
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fix", tags=["fix"])

async def get_farmer_from_cookie(request: Request):
    """Get farmer from cookie"""
    farmer_id = request.cookies.get("farmer_id")
    if not farmer_id:
        return None
    return {"farmer_id": int(farmer_id)}

@router.post("/auto-whatsapp")
async def auto_fix_whatsapp(request: Request):
    """Auto-fix WhatsApp number for logged-in farmer"""
    try:
        # Get farmer from cookie
        farmer_id = request.cookies.get("farmer_id")
        if not farmer_id:
            return JSONResponse(content={
                "success": False,
                "error": "Not logged in"
            }, status_code=401)
        
        farmer_id = int(farmer_id)
        
        # Check current WhatsApp number
        check_query = """
        SELECT farmer_id, name, whatsapp_number, username
        FROM farmers
        WHERE farmer_id = %s
        """
        result = execute_simple_query(check_query, (farmer_id,))
        
        if result.get('success') and result.get('rows'):
            row = result['rows'][0]
            current_whatsapp = row[2]
            farmer_name = row[1]
            username = row[3]
            
            if not current_whatsapp:
                # Generate a WhatsApp number - use username if it looks like a phone
                if username and username.startswith('+'):
                    new_whatsapp = username
                else:
                    # Generate based on farmer ID
                    new_whatsapp = f"+38640{str(farmer_id).zfill(6)}"
                
                # Update farmer record
                update_query = """
                UPDATE farmers
                SET whatsapp_number = %s
                WHERE farmer_id = %s
                """
                update_result = execute_simple_query(update_query, (new_whatsapp, farmer_id))
                
                if update_result.get('success'):
                    # Fix any messages with old format
                    old_format = f"+farmer_{farmer_id}"
                    msg_update_query = """
                    UPDATE chat_messages
                    SET wa_phone_number = %s
                    WHERE wa_phone_number = %s
                    """
                    msg_result = execute_simple_query(msg_update_query, (new_whatsapp, old_format))
                    
                    return JSONResponse(content={
                        "success": True,
                        "farmer_name": farmer_name,
                        "whatsapp_set": new_whatsapp,
                        "messages_updated": msg_result.get('rowcount', 0) if msg_result else 0
                    })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "error": "Failed to update WhatsApp number"
                    }, status_code=500)
            else:
                # Already has WhatsApp, just fix messages
                old_format = f"+farmer_{farmer_id}"
                msg_update_query = """
                UPDATE chat_messages
                SET wa_phone_number = %s
                WHERE wa_phone_number = %s
                """
                msg_result = execute_simple_query(msg_update_query, (current_whatsapp, old_format))
                
                return JSONResponse(content={
                    "success": True,
                    "farmer_name": farmer_name,
                    "already_has": current_whatsapp,
                    "messages_fixed": msg_result.get('rowcount', 0) if msg_result else 0
                })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Farmer not found in database"
            }, status_code=404)
            
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)