#!/usr/bin/env python3
"""
Fixed Database Connection Function
🎯 Purpose: Fix "Invalid IPv6 URL" error in asyncpg connection
📜 Constitutional Compliance: Error isolation + LLM-first approach
"""

import os
import asyncpg
from urllib.parse import quote_plus

async def get_constitutional_db_connection():
    """
    Constitutional database connection with proper URL encoding
    Fixes the "Invalid IPv6 URL" error
    """
    try:
        # Get environment variables
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME', 'farmer_crm')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')
        db_port = os.getenv('DB_PORT', '5432')
        
        # Validate required parameters
        if not all([db_host, db_password]):
            raise ValueError("Missing required environment variables: DB_HOST or DB_PASSWORD")
        
        # Build connection parameters (not URL string)
        connection_params = {
            'host': db_host,
            'port': int(db_port),
            'user': db_user,
            'password': db_password,  # Use raw password, not URL-encoded
            'database': db_name,
            'server_settings': {
                'application_name': 'ava_olo_dashboard'
            }
        }
        
        # Try different SSL modes in order of preference
        ssl_modes = ['require', 'prefer', 'disable']
        
        for ssl_mode in ssl_modes:
            try:
                # Add SSL mode to connection parameters
                if ssl_mode != 'disable':
                    connection_params['ssl'] = ssl_mode
                else:
                    connection_params['ssl'] = False
                
                # Create connection using parameters (not URL string)
                conn = await asyncpg.connect(**connection_params)
                
                # Test the connection
                await conn.fetchval("SELECT 1")
                
                print(f"✅ Connected successfully with SSL: {ssl_mode}")
                return conn
                
            except Exception as ssl_error:
                print(f"⚠️ SSL {ssl_mode} failed: {str(ssl_error)[:50]}...")
                continue
        
        # If all SSL modes fail, try one more time with basic connection
        raise Exception("All SSL connection attempts failed")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        # Constitutional principle: Error isolation - return None instead of crashing
        return None

async def test_fixed_connection():
    """Test the fixed connection and get schema info"""
    
    conn = await get_constitutional_db_connection()
    
    if not conn:
        return {
            "status": "connection_failed",
            "error": "Could not establish database connection"
        }
    
    try:
        # Test basic connectivity
        version = await conn.fetchval("SELECT version()")
        
        # Get table count
        table_count = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
        )
        
        # Get all table names
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        table_names = [row['tablename'] for row in tables]
        
        # Get farmers table structure if it exists
        farmers_info = {}
        if 'farmers' in table_names:
            # Get column information
            farmers_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'farmers' 
                ORDER BY ordinal_position
            """)
            
            # Get farmer count
            farmer_count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
            
            # Get sample farmer data (first 3 farmers, limited columns for privacy)
            sample_farmers = await conn.fetch("""
                SELECT id, name, email 
                FROM farmers 
                LIMIT 3
            """)
            
            farmers_info = {
                "columns": [dict(row) for row in farmers_columns],
                "column_names": [row['column_name'] for row in farmers_columns],
                "count": farmer_count,
                "sample_data": [dict(row) for row in sample_farmers]
            }
        
        await conn.close()
        
        return {
            "status": "success",
            "postgres_version": version[:100],
            "table_count": table_count,
            "tables": table_names,
            "farmers_info": farmers_info
        }
        
    except Exception as e:
        await conn.close()
        return {
            "status": "query_failed",
            "error": str(e)
        }

# Updated query functions using correct column names

async def get_farmer_count():
    """Get total farmer count - WORKING VERSION"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
        await conn.close()
        return {"count": count}
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

async def get_all_farmers():
    """Get all farmers using CORRECT column names from schema"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # FIXED: Use actual column names from farmers table
        farmers = await conn.fetch("""
            SELECT 
                id,
                state_farm_number,
                farm_name,
                manager_name,
                manager_last_name,
                email,
                phone,
                wa_phone_number,
                city,
                country
            FROM farmers 
            ORDER BY farm_name, manager_name
        """)
        
        await conn.close()
        
        return {
            "farmers": [dict(row) for row in farmers],
            "count": len(farmers)
        }
        
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

async def get_farmer_fields(farmer_id: int):
    """Get fields for a farmer using CORRECT foreign key: farmer_id"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # FIXED: Use farmer_id (confirmed from schema)
        fields = await conn.fetch("""
            SELECT 
                id,
                field_name,
                area_ha,
                latitude,
                longitude,
                blok_id,
                raba,
                country,
                notes
            FROM fields 
            WHERE farmer_id = $1 
            ORDER BY field_name
        """, farmer_id)
        
        await conn.close()
        
        return {
            "fields": [dict(row) for row in fields],
            "count": len(fields),
            "farmer_id": farmer_id
        }
        
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

async def get_field_tasks(field_id: int):
    """Get tasks for a field using CORRECT relationship: task_fields junction table"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # FIXED: Use task_fields junction table to link fields and tasks
        tasks = await conn.fetch("""
            SELECT 
                t.id,
                t.task_type,
                t.description,
                t.quantity,
                t.date_performed,
                t.status,
                t.notes,
                t.crop_name,
                t.rate_per_ha,
                t.rate_unit
            FROM tasks t
            INNER JOIN task_fields tf ON t.id = tf.task_id
            WHERE tf.field_id = $1 
            ORDER BY t.date_performed DESC, t.id DESC
            LIMIT 50
        """, field_id)
        
        await conn.close()
        
        return {
            "tasks": [dict(row) for row in tasks],
            "count": len(tasks),
            "field_id": field_id
        }
        
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

async def get_farmer_with_fields_and_tasks(farmer_id: int):
    """
    Get complete farmer information with fields and recent tasks
    🥭 Constitutional: Works for any farmer (Bulgarian mango farmers included!)
    """
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # Get farmer info
        farmer = await conn.fetchrow("""
            SELECT * FROM farmers WHERE id = $1
        """, farmer_id)
        
        if not farmer:
            await conn.close()
            return {"error": "Farmer not found"}
        
        # Get farmer's fields
        fields = await conn.fetch("""
            SELECT 
                id, field_name, area_ha, country
            FROM fields 
            WHERE farmer_id = $1 
            ORDER BY field_name
        """, farmer_id)
        
        # Get recent tasks for this farmer's fields
        recent_tasks = await conn.fetch("""
            SELECT 
                t.id,
                t.task_type,
                t.date_performed,
                t.crop_name,
                f.field_name
            FROM tasks t
            INNER JOIN task_fields tf ON t.id = tf.task_id
            INNER JOIN fields f ON tf.field_id = f.id
            WHERE f.farmer_id = $1 
            ORDER BY t.date_performed DESC
            LIMIT 20
        """, farmer_id)
        
        await conn.close()
        
        return {
            "farmer": dict(farmer),
            "fields": [dict(row) for row in fields],
            "recent_tasks": [dict(row) for row in recent_tasks],
            "field_count": len(fields),
            "recent_task_count": len(recent_tasks)
        }
        
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

async def get_field_with_crops(field_id: int):
    """
    Get field information with crop history
    """
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # Get field info
        field = await conn.fetchrow("""
            SELECT 
                f.*,
                fa.farm_name,
                fa.manager_name
            FROM fields f
            LEFT JOIN farmers fa ON f.farmer_id = fa.id
            WHERE f.id = $1
        """, field_id)
        
        if not field:
            await conn.close()
            return {"error": "Field not found"}
        
        # Get crop history for this field
        crops = await conn.fetch("""
            SELECT 
                crop_name,
                variety,
                expected_yield_t_ha,
                start_year_int,
                start_date,
                end_date
            FROM field_crops 
            WHERE field_id = $1 
            ORDER BY start_year_int DESC, start_date DESC
        """, field_id)
        
        # Get soil data if available
        soil_data = await conn.fetch("""
            SELECT 
                analysis_date,
                ph,
                p2o5_mg_100g,
                k2o_mg_100g,
                organic_matter_percent,
                analysis_institution
            FROM field_soil_data 
            WHERE field_id = $1 
            ORDER BY analysis_date DESC
        """, field_id)
        
        await conn.close()
        
        return {
            "field": dict(field),
            "crops": [dict(row) for row in crops],
            "soil_data": [dict(row) for row in soil_data],
            "crop_count": len(crops)
        }
        
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("🔧 Testing Fixed Database Connection...")
        result = await test_fixed_connection()
        
        import json
        print("\n📋 Connection Test Results:")
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())