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
        
        # First delete related fields
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
            "fields_deleted": fields_deleted,
            "message": f"Deleted {deleted} farmers and {fields_deleted} fields, kept Blaz Vrzel"
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