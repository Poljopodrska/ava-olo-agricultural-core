#!/usr/bin/env python3
"""
Database API routes for AVA OLO Monitoring Dashboards
Handles database queries, schema info, and data operations
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import json
import traceback
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.database_manager import get_db_manager, execute_db_query
from ..core.config import VERSION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/database", tags=["database"])

class NaturalQueryRequest(BaseModel):
    query: str

@router.get("/test")
async def test_database():
    """Test database connection and return basic metrics"""
    try:
        db_manager = get_db_manager()
        
        # Test connection
        if not db_manager.test_connection():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Get metrics
        metrics = db_manager.get_dashboard_metrics()
        
        return JSONResponse({
            "status": "connected",
            "farmers": metrics.get('farmer_count', 0),
            "total_hectares": round(metrics.get('total_hectares', 0), 2),
            "version": VERSION,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "farmers": "--",
            "total_hectares": "--"
        }, status_code=500)

@router.get("/schema")
async def get_database_schema():
    """Get database schema information"""
    try:
        db_manager = get_db_manager()
        
        # Query to get all tables and their columns
        schema_query = """
        SELECT 
            t.table_name,
            array_agg(
                json_build_object(
                    'column_name', c.column_name,
                    'data_type', c.data_type,
                    'is_nullable', c.is_nullable,
                    'column_default', c.column_default
                ) ORDER BY c.ordinal_position
            ) as columns
        FROM information_schema.tables t
        JOIN information_schema.columns c 
            ON t.table_name = c.table_name 
            AND t.table_schema = c.table_schema
        WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
        GROUP BY t.table_name
        ORDER BY t.table_name;
        """
        
        result = db_manager.execute_query(schema_query)
        
        schema = {}
        for row in result.get('rows', []):
            table_name, columns = row
            schema[table_name] = columns
        
        return JSONResponse({
            "schema": schema,
            "table_count": len(schema),
            "version": VERSION,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Schema query failed: {e}")
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.post("/query")
async def execute_database_query(request: NaturalQueryRequest):
    """Execute a database query"""
    try:
        db_manager = get_db_manager()
        
        # Basic SQL injection protection
        query = request.query.strip()
        if not query:
            raise ValueError("Query cannot be empty")
        
        # Only allow SELECT queries for safety
        if not query.upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Execute query
        result = db_manager.execute_query(query)
        
        return JSONResponse({
            "success": True,
            "columns": result.get('columns', []),
            "rows": result.get('rows', []),
            "row_count": len(result.get('rows', [])),
            "query": query,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "query": request.query
        }, status_code=400)

# Agricultural specific endpoints
agricultural_router = APIRouter(prefix="/api/agricultural", tags=["agricultural"])

@agricultural_router.get("/farmer-count")
async def get_farmer_count():
    """Get total farmer count"""
    try:
        db_manager = get_db_manager()
        count = db_manager.get_farmer_count()
        return JSONResponse({"count": count})
    except Exception as e:
        return JSONResponse({"error": str(e), "count": 0}, status_code=500)

@agricultural_router.get("/farmers")
async def get_farmers(limit: int = 10, offset: int = 0):
    """Get list of farmers"""
    try:
        db_manager = get_db_manager()
        
        query = """
        SELECT farmer_id, first_name, last_name, phone_number, 
               location, created_at
        FROM farmers
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        result = db_manager.execute_query(query, (limit, offset))
        
        farmers = []
        for row in result.get('rows', []):
            farmers.append({
                "farmer_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "phone_number": row[3],
                "location": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            })
        
        return JSONResponse({
            "farmers": farmers,
            "count": len(farmers),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        logger.error(f"Failed to get farmers: {e}")
        return JSONResponse({"error": str(e), "farmers": []}, status_code=500)

@agricultural_router.get("/farmer/{farmer_id}")
async def get_farmer_details(farmer_id: str):
    """Get detailed information about a farmer"""
    try:
        db_manager = get_db_manager()
        
        # Get farmer info
        farmer_query = """
        SELECT farmer_id, first_name, last_name, phone_number, 
               location, created_at, updated_at
        FROM farmers
        WHERE farmer_id = %s
        """
        
        farmer_result = db_manager.execute_query(farmer_query, (farmer_id,))
        if not farmer_result.get('rows'):
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        farmer_row = farmer_result['rows'][0]
        farmer_data = {
            "farmer_id": farmer_row[0],
            "first_name": farmer_row[1],
            "last_name": farmer_row[2],
            "phone_number": farmer_row[3],
            "location": farmer_row[4],
            "created_at": farmer_row[5].isoformat() if farmer_row[5] else None,
            "updated_at": farmer_row[6].isoformat() if farmer_row[6] else None
        }
        
        # Get fields
        fields_query = """
        SELECT field_id, field_name, area_hectares, location
        FROM fields
        WHERE farmer_id = %s
        ORDER BY created_at DESC
        """
        
        fields_result = db_manager.execute_query(fields_query, (farmer_id,))
        fields = []
        for row in fields_result.get('rows', []):
            fields.append({
                "field_id": row[0],
                "field_name": row[1],
                "area_hectares": float(row[2]) if row[2] else 0,
                "location": row[3]
            })
        
        farmer_data['fields'] = fields
        farmer_data['total_hectares'] = sum(f['area_hectares'] for f in fields)
        
        return JSONResponse(farmer_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get farmer details: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# Debug endpoints
debug_router = APIRouter(prefix="/api/v1/debug", tags=["debug"])

@debug_router.get("/deployment")
async def debug_deployment():
    """Debug deployment information"""
    return JSONResponse({
        "version": VERSION,
        "file": __file__,
        "module": __name__,
        "timestamp": datetime.now().isoformat()
    })

@debug_router.get("/database-test")
async def debug_database_test():
    """Test database connection with detailed info"""
    try:
        db_manager = get_db_manager()
        
        # Test basic connection
        connection_ok = db_manager.test_connection()
        
        # Get table list
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """
        
        tables_result = db_manager.execute_query(tables_query)
        tables = [row[0] for row in tables_result.get('rows', [])]
        
        # Get sample data
        sample_data = {}
        for table in ['farmers', 'fields', 'tasks'][:3]:  # Limit to 3 tables
            if table in tables:
                try:
                    count_result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table}")
                    count = count_result['rows'][0][0] if count_result['rows'] else 0
                    sample_data[table] = count
                except:
                    sample_data[table] = "error"
        
        return JSONResponse({
            "connection_ok": connection_ok,
            "tables": tables,
            "table_count": len(tables),
            "sample_counts": sample_data,
            "pool_available": db_manager.pool_initialized,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)