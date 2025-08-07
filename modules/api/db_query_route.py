#!/usr/bin/env python3
"""
Direct database query endpoint for debugging
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.post("/sql")
async def execute_sql(request: Request):
    """Execute a SQL query directly (READ ONLY recommended)"""
    try:
        data = await request.json()
        query = data.get('query')
        params = data.get('params', ())
        
        if not query:
            return JSONResponse(content={
                "success": False,
                "error": "No query provided"
            }, status_code=400)
        
        # Log the query for safety
        logger.info(f"Executing query: {query[:100]}...")
        
        result = execute_simple_query(query, params)
        
        if result.get('success'):
            rows = result.get('rows', [])
            # Convert datetime objects to strings
            import datetime
            def serialize_row(row):
                if row is None:
                    return None
                serialized = []
                for item in row:
                    if isinstance(item, (datetime.datetime, datetime.date)):
                        serialized.append(item.isoformat())
                    else:
                        serialized.append(item)
                return serialized
            
            serialized_rows = [serialize_row(row) for row in rows] if rows else []
            
            return JSONResponse(content={
                "success": True,
                "rowcount": result.get('rowcount', len(rows)),
                "rows": serialized_rows,
                "query": query
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Query failed'),
                "query": query
            }, status_code=500)
            
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/check-farmers")
async def check_farmers_table():
    """Check the farmers table"""
    try:
        # Check if farmer 49 exists
        query = """
        SELECT farmer_id, name, username, whatsapp_number, email
        FROM farmers
        WHERE farmer_id = 49
        """
        result = execute_simple_query(query, ())
        
        # Also get count of all farmers
        count_query = "SELECT COUNT(*) FROM farmers"
        count_result = execute_simple_query(count_query, ())
        
        # Get recent farmers
        recent_query = """
        SELECT farmer_id, name, username, whatsapp_number
        FROM farmers
        ORDER BY farmer_id DESC
        LIMIT 5
        """
        recent_result = execute_simple_query(recent_query, ())
        
        return JSONResponse(content={
            "success": True,
            "farmer_49": {
                "exists": bool(result.get('rows')),
                "data": result.get('rows')[0] if result.get('rows') else None
            },
            "total_farmers": count_result.get('rows')[0][0] if count_result.get('rows') else 0,
            "recent_farmers": recent_result.get('rows', [])
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)