#!/usr/bin/env python3
"""
Database Dashboard Routes
Provides database query functionality directly in agricultural-core
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any

from ..core.config import VERSION
from ..core.simple_db import execute_simple_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/database", tags=["database-dashboard"])
templates = Jinja2Templates(directory="templates")

class NLQRequest(BaseModel):
    question: str

class SQLRequest(BaseModel):
    query: str

@router.get("", response_class=HTMLResponse)
async def database_dashboard(request: Request):
    """Main database dashboard page"""
    try:
        return templates.TemplateResponse("database_dashboard.html", {
            "request": request,
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Error rendering database dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sql", response_class=JSONResponse)
async def execute_sql_query(request: SQLRequest):
    """Execute a raw SQL query (SELECT only for safety)"""
    try:
        sql_query = request.query.strip()
        
        # Safety check - only allow SELECT queries
        if not sql_query.upper().startswith('SELECT'):
            return JSONResponse(content={
                "success": False,
                "error": "Only SELECT queries are allowed for safety reasons"
            })
        
        # Additional safety checks
        forbidden_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
        query_upper = sql_query.upper()
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                return JSONResponse(content={
                    "success": False,
                    "error": f"Query contains forbidden keyword: {keyword}"
                })
        
        # Execute the query
        result = execute_simple_query(sql_query, ())
        
        if result.get('success'):
            rows = result.get('rows', [])
            columns = result.get('columns', [])
            
            # Convert rows to dict format
            data = []
            for row in rows:
                row_dict = {}
                # Ensure we don't go out of bounds
                for i in range(min(len(columns), len(row))):
                    col = columns[i]
                    value = row[i]
                    # Convert datetime to string if needed
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, (int, float)):
                        value = value
                    elif value is None:
                        value = ""
                    else:
                        value = str(value)
                    row_dict[col] = value
                
                # Add any missing columns as empty
                for col in columns[len(row):]:
                    row_dict[col] = ""
                    
                data.append(row_dict)
            
            return JSONResponse(content={
                "success": True,
                "data": data,
                "columns": columns,
                "query": sql_query
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Query execution failed')
            })
            
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

@router.post("/nlq", response_class=JSONResponse)
async def natural_language_query(request: NLQRequest):
    """Convert natural language to SQL and execute"""
    try:
        # Convert natural language to SQL
        sql_query = convert_nlq_to_sql(request.question)
        
        if not sql_query:
            return JSONResponse(content={
                "success": False,
                "error": "Could not understand the query. Please try rephrasing."
            })
        
        # Execute the query
        result = execute_simple_query(sql_query, ())
        
        if result.get('success'):
            # Format the results
            rows = result.get('rows', [])
            columns = result.get('columns', [])
            
            # Convert rows to dict format
            data = []
            for row in rows:
                row_dict = {}
                # Ensure we don't go out of bounds
                for i in range(min(len(columns), len(row))):
                    col = columns[i]
                    value = row[i]
                    # Convert datetime to string if needed
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, (int, float)):
                        value = value
                    elif value is None:
                        value = ""
                    else:
                        value = str(value)
                    row_dict[col] = value
                
                # Add any missing columns as empty
                for col in columns[len(row):]:
                    row_dict[col] = ""
                    
                data.append(row_dict)
            
            return JSONResponse(content={
                "success": True,
                "data": data,
                "columns": columns,
                "query": sql_query
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Query execution failed')
            })
            
    except Exception as e:
        logger.error(f"Error in NLQ: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

@router.get("/quick/{query_type}", response_class=JSONResponse)
async def quick_query(query_type: str):
    """Execute predefined quick queries"""
    try:
        queries = {
            "total-farmers": "SELECT COUNT(*) as total_farmers FROM farmers",
            "recent-farmers": """
                SELECT id, farm_name, manager_name, manager_last_name, 
                       city, country, created_at 
                FROM farmers 
                ORDER BY created_at DESC 
                LIMIT 10
            """,
            "all-fields": """
                SELECT f.id, f.field_name, f.area_ha, f.country,
                       fa.manager_name, fa.manager_last_name
                FROM fields f
                LEFT JOIN farmers fa ON f.farmer_id = fa.id
                ORDER BY f.id DESC
                LIMIT 100
            """,
            "farmers-by-country": """
                SELECT country, COUNT(*) as farmer_count 
                FROM farmers 
                WHERE country IS NOT NULL
                GROUP BY country 
                ORDER BY farmer_count DESC
            """,
            "field-statistics": """
                SELECT 
                    COUNT(*) as total_fields,
                    ROUND(SUM(area_ha)::numeric, 2) as total_area_ha,
                    ROUND(AVG(area_ha)::numeric, 2) as avg_area_ha,
                    ROUND(MIN(area_ha)::numeric, 2) as min_area_ha,
                    ROUND(MAX(area_ha)::numeric, 2) as max_area_ha
                FROM fields
                WHERE area_ha IS NOT NULL
            """
        }
        
        sql_query = queries.get(query_type)
        if not sql_query:
            return JSONResponse(content={
                "success": False,
                "error": f"Unknown query type: {query_type}"
            })
        
        result = execute_simple_query(sql_query, ())
        
        if result.get('success'):
            rows = result.get('rows', [])
            columns = result.get('columns', [])
            
            # Convert to dict format with proper type handling
            data = []
            for row in rows:
                row_dict = {}
                # Ensure we don't go out of bounds
                for i in range(min(len(columns), len(row))):
                    col = columns[i]
                    value = row[i]
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, (int, float)):
                        value = value
                    elif value is None:
                        value = ""
                    else:
                        value = str(value)
                    row_dict[col] = value
                # Add any missing columns as empty
                for col in columns[len(row):]:
                    row_dict[col] = ""
                data.append(row_dict)
            
            return JSONResponse(content={
                "success": True,
                "data": data,
                "columns": columns,
                "query": sql_query
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Query execution failed')
            })
            
    except Exception as e:
        logger.error(f"Error in quick query: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

@router.get("/search-farmer", response_class=JSONResponse)
async def search_farmer(name: str):
    """Search for a farmer by name"""
    try:
        sql_query = """
            SELECT id, farm_name, manager_name, manager_last_name,
                   city, country, phone, wa_phone_number, email, created_at
            FROM farmers 
            WHERE LOWER(manager_name) LIKE LOWER(%s) 
               OR LOWER(manager_last_name) LIKE LOWER(%s)
               OR LOWER(farm_name) LIKE LOWER(%s)
               OR LOWER(CONCAT(manager_name, ' ', manager_last_name)) LIKE LOWER(%s)
            ORDER BY created_at DESC
            LIMIT 20
        """
        
        search_pattern = f"%{name}%"
        result = execute_simple_query(sql_query, (search_pattern, search_pattern, search_pattern, search_pattern))
        
        if result.get('success'):
            rows = result.get('rows', [])
            columns = result.get('columns', [])
            
            # Convert to dict format with proper type handling
            data = []
            for row in rows:
                row_dict = {}
                # Ensure we don't go out of bounds
                for i in range(min(len(columns), len(row))):
                    col = columns[i]
                    value = row[i]
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, (int, float)):
                        value = value
                    elif value is None:
                        value = ""
                    else:
                        value = str(value)
                    row_dict[col] = value
                # Add any missing columns as empty
                for col in columns[len(row):]:
                    row_dict[col] = ""
                data.append(row_dict)
            
            # If farmer found, also get their fields
            if data and len(data) > 0:
                farmer_ids = [d['id'] for d in data]
                fields_query = """
                    SELECT farmer_id, id as field_id, field_name, area_ha, 
                           latitude, longitude, created_at
                    FROM fields 
                    WHERE farmer_id = ANY(%s)
                    ORDER BY farmer_id, field_name
                """
                fields_result = execute_simple_query(fields_query, (farmer_ids,))
                
                if fields_result.get('success'):
                    fields_data = []
                    fields_rows = fields_result.get('rows', [])
                    fields_columns = fields_result.get('columns', [])
                    
                    for row in fields_rows:
                        field_dict = {}
                        for i, col in enumerate(fields_columns):
                            value = row[i] if i < len(row) else None
                            if hasattr(value, 'isoformat'):
                                value = value.isoformat()
                            elif isinstance(value, (int, float)):
                                value = value
                            elif value is None:
                                value = ""
                            else:
                                value = str(value)
                            field_dict[col] = value
                        fields_data.append(field_dict)
                    
                    # Add fields to farmers
                    for farmer in data:
                        farmer['fields'] = [f for f in fields_data if f['farmer_id'] == farmer['id']]
            
            return JSONResponse(content={
                "success": True,
                "data": data,
                "columns": columns,
                "query": f"Search for: {name}"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'Search failed')
            })
            
    except Exception as e:
        logger.error(f"Error in farmer search: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

def convert_nlq_to_sql(question: str) -> Optional[str]:
    """
    Simple NLQ to SQL conversion
    This is a basic implementation - in production you'd use OpenAI or similar
    """
    question_lower = question.lower()
    
    # Simple pattern matching for common queries
    if "edi kante" in question_lower:
        if "field" in question_lower:
            return """
                SELECT f.id, f.field_name, f.area_ha, f.country,
                       fa.manager_name, fa.manager_last_name
                FROM fields f
                JOIN farmers fa ON f.farmer_id = fa.id
                WHERE LOWER(fa.manager_name) LIKE '%edi%' 
                   OR LOWER(fa.manager_last_name) LIKE '%kante%'
            """
        else:
            return """
                SELECT * FROM farmers 
                WHERE LOWER(manager_name) LIKE '%edi%' 
                   OR LOWER(manager_last_name) LIKE '%kante%'
            """
    
    elif "how many farmers" in question_lower:
        if "from" in question_lower:
            # Extract country name (simple approach)
            parts = question_lower.split("from")
            if len(parts) > 1:
                country = parts[1].strip().strip('?').strip('.').title()
                return f"SELECT COUNT(*) as farmer_count FROM farmers WHERE country = '{country}'"
        return "SELECT COUNT(*) as total_farmers FROM farmers"
    
    elif "recent" in question_lower and "registration" in question_lower:
        return """
            SELECT id, farm_name, manager_name, manager_last_name, 
                   city, country, created_at 
            FROM farmers 
            ORDER BY created_at DESC 
            LIMIT 20
        """
    
    elif "all fields" in question_lower or "list fields" in question_lower:
        return """
            SELECT f.*, fa.manager_name, fa.manager_last_name
            FROM fields f
            LEFT JOIN farmers fa ON f.farmer_id = fa.id
            ORDER BY f.id DESC
            LIMIT 100
        """
    
    elif "crop" in question_lower:
        return """
            SELECT DISTINCT crop_name, COUNT(*) as count
            FROM field_crops
            GROUP BY crop_name
            ORDER BY count DESC
        """
    
    # Default: try to search in farmers
    return f"""
        SELECT * FROM farmers 
        WHERE LOWER(manager_name) LIKE '%{question_lower}%' 
           OR LOWER(manager_last_name) LIKE '%{question_lower}%'
           OR LOWER(farm_name) LIKE '%{question_lower}%'
        LIMIT 20
    """