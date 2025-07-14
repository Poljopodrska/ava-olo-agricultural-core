# main.py - AVA OLO Monitoring Dashboards
import uvicorn
import os
import json
import psycopg2
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Construct DATABASE_URL from individual components if not set
if not os.getenv('DATABASE_URL'):
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME', 'farmer_crm')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_port = os.getenv('DB_PORT', '5432')
    
    if db_host and db_password:
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        os.environ['DATABASE_URL'] = DATABASE_URL
        logger.info(f"Constructed DATABASE_URL from components")

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Monitoring Dashboards",
    description="Agricultural monitoring and database exploration",
    version="2.0.0"
)

# Database connection
@contextmanager
def get_db_connection():
    """Get database connection with proper error handling"""
    connection = None
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        logger.info(f"Attempting connection to {host}:{port}/{database}")
        
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            connect_timeout=10,
            sslmode='require'
        )
        logger.info("Database connected successfully")
        yield connection
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        yield None
    finally:
        if connection:
            connection.close()

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Monitoring Dashboards</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f3f0;
                color: #3e2e1e;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            .header {
                background-color: #8b4513;
                color: white;
                padding: 40px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 40px;
            }
            .dashboard-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .dashboard-card {
                background: white;
                border: 1px solid #d4a574;
                border-radius: 8px;
                padding: 30px;
                text-align: center;
                transition: transform 0.2s;
                text-decoration: none;
                color: inherit;
                display: block;
            }
            .dashboard-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .card-icon {
                font-size: 48px;
                margin-bottom: 20px;
            }
            .card-title {
                font-size: 24px;
                margin-bottom: 10px;
                color: #8b4513;
            }
            .card-description {
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌾 AVA OLO Monitoring Dashboards</h1>
                <p>Agricultural Intelligence Platform</p>
            </div>
            
            <div class="dashboard-grid">
                <a href="/database-explorer" class="dashboard-card">
                    <div class="card-icon">🔍</div>
                    <h2 class="card-title">Database Explorer</h2>
                    <p class="card-description">Query agricultural data with natural language</p>
                </a>
                
                <a href="/business-dashboard" class="dashboard-card">
                    <div class="card-icon">📊</div>
                    <h2 class="card-title">Business Dashboard</h2>
                    <p class="card-description">Analytics and business metrics</p>
                </a>
                
                <a href="/admin-dashboard" class="dashboard-card">
                    <div class="card-icon">⚙️</div>
                    <h2 class="card-title">Admin Dashboard</h2>
                    <p class="card-description">System administration</p>
                </a>
                
                <a href="/health" class="dashboard-card">
                    <div class="card-icon">💚</div>
                    <h2 class="card-title">Health Check</h2>
                    <p class="card-description">System status and diagnostics</p>
                </a>
            </div>
        </div>
    </body>
    </html>
    """)

# Health check endpoint
@app.get("/health", response_class=JSONResponse)
async def health():
    """Health check endpoint"""
    db_status = "unknown"
    try:
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                db_status = "connected"
            else:
                db_status = "failed"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check OpenAI availability
    openai_available = False
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and len(openai_key) > 10:
        try:
            import openai
            openai_available = True
        except:
            pass
    
    return JSONResponse(content={
        "status": "healthy",
        "service": "monitoring-dashboards",
        "version": "2.0.0",
        "database": db_status,
        "openai": "available" if openai_available else "not available",
        "timestamp": datetime.now().isoformat()
    })

# Database Explorer
@app.get("/database-explorer", response_class=HTMLResponse)
async def database_explorer():
    """Database Explorer interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Explorer - AVA OLO</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f3f0;
                color: #3e2e1e;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background-color: #8b4513;
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
            }
            .back-link {
                color: #8b4513;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
            .query-section {
                background: white;
                border: 1px solid #d4a574;
                border-radius: 8px;
                padding: 30px;
                margin-bottom: 30px;
            }
            textarea {
                width: 100%;
                padding: 15px;
                border: 2px solid #d4a574;
                border-radius: 4px;
                font-size: 16px;
                resize: vertical;
                min-height: 120px;
                box-sizing: border-box;
            }
            button {
                background-color: #556b2f;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                margin-top: 15px;
            }
            button:hover {
                background-color: #3e4e1f;
            }
            .results-section {
                background: white;
                border: 1px solid #d4a574;
                border-radius: 8px;
                padding: 30px;
                min-height: 300px;
            }
            .loading {
                color: #666;
                font-style: italic;
            }
            .error {
                color: #d32f2f;
                padding: 15px;
                background: #ffebee;
                border-radius: 4px;
            }
            .success {
                color: #2e7d32;
                padding: 15px;
                background: #e8f5e9;
                border-radius: 4px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f5f5f5;
                font-weight: bold;
            }
            pre {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            
            <div class="header">
                <h1>🔍 Database Explorer</h1>
                <p>Query your agricultural database using natural language or SQL</p>
            </div>
            
            <div class="query-section">
                <h3>Enter your query:</h3>
                <textarea id="query" placeholder="Examples:
- Show me all farmers in Croatia
- How many fields are larger than 10 hectares?
- List the most recent messages from farmers
- SELECT * FROM farmers LIMIT 10"></textarea>
                <button onclick="executeQuery()">🔍 Execute Query</button>
            </div>
            
            <div class="results-section" id="results">
                <p style="color: #999;">Query results will appear here...</p>
            </div>
        </div>
        
        <script>
            async function executeQuery() {
                const query = document.getElementById('query').value;
                const resultsDiv = document.getElementById('results');
                
                if (!query.trim()) {
                    alert('Please enter a query');
                    return;
                }
                
                resultsDiv.innerHTML = '<p class="loading">Processing query...</p>';
                
                try {
                    const response = await fetch('/api/database/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: query })
                    });
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }
                
                if (data.sql_query) {
                    resultsDiv.innerHTML = `
                        <h3>Generated SQL:</h3>
                        <pre>${data.sql_query}</pre>
                    `;
                }
                
                if (data.results && data.results.rows && data.results.rows.length > 0) {
                    const columns = data.results.columns || Object.keys(data.results.rows[0]);
                    let tableHtml = '<h3>Results:</h3><table><thead><tr>';
                    
                    columns.forEach(col => {
                        tableHtml += `<th>${col}</th>`;
                    });
                    tableHtml += '</tr></thead><tbody>';
                    
                    data.results.rows.forEach(row => {
                        tableHtml += '<tr>';
                        columns.forEach(col => {
                            tableHtml += `<td>${row[col] !== null ? row[col] : 'NULL'}</td>`;
                        });
                        tableHtml += '</tr>';
                    });
                    
                    tableHtml += '</tbody></table>';
                    tableHtml += `<p>Total rows: ${data.results.rows.length}</p>`;
                    resultsDiv.innerHTML += tableHtml;
                } else if (data.message) {
                    resultsDiv.innerHTML += `<div class="success">${data.message}</div>`;
                } else {
                    resultsDiv.innerHTML += '<p>No results found</p>';
                }
            }
            
            // Allow Enter key to submit (Shift+Enter for new line)
            document.getElementById('query').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    executeQuery();
                }
            });
        </script>
    </body>
    </html>
    """)

# Database query API
@app.post("/api/database/query")
async def database_query(request: Request):
    """Execute database query"""
    try:
        body = await request.json()
        query = body.get('query', '')
        
        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "No query provided"}
            )
        
        # Check if it's SQL or natural language
        is_sql = query.strip().upper().startswith(('SELECT', 'WITH'))
        
        if is_sql:
            # Direct SQL execution
            return await execute_sql_query(query)
        else:
            # Natural language processing
            return await process_natural_language_query(query)
            
    except Exception as e:
        logger.error(f"Query error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

async def execute_sql_query(sql_query: str) -> JSONResponse:
    """Execute SQL query safely"""
    try:
        # Security check
        sql_upper = sql_query.upper()
        if any(keyword in sql_upper for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']):
            return JSONResponse(
                status_code=400,
                content={"error": "Only SELECT queries are allowed"}
            )
        
        with get_db_connection() as conn:
            if not conn:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Database connection failed"}
                )
            
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows[:100]:  # Limit to 100 rows
                results.append(dict(zip(columns, row)))
            
            return JSONResponse(content={
                "sql_query": sql_query,
                "results": {
                    "columns": columns,
                    "rows": results,
                    "total_rows": len(rows)
                }
            })
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Query execution error: {str(e)}"}
        )

async def process_natural_language_query(query: str) -> JSONResponse:
    """Convert natural language to SQL and execute"""
    try:
        # Simple pattern matching for common queries
        query_lower = query.lower()
        
        # Farmers queries
        if 'farmers' in query_lower or 'farmer' in query_lower:
            if 'count' in query_lower or 'how many' in query_lower:
                sql = "SELECT COUNT(*) as total_farmers FROM farmers"
            elif 'croatia' in query_lower:
                sql = "SELECT * FROM farmers WHERE country = 'Croatia' LIMIT 20"
            else:
                sql = "SELECT * FROM farmers LIMIT 20"
        
        # Fields queries
        elif 'fields' in query_lower or 'field' in query_lower:
            if 'large' in query_lower or 'big' in query_lower:
                sql = "SELECT * FROM fields WHERE area_ha > 10 LIMIT 20"
            else:
                sql = "SELECT * FROM fields LIMIT 20"
        
        # Messages queries
        elif 'messages' in query_lower or 'message' in query_lower:
            sql = "SELECT * FROM incoming_messages ORDER BY created_at DESC LIMIT 20"
        
        # Default
        else:
            return JSONResponse(content={
                "message": "Query not understood. Try asking about farmers, fields, or messages.",
                "query": query
            })
        
        # Execute the generated SQL
        result = await execute_sql_query(sql)
        content = json.loads(result.body)
        content['natural_query'] = query
        content['sql_query'] = sql
        
        return JSONResponse(content=content)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Natural language processing error: {str(e)}"}
        )

# Redirect routes
@app.get("/business")
async def redirect_business():
    return RedirectResponse(url="/business-dashboard", status_code=302)

@app.get("/admin")
async def redirect_admin():
    return RedirectResponse(url="/admin-dashboard", status_code=302)

@app.get("/agronomic")
async def redirect_agronomic():
    return RedirectResponse(url="/agronomic-dashboard", status_code=302)

# Placeholder pages
@app.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard():
    return HTMLResponse(content="""
    <html>
    <head><title>Business Dashboard</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>📊 Business Dashboard</h1>
        <p>Coming soon...</p>
        <a href="/">← Back to Dashboard</a>
    </body>
    </html>
    """)

@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    return HTMLResponse(content="""
    <html>
    <head><title>Admin Dashboard</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>⚙️ Admin Dashboard</h1>
        <p>Coming soon...</p>
        <a href="/">← Back to Dashboard</a>
    </body>
    </html>
    """)

if __name__ == "__main__":
    logger.info("Starting AVA OLO Monitoring Dashboards")
    uvicorn.run(app, host="0.0.0.0", port=8080)