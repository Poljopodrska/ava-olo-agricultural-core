#!/usr/bin/env python3
"""
Ultimate cleanup - discovers and handles all dependencies
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ultimate", tags=["ultimate"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/cleanup-all")
async def cleanup_all():
    """Ultimate cleanup - discovers all tables and cleans in correct order"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count farmers before
        cursor.execute("SELECT COUNT(*) FROM farmers")
        before = cursor.fetchone()[0]
        
        # Find all tables that reference fields
        cursor.execute("""
            SELECT tc.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND kcu.referenced_table_name = 'fields'
            GROUP BY tc.table_name
        """)
        
        # PostgreSQL version
        cursor.execute("""
            SELECT DISTINCT tc.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'fields'
        """)
        
        tables_referencing_fields = [row[0] for row in cursor.fetchall()]
        deleted_from_tables = {}
        
        # Delete from all tables that reference fields
        for table in tables_referencing_fields:
            try:
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
                """)
                deleted_from_tables[table] = cursor.rowcount
            except Exception as e:
                deleted_from_tables[table] = f"Error: {str(e)}"
        
        # Delete fields
        cursor.execute("DELETE FROM fields WHERE farmer_id != 4")
        fields_deleted = cursor.rowcount
        
        # Delete farmers
        cursor.execute("DELETE FROM farmers WHERE id != 4")
        farmers_deleted = cursor.rowcount
        
        conn.commit()
        
        return JSONResponse(content={
            "success": True,
            "farmers_before": before,
            "farmers_after": 1,
            "deleted": {
                "farmers": farmers_deleted,
                "fields": fields_deleted,
                "dependent_tables": deleted_from_tables
            },
            "message": f"✅ Complete cleanup done! Only Blaz Vrzel remains."
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

@router.get("/test-connection")
async def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"success": True, "result": result[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}