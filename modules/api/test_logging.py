#!/usr/bin/env python3
"""
Test endpoint to verify logging is working
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test/logging")
async def test_logging():
    """Test endpoint that definitely logs"""
    timestamp = datetime.now().isoformat()
    
    # Log at different levels
    logger.debug(f"🔍 TEST DEBUG LOG at {timestamp}")
    logger.info(f"📝 TEST INFO LOG at {timestamp}")
    logger.warning(f"⚠️ TEST WARNING LOG at {timestamp}")
    logger.error(f"❌ TEST ERROR LOG at {timestamp}")
    
    # Also print to stdout
    print(f"🎯 TEST PRINT OUTPUT at {timestamp}")
    
    # Log with corn keyword to test our filters
    logger.info(f"🌽 TEST CORN LOG - Testing if logging works at {timestamp}")
    
    return JSONResponse(content={
        "success": True,
        "timestamp": timestamp,
        "message": "Logging test completed - check CloudWatch logs",
        "version": "v4.27.0"
    })

@router.get("/test/corn")
async def test_corn_query():
    """Test the corn query directly"""
    from modules.core.simple_db import execute_simple_query
    
    logger.info("🌽 TEST CORN ENDPOINT CALLED")
    
    # Query for Edi's corn
    result = {}
    
    try:
        # Get Edi's fields
        fields_query = """
            SELECT id, field_name, area_ha
            FROM fields
            WHERE farmer_id = 49
            ORDER BY field_name
        """
        fields_result = execute_simple_query(fields_query, ())
        
        if fields_result.get('success') and fields_result.get('rows'):
            result['fields'] = [
                {"id": row[0], "name": row[1], "area_ha": row[2]}
                for row in fields_result['rows']
            ]
            logger.info(f"Found {len(result['fields'])} fields for Edi")
        
        # Get crops with corn
        corn_query = """
            SELECT 
                fc.field_id,
                f.field_name,
                fc.crop_name,
                fc.variety
            FROM field_crops fc
            JOIN fields f ON fc.field_id = f.id
            WHERE f.farmer_id = 49
            AND LOWER(fc.crop_name) LIKE '%corn%'
        """
        corn_result = execute_simple_query(corn_query, ())
        
        if corn_result.get('success') and corn_result.get('rows'):
            result['corn_locations'] = [
                {
                    "field_id": row[0],
                    "field_name": row[1],
                    "crop_name": row[2],
                    "variety": row[3]
                }
                for row in corn_result['rows']
            ]
            logger.info(f"🌽 CORN FOUND: {result['corn_locations']}")
        else:
            result['corn_locations'] = []
            logger.info("🌽 NO CORN FOUND in database")
        
        result['success'] = True
        
    except Exception as e:
        logger.error(f"Error in test corn query: {e}")
        result = {"success": False, "error": str(e)}
    
    return JSONResponse(content=result)