# main.py - Safe Agricultural Dashboard with Optional LLM
import uvicorn
import os
import json
import psycopg2
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

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
        print(f"DEBUG: Constructed DATABASE_URL from components")

# Constitutional Error Isolation - Import OpenAI safely
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_AVAILABLE = False

# Check if API key exists
if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
    try:
        # For OpenAI 1.x, we just need to check if import works
        # The actual client is created in llm_integration.py
        from openai import OpenAI
        OPENAI_AVAILABLE = True
        print(f"DEBUG: OpenAI available with key: {OPENAI_API_KEY[:10]}...")
    except ImportError as e:
        print(f"DEBUG: OpenAI import failed: {e}")
    except Exception as e:
        print(f"DEBUG: OpenAI setup error: {e}")
else:
    print(f"DEBUG: OpenAI key issue - Present: {bool(OPENAI_API_KEY)}, Length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")

app = FastAPI(title="AVA OLO Agricultural Database Dashboard")

# Constitutional AWS RDS Connection (RESTORED WORKING VERSION)
@contextmanager
def get_constitutional_db_connection():
    """Constitutional connection with multiple strategies (from working debug version)"""
    connection = None
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        print(f"DEBUG: Attempting connection to {host}:{port}/{database} as {user}")
        
        # Strategy 1: Try with SSL required (AWS RDS default)
        try:
            connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode='require'
            )
            print("DEBUG: Connected with SSL required")
            yield connection
            return
        except psycopg2.OperationalError as ssl_error:
            print(f"DEBUG: SSL required failed: {ssl_error}")
        
        # Strategy 2: Try with SSL preferred
        try:
            connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode='prefer'
            )
            print("DEBUG: Connected with SSL preferred")
            yield connection
            return
        except psycopg2.OperationalError as ssl_pref_error:
            print(f"DEBUG: SSL preferred failed: {ssl_pref_error}")
        
        # Strategy 3: Try connecting to postgres database instead
        try:
            connection = psycopg2.connect(
                host=host,
                database='postgres',  # Fallback database
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode='require'
            )
            print("DEBUG: Connected to postgres database")
            yield connection
            return
        except psycopg2.OperationalError as postgres_error:
            print(f"DEBUG: Postgres database failed: {postgres_error}")
            
        # All strategies failed
        print("DEBUG: All connection strategies failed")
        yield None
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        yield None
    finally:
        if connection:
            connection.close()

# Add a simple root route first
@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple root endpoint to verify deployment"""
    return HTMLResponse(content="""
    <html>
    <head>
        <title>AVA OLO Monitoring Dashboards</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .status { color: green; font-weight: bold; }
            .links { margin-top: 20px; }
            a { display: block; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>AVA OLO Monitoring Dashboards</h1>
        <p class="status">✅ Service is running!</p>
        <div class="links">
            <h3>Available Dashboards:</h3>
            <a href="./database-explorer">Database Explorer</a>
            <a href="./business-dashboard">Business Dashboard</a>
            <a href="./health">Health Check</a>
        </div>
    </body>
    </html>
    """)

@app.get("/health", response_class=JSONResponse)
@app.get("/health/", response_class=JSONResponse)
async def health():
    """Health check endpoint"""
    db_status = "unknown"
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                db_status = "connected"
            else:
                db_status = "failed"
    except:
        db_status = "error"
    
    return JSONResponse(content={
        "status": "healthy",
        "service": "monitoring-dashboards",
        "database": db_status,
        "openai": "available" if OPENAI_AVAILABLE else "not available"
    })

# Database Explorer functionality
@app.get("/database-explorer", response_class=HTMLResponse)
@app.get("/database-explorer/", response_class=HTMLResponse)
async def database_explorer():
    """Database Explorer - Natural Language Query Interface"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Database Explorer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f3f0;
                color: #3e2e1e;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                background-color: #8b4513;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .query-box {
                background: white;
                border: 1px solid #d4a574;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #d4a574;
                border-radius: 4px;
                font-size: 16px;
                resize: vertical;
                min-height: 100px;
            }
            button {
                background-color: #556b2f;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                margin-top: 10px;
            }
            button:hover {
                background-color: #3e4e1f;
            }
            .results {
                background: white;
                border: 1px solid #d4a574;
                border-radius: 8px;
                padding: 20px;
                min-height: 200px;
            }
            .back-link {
                color: #8b4513;
                text-decoration: none;
                margin-bottom: 20px;
                display: inline-block;
            }
            .loading {
                color: #666;
                font-style: italic;
            }
            pre {
                background: #f5f5f5;
                padding: 10px;
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
                <p>Ask questions about your agricultural data in natural language</p>
            </div>
            
            <div class="query-box">
                <h3>Enter your question:</h3>
                <textarea id="query" placeholder="Examples:
- Show me all farmers in Croatia
- How many hectares of tomatoes do we have?
- List farmers who joined this month
- What crops are grown in Serbia?"></textarea>
                <button onclick="executeQuery()">🔍 Search Database</button>
            </div>
            
            <div class="results" id="results">
                <p style="color: #999;">Results will appear here...</p>
            </div>
        </div>
        
        <script>
            async function executeQuery() {
                const query = document.getElementById('query').value;
                const resultsDiv = document.getElementById('results');
                
                if (!query.trim()) {
                    alert('Please enter a question');
                    return;
                }
                
                resultsDiv.innerHTML = '<p class="loading">Processing your query...</p>';
                
                try {
                    const response = await fetch('/api/database/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: query })
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        resultsDiv.innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                    } else {
                        resultsDiv.innerHTML = `
                            <h3>Results:</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        `;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
                }
            }
            
            // Allow Enter key to submit
            document.getElementById('query').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    executeQuery();
                }
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

# API endpoint for database queries
@app.post("/api/database/query")
async def api_database_query(request: Request):
    """Process natural language database queries"""
    try:
        body = await request.json()
        query = body.get('query', '')
        
        # For now, return a simple response
        # We'll add the LLM integration later
        return JSONResponse(content={
            "query": query,
            "message": "Database query functionality will be added soon",
            "status": "pending"
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)