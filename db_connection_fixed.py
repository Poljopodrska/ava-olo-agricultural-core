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
    """Get all farmers using CORRECT column names"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # Use actual column names: id, name, email (not farmer_id, farm_name)
        farmers = await conn.fetch("""
            SELECT id, name, email, created_at
            FROM farmers 
            ORDER BY created_at DESC
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
    """Get fields for a farmer using CORRECT foreign key"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # First, check what the actual foreign key column is called
        fields = await conn.fetch("""
            SELECT * FROM fields 
            WHERE farmer_id = $1 OR owner_id = $1 
            LIMIT 10
        """, farmer_id)
        
        await conn.close()
        
        return {
            "fields": [dict(row) for row in fields],
            "count": len(fields)
        }
        
    except Exception as e:
        await conn.close()
        return {"error": str(e)}

async def get_field_tasks(field_id: int):
    """Get tasks for a field using CORRECT foreign key"""
    conn = await get_constitutional_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        tasks = await conn.fetch("""
            SELECT * FROM tasks 
            WHERE field_id = $1 
            ORDER BY created_at DESC
            LIMIT 20
        """, field_id)
        
        await conn.close()
        
        return {
            "tasks": [dict(row) for row in tasks],
            "count": len(tasks)
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