"""
AVA OLO Database Dashboard Module
Implements two-level database dashboard with data retrieval and population options
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
import json
import logging
import time
from modules.core.database_manager import get_db_manager
from modules.core.config import config
import os
import openai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/database", tags=["database_dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def database_dashboard(request: Request):
    """Main database dashboard - level 1 selection"""
    return templates.TemplateResponse("database_dashboard_landing.html", {
        "request": request
    })

@router.get("/retrieval", response_class=HTMLResponse)
async def database_retrieval(request: Request):
    """Data retrieval dashboard - level 2"""
    return templates.TemplateResponse("database_retrieval.html", {
        "request": request
    })

@router.get("/population", response_class=HTMLResponse)
async def database_population(request: Request):
    """Database population dashboard - level 2 (placeholder)"""
    return templates.TemplateResponse("database_population.html", {
        "request": request
    })

# API endpoints for database operations

@router.get("/api/quick-queries/{query_type}", response_class=JSONResponse)
async def execute_quick_query(query_type: str, farmer_id: Optional[int] = None, field_ids: Optional[str] = None):
    """Execute predefined quick queries"""
    db_manager = get_db_manager()
    
    try:
        if query_type == "total-farmers":
            query = "SELECT COUNT(*) as total FROM farmers WHERE subscription_status = 'active'"
            result = await db_manager.execute_query(query)
            
            if result and result.get('success'):
                total = result.get('data', [[0]])[0][0]
                return {
                    "success": True,
                    "data": {"total_farmers": total},
                    "query": query
                }
                
        elif query_type == "all-farmers":
            query = """
            SELECT id, name, phone_number, city, primary_occupation, 
                   size_hectares, created_at
            FROM farmers 
            WHERE subscription_status = 'active'
            ORDER BY created_at DESC
            LIMIT 100
            """
            result = await db_manager.execute_query(query)
            
            if result and result.get('success'):
                farmers = []
                for row in result.get('data', []):
                    farmers.append({
                        'id': row[0],
                        'name': row[1],
                        'phone_number': row[2],
                        'city': row[3],
                        'primary_occupation': row[4],
                        'size_hectares': float(row[5]) if row[5] else 0,
                        'created_at': row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else ''
                    })
                return {
                    "success": True,
                    "data": farmers,
                    "query": query
                }
                
        elif query_type == "farmer-fields" and farmer_id:
            query = """
            SELECT f.id, f.field_name, f.size_hectares, f.crop_type, 
                   f.planting_date, f.harvest_date, f.created_at
            FROM fields f
            WHERE f.farmer_id = %s
            ORDER BY f.created_at DESC
            """
            result = await db_manager.execute_query(query, (farmer_id,))
            
            if result and result.get('success'):
                fields = []
                for row in result.get('data', []):
                    fields.append({
                        'id': row[0],
                        'field_name': row[1],
                        'size_hectares': float(row[2]) if row[2] else 0,
                        'crop_type': row[3],
                        'planting_date': row[4].strftime('%Y-%m-%d') if row[4] else None,
                        'harvest_date': row[5].strftime('%Y-%m-%d') if row[5] else None,
                        'created_at': row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else ''
                    })
                return {
                    "success": True,
                    "data": fields,
                    "query": query.replace('%s', str(farmer_id))
                }
                
        elif query_type == "field-tasks" and field_ids:
            # Parse comma-separated field IDs
            ids = [int(id.strip()) for id in field_ids.split(',') if id.strip().isdigit()]
            if not ids:
                return {"success": False, "error": "Invalid field IDs"}
            
            placeholders = ','.join(['%s'] * len(ids))
            query = f"""
            SELECT t.id, t.field_id, t.task_type, t.task_description,
                   t.due_date, t.status, t.created_at, f.field_name
            FROM tasks t
            JOIN fields f ON t.field_id = f.id
            WHERE t.field_id IN ({placeholders})
            ORDER BY t.due_date ASC
            """
            
            result = await db_manager.execute_query(query, tuple(ids))
            
            if result and result.get('success'):
                tasks = []
                for row in result.get('data', []):
                    tasks.append({
                        'id': row[0],
                        'field_id': row[1],
                        'task_type': row[2],
                        'task_description': row[3],
                        'due_date': row[4].strftime('%Y-%m-%d') if row[4] else None,
                        'status': row[5],
                        'created_at': row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else '',
                        'field_name': row[7]
                    })
                return {
                    "success": True,
                    "data": tasks,
                    "query": query.replace(placeholders, ','.join(map(str, ids)))
                }
                
        else:
            return {"success": False, "error": "Invalid query type or missing parameters"}
            
    except Exception as e:
        logger.error(f"Error executing quick query {query_type}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/api/natural-query", response_class=JSONResponse)
async def execute_natural_query(request: Request):
    """Convert natural language to SQL and execute"""
    try:
        data = await request.json()
        question = data.get('question', '')
        
        if not question:
            return {"success": False, "error": "No question provided"}
        
        # Generate SQL using LLM
        sql_query = await generate_sql_from_natural_language(question)
        
        if not sql_query:
            return {
                "success": False,
                "error": "Could not generate SQL query from your question"
            }
        
        # Validate query is safe (SELECT only)
        if not is_safe_query(sql_query):
            return {
                "success": False,
                "error": "Generated query contains unsafe operations. Only SELECT queries are allowed."
            }
        
        # Execute the query
        db_manager = get_db_manager()
        start_time = time.time()
        result = await db_manager.execute_query(sql_query)
        execution_time = int((time.time() - start_time) * 1000)
        
        if result and result.get('success'):
            # Format results for display
            data = result.get('data', [])
            columns = result.get('columns', [])
            
            formatted_data = []
            for row in data:
                formatted_row = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert datetime objects to strings
                    if hasattr(value, 'strftime'):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                    formatted_row[col] = value
                formatted_data.append(formatted_row)
            
            return {
                "success": True,
                "data": formatted_data,
                "columns": columns,
                "query": sql_query,
                "row_count": len(formatted_data),
                "execution_time": execution_time
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Query execution failed'),
                "query": sql_query
            }
            
    except Exception as e:
        logger.error(f"Error executing natural query: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_sql_from_natural_language(question: str) -> Optional[str]:
    """Use OpenAI to convert natural language to SQL"""
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.error("OpenAI API key not configured")
            return None
        
        openai.api_key = openai_api_key
        
        # Database schema context
        schema_context = """
        Database schema for AVA OLO agricultural system:
        
        Tables:
        1. farmers (id, name, phone_number, city, country, primary_occupation, size_hectares, subscription_status, created_at, updated_at)
        2. fields (id, farmer_id, field_name, size_hectares, crop_type, planting_date, harvest_date, created_at)
        3. tasks (id, field_id, task_type, task_description, due_date, status, created_at)
        4. conversations (id, farmer_id, message, response, timestamp, approved, approval_timestamp, approved_by)
        5. weather_data (id, farmer_id, temperature, humidity, precipitation, wind_speed, timestamp)
        
        Guidelines:
        - Use proper JOIN syntax when querying related tables
        - Always filter farmers by subscription_status = 'active' unless specifically asked for all farmers
        - Return meaningful column names
        - Limit results to 100 rows unless specified otherwise
        """
        
        prompt = f"""
        {schema_context}
        
        Convert this natural language question to a SQL query:
        "{question}"
        
        Return ONLY the SQL query, no explanations.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate only SELECT queries that are safe to execute."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the query
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        return sql_query
        
    except Exception as e:
        logger.error(f"Error generating SQL from natural language: {str(e)}")
        return None

def is_safe_query(query: str) -> bool:
    """Check if a SQL query is safe to execute (SELECT only)"""
    # Remove comments and normalize whitespace
    import re
    cleaned_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
    cleaned_query = ' '.join(cleaned_query.split()).upper()
    
    # Check for unsafe operations
    unsafe_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]
    
    for keyword in unsafe_keywords:
        if keyword in cleaned_query:
            return False
    
    # Must start with SELECT
    if not cleaned_query.strip().startswith('SELECT'):
        return False
    
    return True

@router.get("/api/table-schema/{table_name}", response_class=JSONResponse)
async def get_table_schema(table_name: str):
    """Get schema information for a specific table"""
    db_manager = get_db_manager()
    
    # Validate table name to prevent SQL injection
    allowed_tables = ['farmers', 'fields', 'tasks', 'conversations', 'weather_data']
    if table_name not in allowed_tables:
        return {"success": False, "error": "Invalid table name"}
    
    try:
        # Get column information
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        
        result = await db_manager.execute_query(query, (table_name,))
        
        if result and result.get('success'):
            columns = []
            for row in result.get('data', []):
                columns.append({
                    'column_name': row[0],
                    'data_type': row[1],
                    'is_nullable': row[2] == 'YES',
                    'default_value': row[3]
                })
            
            # Get row count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = await db_manager.execute_query(count_query)
            row_count = count_result.get('data', [[0]])[0][0] if count_result and count_result.get('success') else 0
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to get table schema"
            }
            
    except Exception as e:
        logger.error(f"Error getting table schema for {table_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }