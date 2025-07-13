# main.py - Safe Agricultural Dashboard with Optional LLM
import uvicorn
import os
import json
import psycopg2
from contextlib import contextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

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

# PART 1: Standard Agricultural Queries (ALWAYS WORKS)
async def get_farmer_count():
    """Standard Query: Number of farmers"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as farmer_count FROM farmers")
                result = cursor.fetchone()
                return {"status": "success", "farmer_count": result[0]}
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_all_farmers():
    """Standard Query: List all farmers - DISCOVER ACTUAL SCHEMA"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # First get the count (we know this works)
                cursor.execute("SELECT COUNT(*) FROM farmers")
                total_count = cursor.fetchone()[0]
                
                # Discover the actual column structure
                try:
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'farmers' 
                        ORDER BY ordinal_position
                    """)
                    columns_info = cursor.fetchall()
                    
                    # Get the actual column names
                    column_names = [col[0] for col in columns_info]
                    
                    # Try to get actual data using discovered columns
                    if column_names:
                        # Use actual column names discovered from schema
                        # Fixed: Use correct column names from schema
                        preferred_columns = ['id', 'farm_name', 'manager_name', 'email', 'city', 'country']
                        select_columns = [col for col in preferred_columns if col in column_names]
                        if not select_columns:
                            select_columns = column_names[:5]  # Fallback to first 5 columns
                        select_query = f"SELECT {', '.join(select_columns)} FROM farmers LIMIT 10"
                        
                        cursor.execute(select_query)
                        results = cursor.fetchall()
                        
                        farmers = []
                        for i, row in enumerate(results):
                            farmer_data = {"row_number": i + 1}
                            for j, col_name in enumerate(select_columns):
                                farmer_data[col_name] = row[j] if j < len(row) else "N/A"
                            farmers.append(farmer_data)
                        
                        return {
                            "status": "success", 
                            "farmers": farmers, 
                            "total": len(farmers),
                            "total_in_db": total_count,
                            "discovered_columns": column_names,
                            "note": "Using actual database schema"
                        }
                    else:
                        return {
                            "status": "schema_discovery_failed",
                            "farmers": [{"error": "Could not discover table structure"}],
                            "total": 1
                        }
                        
                except Exception as schema_error:
                    # Fallback - just show we found farmers
                    farmers = [
                        {"info": f"Found {total_count} farmers in database"},
                        {"error": f"Schema discovery failed: {str(schema_error)}"}
                    ]
                    return {"status": "partial_success", "farmers": farmers, "total": 2}
                    
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_farmer_fields(farmer_id: int):
    """Standard Query: List all fields of a specific farmer - FIXED VERSION"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # FIXED: Use correct column names from schema
                try:
                    cursor.execute("""
                        SELECT id, field_name, area_ha, country, notes
                        FROM fields 
                        WHERE farmer_id = %s 
                        ORDER BY field_name
                        LIMIT 20
                    """, (farmer_id,))
                    results = cursor.fetchall()
                    cursor.close()
                    
                    fields = []
                    for r in results:
                        fields.append({
                            "field_id": r[0],
                            "field_name": r[1] if r[1] else "N/A",
                            "area_ha": r[2] if len(r) > 2 and r[2] else "N/A",
                            "country": r[3] if len(r) > 3 and r[3] else "N/A",
                            "notes": r[4] if len(r) > 4 and r[4] else "N/A"
                        })
                    
                except psycopg2.Error as schema_error:
                    # Fallback query with minimal columns
                    cursor.execute("""
                        SELECT id, field_name 
                        FROM fields 
                        WHERE farmer_id = %s 
                        ORDER BY field_name
                        LIMIT 20
                    """, (farmer_id,))
                    results = cursor.fetchall()
                    cursor.close()
                    
                    fields = []
                    for r in results:
                        fields.append({
                            "field_id": r[0],
                            "field_name": r[1] if r[1] else "N/A",
                            "area_ha": "N/A",
                            "country": "N/A",
                            "notes": "N/A"
                        })
                
                return {"status": "success", "fields": fields, "total": len(fields)}
            else:
                return {"status": "connection_failed", "error": "No database connection"}
    except Exception as e:
        return {"status": "error", "error": f"Database query failed: {str(e)}"}

async def get_field_tasks(farmer_id: int, field_id: int):
    """Standard Query: List all tasks on specific field - FIXED VERSION using task_fields junction"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                try:
                    # FIXED: Use task_fields junction table
                    cursor.execute("""
                        SELECT 
                            t.id, 
                            t.task_type, 
                            t.description, 
                            t.status, 
                            t.date_performed, 
                            t.crop_name,
                            t.quantity,
                            t.rate_per_ha
                        FROM tasks t
                        INNER JOIN task_fields tf ON t.id = tf.task_id
                        WHERE tf.field_id = %s 
                        ORDER BY t.date_performed DESC
                        LIMIT 20
                    """, (field_id,))
                    results = cursor.fetchall()
                    cursor.close()
                    
                    tasks = []
                    for r in results:
                        tasks.append({
                            "task_id": r[0],
                            "task_type": r[1] if r[1] else "N/A",
                            "description": r[2] if len(r) > 2 and r[2] else "N/A",
                            "status": r[3] if len(r) > 3 and r[3] else "N/A",
                            "date_performed": str(r[4]) if len(r) > 4 and r[4] else None,
                            "crop_name": r[5] if len(r) > 5 and r[5] else "N/A",
                            "quantity": r[6] if len(r) > 6 and r[6] else "N/A",
                            "rate_per_ha": r[7] if len(r) > 7 and r[7] else "N/A"
                        })
                    
                except psycopg2.Error as schema_error:
                    # Fallback query with minimal columns
                    cursor.execute("""
                        SELECT t.id, t.task_type 
                        FROM tasks t
                        INNER JOIN task_fields tf ON t.id = tf.task_id
                        WHERE tf.field_id = %s 
                        LIMIT 20
                    """, (field_id,))
                    results = cursor.fetchall()
                    cursor.close()
                    
                    tasks = []
                    for r in results:
                        tasks.append({
                            "task_id": r[0],
                            "task_type": r[1] if r[1] else "N/A",
                            "description": "N/A",
                            "status": "N/A",
                            "date_performed": None,
                            "crop_name": "N/A",
                            "quantity": "N/A",
                            "rate_per_ha": "N/A"
                        })
                
                return {"status": "success", "tasks": tasks, "total": len(tasks)}
            else:
                return {"status": "connection_failed", "error": "No database connection"}
    except Exception as e:
        return {"status": "error", "error": f"Database query failed: {str(e)}"}

# PART 2: LLM Query Assistant is now in llm_integration.py

# Request models
class NaturalQueryRequest(BaseModel):
    question: str

# HTML Interface (SAFE VERSION)
AGRICULTURAL_DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AVA OLO Agricultural Database Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .section { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .agricultural { background: #e8f5e8; border-left: 5px solid #27ae60; }
        .llm { background: #e8f4f8; border-left: 5px solid #3498db; }
        .warning { background: #fff3cd; border-left: 5px solid #ffc107; }
        textarea { width: 100%; height: 80px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        input { width: 100px; padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
        button { background: #27ae60; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .llm-button { background: #3498db; }
        button:hover { opacity: 0.8; }
        .results { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; max-height: 400px; overflow-y: auto; }
        .success { background: #e8f5e8; }
        .error { background: #ffebee; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f5f5f5; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌾 AVA OLO Agricultural Database Dashboard</h1>
        <p><strong>Constitutional Compliance:</strong> Agricultural Intelligence System | AWS RDS Connected | Error Isolation Active</p>
        
        <!-- System Status -->
        <div class="section warning" style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #92400e;">🔍 System Status</h3>
            <div id="system-status-details">
                <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                    <span class="status-icon" style="margin-right: 10px; font-size: 16px;">⏳</span>
                    <span class="status-text">Database: Checking connection...</span>
                </div>
                <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                    <span class="status-icon" style="margin-right: 10px; font-size: 16px;">⏳</span>
                    <span class="status-text">LLM: Checking availability...</span>
                </div>
                <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                    <span class="status-icon" style="margin-right: 10px; font-size: 16px;">⏳</span>
                    <span class="status-text">Constitutional: Checking compliance...</span>
                </div>
            </div>
        </div>
        
        <!-- Schema Discovery -->
        <div class="section warning">
            <h3>🔍 Database Tools</h3>
            <p><a href="/schema/">View Complete Database Schema</a> - Discover all tables and columns</p>
            <p><a href="/diagnostics/">Run Connection Diagnostics</a> - Test database connections and configurations</p>
        </div>
        
        <!-- PART 1: Standard Agricultural Queries -->
        <div class="section agricultural">
            <h2>📊 Part 1: Standard Agricultural Queries (Always Available)</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                <div>
                    <h4>Total Farmers</h4>
                    <button onclick="getFarmerCount()">Count Farmers</button>
                </div>
                
                <div>
                    <h4>List All Farmers</h4>
                    <button onclick="getAllFarmers()">List Farmers</button>
                </div>
                
                <div>
                    <h4>Farmer's Fields</h4>
                    <input type="number" id="farmerId" placeholder="Farmer ID" style="width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px;">
                    <button onclick="getFarmerFields()" style="width: 100%; margin-bottom: 5px;">Get Fields</button>
                    <button onclick="clearFieldInputs()" style="background-color: #ef4444; width: 100%; padding: 8px 16px; font-size: 14px;">🧹 Clear Field</button>
                </div>
                
                <div>
                    <h4>Field Tasks</h4>
                    <input type="number" id="taskFarmerId" placeholder="Farmer ID" style="width: 100%; padding: 10px; margin-bottom: 5px; border: 1px solid #ccc; border-radius: 4px;">
                    <input type="number" id="fieldId" placeholder="Field ID" style="width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px;">
                    <button onclick="getFieldTasks()" style="width: 100%; margin-bottom: 5px;">Get Tasks</button>
                    <button onclick="clearTaskInputs()" style="background-color: #ef4444; width: 100%; padding: 8px 16px; font-size: 14px;">🧹 Clear Fields</button>
                </div>
            </div>
        </div>
        
        <!-- PART 2: LLM Natural Language Assistant -->
        <div class="section llm">
            <h2>🤖 Part 2: LLM Natural Language Query Assistant</h2>
            <p><strong>Ask questions in natural language - AI will help generate SQL queries</strong></p>
            
            <div>
                <h4>Ask Agricultural Questions:</h4>
                <textarea id="naturalQuestion" placeholder="Examples:
• How many farmers do we have?
• Show me all farmers
• Which fields belong to farmer ID 1?
• What tasks are there for field 5?"></textarea>
                <br>
                <button class="llm-button" onclick="askNaturalQuestion()">🧠 Try LLM Assistant</button>
            </div>
        </div>
        
        <!-- Results Display -->
        <div id="results" class="results" style="display: none;">
            <h3>Results:</h3>
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
        // Check system status on load
        window.onload = function() {
            fetch('/api/debug/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('systemStatus').innerHTML = 
                        `Database: ${data.database_connected} | LLM: ${data.llm_model || 'Not Available'} | Constitutional: ${data.constitutional_compliance ? '✅' : '❌'}`;
                })
                .catch(error => {
                    document.getElementById('systemStatus').innerHTML = 'Status check failed - system may have issues';
                });
        };
        
        function showResults(data, isSuccess = true) {
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('resultsContent');
            
            resultsDiv.style.display = 'block';
            resultsDiv.className = isSuccess ? 'results success' : 'results error';
            
            if (typeof data === 'string') {
                contentDiv.innerHTML = data;
            } else {
                contentDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }
        }
        
        // Standard Agricultural Queries
        function getFarmerCount() {
            fetch('/api/agricultural/farmer-count')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showResults(`<h4>🌾 Total Farmers: ${data.farmer_count}</h4><p>Constitutional agricultural system operational!</p>`);
                    } else {
                        showResults(data, false);
                    }
                });
        }
        
        function getAllFarmers() {
            fetch('/api/agricultural/farmers')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        let html = `<h4>🌾 All Farmers (${data.total} of ${data.total_in_db}):</h4>`;
                        
                        // Show discovered columns
                        if (data.discovered_columns) {
                            html += `<p><strong>Discovered columns:</strong> ${data.discovered_columns.join(', ')}</p>`;
                        }
                        
                        // Build table dynamically based on actual data
                        if (data.farmers && data.farmers.length > 0) {
                            html += '<table><tr>';
                            // Get headers from first farmer object
                            const headers = Object.keys(data.farmers[0]);
                            headers.forEach(header => {
                                html += `<th>${header}</th>`;
                            });
                            html += '</tr>';
                            
                            // Add data rows
                            data.farmers.forEach(farmer => {
                                html += '<tr>';
                                headers.forEach(header => {
                                    html += `<td>${farmer[header] || 'N/A'}</td>`;
                                });
                                html += '</tr>';
                            });
                            html += '</table>';
                        }
                        
                        showResults(html);
                    } else {
                        showResults(data, false);
                    }
                });
        }
        
        function getFarmerFields() {
            const farmerId = document.getElementById('farmerId').value;
            if (!farmerId) {
                alert('Please enter Farmer ID');
                return;
            }
            
            fetch(`/api/agricultural/farmer-fields/${farmerId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        let html = `<h4>🌾 Fields for Farmer ${farmerId} (${data.total}):</h4><table><tr><th>Field ID</th><th>Field Name</th><th>Area (ha)</th><th>Country</th><th>Notes</th></tr>`;
                        data.fields.forEach(field => {
                            html += `<tr><td>${field.field_id}</td><td>${field.field_name}</td><td>${field.area_ha}</td><td>${field.country}</td><td>${field.notes}</td></tr>`;
                        });
                        html += '</table>';
                        showResults(html);
                    } else {
                        showResults(data, false);
                    }
                });
        }
        
        function getFieldTasks() {
            const farmerId = document.getElementById('taskFarmerId').value;
            const fieldId = document.getElementById('fieldId').value;
            if (!farmerId || !fieldId) {
                alert('Please enter both Farmer ID and Field ID');
                return;
            }
            
            fetch(`/api/agricultural/field-tasks/${farmerId}/${fieldId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        let html = `<h4>🌾 Tasks for Field ${fieldId} (${data.total}):</h4><table><tr><th>Task ID</th><th>Task Type</th><th>Description</th><th>Status</th><th>Date Performed</th><th>Crop</th></tr>`;
                        data.tasks.forEach(task => {
                            html += `<tr><td>${task.task_id}</td><td>${task.task_type}</td><td>${task.description}</td><td>${task.status}</td><td>${task.date_performed || 'N/A'}</td><td>${task.crop_name || 'N/A'}</td></tr>`;
                        });
                        html += '</table>';
                        showResults(html);
                    } else {
                        showResults(data, false);
                    }
                });
        }
        
        // LLM Natural Language Query
        function askNaturalQuestion() {
            const question = document.getElementById('naturalQuestion').value.trim();
            if (!question) {
                alert('Please enter a question');
                return;
            }
            
            showResults('<p>🧠 Checking LLM availability...</p>');
            
            fetch('/api/natural-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: question })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let html = `
                        <h4>🧠 LLM Query Result:</h4>
                        <p><strong>Your Question:</strong> ${data.original_query}</p>
                        <p><strong>Generated SQL:</strong></p>
                        <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">${data.sql_query || 'No SQL generated'}</pre>
                    `;
                    
                    // If query was executed
                    if (data.execution_result && data.execution_result.status === 'success') {
                        html += `<h5>📊 Query Results (${data.execution_result.row_count} rows):</h5>`;
                        
                        if (data.execution_result.data && data.execution_result.data.length > 0) {
                            html += '<table style="width: 100%; margin-top: 10px;">';
                            
                            // Headers
                            const headers = Object.keys(data.execution_result.data[0]);
                            html += '<tr>';
                            headers.forEach(h => html += `<th>${h}</th>`);
                            html += '</tr>';
                            
                            // Data
                            data.execution_result.data.forEach(row => {
                                html += '<tr>';
                                headers.forEach(h => html += `<td>${row[h] || 'null'}</td>`);
                                html += '</tr>';
                            });
                            html += '</table>';
                        }
                    } else if (data.execution_result && data.execution_result.error) {
                        html += `<p style="color: red;">Execution Error: ${data.execution_result.error}</p>`;
                    }
                    
                    showResults(html);
                } else if (data.status === 'unavailable') {
                    showResults(`<p style="color: orange;">🔔 ${data.error}<br>${data.fallback}</p>`);
                } else {
                    showResults(data, false);
                }
            })
            .catch(error => {
                showResults(`<p style="color: red;">Request failed: ${error}</p>`);
            });
        }
        
        // Clear functions
        function clearFieldInputs() {
            document.getElementById('farmerId').value = '';
            document.getElementById('results').innerHTML = '';
            
            // Visual feedback
            const button = event.target;
            const originalText = button.innerHTML;
            const originalColor = button.style.backgroundColor;
            button.innerHTML = '✅ Cleared';
            button.style.backgroundColor = '#10b981';
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.backgroundColor = originalColor;
            }, 1500);
        }
        
        function clearTaskInputs() {
            document.getElementById('taskFarmerId').value = '';
            document.getElementById('fieldId').value = '';
            document.getElementById('results').innerHTML = '';
            
            // Visual feedback
            const button = event.target;
            const originalText = button.innerHTML;
            const originalColor = button.style.backgroundColor;
            button.innerHTML = '✅ Cleared';
            button.style.backgroundColor = '#10b981';
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.backgroundColor = originalColor;
            }, 1500);
        }
        
        // Update system status on page load
        async function updateSystemStatus() {
            try {
                const response = await fetch('/api/system-status');
                const status = await response.json();
                
                const statusDetails = document.getElementById('system-status-details');
                statusDetails.innerHTML = `
                    <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                        <span class="status-icon" style="margin-right: 10px; font-size: 16px;">${status.database.icon}</span>
                        <span class="status-text">Database: ${status.database.message}</span>
                    </div>
                    <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                        <span class="status-icon" style="margin-right: 10px; font-size: 16px;">${status.llm.icon}</span>
                        <span class="status-text">LLM: ${status.llm.message}</span>
                    </div>
                    <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                        <span class="status-icon" style="margin-right: 10px; font-size: 16px;">${status.constitutional.icon}</span>
                        <span class="status-text">Constitutional: ${status.constitutional.message}</span>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to update system status:', error);
            }
        }
        
        // Call on page load
        document.addEventListener('DOMContentLoaded', updateSystemStatus);
    </script>
</body>
</html>
"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def agricultural_dashboard():
    """Agricultural Database Dashboard - Safe Version"""
    return HTMLResponse(content=AGRICULTURAL_DASHBOARD_HTML)

# Add diagnostics viewer page
@app.get("/diagnostics/", response_class=HTMLResponse)
async def diagnostics_viewer():
    """Visual diagnostics interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Connection Diagnostics</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .section { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 8px; }
            .success { background: #e8f5e8; border-left: 5px solid #27ae60; }
            .error { background: #ffebee; border-left: 5px solid #e74c3c; }
            .warning { background: #fff3cd; border-left: 5px solid #ffc107; }
            .info { background: #e3f2fd; border-left: 5px solid #2196f3; }
            button { background: #27ae60; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1em; }
            button:hover { background: #219a52; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f5f5f5; }
            .recommendation { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .recommendation.fix { background: #fff3cd; }
            .recommendation.critical { background: #ffebee; }
            .recommendation.info { background: #e3f2fd; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Database Connection Diagnostics</h1>
            <p>Comprehensive testing of database connections and configurations</p>
            
            <button onclick="runDiagnostics()">🔧 Run Complete Diagnostics</button>
            
            <div id="diagnosticsResults" style="margin-top: 20px;"></div>
        </div>
        
        <script>
            function runDiagnostics() {
                document.getElementById('diagnosticsResults').innerHTML = '<p>🔍 Running diagnostics...</p>';
                
                fetch('/api/diagnostics')
                    .then(response => response.json())
                    .then(data => {
                        let html = '<h2>Diagnostic Results</h2>';
                        
                        // 1. Environment Variables
                        html += '<div class="section">';
                        html += '<h3>📋 Environment Variables</h3>';
                        html += '<table>';
                        html += '<tr><th>Variable</th><th>Status</th><th>Value/Length</th></tr>';
                        
                        for (const [varName, info] of Object.entries(data.environment_check || {})) {
                            const status = info.present ? '✅' : '❌';
                            const value = info.value !== '***' ? info.value : `Length: ${info.length}`;
                            html += `<tr>
                                <td>${varName}</td>
                                <td>${status}</td>
                                <td>${value || 'Not set'}</td>
                            </tr>`;
                        }
                        html += '</table>';
                        html += '</div>';
                        
                        // 2. psycopg2 Test Results
                        if (data.psycopg2_test) {
                            const test = data.psycopg2_test;
                            const statusClass = test.status === 'success' ? 'success' : 'error';
                            html += `<div class="section ${statusClass}">`;
                            html += '<h3>🔌 Current Connection Test (psycopg2)</h3>';
                            
                            if (test.status === 'success') {
                                html += `<p>✅ <strong>Connected to database:</strong> ${test.database}</p>`;
                                html += `<p><strong>Farmer count:</strong> ${test.farmer_count}</p>`;
                                
                                if (test.farmers_columns && test.farmers_columns.length > 0) {
                                    html += '<p><strong>Farmers table columns:</strong></p>';
                                    html += '<ul>';
                                    test.farmers_columns.forEach(col => {
                                        html += `<li>${col.name} (${col.type})</li>`;
                                    });
                                    html += '</ul>';
                                }
                            } else {
                                html += `<p>❌ <strong>Status:</strong> ${test.status}</p>`;
                                if (test.error) {
                                    html += `<p><strong>Error:</strong> ${test.error}</p>`;
                                }
                            }
                            html += '</div>';
                        }
                        
                        // 3. AsyncPG Tests
                        if (data.asyncpg_tests && data.asyncpg_tests.length > 0) {
                            html += '<div class="section">';
                            html += '<h3>🧪 Additional Connection Tests (asyncpg)</h3>';
                            
                            data.asyncpg_tests.forEach(test => {
                                const testClass = test.status === 'success' ? 'success' : 'error';
                                html += `<div class="section ${testClass}">`;
                                html += `<h4>Database: ${test.database} (SSL: ${test.ssl})</h4>`;
                                
                                if (test.status === 'success') {
                                    html += `<p>✅ Connected successfully</p>`;
                                    html += `<p>Tables in database: ${test.table_count}</p>`;
                                    html += `<p>Farmers table exists: ${test.farmers_table_exists ? 'Yes' : 'No'}</p>`;
                                    
                                    if (test.farmer_count !== undefined) {
                                        html += `<p>Farmers: ${test.farmer_count}</p>`;
                                    }
                                    
                                    if (test.farmer_columns) {
                                        html += `<p>Columns: ${test.farmer_columns.join(', ')}</p>`;
                                    }
                                } else {
                                    html += `<p>❌ Failed: ${test.error || 'Unknown error'}</p>`;
                                }
                                
                                html += '</div>';
                            });
                            
                            html += '</div>';
                        }
                        
                        // 4. Recommendations
                        if (data.recommendations && data.recommendations.length > 0) {
                            html += '<div class="section">';
                            html += '<h3>💡 Recommendations</h3>';
                            
                            data.recommendations.forEach(rec => {
                                html += `<div class="recommendation ${rec.type}">`;
                                html += `<strong>${rec.message}</strong><br>`;
                                html += `Action: ${rec.action}`;
                                html += '</div>';
                            });
                            
                            html += '</div>';
                        }
                        
                        // 5. Raw JSON
                        html += '<div class="section">';
                        html += '<h3>📄 Raw Diagnostic Data</h3>';
                        html += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        html += '</div>';
                        
                        document.getElementById('diagnosticsResults').innerHTML = html;
                    })
                    .catch(error => {
                        document.getElementById('diagnosticsResults').innerHTML = 
                            `<div class="section error">
                                <p>❌ Diagnostic request failed: ${error}</p>
                            </div>`;
                    });
            }
        </script>
    </body>
    </html>
    """)

# Add simple HTML interface to view schema
@app.get("/schema/", response_class=HTMLResponse)
async def schema_viewer():
    """Simple schema viewer interface"""
    # Read the fixed HTML file
    with open('schema_viewer_fix.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Old version kept for reference
@app.get("/schema-old/", response_class=HTMLResponse)
async def schema_viewer_old():
    """Old schema viewer interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Schema Discovery</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .table-info { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 8px; }
            .columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
            .column { background: #f9f9f9; padding: 8px; border-radius: 4px; font-size: 0.9em; }
            button { background: #27ae60; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1em; }
            button:hover { background: #219a52; }
            .sample-data { background: #f0f8ff; padding: 10px; border-radius: 5px; margin: 10px 0; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Database Schema Discovery</h1>
            <p>Discover the structure of your agricultural database</p>
            
            <button onclick="discoverSchema()">🔍 Discover Complete Schema</button>
            
            <div id="schemaResults" style="margin-top: 20px;"></div>
        </div>
        
        <script>
            function discoverSchema() {
                document.getElementById('schemaResults').innerHTML = '<p>🔍 Discovering schema...</p>';
                
                fetch('/api/debug/discover-schema')
                    .then(response => response.json())
                    .then(data => {
                        let html = '<h2>Database Schema Discovery Results</h2>';
                        
                        if (data.status === 'success') {
                            html += `<p><strong>Total Tables:</strong> ${data.summary.total_tables}</p>`;
                            html += `<p><strong>Tables with Data:</strong> ${data.summary.tables_with_data}</p>`;
                            
                            // Show each table
                            for (const [tableName, tableInfo] of Object.entries(data.schema_details)) {
                                html += `<div class="table-info">`;
                                html += `<h3>📊 Table: ${tableName}</h3>`;
                                
                                if (tableInfo.error) {
                                    html += `<p style="color: red;">Error: ${tableInfo.error}</p>`;
                                } else {
                                    html += `<p><strong>Rows:</strong> ${tableInfo.row_count}</p>`;
                                    
                                    // Show columns
                                    html += `<h4>Columns:</h4>`;
                                    html += `<div class="columns">`;
                                    tableInfo.columns.forEach(col => {
                                        html += `<div class="column">
                                            <strong>${col.name}</strong><br>
                                            Type: ${col.type}<br>
                                            Nullable: ${col.nullable}
                                        </div>`;
                                    });
                                    html += `</div>`;
                                    
                                    // Show sample data
                                    if (tableInfo.sample_data && tableInfo.sample_data.length > 0) {
                                        html += `<h4>Sample Data:</h4>`;
                                        html += `<div class="sample-data">`;
                                        html += `<table border="1" style="width: 100%; border-collapse: collapse;">`;
                                        
                                        // Header
                                        html += `<tr>`;
                                        tableInfo.column_names.forEach(colName => {
                                            html += `<th style="padding: 5px; background: #f0f0f0;">${colName}</th>`;
                                        });
                                        html += `</tr>`;
                                        
                                        // Data rows
                                        tableInfo.sample_data.forEach(row => {
                                            html += `<tr>`;
                                            row.forEach(cell => {
                                                html += `<td style="padding: 5px;">${cell || 'NULL'}</td>`;
                                            });
                                            html += `</tr>`;
                                        });
                                        
                                        html += `</table>`;
                                        html += `</div>`;
                                    }
                                    
                                    // Generate simple query
                                    html += `<h4>Simple Query:</h4>`;
                                    html += `<pre>SELECT * FROM ${tableName} LIMIT 10;</pre>`;
                                }
                                
                                html += `</div>`;
                            }
                        } else {
                            html += `<p style="color: red;">Error: ${data.error}</p>`;
                        }
                        
                        // Add copyable text version at the bottom
                        if (data.status === 'success' && data.schema_details) {
                            html += '<hr style="margin: 40px 0;">';
                            html += '<h2>📋 Copyable Schema Summary</h2>';
                            html += '<p>Copy this text to share the schema:</p>';
                            html += '<textarea id="schemaCopy" style="width: 100%; height: 400px; font-family: monospace; padding: 10px; border: 1px solid #ddd; border-radius: 5px;" readonly>';
                            
                            // Build copyable text
                            let schemaText = 'DATABASE SCHEMA SUMMARY\n';
                            schemaText += '======================\n\n';
                            
                            for (const [tableName, tableInfo] of Object.entries(data.schema_details)) {
                                if (!tableInfo.error) {
                                    schemaText += `TABLE: ${tableName}\n`;
                                    schemaText += `Rows: ${tableInfo.row_count}\n`;
                                    schemaText += `Columns:\n`;
                                    
                                    tableInfo.columns.forEach(col => {
                                        schemaText += `  - ${col.name} (${col.type}) ${col.nullable === 'NO' ? 'NOT NULL' : 'NULL'}\n`;
                                    });
                                    
                                    schemaText += '\n';
                                }
                            }
                            
                            // Add relationships section
                            schemaText += 'KEY RELATIONSHIPS:\n';
                            schemaText += '==================\n';
                            
                            // Try to identify foreign keys
                            for (const [tableName, tableInfo] of Object.entries(data.schema_details)) {
                                if (!tableInfo.error && tableInfo.columns) {
                                    tableInfo.columns.forEach(col => {
                                        if (col.name.endsWith('_id') && col.name !== 'id') {
                                            schemaText += `${tableName}.${col.name} -> likely references ${col.name.replace('_id', 's')}.id\n`;
                                        }
                                    });
                                }
                            }
                            
                            html += schemaText;
                            html += '</textarea>';
                            html += '<button onclick="copySchema()" style="margin-top: 10px;">📋 Copy to Clipboard</button>';
                        }
                        
                        document.getElementById('schemaResults').innerHTML = html;
                    })
                    .catch(error => {
                        document.getElementById('schemaResults').innerHTML = `<p style="color: red;">Request failed: ${error}</p>`;
                    });
            }
            
            function copySchema() {
                const textarea = document.getElementById('schemaCopy');
                textarea.select();
                document.execCommand('copy');
                alert('Schema copied to clipboard!');
            }
        </script>
    </body>
    </html>
    """)

# PART 1: Standard Agricultural Query APIs (ALWAYS WORK)
@app.get("/api/agricultural/farmer-count")
async def api_farmer_count():
    return await get_farmer_count()

# Add a test endpoint that's IDENTICAL to get_farmer_count
@app.get("/api/agricultural/test-farmers")
async def test_farmers_identical():
    """Test endpoint - IDENTICAL to farmer count but different name"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as farmer_count FROM farmers")
                result = cursor.fetchone()
                return {"status": "success", "farmer_count": result[0], "test": "identical_to_count"}
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/agricultural/farmers")
async def api_all_farmers():
    return await get_all_farmers()

@app.get("/api/agricultural/farmer-fields/{farmer_id}")
async def api_farmer_fields(farmer_id: int):
    return await get_farmer_fields(farmer_id)

@app.get("/api/agricultural/field-tasks/{farmer_id}/{field_id}")
async def api_field_tasks(farmer_id: int, field_id: int):
    return await get_field_tasks(farmer_id, field_id)

# PART 2: LLM Natural Language Query API moved to new endpoints below

# Add this schema discovery endpoint to main.py
@app.get("/api/debug/discover-schema")
async def discover_complete_schema():
    """Discover complete database schema - all tables and columns"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # 1. Get all tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                schema_info = {}
                
                # 2. For each table, get columns and sample data
                for table in tables:
                    try:
                        # Get column information
                        cursor.execute("""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns 
                            WHERE table_name = %s 
                            ORDER BY ordinal_position
                        """, (table,))
                        columns = cursor.fetchall()
                        
                        # Get row count
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        
                        # Get sample data (first 2 rows)
                        column_names = [col[0] for col in columns]
                        if column_names:
                            column_list = ', '.join(column_names)
                            cursor.execute(f"SELECT {column_list} FROM {table} LIMIT 2")
                            sample_data = cursor.fetchall()
                        else:
                            sample_data = []
                        
                        schema_info[table] = {
                            "columns": [{"name": col[0], "type": col[1], "nullable": col[2], "default": col[3]} for col in columns],
                            "row_count": row_count,
                            "sample_data": sample_data,
                            "column_names": column_names
                        }
                        
                    except Exception as table_error:
                        schema_info[table] = {"error": f"Could not analyze table: {str(table_error)}"}
                
                return {
                    "status": "success",
                    "database_name": "Connected to database",
                    "tables": tables,
                    "schema_details": schema_info,
                    "summary": {
                        "total_tables": len(tables),
                        "tables_with_data": len([t for t in schema_info.values() if isinstance(t, dict) and t.get("row_count", 0) > 0])
                    }
                }
                
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Diagnostics endpoint for troubleshooting
@app.get("/api/diagnostics")
async def run_diagnostics():
    """Run enhanced database connection diagnostics"""
    import asyncio
    import asyncpg
    import json
    
    diagnostics = {
        "environment_check": {},
        "psycopg2_test": {},
        "asyncpg_tests": [],
        "recommendations": []
    }
    
    # 1. Environment Check
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    for var in required_vars:
        value = os.getenv(var)
        diagnostics["environment_check"][var] = {
            "present": bool(value),
            "length": len(value) if value else 0,
            "value": value if var not in ['DB_PASSWORD'] and value else "***"
        }
    
    # 2. Test with psycopg2 (current connection method)
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT current_database()")
                current_db = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM farmers")
                farmer_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'farmers' 
                    ORDER BY ordinal_position
                """)
                farmers_columns = cursor.fetchall()
                
                diagnostics["psycopg2_test"] = {
                    "status": "success",
                    "database": current_db,
                    "farmer_count": farmer_count,
                    "farmers_columns": [{"name": col[0], "type": col[1]} for col in farmers_columns]
                }
            else:
                diagnostics["psycopg2_test"] = {"status": "connection_failed"}
    except Exception as e:
        diagnostics["psycopg2_test"] = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # 3. Test with asyncpg for more detailed diagnostics
    try:
        # Test different configurations
        env_host = os.getenv('DB_HOST', '')
        env_user = os.getenv('DB_USER', 'postgres')
        env_password = os.getenv('DB_PASSWORD', '')
        env_port = os.getenv('DB_PORT', '5432')
        env_db = os.getenv('DB_NAME', 'postgres')
        
        # Test configurations
        test_configs = [
            {"database": env_db, "ssl": "require"},
            {"database": "postgres", "ssl": "require"},
            {"database": "farmer_crm", "ssl": "require"},
        ]
        
        for config in test_configs:
            test_result = {
                "database": config["database"],
                "ssl": config["ssl"],
                "status": "unknown"
            }
            
            try:
                # Build connection parameters (not URL) to fix IPv6 error
                connection_params = {
                    'host': env_host,
                    'port': int(env_port),
                    'user': env_user,
                    'password': env_password,
                    'database': config['database'],
                    'server_settings': {
                        'application_name': 'ava_olo_dashboard'
                    }
                }
                
                # Add SSL configuration
                if config['ssl'] != 'disable':
                    connection_params['ssl'] = config['ssl']
                else:
                    connection_params['ssl'] = False
                
                # Attempt async connection
                conn = await asyncpg.connect(**connection_params, timeout=5)
                
                # Test queries
                table_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                
                # Check for farmers table
                farmers_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='farmers')"
                )
                
                if farmers_exists:
                    farmer_count = await conn.fetchval("SELECT COUNT(*) FROM farmers")
                    test_result["farmer_count"] = farmer_count
                    
                    # Get column names
                    columns = await conn.fetch("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'farmers' ORDER BY ordinal_position
                    """)
                    test_result["farmer_columns"] = [row['column_name'] for row in columns]
                
                await conn.close()
                
                test_result["status"] = "success"
                test_result["table_count"] = table_count
                test_result["farmers_table_exists"] = farmers_exists
                
            except Exception as e:
                test_result["status"] = "failed"
                test_result["error"] = str(e)[:200]
            
            diagnostics["asyncpg_tests"].append(test_result)
    
    except Exception as e:
        diagnostics["asyncpg_error"] = str(e)
    
    # 4. Generate recommendations
    if diagnostics["psycopg2_test"].get("status") == "success":
        diagnostics["recommendations"].append({
            "type": "info",
            "message": "psycopg2 connection works",
            "action": "Continue using current connection method"
        })
        
        # Check column names
        columns = [col["name"] for col in diagnostics["psycopg2_test"].get("farmers_columns", [])]
        if columns and "farmer_id" not in columns and "id" in columns:
            diagnostics["recommendations"].append({
                "type": "fix",
                "message": "Primary key is 'id' not 'farmer_id'",
                "action": "Update all queries to use 'id' instead of 'farmer_id'"
            })
    
    # Check environment variables
    missing_vars = [var for var, info in diagnostics["environment_check"].items() if not info["present"]]
    if missing_vars:
        diagnostics["recommendations"].append({
            "type": "critical",
            "message": f"Missing environment variables: {missing_vars}",
            "action": "Set these variables in AWS App Runner configuration"
        })
    
    return diagnostics

# Debug endpoint - check which database Count Farmers actually uses
@app.get("/api/debug/status")
async def debug_status():
    # Test database connection with detailed info
    db_status = "disconnected"
    actual_database = "unknown"
    
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    db_status = "connected"
                    # Check which database we're actually connected to
                    cursor.execute("SELECT current_database()")
                    actual_database = cursor.fetchone()[0]
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Enhanced OpenAI check
    openai_key = os.getenv('OPENAI_API_KEY')
    openai_debug = {
        "key_present": bool(openai_key),
        "key_length": len(openai_key) if openai_key else 0,
        "key_preview": openai_key[:10] + "..." if openai_key and len(openai_key) > 10 else "N/A",
        "available": OPENAI_AVAILABLE
    }
    
    return {
        "database_connected": f"AWS RDS PostgreSQL - {db_status}",
        "actual_database": actual_database,
        "expected_database": os.getenv('DB_NAME', 'farmer_crm'),
        "llm_model": "GPT-4" if OPENAI_AVAILABLE else "Not Available", 
        "constitutional_compliance": True,
        "agricultural_focus": "Farmers, Fields, Tasks",
        "openai_key_configured": OPENAI_AVAILABLE,
        "openai_debug": openai_debug
    }

# Improved system status endpoint
@app.get("/api/system-status")
async def get_system_status():
    """
    Get detailed system status for improved display
    """
    status = {
        "database": {
            "status": "checking",
            "message": "AWS RDS PostgreSQL",
            "icon": "⏳"
        },
        "llm": {
            "status": "not_available", 
            "message": "OpenAI API key not configured",
            "icon": "❌"
        },
        "constitutional": {
            "status": "compliant",
            "message": "All 13 principles implemented",
            "icon": "✅"
        }
    }
    
    # Test database connection
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    status["database"]["status"] = "connected"
                    status["database"]["message"] = "AWS RDS PostgreSQL - Connected"
                    status["database"]["icon"] = "✅"
                else:
                    status["database"]["status"] = "failed"
                    status["database"]["message"] = "Connection failed"
                    status["database"]["icon"] = "❌"
            else:
                status["database"]["status"] = "failed"
                status["database"]["message"] = "Connection failed"
                status["database"]["icon"] = "❌"
    except Exception as e:
        status["database"]["status"] = "error"
        status["database"]["message"] = f"Error: {str(e)[:50]}..."
        status["database"]["icon"] = "❌"
    
    # Test LLM availability
    if OPENAI_AVAILABLE:
        status["llm"]["status"] = "available"
        status["llm"]["message"] = "OpenAI API configured"
        status["llm"]["icon"] = "✅"
    
    # Check constitutional compliance
    try:
        compliance = await check_constitutional_compliance()
        if compliance.get("fully_compliant"):
            status["constitutional"]["status"] = "compliant"
            status["constitutional"]["message"] = f"All {compliance['total_principles']} principles implemented"
            status["constitutional"]["icon"] = "✅"
        else:
            status["constitutional"]["status"] = "partial"
            status["constitutional"]["message"] = f"{compliance['compliant']}/{compliance['total_principles']} principles compliant"
            status["constitutional"]["icon"] = "⚠️"
    except:
        pass
    
    return status

# Essential schema endpoint for quick reference
@app.get("/api/essential-schema")
async def get_essential_schema():
    """
    Get essential schema for farmers, fields, tasks relationships
    🎯 Purpose: Focus on tables needed for dashboard
    """
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                essential_tables = ['farmers', 'fields', 'tasks', 'field_crops']
                schema = {}
                
                for table_name in essential_tables:
                    try:
                        # Check if table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = %s
                            )
                        """, (table_name,))
                        exists = cursor.fetchone()[0]
                        
                        if not exists:
                            schema[table_name] = {"exists": False}
                            continue
                        
                        # Get columns
                        cursor.execute("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns 
                            WHERE table_name = %s 
                            ORDER BY ordinal_position
                        """, (table_name,))
                        columns = cursor.fetchall()
                        
                        # Get row count
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        
                        # Get sample data (first 2 rows)
                        column_names = [col[0] for col in columns]
                        if column_names:
                            cursor.execute(f"SELECT {', '.join(column_names)} FROM {table_name} LIMIT 2")
                            sample_data = cursor.fetchall()
                        else:
                            sample_data = []
                        
                        schema[table_name] = {
                            "exists": True,
                            "columns": column_names,
                            "column_details": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns],
                            "row_count": row_count,
                            "sample_data": [dict(zip(column_names, row)) for row in sample_data]
                        }
                        
                    except Exception as table_error:
                        schema[table_name] = {"error": str(table_error)}
                
                return {"status": "success", "schema": schema}
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Import async functions from db_connection_fixed
from db_connection_fixed import (
    get_farmer_with_fields_and_tasks,
    get_field_with_crops,
    get_farmer_fields as async_get_farmer_fields,
    get_field_tasks as async_get_field_tasks,
    get_all_farmers as async_get_all_farmers,
    get_constitutional_db_connection as async_get_db_connection
)

# Import LLM integration functions
from llm_integration import (
    test_llm_connection,
    process_natural_language_query,
    execute_llm_generated_query,
    test_mango_compliance_queries,
    check_constitutional_compliance
)

# New API endpoints using correct async functions
@app.get("/api/farmers/{farmer_id}/fields")
async def api_get_farmer_fields(farmer_id: int):
    """API endpoint for farmer's fields using async function"""
    return await async_get_farmer_fields(farmer_id)

@app.get("/api/fields/{field_id}/tasks") 
async def api_get_field_tasks(field_id: int):
    """API endpoint for field's tasks using async function"""
    return await async_get_field_tasks(field_id)

@app.get("/api/farmers/{farmer_id}/complete")
async def api_get_farmer_complete(farmer_id: int):
    """API endpoint for complete farmer information"""
    return await get_farmer_with_fields_and_tasks(farmer_id)

@app.get("/api/fields/{field_id}/complete")
async def api_get_field_complete(field_id: int):
    """API endpoint for complete field information"""
    return await get_field_with_crops(field_id)

# LLM Integration Endpoints
@app.get("/api/llm-status")
async def check_llm_status():
    """Check LLM connection status"""
    return await test_llm_connection()

@app.post("/api/natural-query")
async def process_natural_query(request: Dict[str, Any]):
    """
    Process natural language queries
    🥭 Constitutional: Supports any language, any crop
    """
    
    query = request.get("query", "")
    farmer_id = request.get("farmer_id")
    
    if not query:
        return {"error": "No query provided"}
    
    # Get farmer context if provided
    farmer_context = None
    if farmer_id:
        try:
            conn = await async_get_db_connection()
            if conn:
                farmer = await conn.fetchrow("SELECT * FROM farmers WHERE id = $1", farmer_id)
                if farmer:
                    farmer_context = dict(farmer)
                await conn.close()
        except:
            pass
    
    # Process with LLM
    llm_result = await process_natural_language_query(query, farmer_context)
    
    if llm_result.get("ready_to_execute") and llm_result.get("sql_query"):
        # Execute the generated SQL
        conn = await async_get_db_connection()
        if conn:
            execution_result = await execute_llm_generated_query(llm_result["sql_query"], conn)
            await conn.close()
            llm_result["execution_result"] = execution_result
    
    return llm_result

@app.get("/api/test-mango-compliance")
async def test_mango_compliance():
    """
    🥭 Test constitutional mango compliance
    Test if LLM can handle Bulgarian mango farmer
    """
    
    results = await test_mango_compliance_queries()
    
    return {
        "test_name": "Mango Rule Compliance Test",
        "constitutional_principle": "🥭 Works for any crop in any country",
        "test_results": results,
        "overall_compliance": all(r["success"] for r in results)
    }

@app.get("/api/constitutional-compliance")
async def get_constitutional_compliance():
    """
    Check all 13 constitutional principles
    """
    return await check_constitutional_compliance()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)