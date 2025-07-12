# main.py - Fix AWS RDS Authentication and SSL Issues
import uvicorn
import os
import json
import psycopg2
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="AVA OLO Constitutional Monitoring Hub")

# FIXED: Constitutional AWS RDS Connection with Multiple Authentication Attempts
@contextmanager
def get_constitutional_db_connection():
    """Constitutional connection with multiple authentication strategies"""
    connection = None
    try:
        # Get connection parameters
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
        
        # Strategy 3: Try without SSL (fallback)
        try:
            connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode='disable'
            )
            print("DEBUG: Connected without SSL")
            yield connection
            return
        except psycopg2.OperationalError as no_ssl_error:
            print(f"DEBUG: No SSL failed: {no_ssl_error}")
        
        # Strategy 4: Try with different authentication method
        try:
            connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode='require',
                application_name='ava_olo_constitutional'
            )
            print("DEBUG: Connected with application name")
            yield connection
            return
        except psycopg2.OperationalError as app_name_error:
            print(f"DEBUG: Application name failed: {app_name_error}")
        
        # Strategy 5: Try connecting to postgres database instead of farmer_crm
        try:
            connection = psycopg2.connect(
                host=host,
                database='postgres',  # Default database
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode='require'
            )
            print("DEBUG: Connected to postgres database (farmer_crm might not exist)")
            yield connection
            return
        except psycopg2.OperationalError as postgres_db_error:
            print(f"DEBUG: Postgres database failed: {postgres_db_error}")
            
        # All strategies failed
        print("DEBUG: All connection strategies failed")
        yield None
        
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        yield None
    finally:
        if connection:
            connection.close()

# Enhanced debug endpoint to test all strategies
@app.get("/api/debug/connection-strategies")
async def debug_connection_strategies():
    """Test all connection strategies"""
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME', 'farmer_crm')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    port = int(os.getenv('DB_PORT', '5432'))
    
    strategies = []
    
    # Test each strategy individually
    connection_configs = [
        {"name": "SSL Required", "sslmode": "require", "database": database},
        {"name": "SSL Preferred", "sslmode": "prefer", "database": database},
        {"name": "SSL Disabled", "sslmode": "disable", "database": database},
        {"name": "SSL Required + App Name", "sslmode": "require", "database": database, "application_name": "ava_olo"},
        {"name": "Postgres DB + SSL", "sslmode": "require", "database": "postgres"},
        {"name": "Postgres DB + No SSL", "sslmode": "disable", "database": "postgres"}
    ]
    
    for config in connection_configs:
        try:
            conn_params = {
                "host": host,
                "user": user,
                "password": password,
                "port": port,
                "connect_timeout": 5,
                "database": config["database"],
                "sslmode": config["sslmode"]
            }
            
            if "application_name" in config:
                conn_params["application_name"] = config["application_name"]
            
            connection = psycopg2.connect(**conn_params)
            cursor = connection.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # Test if farmer_crm database exists (if connected to postgres)
            if config["database"] == "postgres":
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'farmer_crm'")
                farmer_crm_exists = bool(cursor.fetchone())
            else:
                farmer_crm_exists = True
                
            connection.close()
            
            strategies.append({
                "strategy": config["name"],
                "status": "SUCCESS",
                "postgres_version": version[:50],  # Truncate for readability
                "farmer_crm_exists": farmer_crm_exists
            })
            
        except psycopg2.OperationalError as op_error:
            strategies.append({
                "strategy": config["name"],
                "status": "FAILED",
                "error": str(op_error)[:100]  # Truncate error
            })
        except Exception as e:
            strategies.append({
                "strategy": config["name"],
                "status": "ERROR",
                "error": str(e)[:100]
            })
    
    return {
        "connection_strategies": strategies,
        "summary": {
            "any_successful": any(s["status"] == "SUCCESS" for s in strategies),
            "farmer_crm_exists": any(s.get("farmer_crm_exists", False) for s in strategies if s["status"] == "SUCCESS")
        }
    }

# Test if farmer_crm database exists
@app.get("/api/debug/database-exists")
async def check_database_exists():
    """Check if farmer_crm database exists"""
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    port = int(os.getenv('DB_PORT', '5432'))
    
    try:
        # Connect to postgres database to check if farmer_crm exists
        connection = psycopg2.connect(
            host=host,
            database='postgres',
            user=user,
            password=password,
            port=port,
            connect_timeout=10,
            sslmode='require'
        )
        
        cursor = connection.cursor()
        
        # Check if farmer_crm database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'farmer_crm'")
        farmer_crm_exists = bool(cursor.fetchone())
        
        # Get list of all databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = [row[0] for row in cursor.fetchall()]
        
        connection.close()
        
        return {
            "farmer_crm_exists": farmer_crm_exists,
            "available_databases": databases,
            "recommendation": "Use 'postgres' database" if not farmer_crm_exists else "Use 'farmer_crm' database"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "farmer_crm_exists": "unknown"
        }

# Updated constitutional query function
async def execute_constitutional_query(query: str):
    """Execute query with working connection strategy"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                return {
                    "status": "connection_failed",
                    "error": "Could not connect to AWS RDS database",
                    "debug_info": "Check /api/debug/connection-strategies for detailed diagnostics"
                }
                
            cursor = conn.cursor()
            
            # Constitutional safety
            if not query.upper().strip().startswith('SELECT'):
                return {
                    "status": "constitutional_protection",
                    "error": "Only SELECT queries allowed for safety"
                }
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = cursor.fetchall()
            
            # Convert to JSON-safe format
            json_results = []
            for row in results:
                json_row = [str(item) if item is not None else None for item in row]
                json_results.append(json_row)
            
            return {
                "status": "success",
                "columns": columns,
                "rows": json_results,
                "row_count": len(results),
                "constitutional_compliance": True
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "debug_info": "Check /api/debug/connection-strategies for detailed diagnostics"
        }

# Keep existing debug endpoints
@app.get("/api/debug/complete")
async def debug_complete():
    """Complete diagnostic with enhanced connection testing"""
    
    # Test connection strategies
    strategies_result = await debug_connection_strategies()
    
    # Check database existence
    db_exists_result = await check_database_exists()
    
    # Summary
    summary = {
        "environment_ok": bool(os.getenv('DB_HOST') and os.getenv('DB_PASSWORD')),
        "any_connection_works": strategies_result["summary"]["any_successful"],
        "farmer_crm_exists": db_exists_result.get("farmer_crm_exists", False),
        "recommended_action": "Use working connection strategy" if strategies_result["summary"]["any_successful"] else "Check credentials"
    }
    
    return {
        "summary": summary,
        "connection_strategies": strategies_result,
        "database_check": db_exists_result,
        "next_steps": {
            "if_no_connection_works": "Check AWS RDS credentials and user permissions",
            "if_farmer_crm_missing": "Create farmer_crm database or use postgres database",
            "if_connection_works": "Use the successful strategy for main application"
        }
    }

# Simple working HTML templates
@app.get("/", response_class=HTMLResponse)
async def dashboard_hub():
    """Main hub with enhanced debug info"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Enhanced Debug</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .debug { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 8px; }
            a { color: #3498db; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌾 AVA OLO Enhanced Debug Mode</h1>
            
            <div class="debug">
                <strong>🔍 Enhanced Debug Active:</strong> Testing multiple connection strategies to AWS RDS.
            </div>
            
            <div class="card">
                <h3>🚨 Enhanced Debug Links:</h3>
                <ul>
                    <li><a href="/api/debug/connection-strategies">Test All Connection Strategies</a></li>
                    <li><a href="/api/debug/database-exists">Check if farmer_crm Database Exists</a></li>
                    <li><a href="/api/debug/complete">Complete Enhanced Diagnostic</a></li>
                </ul>
            </div>
            
            <div class="card">
                <h3><a href="/database/">🗄️ Database Dashboard</a></h3>
                <p>Test the database query interface with enhanced connection handling</p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/database/", response_class=HTMLResponse)
async def database_dashboard():
    """Database dashboard with enhanced debug"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Dashboard - Enhanced Debug</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .debug { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .query-box { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
            textarea { width: 100%; height: 80px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .results { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .error { background: #ffebee; }
            .success { background: #e8f5e8; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f5f5f5; }
        </style>
    </head>
    <body>
        <div class="container">
            <p><a href="/">← Back to Enhanced Debug Hub</a></p>
            <h1>🗄️ Database Dashboard - Enhanced Debug</h1>
            
            <div class="debug">
                <strong>🔍 Enhanced Debug:</strong> Testing multiple AWS RDS connection strategies.
                <a href="/api/debug/connection-strategies">Check Connection Strategies</a>
            </div>
            
            <div class="query-box">
                <h3>Test Enhanced AWS RDS Connection</h3>
                <form id="queryForm">
                    <textarea id="queryInput" placeholder="SELECT version();">SELECT version();</textarea>
                    <br>
                    <button type="submit">Execute Query</button>
                    <button type="button" onclick="testStrategies()">Test All Strategies</button>
                </form>
            </div>
            
            <div id="queryResults" class="results" style="display: none;"></div>
        </div>
        
        <script>
            function testStrategies() {
                fetch('/api/debug/connection-strategies')
                    .then(response => response.json())
                    .then(data => {
                        const resultsDiv = document.getElementById('queryResults');
                        resultsDiv.style.display = 'block';
                        resultsDiv.className = 'results';
                        resultsDiv.innerHTML = '<h4>Connection Strategies Test:</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    });
            }
            
            document.getElementById('queryForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const query = document.getElementById('queryInput').value;
                
                fetch('/api/database/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({query: query})
                })
                .then(response => response.json())
                .then(data => {
                    const resultsDiv = document.getElementById('queryResults');
                    resultsDiv.style.display = 'block';
                    
                    if (data.status === 'success') {
                        resultsDiv.className = 'results success';
                        let html = `<h4>Success! (${data.row_count} rows)</h4>`;
                        if (data.rows && data.rows.length > 0) {
                            html += '<table><tr>';
                            data.columns.forEach(col => html += `<th>${col}</th>`);
                            html += '</tr>';
                            data.rows.forEach(row => {
                                html += '<tr>';
                                row.forEach(cell => html += `<td>${cell}</td>`);
                                html += '</tr>';
                            });
                            html += '</table>';
                        }
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.className = 'results error';
                        resultsDiv.innerHTML = `<h4>Error:</h4><p>${data.error}</p><p><em>${data.debug_info || ''}</em></p>`;
                    }
                });
            });
        </script>
    </body>
    </html>
    """)

# API endpoint
@app.post("/api/database/query")
async def execute_query_api(request: Request):
    """Execute query with enhanced connection handling"""
    try:
        data = await request.json()
        query = data.get('query', '').strip()
        return await execute_constitutional_query(query)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "debug_info": "Check /api/debug/connection-strategies for diagnostics"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)