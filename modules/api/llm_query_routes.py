#!/usr/bin/env python3
"""
LLM Query Routes
Provides AI-powered natural language to SQL query conversion using GPT-3.5
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..core.config import VERSION
from ..core.simple_db import execute_simple_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/database/llm", tags=["llm-query"])
templates = Jinja2Templates(directory="templates")

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = None

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set - LLM queries will use fallback mode")
else:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None

class LLMQueryRequest(BaseModel):
    query: str

@router.get("", response_class=HTMLResponse)
async def llm_query_page(request: Request):
    """Main LLM query page"""
    try:
        return templates.TemplateResponse("llm_query.html", {
            "request": request,
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Error rendering LLM query page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_database_schema() -> str:
    """Fetch the current database schema"""
    try:
        # Get all tables
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        tables_result = execute_simple_query(tables_query, ())
        
        if not tables_result.get('success'):
            return "Unable to fetch schema"
        
        schema_info = []
        
        for table_row in tables_result.get('rows', []):
            table_name = table_row[0]
            
            # Get columns for each table
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                    AND table_name = %s
                ORDER BY ordinal_position
            """
            columns_result = execute_simple_query(columns_query, (table_name,))
            
            if columns_result.get('success'):
                columns = []
                for col_row in columns_result.get('rows', []):
                    col_name = col_row[0]
                    col_type = col_row[1]
                    max_length = col_row[2]
                    nullable = col_row[3]
                    
                    if max_length:
                        col_type = f"{col_type}({max_length})"
                    
                    nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
                    columns.append(f"  - {col_name}: {col_type} {nullable_str}")
                
                schema_info.append(f"Table: {table_name}")
                schema_info.extend(columns[:10])  # Limit to first 10 columns per table
                if len(columns) > 10:
                    schema_info.append(f"  ... and {len(columns) - 10} more columns")
                schema_info.append("")  # Empty line between tables
        
        return "\n".join(schema_info)
        
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
        return f"Error fetching schema: {str(e)}"

def create_gpt_prompt(user_query: str, schema: str) -> str:
    """Create a detailed prompt for GPT-3.5"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""You are a PostgreSQL SQL query expert. Your task is to convert natural language questions into SQL queries.

CURRENT DATE: {current_date}

DATABASE SCHEMA:
{schema}

IMPORTANT RULES:
1. ONLY generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
2. Use proper PostgreSQL syntax
3. Include appropriate JOINs when data from multiple tables is needed
4. Use meaningful column aliases when needed
5. Apply appropriate WHERE clauses based on the question
6. Use ORDER BY and LIMIT when the question implies sorting or limiting results
7. For date/time queries, use PostgreSQL date functions (NOW(), INTERVAL, DATE_TRUNC, etc.)
8. Always use lowercase for table and column names
9. When counting or aggregating, use appropriate GROUP BY clauses
10. For text searches, use ILIKE for case-insensitive matching

USER QUESTION: {user_query}

Please respond with ONLY the SQL query, no explanations or markdown. The query should be ready to execute."""
    
    return prompt

def generate_sql_with_gpt(user_query: str, schema: str) -> tuple[str, str]:
    """Generate SQL using GPT-3.5"""
    try:
        if not openai_client:
            # Fallback to simple pattern matching if no API key or client
            return generate_fallback_sql(user_query), "Using fallback SQL generation (OpenAI not available)"
        
        prompt = create_gpt_prompt(user_query, schema)
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a PostgreSQL SQL expert. Generate only executable SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more deterministic output
            max_tokens=500,
            n=1
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Remove any markdown formatting if present
        if sql_query.startswith("```"):
            sql_query = sql_query.split("```")[1]
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
        sql_query = sql_query.strip()
        
        # Safety check - ensure it's a SELECT query
        if not sql_query.upper().startswith("SELECT"):
            return None, "Generated query is not a SELECT statement"
        
        # Additional safety checks
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
        query_upper = sql_query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return None, f"Query contains forbidden keyword: {keyword}"
        
        explanation = f"Generated SQL query for: {user_query}"
        return sql_query, explanation
        
    except Exception as e:
        logger.error(f"Error generating SQL with GPT: {e}")
        # Fallback to simple generation
        return generate_fallback_sql(user_query), f"Fallback SQL generation (GPT error: {str(e)})"

def generate_fallback_sql(user_query: str) -> str:
    """Simple fallback SQL generation when GPT is not available"""
    query_lower = user_query.lower()
    
    # Simple pattern matching for common queries
    if "farmers" in query_lower:
        if "count" in query_lower or "how many" in query_lower:
            if "country" in query_lower or "from" in query_lower:
                # Try to extract country name
                words = query_lower.split()
                if "from" in words:
                    idx = words.index("from")
                    if idx + 1 < len(words):
                        country = words[idx + 1].strip('?,.')
                        return f"SELECT COUNT(*) as count FROM farmers WHERE LOWER(country) = '{country}'"
            return "SELECT COUNT(*) as total_farmers FROM farmers"
        
        if "recent" in query_lower or "latest" in query_lower or "last" in query_lower:
            limit = 10
            if "5" in query_lower:
                limit = 5
            elif "20" in query_lower:
                limit = 20
            return f"SELECT * FROM farmers ORDER BY created_at DESC LIMIT {limit}"
        
        if any(country in query_lower for country in ["slovenia", "croatia", "bulgaria", "serbia"]):
            for country in ["slovenia", "croatia", "bulgaria", "serbia"]:
                if country in query_lower:
                    return f"SELECT * FROM farmers WHERE LOWER(country) = '{country}'"
        
        return "SELECT * FROM farmers LIMIT 20"
    
    elif "fields" in query_lower:
        if "large" in query_lower or "hectare" in query_lower or "area" in query_lower:
            # Look for number
            import re
            numbers = re.findall(r'\d+', user_query)
            if numbers:
                area = numbers[0]
                return f"SELECT * FROM fields WHERE area_ha > {area} ORDER BY area_ha DESC"
        
        if "total" in query_lower and "area" in query_lower:
            return """
                SELECT f.manager_name, f.manager_last_name, 
                       COUNT(fi.id) as field_count,
                       SUM(fi.area_ha) as total_area
                FROM farmers f
                LEFT JOIN fields fi ON f.id = fi.farmer_id
                GROUP BY f.id, f.manager_name, f.manager_last_name
                ORDER BY total_area DESC
            """
        
        return "SELECT * FROM fields ORDER BY area_ha DESC LIMIT 20"
    
    elif "messages" in query_lower or "chat" in query_lower:
        if "recent" in query_lower or "last" in query_lower:
            if "week" in query_lower:
                return "SELECT * FROM chat_messages WHERE created_at > NOW() - INTERVAL '7 days' ORDER BY created_at DESC"
            elif "day" in query_lower:
                return "SELECT * FROM chat_messages WHERE created_at > NOW() - INTERVAL '1 day' ORDER BY created_at DESC"
            elif "month" in query_lower:
                return "SELECT * FROM chat_messages WHERE created_at > NOW() - INTERVAL '1 month' ORDER BY created_at DESC"
        return "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 20"
    
    elif "crops" in query_lower or "crop" in query_lower:
        if "count" in query_lower or "how many" in query_lower:
            return """
                SELECT crop_name, COUNT(DISTINCT field_id) as field_count
                FROM field_crops
                GROUP BY crop_name
                ORDER BY field_count DESC
            """
        return "SELECT * FROM field_crops LIMIT 20"
    
    # Default query
    return "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"

@router.post("/query", response_class=JSONResponse)
async def process_llm_query(request: LLMQueryRequest):
    """Process a natural language query using LLM"""
    try:
        user_query = request.query.strip()
        
        if not user_query:
            return JSONResponse(content={
                "success": False,
                "error": "Query cannot be empty"
            })
        
        # Get current database schema
        schema = get_database_schema()
        
        # Generate SQL using GPT-3.5 or fallback
        sql_query, explanation = generate_sql_with_gpt(user_query, schema)
        
        if not sql_query:
            return JSONResponse(content={
                "success": False,
                "error": explanation or "Failed to generate SQL query"
            })
        
        # Execute the generated SQL
        result = execute_simple_query(sql_query, ())
        
        if result.get('success'):
            rows = result.get('rows', [])
            columns = result.get('columns', [])
            
            # Convert rows to dict format
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
                "sql_query": sql_query,
                "explanation": explanation,
                "results": data,
                "columns": columns,
                "row_count": len(data)
            })
        else:
            # Try to provide helpful error message
            error_msg = result.get('error', 'Query execution failed')
            
            # If it's a SQL error, try to generate a corrected query
            if "column" in error_msg.lower() or "table" in error_msg.lower():
                # Could retry with GPT here with the error message
                return JSONResponse(content={
                    "success": False,
                    "error": f"SQL execution error: {error_msg}",
                    "sql_query": sql_query,
                    "suggestion": "The generated query had an error. Please try rephrasing your question."
                })
            
            return JSONResponse(content={
                "success": False,
                "error": error_msg,
                "sql_query": sql_query
            })
            
    except Exception as e:
        logger.error(f"Error in LLM query processing: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })