#!/usr/bin/env python3
"""
Migration endpoint for location columns
Temporary endpoint to run migrations in production
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from modules.core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migrations", tags=["migrations"])

@router.post("/run-location-migration")
async def run_location_migration():
    """Run migration to add location columns to farmers table"""
    db_manager = get_db_manager()
    results = {
        "timestamp": datetime.now().isoformat(),
        "columns_added": [],
        "columns_existed": [],
        "errors": [],
        "farmers_updated": 0
    }
    
    try:
        # First check what columns already exist
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farmers'
            AND column_name IN (
                'street_address', 'house_number', 'postal_code', 'city', 'country',
                'weather_latitude', 'weather_longitude', 'weather_location_name',
                'address_collected', 'location_prompt_shown', 'location_updated_at'
            )
        """
        existing_result = db_manager.execute_query(check_query)
        existing_columns = [row[0] for row in existing_result.get('rows', [])] if existing_result else []
        
        # All columns to add
        all_columns = [
            ("city", "VARCHAR(100)"),
            ("street_address", "VARCHAR(255)"),
            ("postal_code", "VARCHAR(20)"),
            ("house_number", "VARCHAR(20)"),
            ("country", "VARCHAR(100)"),
            ("weather_latitude", "DECIMAL(10, 8)"),
            ("weather_longitude", "DECIMAL(11, 8)"),
            ("weather_location_name", "VARCHAR(255)"),
            ("vat_number", "VARCHAR(50)"),
            ("address_collected", "BOOLEAN DEFAULT FALSE"),
            ("location_prompt_shown", "BOOLEAN DEFAULT FALSE"),
            ("location_updated_at", "TIMESTAMP")
        ]
        
        # Add missing columns
        for column_name, column_type in all_columns:
            if column_name not in existing_columns:
                try:
                    alter_query = f"""
                        ALTER TABLE farmers 
                        ADD COLUMN {column_name} {column_type}
                    """
                    result = db_manager.execute_query(alter_query)
                    if result:
                        results["columns_added"].append(column_name)
                        logger.info(f"Added column: {column_name}")
                except Exception as e:
                    error_msg = str(e)
                    if "already exists" in error_msg.lower():
                        results["columns_existed"].append(column_name)
                    else:
                        results["errors"].append(f"{column_name}: {error_msg}")
                        logger.error(f"Error adding column {column_name}: {e}")
            else:
                results["columns_existed"].append(column_name)
        
        # Update existing farmers to set address_collected = false where null
        update_query = """
            UPDATE farmers 
            SET address_collected = FALSE 
            WHERE address_collected IS NULL
        """
        update_result = db_manager.execute_query(update_query)
        if update_result:
            results["farmers_updated"] = update_result.get('affected_rows', 0)
        
        # Final verification
        verify_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'farmers'
            AND column_name IN (
                'street_address', 'house_number', 'postal_code', 'city', 'country',
                'weather_latitude', 'weather_longitude', 'weather_location_name',
                'address_collected', 'location_prompt_shown', 'location_updated_at'
            )
            ORDER BY ordinal_position
        """
        verify_result = db_manager.execute_query(verify_query)
        if verify_result and 'rows' in verify_result:
            results["final_schema"] = [
                {"column": row[0], "type": row[1]} 
                for row in verify_result['rows']
            ]
        
        results["status"] = "success"
        results["message"] = f"Migration completed. Added {len(results['columns_added'])} columns."
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        results["status"] = "error"
        results["message"] = str(e)
        return JSONResponse(content=results, status_code=500)

@router.get("/check-location-schema")
async def check_location_schema():
    """Check if location columns exist in farmers table"""
    db_manager = get_db_manager()
    
    try:
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'farmers'
            AND column_name IN (
                'street_address', 'house_number', 'postal_code', 'city', 'country',
                'weather_latitude', 'weather_longitude', 'weather_location_name',
                'address_collected', 'location_prompt_shown', 'location_updated_at',
                'language_preference'
            )
            ORDER BY ordinal_position
        """
        result = db_manager.execute_query(query)
        
        if result and 'rows' in result:
            columns = [
                {
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "default": row[3]
                }
                for row in result['rows']
            ]
            
            required_columns = [
                'street_address', 'house_number', 'postal_code', 'city', 'country',
                'weather_latitude', 'weather_longitude', 'address_collected'
            ]
            
            missing = [col for col in required_columns if col not in [c['name'] for c in columns]]
            
            return JSONResponse(content={
                "status": "success",
                "columns": columns,
                "missing": missing,
                "ready": len(missing) == 0
            })
        else:
            return JSONResponse(content={
                "status": "error",
                "message": "Could not query schema"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Schema check failed: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        }, status_code=500)