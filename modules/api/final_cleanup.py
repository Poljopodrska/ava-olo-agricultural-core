#!/usr/bin/env python3
"""
Final cleanup - handles only existing tables
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/final", tags=["final"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/cleanup-now")
async def cleanup_now():
    """Final cleanup - keep only Vrzel"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count farmers before
        cursor.execute("SELECT COUNT(*) FROM farmers")
        before = cursor.fetchone()[0]
        
        # 1. Try to delete fertilizing_plans
        try:
            cursor.execute("""
                DELETE FROM fertilizing_plans 
                WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
            """)
            plans_deleted = cursor.rowcount
        except:
            plans_deleted = 0
        
        # 2. Delete fields
        cursor.execute("DELETE FROM fields WHERE farmer_id != 4")
        fields_deleted = cursor.rowcount
        
        # 3. Delete farmers
        cursor.execute("DELETE FROM farmers WHERE id != 4")
        farmers_deleted = cursor.rowcount
        
        conn.commit()
        
        return JSONResponse(content={
            "success": True,
            "deleted": {
                "farmers": farmers_deleted,
                "fields": fields_deleted,
                "plans": plans_deleted
            },
            "farmers_before": before,
            "farmers_after": 1,
            "message": f"✅ Cleanup complete! Deleted {farmers_deleted} farmers. Only Blaz Vrzel remains."
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