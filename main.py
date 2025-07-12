# main.py - Safe Agricultural Dashboard with Optional LLM
import uvicorn
import os
import json
import psycopg2
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Constitutional Error Isolation - Import OpenAI safely
try:
    import openai
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_AVAILABLE = bool(OPENAI_API_KEY and len(OPENAI_API_KEY) > 10)
    if OPENAI_AVAILABLE:
        openai.api_key = OPENAI_API_KEY
        print(f"DEBUG: OpenAI configured with key: {OPENAI_API_KEY[:10]}...")
    else:
        print(f"DEBUG: OpenAI key issue - Key present: {bool(OPENAI_API_KEY)}, Length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")
except ImportError as import_error:
    OPENAI_AVAILABLE = False
    print(f"DEBUG: OpenAI import failed: {import_error}")
except Exception as config_error:
    OPENAI_AVAILABLE = False
    print(f"DEBUG: OpenAI config failed: {config_error}")

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
    """Standard Query: List all farmers - USE SAME LOGIC AS COUNT FARMERS"""
    try:
        # Use the SAME connection logic that works for Count Farmers
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT farmer_id, farm_name, email FROM farmers ORDER BY farm_name LIMIT 20")
                results = cursor.fetchall()
                cursor.close()
                
                farmers = []
                for r in results:
                    farmers.append({
                        "farmer_id": r[0], 
                        "farm_name": r[1] if r[1] else "N/A", 
                        "email": r[2] if r[2] else "N/A"
                    })
                
                return {"status": "success", "farmers": farmers, "total": len(farmers)}
            else:
                return {"status": "connection_failed", "error": "No database connection"}
    except Exception as e:
        return {"status": "error", "error": f"Same logic as Count Farmers: {str(e)}"}

async def get_farmer_fields(farmer_id: int):
    """Standard Query: List all fields of a specific farmer - FIXED VERSION"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # Try full query first, then fallback
                try:
                    cursor.execute("""
                        SELECT field_id, field_name, area_hectares, location
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
                            "area_hectares": r[2] if len(r) > 2 and r[2] else "N/A",
                            "location": r[3] if len(r) > 3 and r[3] else "N/A"
                        })
                    
                except psycopg2.Error as schema_error:
                    # Fallback query with minimal columns
                    cursor.execute("""
                        SELECT field_id, field_name 
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
                            "area_hectares": "N/A",
                            "location": "N/A"
                        })
                
                return {"status": "success", "fields": fields, "total": len(fields)}
            else:
                return {"status": "connection_failed", "error": "No database connection"}
    except Exception as e:
        return {"status": "error", "error": f"Database query failed: {str(e)}"}

async def get_field_tasks(farmer_id: int, field_id: int):
    """Standard Query: List all tasks on specific field of specific farmer - FIXED VERSION"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        SELECT task_id, task_name, task_type, status, due_date, description
                        FROM tasks 
                        WHERE farmer_id = %s AND field_id = %s 
                        ORDER BY due_date DESC
                        LIMIT 20
                    """, (farmer_id, field_id))
                    results = cursor.fetchall()
                    cursor.close()
                    
                    tasks = []
                    for r in results:
                        tasks.append({
                            "task_id": r[0],
                            "task_name": r[1] if r[1] else "N/A",
                            "task_type": r[2] if len(r) > 2 and r[2] else "N/A",
                            "status": r[3] if len(r) > 3 and r[3] else "N/A",
                            "due_date": str(r[4]) if len(r) > 4 and r[4] else None,
                            "description": r[5] if len(r) > 5 and r[5] else "N/A"
                        })
                    
                except psycopg2.Error as schema_error:
                    # Fallback query with minimal columns
                    cursor.execute("""
                        SELECT task_id, task_name 
                        FROM tasks 
                        WHERE farmer_id = %s AND field_id = %s 
                        LIMIT 20
                    """, (farmer_id, field_id))
                    results = cursor.fetchall()
                    cursor.close()
                    
                    tasks = []
                    for r in results:
                        tasks.append({
                            "task_id": r[0],
                            "task_name": r[1] if r[1] else "N/A",
                            "task_type": "N/A",
                            "status": "N/A",
                            "due_date": None,
                            "description": "N/A"
                        })
                
                return {"status": "success", "tasks": tasks, "total": len(tasks)}
            else:
                return {"status": "connection_failed", "error": "No database connection"}
    except Exception as e:
        return {"status": "error", "error": f"Database query failed: {str(e)}"}

# PART 2: LLM Query Assistant (SAFE VERSION)
async def llm_natural_language_query(user_question: str):
    """LLM-powered natural language query with constitutional safety"""
    if not OPENAI_AVAILABLE:
        return {
            "status": "llm_unavailable",
            "error": "OpenAI API key not configured",
            "fallback_message": "LLM features require OPENAI_API_KEY environment variable. Standard queries still work.",
            "constitutional_note": "Error isolation - system remains operational"
        }
    
    try:
        # Simple LLM implementation for now
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an agricultural database assistant. Convert questions to simple SQL SELECT queries for farmers, fields, and tasks tables."},
                {"role": "user", "content": f"Convert to SQL: {user_question}"}
            ],
            max_tokens=100,
            temperature=0
        )
        
        sql_suggestion = response.choices[0].message.content.strip()
        
        return {
            "status": "llm_success",
            "user_question": user_question,
            "sql_suggestion": sql_suggestion,
            "note": "LLM query generation active - execute manually in database interface"
        }
        
    except Exception as e:
        return {
            "status": "llm_error",
            "error": str(e),
            "constitutional_note": "LLM error isolated - standard queries still work"
        }

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
        <div class="section warning">
            <h3>🔍 System Status</h3>
            <p id="systemStatus">Loading system status...</p>
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
                    <input type="number" id="farmerId" placeholder="Farmer ID">
                    <button onclick="getFarmerFields()">Get Fields</button>
                </div>
                
                <div>
                    <h4>Field Tasks</h4>
                    <input type="number" id="taskFarmerId" placeholder="Farmer ID">
                    <input type="number" id="fieldId" placeholder="Field ID">
                    <button onclick="getFieldTasks()">Get Tasks</button>
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
                        let html = `<h4>🌾 All Farmers (${data.total}):</h4><table><tr><th>ID</th><th>Farm Name</th><th>Email</th></tr>`;
                        data.farmers.forEach(farmer => {
                            html += `<tr><td>${farmer.farmer_id}</td><td>${farmer.farm_name}</td><td>${farmer.email}</td></tr>`;
                        });
                        html += '</table>';
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
                        let html = `<h4>🌾 Fields for Farmer ${farmerId} (${data.total}):</h4><table><tr><th>Field ID</th><th>Field Name</th><th>Area (ha)</th><th>Location</th></tr>`;
                        data.fields.forEach(field => {
                            html += `<tr><td>${field.field_id}</td><td>${field.field_name}</td><td>${field.area_hectares}</td><td>${field.location}</td></tr>`;
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
                        let html = `<h4>🌾 Tasks for Farmer ${farmerId}, Field ${fieldId} (${data.total}):</h4><table><tr><th>Task ID</th><th>Task Name</th><th>Type</th><th>Status</th><th>Due Date</th></tr>`;
                        data.tasks.forEach(task => {
                            html += `<tr><td>${task.task_id}</td><td>${task.task_name}</td><td>${task.task_type}</td><td>${task.status}</td><td>${task.due_date || 'N/A'}</td></tr>`;
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
            
            fetch('/api/llm/natural-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'llm_success') {
                    let html = `
                        <h4>🧠 LLM SQL Suggestion:</h4>
                        <p><strong>Question:</strong> ${data.user_question}</p>
                        <p><strong>Suggested SQL:</strong> <code>${data.sql_suggestion}</code></p>
                        <p><em>${data.note}</em></p>
                    `;
                    showResults(html);
                } else {
                    showResults(data, false);
                }
            });
        }
    </script>
</body>
</html>
"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def agricultural_dashboard():
    """Agricultural Database Dashboard - Safe Version"""
    return HTMLResponse(content=AGRICULTURAL_DASHBOARD_HTML)

# PART 1: Standard Agricultural Query APIs (ALWAYS WORK)
@app.get("/api/agricultural/farmer-count")
async def api_farmer_count():
    return await get_farmer_count()

@app.get("/api/agricultural/farmers")
async def api_all_farmers():
    return await get_all_farmers()

@app.get("/api/agricultural/farmer-fields/{farmer_id}")
async def api_farmer_fields(farmer_id: int):
    return await get_farmer_fields(farmer_id)

@app.get("/api/agricultural/field-tasks/{farmer_id}/{field_id}")
async def api_field_tasks(farmer_id: int, field_id: int):
    return await get_field_tasks(farmer_id, field_id)

# PART 2: LLM Natural Language Query API (SAFE VERSION)
@app.post("/api/llm/natural-query")
async def api_natural_query(request: NaturalQueryRequest):
    return await llm_natural_language_query(request.question)

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)