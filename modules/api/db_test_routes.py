#!/usr/bin/env python3
"""
Database Test Routes - Debug database connectivity issues
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from ..core.database_manager import get_db_manager
from ..core.config import get_database_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/db-test", tags=["database-test"])

@router.get("/connection")
async def test_connection():
    """Test basic database connection"""
    db_manager = get_db_manager()
    
    try:
        # Test basic connection
        result = db_manager.test_connection()
        
        return JSONResponse(content={
            "success": result,
            "message": "Database connection successful" if result else "Database connection failed"
        })
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/config")
async def get_config():
    """Get database configuration (with password hidden)"""
    config = get_database_config()
    
    # Hide password
    safe_config = config.copy()
    if 'password' in safe_config:
        safe_config['password'] = '***' if safe_config['password'] else None
    if 'url' in safe_config and safe_config['url']:
        # Hide password in URL
        import re
        safe_config['url'] = re.sub(r':([^:@]+)@', ':***@', safe_config['url'])
    
    return JSONResponse(content={
        "config": safe_config
    })

@router.get("/tables")
async def list_tables():
    """List all tables in the database"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """
        
        result = db_manager.execute_query(query)
        
        tables = []
        if result and 'rows' in result:
            tables = [row[0] for row in result['rows']]
        
        return JSONResponse(content={
            "success": True,
            "tables": tables,
            "count": len(tables)
        })
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/farmers-columns")
async def farmers_columns():
    """Get columns of farmers table"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'farmers'
        ORDER BY ordinal_position
        """
        
        result = db_manager.execute_query(query)
        
        columns = []
        if result and 'rows' in result:
            for row in result['rows']:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2]
                })
        
        # Check for specific columns we need
        column_names = [col['name'] for col in columns]
        required_columns = ['password_hash', 'is_active', 'whatsapp_number', 'wa_phone_number']
        
        missing = [col for col in required_columns if col not in column_names]
        
        return JSONResponse(content={
            "success": True,
            "columns": columns,
            "missing_required": missing,
            "has_password_hash": 'password_hash' in column_names,
            "has_is_active": 'is_active' in column_names
        })
    except Exception as e:
        logger.error(f"Failed to get farmers columns: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/test-query")
async def test_query():
    """Test a simple query"""
    db_manager = get_db_manager()
    
    try:
        # Test COUNT query
        query = "SELECT COUNT(*) FROM farmers"
        result = db_manager.execute_query(query)
        
        count = 0
        if result and 'rows' in result and result['rows']:
            count = result['rows'][0][0]
        
        return JSONResponse(content={
            "success": True,
            "farmer_count": count,
            "result_structure": {
                "has_rows": 'rows' in result if result else False,
                "has_columns": 'columns' in result if result else False,
                "columns": result.get('columns', []) if result else []
            }
        })
    except Exception as e:
        logger.error(f"Test query failed: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)