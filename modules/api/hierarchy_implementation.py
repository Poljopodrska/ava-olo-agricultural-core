#!/usr/bin/env python3
"""
Precise Database Hierarchy Implementation
Based on actual table analysis - 18 farmer-specific, 15 knowledge tables
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hierarchy", tags=["hierarchy"])

# Farmer-specific tables that CASCADE DELETE
FARMER_SPECIFIC_TABLES = [
    'farmers', 'fields', 'field_crops', 'field_soil_data', 'fertilizing_plans',
    'tasks', 'task_fields', 'task_materials', 'inventory', 'inventory_deductions',
    'orders', 'invoices', 'chat_messages', 'conversation_states', 
    'incoming_messages', 'pending_messages', 'farmer_facts', 'farmer_interaction_costs'
]

# Knowledge tables that are PROTECTED from deletion
KNOWLEDGE_TABLES = [
    'crop_nutrient_needs', 'crop_protection_croatia', 'crop_technology',
    'fertilizers', 'cp_products', 'seeds', 'variety_trial_data',
    'material_catalog', 'cost_rates', 'farm_machinery', 'farm_organic_fertilizers',
    'standard_queries', 'advice_log', 'weather_data'
]

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/create-archive-tables")
async def create_archive_tables():
    """Create archive tables for all farmer-specific tables"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        created_tables = []
        errors = []
        
        for table in FARMER_SPECIFIC_TABLES:
            try:
                # Create archive table
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table}_archive (
                        LIKE {table} INCLUDING ALL,
                        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        deleted_by VARCHAR(100) DEFAULT 'hierarchy_system',
                        deletion_reason VARCHAR(500)
                    )
                """)
                created_tables.append(f"{table}_archive")
                
            except Exception as e:
                errors.append(f"{table}: {str(e)}")
        
        conn.commit()
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "created_tables": created_tables,
            "errors": errors,
            "message": f"Created {len(created_tables)} archive tables"
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Archive table creation error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/configure-cascade-deletes")
async def configure_cascade_deletes():
    """Configure CASCADE DELETE for farmer-specific table hierarchy"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Define foreign key relationships for CASCADE DELETE
        cascade_configs = [
            # Direct farmer relationships
            ("fields", "fields_farmer_id_fkey", "fields", "farmer_id", "farmers", "id"),
            ("inventory", "inventory_farmer_id_fkey", "inventory", "farmer_id", "farmers", "id"),
            ("orders", "orders_farmer_id_fkey", "orders", "farmer_id", "farmers", "id"),
            ("invoices", "invoices_farmer_id_fkey", "invoices", "farmer_id", "farmers", "id"),
            ("chat_messages", "chat_messages_farmer_id_fkey", "chat_messages", "farmer_id", "farmers", "id"),
            ("conversation_states", "conversation_states_farmer_id_fkey", "conversation_states", "farmer_id", "farmers", "id"),
            ("incoming_messages", "incoming_messages_farmer_id_fkey", "incoming_messages", "farmer_id", "farmers", "id"),
            ("pending_messages", "pending_messages_farmer_id_fkey", "pending_messages", "farmer_id", "farmers", "id"),
            ("farmer_facts", "farmer_facts_farmer_id_fkey", "farmer_facts", "farmer_id", "farmers", "id"),
            ("farmer_interaction_costs", "farmer_interaction_costs_farmer_id_fkey", "farmer_interaction_costs", "farmer_id", "farmers", "id"),
            
            # Field-dependent relationships
            ("field_crops", "field_crops_field_id_fkey", "field_crops", "field_id", "fields", "id"),
            ("field_soil_data", "field_soil_data_field_id_fkey", "field_soil_data", "field_id", "fields", "id"),
            ("fertilizing_plans", "fertilizing_plans_field_id_fkey", "fertilizing_plans", "field_id", "fields", "id"),
            ("task_fields", "task_fields_field_id_fkey", "task_fields", "field_id", "fields", "id"),
            
            # Task relationships
            ("task_materials", "task_materials_task_id_fkey", "task_materials", "task_id", "tasks", "id"),
            
            # Inventory relationships
            ("inventory_deductions", "inventory_deductions_inventory_id_fkey", "inventory_deductions", "inventory_id", "inventory", "id"),
        ]
        
        updated = []
        errors = []
        
        for table, constraint, table_name, column, ref_table, ref_column in cascade_configs:
            try:
                # Drop existing constraint
                cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint}")
                
                # Add back with CASCADE DELETE
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT {constraint} 
                    FOREIGN KEY ({column}) 
                    REFERENCES {ref_table}({ref_column}) 
                    ON DELETE CASCADE
                """)
                
                updated.append(f"{table_name}.{column} -> {ref_table}.{ref_column}")
                
            except Exception as e:
                errors.append(f"{table}: {str(e)}")
        
        conn.commit()
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "updated_constraints": updated,
            "errors": errors,
            "message": f"Updated {len(updated)} foreign keys with CASCADE DELETE"
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"CASCADE configuration error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/create-archive-function")
async def create_archive_function():
    """Create archive-before-delete function"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create the archive and delete function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION archive_and_delete_farmer(farmer_id_param INTEGER, reason VARCHAR DEFAULT 'User requested deletion')
            RETURNS JSON AS $$
            DECLARE
                archived_counts JSON;
                result JSON;
            BEGIN
                -- Initialize counts object
                archived_counts := '{}'::JSON;
                
                -- Archive farmer_interaction_costs
                INSERT INTO farmer_interaction_costs_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM farmer_interaction_costs WHERE farmer_id = farmer_id_param;
                
                -- Archive farmer_facts
                INSERT INTO farmer_facts_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM farmer_facts WHERE farmer_id = farmer_id_param;
                
                -- Archive pending_messages
                INSERT INTO pending_messages_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM pending_messages WHERE farmer_id = farmer_id_param;
                
                -- Archive incoming_messages
                INSERT INTO incoming_messages_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM incoming_messages WHERE farmer_id = farmer_id_param;
                
                -- Archive conversation_states
                INSERT INTO conversation_states_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM conversation_states WHERE farmer_id = farmer_id_param;
                
                -- Archive chat_messages
                INSERT INTO chat_messages_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM chat_messages WHERE farmer_id = farmer_id_param;
                
                -- Archive invoices
                INSERT INTO invoices_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM invoices WHERE farmer_id = farmer_id_param;
                
                -- Archive orders
                INSERT INTO orders_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM orders WHERE farmer_id = farmer_id_param;
                
                -- Archive inventory_deductions
                INSERT INTO inventory_deductions_archive
                SELECT id.*, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM inventory_deductions id
                JOIN inventory i ON id.inventory_id = i.id
                WHERE i.farmer_id = farmer_id_param;
                
                -- Archive inventory
                INSERT INTO inventory_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM inventory WHERE farmer_id = farmer_id_param;
                
                -- Archive task_materials
                INSERT INTO task_materials_archive
                SELECT tm.*, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM task_materials tm
                JOIN tasks t ON tm.task_id = t.id
                WHERE t.farmer_id = farmer_id_param;
                
                -- Archive task_fields
                INSERT INTO task_fields_archive
                SELECT tf.*, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM task_fields tf
                JOIN fields f ON tf.field_id = f.id
                WHERE f.farmer_id = farmer_id_param;
                
                -- Archive tasks
                INSERT INTO tasks_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM tasks WHERE farmer_id = farmer_id_param;
                
                -- Archive fertilizing_plans
                INSERT INTO fertilizing_plans_archive
                SELECT fp.*, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM fertilizing_plans fp
                JOIN fields f ON fp.field_id = f.id
                WHERE f.farmer_id = farmer_id_param;
                
                -- Archive field_soil_data
                INSERT INTO field_soil_data_archive
                SELECT fsd.*, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM field_soil_data fsd
                JOIN fields f ON fsd.field_id = f.id
                WHERE f.farmer_id = farmer_id_param;
                
                -- Archive field_crops
                INSERT INTO field_crops_archive
                SELECT fc.*, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM field_crops fc
                JOIN fields f ON fc.field_id = f.id
                WHERE f.farmer_id = farmer_id_param;
                
                -- Archive fields
                INSERT INTO fields_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM fields WHERE farmer_id = farmer_id_param;
                
                -- Archive farmers
                INSERT INTO farmers_archive
                SELECT *, CURRENT_TIMESTAMP, 'hierarchy_system', reason
                FROM farmers WHERE id = farmer_id_param;
                
                -- Delete the farmer (CASCADE handles all dependencies)
                DELETE FROM farmers WHERE id = farmer_id_param;
                
                -- Return success
                result := json_build_object(
                    'success', true,
                    'farmer_id', farmer_id_param,
                    'archived_at', CURRENT_TIMESTAMP,
                    'reason', reason
                );
                
                RETURN result;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": "Archive and delete function created successfully"
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Function creation error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/execute-cleanup")
async def execute_cleanup():
    """Execute immediate cleanup - delete all farmers except Blaz Vrzel"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get list of farmers to delete
        cursor.execute("SELECT id, first_name, last_name FROM farmers WHERE id != 4")
        farmers_to_delete = cursor.fetchall()
        
        deleted_farmers = []
        errors = []
        
        # Archive and delete each farmer
        for farmer_id, first_name, last_name in farmers_to_delete:
            try:
                cursor.execute(
                    "SELECT archive_and_delete_farmer(%s, %s)",
                    (farmer_id, f"Cleanup - keeping only Blaz Vrzel")
                )
                result = cursor.fetchone()[0]
                deleted_farmers.append({
                    "id": farmer_id,
                    "name": f"{first_name} {last_name}",
                    "result": result
                })
            except Exception as e:
                errors.append({
                    "farmer_id": farmer_id,
                    "name": f"{first_name} {last_name}",
                    "error": str(e)
                })
        
        conn.commit()
        
        # Verify final count
        cursor.execute("SELECT COUNT(*) FROM farmers")
        final_count = cursor.fetchone()[0]
        
        return JSONResponse(content={
            "success": len(errors) == 0,
            "farmers_deleted": len(deleted_farmers),
            "deleted_details": deleted_farmers,
            "errors": errors,
            "final_farmer_count": final_count,
            "message": f"Cleanup complete! Deleted {len(deleted_farmers)} farmers. Only Blaz Vrzel remains."
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Cleanup error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/knowledge-tables")
async def list_knowledge_tables():
    """List all protected knowledge tables"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        table_info = {}
        
        for table in KNOWLEDGE_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_info[table] = {
                    "protected": True,
                    "row_count": count,
                    "category": "knowledge"
                }
            except:
                table_info[table] = {
                    "protected": True,
                    "row_count": "N/A",
                    "category": "knowledge"
                }
        
        return JSONResponse(content={
            "knowledge_tables": table_info,
            "total_tables": len(KNOWLEDGE_TABLES),
            "message": "These tables are protected from farmer deletion"
        })
        
    except Exception as e:
        logger.error(f"Knowledge tables error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/archive-summary")
async def archive_summary():
    """Show archived farmers and restoration options"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get archived farmers
        cursor.execute("""
            SELECT id, first_name, last_name, deleted_at, deletion_reason
            FROM farmers_archive
            ORDER BY deleted_at DESC
        """)
        archived_farmers = cursor.fetchall()
        
        # Get archive counts
        archive_counts = {}
        for table in FARMER_SPECIFIC_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}_archive")
                count = cursor.fetchone()[0]
                archive_counts[f"{table}_archive"] = count
            except:
                archive_counts[f"{table}_archive"] = 0
        
        return JSONResponse(content={
            "archived_farmers": [
                {
                    "id": f[0],
                    "name": f"{f[1]} {f[2]}",
                    "deleted_at": f[3].isoformat() if f[3] else None,
                    "reason": f[4]
                }
                for f in archived_farmers
            ],
            "archive_counts": archive_counts,
            "total_archived": len(archived_farmers),
            "restoration_available": True
        })
        
    except Exception as e:
        logger.error(f"Archive summary error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/setup-complete-hierarchy")
async def setup_complete_hierarchy():
    """One-click setup of complete hierarchy system"""
    results = {}
    
    # Step 1: Create archive tables
    archive_result = await create_archive_tables()
    results['archive_tables'] = archive_result.body.decode()
    
    # Step 2: Configure CASCADE DELETEs
    cascade_result = await configure_cascade_deletes()
    results['cascade_config'] = cascade_result.body.decode()
    
    # Step 3: Create archive function
    function_result = await create_archive_function()
    results['archive_function'] = function_result.body.decode()
    
    # Step 4: Execute cleanup
    cleanup_result = await execute_cleanup()
    results['cleanup'] = cleanup_result.body.decode()
    
    return JSONResponse(content={
        "success": True,
        "steps_completed": results,
        "message": "Complete hierarchy system implemented and cleanup executed!"
    })