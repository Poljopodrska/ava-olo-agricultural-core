#!/usr/bin/env python3
"""
Database Explorer Routes
Provides table browsing and data viewing functionality
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
from typing import Optional, List, Dict, Any

from ..core.config import VERSION
from ..core.simple_db import execute_simple_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/database/explorer", tags=["database-explorer"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def database_explorer(request: Request):
    """Main database explorer page"""
    try:
        return templates.TemplateResponse("database_explorer.html", {
            "request": request,
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Error rendering database explorer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables", response_class=JSONResponse)
async def get_tables():
    """Get list of all tables with row counts"""
    try:
        # Query to get all tables from information schema
        query = """
            SELECT 
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        result = execute_simple_query(query, ())
        
        if not result.get('success'):
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Failed to fetch tables')
            })
        
        tables = []
        for row in result.get('rows', []):
            table_name = row[0]
            
            # Get row count for each table
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = execute_simple_query(count_query, ())
            
            row_count = 0
            if count_result.get('success') and count_result.get('rows'):
                row_count = count_result['rows'][0][0]
            
            tables.append({
                "name": table_name,
                "row_count": row_count
            })
        
        return JSONResponse(content={
            "success": True,
            "tables": tables
        })
        
    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

@router.get("/schema/{table_name}", response_class=JSONResponse)
async def get_table_schema(table_name: str):
    """Get schema information for a specific table"""
    try:
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').isalnum():
            return JSONResponse(content={
                "success": False,
                "error": "Invalid table name"
            })
        
        # Query to get column information
        query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
                AND table_name = %s
            ORDER BY ordinal_position
        """
        
        result = execute_simple_query(query, (table_name,))
        
        if not result.get('success'):
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Failed to fetch schema')
            })
        
        columns = []
        for row in result.get('rows', []):
            col_info = {
                "column_name": row[0],
                "data_type": row[1],
                "max_length": row[2],
                "is_nullable": row[3],
                "default": row[4]
            }
            
            # Format data type display
            if col_info['max_length']:
                col_info['data_type'] = f"{col_info['data_type']}({col_info['max_length']})"
            
            columns.append(col_info)
        
        return JSONResponse(content={
            "success": True,
            "table_name": table_name,
            "columns": columns
        })
        
    except Exception as e:
        logger.error(f"Error fetching schema for table {table_name}: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

@router.get("/data/{table_name}", response_class=JSONResponse)
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get data from a specific table with pagination"""
    try:
        # Validate table name
        if not table_name.replace('_', '').isalnum():
            return JSONResponse(content={
                "success": False,
                "error": "Invalid table name"
            })
        
        # First get total count
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        count_result = execute_simple_query(count_query, ())
        
        total_rows = 0
        if count_result.get('success') and count_result.get('rows'):
            total_rows = count_result['rows'][0][0]
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get paginated data
        data_query = f"""
            SELECT * FROM {table_name}
            ORDER BY 1
            LIMIT %s OFFSET %s
        """
        
        result = execute_simple_query(data_query, (limit, offset))
        
        if not result.get('success'):
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Failed to fetch data')
            })
        
        rows = result.get('rows', [])
        columns = result.get('columns', [])
        
        # Convert rows to dict format with proper type handling
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i] if i < len(row) else None
                
                # Handle different data types
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                elif isinstance(value, (int, float)):
                    value = value
                elif value is None:
                    value = None
                else:
                    value = str(value)
                    
                row_dict[col] = value
            data.append(row_dict)
        
        return JSONResponse(content={
            "success": True,
            "rows": data,
            "columns": columns,
            "total_rows": total_rows,
            "page": page,
            "limit": limit,
            "total_pages": (total_rows + limit - 1) // limit if total_rows > 0 else 1
        })
        
    except Exception as e:
        logger.error(f"Error fetching data for table {table_name}: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })