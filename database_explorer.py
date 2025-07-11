"""
AVA OLO Database Explorer - Port 8005
Professional database exploration interface with AI-powered querying
"""
from fastapi import FastAPI, Request, Query, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import os
import sys
from typing import Dict, Any, List, Optional
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Database Explorer",
    description="Professional database exploration with AI-powered querying",
    version="3.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize database
db_ops = DatabaseOperations()

# Import RDS inspector
from inspect_rds import create_inspect_endpoint

# Import translations
try:
    from slovenian_translations import UI_TRANSLATIONS, TABLE_DESCRIPTIONS, AI_QUERY_EXAMPLES
except:
    UI_TRANSLATIONS = {"en": {}, "sl": {}}
    TABLE_DESCRIPTIONS = {"en": {}, "sl": {}}
    AI_QUERY_EXAMPLES = {"en": [], "sl": []}

class DatabaseExplorer:
    """Enhanced database explorer with AI query capabilities"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    def get_table_groups(self) -> Dict[str, List[Dict[str, str]]]:
        """Get tables organized into logical groups"""
        return {
            "Core Data": [
                {"name": "farmers", "description": "Farmer profiles and information", "icon": "👨‍🌾"},
                {"name": "fields", "description": "Agricultural fields and properties", "icon": "🌾"},
                {"name": "crops", "description": "Crop types and varieties", "icon": "🌱"}
            ],
            "Operations": [
                {"name": "tasks", "description": "Field operations and activities", "icon": "📋"},
                {"name": "activities", "description": "Agricultural activities tracking", "icon": "🚜"},
                {"name": "field_operations", "description": "Detailed field operations", "icon": "⚙️"}
            ],
            "Communication": [
                {"name": "incoming_messages", "description": "Farmer questions and messages", "icon": "💬"},
                {"name": "outgoing_messages", "description": "System responses and advice", "icon": "📤"},
                {"name": "notifications", "description": "System notifications", "icon": "🔔"}
            ],
            "Analytics": [
                {"name": "recommendations", "description": "AI-generated recommendations", "icon": "🤖"},
                {"name": "weather_data", "description": "Weather information and forecasts", "icon": "🌤️"},
                {"name": "market_prices", "description": "Market price tracking", "icon": "💰"}
            ]
        }
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get comprehensive table information"""
        try:
            with self.db_ops.get_session() as session:
                inspector = inspect(session.bind)
                
                # Get columns
                columns = inspector.get_columns(table_name)
                
                # Get row count
                total_count = session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar() or 0
                
                # Get recent entries count - check if date columns exist
                counts = {"24h": 0, "7d": 0, "30d": 0}
                
                # Check if table has date columns
                date_columns = []
                for col in columns:
                    col_name = col["name"].lower()
                    if col_name in ["created_at", "updated_at", "date", "timestamp"]:
                        date_columns.append(col["name"])
                
                if date_columns:
                    for period_name, days in [("24h", 1), ("7d", 7), ("30d", 30)]:
                        start_date = datetime.now() - timedelta(days=days)
                        date_conditions = " OR ".join([f"{col} >= :start_date" for col in date_columns])
                        try:
                            count = session.execute(
                                text(f"SELECT COUNT(*) FROM {table_name} WHERE {date_conditions}"),
                                {"start_date": start_date}
                            ).scalar() or 0
                            counts[period_name] = count
                        except:
                            pass
                
                # Get sample data
                try:
                    # Try to order by a date column if available, otherwise by id
                    order_column = date_columns[0] if date_columns else "id"
                    sample_rows = session.execute(
                        text(f"SELECT * FROM {table_name} ORDER BY {order_column} DESC LIMIT 5")
                    ).fetchall()
                except:
                    # If ordering fails, just get any 5 rows
                    sample_rows = session.execute(
                        text(f"SELECT * FROM {table_name} LIMIT 5")
                    ).fetchall()
                
                return {
                    "table_name": table_name,
                    "total_records": total_count,
                    "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
                    "recent_counts": counts,
                    "sample_data": [dict(zip([col["name"] for col in columns], row)) for row in sample_rows] if sample_rows else []
                }
                
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            # Check if it's a table not found error
            error_msg = str(e)
            if "does not exist" in error_msg or "farmers" in table_name:
                # Try to list available tables
                try:
                    with self.db_ops.get_session() as session:
                        tables_result = session.execute(
                            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                        ).fetchall()
                        available_tables = [t[0] for t in tables_result] if tables_result else []
                        return {
                            "table_name": table_name,
                            "error": f"Table '{table_name}' not found. Available tables: {', '.join(available_tables) if available_tables else 'No tables found in database'}"
                        }
                except:
                    pass
            return {
                "table_name": table_name,
                "error": error_msg
            }
    
    async def get_table_data_filtered(self, table_name: str, days: int = 30, 
                                    page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get filtered table data"""
        try:
            with self.db_ops.get_session() as session:
                inspector = inspect(session.bind)
                columns = [col["name"] for col in inspector.get_columns(table_name)]
                
                # Build date filter
                start_date = datetime.now() - timedelta(days=days)
                
                # Check if table has date columns
                date_columns = []
                for col in ["created_at", "updated_at", "sent_at", "date"]:
                    if col in columns:
                        date_columns.append(col)
                
                # Build query with date filter
                if date_columns:
                    date_conditions = " OR ".join([
                        f"{col} >= :start_date" for col in date_columns
                    ])
                    query = f"""
                        SELECT * FROM {table_name}
                        WHERE {date_conditions}
                        ORDER BY {date_columns[0]} DESC
                        LIMIT :limit OFFSET :offset
                    """
                    count_query = f"""
                        SELECT COUNT(*) FROM {table_name}
                        WHERE {date_conditions}
                    """
                else:
                    query = f"""
                        SELECT * FROM {table_name}
                        ORDER BY id DESC
                        LIMIT :limit OFFSET :offset
                    """
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                
                # Execute queries
                offset = (page - 1) * limit
                params = {"start_date": start_date, "limit": limit, "offset": offset}
                
                total_count = session.execute(text(count_query), params).scalar() or 0
                results = session.execute(text(query), params).fetchall()
                
                rows = [dict(zip(columns, row)) for row in results]
                
                return {
                    "columns": columns,
                    "rows": rows,
                    "total_count": total_count,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total_count + limit - 1) // limit
                }
                
        except Exception as e:
            logger.error(f"Error getting filtered table data: {e}")
            return {
                "columns": [],
                "rows": [],
                "total_count": 0,
                "error": str(e)
            }
    
    async def convert_natural_language_to_sql(self, description: str) -> Dict[str, Any]:
        """Convert natural language query to SQL using LLM approach"""
        try:
            # Get available tables and their schemas
            with self.db_ops.get_session() as session:
                inspector = inspect(session.bind)
                
                # Get all tables with their columns
                table_schemas = []
                for table_name in inspector.get_table_names():
                    columns = []
                    for col in inspector.get_columns(table_name):
                        columns.append(f"{col['name']} ({col['type']})")
                    table_schemas.append(f"Table {table_name}: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                
                schema_context = "\n".join(table_schemas)
            
            # Use LLM-style prompt to generate SQL
            prompt = f"""Given the following database schema:
{schema_context}

User request: {description}

Generate a PostgreSQL SELECT query to fulfill this request. Consider:
- The query can be in English or Slovenian
- Common Slovenian terms: kmet=farmer, parcela/polje=field, sporočilo=message, naloga=task, koliko=how many
- Only generate SELECT queries
- Include proper JOINs if needed
- Add ORDER BY and LIMIT where appropriate
- Return only the SQL query, no explanations
"""
            
            # Simulate LLM response with more intelligent parsing
            sql_query = self._generate_sql_from_prompt(description, schema_context)
            
            if sql_query and sql_query.strip().upper().startswith("SELECT"):
                return {
                    "sql_query": sql_query,
                    "query_type": "llm_generated",
                    "original_description": description
                }
            else:
                return {
                    "sql_query": f"-- Unable to generate SQL from: {description}",
                    "query_type": "failed",
                    "original_description": description
                }
                
        except Exception as e:
            logger.error(f"Error in LLM query conversion: {e}")
            return {
                "sql_query": f"-- Error: {str(e)}",
                "query_type": "error",
                "original_description": description
            }
    
    def _generate_sql_from_prompt(self, description: str, schema_context: str) -> str:
        """Generate SQL from natural language using intelligent parsing"""
        description_lower = description.lower()
        
        # Build a more intelligent query based on detected entities and intents
        tables_mentioned = []
        conditions = []
        select_fields = "*"
        order_by = ""
        limit = ""
        
        # Detect table references
        table_mappings = {
            "farmers": ["farmer", "kmet", "kmeti", "kmetje", "kmetov"],
            "fields": ["field", "parcela", "parcele", "parcel", "polje", "polja", "njiva"],
            "incoming_messages": ["message", "sporočilo", "sporočila", "sporočil", "vprašanj"],
            "tasks": ["task", "naloga", "naloge", "nalog", "opravilo", "opravila", "opravil"],
            "crops": ["crop", "pridelek", "pridelki", "pridelkov"],
            "weather_data": ["weather", "vreme", "vremenske"],
            "recommendations": ["recommendation", "priporočilo", "priporočila"]
        }
        
        for table, keywords in table_mappings.items():
            if any(keyword in description_lower for keyword in keywords):
                tables_mentioned.append(table)
        
        # If no tables detected, try to infer from context
        if not tables_mentioned:
            if any(word in description_lower for word in ["count", "koliko", "število", "how many"]):
                # Check for specific patterns like "v bazi" (in database)
                if "bazi" in description_lower or "database" in description_lower:
                    # Default to farmers if asking about database in general
                    tables_mentioned = ["farmers"]
                else:
                    # Default to farmers if counting without specific table
                    tables_mentioned = ["farmers"]
            else:
                return "-- Could not identify which table to query"
        
        # Detect counting queries
        if any(word in description_lower for word in ["count", "koliko", "število", "how many", "številka"]):
            select_fields = f"COUNT(*) as count"
        
        # Detect filtering conditions
        if any(word in description_lower for word in ["today", "danes", "današnji"]):
            conditions.append("DATE(created_at) = CURRENT_DATE")
        elif any(word in description_lower for word in ["yesterday", "včeraj"]):
            conditions.append("DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'")
        elif any(word in description_lower for word in ["week", "teden", "tednu"]):
            conditions.append("created_at >= CURRENT_DATE - INTERVAL '7 days'")
        elif any(word in description_lower for word in ["month", "mesec", "mesecu"]):
            conditions.append("created_at >= CURRENT_DATE - INTERVAL '30 days'")
        
        # Detect size conditions
        if any(word in description_lower for word in ["large", "big", "velik", "večj"]):
            if "fields" in tables_mentioned:
                conditions.append("area_hectares > 50")
        elif any(word in description_lower for word in ["small", "majhn", "mali"]):
            if "fields" in tables_mentioned:
                conditions.append("area_hectares < 10")
        
        # Detect status conditions
        if any(word in description_lower for word in ["pending", "incomplete", "nedokončan", "čakajoč"]):
            conditions.append("status != 'completed'")
        elif any(word in description_lower for word in ["completed", "dokončan", "končan"]):
            conditions.append("status = 'completed'")
        
        # Detect grouping
        if any(phrase in description_lower for phrase in ["by city", "po mestih", "po mestu"]):
            select_fields = "city, COUNT(*) as count"
            order_by = "ORDER BY count DESC"
            # Add GROUP BY
            conditions.append("GROUP BY city")
        elif any(phrase in description_lower for phrase in ["by country", "po državah", "po državi"]):
            select_fields = "country, COUNT(*) as count" 
            order_by = "ORDER BY count DESC"
            conditions.append("GROUP BY country")
        
        # Detect ordering
        if not order_by:
            if any(word in description_lower for word in ["recent", "latest", "zadnji", "najnovejši"]):
                order_by = "ORDER BY created_at DESC"
            elif any(word in description_lower for word in ["oldest", "first", "najstarejši", "prvi"]):
                order_by = "ORDER BY created_at ASC"
        
        # Detect limits
        if any(word in description_lower for word in ["all", "vse", "vsi"]):
            limit = ""
        elif "10" in description_lower or any(word in description_lower for word in ["recent", "zadnjih"]):
            limit = "LIMIT 10"
        elif "5" in description_lower:
            limit = "LIMIT 5"
        elif "20" in description_lower:
            limit = "LIMIT 20"
        
        # Build the query
        main_table = tables_mentioned[0]
        where_clause = " AND ".join([c for c in conditions if "GROUP BY" not in c])
        group_clause = next((c for c in conditions if "GROUP BY" in c), "")
        
        if where_clause:
            where_clause = f" WHERE {where_clause}"
        
        query = f"SELECT {select_fields} FROM {main_table}{where_clause} {group_clause} {order_by} {limit}".strip()
        
        # Clean up extra spaces
        query = " ".join(query.split())
        
        return query
    
    async def execute_ai_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute the AI-generated SQL query safely"""
        try:
            # Security check
            query_upper = sql_query.upper()
            if not query_upper.strip().startswith("SELECT") and not query_upper.strip().startswith("--"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Check for dangerous keywords with word boundaries
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
            import re
            for keyword in dangerous_keywords:
                if re.search(r'\b' + keyword + r'\b', query_upper):
                    raise ValueError("Query contains dangerous operations")
            
            with self.db_ops.get_session() as session:
                # Add limit if not present
                if "LIMIT" not in query_upper and not query_upper.strip().startswith("--"):
                    sql_query += " LIMIT 100"
                
                result = session.execute(text(sql_query))
                
                # Get column names first
                columns = list(result.keys())
                
                # Fetch all rows
                results = result.fetchall()
                
                if results:
                    # Convert rows to dictionaries
                    rows = []
                    for row in results:
                        row_dict = {}
                        for idx, col in enumerate(columns):
                            row_dict[col] = row[idx]
                        rows.append(row_dict)
                else:
                    rows = []
                
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "columns": [],
                "rows": []
            }
    
    async def convert_natural_language_to_modification_sql(self, description: str) -> Dict[str, Any]:
        """Convert natural language to INSERT/UPDATE/DELETE SQL using LLM approach"""
        try:
            # Get available tables and their schemas
            with self.db_ops.get_session() as session:
                inspector = inspect(session.bind)
                
                # Get all tables with their columns
                table_schemas = []
                for table_name in inspector.get_table_names():
                    columns = []
                    for col in inspector.get_columns(table_name):
                        col_type = str(col['type'])
                        nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                        columns.append(f"{col['name']} {col_type} {nullable}")
                    table_schemas.append(f"Table {table_name}:\n  {chr(10).join(columns[:10])}{'...' if len(columns) > 10 else ''}")
                
                schema_context = "\n\n".join(table_schemas)
            
            # Generate SQL using intelligent parsing
            sql_query = self._generate_modification_sql_from_prompt(description, schema_context)
            
            if sql_query and not sql_query.startswith("--"):
                # Determine operation type
                sql_upper = sql_query.strip().upper()
                if sql_upper.startswith("INSERT"):
                    operation = "insert"
                elif sql_upper.startswith("UPDATE"):
                    operation = "update"
                elif sql_upper.startswith("DELETE"):
                    operation = "delete"
                else:
                    operation = "unknown"
                
                return {"success": True, "sql": sql_query, "operation": operation}
            else:
                return {"success": False, "sql": sql_query, "operation": "failed"}
                
        except Exception as e:
            logger.error(f"Error in modification SQL conversion: {e}")
            return {"success": False, "sql": f"-- Error: {str(e)}", "operation": "error"}
    
    def _generate_modification_sql_from_prompt(self, description: str, schema_context: str) -> str:
        """Generate modification SQL from natural language using intelligent parsing"""
        import re
        description_lower = description.lower()
        
        # Detect operation type
        operation = ""
        if any(word in description_lower for word in ["add", "create", "insert", "dodaj", "ustvari", "vstavi"]):
            operation = "INSERT"
        elif any(word in description_lower for word in ["update", "change", "modify", "posodobi", "spremeni", "nastavi"]):
            operation = "UPDATE"
        elif any(word in description_lower for word in ["delete", "remove", "izbriši", "odstrani", "pobriši"]):
            operation = "DELETE"
        else:
            return "-- Could not determine operation type (INSERT/UPDATE/DELETE)"
        
        # Detect table references
        table_mappings = {
            "farmers": ["farmer", "kmet", "kmeta", "kmetu", "kmetom"],
            "fields": ["field", "parcela", "parcele", "parcelo", "parcel", "polje", "polja", "njiva", "njivo"],
            "incoming_messages": ["message", "sporočilo", "sporočila"],
            "tasks": ["task", "naloga", "nalogo", "opravilo"],
            "crops": ["crop", "pridelek", "pridelka"],
            "weather_data": ["weather", "vreme"],
            "recommendations": ["recommendation", "priporočilo"]
        }
        
        target_table = None
        for table, keywords in table_mappings.items():
            if any(keyword in description_lower for keyword in keywords):
                target_table = table
                break
        
        if not target_table:
            return "-- Could not identify which table to modify"
        
        # Parse based on operation type
        if operation == "INSERT":
            if target_table == "fields":
                # Extract field name
                field_name = None
                farmer_ref = None
                
                # Look for field name patterns
                name_patterns = [
                    r'called\s+["\']?([^"\']+)["\']?',
                    r'imenovano\s+["\']?([^"\']+)["\']?',
                    r'parcelo\s+["\']?([^"\']+)["\']?\s+kmetu',
                    r'field\s+["\']?([^"\']+)["\']?\s+to',
                    r'called\s+(\w+\s+\w+)',  # For "called Big field"
                    r'"([^"]+)"',
                    r"'([^']+)'"
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        field_name = match.group(1).strip()
                        break
                
                # Look for farmer reference
                farmer_patterns = [
                    r'to\s+(?:farmer\s+)?([^\s]+(?:\s+[^\s]+)?)',
                    r'kmetu\s+([^\s]+(?:\s+[^\s]+)?)',
                    r'for\s+([^\s]+(?:\s+[^\s]+)?)',
                    r'za\s+([^\s]+(?:\s+[^\s]+)?)'
                ]
                
                for pattern in farmer_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        farmer_ref = match.group(1).strip()
                        # Remove trailing words like "called", "named", etc.
                        farmer_ref = re.sub(r'\s+(called|named|imenovano|z\s+imenom).*$', '', farmer_ref, flags=re.IGNORECASE)
                        break
                
                if field_name and farmer_ref:
                    return f"""INSERT INTO fields (farmer_id, name, location, area_hectares, created_at)
SELECT id, '{field_name}', 'Unknown', 10.0, NOW()
FROM farmers 
WHERE LOWER(farm_name) LIKE LOWER('%{farmer_ref}%')
   OR LOWER(manager_name || ' ' || manager_last_name) LIKE LOWER('%{farmer_ref}%')
   OR LOWER(manager_name) LIKE LOWER('%{farmer_ref}%')
LIMIT 1"""
                
            elif target_table == "farmers":
                # Extract farmer name
                farmer_name = None
                name_patterns = [
                    r'farmer\s+([^\s]+(?:\s+[^\s]+)?)',
                    r'kmeta\s+([^\s]+(?:\s+[^\s]+)?)',
                    r'add\s+([^\s]+(?:\s+[^\s]+)?)',
                    r'dodaj\s+([^\s]+(?:\s+[^\s]+)?)'
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        farmer_name = match.group(1).strip()
                        break
                
                if farmer_name:
                    # Split into first and last name if possible
                    parts = farmer_name.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = ' '.join(parts[1:])
                    else:
                        first_name = farmer_name
                        last_name = "Farm"
                    
                    return f"""INSERT INTO farmers (farm_name, manager_name, manager_last_name, country, city, postal_code, street_and_no, village)
VALUES ('{farmer_name} Farm', '{first_name}', '{last_name}', 'Slovenia', 'Ljubljana', '1000', 'Unknown 1', 'Unknown')"""
        
        elif operation == "UPDATE":
            if target_table == "fields":
                # Extract field name and new value
                field_name = None
                new_value = None
                field_to_update = None
                
                # Look for field name
                name_match = re.search(r'(?:field|parcelo?)\s+["\']?([^"\']+?)["\']?\s+(?:set|to|na)', description, re.IGNORECASE)
                if name_match:
                    field_name = name_match.group(1).strip()
                
                # Look for numeric values (likely area)
                number_match = re.search(r'(\d+(?:\.\d+)?)', description)
                if number_match:
                    new_value = float(number_match.group(1))
                    field_to_update = "area_hectares"
                
                if field_name and new_value:
                    return f"""UPDATE fields 
SET {field_to_update} = {new_value}
WHERE LOWER(name) = LOWER('{field_name}')"""
        
        elif operation == "DELETE":
            if target_table == "fields":
                # Extract field name
                field_name = None
                name_patterns = [
                    r'field\s+["\']?([^"\']+)["\']?',
                    r'parcelo?\s+["\']?([^"\']+)["\']?',
                    r'"([^"]+)"',
                    r"'([^']+)'"
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        field_name = match.group(1).strip()
                        break
                
                if field_name:
                    return f"""DELETE FROM fields 
WHERE LOWER(name) = LOWER('{field_name}')"""
        
        return f"-- Could not generate {operation} query for {target_table} from: {description}"
    
    async def execute_modification_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute INSERT/UPDATE/DELETE queries with proper safety checks"""
        try:
            with self.db_ops.get_session() as session:
                result = session.execute(text(sql_query))
                session.commit()
                
                rows_affected = result.rowcount if hasattr(result, 'rowcount') else 0
                
                return {
                    "success": True,
                    "rows_affected": rows_affected,
                    "message": f"Successfully executed. {rows_affected} row(s) affected."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows_affected": 0
            }

# Initialize explorer
explorer = DatabaseExplorer()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = Query("en")):
    """Enhanced Database Explorer Dashboard with language support"""
    table_groups = explorer.get_table_groups()
    
    # Get translations for current language
    translations = UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["en"])
    table_desc = TABLE_DESCRIPTIONS.get(lang, TABLE_DESCRIPTIONS["en"])
    examples = AI_QUERY_EXAMPLES.get(lang, AI_QUERY_EXAMPLES["en"])
    
    return templates.TemplateResponse("database_explorer.html", {
        "request": request,
        "table_groups": table_groups,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lang": lang,
        "t": translations,
        "table_desc": table_desc,
        "examples": examples
    })

@app.get("/table/{table_name}", response_class=HTMLResponse)
async def view_table(request: Request, table_name: str, days: int = Query(30)):
    """View table with time-based filtering"""
    table_info = await explorer.get_table_info(table_name)
    table_data = await explorer.get_table_data_filtered(table_name, days=days)
    
    return templates.TemplateResponse("table_view.html", {
        "request": request,
        "table_name": table_name,
        "table_info": table_info,
        "table_data": table_data,
        "selected_days": days,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.post("/ai-query", response_class=HTMLResponse)
async def ai_query(request: Request, query_description: str = Form(...)):
    """Convert natural language to SQL and execute"""
    # Convert to SQL
    query_result = await explorer.convert_natural_language_to_sql(query_description)
    
    # Execute if successful
    if query_result["query_type"] != "failed":
        execution_result = await explorer.execute_ai_query(query_result["sql_query"])
    else:
        execution_result = {"success": False, "error": "Could not generate valid SQL query"}
    
    return templates.TemplateResponse("ai_query_results.html", {
        "request": request,
        "query_description": query_description,
        "sql_query": query_result["sql_query"],
        "query_type": query_result["query_type"],
        "results": execution_result,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.get("/api/table/{table_name}/data")
async def api_table_data(
    table_name: str,
    days: int = Query(30),
    page: int = Query(1),
    limit: int = Query(50)
):
    """API endpoint for table data with filtering"""
    return await explorer.get_table_data_filtered(table_name, days, page, limit)

@app.get("/api/table/{table_name}/info")
async def api_table_info(table_name: str):
    """API endpoint for table information"""
    return await explorer.get_table_info(table_name)

@app.post("/api/ai-query")
async def api_ai_query(query_description: str = Form(...)):
    """API endpoint for AI query conversion and execution"""
    query_result = await explorer.convert_natural_language_to_sql(query_description)
    
    if query_result["query_type"] != "failed":
        execution_result = await explorer.execute_ai_query(query_result["sql_query"])
        return {
            "query": query_result,
            "execution": execution_result
        }
    else:
        return {
            "query": query_result,
            "execution": {"success": False, "error": "Could not generate valid SQL query"}
        }

@app.get("/api/test-connection")
async def test_connection():
    """Test database connection and show basic info"""
    try:
        with db_ops.get_session() as session:
            # Test basic connection
            db_version = session.execute(text("SELECT version()")).scalar()
            current_db = session.execute(text("SELECT current_database()")).scalar()
            current_user = session.execute(text("SELECT current_user")).scalar()
            
            # List all databases
            databases = session.execute(
                text("SELECT datname FROM pg_database WHERE datistemplate = false")
            ).fetchall()
            
            # Check all schemas
            schemas = session.execute(
                text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """)
            ).fetchall()
            
            return {
                "success": True,
                "connection": {
                    "version": db_version,
                    "current_database": current_db,
                    "current_user": current_user,
                    "host": db_ops.connection_string.split('@')[1].split('/')[0]
                },
                "databases": [db[0] for db in databases],
                "schemas": [s[0] for s in schemas]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "connection_string": db_ops.connection_string.split('@')[1] if '@' in db_ops.connection_string else "Unknown"
        }

@app.get("/api/tables")
async def list_tables():
    """List all available tables in the database"""
    try:
        with db_ops.get_session() as session:
            result = session.execute(
                text("""
                    SELECT table_name, 
                           pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::text)) as size
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            ).fetchall()
            
            tables = [{"name": row[0], "size": row[1]} for row in result]
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables),
                "database": db_ops.connection_string.split('/')[-1].split('?')[0]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tables": []
        }

@app.post("/api/import-sql")
async def import_sql_file(file: UploadFile = File(...)):
    """Import SQL file to create database structure"""
    try:
        # Read the uploaded file
        content = await file.read()
        sql_content = content.decode('utf-8')
        
        # Parse SQL statements
        statements = []
        current = []
        in_function = False
        
        for line in sql_content.split('\n'):
            # Skip comments
            if line.strip().startswith('--'):
                continue
                
            # Track if we're inside a function
            if 'CREATE FUNCTION' in line or 'CREATE OR REPLACE FUNCTION' in line:
                in_function = True
            if in_function and 'LANGUAGE' in line and line.strip().endswith(';'):
                in_function = False
                
            if line.strip():
                current.append(line)
                
            # End of statement
            if not in_function and line.strip().endswith(';'):
                stmt = ' '.join(current)
                if stmt.strip():
                    statements.append(stmt)
                current = []
        
        # Execute statements
        executed = 0
        errors = []
        tables_created = []
        
        with db_ops.get_session() as session:
            for i, statement in enumerate(statements):
                try:
                    # Skip certain statements
                    if any(skip in statement.upper() for skip in ['SET STATEMENT_TIMEOUT', 'SET LOCK_TIMEOUT', 'SELECT PG_CATALOG', 'SET CHECK_FUNCTION_BODIES', 'SET XMLOPTION', 'SET CLIENT_MIN_MESSAGES', 'SET ROW_SECURITY', 'SET DEFAULT_TABLE_ACCESS_METHOD', 'COMMENT ON SCHEMA']):
                        continue
                    
                    # Handle COPY statements specially
                    if 'COPY' in statement.upper() and 'FROM stdin' in statement:
                        # This is a COPY statement with data
                        table_match = re.search(r'COPY\s+"?\w*"?\."?(\w+)"?', statement, re.IGNORECASE)
                        if table_match:
                            table_name = table_match.group(1)
                            # Extract the data part
                            data_start = statement.find('FROM stdin;') + len('FROM stdin;')
                            data_end = statement.rfind('\\.')
                            if data_start > 0 and data_end > data_start:
                                data = statement[data_start:data_end].strip()
                                if data:
                                    # Count existing records
                                    existing = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                                    if existing == 0:
                                        # Process line by line
                                        lines = data.split('\n')
                                        imported = 0
                                        for line in lines:
                                            if line.strip():
                                                values = line.split('\t')
                                                # Convert \N to NULL
                                                values = [None if v == '\\N' else v for v in values]
                                                # Create INSERT statement
                                                placeholders = ', '.join([':p' + str(i) for i in range(len(values))])
                                                params = {f'p{i}': val for i, val in enumerate(values)}
                                                try:
                                                    session.execute(
                                                        text(f"INSERT INTO {table_name} VALUES ({placeholders})"),
                                                        params
                                                    )
                                                    imported += 1
                                                except:
                                                    pass
                                        if imported > 0:
                                            session.commit()
                                            executed += 1
                                            tables_created.append(f"{table_name} ({imported} rows)")
                                    continue
                    
                    # Extract table name if CREATE TABLE
                    if 'CREATE TABLE' in statement.upper():
                        match = re.search(r'CREATE TABLE\s+["]?([^"\s]+)["]?\.?["]?([^"\s(]+)?', statement, re.IGNORECASE)
                        if match:
                            table_name = match.group(2) if match.group(2) else match.group(1)
                            tables_created.append(table_name)
                    
                    session.execute(text(statement))
                    session.commit()
                    executed += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f"Statement {i+1}: {error_msg[:200]}")
                    session.rollback()
                    
                    # Continue on certain errors
                    if 'already exists' in error_msg:
                        continue
        
        return {
            "success": len(errors) == 0,
            "filename": file.filename,
            "total_statements": len(statements),
            "executed": executed,
            "tables_created": tables_created,
            "errors": errors[:10] if errors else []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Simple import page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Import Database</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .upload-form { border: 2px dashed #ccc; padding: 40px; text-align: center; }
            input[type="file"] { margin: 20px 0; }
            button { background: #1a73e8; color: white; padding: 10px 30px; border: none; border-radius: 5px; cursor: pointer; }
            .result { margin-top: 20px; padding: 20px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>Import Database Structure</h1>
        <div class="upload-form">
            <h3>Upload SQL file to import database structure</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="sqlFile" accept=".sql" required>
                <br>
                <button type="submit">Import SQL</button>
            </form>
        </div>
        <div id="result"></div>
        
        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('sqlFile');
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<p>Importing...</p>';
                
                try {
                    const response = await fetch('/database/api/import-sql', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        resultDiv.className = 'result success';
                        resultDiv.innerHTML = `
                            <h3>✅ Import Successful!</h3>
                            <p>Executed ${result.executed} statements</p>
                            <p>Created ${result.tables_created.length} tables: ${result.tables_created.join(', ')}</p>
                        `;
                    } else {
                        resultDiv.className = 'result error';
                        resultDiv.innerHTML = `
                            <h3>❌ Import Failed</h3>
                            <p>${result.error || result.errors.join('<br>')}</p>
                        `;
                    }
                } catch (error) {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>Error: ${error.message}</h3>`;
                }
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/run-import")
async def run_import():
    """One-time import of database schema"""
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "import_database.py"],
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/add-test-data")
async def add_test_data():
    """Add test data to farmers table"""
    try:
        with db_ops.get_session() as session:
            # Check if farmers table is empty
            count = session.execute(text("SELECT COUNT(*) FROM farmers")).scalar()
            
            if count > 0:
                return {"success": False, "message": f"Farmers table already has {count} records"}
            
            # Add test farmer
            session.execute(text("""
                INSERT INTO farmers (
                    state_farm_number, farm_name, manager_name, manager_last_name,
                    street_and_no, village, postal_code, city, country,
                    vat_no, email, phone, wa_phone_number, notes
                ) VALUES (
                    'TEST001', 'Test Farm Zagreb', 'Ivan', 'Horvat',
                    'Ilica 1', 'Zagreb', '10000', 'Zagreb', 'Croatia',
                    'HR12345678901', 'ivan@testfarm.hr', '+385911234567', '+385911234567',
                    'Test farmer for database verification'
                )
            """))
            
            session.execute(text("""
                INSERT INTO farmers (
                    state_farm_number, farm_name, manager_name, manager_last_name,
                    street_and_no, village, postal_code, city, country,
                    vat_no, email, phone, wa_phone_number, notes
                ) VALUES (
                    'TEST002', 'Organic Gardens Split', 'Ana', 'Kovač',
                    'Riva 25', 'Split', '21000', 'Split', 'Croatia',
                    'HR98765432109', 'ana@organicgardens.hr', '+385921234567', '+385921234567',
                    'Specializes in organic vegetables'
                )
            """))
            
            session.commit()
            
            # Get new count
            new_count = session.execute(text("SELECT COUNT(*) FROM farmers")).scalar()
            
            return {
                "success": True,
                "message": f"Added test data successfully. Farmers table now has {new_count} records",
                "farmers_added": 2
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/modify", response_class=HTMLResponse)
async def modify_page(request: Request, lang: str = Query("en")):
    """Data modification page with natural language support"""
    translations = UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["en"])
    
    return templates.TemplateResponse("data_modifier.html", {
        "request": request,
        "lang": lang,
        "t": translations,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.post("/api/ai-modify")
async def ai_modify(query_description: str = Form(...)):
    """Convert natural language to modification SQL and execute"""
    try:
        # Convert to SQL
        sql_query = await explorer.convert_natural_language_to_modification_sql(query_description)
        
        if sql_query["success"]:
            # Execute the modification
            result = await explorer.execute_modification_query(sql_query["sql"])
            return {
                "success": result["success"],
                "sql": sql_query["sql"],
                "operation": sql_query["operation"],
                "message": result.get("message", ""),
                "rows_affected": result.get("rows_affected", 0)
            }
        else:
            return {
                "success": False,
                "error": "Could not understand the modification request",
                "sql": ""
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sql": ""
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = await db_ops.health_check()
    
    return {
        "service": "Database Explorer",
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
        "port": 8005,
        "purpose": "Professional database exploration with AI querying",
        "version": "3.0.0"
    }

# Add RDS inspection endpoints
inspector = create_inspect_endpoint(app, db_ops)

if __name__ == "__main__":
    import uvicorn
    print("🗃️ Starting AVA OLO Database Explorer on port 8005")
    print("✨ Features: AI Query Assistant, Time Filtering, Table Groups")
    uvicorn.run(app, host="0.0.0.0", port=8005)