#!/usr/bin/env python3
"""
Standalone RDS Database Structure Inspector for AWS ECS
Returns database structure information as JSON
"""
import os
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor

def get_database_config():
    """Get database configuration from environment variables"""
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "database": os.environ.get("DB_NAME", "ava_olo"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", "")
    }

def inspect_database_structure() -> Dict[str, Any]:
    """
    Inspect RDS PostgreSQL database structure
    Returns JSON with all schemas, tables, and analysis
    """
    config = get_database_config()
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Initialize result structure
        result = {
            "inspection_timestamp": datetime.now().isoformat(),
            "database_name": config["database"],
            "connection_info": {
                "host": config["host"],
                "port": config["port"],
                "user": config["user"]
            },
            "schemas": {},
            "summary": {
                "total_schemas": 0,
                "total_tables": 0,
                "total_rows": 0,
                "schemas_with_tables": 0
            },
            "tables_outside_public": [],
            "analysis": {}
        }
        
        # Get all schemas
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
            ORDER BY schema_name
        """)
        schemas = [row["schema_name"] for row in cursor.fetchall()]
        result["summary"]["total_schemas"] = len(schemas)
        
        # Inspect each schema
        for schema_name in schemas:
            schema_info = {
                "tables": {},
                "table_count": 0,
                "total_rows": 0
            }
            
            # Get tables in this schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema_name,))
            
            tables = [row["table_name"] for row in cursor.fetchall()]
            schema_info["table_count"] = len(tables)
            
            if len(tables) > 0:
                result["summary"]["schemas_with_tables"] += 1
            
            # Inspect each table
            for table_name in tables:
                table_info = {"columns": [], "row_count": 0}
                
                # Get columns
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, table_name))
                
                table_info["columns"] = [
                    {
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col["is_nullable"] == "YES"
                    }
                    for col in cursor.fetchall()
                ]
                
                # Get row count
                try:
                    if schema_name == 'public':
                        cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}"')
                    else:
                        cursor.execute(f'SELECT COUNT(*) as count FROM "{schema_name}"."{table_name}"')
                    
                    table_info["row_count"] = cursor.fetchone()["count"]
                    schema_info["total_rows"] += table_info["row_count"]
                except Exception as e:
                    table_info["row_count"] = 0
                    table_info["error"] = str(e)
                
                schema_info["tables"][table_name] = table_info
                
                # Track tables outside public
                if schema_name != 'public' and table_info["row_count"] > 0:
                    result["tables_outside_public"].append({
                        "schema": schema_name,
                        "table": table_name,
                        "row_count": table_info["row_count"]
                    })
            
            result["schemas"][schema_name] = schema_info
            result["summary"]["total_tables"] += schema_info["table_count"]
            result["summary"]["total_rows"] += schema_info["total_rows"]
        
        # Analysis
        result["analysis"] = {
            "has_non_public_tables": len(result["tables_outside_public"]) > 0,
            "non_public_table_count": len(result["tables_outside_public"]),
            "schemas_with_data": [
                schema_name for schema_name, info in result["schemas"].items()
                if info["total_rows"] > 0
            ]
        }
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "inspection_timestamp": datetime.now().isoformat(),
            "database_config": {
                "host": config["host"],
                "port": config["port"],
                "database": config["database"]
            }
        }

def main():
    """Main function for standalone execution"""
    print("🔍 RDS Database Structure Inspector")
    print("=" * 50)
    
    # Run inspection
    result = inspect_database_structure()
    
    # Print JSON result
    print(json.dumps(result, indent=2, default=str))
    
    # Save to file if requested
    if "--save" in sys.argv:
        filename = f"rds_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main()