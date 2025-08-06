#!/usr/bin/env python3
"""
Database fix routes to add missing columns
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from ..core.database_manager import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/db-fix", tags=["database-fix"])

@router.post("/add-timestamp-columns")
async def add_timestamp_columns():
    """Add created_at and updated_at columns to fields table if missing"""
    db_manager = get_db_manager()
    
    try:
        # Check which columns exist
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'fields' 
        AND column_name IN ('created_at', 'updated_at');
        """
        
        result = db_manager.execute_query(check_query, ())
        existing_columns = [row[0] for row in result.get('rows', [])] if result else []
        
        messages = []
        
        # Add created_at if missing
        if 'created_at' not in existing_columns:
            try:
                alter_query = """
                ALTER TABLE fields 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """
                db_manager.execute_query(alter_query, ())
                messages.append("Added created_at column")
            except Exception as e:
                if "already exists" not in str(e):
                    raise e
                messages.append("created_at column already exists")
        else:
            messages.append("created_at column already exists")
        
        # Add updated_at if missing
        if 'updated_at' not in existing_columns:
            try:
                alter_query = """
                ALTER TABLE fields 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """
                db_manager.execute_query(alter_query, ())
                messages.append("Added updated_at column")
            except Exception as e:
                if "already exists" not in str(e):
                    raise e
                messages.append("updated_at column already exists")
        else:
            messages.append("updated_at column already exists")
        
        return JSONResponse(content={
            "success": True,
            "messages": messages
        })
        
    except Exception as e:
        logger.error(f"Error adding timestamp columns: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/check-fields-structure")
async def check_fields_structure():
    """Check the current structure of fields table"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'fields'
        ORDER BY ordinal_position;
        """
        
        result = db_manager.execute_query(query, ())
        
        columns = []
        if result and 'rows' in result:
            for row in result['rows']:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "default": row[3]
                })
        
        return JSONResponse(content={
            "success": True,
            "columns": columns
        })
        
    except Exception as e:
        logger.error(f"Error checking table structure: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)