#!/usr/bin/env python3
"""
Endpoint to fix farmer's WhatsApp number
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from ..auth.routes import require_auth
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fix", tags=["fix"])

@router.post("/set-whatsapp")
async def set_farmer_whatsapp(farmer: dict = Depends(require_auth)):
    """Set a WhatsApp number for the current farmer if they don't have one"""
    try:
        farmer_id = farmer.get('farmer_id')
        
        # Check current WhatsApp number
        check_query = """
        SELECT farmer_id, name, whatsapp_number
        FROM farmers
        WHERE farmer_id = %s
        """
        result = execute_simple_query(check_query, (farmer_id,))
        
        if result.get('success') and result.get('rows'):
            row = result['rows'][0]
            current_whatsapp = row[2]
            
            if not current_whatsapp:
                # Generate a WhatsApp number for this farmer
                # Using Slovenia format +386 40 XXX XXX
                new_whatsapp = f"+38640{str(farmer_id).zfill(6)}"
                
                # Update farmer record
                update_query = """
                UPDATE farmers
                SET whatsapp_number = %s
                WHERE farmer_id = %s
                """
                update_result = execute_simple_query(update_query, (new_whatsapp, farmer_id))
                
                if update_result.get('success'):
                    # Also update any existing messages from +farmer_ID format
                    old_format = f"+farmer_{farmer_id}"
                    msg_update_query = """
                    UPDATE chat_messages
                    SET wa_phone_number = %s
                    WHERE wa_phone_number = %s
                    """
                    msg_result = execute_simple_query(msg_update_query, (new_whatsapp, old_format))
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": f"WhatsApp number set to {new_whatsapp}",
                        "messages_updated": msg_result.get('rowcount', 0) if msg_result else 0
                    })
                else:
                    return JSONResponse(content={
                        "success": False,
                        "error": "Failed to update WhatsApp number"
                    }, status_code=500)
            else:
                return JSONResponse(content={
                    "success": True,
                    "message": f"Already has WhatsApp: {current_whatsapp}",
                    "whatsapp_number": current_whatsapp
                })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Farmer not found"
            }, status_code=404)
            
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)