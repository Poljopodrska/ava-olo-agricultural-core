#!/usr/bin/env python3
"""
Database initialization routes to create missing tables
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from ..core.database_manager import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/db", tags=["database-init"])

@router.post("/init-fields-table")
async def init_fields_table():
    """Create fields table if it doesn't exist"""
    db_manager = get_db_manager()
    
    try:
        # Check if table exists
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'fields'
        );
        """
        
        result = db_manager.execute_query(check_query, ())
        table_exists = result['rows'][0][0] if result and result['rows'] else False
        
        if table_exists:
            # Get row count
            count_result = db_manager.execute_query("SELECT COUNT(*) FROM fields", ())
            count = count_result['rows'][0][0] if count_result and count_result['rows'] else 0
            return JSONResponse(content={
                "success": True,
                "message": f"Fields table already exists with {count} records"
            })
        
        # Create the table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS fields (
            id SERIAL PRIMARY KEY,
            farmer_id INTEGER NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            area_ha DECIMAL(10, 2) NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            country VARCHAR(100),
            crop_type VARCHAR(100),
            variety VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db_manager.execute_query(create_table_query, ())
        
        # Create index
        index_query = "CREATE INDEX IF NOT EXISTS idx_fields_farmer_id ON fields(farmer_id);"
        db_manager.execute_query(index_query, ())
        
        return JSONResponse(content={
            "success": True,
            "message": "Fields table created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating fields table: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/init-field-crops-table")
async def init_field_crops_table():
    """Create field_crops table if it doesn't exist"""
    db_manager = get_db_manager()
    
    try:
        # Check if table exists
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'field_crops'
        );
        """
        
        result = db_manager.execute_query(check_query, ())
        table_exists = result['rows'][0][0] if result and result['rows'] else False
        
        if table_exists:
            return JSONResponse(content={
                "success": True,
                "message": "Field crops table already exists"
            })
        
        # Create the table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS field_crops (
            id SERIAL PRIMARY KEY,
            field_id INTEGER NOT NULL,
            crop_type VARCHAR(100),
            crop_name VARCHAR(100),
            variety VARCHAR(100),
            planting_date DATE,
            harvest_date DATE,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db_manager.execute_query(create_table_query, ())
        
        # Create index
        index_query = "CREATE INDEX IF NOT EXISTS idx_field_crops_field_id ON field_crops(field_id);"
        db_manager.execute_query(index_query, ())
        
        return JSONResponse(content={
            "success": True,
            "message": "Field crops table created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating field crops table: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/check-tables")
async def check_tables():
    """Check if required tables exist"""
    db_manager = get_db_manager()
    
    try:
        tables_to_check = ['farmers', 'fields', 'field_crops']
        results = {}
        
        for table in tables_to_check:
            check_query = f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """
            
            result = db_manager.execute_query(check_query, (table,))
            exists = result['rows'][0][0] if result and result['rows'] else False
            
            if exists:
                count_result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table}", ())
                count = count_result['rows'][0][0] if count_result and count_result['rows'] else 0
                results[table] = {"exists": True, "count": count}
            else:
                results[table] = {"exists": False, "count": 0}
        
        return JSONResponse(content={
            "success": True,
            "tables": results
        })
        
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)