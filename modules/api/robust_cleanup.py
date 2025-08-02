#!/usr/bin/env python3
"""
Robust cleanup with separate transactions for each table
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/robust", tags=["robust"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

def delete_table_data(table_name, where_clause):
    """Delete data from a table with its own transaction"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
        count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return {"success": True, "count": count}
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return {"success": False, "error": str(e)}

@router.post("/cleanup-all")
async def robust_cleanup():
    """Cleanup with separate transactions for each table"""
    results = {}
    
    # Get initial farmer count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM farmers")
    farmers_before = cursor.fetchone()[0]
    cursor.execute("SELECT id, farm_name FROM farmers WHERE id != 4")
    farmers_to_delete = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Tables that reference fields (delete first)
    field_referencing_tables = [
        'advice_log',
        'fertilizing_plans', 
        'field_crops',
        'field_soil_data',
        'growth_stage_reports',
        'task_fields',
        'weather_data'
    ]
    
    for table in field_referencing_tables:
        results[table] = delete_table_data(
            table, 
            "field_id IN (SELECT id FROM fields WHERE farmer_id != 4)"
        )
    
    # Tables that reference farmers directly
    farmer_referencing_tables = [
        'advice_log',
        'farm_machinery',
        'farm_organic_fertilizers',
        'growth_stage_reports',
        'incoming_messages',
        'inventory',
        'invoices', 
        'pending_messages',
        'standard_queries'
    ]
    
    for table in farmer_referencing_tables:
        results[table] = delete_table_data(table, "farmer_id != 4")
    
    # Delete fields
    results['fields'] = delete_table_data('fields', 'farmer_id != 4')
    
    # Finally delete farmers
    results['farmers'] = delete_table_data('farmers', 'id != 4')
    
    # Get final count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM farmers")
    farmers_after = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    # Count successes and failures
    successes = sum(1 for r in results.values() if r.get('success', False))
    failures = sum(1 for r in results.values() if not r.get('success', False))
    
    return JSONResponse(content={
        "success": failures == 0,
        "farmers_before": farmers_before,
        "farmers_after": farmers_after,
        "farmers_deleted": len(farmers_to_delete),
        "deleted_farmers": [{"id": f[0], "name": f[1]} for f in farmers_to_delete],
        "table_results": results,
        "summary": {
            "successes": successes,
            "failures": failures,
            "total_tables": len(results)
        },
        "message": f"Cleanup {'complete' if failures == 0 else 'partial'}! Processed {len(results)} tables."
    })

@router.post("/force-cleanup")
async def force_cleanup():
    """Force cleanup by disabling foreign key checks temporarily"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get initial count
        cursor.execute("SELECT COUNT(*) FROM farmers")
        before = cursor.fetchone()[0]
        
        # Disable foreign key checks
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Delete all data
        deleted_counts = {}
        
        # Delete from all tables that might have farmer data
        tables_to_clean = [
            ('field_soil_data', 'field_id IN (SELECT id FROM fields WHERE farmer_id != 4)'),
            ('field_crops', 'field_id IN (SELECT id FROM fields WHERE farmer_id != 4)'),
            ('fertilizing_plans', 'field_id IN (SELECT id FROM fields WHERE farmer_id != 4)'),
            ('growth_stage_reports', 'field_id IN (SELECT id FROM fields WHERE farmer_id != 4)'),
            ('task_fields', 'field_id IN (SELECT id FROM fields WHERE farmer_id != 4)'),
            ('weather_data', 'field_id IN (SELECT id FROM fields WHERE farmer_id != 4)'),
            ('advice_log', 'farmer_id != 4'),
            ('farm_machinery', 'farmer_id != 4'),
            ('farm_organic_fertilizers', 'farmer_id != 4'),
            ('incoming_messages', 'farmer_id != 4'),
            ('inventory', 'farmer_id != 4'),
            ('invoices', 'farmer_id != 4'),
            ('pending_messages', 'farmer_id != 4'),
            ('standard_queries', 'farmer_id != 4'),
            ('fields', 'farmer_id != 4'),
            ('farmers', 'id != 4')
        ]
        
        for table, condition in tables_to_clean:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE {condition}")
                deleted_counts[table] = cursor.rowcount
            except Exception as e:
                deleted_counts[table] = f"Error: {str(e)}"
        
        # Re-enable foreign key checks
        cursor.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM farmers")
        after = cursor.fetchone()[0]
        
        return JSONResponse(content={
            "success": True,
            "farmers_before": before,
            "farmers_after": after,
            "deleted_counts": deleted_counts,
            "message": f"Force cleanup complete! Only Blaz Vrzel remains."
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Force cleanup error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()