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
        """Convert natural language query to SQL"""
        description_lower = description.lower()
        
        # Pattern matching for common queries
        sql_query = ""
        query_type = "custom"
        
        # Farmer queries
        if "farmer" in description_lower:
            if "all" in description_lower and ("show" in description_lower or "list" in description_lower or "get" in description_lower):
                sql_query = "SELECT * FROM farmers ORDER BY id DESC"
                query_type = "all_farmers"
            elif "new" in description_lower or "recent" in description_lower:
                # Since farmers table doesn't have created_at, we can't filter by date
                sql_query = "SELECT * FROM farmers ORDER BY id DESC LIMIT 10"
                query_type = "recent_farmers"
            elif "count" in description_lower or "how many" in description_lower:
                sql_query = "SELECT COUNT(*) as total_farmers FROM farmers"
                query_type = "count"
            elif "by city" in description_lower or "cities" in description_lower:
                sql_query = "SELECT city, COUNT(*) as farmer_count FROM farmers GROUP BY city ORDER BY farmer_count DESC"
                query_type = "farmers_by_city"
            elif "by country" in description_lower:
                sql_query = "SELECT country, COUNT(*) as farmer_count FROM farmers GROUP BY country ORDER BY farmer_count DESC"
                query_type = "farmers_by_country"
        
        # Field queries
        elif "field" in description_lower:
            if "all" in description_lower and ("show" in description_lower or "list" in description_lower or "get" in description_lower):
                sql_query = "SELECT * FROM fields ORDER BY created_at DESC"
                query_type = "all_fields"
            elif "large" in description_lower or "big" in description_lower:
                sql_query = "SELECT * FROM fields WHERE area_hectares > 50 ORDER BY area_hectares DESC"
                query_type = "large_fields"
            elif "crop" in description_lower:
                sql_query = "SELECT f.*, c.name as crop_name FROM fields f LEFT JOIN crops c ON f.crop_id = c.id ORDER BY f.created_at DESC"
                query_type = "fields_with_crops"
        
        # Message queries
        elif "message" in description_lower or "question" in description_lower:
            if "today" in description_lower:
                sql_query = "SELECT * FROM incoming_messages WHERE DATE(created_at) = CURRENT_DATE ORDER BY created_at DESC"
                query_type = "today_messages"
            elif "unanswered" in description_lower:
                sql_query = "SELECT * FROM incoming_messages WHERE response_sent = FALSE ORDER BY created_at DESC"
                query_type = "unanswered"
        
        # Task queries
        elif "task" in description_lower or "operation" in description_lower:
            if "pending" in description_lower or "incomplete" in description_lower:
                sql_query = "SELECT * FROM tasks WHERE status != 'completed' ORDER BY priority DESC, created_at DESC"
                query_type = "pending_tasks"
            elif "today" in description_lower:
                sql_query = "SELECT * FROM tasks WHERE DATE(created_at) = CURRENT_DATE ORDER BY created_at DESC"
                query_type = "today_tasks"
        
        # Analytics queries
        elif "statistic" in description_lower or "summary" in description_lower:
            sql_query = """
                SELECT 
                    (SELECT COUNT(*) FROM farmers) as total_farmers,
                    (SELECT COUNT(*) FROM fields) as total_fields,
                    (SELECT COUNT(*) FROM incoming_messages) as total_messages,
                    (SELECT COUNT(*) FROM tasks) as total_tasks
            """
            query_type = "statistics"
        
        # Default fallback
        if not sql_query:
            sql_query = f"-- Unable to generate SQL from: {description}\n-- Try being more specific about what data you want to see"
            query_type = "failed"
        
        return {
            "sql_query": sql_query,
            "query_type": query_type,
            "original_description": description
        }
    
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

# Initialize explorer
explorer = DatabaseExplorer()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Enhanced Database Explorer Dashboard"""
    table_groups = explorer.get_table_groups()
    
    return templates.TemplateResponse("database_explorer.html", {
        "request": request,
        "table_groups": table_groups,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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