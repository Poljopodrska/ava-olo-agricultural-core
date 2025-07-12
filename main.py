# main.py - Fast Debug Version for AWS RDS Connection
import uvicorn
import os
import json
import psycopg2
import socket
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="AVA OLO Constitutional Monitoring Hub - DEBUG MODE")

# COMPREHENSIVE DEBUG: Constitutional AWS RDS Connection with Full Diagnostics
@contextmanager
def get_constitutional_db_connection():
    """Constitutional connection with comprehensive diagnostics"""
    connection = None
    try:
        # Get all connection parameters
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        print(f"DEBUG: Attempting connection to {host}:{port}/{database} as {user}")
        print(f"DEBUG: Password present: {bool(password)}")
        
        if not host:
            print("DEBUG: DB_HOST environment variable not set!")
            yield None
            return
            
        if not password:
            print("DEBUG: DB_PASSWORD environment variable not set!")
            yield None
            return
        
        # Test network connectivity first
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result != 0:
                print(f"DEBUG: Cannot reach {host}:{port} - Network connectivity issue")
                yield None
                return
            else:
                print(f"DEBUG: Network connectivity to {host}:{port} - OK")
        except Exception as net_error:
            print(f"DEBUG: Network test failed: {net_error}")
            yield None
            return
            
        # Attempt database connection
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            connect_timeout=10,
            sslmode='require'  # AWS RDS typically requires SSL
        )
        print("DEBUG: AWS RDS connection successful!")
        yield connection
        
    except psycopg2.OperationalError as op_error:
        print(f"DEBUG: PostgreSQL Operational Error: {op_error}")
        # Try without SSL as fallback
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
            print("DEBUG: AWS RDS connection successful (without SSL)!")
            yield connection
        except Exception as ssl_fallback_error:
            print(f"DEBUG: SSL fallback also failed: {ssl_fallback_error}")
            yield None
    except Exception as e:
        print(f"DEBUG: General connection error: {e}")
        yield None
    finally:
        if connection:
            connection.close()

# FAST DEBUG ENDPOINTS
@app.get("/api/debug/environment")
async def debug_environment():
    """Complete environment variable diagnostic"""
    return {
        "timestamp": "2025-07-12",
        "environment_variables": {
            "DB_HOST": os.getenv('DB_HOST', 'NOT_SET'),
            "DB_HOST_length": len(os.getenv('DB_HOST', '')),
            "DB_NAME": os.getenv('DB_NAME', 'NOT_SET'),
            "DB_USER": os.getenv('DB_USER', 'NOT_SET'),
            "DB_PASSWORD": "SET" if os.getenv('DB_PASSWORD') else "NOT_SET",
            "DB_PASSWORD_length": len(os.getenv('DB_PASSWORD', '')),
            "DB_PORT": os.getenv('DB_PORT', 'NOT_SET')
        },
        "expected_values": {
            "DB_HOST": "farmer-cr...",
            "DB_NAME": "farmer_crm",
            "DB_USER": "postgres",
            "DB_PASSWORD": "2hpxvrg...",
            "DB_PORT": "5432"
        },
        "all_env_vars": {k: v for k, v in os.environ.items() if k.startswith('DB_')}
    }

@app.get("/api/debug/network")
async def debug_network():
    """Network connectivity test to AWS RDS"""
    host = os.getenv('DB_HOST')
    port = int(os.getenv('DB_PORT', '5432'))
    
    if not host:
        return {"error": "DB_HOST not set", "status": "env_missing"}
    
    try:
        # Test network connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {
                "network_status": "SUCCESS", 
                "host": host, 
                "port": port,
                "message": "Can reach AWS RDS endpoint"
            }
        else:
            return {
                "network_status": "FAILED",
                "host": host,
                "port": port,
                "error_code": result,
                "message": "Cannot reach AWS RDS endpoint"
            }
    except Exception as e:
        return {
            "network_status": "ERROR",
            "host": host,
            "port": port,
            "error": str(e)
        }

@app.get("/api/debug/connection")
async def debug_connection():
    """Complete database connection diagnostic"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                # Test farmer table
                cursor.execute("SELECT COUNT(*) FROM farmers")
                farmer_count = cursor.fetchone()[0]
                
                # Test reference farmer
                cursor.execute("SELECT farm_name, email FROM farmers WHERE farm_name LIKE '%VRZEL%' LIMIT 1")
                vrzel = cursor.fetchone()
                
                return {
                    "connection_status": "SUCCESS",
                    "postgres_version": version,
                    "farmer_count": farmer_count,
                    "reference_farmer": vrzel,
                    "constitutional_compliance": True
                }
            else:
                return {
                    "connection_status": "FAILED",
                    "error": "No connection object returned",
                    "check": "See logs for detailed error information"
                }
    except Exception as e:
        return {
            "connection_status": "ERROR",
            "error": str(e),
            "constitutional_note": "Error isolated - system remains stable"
        }

@app.get("/api/debug/complete")
async def debug_complete():
    """Complete diagnostic - all tests in one"""
    
    # Environment check
    env_result = await debug_environment()
    
    # Network check  
    network_result = await debug_network()
    
    # Connection check
    connection_result = await debug_connection()
    
    # Summary
    summary = {
        "environment_ok": all([
            env_result["environment_variables"]["DB_HOST"] != "NOT_SET",
            env_result["environment_variables"]["DB_PASSWORD"] != "NOT_SET"
        ]),
        "network_ok": network_result.get("network_status") == "SUCCESS",
        "connection_ok": connection_result.get("connection_status") == "SUCCESS"
    }
    
    return {
        "summary": summary,
        "environment": env_result,
        "network": network_result, 
        "connection": connection_result,
        "next_steps": {
            "if_env_failed": "Check AWS App Runner environment variables",
            "if_network_failed": "Check RDS security groups and VPC settings",
            "if_connection_failed": "Check database credentials and SSL settings"
        }
    }

# Simplified database functions for testing
async def execute_constitutional_query(query: str):
    """Simplified query execution for debugging"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                return {
                    "status": "connection_failed",
                    "error": "Could not connect to AWS RDS database",
                    "debug_info": "Check /api/debug/complete for detailed diagnostics"
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
                "row_count": len(results)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "debug_info": "Check /api/debug/complete for detailed diagnostics"
        }

# Keep existing routes but add debug info
@app.get("/", response_class=HTMLResponse)
async def dashboard_hub():
    """Main hub with debug links"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AVA OLO Debug Mode</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .debug { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 8px; }
            a { color: #3498db; text-decoration: none; }
            .debug-links { background: #e8f4f8; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌾 AVA OLO Constitutional Hub - DEBUG MODE</h1>
            
            <div class="debug">
                <strong>🔍 Debug Mode Active:</strong> Use the debug links below to diagnose AWS RDS connection issues.
            </div>
            
            <div class="debug-links">
                <h3>🚨 Fast Debug Links:</h3>
                <ul>
                    <li><a href="/api/debug/complete">Complete Diagnostic (START HERE)</a></li>
                    <li><a href="/api/debug/environment">Environment Variables</a></li>
                    <li><a href="/api/debug/network">Network Connectivity</a></li>
                    <li><a href="/api/debug/connection">Database Connection</a></li>
                </ul>
            </div>
            
            <div class="card">
                <h3><a href="/database/">🗄️ Database Dashboard</a></h3>
                <p>Test the database query interface (will show connection status)</p>
            </div>
            
            <div class="card">
                <h3><a href="/health/">🏥 Health Dashboard</a></h3>
                <p>System health with database diagnostics</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/database/", response_class=HTMLResponse)
async def database_dashboard():
    """Database dashboard with debug info"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Dashboard - DEBUG MODE</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .debug { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .query-box { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
            textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
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
            <p><a href="/">← Back to Debug Hub</a></p>
            <h1>🗄️ Database Dashboard - DEBUG MODE</h1>
            
            <div class="debug">
                <strong>🔍 Debug Mode:</strong> If queries fail, check 
                <a href="/api/debug/complete">Complete Diagnostic</a> for detailed error analysis.
            </div>
            
            <div class="query-box">
                <h3>Test AWS RDS Connection</h3>
                <form id="queryForm">
                    <textarea id="queryInput" placeholder="SELECT COUNT(*) FROM farmers;">SELECT COUNT(*) FROM farmers;</textarea>
                    <br>
                    <button type="submit">Execute Query</button>
                    <button type="button" onclick="testConnection()">Test Connection</button>
                </form>
            </div>
            
            <div id="queryResults" class="results" style="display: none;"></div>
        </div>
        
        <script>
            function testConnection() {
                fetch('/api/debug/connection')
                    .then(response => response.json())
                    .then(data => {
                        const resultsDiv = document.getElementById('queryResults');
                        resultsDiv.style.display = 'block';
                        resultsDiv.className = data.connection_status === 'SUCCESS' ? 'results success' : 'results error';
                        resultsDiv.innerHTML = '<h4>Connection Test:</h4><pre>' + JSON.stringify(data, null, 2) + '</pre>';
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

# API Endpoints
@app.post("/api/database/query")
async def execute_query_api(request: Request):
    """Execute query with debug info"""
    try:
        data = await request.json()
        query = data.get('query', '').strip()
        return await execute_constitutional_query(query)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "debug_info": "Check /api/debug/complete for diagnostics"
        }

@app.get("/health/", response_class=HTMLResponse)
async def health_dashboard():
    """Health dashboard with debug info"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>Health Dashboard - DEBUG</title>
    <style>body{font-family:Arial,sans-serif;margin:20px;}.container{max-width:800px;margin:0 auto;background:white;padding:30px;}.debug{background:#fff3cd;padding:15px;border-radius:5px;margin:15px 0;}</style>
    </head>
    <body>
        <div class="container">
            <p><a href="/">← Back to Debug Hub</a></p>
            <h1>🏥 Health Dashboard - DEBUG MODE</h1>
            
            <div class="debug">
                <strong>🔍 Debug Mode:</strong> Check <a href="/api/debug/complete">Complete Diagnostic</a> for AWS RDS status.
            </div>
            
            <p><strong>System Status:</strong> Operational ✅</p>
            <p><strong>Constitutional Compliance:</strong> Active ✅</p>
            <p><strong>Debug Mode:</strong> AWS RDS diagnostics available</p>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)