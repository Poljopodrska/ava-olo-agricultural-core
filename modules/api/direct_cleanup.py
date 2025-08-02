#!/usr/bin/env python3
"""
Direct cleanup without async issues
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/direct", tags=["direct"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/cleanup-vrzel")
async def cleanup_vrzel():
    """Direct cleanup keeping only Vrzel"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count before
        cursor.execute("SELECT COUNT(*) FROM farmers")
        before = cursor.fetchone()[0]
        
        # Delete in reverse order of dependencies
        # 1. Delete fertilizing_plans for fields that belong to farmers != 4
        cursor.execute("""
            DELETE FROM fertilizing_plans 
            WHERE field_id IN (
                SELECT id FROM fields WHERE farmer_id != 4
            )
        """)
        plans_deleted = cursor.rowcount
        
        # 2. Delete plant_protection_plans
        cursor.execute("""
            DELETE FROM plant_protection_plans 
            WHERE field_id IN (
                SELECT id FROM fields WHERE farmer_id != 4
            )
        """)
        protection_deleted = cursor.rowcount
        
        # 3. Delete messages for farmers != 4
        cursor.execute("""
            DELETE FROM messages 
            WHERE farmer_id != 4
        """)
        messages_deleted = cursor.rowcount
        
        # 4. Delete fields for farmers != 4
        cursor.execute("""
            DELETE FROM fields 
            WHERE farmer_id != 4
        """)
        fields_deleted = cursor.rowcount
        
        # Then delete all farmers except Vrzel (ID 4)
        cursor.execute("""
            DELETE FROM farmers 
            WHERE id != 4
        """)
        
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
            "details": {
                "farmers": deleted,
                "fields": fields_deleted,
                "messages": messages_deleted,
                "fertilizing_plans": plans_deleted,
                "protection_plans": protection_deleted
            },
            "message": f"Cleanup complete! Kept only Blaz Vrzel (ID 4)"
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Direct cleanup error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()