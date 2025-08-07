#!/usr/bin/env python3
"""
Direct endpoint to fix Edi's WhatsApp number without auth
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fix", tags=["fix"])

@router.get("/edi-whatsapp")
async def fix_edi_whatsapp():
    """Directly fix Edi Kante's WhatsApp number"""
    try:
        # Directly update Edi's record (farmer_id = 49)
        farmer_id = 49
        new_whatsapp = "+38640000049"  # Slovenia format
        
        # First check current status
        check_query = """
        SELECT farmer_id, name, whatsapp_number
        FROM farmers
        WHERE farmer_id = %s
        """
        result = execute_simple_query(check_query, (farmer_id,))
        
        if result.get('success') and result.get('rows'):
            row = result['rows'][0]
            current_whatsapp = row[2]
            farmer_name = row[1]
            
            if not current_whatsapp:
                # Update farmer record
                update_query = """
                UPDATE farmers
                SET whatsapp_number = %s
                WHERE farmer_id = %s
                """
                update_result = execute_simple_query(update_query, (new_whatsapp, farmer_id))
                
                if update_result.get('success'):
                    # Also update any existing messages from +farmer_49 format
                    old_format = f"+farmer_{farmer_id}"
                    msg_update_query = """
                    UPDATE chat_messages
                    SET wa_phone_number = %s
                    WHERE wa_phone_number = %s
                    """
                    msg_result = execute_simple_query(msg_update_query, (new_whatsapp, old_format))
                    
                    return JSONResponse(content={
                        "success": True,
                        "farmer": farmer_name,
                        "message": f"WhatsApp number set to {new_whatsapp}",
                        "messages_updated": msg_result.get('rowcount', 0) if msg_result else 0
                    })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "error": "Failed to update WhatsApp number"
                    }, status_code=500)
            else:
                # Also fix messages even if WhatsApp exists
                old_format = f"+farmer_{farmer_id}"
                msg_update_query = """
                UPDATE chat_messages
                SET wa_phone_number = %s
                WHERE wa_phone_number = %s
                """
                msg_result = execute_simple_query(msg_update_query, (current_whatsapp, old_format))
                
                return JSONResponse(content={
                    "success": True,
                    "farmer": farmer_name,
                    "message": f"Already has WhatsApp: {current_whatsapp}",
                    "whatsapp_number": current_whatsapp,
                    "messages_fixed": msg_result.get('rowcount', 0) if msg_result else 0
                })
        else:
            return JSONResponse(content={
                "success": False,
                "error": f"Farmer {farmer_id} not found"
            }, status_code=404)
            
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)