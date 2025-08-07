#!/usr/bin/env python3
"""
Test endpoint to check chat_messages table structure
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from ..auth.routes import require_auth
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["test"])

@router.get("/chat-table-structure")
async def test_chat_table(farmer: dict = Depends(require_auth)):
    """Check chat_messages table structure and test queries"""
    try:
        results = {}
        
        # 1. Check if chat_messages table exists
        check_table = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'chat_messages'
        )
        """
        table_result = execute_simple_query(check_table, ())
        results["table_exists"] = table_result.get('rows')[0][0] if table_result.get('success') and table_result.get('rows') else False
        
        # 2. Get column names and types
        if results["table_exists"]:
            columns_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'chat_messages'
            ORDER BY ordinal_position
            """
            columns_result = execute_simple_query(columns_query, ())
            
            if columns_result.get('success') and columns_result.get('rows'):
                results["columns"] = []
                for row in columns_result['rows']:
                    results["columns"].append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2]
                    })
            
            # 3. Count total messages
            count_query = "SELECT COUNT(*) FROM chat_messages"
            count_result = execute_simple_query(count_query, ())
            results["total_messages"] = count_result['rows'][0][0] if count_result.get('success') and count_result.get('rows') else 0
            
            # 4. Get sample messages for this farmer
            farmer_id = farmer.get('farmer_id')
            wa_phone = f"+farmer_{farmer_id}"
            
            # Try different phone number formats
            sample_query = """
            SELECT wa_phone_number, role, content, timestamp
            FROM chat_messages
            WHERE wa_phone_number = %s OR wa_phone_number = %s
            ORDER BY timestamp DESC
            LIMIT 5
            """
            sample_result = execute_simple_query(sample_query, (wa_phone, f"farmer_{farmer_id}"))
            
            if sample_result.get('success') and sample_result.get('rows'):
                results["sample_messages"] = []
                for row in sample_result['rows']:
                    results["sample_messages"].append({
                        "wa_phone": row[0],
                        "role": row[1],
                        "content": row[2][:50] + "..." if row[2] else None,
                        "timestamp": str(row[3]) if row[3] else None
                    })
            else:
                results["sample_messages"] = []
                results["sample_error"] = sample_result.get('error')
            
            # 5. Get all unique wa_phone_number values to see what format is being used
            unique_phones_query = """
            SELECT DISTINCT wa_phone_number 
            FROM chat_messages 
            LIMIT 20
            """
            phones_result = execute_simple_query(unique_phones_query, ())
            
            if phones_result.get('success') and phones_result.get('rows'):
                results["unique_phone_formats"] = [row[0] for row in phones_result['rows']]
        
        return JSONResponse(content={
            "success": True,
            "farmer_id": farmer_id,
            "expected_wa_phone": wa_phone,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error testing chat table: {e}")
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)