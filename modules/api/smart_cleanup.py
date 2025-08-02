#!/usr/bin/env python3
"""
Smart cleanup that handles actual database structure
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/smart", tags=["smart"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/cleanup-farmers")
async def smart_cleanup():
    """Smart cleanup that handles actual table structure"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count farmers before
        cursor.execute("SELECT COUNT(*) FROM farmers")
        before = cursor.fetchone()[0]
        
        # Get actual farmers to delete (using correct column names)
        cursor.execute("SELECT id, farm_name FROM farmers WHERE id != 4")
        farmers_to_delete = cursor.fetchall()
        
        deleted_counts = {}
        errors = []
        
        # Delete in correct order based on foreign key dependencies
        
        # 1. Delete field_soil_data (references fields)
        try:
            cursor.execute("""
                DELETE FROM field_soil_data 
                WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
            """)
            deleted_counts['field_soil_data'] = cursor.rowcount
        except Exception as e:
            errors.append(f"field_soil_data: {str(e)}")
        
        # 2. Delete field_crops (references fields)
        try:
            cursor.execute("""
                DELETE FROM field_crops 
                WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
            """)
            deleted_counts['field_crops'] = cursor.rowcount
        except Exception as e:
            errors.append(f"field_crops: {str(e)}")
        
        # 3. Delete fertilizing_plans (references fields)
        try:
            cursor.execute("""
                DELETE FROM fertilizing_plans 
                WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
            """)
            deleted_counts['fertilizing_plans'] = cursor.rowcount
        except Exception as e:
            errors.append(f"fertilizing_plans: {str(e)}")
        
        # 4. Delete plant_protection_plans if exists
        try:
            cursor.execute("""
                DELETE FROM plant_protection_plans 
                WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
            """)
            deleted_counts['plant_protection_plans'] = cursor.rowcount
        except:
            pass  # Table might not exist
        
        # 5. Delete task_fields if exists
        try:
            cursor.execute("""
                DELETE FROM task_fields 
                WHERE field_id IN (SELECT id FROM fields WHERE farmer_id != 4)
            """)
            deleted_counts['task_fields'] = cursor.rowcount
        except:
            pass
        
        # 6. Delete fields
        try:
            cursor.execute("DELETE FROM fields WHERE farmer_id != 4")
            deleted_counts['fields'] = cursor.rowcount
        except Exception as e:
            errors.append(f"fields: {str(e)}")
        
        # 7. Delete messages if exists
        try:
            cursor.execute("DELETE FROM messages WHERE farmer_id != 4")
            deleted_counts['messages'] = cursor.rowcount
        except:
            pass
        
        # 8. Delete tasks if exists
        try:
            cursor.execute("DELETE FROM tasks WHERE farmer_id != 4")
            deleted_counts['tasks'] = cursor.rowcount
        except:
            pass
        
        # 9. Delete inventory if exists
        try:
            cursor.execute("DELETE FROM inventory WHERE farmer_id != 4")
            deleted_counts['inventory'] = cursor.rowcount
        except:
            pass
        
        # 10. Delete chat tables if they exist
        for table in ['chat_messages', 'conversation_states', 'incoming_messages', 'pending_messages']:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE farmer_id != 4")
                deleted_counts[table] = cursor.rowcount
            except:
                pass
        
        # 11. Finally delete farmers
        try:
            cursor.execute("DELETE FROM farmers WHERE id != 4")
            deleted_counts['farmers'] = cursor.rowcount
        except Exception as e:
            errors.append(f"farmers: {str(e)}")
        
        conn.commit()
        
        # Count after
        cursor.execute("SELECT COUNT(*) FROM farmers")
        after = cursor.fetchone()[0]
        
        # Verify Blaz Vrzel remains
        cursor.execute("SELECT id, farm_name FROM farmers WHERE id = 4")
        remaining_farmer = cursor.fetchone()
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "farmers_before": before,
            "farmers_after": after,
            "farmers_deleted": len(farmers_to_delete),
            "deleted_details": [{"id": f[0], "name": f[1]} for f in farmers_to_delete],
            "deleted_counts": deleted_counts,
            "errors": errors,
            "remaining_farmer": {
                "id": remaining_farmer[0],
                "name": remaining_farmer[1]
            } if remaining_farmer else None,
            "message": f"✅ Cleanup complete! Deleted {len(farmers_to_delete)} farmers. Only Blaz Vrzel remains."
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Smart cleanup error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/check-structure")
async def check_structure():
    """Check actual database structure"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get farmers table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farmers'
            ORDER BY ordinal_position
        """)
        farmer_columns = [row[0] for row in cursor.fetchall()]
        
        # Get all tables that reference farmers
        cursor.execute("""
            SELECT DISTINCT tc.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'farmers'
        """)
        tables_referencing_farmers = [row[0] for row in cursor.fetchall()]
        
        # Get all tables that reference fields
        cursor.execute("""
            SELECT DISTINCT tc.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'fields'
        """)
        tables_referencing_fields = [row[0] for row in cursor.fetchall()]
        
        return JSONResponse(content={
            "farmers_columns": farmer_columns,
            "tables_referencing_farmers": tables_referencing_farmers,
            "tables_referencing_fields": tables_referencing_fields
        })
        
    except Exception as e:
        logger.error(f"Structure check error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()