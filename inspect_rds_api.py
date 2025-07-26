#!/usr/bin/env python3
"""
FastAPI service for RDS database inspection
Deployable to AWS ECS
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RDS Database Inspector",
    description="Inspect RDS PostgreSQL database structure",
    version="1.0.0"
)

def get_database_config():
    """Get database configuration from environment variables"""
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "database": os.environ.get("DB_NAME", "ava_olo"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", "")
    }

def get_db_connection():
    """Create database connection"""
    config = get_database_config()
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RDS Database Inspector",
        "version": "1.0.0",
        "endpoints": {
            "/inspect": "Full database structure inspection",
            "/schemas": "List all schemas",
            "/tables/{schema}": "List tables in a schema",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/inspect")
async def inspect_database():
    """Complete database structure inspection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Initialize result
        result = {
            "inspection_timestamp": datetime.now().isoformat(),
            "database_name": get_database_config()["database"],
            "schemas": {},
            "summary": {
                "total_schemas": 0,
                "total_tables": 0,
                "total_rows": 0,
                "schemas_with_tables": 0
            },
            "tables_outside_public": []
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
            
            # Get tables
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
            
            # Get basic info for each table
            for table_name in tables:
                # Get column count
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                """, (schema_name, table_name))
                column_count = cursor.fetchone()["count"]
                
                # Get row count
                row_count = 0
                try:
                    if schema_name == 'public':
                        cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}"')
                    else:
                        cursor.execute(f'SELECT COUNT(*) as count FROM "{schema_name}"."{table_name}"')
                    row_count = cursor.fetchone()["count"]
                except:
                    pass
                
                schema_info["tables"][table_name] = {
                    "column_count": column_count,
                    "row_count": row_count
                }
                schema_info["total_rows"] += row_count
                
                # Track non-public tables
                if schema_name != 'public' and row_count > 0:
                    result["tables_outside_public"].append({
                        "schema": schema_name,
                        "table": table_name,
                        "row_count": row_count
                    })
            
            result["schemas"][schema_name] = schema_info
            result["summary"]["total_tables"] += schema_info["table_count"]
            result["summary"]["total_rows"] += schema_info["total_rows"]
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Database inspection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schemas")
async def list_schemas():
    """List all database schemas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
            ORDER BY schema_name
        """)
        
        schemas = [row["schema_name"] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "schemas": schemas,
            "count": len(schemas)
        }
        
    except Exception as e:
        logger.error(f"Failed to list schemas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables/{schema_name}")
async def list_tables(schema_name: str):
    """List all tables in a specific schema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_schema)||'.'||quote_ident(table_name))) as size
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema_name,))
        
        tables = []
        for row in cursor.fetchall():
            # Get row count
            try:
                if schema_name == 'public':
                    cursor.execute(f'SELECT COUNT(*) as count FROM "{row["table_name"]}"')
                else:
                    cursor.execute(f'SELECT COUNT(*) as count FROM "{schema_name}"."{row["table_name"]}"')
                row_count = cursor.fetchone()["count"]
            except:
                row_count = 0
            
            tables.append({
                "name": row["table_name"],
                "size": row["size"],
                "row_count": row_count
            })
        
        cursor.close()
        conn.close()
        
        return {
            "schema": schema_name,
            "tables": tables,
            "count": len(tables)
        }
        
    except Exception as e:
        logger.error(f"Failed to list tables in schema {schema_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8006"))
    print(f"🔍 Starting RDS Database Inspector on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)