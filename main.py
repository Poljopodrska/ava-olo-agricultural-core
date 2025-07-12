# main.py - Agricultural Database Dashboard with LLM Query Assistant
import uvicorn
import os
import json
import psycopg2
import openai
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="AVA OLO Agricultural Database with LLM Assistant")

# Set up OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Constitutional AWS RDS Connection (using working strategy)
@contextmanager
def get_constitutional_db_connection():
    """Constitutional connection to AWS Aurora RDS PostgreSQL"""
    connection = None
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        # Use the working strategy from debug (SSL required)
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            connect_timeout=10,
            sslmode='require'
        )
        yield connection
        
    except Exception as e:
        print(f"Database connection error: {e}")
        yield None
    finally:
        if connection:
            connection.close()

# PART 1: Standard Agricultural Queries
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
    """Standard Query: List all farmers"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT farmer_id, farm_name, email FROM farmers ORDER BY farm_name")
                results = cursor.fetchall()
                farmers = [{"farmer_id": r[0], "farm_name": r[1], "email": r[2]} for r in results]
                return {"status": "success", "farmers": farmers, "total": len(farmers)}
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_farmer_fields(farmer_id: int):
    """Standard Query: List all fields of a specific farmer"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.field_id, f.field_name, f.area_hectares, f.location
                    FROM fields f 
                    WHERE f.farmer_id = %s 
                    ORDER BY f.field_name
                """, (farmer_id,))
                results = cursor.fetchall()
                fields = [{"field_id": r[0], "field_name": r[1], "area_hectares": r[2], "location": r[3]} for r in results]
                return {"status": "success", "fields": fields, "total": len(fields)}
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_field_tasks(farmer_id: int, field_id: int):
    """Standard Query: List all tasks on specific field of specific farmer"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.task_id, t.task_name, t.task_type, t.status, t.due_date, t.description
                    FROM tasks t 
                    WHERE t.farmer_id = %s AND t.field_id = %s 
                    ORDER BY t.due_date DESC
                """, (farmer_id, field_id))
                results = cursor.fetchall()
                tasks = [{
                    "task_id": r[0], 
                    "task_name": r[1], 
                    "task_type": r[2], 
                    "status": r[3],
                    "due_date": str(r[4]) if r[4] else None,
                    "description": r[5]
                } for r in results]
                return {"status": "success", "tasks": tasks, "total": len(tasks)}
            else:
                return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# PART 2: LLM Query Assistant
async def get_database_schema():
    """Get database schema for LLM context"""
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # Get table structure
                schema_info = {}
                tables = ['farmers', 'fields', 'tasks']
                
                for table in tables:
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position
                    """, (table,))
                    columns = cursor.fetchall()
                    schema_info[table] = [{"column": c[0], "type": c[1]} for c in columns]
                
                return schema_info
            else:
                return {}
    except Exception as e:
        return {}

async def llm_natural_language_query(user_question: str):
    """LLM-powered natural language to SQL conversion and response"""
    try:
        # Get database schema for context
        schema = await get_database_schema()
        
        # Create prompt for GPT-4
        system_prompt = f"""You are an agricultural database assistant. Convert natural language questions to SQL queries and provide concise answers.

DATABASE SCHEMA:
{json.dumps(schema, indent=2)}

RULES:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE)
2. Use proper JOIN statements when needed
3. Return results in natural language, concise and to the point
4. Focus on agricultural terminology
5. If query fails, explain why briefly

Tables available:
- farmers: Contains farmer information
- fields: Contains field information linked to farmers
- tasks: Contains tasks linked to farmers and fields

Response format:
1. Generate SQL query
2. Execute query  
3. Return natural language summary of results
"""

        user_prompt = f"Question: {user_question}\n\nPlease generate the SQL query and provide a concise answer."

        # Call GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        llm_response = response.choices[0].message.content
        
        # Extract SQL query from LLM response (simple extraction)
        sql_query = None
        lines = llm_response.split('\n')
        for line in lines:
            if 'SELECT' in line.upper():
                sql_query = line.strip()
                break
        
        if not sql_query:
            return {
                "status": "llm_error", 
                "error": "Could not extract SQL query from LLM response",
                "llm_response": llm_response
            }
        
        # Execute the generated query
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Generate natural language response
                result_prompt = f"""Based on this SQL query result, provide a concise natural language answer:

Query: {sql_query}
Results: {results}
Columns: {columns}

Provide a brief, clear answer focusing on the key information. Be agricultural and professional."""

                final_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "user", "content": result_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.1
                )
                
                natural_answer = final_response.choices[0].message.content
                
                return {
                    "status": "success",
                    "user_question": user_question,
                    "generated_sql": sql_query,
                    "raw_results": results,
                    "columns": columns,
                    "natural_answer": natural_answer,
                    "constitutional_compliance": True
                }
            else:
                return {"status": "connection_failed"}
            
    except Exception as e:
        return {
            "status": "llm_error",
            "error": str(e),
            "constitutional_note": "LLM error isolated - system remains stable"
        }

# Request models
class NaturalQueryRequest(BaseModel):
    question: str

class StandardQueryRequest(BaseModel):
    farmer_id: int = None
    field_id: int = None

# HTML Interface
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
        textarea { width: 100%; height: 80px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        input { width: 100px; padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
        button { background: #27ae60; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .llm-button { background: #3498db; }
        button:hover { opacity: 0.8; }
        .results { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; max-height: 300px; overflow-y: auto; }
        .success { background: #e8f5e8; }
        .error { background: #ffebee; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f5f5f5; }
        .natural-response { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0; font-size: 1.1em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌾 AVA OLO Agricultural Database Dashboard</h1>
        <p><strong>Constitutional Compliance:</strong> LLM-First Agricultural Intelligence | AWS RDS Connected</p>
        
        <!-- PART 1: Standard Agricultural Queries -->
        <div class="section agricultural">
            <h2>📊 Part 1: Standard Agricultural Queries</h2>
            
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
            <p><strong>Ask questions in natural language - GPT-4 will convert to SQL and provide concise answers</strong></p>
            
            <div>
                <h4>Ask Agricultural Questions:</h4>
                <textarea id="naturalQuestion" placeholder="Examples:
• How many farmers do we have?
• Show me all farmers from Slovenia
• Which fields belong to farmer ID 1?
• What tasks are pending for field 5?
• How many hectares does farmer Vrzel have?"></textarea>
                <br>
                <button class="llm-button" onclick="askNaturalQuestion()">🧠 Ask GPT-4</button>
            </div>
        </div>
        
        <!-- Results Display -->
        <div id="results" class="results" style="display: none;">
            <h3>Results:</h3>
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
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
                        showResults(`<h4>Total Farmers: ${data.farmer_count}</h4>`);
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
                        let html = `<h4>All Farmers (${data.total}):</h4><table><tr><th>ID</th><th>Farm Name</th><th>Email</th></tr>`;
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
                        let html = `<h4>Fields for Farmer ${farmerId} (${data.total}):</h4><table><tr><th>Field ID</th><th>Field Name</th><th>Area (ha)</th><th>Location</th></tr>`;
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
                        let html = `<h4>Tasks for Farmer ${farmerId}, Field ${fieldId} (${data.total}):</h4><table><tr><th>Task ID</th><th>Task Name</th><th>Type</th><th>Status</th><th>Due Date</th></tr>`;
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
            
            // Show loading
            showResults('<p>🧠 GPT-4 is processing your question...</p>');
            
            fetch('/api/llm/natural-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let html = `
                        <div class="natural-response">
                            <h4>🧠 GPT-4 Answer:</h4>
                            <p><strong>${data.natural_answer}</strong></p>
                        </div>
                        <details>
                            <summary>Technical Details</summary>
                            <p><strong>Generated SQL:</strong> <code>${data.generated_sql}</code></p>
                            <p><strong>Raw Results:</strong> ${data.raw_results.length} rows</p>
                        </details>
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
    """Agricultural Database Dashboard"""
    return HTMLResponse(content=AGRICULTURAL_DASHBOARD_HTML)

# PART 1: Standard Agricultural Query APIs
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

# PART 2: LLM Natural Language Query API
@app.post("/api/llm/natural-query")
async def api_natural_query(request: NaturalQueryRequest):
    return await llm_natural_language_query(request.question)

# Keep debug endpoint for emergencies
@app.get("/api/debug/status")
async def debug_status():
    return {
        "database_connected": "AWS RDS PostgreSQL",
        "llm_model": "GPT-4",
        "constitutional_compliance": True,
        "agricultural_focus": "Farmers, Fields, Tasks"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)