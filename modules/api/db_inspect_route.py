#!/usr/bin/env python3
"""
Database inspection endpoint - get full schema information
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..core.simple_db import execute_simple_query
import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/db", tags=["database"])

def serialize_value(value):
    """Convert non-JSON serializable values"""
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return value

def serialize_rows(rows):
    """Serialize all rows"""
    if not rows:
        return []
    return [[serialize_value(col) for col in row] for row in rows]

@router.get("/inspect")
async def inspect_database():
    """Get complete database schema information"""
    try:
        results = {}
        
        # 1. List all tables
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """
        tables_result = execute_simple_query(tables_query, ())
        
        if tables_result.get('success'):
            tables = [row[0] for row in tables_result.get('rows', [])]
            results['tables'] = tables
            
            # 2. For each important table, get schema
            important_tables = ['farmers', 'fields', 'chat_messages', 'field_crops', 'field_activities']
            results['schemas'] = {}
            
            for table in important_tables:
                if table in tables:
                    schema_query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                    """
                    schema_result = execute_simple_query(schema_query, (table,))
                    if schema_result.get('success'):
                        results['schemas'][table] = [
                            {
                                'name': row[0],
                                'type': row[1],
                                'nullable': row[2],
                                'default': row[3],
                                'max_length': row[4]
                            }
                            for row in schema_result.get('rows', [])
                        ]
            
            # 3. Sample data from farmers table
            farmers_query = """
            SELECT id, manager_name, manager_last_name, whatsapp_number, wa_phone_number, email
            FROM farmers
            ORDER BY id
            LIMIT 5
            """
            farmers_result = execute_simple_query(farmers_query, ())
            if farmers_result.get('success'):
                results['sample_farmers'] = serialize_rows(farmers_result.get('rows', []))
            
            # 4. Check for farmer 49
            farmer49_query = """
            SELECT id, manager_name, manager_last_name, whatsapp_number, wa_phone_number, email
            FROM farmers
            WHERE id = 49
            """
            farmer49_result = execute_simple_query(farmer49_query, ())
            results['farmer_49'] = {
                'exists': bool(farmer49_result.get('rows')),
                'data': serialize_rows(farmer49_result.get('rows', []))[0] if farmer49_result.get('rows') else None
            }
            
            # 5. Count records in key tables
            counts = {}
            for table in ['farmers', 'fields', 'chat_messages']:
                count_query = f"SELECT COUNT(*) FROM {table}"
                count_result = execute_simple_query(count_query, ())
                if count_result.get('success') and count_result.get('rows'):
                    counts[table] = count_result['rows'][0][0]
            results['record_counts'] = counts
            
            # 6. Recent chat messages
            messages_query = """
            SELECT wa_phone_number, role, LEFT(content, 50), timestamp
            FROM chat_messages
            ORDER BY timestamp DESC
            LIMIT 10
            """
            messages_result = execute_simple_query(messages_query, ())
            if messages_result.get('success'):
                results['recent_messages'] = [
                    {
                        'phone': row[0],
                        'role': row[1],
                        'content': row[2],
                        'timestamp': serialize_value(row[3])
                    }
                    for row in messages_result.get('rows', [])
                ]
        
        return JSONResponse(content={
            "success": True,
            "database_info": results
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/fix-columns")
async def get_column_mapping():
    """Get the correct column mappings for fixing the code"""
    try:
        # Get farmers table structure
        farmers_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'farmers'
        ORDER BY ordinal_position
        """
        farmers_result = execute_simple_query(farmers_query, ())
        
        farmers_columns = {}
        if farmers_result.get('success'):
            for row in farmers_result.get('rows', []):
                farmers_columns[row[0]] = row[1]
        
        # Identify the mapping issues
        mapping = {
            "farmers_table": {
                "current_columns": farmers_columns,
                "code_expects": {
                    "farmer_id": "Should use 'id'",
                    "name": "Should use 'manager_name' + 'manager_last_name'",
                    "username": "Column doesn't exist - might use 'wa_phone_number' or 'whatsapp_number'"
                },
                "correct_mapping": {
                    "id_column": "id",
                    "name_columns": ["manager_name", "manager_last_name"],
                    "whatsapp_column": "whatsapp_number or wa_phone_number",
                    "email_column": "email",
                    "password_column": "password_hash"
                }
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "column_mapping": mapping,
            "action_needed": "Update all queries to use correct column names"
        })
        
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)