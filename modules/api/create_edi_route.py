#!/usr/bin/env python3
"""
Create Edi Kante in the database
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fix", tags=["fix"])

@router.post("/create-edi")
async def create_edi_kante():
    """Create Edi Kante in the farmers table"""
    try:
        # Check if farmer 49 exists
        check_query = "SELECT farmer_id, name FROM farmers WHERE farmer_id = 49"
        check_result = execute_simple_query(check_query, ())
        
        if check_result.get('success') and check_result.get('rows'):
            return JSONResponse(content={
                "success": False,
                "message": f"Farmer 49 already exists: {check_result['rows'][0][1]}"
            })
        
        # Create Edi Kante
        insert_query = """
        INSERT INTO farmers (
            farmer_id,
            name,
            username,
            whatsapp_number,
            email,
            password_hash,
            created_at,
            language_preference
        ) VALUES (
            49,
            'Edi Kante',
            '+38640123449',
            '+38640123449',
            'edi.kante@example.com',
            '$2b$12$dummy.hash.for.edi.kante',
            NOW(),
            'sl'
        )
        """
        
        insert_result = execute_simple_query(insert_query, ())
        
        if not insert_result.get('success'):
            return JSONResponse(content={
                "success": False,
                "error": "Failed to create farmer",
                "details": str(insert_result.get('error'))
            }, status_code=500)
        
        # Update orphaned messages
        update_query = """
        UPDATE chat_messages 
        SET wa_phone_number = '+38640123449'
        WHERE wa_phone_number = '+farmer_49'
        """
        update_result = execute_simple_query(update_query, ())
        messages_updated = update_result.get('rowcount', 0) if update_result else 0
        
        # Verify creation
        verify_query = """
        SELECT farmer_id, name, username, whatsapp_number 
        FROM farmers 
        WHERE farmer_id = 49
        """
        verify_result = execute_simple_query(verify_query, ())
        
        if verify_result.get('success') and verify_result.get('rows'):
            farmer = verify_result['rows'][0]
            return JSONResponse(content={
                "success": True,
                "message": "Edi Kante created successfully",
                "farmer": {
                    "farmer_id": farmer[0],
                    "name": farmer[1],
                    "username": farmer[2],
                    "whatsapp_number": farmer[3]
                },
                "messages_updated": messages_updated
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Creation seemed to work but verification failed"
            }, status_code=500)
            
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)