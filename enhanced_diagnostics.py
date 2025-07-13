#!/usr/bin/env python3
"""
Enhanced Database Connection Diagnostics
🎯 Purpose: Comprehensive diagnosis of App Runner → RDS connection issues
📜 Constitutional Compliance: Error isolation + transparency
"""

import os
import asyncio
import asyncpg
import json
from typing import Dict, Any, List

async def diagnose_connection_comprehensive():
    """Comprehensive connection diagnosis"""
    
    diagnostics = {
        "environment_check": {},
        "connection_attempts": [],
        "network_tests": {},
        "schema_discovery": {},
        "recommendations": []
    }
    
    print("🔧 AVA OLO Enhanced Connection Diagnostics")
    print("=" * 60)
    
    # 1. Environment Variables Analysis
    print("\n📋 1. ENVIRONMENT VARIABLES CHECK")
    print("-" * 40)
    
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    optional_vars = ['DATABASE_URL', 'POSTGRES_URL', 'RDS_HOSTNAME', 'RDS_DB_NAME']
    
    for var in required_vars + optional_vars:
        value = os.getenv(var)
        diagnostics["environment_check"][var] = {
            "present": bool(value),
            "length": len(value) if value else 0,
            "required": var in required_vars
        }
        
        status = "✅ SET" if value else "❌ MISSING"
        req_status = "(REQUIRED)" if var in required_vars else "(optional)"
        print(f"  {var}: {status} {req_status}")
        if value and var not in ['DB_PASSWORD']:  # Don't log passwords
            print(f"    Length: {len(value)} chars")
    
    # 2. Multiple Database/Host Combinations
    print("\n🌐 2. CONNECTION ATTEMPTS")
    print("-" * 40)
    
    # Get environment values
    env_host = os.getenv('DB_HOST', '')
    env_user = os.getenv('DB_USER', 'postgres')
    env_password = os.getenv('DB_PASSWORD', '')
    env_port = os.getenv('DB_PORT', '5432')
    
    # Possible database names to try
    database_names = [
        os.getenv('DB_NAME', ''),
        'farmer_crm',
        'postgres', 
        'ava_olo'
    ]
    
    # Possible hosts (in case environment is different)
    hosts_to_try = [
        env_host,
        'farmer-crm-production.c123456789.us-east-1.rds.amazonaws.com',
        'localhost'
    ]
    
    # Remove empty values
    database_names = [db for db in database_names if db]
    hosts_to_try = [host for host in hosts_to_try if host]
    
    ssl_modes = ['require', 'prefer', 'disable']
    
    for host in hosts_to_try:
        for db_name in database_names:
            for ssl_mode in ssl_modes:
                attempt_id = f"{host[:20]}.../{db_name}/{ssl_mode}"
                print(f"\n🔍 Testing: {attempt_id}")
                
                attempt_result = {
                    "host": host,
                    "database": db_name,
                    "ssl_mode": ssl_mode,
                    "status": "unknown",
                    "error": None,
                    "details": {}
                }
                
                try:
                    # Build connection parameters (not URL) to fix IPv6 error
                    connection_params = {
                        'host': host,
                        'port': int(env_port),
                        'user': env_user,
                        'password': env_password,
                        'database': db_name,
                        'server_settings': {
                            'application_name': 'ava_olo_diagnostics'
                        }
                    }
                    
                    # Add SSL configuration
                    if ssl_mode != 'disable':
                        connection_params['ssl'] = ssl_mode
                    else:
                        connection_params['ssl'] = False
                    
                    # Attempt connection with timeout
                    print(f"  Connecting with SSL {ssl_mode}...")
                    conn = await asyncio.wait_for(
                        asyncpg.connect(**connection_params), 
                        timeout=10.0
                    )
                    
                    # Test basic queries
                    print("  Testing basic queries...")
                    
                    # 1. Check if connected
                    version = await conn.fetchval("SELECT version()")
                    attempt_result["details"]["postgres_version"] = version[:50]
                    
                    # 2. Count tables
                    table_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                    )
                    attempt_result["details"]["table_count"] = table_count
                    
                    # 3. List table names
                    tables = await conn.fetch(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
                    )
                    table_names = [row['tablename'] for row in tables]
                    attempt_result["details"]["tables"] = table_names
                    
                    # 4. Check for farmers table specifically
                    if 'farmers' in table_names:
                        farmer_count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
                        attempt_result["details"]["farmer_count"] = farmer_count
                        
                        # Get farmers table columns
                        farmer_columns = await conn.fetch("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns 
                            WHERE table_name = 'farmers' 
                            ORDER BY ordinal_position
                        """)
                        attempt_result["details"]["farmer_columns"] = [
                            dict(row) for row in farmer_columns
                        ]
                        
                        print(f"  ✅ SUCCESS! Found {farmer_count} farmers")
                        print(f"    Tables: {len(table_names)}")
                        print(f"    Farmer columns: {[col['column_name'] for col in farmer_columns]}")
                    else:
                        print(f"  ⚠️ Connected but no farmers table")
                        print(f"    Available tables: {table_names}")
                    
                    await conn.close()
                    attempt_result["status"] = "success"
                    
                    # If this works, save as working connection
                    if 'farmers' in table_names:
                        diagnostics["working_connection"] = {
                            "host": host,
                            "database": db_name,
                            "ssl_mode": ssl_mode,
                            "farmer_count": attempt_result["details"]["farmer_count"],
                            "farmer_columns": [col['column_name'] for col in farmer_columns]
                        }
                    
                except asyncio.TimeoutError:
                    print("  ❌ TIMEOUT (10s)")
                    attempt_result["status"] = "timeout"
                    attempt_result["error"] = "Connection timeout after 10 seconds"
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ ERROR: {error_msg[:50]}...")
                    attempt_result["status"] = "failed"
                    attempt_result["error"] = error_msg
                
                diagnostics["connection_attempts"].append(attempt_result)
    
    # 3. Generate Recommendations
    print("\n💡 3. RECOMMENDATIONS")
    print("-" * 40)
    
    working_connections = [
        attempt for attempt in diagnostics["connection_attempts"] 
        if attempt["status"] == "success"
    ]
    
    if working_connections:
        best_connection = working_connections[0]
        print("✅ WORKING CONNECTION FOUND!")
        print(f"   Host: {best_connection['host']}")
        print(f"   Database: {best_connection['database']}")
        print(f"   SSL Mode: {best_connection['ssl_mode']}")
        
        if "farmer_count" in best_connection.get("details", {}):
            print(f"   Farmers: {best_connection['details']['farmer_count']}")
            
        diagnostics["recommendations"].append({
            "type": "success",
            "message": "Working connection found",
            "action": f"Use database '{best_connection['database']}' with SSL '{best_connection['ssl_mode']}'"
        })
        
        # Check if columns are different than expected
        if "farmer_columns" in diagnostics.get("working_connection", {}):
            columns = diagnostics["working_connection"]["farmer_columns"]
            if 'farmer_id' not in columns and 'id' in columns:
                diagnostics["recommendations"].append({
                    "type": "column_fix",
                    "message": "Use 'id' instead of 'farmer_id'",
                    "action": "Update queries to use 'id' as primary key"
                })
                print("   ⚠️ Use 'id' instead of 'farmer_id' in queries")
    else:
        print("❌ NO WORKING CONNECTIONS FOUND")
        
        # Analyze failures
        timeout_count = len([a for a in diagnostics["connection_attempts"] if a["status"] == "timeout"])
        error_count = len([a for a in diagnostics["connection_attempts"] if a["status"] == "failed"])
        
        if timeout_count > 0:
            diagnostics["recommendations"].append({
                "type": "network",
                "message": "Connection timeouts detected",
                "action": "Check VPC configuration and security groups"
            })
            print("   🌐 Network issue: Check VPC configuration")
            
        if error_count > 0:
            # Get most common error
            errors = [a["error"] for a in diagnostics["connection_attempts"] if a.get("error")]
            if errors:
                common_error = max(set(errors), key=errors.count)
                print(f"   🚨 Common error: {common_error[:100]}")
                
                if "does not exist" in common_error:
                    diagnostics["recommendations"].append({
                        "type": "database",
                        "message": "Database name issue",
                        "action": "Try 'postgres' as default database name"
                    })
                elif "authentication" in common_error.lower():
                    diagnostics["recommendations"].append({
                        "type": "auth",
                        "message": "Authentication issue",
                        "action": "Check DB_USER and DB_PASSWORD environment variables"
                    })
    
    # 4. Environment Variable Issues
    missing_required = [
        var for var in required_vars 
        if not diagnostics["environment_check"][var]["present"]
    ]
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {missing_required}")
        diagnostics["recommendations"].append({
            "type": "environment",
            "message": f"Missing variables: {missing_required}",
            "action": "Set missing environment variables in AWS App Runner"
        })
    
    return diagnostics

async def main():
    """Main function"""
    try:
        result = await diagnose_connection_comprehensive()
        
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        # Print JSON for Claude Code
        print("\n📋 Results for Claude Code:")
        print(json.dumps(result, indent=2, default=str))
        
        return result
        
    except Exception as e:
        print(f"🚨 Diagnostic failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())