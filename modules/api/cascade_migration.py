#!/usr/bin/env python3
"""
Add CASCADE DELETE to all foreign keys
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cascade", tags=["cascade"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/add-cascade-deletes")
async def add_cascade_deletes():
    """Add CASCADE DELETE to all foreign keys"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # List of foreign key updates
        cascade_updates = [
            # Fields -> Farmers (when farmer deleted, delete their fields)
            ("fields", "fk_farmer", "fields", "farmer_id", "farmers", "id"),
            
            # Messages -> Farmers (when farmer deleted, delete their messages)
            ("messages", "messages_farmer_id_fkey", "messages", "farmer_id", "farmers", "id"),
            
            # Fertilizing Plans -> Fields (when field deleted, delete its plans)
            ("fertilizing_plans", "fk_field", "fertilizing_plans", "field_id", "fields", "id"),
            
            # Plant Protection Plans -> Fields (when field deleted, delete its plans)
            ("plant_protection_plans", "plant_protection_plans_field_id_fkey", "plant_protection_plans", "field_id", "fields", "id"),
        ]
        
        updated = []
        errors = []
        
        for table, constraint_name, table_name, column_name, ref_table, ref_column in cascade_updates:
            try:
                # Drop existing constraint
                cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}")
                
                # Add back with CASCADE DELETE
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT {constraint_name} 
                    FOREIGN KEY ({column_name}) 
                    REFERENCES {ref_table}({ref_column}) 
                    ON DELETE CASCADE
                """)
                
                updated.append(f"{table_name}.{column_name} -> {ref_table}.{ref_column}")
                
            except Exception as e:
                errors.append(f"{table}: {str(e)}")
        
        conn.commit()
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "updated": updated,
            "errors": errors,
            "message": f"Updated {len(updated)} foreign keys with CASCADE DELETE"
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"CASCADE migration error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/simple-cleanup")
async def simple_cleanup():
    """Simple cleanup - now with CASCADE DELETE, just delete farmers"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count before
        cursor.execute("SELECT COUNT(*) FROM farmers")
        before = cursor.fetchone()[0]
        
        # Just delete farmers - CASCADE will handle the rest!
        cursor.execute("DELETE FROM farmers WHERE id != 4")
        deleted = cursor.rowcount
        
        conn.commit()
        
        # Count after
        cursor.execute("SELECT COUNT(*) FROM farmers")
        after = cursor.fetchone()[0]
        
        return JSONResponse(content={
            "success": True,
            "before": before,
            "after": after,
            "deleted": deleted,
            "message": f"Deleted {deleted} farmers (CASCADE deleted all related data)"
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()