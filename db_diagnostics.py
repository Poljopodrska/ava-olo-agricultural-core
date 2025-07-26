#!/usr/bin/env python3
"""
Constitutional Database Connection Diagnostics
🎯 Purpose: Identify why schema discovery is failing
📜 Constitutional Compliance: Error isolation + transparency
"""

import os
import asyncio
import asyncpg
from typing import Dict, Any

async def test_connection_methods():
    """Test different connection approaches to identify the issue"""
    
    results = {
        "environment_vars": {},
        "connection_tests": {},
        "ssl_modes": {},
        "database_names": {}
    }
    
    # 1. Check environment variables
    print("🔍 Checking Environment Variables...")
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT', 'DATABASE_URL']
    for var in env_vars:
        value = os.getenv(var)
        results["environment_vars"][var] = "SET" if value else "MISSING"
        if value and var != 'DB_PASSWORD':  # Don't log password
            print(f"  {var}: {'SET' if value else 'MISSING'}")
    
    # 2. Test different database names (Constitutional: farmer_crm vs postgres)
    db_names_to_test = ['farmer_crm', 'postgres', 'ava_olo']
    
    for db_name in db_names_to_test:
        print(f"\n🗄️ Testing database: {db_name}")
        
        # Test different SSL modes
        ssl_modes = ['require', 'prefer', 'disable']
        
        for ssl_mode in ssl_modes:
            try:
                # Build connection string
                host = os.getenv('DB_HOST', 'farmer-crm-production.c123456789.us-east-1.rds.amazonaws.com')
                user = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', 'your_password')
                port = os.getenv('DB_PORT', '5432')
                
                dsn = f"postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode={ssl_mode}"
                
                conn = await asyncpg.connect(dsn, timeout=10)
                
                # Test basic query
                result = await conn.fetchval("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                
                await conn.close()
                
                results["connection_tests"][f"{db_name}_{ssl_mode}"] = {
                    "status": "SUCCESS",
                    "table_count": result
                }
                
                print(f"  ✅ {ssl_mode}: SUCCESS (Tables: {result})")
                
                # If this works, test farmer count
                if db_name in ['farmer_crm', 'postgres']:
                    try:
                        conn = await asyncpg.connect(dsn, timeout=10)
                        farmer_count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
                        await conn.close()
                        print(f"    🧑‍🌾 Farmers found: {farmer_count}")
                        results["connection_tests"][f"{db_name}_{ssl_mode}"]["farmer_count"] = farmer_count
                    except Exception as e:
                        print(f"    ⚠️ No farmers table: {str(e)[:50]}...")
                
            except Exception as e:
                results["connection_tests"][f"{db_name}_{ssl_mode}"] = {
                    "status": "FAILED",
                    "error": str(e)[:100]
                }
                print(f"  ❌ {ssl_mode}: {str(e)[:50]}...")
    
    return results

async def test_current_working_connection():
    """Test the exact connection that works for Count Farmers"""
    print("\n🎯 Testing Current Working Connection...")
    
    try:
        # Use the same connection logic as Count Farmers
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME', 'postgres')  # Default to postgres
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')
        db_port = os.getenv('DB_PORT', '5432')
        
        print(f"  Host: {db_host}")
        print(f"  Database: {db_name}")
        print(f"  User: {db_user}")
        print(f"  Port: {db_port}")
        
        # Test with SSL strategies
        ssl_strategies = [
            "require",
            "prefer", 
            "disable"
        ]
        
        for ssl_mode in ssl_strategies:
            try:
                dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={ssl_mode}"
                
                conn = await asyncpg.connect(dsn, timeout=15)
                
                # Test queries that should work
                table_count = await conn.fetchval("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                farmer_count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
                
                # Get actual table names
                tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
                
                await conn.close()
                
                print(f"  ✅ SSL {ssl_mode}: SUCCESS")
                print(f"    📊 Tables: {table_count}")
                print(f"    🧑‍🌾 Farmers: {farmer_count}")
                print(f"    📋 Table names: {[row['tablename'] for row in tables]}")
                
                return {
                    "status": "SUCCESS",
                    "ssl_mode": ssl_mode,
                    "table_count": table_count,
                    "farmer_count": farmer_count,
                    "tables": [row['tablename'] for row in tables]
                }
                
            except Exception as e:
                print(f"  ❌ SSL {ssl_mode}: {str(e)[:50]}...")
                continue
        
        return {"status": "ALL_FAILED"}
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return {"status": "ERROR", "error": str(e)}

async def get_schema_info():
    """Get the actual schema information we need"""
    print("\n📋 Getting Schema Information...")
    
    try:
        # Use working connection parameters
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME', 'postgres')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')
        db_port = os.getenv('DB_PORT', '5432')
        
        dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
        
        conn = await asyncpg.connect(dsn, timeout=15)
        
        # Get farmers table structure
        farmers_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'farmers' 
            ORDER BY ordinal_position
        """)
        
        # Get fields table structure (if exists)
        fields_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'fields' 
            ORDER BY ordinal_position
        """)
        
        # Get all table names
        all_tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        
        await conn.close()
        
        print("✅ Schema Retrieved Successfully!")
        print(f"📋 All tables: {[row['tablename'] for row in all_tables]}")
        print(f"🧑‍🌾 Farmers columns: {[row['column_name'] for row in farmers_columns]}")
        print(f"🏞️ Fields columns: {[row['column_name'] for row in fields_columns] if fields_columns else 'No fields table'}")
        
        return {
            "farmers_columns": [dict(row) for row in farmers_columns],
            "fields_columns": [dict(row) for row in fields_columns],
            "all_tables": [row['tablename'] for row in all_tables]
        }
        
    except Exception as e:
        print(f"❌ Schema retrieval failed: {e}")
        return {"error": str(e)}

async def main():
    """Main diagnostic function"""
    print("🔧 AVA OLO Database Connection Diagnostics")
    print("=" * 50)
    
    # Test 1: Environment check
    env_results = await test_connection_methods()
    
    # Test 2: Current working connection
    working_results = await test_current_working_connection()
    
    # Test 3: Get schema if connection works
    if working_results.get("status") == "SUCCESS":
        schema_results = await get_schema_info()
        
        # Print summary for Claude Code
        print("\n" + "=" * 50)
        print("📋 SUMMARY FOR CLAUDE CODE:")
        print("=" * 50)
        
        if "farmers_columns" in schema_results:
            print("✅ WORKING CONNECTION FOUND!")
            print(f"Database: {os.getenv('DB_NAME', 'postgres')}")
            print(f"SSL Mode: {working_results.get('ssl_mode')}")
            print(f"Farmers Table Columns: {[col['column_name'] for col in schema_results['farmers_columns']]}")
            
            # Check for specific columns
            farmer_cols = [col['column_name'] for col in schema_results['farmers_columns']]
            print(f"\n🔍 Column Analysis:")
            print(f"  - Has 'farmer_id'? {'farmer_id' in farmer_cols}")
            print(f"  - Has 'id'? {'id' in farmer_cols}")
            print(f"  - Has 'name'? {'name' in farmer_cols}")
            print(f"  - Has 'email'? {'email' in farmer_cols}")
            print(f"  - Primary key appears to be: {farmer_cols[0] if farmer_cols else 'UNKNOWN'}")
        else:
            print("❌ Schema retrieval failed even with working connection")
    else:
        print("\n❌ NO WORKING CONNECTION FOUND")
        print("Check AWS environment variables in ECS!")

if __name__ == "__main__":
    asyncio.run(main())