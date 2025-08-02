#!/usr/bin/env python3
"""
Migration routes - Run database migrations via API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from ..core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/migration", tags=["migration"])

@router.post("/add-auth-columns")
async def add_auth_columns():
    """Add authentication columns to farmers table"""
    db_manager = get_db_manager()
    
    try:
        # Check current columns
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'farmers' 
        AND column_name IN ('password_hash', 'is_active', 'created_at', 'whatsapp_number')
        """
        
        result = db_manager.execute_query(check_query)
        existing_columns = []
        if result and 'rows' in result:
            existing_columns = [row[0] for row in result['rows']]
        
        added_columns = []
        errors = []
        
        # Add password_hash column
        if 'password_hash' not in existing_columns:
            try:
                db_manager.execute_query("""
                    ALTER TABLE farmers 
                    ADD COLUMN password_hash VARCHAR(255)
                """)
                added_columns.append('password_hash')
            except Exception as e:
                errors.append(f"password_hash: {str(e)}")
        
        # Add is_active column
        if 'is_active' not in existing_columns:
            try:
                db_manager.execute_query("""
                    ALTER TABLE farmers 
                    ADD COLUMN is_active BOOLEAN DEFAULT true
                """)
                added_columns.append('is_active')
            except Exception as e:
                errors.append(f"is_active: {str(e)}")
        
        # Add created_at column
        if 'created_at' not in existing_columns:
            try:
                db_manager.execute_query("""
                    ALTER TABLE farmers 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                added_columns.append('created_at')
            except Exception as e:
                errors.append(f"created_at: {str(e)}")
        
        # Add whatsapp_number column
        if 'whatsapp_number' not in existing_columns:
            try:
                db_manager.execute_query("""
                    ALTER TABLE farmers 
                    ADD COLUMN whatsapp_number VARCHAR(20)
                """)
                
                # Copy existing wa_phone_number data
                db_manager.execute_query("""
                    UPDATE farmers 
                    SET whatsapp_number = wa_phone_number 
                    WHERE whatsapp_number IS NULL AND wa_phone_number IS NOT NULL
                """)
                
                added_columns.append('whatsapp_number')
            except Exception as e:
                errors.append(f"whatsapp_number: {str(e)}")
        
        # Create index on whatsapp_number
        try:
            db_manager.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_farmers_whatsapp_number 
                ON farmers(whatsapp_number)
            """)
        except Exception as e:
            logger.warning(f"Index creation failed: {e}")
        
        # Verify final state
        final_check = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'farmers' 
        AND column_name IN ('password_hash', 'is_active', 'created_at', 'whatsapp_number')
        """
        
        result = db_manager.execute_query(final_check)
        final_columns = []
        if result and 'rows' in result:
            final_columns = [row[0] for row in result['rows']]
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "added_columns": added_columns,
            "existing_columns": existing_columns,
            "final_columns": final_columns,
            "errors": errors,
            "message": f"Added {len(added_columns)} columns" if added_columns else "All columns already exist"
        })
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/check-columns")
async def check_columns():
    """Check which authentication columns exist"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'farmers' 
        ORDER BY ordinal_position
        """
        
        result = db_manager.execute_query(query)
        
        columns = []
        if result and 'rows' in result:
            for row in result['rows']:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "default": row[3]
                })
        
        # Check for required auth columns
        column_names = [col['name'] for col in columns]
        auth_columns = {
            'password_hash': 'password_hash' in column_names,
            'is_active': 'is_active' in column_names,
            'created_at': 'created_at' in column_names,
            'whatsapp_number': 'whatsapp_number' in column_names,
            'wa_phone_number': 'wa_phone_number' in column_names
        }
        
        return JSONResponse(content={
            "success": True,
            "total_columns": len(columns),
            "columns": columns,
            "auth_columns": auth_columns,
            "ready_for_auth": all([auth_columns['password_hash'], auth_columns['is_active']])
        })
        
    except Exception as e:
        logger.error(f"Column check failed: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)