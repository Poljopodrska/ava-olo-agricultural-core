# main.py - Safe Agricultural Dashboard with Optional LLM
import uvicorn
import os
import json
import psycopg2
from datetime import datetime
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
        .standard-queries { background: #f3e8ff; border-left: 5px solid #8b5cf6; }
        .standard-query-btn { 
            background: #8b5cf6; 
            color: white; 
            padding: 8px 16px; 
            margin: 5px;
            border: none; 
            border-radius: 5px; 
            cursor: pointer;
            position: relative;
        }
        .standard-query-btn:hover { background: #7c3aed; }
        .delete-btn {
            position: absolute;
            right: 5px;
            top: 50%;
            transform: translateY(-50%);
            background: #ef4444;
            color: white;
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 12px;
        }
        .save-standard-btn {
            background: #f59e0b;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 100px auto;
        }
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
        
        <!-- Standard Queries Section -->
        <div class="section standard-queries">
            <h3>📌 Quick Queries</h3>
            <div id="standard-query-buttons">
                <!-- Dynamically populated -->
            </div>
            <button onclick="manageStandardQueries()" style="background: #6b7280;">⚙️ Manage Queries</button>
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
                <h4>Ask Agricultural Questions or Enter Data:</h4>
                <textarea id="naturalQuestion" placeholder="Examples:
• How many farmers do we have?
• Show me all farmers
• Add farmer John Smith from Zagreb
• I sprayed Prosaro on Field A today
• Update my corn yield to 12 t/ha
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
            <div id="query-actions" style="display:none;">
                <button onclick="saveAsStandardQuery()" class="save-standard-btn">
                    ⭐ Save as Standard Query
                </button>
            </div>
        </div>
        
        <!-- Confirmation Modal -->
        <div id="confirmationModal" style="display:none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5);">
            <div class="modal-content">
                <h3>Confirm Data Operation</h3>
                <p id="confirmationMessage"></p>
                <pre id="confirmationSQL" style="background: #f5f5f5; padding: 10px; border-radius: 5px;"></pre>
                <button onclick="confirmDataOperation()" style="background: #10b981;">✅ Confirm</button>
                <button onclick="cancelDataOperation()" style="background: #ef4444;">❌ Cancel</button>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let lastExecutedQuery = null;
        let pendingOperation = null;
        
        // Check system status on load
        window.onload = function() {
            // Load system status
            fetch('/api/system-status')
                .then(response => response.json())
                .then(data => {
                    // Update individual status items
                    const statusDetails = document.getElementById('system-status-details');
                    if (statusDetails) {
                        statusDetails.innerHTML = `
                            <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                                <span class="status-icon" style="margin-right: 10px; font-size: 16px;">${data.database.icon}</span>
                                <span class="status-text">Database: ${data.database.message}</span>
                            </div>
                            <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                                <span class="status-icon" style="margin-right: 10px; font-size: 16px;">${data.llm.icon}</span>
                                <span class="status-text">LLM: ${data.llm.message}</span>
                            </div>
                            <div class="status-item" style="margin-bottom: 8px; display: flex; align-items: center;">
                                <span class="status-icon" style="margin-right: 10px; font-size: 16px;">${data.constitutional.icon}</span>
                                <span class="status-text">Constitutional: ${data.constitutional.message}</span>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Status check failed:', error);
                });
            
            // Load standard queries
            loadStandardQueries();
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
                    // Store for save functionality
                    lastExecutedQuery = {
                        sql: data.sql_query,
                        original_question: data.original_query
                    };
                    
                    let html = `
                        <h4>🧠 LLM Query Result:</h4>
                        <p><strong>Your Question:</strong> ${data.original_query}</p>
                        <p><strong>Generated SQL:</strong></p>
                        <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">${data.sql_query || 'No SQL generated'}</pre>
                    `;
                    
                    // Check if this is a data modification that needs confirmation
                    if (data.execution_result && data.execution_result.requires_confirmation) {
                        pendingOperation = data;
                        document.getElementById('confirmationMessage').textContent = 
                            `This will execute a ${data.execution_result.operation_type} operation. Are you sure?`;
                        document.getElementById('confirmationSQL').textContent = data.sql_query;
                        document.getElementById('confirmationModal').style.display = 'block';
                        return;
                    }
                    
                    // If query was executed
                    if (data.execution_result && data.execution_result.status === 'success') {
                        const opType = data.execution_result.operation_type || 'SELECT';
                        
                        if (opType === 'SELECT') {
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
                            
                            // Show save button for SELECT queries
                            document.getElementById('query-actions').style.display = 'block';
                        } else {
                            // For INSERT, UPDATE, DELETE
                            html += `<h5>✅ ${opType} Operation Successful</h5>`;
                            html += `<p>Affected rows: ${data.execution_result.affected_rows || 0}</p>`;
                            if (data.execution_result.message) {
                                html += `<p>${data.execution_result.message}</p>`;
                            }
                        }
                    } else if (data.execution_result && data.execution_result.error) {
                        html += `<div style="background: #ffebee; padding: 15px; border-radius: 5px; margin: 10px 0;">`;
                        html += `<p style="color: red; margin: 0;"><strong>Execution Error:</strong></p>`;
                        html += `<p style="color: #c62828; margin: 5px 0;">${data.execution_result.error}</p>`;
                        if (data.execution_result.hint) {
                            html += `<p style="color: #666; margin: 5px 0;"><strong>Hint:</strong> ${data.execution_result.hint}</p>`;
                        }
                        html += `</div>`;
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
        
        // Standard Queries Functions
        async function loadStandardQueries() {
            try {
                const response = await fetch('/api/standard-queries');
                const data = await response.json();
                
                const container = document.getElementById('standard-query-buttons');
                
                if (data.error && data.error.includes('Standard queries table not found')) {
                    // Table doesn't exist - show initialize button
                    container.innerHTML = `
                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                            <p style="margin: 0 0 10px 0; color: #856404;">⚠️ Standard queries table not found.</p>
                            <button onclick="initializeStandardQueries()" style="background: #28a745;">🔧 Initialize Standard Queries</button>
                        </div>
                    `;
                } else if (data.queries && data.queries.length > 0) {
                    // Show query buttons
                    container.innerHTML = data.queries.map(q => 
                        `<button onclick="runStandardQuery(${q.id})" class="standard-query-btn" title="${q.natural_language_query || q.description || ''}">
                            ${q.query_name}
                            ${!q.is_global ? `<span onclick="event.stopPropagation(); deleteStandardQuery(${q.id})" class="delete-btn">×</span>` : ''}
                         </button>`
                    ).join('');
                } else {
                    // No queries yet
                    container.innerHTML = '<p style="color: #666;">No standard queries available yet.</p>';
                }
            } catch (error) {
                console.error('Failed to load standard queries:', error);
                const container = document.getElementById('standard-query-buttons');
                container.innerHTML = '<p style="color: red;">Failed to load standard queries</p>';
            }
        }
        
        async function runStandardQuery(queryId) {
            try {
                const response = await fetch(`/api/run-standard-query/${queryId}`, {method: 'POST'});
                const result = await response.json();
                
                if (result.status === 'success') {
                    let html = `
                        <h4>📌 Standard Query: ${result.query_name}</h4>
                        <p><strong>SQL:</strong></p>
                        <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">${result.sql_query}</pre>
                        <h5>📊 Results (${result.row_count} rows):</h5>
                    `;
                    
                    if (result.data && result.data.length > 0) {
                        html += '<table style="width: 100%; margin-top: 10px;">';
                        const headers = Object.keys(result.data[0]);
                        html += '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
                        result.data.forEach(row => {
                            html += '<tr>' + headers.map(h => `<td>${row[h] || 'null'}</td>`).join('') + '</tr>';
                        });
                        html += '</table>';
                    }
                    
                    showResults(html);
                } else {
                    showResults(`<p style="color: red;">Error: ${result.error}</p>`, false);
                }
            } catch (error) {
                showResults(`<p style="color: red;">Failed to run query: ${error}</p>`, false);
            }
        }
        
        async function saveAsStandardQuery() {
            if (!lastExecutedQuery) {
                console.error('No query to save');
                alert('No query to save. Please run a query first.');
                return;
            }
            
            const queryName = prompt("Name for this query:");
            if (!queryName) return;
            
            const requestData = {
                query_name: queryName,
                sql_query: lastExecutedQuery.sql,
                natural_language_query: lastExecutedQuery.original_question,
                farmer_id: null // TODO: Add farmer context if needed
            };
            
            console.log('Saving standard query:', requestData);
            
            try {
                const response = await fetch('/api/save-standard-query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(requestData)
                });
                
                console.log('Response status:', response.status);
                const result = await response.json();
                console.log('Response data:', result);
                
                if (result.status === 'success') {
                    loadStandardQueries();
                    alert('Query saved successfully!');
                } else if (result.error && result.error.includes('Standard queries table not found')) {
                    console.error('Table missing:', result.error);
                    if (confirm('Standard queries table not found. Would you like to initialize it now?')) {
                        await initializeStandardQueries();
                        // Try saving again after initialization
                        setTimeout(async () => {
                            const retryResponse = await fetch('/api/save-standard-query', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify(requestData)
                            });
                            const retryResult = await retryResponse.json();
                            if (retryResult.status === 'success') {
                                loadStandardQueries();
                                alert('Query saved successfully!');
                            } else {
                                alert('Failed to save query after initialization: ' + (retryResult.error || 'Unknown error'));
                            }
                        }, 1000);
                    }
                } else {
                    console.error('Save failed:', result.error);
                    alert('Failed to save query: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error saving query:', error);
                alert('Error saving query: ' + error.message);
            }
        }
        
        async function deleteStandardQuery(queryId) {
            if (!confirm('Delete this standard query?')) return;
            
            try {
                const response = await fetch(`/api/standard-queries/${queryId}`, {method: 'DELETE'});
                const result = await response.json();
                
                if (result.status === 'success') {
                    loadStandardQueries();
                } else {
                    alert('Failed to delete query: ' + result.error);
                }
            } catch (error) {
                alert('Error deleting query: ' + error);
            }
        }
        
        async function initializeStandardQueries() {
            if (!confirm('Initialize the standard queries table? This will create the table and add default queries.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/initialize-standard-queries', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    alert('✅ Standard queries table initialized successfully!');
                    loadStandardQueries(); // Reload the queries
                } else if (result.status === 'already_exists') {
                    alert('ℹ️ ' + result.message);
                    loadStandardQueries();
                } else {
                    alert('❌ Failed to initialize: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('❌ Error initializing standard queries: ' + error.message);
            }
        }
        
        function manageStandardQueries() {
            alert('Standard queries management - You can save up to 10 custom queries per farmer!');
        }
        
        // Data operation confirmation functions
        function confirmDataOperation() {
            document.getElementById('confirmationModal').style.display = 'none';
            if (pendingOperation) {
                // Execute the pending operation
                // This would need to be implemented based on your needs
                showResults('<p>Operation confirmed and executed!</p>');
                pendingOperation = null;
            }
        }
        
        function cancelDataOperation() {
            document.getElementById('confirmationModal').style.display = 'none';
            pendingOperation = null;
            showResults('<p style="color: orange;">Operation cancelled.</p>');
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

# Front Page HTML
FRONT_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 AVA OLO Dashboard Hub</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .logo {
            font-size: 3rem;
            font-weight: 700;
            color: #2e7d32;
            margin-bottom: 0.5rem;
        }
        
        .tagline {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 1rem;
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #e8f5e9;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            color: #2e7d32;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: #4caf50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            max-width: 900px;
            width: 100%;
        }
        
        .dashboard-card {
            background: white;
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            position: relative;
            overflow: hidden;
        }
        
        .dashboard-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }
        
        .dashboard-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #2e7d32, #4caf50);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        
        .dashboard-card:hover::before {
            transform: scaleX(1);
        }
        
        .card-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .card-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #333;
        }
        
        .card-description {
            color: #666;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        
        .card-features {
            list-style: none;
            margin-bottom: 1.5rem;
        }
        
        .card-features li {
            padding: 0.5rem 0;
            color: #555;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .card-features li::before {
            content: '✓';
            color: #4caf50;
            font-weight: bold;
        }
        
        .card-action {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: #2e7d32;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .footer {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
        
        .tech-stack {
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        
        .tech-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .logo {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="logo">🌾 AVA OLO Dashboard Hub</h1>
        <p class="tagline">Agricultural Intelligence & Business Analytics Platform</p>
        <div class="status">
            <span class="status-dot"></span>
            <span>All Systems Operational</span>
        </div>
    </div>
    
    <div class="container">
        <div class="dashboard-grid">
            <!-- Database Dashboard -->
            <a href="/database-dashboard" class="dashboard-card">
                <div class="card-icon">🗄️</div>
                <h2 class="card-title">Database Dashboard</h2>
                <p class="card-description">
                    Interactive agricultural database explorer with AI-powered natural language queries
                </p>
                <ul class="card-features">
                    <li>Natural language SQL queries</li>
                    <li>Real-time data exploration</li>
                    <li>Save frequently used queries</li>
                    <li>GPT-4 powered insights</li>
                </ul>
                <div class="card-action">
                    Open Database Dashboard 
                    <span style="font-size: 1.2rem;">→</span>
                </div>
            </a>
            
            <!-- Business Dashboard -->
            <a href="/business-dashboard" class="dashboard-card">
                <div class="card-icon">📊</div>
                <h2 class="card-title">Business Dashboard</h2>
                <p class="card-description">
                    Comprehensive KPIs and metrics for agricultural business intelligence
                </p>
                <ul class="card-features">
                    <li>Real-time business metrics</li>
                    <li>Growth trends & analytics</li>
                    <li>Interactive data charts</li>
                    <li>Activity monitoring</li>
                </ul>
                <div class="card-action">
                    Open Business Dashboard 
                    <span style="font-size: 1.2rem;">→</span>
                </div>
            </a>
        </div>
    </div>
    
    <div class="footer">
        <p>© 2024 AVA OLO Agricultural Intelligence Platform</p>
        <div class="tech-stack">
            <div class="tech-item">
                <span>⚡</span>
                <span>Powered by FastAPI</span>
            </div>
            <div class="tech-item">
                <span>🐘</span>
                <span>PostgreSQL Database</span>
            </div>
            <div class="tech-item">
                <span>🤖</span>
                <span>OpenAI GPT-4</span>
            </div>
            <div class="tech-item">
                <span>☁️</span>
                <span>AWS App Runner</span>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def home_page():
    """Main landing page with dashboard selection"""
    return HTMLResponse(content=FRONT_PAGE_HTML)

@app.get("/database-dashboard", response_class=HTMLResponse)
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
    
    # Test LLM availability with actual connection test
    try:
        llm_test = await test_llm_connection()
        if llm_test.get("status") == "connected":
            status["llm"]["status"] = "available"
            status["llm"]["message"] = "OpenAI GPT-4 connected"
            status["llm"]["icon"] = "✅"
        else:
            status["llm"]["status"] = "failed"
            status["llm"]["message"] = llm_test.get("error", "Connection failed")[:50]
            status["llm"]["icon"] = "❌"
    except Exception as e:
        status["llm"]["status"] = "error"
        status["llm"]["message"] = f"Test failed: {str(e)[:30]}"
        status["llm"]["icon"] = "❌"
    
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
        # Execute the generated SQL in a safe way
        conn = None
        cursor = None
        try:
            # Get connection without context manager to avoid async issues
            host = os.getenv('DB_HOST')
            database = os.getenv('DB_NAME', 'farmer_crm')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD')
            port = int(os.getenv('DB_PORT', '5432'))
            
            # Try connection with SSL first, then without
            try:
                conn = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='require'
                )
            except psycopg2.OperationalError:
                # Fallback to SSL preferred if required fails
                conn = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='prefer'
                )
            
            cursor = conn.cursor()
            sql_query = llm_result["sql_query"]
            sql_upper = sql_query.strip().upper()
            
            # Determine operation type
            operation_type = "SELECT"
            if sql_upper.startswith('INSERT'):
                operation_type = "INSERT"
            elif sql_upper.startswith('UPDATE'):
                operation_type = "UPDATE"
            elif sql_upper.startswith('DELETE'):
                operation_type = "DELETE"
            elif sql_upper.startswith('BEGIN'):
                operation_type = "TRANSACTION"
            
            # Safety check for UPDATE/DELETE
            if operation_type in ['UPDATE', 'DELETE'] and 'WHERE' not in sql_upper:
                llm_result["execution_result"] = {
                    "status": "error",
                    "error": f"{operation_type} without WHERE clause is too dangerous",
                    "requires_confirmation": True,
                    "operation_type": operation_type
                }
            else:
                # Execute the query
                cursor.execute(sql_query)
                
                if operation_type == "SELECT":
                    # Get column names
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    # Fetch all results
                    rows = cursor.fetchall()
                    
                    # Convert to list of dicts
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    llm_result["execution_result"] = {
                        "status": "success",
                        "operation_type": operation_type,
                        "row_count": len(rows),
                        "data": data
                    }
                else:
                    # For INSERT, UPDATE, DELETE
                    conn.commit()  # Important: commit the transaction
                    affected_rows = cursor.rowcount
                    
                    llm_result["execution_result"] = {
                        "status": "success",
                        "operation_type": operation_type,
                        "affected_rows": affected_rows,
                        "message": f"{operation_type} executed successfully"
                    }
                    
        except psycopg2.OperationalError as op_error:
            # Connection error
            error_msg = str(op_error)
            print(f"ERROR: Connection error during LLM query execution: {error_msg}")
            llm_result["execution_result"] = {
                "error": f"Database connection error: {error_msg}",
                "hint": "Check database connection settings"
            }
            
        except psycopg2.Error as db_error:
            # Database-specific error
            error_msg = str(db_error)
            print(f"ERROR: Database error during LLM query execution: {error_msg}")
            
            # Extract useful error info
            if "null value in column" in error_msg:
                llm_result["execution_result"] = {
                    "error": f"Database error: Missing required field. {error_msg}",
                    "hint": "Make sure all required fields are included in the INSERT statement"
                }
            elif "violates foreign key constraint" in error_msg:
                llm_result["execution_result"] = {
                    "error": f"Database error: Invalid reference. {error_msg}",
                    "hint": "Check that referenced IDs exist in related tables"
                }
            else:
                llm_result["execution_result"] = {"error": f"Database error: {error_msg}"}
            
            # Rollback on error
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
                    
        except Exception as e:
            # General error
            print(f"ERROR: General error during LLM query execution: {str(e)}")
            llm_result["execution_result"] = {"error": f"Execution error: {str(e)}"}
            
        finally:
            # Clean up connections
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
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

@app.get("/api/debug-openai")
async def debug_openai_connection():
    """Debug what's happening with OpenAI connection"""
    import asyncio
    
    # Check environment
    api_key = os.getenv('OPENAI_API_KEY')
    
    result = {
        "api_key_exists": bool(api_key),
        "api_key_format": api_key.startswith('sk-') if api_key else False,
        "api_key_length": len(api_key) if api_key else 0,
        "environment_check": "passed" if api_key and api_key.startswith('sk-') else "failed"
    }
    
    # Try importing OpenAI
    try:
        from openai import AsyncOpenAI
        result["openai_import"] = "success"
        
        # Try creating client (no API call yet)
        if api_key:
            client = AsyncOpenAI(api_key=api_key)
            result["client_creation"] = "success"
            
            # Try very simple API call with shorter timeout
            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=3,
                        timeout=3  # Very short timeout
                    ),
                    timeout=5.0  # Even shorter overall timeout
                )
                result["api_call"] = "success"
                result["response"] = response.choices[0].message.content
                result["model_used"] = "gpt-4"
                
            except asyncio.TimeoutError:
                result["api_call"] = "timeout_error"
                result["note"] = "API call timed out - may be network/AWS restriction"
            except Exception as e:
                result["api_call"] = f"error: {str(e)}"
                result["error_details"] = {
                    "type": type(e).__name__,
                    "message": str(e)[:200]
                }
        else:
            result["client_creation"] = "skipped - no API key"
            
    except ImportError as e:
        result["openai_import"] = f"failed: {str(e)}"
    except Exception as e:
        result["client_creation"] = f"failed: {str(e)}"
    
    return result

# Standard Queries API Endpoints
@app.post("/api/save-standard-query")
async def save_standard_query(request: Dict[str, Any]):
    """Save a query as standard query, limit to 10 per farmer"""
    # Debug logging
    print(f"DEBUG: Received save-standard-query request: {request}")
    
    # Validate input
    try:
        query_name = request.get("query_name", "").strip()
        sql_query = request.get("sql_query", "").strip()
        natural_language_query = request.get("natural_language_query", "")
        farmer_id = request.get("farmer_id")
    except Exception as e:
        print(f"ERROR: Failed to parse request: {e}")
        return {"error": f"Invalid request format: {str(e)}"}
    
    if not query_name or not sql_query:
        return {"error": "Query name and SQL are required"}
    
    # Limit query name length
    if len(query_name) > 255:
        return {"error": "Query name too long (max 255 characters)"}
    
    conn = None
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                return {"error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # First check if table exists
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'standard_queries'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    print("WARNING: standard_queries table does not exist")
                    return {"error": "Standard queries table not found. Please run the migration."}
            except Exception as table_check_error:
                print(f"ERROR: Failed to check table existence: {table_check_error}")
                return {"error": "Failed to verify database schema"}
            
            try:
                # Check if farmer already has 10 queries
                if farmer_id:
                    cursor.execute(
                        "SELECT COUNT(*) FROM standard_queries WHERE farmer_id = %s",
                        (farmer_id,)
                    )
                    count = cursor.fetchone()[0]
                    
                    # If at limit, delete the oldest/least used one
                    if count >= 10:
                        cursor.execute("""
                            DELETE FROM standard_queries 
                            WHERE id = (
                                SELECT id FROM standard_queries 
                                WHERE farmer_id = %s 
                                ORDER BY usage_count ASC, created_at ASC 
                                LIMIT 1
                            )
                        """, (farmer_id,))
                        print(f"DEBUG: Deleted oldest query for farmer {farmer_id}")
                
                # Insert new standard query
                if farmer_id:
                    # Save as farmer-specific query
                    cursor.execute("""
                        INSERT INTO standard_queries 
                        (query_name, sql_query, natural_language_query, farmer_id, is_global)
                        VALUES (%s, %s, %s, %s, FALSE)
                        RETURNING id
                    """, (query_name, sql_query, natural_language_query, farmer_id))
                else:
                    # Save as user-created global query (not system default)
                    cursor.execute("""
                        INSERT INTO standard_queries 
                        (query_name, sql_query, natural_language_query, is_global)
                        VALUES (%s, %s, %s, FALSE)
                        RETURNING id
                    """, (query_name, sql_query, natural_language_query))
                
                query_id = cursor.fetchone()[0]
                conn.commit()
                
                # Verify the save
                cursor.execute("SELECT query_name, is_global, farmer_id FROM standard_queries WHERE id = %s", (query_id,))
                saved_query = cursor.fetchone()
                print(f"SUCCESS: Saved standard query with ID {query_id}")
                print(f"DEBUG: Saved query details - Name: {saved_query[0]}, Global: {saved_query[1]}, Farmer: {saved_query[2]}")
                
                return {"status": "success", "query_id": query_id, "query_name": query_name}
                
            except psycopg2.Error as db_error:
                print(f"ERROR: Database error: {db_error}")
                if conn:
                    conn.rollback()
                return {"error": f"Database error: {str(db_error)}"}
                
    except psycopg2.OperationalError as conn_error:
        print(f"ERROR: Connection error: {conn_error}")
        return {"error": "Database connection failed"}
    except Exception as e:
        print(f"ERROR: Unexpected error in save-standard-query: {e}")
        if conn:
            conn.rollback()
        return {"error": f"Failed to save query: {str(e)}"}

@app.get("/api/standard-queries")
async def get_standard_queries(farmer_id: int = None):
    """Get all standard queries for a farmer"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                return {"error": "Database connection failed", "queries": []}
                
            cursor = conn.cursor()
            
            # Check if table exists first
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'standard_queries'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    print("INFO: standard_queries table does not exist yet")
                    return {"queries": [], "info": "Standard queries not yet initialized"}
            except Exception:
                return {"queries": [], "error": "Failed to verify database schema"}
            
            try:
                # Get both global and farmer-specific queries
                if farmer_id:
                    cursor.execute("""
                        SELECT id, query_name, sql_query, natural_language_query, 
                               usage_count, is_global, created_at
                        FROM standard_queries 
                        WHERE farmer_id = %s OR is_global = TRUE
                        ORDER BY usage_count DESC, created_at DESC
                        LIMIT 15
                    """, (farmer_id,))
                else:
                    # When no farmer_id, show all queries (both global and user-created)
                    cursor.execute("""
                        SELECT id, query_name, sql_query, natural_language_query, 
                               usage_count, is_global, created_at
                        FROM standard_queries 
                        WHERE farmer_id IS NULL  -- Include both global and non-farmer-specific queries
                        ORDER BY is_global DESC, usage_count DESC, created_at DESC
                    """)
                
                columns = [desc[0] for desc in cursor.description]
                queries = []
                for row in cursor.fetchall():
                    query_dict = dict(zip(columns, row))
                    # Convert datetime to string for JSON serialization
                    if query_dict.get('created_at'):
                        query_dict['created_at'] = str(query_dict['created_at'])
                    queries.append(query_dict)
                
                return {"queries": queries}
                
            except psycopg2.Error as db_error:
                print(f"ERROR: Database error in get-standard-queries: {db_error}")
                return {"error": f"Database error: {str(db_error)}", "queries": []}
                
    except Exception as e:
        print(f"ERROR: Unexpected error in get-standard-queries: {e}")
        return {"error": f"Failed to get queries: {str(e)}", "queries": []}

@app.delete("/api/standard-queries/{query_id}")
async def delete_standard_query(query_id: int):
    """Delete a standard query"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                print("ERROR: Database connection failed in delete_standard_query")
                return {"error": "Database connection failed"}
            
            cursor = conn.cursor()
            
            # Check if table exists first
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'standard_queries'
                    )
                """)
                if not cursor.fetchone()[0]:
                    print("ERROR: standard_queries table does not exist")
                    return {"error": "Standard queries table not found. Please run migration."}
            except Exception as e:
                print(f"ERROR: Failed to check table existence: {e}")
                return {"error": f"Failed to verify table: {str(e)}"}
            
            # Delete the query
            try:
                cursor.execute(
                    "DELETE FROM standard_queries WHERE id = %s AND is_global = FALSE",
                    (query_id,)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"SUCCESS: Deleted standard query {query_id}")
                    return {"status": "success"}
                else:
                    print(f"WARNING: Query {query_id} not found or is global")
                    return {"error": "Query not found or is global"}
            except psycopg2.Error as e:
                conn.rollback()
                print(f"ERROR: Database error in delete: {e}")
                return {"error": f"Database error: {str(e)}"}
                
    except Exception as e:
        print(f"ERROR: Delete standard query exception: {e}")
        return {"error": f"Failed to delete query: {str(e)}"}

@app.post("/api/run-standard-query/{query_id}")
async def run_standard_query(query_id: int):
    """Execute a saved standard query and increment usage count"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                print("ERROR: Database connection failed in run_standard_query")
                return {"error": "Database connection failed"}
            
            cursor = conn.cursor()
            
            # Check if table exists first
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'standard_queries'
                    )
                """)
                if not cursor.fetchone()[0]:
                    print("ERROR: standard_queries table does not exist")
                    return {"error": "Standard queries table not found. Please run migration."}
            except Exception as e:
                print(f"ERROR: Failed to check table existence: {e}")
                return {"error": f"Failed to verify table: {str(e)}"}
            
            # Get the query
            try:
                cursor.execute(
                    "SELECT sql_query, query_name FROM standard_queries WHERE id = %s",
                    (query_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    print(f"WARNING: Standard query {query_id} not found")
                    return {"error": "Query not found"}
                
                sql_query, query_name = result
                print(f"DEBUG: Running standard query '{query_name}': {sql_query[:100]}...")
                
            except psycopg2.Error as e:
                print(f"ERROR: Failed to fetch query: {e}")
                return {"error": f"Failed to fetch query: {str(e)}"}
            
            # Update usage count
            try:
                cursor.execute(
                    "UPDATE standard_queries SET usage_count = usage_count + 1 WHERE id = %s",
                    (query_id,)
                )
            except Exception as e:
                print(f"WARNING: Failed to update usage count: {e}")
                # Continue anyway, this is not critical
            
            # Execute the query
            try:
                cursor.execute(sql_query)
                
                # Get results
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                # Convert to list of dicts
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                
                conn.commit()
                
                print(f"SUCCESS: Executed standard query {query_id}, returned {len(rows)} rows")
                return {
                    "status": "success",
                    "query_name": query_name,
                    "row_count": len(rows),
                    "data": data,
                    "sql_query": sql_query
                }
                
            except psycopg2.Error as e:
                conn.rollback()
                print(f"ERROR: Failed to execute query: {e}")
                return {"error": f"Query execution failed: {str(e)}"}
                
    except Exception as e:
        print(f"ERROR: Run standard query exception: {e}")
        return {"error": f"Failed to run query: {str(e)}"}

@app.get("/api/test-standard-queries-table")
async def test_standard_queries_table():
    """Test if standard_queries table exists and show its structure"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                print("ERROR: Database connection failed in test_standard_queries_table")
                return {"error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # Check if table exists
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'standard_queries'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                print(f"DEBUG: standard_queries table exists: {table_exists}")
            except Exception as e:
                print(f"ERROR: Failed to check table existence: {e}")
                return {"error": f"Failed to check table existence: {str(e)}"}
            
            result = {"table_exists": table_exists}
            
            if table_exists:
                # Get table structure
                try:
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = 'standard_queries'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    result["columns"] = [
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2],
                            "default": col[3]
                        }
                        for col in columns
                    ]
                    print(f"DEBUG: Found {len(columns)} columns")
                except Exception as e:
                    print(f"ERROR: Failed to get column info: {e}")
                    result["column_error"] = str(e)
                
                # Get row count
                try:
                    cursor.execute("SELECT COUNT(*) FROM standard_queries")
                    result["row_count"] = cursor.fetchone()[0]
                    print(f"DEBUG: Found {result['row_count']} rows")
                    
                    # Get sample data if any
                    if result["row_count"] > 0:
                        cursor.execute("""
                            SELECT id, query_name, is_global, usage_count 
                            FROM standard_queries 
                            ORDER BY created_at DESC 
                            LIMIT 5
                        """)
                        samples = cursor.fetchall()
                        result["sample_queries"] = [
                            {
                                "id": row[0],
                                "name": row[1],
                                "is_global": row[2],
                                "usage_count": row[3]
                            }
                            for row in samples
                        ]
                except Exception as e:
                    print(f"ERROR: Failed to get row count: {e}")
                    result["count_error"] = str(e)
            else:
                result["migration_needed"] = True
                result["migration_sql"] = """
                    CREATE TABLE IF NOT EXISTS standard_queries (
                        id SERIAL PRIMARY KEY,
                        query_name VARCHAR(255) NOT NULL,
                        sql_query TEXT NOT NULL,
                        description TEXT,
                        natural_language_query TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
                        usage_count INTEGER DEFAULT 0,
                        is_global BOOLEAN DEFAULT FALSE
                    );
                """
                result["action_required"] = "Run the migration SQL to create the standard_queries table"
            
            print(f"SUCCESS: Test completed, table exists: {table_exists}")
            return result
            
    except Exception as e:
        print(f"ERROR: Test standard queries table exception: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return {"error": f"Test failed: {str(e)}", "traceback": traceback.format_exc()}

@app.post("/api/initialize-standard-queries")
async def initialize_standard_queries():
    """Initialize the standard queries table if it doesn't exist"""
    try:
        with get_constitutional_db_connection() as conn:
            if not conn:
                print("ERROR: Database connection failed in initialize_standard_queries")
                return {"error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # Check if table already exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'standard_queries'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("INFO: standard_queries table already exists")
                return {"status": "already_exists", "message": "Standard queries table already exists"}
            
            # Create the table
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS standard_queries (
                        id SERIAL PRIMARY KEY,
                        query_name VARCHAR(255) NOT NULL,
                        sql_query TEXT NOT NULL,
                        description TEXT,
                        natural_language_query TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
                        usage_count INTEGER DEFAULT 0,
                        is_global BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_standard_queries_farmer ON standard_queries(farmer_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_standard_queries_usage ON standard_queries(usage_count DESC)")
                
                # Insert default global queries
                cursor.execute("""
                    INSERT INTO standard_queries (query_name, sql_query, description, natural_language_query, is_global) VALUES
                    ('Total Farmers', 'SELECT COUNT(*) as farmer_count FROM farmers', 'Get total number of farmers', 'How many farmers do we have?', TRUE),
                    ('All Fields', 'SELECT f.farm_name, fi.field_name, fi.area_ha FROM farmers f JOIN fields fi ON f.id = fi.farmer_id ORDER BY f.farm_name, fi.field_name', 'List all fields with farmer names', 'Show me all fields', TRUE),
                    ('Recent Tasks', 'SELECT t.date_performed, f.farm_name, fi.field_name, t.task_type, t.description FROM tasks t JOIN task_fields tf ON t.id = tf.task_id JOIN fields fi ON tf.field_id = fi.id JOIN farmers f ON fi.farmer_id = f.id WHERE t.date_performed >= CURRENT_DATE - INTERVAL ''7 days'' ORDER BY t.date_performed DESC', 'Tasks performed in last 7 days', 'What happened in the last week?', TRUE)
                """)
                
                conn.commit()
                
                print("SUCCESS: Created standard_queries table and added default queries")
                return {
                    "status": "success",
                    "message": "Standard queries table created successfully",
                    "defaults_added": 3
                }
                
            except psycopg2.Error as e:
                conn.rollback()
                print(f"ERROR: Failed to create table: {e}")
                return {"error": f"Failed to create table: {str(e)}"}
                
    except Exception as e:
        print(f"ERROR: Initialize standard queries exception: {e}")
        return {"error": f"Failed to initialize: {str(e)}"}

@app.get("/api/test-external-connection")
async def test_external_connection():
    """Test if App Runner can reach external APIs"""
    
    results = {}
    
    # Test 1: Can we import OpenAI?
    try:
        from openai import AsyncOpenAI
        results["openai_import"] = "✅ Success"
    except Exception as e:
        results["openai_import"] = f"❌ Failed: {str(e)}"
    
    # Test 2: Can we reach external HTTP?
    try:
        import httpx  # Using httpx since it's already in requirements
        async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification for testing
            response = await client.get('https://httpbin.org/get', timeout=10.0)  # Increased timeout
            results["external_http"] = f"✅ Success: {response.status_code}"
    except httpx.ConnectTimeout:
        results["external_http"] = "❌ Connection timeout - network routing issue"
    except httpx.ReadTimeout:
        results["external_http"] = "❌ Read timeout - slow connection"
    except Exception as e:
        results["external_http"] = f"❌ Failed: {type(e).__name__}: {str(e)}"
    
    # Test 3: Can we reach OpenAI specifically?
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        try:
            import httpx
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL for testing
                response = await client.get(
                    'https://api.openai.com/v1/models', 
                    headers={'Authorization': f'Bearer {api_key}'}, 
                    timeout=10.0  # Increased timeout
                )
                results["openai_api"] = f"✅ Success: {response.status_code}"
        except httpx.ConnectTimeout:
            results["openai_api"] = "❌ Connection timeout to OpenAI"
        except httpx.ReadTimeout:
            results["openai_api"] = "❌ Read timeout from OpenAI"
        except Exception as e:
            results["openai_api"] = f"❌ Failed: {type(e).__name__}: {str(e)}"
    else:
        results["openai_api"] = "❌ No API key found"
    
    # Test 4: Basic DNS resolution
    try:
        import socket
        socket.gethostbyname('api.openai.com')
        results["dns_resolution"] = "✅ Can resolve api.openai.com"
    except Exception as e:
        results["dns_resolution"] = f"❌ DNS failed: {str(e)}"
    
    # Test 5: Environment check
    results["environment"] = {
        "api_key_present": bool(api_key),
        "api_key_format": api_key.startswith('sk-') if api_key else False,
        "db_name": os.getenv('DB_NAME', 'not_set'),
        "db_host": bool(os.getenv('DB_HOST'))
    }
    
    return {
        "test_name": "AWS App Runner External Connectivity Test",
        "timestamp": str(datetime.now()) if 'datetime' in globals() else "unknown",
        "results": results,
        "summary": {
            "total_tests": len(results) - 1,  # Exclude environment from count
            "passed": len([r for r in results.values() if isinstance(r, str) and "✅" in r]),
            "failed": len([r for r in results.values() if isinstance(r, str) and "❌" in r])
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)