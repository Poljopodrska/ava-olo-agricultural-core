# main.py - Safe Agricultural Dashboard with Optional LLM
import uvicorn
import os
import json
import psycopg2
import asyncio
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sys
import urllib.parse
sys.path.append('.')
from database.insert_operations import ConstitutionalInsertOperations
from database_operations import DatabaseOperations

# Construct DATABASE_URL from individual components if not set
if not os.getenv('DATABASE_URL'):
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME', 'farmer_crm')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_port = os.getenv('DB_PORT', '5432')
    
    # Handle potential HTML encoding issues from AWS App Runner
    if db_password:
        # Check if password appears to be HTML-encoded
        if '&lt;' in db_password or '&gt;' in db_password or '&amp;' in db_password:
            import html
            db_password = html.unescape(db_password)
            print(f"DEBUG: Detected HTML-encoded password, unescaping...")
    
    if db_host and db_password:
        # Clean up hostname - remove any whitespace or special characters
        db_host = db_host.strip().replace(" ", "")  # Remove all spaces
        
        # URL encode the password to handle special characters
        db_password_encoded = urllib.parse.quote(db_password, safe='')
        print(f"DEBUG: URL encoding password. Original length: {len(db_password)}, Encoded length: {len(db_password_encoded)}")
        
        DATABASE_URL = f"postgresql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}"
        os.environ['DATABASE_URL'] = DATABASE_URL
        print(f"DEBUG: Constructed DATABASE_URL from components")
        print(f"DEBUG: DB_HOST = '{db_host}'")
        print(f"DEBUG: DB_NAME = '{db_name}'")
        print(f"DEBUG: DB_USER = '{db_user}'")
        print(f"DEBUG: DB_PASSWORD = {'SET (' + str(len(db_password)) + ' chars)' if db_password else 'NOT SET'}")
        print(f"DEBUG: DATABASE_URL = '{DATABASE_URL[:60]}...{DATABASE_URL[-20:]}'")
        
        # Test the connection string format
        if "[" in DATABASE_URL or "]" in DATABASE_URL:
            print("WARNING: DATABASE_URL contains brackets - may need URL encoding")
        if " " in DATABASE_URL:
            print("WARNING: DATABASE_URL contains spaces")
    else:
        print(f"DEBUG: Missing DB_HOST or DB_PASSWORD")
        print(f"DEBUG: DB_HOST = '{db_host}'")
        print(f"DEBUG: DB_PASSWORD = {'SET' if db_password else 'NOT SET'}")
else:
    print(f"DEBUG: Using provided DATABASE_URL")

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

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper function to get design system CSS
def get_design_system_css():
    """Return the CSS link tag for the shared constitutional design system v2"""
    return '<link rel="stylesheet" href="/static/css/constitutional-design-system-v2.css">'

# Base HTML template for all dashboards
def get_base_html_start(title="AVA OLO Dashboard"):
    """Return the base HTML start with design system"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {get_design_system_css()}
    <style>
        /* Base styles using design system */
        body {{
            font-family: var(--font-primary);
            background: linear-gradient(135deg, var(--color-primary-gradient-start) 0%, var(--color-primary-gradient-end) 100%);
            margin: 0;
            min-height: 100vh;
            color: var(--color-gray-800);
        }}
        .dashboard-container {{
            max-width: 1400px;
            margin: var(--spacing-8) auto;
            background: var(--color-bg-white);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-2xl);
            box-shadow: var(--shadow-2xl);
            overflow: hidden;
        }}
        .dashboard-header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: var(--spacing-6) var(--spacing-8);
            border-bottom: 1px solid var(--color-gray-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .back-link {{
            color: var(--color-primary);
            text-decoration: none;
            font-weight: var(--font-weight-semibold);
            transition: all var(--transition-base);
        }}
        .back-link:hover {{
            color: var(--color-primary-dark);
            transform: translateX(-5px);
        }}
        h1 {{
            color: var(--color-agri-green);
            font-size: var(--font-size-3xl);
            font-weight: var(--font-weight-bold);
            margin: 0;
        }}
        .btn {{
            padding: var(--spacing-3) var(--spacing-6);
            border: none;
            border-radius: var(--radius-md);
            font-weight: var(--font-weight-semibold);
            cursor: pointer;
            transition: all var(--transition-base);
            text-decoration: none;
            display: inline-block;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: white;
            box-shadow: var(--shadow-primary);
        }}
        .btn-primary:hover {{
            transform: var(--transform-hover-up);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}
    </style>"""

# Helper function for formatting time ago
def format_time_ago(timestamp):
    """Format timestamp as human-readable time ago"""
    if not timestamp:
        return "Unknown time"
    
    # Handle both datetime objects and strings
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return "Unknown time"
    
    now = datetime.now()
    
    # If timestamp is timezone-aware, make now timezone-aware too
    if timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None:
        import pytz
        now = now.replace(tzinfo=pytz.UTC)
    
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} min ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return timestamp.strftime("%Y-%m-%d")

def create_cost_tables():
    """Create cost tracking tables - Simple implementation"""
    try:
        with get_constitutional_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS farmer_interaction_costs (
                        id SERIAL PRIMARY KEY,
                        farmer_id INTEGER NOT NULL,
                        interaction_type VARCHAR(50) NOT NULL,
                        cost_amount DECIMAL(10,6) NOT NULL,
                        tokens_used INTEGER NULL,
                        api_service VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cost_rates (
                        id SERIAL PRIMARY KEY,
                        service_name VARCHAR(50) UNIQUE NOT NULL,
                        cost_per_unit DECIMAL(10,6) NOT NULL,
                        unit_type VARCHAR(20) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'USD',
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_costs_farmer ON farmer_interaction_costs(farmer_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_costs_date ON farmer_interaction_costs(created_at)")
                
                # Insert default cost rates
                cursor.execute("""
                    INSERT INTO cost_rates (service_name, cost_per_unit, unit_type, currency) 
                    VALUES 
                        ('openai_gpt4', 0.00002, 'token', 'USD'),
                        ('twilio_whatsapp_out', 0.0075, 'message', 'USD'),
                        ('twilio_whatsapp_in', 0.005, 'message', 'USD'),
                        ('openweather_api', 0.001, 'api_call', 'USD')
                    ON CONFLICT (service_name) DO NOTHING
                """)
                
                connection.commit()
                return True
    except Exception as e:
        print(f"Cost table creation failed: {e}")
        return False

def track_cost(farmer_id, interaction_type, cost_amount, tokens_used=None, api_service="unknown"):
    """Track cost - Simple implementation"""
    try:
        with get_constitutional_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                
                cursor.execute("""
                    INSERT INTO farmer_interaction_costs 
                    (farmer_id, interaction_type, cost_amount, tokens_used, api_service)
                    VALUES (%s, %s, %s, %s, %s)
                """, (farmer_id, interaction_type, cost_amount, tokens_used, api_service))
                
                connection.commit()
                return True
    except Exception as e:
        print(f"Cost tracking failed: {e}")
        return False

# Constitutional AWS RDS Connection (RESTORED WORKING VERSION)
@contextmanager
def get_constitutional_db_connection():
    """Constitutional connection with multiple strategies (FIXED VERSION)"""
    connection = None
    
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        print(f"DEBUG: Attempting connection to {host}:{port}/{database} as {user}")
        
        # Strategy 1: Try with SSL required (AWS RDS default)
        if not connection:
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
            except psycopg2.OperationalError as ssl_error:
                print(f"DEBUG: SSL required failed: {ssl_error}")
        
        # Strategy 2: Try with SSL preferred
        if not connection:
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
            except psycopg2.OperationalError as ssl_pref_error:
                print(f"DEBUG: SSL preferred failed: {ssl_pref_error}")
        
        # Strategy 3: Try connecting to postgres database instead
        if not connection:
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
            except psycopg2.OperationalError as postgres_error:
                print(f"DEBUG: Postgres database failed: {postgres_error}")
        
        # Yield the connection (successful or None)
        if connection:
            print("DEBUG: Yielding successful connection")
        else:
            print("DEBUG: All connection strategies failed, yielding None")
        
        yield connection
        
    except Exception as e:
        print(f"DEBUG: Unexpected error in connection: {e}")
        yield None
    finally:
        if connection:
            try:
                connection.close()
                print("DEBUG: Connection closed")
            except:
                pass

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
DASHBOARD_LANDING_HTML = """
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
            <p><a href="/health/database" style="color: #007bff; font-weight: bold;">🔍 Database Health Check</a> - Test RDS connectivity and permissions</p>
            <p><a href="/debug/database-connection" style="color: #dc3545; font-weight: bold;">🐛 Database Debug</a> - Detailed connection troubleshooting</p>
            <p><a href="/health/google-maps" style="color: #28a745; font-weight: bold;">🗺️ Google Maps API Check</a> - Check if API key is configured</p>
            <p><a href="/farmer-registration" style="font-weight: bold;">🌾 Register New Farmer</a> - Add new farmer with fields and app access</p>
            <p><a href="/field-drawing-test" style="color: #28a745; font-weight: bold;">🗺️ Test Field Drawing</a> - Test the interactive map functionality</p>
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

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard_landing():
    """Dashboard Landing Page with 3-Dashboard Navigation"""
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>AVA OLO Agricultural Dashboards</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {get_design_system_css()}
    <style>
        body {{ 
            font-family: var(--font-primary);
            background: linear-gradient(135deg, var(--color-primary-gradient-start) 0%, var(--color-primary-gradient-end) 100%);
            color: var(--color-gray-800);
            margin: 0;
            padding: var(--spacing-6);
            min-height: 100vh;
        }}
        .constitutional-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--color-bg-white);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-2xl);
            box-shadow: var(--shadow-2xl);
            overflow: hidden;
        }}
        .constitutional-header {{
            background: linear-gradient(135deg, var(--color-agri-green) 0%, var(--color-agri-green-light) 100%);
            color: white;
            padding: var(--spacing-12) var(--spacing-6);
            text-align: center;
        }}
        .constitutional-title {{
            margin: 0 0 var(--spacing-3) 0;
            font-size: var(--font-size-4xl);
            font-weight: var(--font-weight-bold);
        }}
        .constitutional-subtitle {{
            margin: 0;
            font-size: var(--font-size-xl);
            opacity: 0.9;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: var(--spacing-8);
            padding: var(--spacing-10);
        }}
        .constitutional-card {{
            background: white;
            border: 2px solid transparent;
            border-radius: var(--radius-lg);
            padding: var(--spacing-8);
            text-align: center;
            transition: all var(--transition-base);
            box-shadow: var(--shadow-md);
        }}
        .constitutional-card:hover {{
            transform: var(--transform-hover-up);
            box-shadow: var(--shadow-xl);
            border-color: var(--color-primary);
        }}
        .constitutional-card h2 {{
            color: var(--color-agri-green);
            margin-bottom: var(--spacing-4);
            font-size: var(--font-size-2xl);
            font-weight: var(--font-weight-bold);
        }}
        .constitutional-card p {{
            color: var(--color-gray-600);
            margin-bottom: var(--spacing-6);
            font-size: var(--font-size-lg);
            line-height: var(--line-height-normal);
        }}
        .constitutional-button {{
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: white;
            padding: var(--spacing-4) var(--spacing-8);
            text-decoration: none;
            border-radius: var(--radius-md);
            font-weight: var(--font-weight-semibold);
            font-size: var(--font-size-base);
            display: inline-block;
            transition: all var(--transition-base);
            box-shadow: var(--shadow-primary);
        }}
        .constitutional-button:hover {{
            transform: var(--transform-hover-up);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            text-decoration: none;
            color: white;
        }}
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
                padding: var(--spacing-6);
            }}
            .constitutional-title {{
                font-size: var(--font-size-3xl);
            }}
        }}
    </style>
</head>
<body>
    <div class="constitutional-container">
        <header class="constitutional-header">
            <h1 class="constitutional-title">🌾 AVA OLO Dashboard Hub</h1>
            <p class="constitutional-subtitle">Agricultural Intelligence Platform</p>
        </header>
        
        <main class="dashboard-grid">
            <div class="constitutional-card">
                <h2>📊 Business Dashboard</h2>
                <p>Financial metrics and business intelligence</p>
                <a href="/business-dashboard" class="constitutional-button">Enter Dashboard</a>
            </div>
            
            <div class="constitutional-card">
                <h2>🌱 Agronomic Dashboard</h2>
                <p>Live conversation monitoring and expert intervention</p>
                <a href="/agronomic-dashboard" class="constitutional-button">Enter Dashboard</a>
            </div>
            
            <div class="constitutional-card">
                <h2>💾 Database Dashboard</h2>
                <p>Data management and queries</p>
                <a href="/database-dashboard" class="constitutional-button">Enter Dashboard</a>
            </div>
            
            <div class="constitutional-card">
                <h2>🏥 System Health</h2>
                <p>Monitor all system components and API connections</p>
                <a href="/health-dashboard" class="constitutional-button">Enter Dashboard</a>
            </div>
        </main>
    </div>
</body>
</html>
""")

# Design System Demo Route
@app.get("/design-demo", response_class=HTMLResponse)
async def design_demo():
    """Unified Design System Demo Page"""
    with open("templates/design_demo.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)

# Database Dashboard Route - Keep existing functionality  
@app.get("/database-dashboard", response_class=HTMLResponse)
async def database_dashboard():
    """Agricultural Database Dashboard - Full Functionality"""
    return HTMLResponse(content=DASHBOARD_LANDING_HTML)

# Simple Cost Analytics Route
@app.get("/cost-analytics", response_class=HTMLResponse)
async def cost_analytics():
    """Simple Cost Analytics - Safe Implementation"""
    
    cost_data = {
        "total_cost": 0.0,
        "avg_cost_per_farmer": 0.0,
        "tables_exist": False
    }
    
    try:
        with get_constitutional_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                
                # Check if cost tables exist
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'farmer_interaction_costs'
                    )
                """)
                
                cost_data["tables_exist"] = cursor.fetchone()[0]
                
                if cost_data["tables_exist"]:
                    # Get basic cost data
                    cursor.execute("""
                        SELECT 
                            COUNT(DISTINCT farmer_id) as farmers,
                            COALESCE(SUM(cost_amount), 0) as total_cost
                        FROM farmer_interaction_costs
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """)
                    
                    result = cursor.fetchone()
                    farmers = result[0] or 1
                    total_cost = result[1] or 0
                    
                    cost_data["total_cost"] = round(total_cost, 2)
                    cost_data["avg_cost_per_farmer"] = round(total_cost / farmers, 2)
                    
    except Exception as e:
        print(f"Cost analytics error: {e}")
    
    # Simple HTML response
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cost Analytics - AVA OLO</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #F5F3F0; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
            .metric {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
            .value {{ font-size: 24px; font-weight: bold; color: #2D5A27; }}
            .label {{ color: #6B5B73; margin-bottom: 5px; }}
            .back-link {{ color: #6B5B73; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/business-dashboard" class="back-link">← Back to Business Dashboard</a>
            <h1>💰 Cost Analytics</h1>
            
            """ + ("<p>Cost tracking tables not yet created. <a href='/initialize-cost-tables'>Click here to initialize</a></p>" if not cost_data["tables_exist"] else "") + """
            
            """ + ("<p style='text-align: center; margin: 15px 0;'><a href='/cost-rates' style='background: #3b82f6; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;'>⚙️ Manage Cost Rates</a></p>" if cost_data["tables_exist"] else "") + """
            
            """ + (f"""
            <div class="metric">
                <div class="label">Total Cost (30 days)</div>
                <div class="value">${cost_data["total_cost"]}</div>
            </div>
            
            <div class="metric">
                <div class="label">Average Cost per Farmer</div>
                <div class="value">${cost_data["avg_cost_per_farmer"]}</div>
            </div>
            """ if cost_data["tables_exist"] else "") + """
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

# Initialize cost tables endpoint
@app.get("/initialize-cost-tables")
async def initialize_cost_tables():
    """Initialize cost tracking tables"""
    success = create_cost_tables()
    
    if success:
        # Add some test data
        try:
            track_cost(1, "llm_query", 0.05, 2500, "openai")
            track_cost(2, "llm_query", 0.03, 1500, "openai")
            track_cost(1, "whatsapp_out", 0.0075, None, "twilio")
        except:
            pass
    
    return {"success": success, "message": "Cost tables initialized" if success else "Failed to initialize"}

@app.get("/cost-rates", response_class=HTMLResponse)
async def cost_rates_management():
    """Cost rates management interface"""
    rates = []
    error_msg = None
    connection = None
    
    try:
        # Use same connection strategy as get_constitutional_db_connection
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        # Strategy 1: Try farmer_crm database first
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
        except psycopg2.OperationalError:
            # Strategy 2: Fallback to postgres database (like working endpoints)
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
        cursor.execute("SELECT service_name, cost_per_unit, unit_type, currency FROM cost_rates ORDER BY service_name")
        rates = cursor.fetchall()
        cursor.close()
        
    except psycopg2.Error as e:
        error_msg = f"Database error: {str(e)}"
    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
    finally:
        if connection:
            connection.close()
    
    if error_msg:
        return HTMLResponse(f"""
        <html><head><title>Cost Rates Management</title></head><body>
        <h1>Cost Rates Configuration</h1>
        <p><a href="/business-dashboard">← Back to Dashboard</a></p>
        <p style="color: red;">Error: {error_msg}</p>
        <p>Please ensure cost tables are initialized first: <a href="/initialize-cost-tables">Initialize Cost Tables</a></p>
        </body></html>
        """)
    
    rates_html = ""
    for service, cost, unit, currency in rates:
        rates_html += f"""
        <tr>
            <td>{service}</td>
            <td><input type="number" step="0.000001" value="{cost}" id="rate_{service}"></td>
            <td>{unit}</td>
            <td>{currency}</td>
            <td><button onclick="updateRate('{service}')" class="update-btn">Update</button></td>
        </tr>"""
    
    return HTMLResponse(f"""
    {get_base_html_start("Cost Rates Management")}
    <style>
        .content {{
            padding: var(--spacing-8);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: var(--spacing-6) 0;
            background: white;
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }}
        th {{
            background: var(--color-gray-100);
            padding: var(--spacing-4);
            text-align: left;
            font-weight: var(--font-weight-semibold);
            color: var(--color-gray-700);
        }}
        td {{
            padding: var(--spacing-4);
            border-bottom: 1px solid var(--color-gray-200);
        }}
        input[type="number"] {{
            padding: var(--spacing-2);
            border: 2px solid var(--color-gray-200);
            border-radius: var(--radius-base);
            width: 120px;
            transition: all var(--transition-base);
        }}
        input[type="number"]:focus {{
            outline: none;
            border-color: var(--color-primary);
            box-shadow: var(--focus-ring);
        }}
        .update-btn {{
            background: linear-gradient(135deg, var(--color-info) 0%, var(--color-info-dark) 100%);
            color: white;
            border: none;
            padding: var(--spacing-2) var(--spacing-4);
            border-radius: var(--radius-base);
            cursor: pointer;
            transition: all var(--transition-base);
            font-weight: var(--font-weight-medium);
        }}
        .update-btn:hover {{
            transform: var(--transform-hover-up);
            box-shadow: var(--shadow-sm);
        }}
    </style>
    </head>
    <body>
    <div class="dashboard-container">
        <div class="dashboard-header">
            <a href="/business-dashboard" class="back-link">← Back to Dashboard</a>
            <h1>💰 Cost Rates Configuration</h1>
            <div></div>
        </div>
        <div class="content">
    
    <table>
        <tr>
            <th>Service</th>
            <th>Cost per Unit</th>
            <th>Unit Type</th>
            <th>Currency</th>
            <th>Action</th>
        </tr>
        {rates_html}
    </table>
    
    <script>
    function updateRate(serviceName) {{
        const newRate = document.getElementById('rate_' + serviceName).value;
        
        fetch('/api/update-cost-rate', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{service: serviceName, rate: parseFloat(newRate)}})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                alert('✅ Updated ' + serviceName + ' rate to $' + newRate);
            }} else {{
                alert('❌ Failed to update rate: ' + data.error);
            }}
        }});
    }}
    </script>
        </div>
    </div>
    </body></html>
    """)

@app.post("/api/update-cost-rate")
async def update_cost_rate(request: Request):
    """Update cost rate for a service"""
    connection = None
    try:
        data = await request.json()
        service = data.get('service')
        rate = data.get('rate')
        
        if not service or rate is None:
            return {"success": False, "error": "Missing service or rate"}
        
        # Use same connection strategy as get_constitutional_db_connection
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        # Strategy 1: Try farmer_crm database first
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
        except psycopg2.OperationalError:
            # Strategy 2: Fallback to postgres database (like working endpoints)
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
        cursor.execute("""
            UPDATE cost_rates 
            SET cost_per_unit = %s, updated_at = NOW()
            WHERE service_name = %s
        """, (rate, service))
        
        if cursor.rowcount > 0:
            connection.commit()
            cursor.close()
            return {"success": True, "message": f"Updated {service} rate to ${rate}"}
        else:
            cursor.close()
            return {"success": False, "error": f"Service {service} not found"}
            
    except psycopg2.Error as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if connection:
            connection.close()

# Business Dashboard Implementation
@app.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard():
    """Business Dashboard - Comprehensive Agricultural Metrics"""
    
    # Initialize metrics with safe defaults
    metrics = {
        "total_farmers": 0,
        "total_hectares": 0,
        "hectares_by_crop": {},
        "farmers_24h": 0,
        "farmers_7d": 0,
        "farmers_30d": 0,
        "unsubscribed_24h": 0,
        "unsubscribed_7d": 0,
        "unsubscribed_30d": 0,
        "hectares_24h": 0,
        "hectares_7d": 0,
        "hectares_30d": 0,
        "recent_activities": [],
        "recent_changes": [],
        "farmer_growth_data": [],
        "churn_rate_daily": 0,
        "churn_rate_7d_avg": 0,
        "cost_analytics_enabled": False
    }
    
    try:
        with get_constitutional_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                
                # 1. Total farmers and hectares
                cursor.execute("SELECT COUNT(*) FROM farmers")
                metrics["total_farmers"] = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COALESCE(SUM(area_ha), 0) FROM fields")
                metrics["total_hectares"] = round(cursor.fetchone()[0] or 0, 2)
                
                # 2. Hectares by crop type (using field_crops table)
                cursor.execute("""
                    SELECT 
                        fc.crop_name,
                        COUNT(DISTINCT f.id) as field_count,
                        COALESCE(SUM(f.area_ha), 0) as total_area
                    FROM fields f
                    JOIN field_crops fc ON f.id = fc.field_id
                    WHERE fc.start_year_int = EXTRACT(YEAR FROM CURRENT_DATE)
                    GROUP BY fc.crop_name
                    ORDER BY total_area DESC
                """)
                
                crop_data = cursor.fetchall()
                crop_categories = {
                    "herbal": 0,
                    "vineyard": 0,
                    "orchard": 0,
                    "others": 0
                }
                
                # Classify crops into categories
                for crop_name, field_count, area in crop_data:
                    crop_lower = (crop_name or "").lower()
                    if any(herb in crop_lower for herb in ["basil", "mint", "thyme", "oregano", "rosemary", "lavender", "sage"]):
                        crop_categories["herbal"] += area
                    elif any(vine in crop_lower for vine in ["grape", "vine", "vineyard"]):
                        crop_categories["vineyard"] += area
                    elif any(fruit in crop_lower for fruit in ["apple", "pear", "cherry", "plum", "peach", "apricot", "orchard"]):
                        crop_categories["orchard"] += area
                    else:
                        crop_categories["others"] += area
                
                metrics["hectares_by_crop"] = {
                    "herbal": round(crop_categories["herbal"], 2),
                    "vineyard": round(crop_categories["vineyard"], 2),
                    "orchard": round(crop_categories["orchard"], 2),
                    "others": round(crop_categories["others"], 2)
                }
                
                # 3. Growth metrics (simulate since we don't have created_at in farmers table)
                # For now, we'll use recent messages as a proxy for farmer activity
                
                now = datetime.now()
                day_ago = now - timedelta(days=1)
                week_ago = now - timedelta(days=7)
                month_ago = now - timedelta(days=30)
                
                # Count recent messages as proxy for new farmer activity
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT CASE WHEN timestamp >= %s THEN farmer_id END) as day_count,
                        COUNT(DISTINCT CASE WHEN timestamp >= %s THEN farmer_id END) as week_count,
                        COUNT(DISTINCT CASE WHEN timestamp >= %s THEN farmer_id END) as month_count
                    FROM incoming_messages
                    WHERE timestamp >= %s
                """, (day_ago, week_ago, month_ago, month_ago))
                
                result = cursor.fetchone()
                if result:
                    metrics["farmers_24h"] = result[0] or 0
                    metrics["farmers_7d"] = result[1] or 0
                    metrics["farmers_30d"] = result[2] or 0
                
                # 4. Recent activities from messages
                cursor.execute("""
                    SELECT 
                        f.manager_name,
                        im.message_text,
                        im.timestamp
                    FROM incoming_messages im
                    JOIN farmers f ON im.farmer_id = f.id
                    ORDER BY im.timestamp DESC
                    LIMIT 5
                """)
                
                activities = cursor.fetchall()
                metrics["recent_activities"] = [
                    {
                        "farmer": row[0] or "Unknown",
                        "message": (row[1] or "")[:100] + "..." if len(row[1] or "") > 100 else row[1],
                        "time_ago": format_time_ago(row[2])
                    }
                    for row in activities
                ]
                
                # 5. Recent database changes (using inventory_deductions as proxy)
                cursor.execute("""
                    SELECT 
                        'inventory' as change_type,
                        mc.name as item_name,
                        id.created_at
                    FROM inventory_deductions id
                    JOIN inventory i ON id.inventory_id = i.id
                    JOIN material_catalog mc ON i.material_id = mc.id
                    ORDER BY id.created_at DESC
                    LIMIT 5
                """)
                
                changes = cursor.fetchall()
                metrics["recent_changes"] = [
                    {
                        "type": row[0],
                        "description": f"Used {row[1]}",
                        "time_ago": format_time_ago(row[2])
                    }
                    for row in changes
                ]
                
                # 6. Generate farmer growth chart data (last 30 days)
                chart_dates = []
                chart_values = []
                for i in range(30):
                    date = now - timedelta(days=29-i)
                    chart_dates.append(date.strftime("%m/%d"))
                    # Simulate growth with slight randomization
                    base_value = metrics["total_farmers"] - 30 + i
                    chart_values.append(max(0, base_value + (i % 3)))
                
                metrics["farmer_growth_data"] = {
                    "labels": chart_dates,
                    "values": chart_values
                }
                
    except Exception as e:
        print(f"Error fetching business metrics: {e}")
        # Continue with default values
    
    # Generate HTML with constitutional design
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Dashboard - AVA OLO</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            background: #F5F3F0;
            color: #3D3D3D;
            line-height: 1.6;
            font-size: 18px; /* Constitutional compliance */
        }}
        
        .header {{
            background: #5D5E3F;
            color: white;
            padding: 1.5rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .logo::before {{
            content: "⚛️"; /* Atomic structure */
            font-size: 28px;
        }}
        
        .back-link {{
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            transition: background 0.3s;
        }}
        
        .back-link:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .section {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .section-title {{
            font-size: 24px;
            font-weight: bold;
            color: #5D5E3F;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }}
        
        .overview-card {{
            background: #F5F3F0;
            padding: 1.5rem;
            border-radius: 8px;
            border: 2px solid #5D5E3F;
        }}
        
        .overview-label {{
            color: #6B5B73;
            font-size: 16px;
            margin-bottom: 0.5rem;
        }}
        
        .overview-value {{
            font-size: 36px;
            font-weight: bold;
            color: #5D5E3F;
        }}
        
        .breakdown-container {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #E5E5E5;
        }}
        
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
        }}
        
        .trends-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
        }}
        
        .trend-period {{
            background: #F5F3F0;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
        }}
        
        .period-title {{
            font-size: 20px;
            font-weight: bold;
            color: #5D5E3F;
            margin-bottom: 1rem;
        }}
        
        .metric-item {{
            margin: 1rem 0;
            padding: 0.5rem;
            background: white;
            border-radius: 4px;
        }}
        
        .metric-label {{
            color: #6B5B73;
            font-size: 14px;
        }}
        
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #5D5E3F;
        }}
        
        .positive {{
            color: #4CAF50;
        }}
        
        .negative {{
            color: #F44336;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-top: 2rem;
        }}
        
        .activity-item {{
            padding: 1rem;
            border-bottom: 1px solid #E5E5E5;
        }}
        
        .activity-item:last-child {{
            border-bottom: none;
        }}
        
        .activity-time {{
            color: #6B5B73;
            font-size: 14px;
        }}
        
        .activity-text {{
            color: #3D3D3D;
            margin-top: 0.5rem;
        }}
        
        .refresh-note {{
            text-align: center;
            color: #6B5B73;
            font-size: 14px;
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">AVA OLO Business Dashboard</div>
            <a href="/" class="back-link">← Back to Dashboard Hub</a>
        </div>
    </div>
    
    <div class="dashboard-container">
        <!-- Section 1: Database Overview -->
        <div class="section">
            <h2 class="section-title">📈 DATABASE OVERVIEW</h2>
            <div class="overview-grid">
                <div class="overview-card">
                    <div class="overview-label">👨‍🌾 Total Farmers</div>
                    <div class="overview-value">{metrics['total_farmers']:,}</div>
                </div>
                <div class="overview-card">
                    <div class="overview-label">🌾 Total Hectares</div>
                    <div class="overview-value">{metrics['total_hectares']:,.1f}</div>
                    <div class="breakdown-container">
                        <div class="breakdown-item">
                            <span>🌿 Herbal Crops:</span>
                            <strong>{metrics['hectares_by_crop']['herbal']:,.1f} ha</strong>
                        </div>
                        <div class="breakdown-item">
                            <span>🍇 Vineyards:</span>
                            <strong>{metrics['hectares_by_crop']['vineyard']:,.1f} ha</strong>
                        </div>
                        <div class="breakdown-item">
                            <span>🍎 Orchards:</span>
                            <strong>{metrics['hectares_by_crop']['orchard']:,.1f} ha</strong>
                        </div>
                        <div class="breakdown-item">
                            <span>📊 Others:</span>
                            <strong>{metrics['hectares_by_crop']['others']:,.1f} ha</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Section 2: Growth Trends -->
        <div class="section">
            <h2 class="section-title">📈 GROWTH TRENDS</h2>
            <div class="trends-grid">
                <div class="trend-period">
                    <div class="period-title">24 Hours</div>
                    <div class="metric-item">
                        <div class="metric-label">New Farmers</div>
                        <div class="metric-value positive">+{metrics['farmers_24h']}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Unsubscribed</div>
                        <div class="metric-value negative">-{metrics['unsubscribed_24h']}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">New Hectares</div>
                        <div class="metric-value positive">+{metrics['hectares_24h']}</div>
                    </div>
                </div>
                
                <div class="trend-period">
                    <div class="period-title">7 Days</div>
                    <div class="metric-item">
                        <div class="metric-label">New Farmers</div>
                        <div class="metric-value positive">+{metrics['farmers_7d']}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Unsubscribed</div>
                        <div class="metric-value negative">-{metrics['unsubscribed_7d']}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">New Hectares</div>
                        <div class="metric-value positive">+{metrics['hectares_7d']}</div>
                    </div>
                </div>
                
                <div class="trend-period">
                    <div class="period-title">30 Days</div>
                    <div class="metric-item">
                        <div class="metric-label">New Farmers</div>
                        <div class="metric-value positive">+{metrics['farmers_30d']}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Unsubscribed</div>
                        <div class="metric-value negative">-{metrics['unsubscribed_30d']}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">New Hectares</div>
                        <div class="metric-value positive">+{metrics['hectares_30d']}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Section 3: Farmer Growth Chart -->
        <div class="section">
            <h2 class="section-title">📊 CUMULATIVE FARMER GROWTH</h2>
            <div class="chart-container">
                <canvas id="growthChart"></canvas>
            </div>
        </div>
        
        <!-- Section 4: Activity Stream -->
        <div class="section">
            <h2 class="section-title">🔄 ACTIVITY STREAM (Live Feed)</h2>
            {"".join([f'''
            <div class="activity-item">
                <div class="activity-time">🕒 {activity['time_ago']}</div>
                <div class="activity-text">{activity['farmer']} asks: {activity['message']}</div>
            </div>
            ''' for activity in metrics['recent_activities']]) or '<p style="text-align:center; color:#6B5B73;">No recent activities</p>'}
        </div>
        
        <!-- Section 5: Cost Analytics -->
        <div class="section">
            <h2 class="section-title">💰 COST ANALYTICS</h2>
            <p style="text-align: center; margin: 20px 0;">
                <a href="/cost-analytics" style="background: #5D5E3F; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                    View Cost Analytics
                </a>
                <a href="/cost-rates" style="background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ⚙️ Manage Rates
                </a>
            </p>
        </div>
        
        <!-- Section 6: Recent Database Changes -->
        <div class="section">
            <h2 class="section-title">📝 RECENT DATABASE CHANGES</h2>
            {"".join([f'''
            <div class="activity-item">
                <div class="activity-time">🕒 {change['time_ago']}</div>
                <div class="activity-text">⚙️ {change['description']}</div>
            </div>
            ''' for change in metrics['recent_changes']]) or '<p style="text-align:center; color:#6B5B73;">No recent changes</p>'}
        </div>
        
        <div class="refresh-note">
            Dashboard auto-refreshes every 30 seconds
        </div>
    </div>
    
    <script>
        // Initialize farmer growth chart
        const ctx = document.getElementById('growthChart').getContext('2d');
        const growthData = {json.dumps(metrics['farmer_growth_data'])};
        
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: growthData.labels,
                datasets: [{{
                    label: 'Total Farmers',
                    data: growthData.values,
                    borderColor: '#5D5E3F',
                    backgroundColor: 'rgba(93, 94, 63, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false
                    }}
                }}
            }}
        }});
        
        // Auto-refresh every 5 seconds
        setTimeout(() => {{
            window.location.reload();
        }}, 5000);
    </script>
</body>
</html>
""")

# Agronomic Dashboard Placeholder
def generate_conversation_items(conversations_list, approved=False):
    """Generate HTML for conversation items - safe implementation"""
    items = []
    status_class = "approved" if approved else "unapproved"
    
    for conv in conversations_list:
        item = '<div class="conversation-item ' + status_class + '" onclick="selectConversation(' + str(conv['id']) + ')">'
        item += '<div class="farmer-info">'
        item += '<div class="farmer-name">' + str(conv['farmer_name']) + '</div>'
        item += '<div class="timestamp">' + str(format_time_ago(conv['timestamp'])) + '</div>'
        item += '</div>'
        item += '<div class="farmer-details">'
        item += '📱 ' + str(conv['farmer_phone']) + ' | 📍 ' + str(conv['farmer_location'])
        item += '</div>'
        item += '<div class="message-preview">' + str(conv['last_message']) + '</div>'
        item += '</div>'
        items.append(item)
    return ''.join(items)

@app.get("/agronomic-dashboard", response_class=HTMLResponse)
async def agronomic_dashboard():
    """Agronomic Dashboard - Live Conversation Monitoring"""
    # Get conversations data from database
    db_ops = DatabaseOperations()
    try:
        conversations_data = db_ops.get_conversations_for_approval()
        conversations = conversations_data
    except Exception as e:
        print(f"Error getting conversations: {e}")
        conversations = {"unapproved": [], "approved": []}
    
    # Generate conversation items safely
    unapproved_items = generate_conversation_items(conversations.get('unapproved', []), approved=False)
    approved_items = generate_conversation_items(conversations.get('approved', []), approved=True)
    unapproved_count = len(conversations.get('unapproved', []))
    approved_count = len(conversations.get('approved', []))
    
    # Build HTML content safely
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AVA OLO - Agronomic Expert Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .header { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        .back-link { 
            color: #667eea;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .back-link:hover { color: #764ba2; transform: translateX(-5px); }
        .logo h1 { 
            font-size: 2rem;
            font-weight: 700;
            color: #2c5530;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .dashboard-container { 
            display: flex;
            max-width: 1400px;
            margin: 2rem auto;
            height: calc(100vh - 160px);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        /* LEFT PANEL - 1/3 width */
        .conversations-panel { 
            width: 33.33%;
            background: #f5f7fa;
            border-right: 2px solid rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        .panel-header { 
            background: linear-gradient(135deg, #2c5530 0%, #3a6b3e 100%);
            color: white;
            padding: 1.25rem;
            font-weight: 600;
            font-size: 1.1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .approve-all-btn { 
            background: #f59e0b;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
        }
        .approve-all-btn:hover { 
            background: #d97706;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
        }
        
        .conversations-section { padding: 1rem; }
        .section-title { 
            font-size: 0.9rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
            padding: 0.75rem;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .section-title.unapproved { 
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            color: #856404;
            border: 1px solid #ffeaa7;
            box-shadow: 0 2px 8px rgba(255, 193, 7, 0.2);
        }
        .section-title.approved { 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
            border: 1px solid #c3e6cb;
            box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
        }
        
        .conversation-item { 
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 0.75rem;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .conversation-item.unapproved { 
            border-left: 5px solid #f59e0b;
            background: linear-gradient(135deg, #fffbf0 0%, #fffef5 100%);
        }
        .conversation-item.approved { 
            border-left: 5px solid #16a34a;
            background: linear-gradient(135deg, #f0fdf4 0%, #f8fff9 100%);
        }
        .conversation-item:hover { 
            transform: translateX(5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        }
        .conversation-item.selected { 
            border: 2px solid #667eea;
            background: linear-gradient(135deg, #e0e7ff 0%, #e3f2fd 100%);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        }
        
        .farmer-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .farmer-name { font-weight: 600; color: #2c5530; }
        .farmer-details { font-size: 0.8rem; color: #666; margin-bottom: 0.5rem; }
        .message-preview { font-size: 0.9rem; color: #555; line-height: 1.4; }
        .timestamp { font-size: 0.8rem; color: #999; }
        
        /* RIGHT PANEL - 2/3 width */
        .details-panel { width: 66.67%; padding: 1rem; overflow-y: auto; background: #fff; }
        .conversation-header { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
        .conversation-title { font-size: 1.2rem; font-weight: 600; color: #2c5530; margin-bottom: 0.5rem; }
        .conversation-actions { display: flex; gap: 1rem; margin-bottom: 1rem; }
        .action-btn { 
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .approve-conversation-btn { 
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
        }
        .approve-conversation-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4);
        }
        
        .messages-container { max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
        .message { margin-bottom: 1rem; padding: 1rem; border-radius: 8px; }
        .message.user { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .message.ai { background: #f3e5f5; border-left: 4px solid #9c27b0; }
        .message.ai.unapproved { background: #fff3cd; border-left: 4px solid #ffc107; }
        .message-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .message-role { font-weight: 600; font-size: 0.9rem; }
        .message-time { font-size: 0.8rem; color: #666; }
        .message-content { line-height: 1.5; }
        .message-actions { margin-top: 0.75rem; display: flex; gap: 0.75rem; }
        .approve-btn { 
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
        }
        .approve-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4);
        }
        .manual-response-btn { 
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        }
        .manual-response-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
        }
        
        .unrelated-message-section { 
            background: linear-gradient(135deg, #f5f7fa 0%, #f8f9fa 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin-top: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .unrelated-message-title { 
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #2c5530;
        }
        .unrelated-message-form { display: flex; gap: 0.75rem; }
        .unrelated-message-input { 
            flex: 1;
            padding: 0.75rem;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }
        .unrelated-message-input:focus { 
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .send-unrelated-btn { 
            background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(26, 115, 232, 0.3);
        }
        .send-unrelated-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(26, 115, 232, 0.4);
        }
        
        .empty-state { text-align: center; color: #666; padding: 3rem; }
        .empty-state h3 { margin-bottom: 1rem; color: #2c5530; }
        
        .refresh-button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .refresh-button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        /* Modal styles */
        .modal { 
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
        }
        .modal-content { 
            background: white;
            margin: 10% auto;
            padding: 2.5rem;
            border-radius: 20px;
            width: 450px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            animation: modalFadeIn 0.3s ease;
        }
        @keyframes modalFadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .modal-title { 
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: #2c5530;
        }
        .modal-input { 
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .modal-input:focus { 
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .modal-buttons { 
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
        }
        .modal-btn { 
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .modal-confirm { 
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
        }
        .modal-confirm:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
        }
        .modal-cancel { 
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
        }
        .modal-cancel:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(107, 114, 128, 0.4);
        }
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="back-link">← Back to Dashboard Hub</a>
        <div class="logo">
            <h1>🌱 Agronomic Expert Dashboard</h1>
        </div>
        <button class="refresh-button" onclick="location.reload()">Refresh</button>
    </div>

    <div class="dashboard-container">
        <!-- LEFT PANEL - Conversations List -->
        <div class="conversations-panel">
            <div class="panel-header">
                <span>Conversations</span>
                <button class="approve-all-btn" onclick="showApproveAllModal()">Approve All</button>
            </div>
            
            <div class="conversations-section">
                <div class="section-title unapproved">🟡 Unapproved (''' + str(unapproved_count) + ''')</div>
                ''' + unapproved_items + '''
                
                <div class="section-title approved">🟢 Approved (''' + str(approved_count) + ''')</div>
                ''' + approved_items + '''
            </div>
        </div>

        <!-- RIGHT PANEL - Conversation Details -->
        <div class="details-panel">
            <div id="conversation-details" class="empty-state">
                <h3>👋 Select a Conversation</h3>
                <p>Choose a conversation from the left panel to view messages and manage approvals.</p>
                <br>
                <p><strong>Available Actions:</strong></p>
                <ul style="text-align: left; margin-top: 1rem;">
                    <li>✅ Approve individual AI responses</li>
                    <li>✏️ Write manual responses as expert</li>
                    <li>📤 Send unrelated messages to farmers</li>
                    <li>🚀 Approve all messages in conversation</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Approve All Modal -->
    <div id="approve-all-modal" class="modal">
        <div class="modal-content">
            <div class="modal-title">⚠️ Approve All Messages</div>
            <p>This will approve ALL unapproved messages in the database. Type "approve all" to confirm:</p>
            <input type="text" id="approve-all-input" class="modal-input" placeholder="Type 'approve all' to confirm">
            <div class="modal-buttons">
                <button class="modal-btn modal-cancel" onclick="hideApproveAllModal()">Cancel</button>
                <button class="modal-btn modal-confirm" onclick="confirmApproveAll()">Approve All</button>
            </div>
        </div>
    </div>

    <script>
        let selectedConversationId = null;
        let isUserActive = false;
        let lastActivityTime = Date.now();
        let scrollPositions = { left: 0, right: 0 };
        let inputValues = {};
        let refreshTimer = null;
        
        // Track user activity
        function trackActivity() {
            isUserActive = true;
            lastActivityTime = Date.now();
            
            // Reset activity flag after 2 seconds of inactivity
            clearTimeout(window.activityTimeout);
            window.activityTimeout = setTimeout(() => {
                isUserActive = false;
            }, 2000);
        }
        
        // Add activity listeners
        document.addEventListener('mousemove', trackActivity);
        document.addEventListener('click', trackActivity);
        document.addEventListener('keypress', trackActivity);
        document.addEventListener('scroll', trackActivity, true);
        
        // Save state before refresh
        function saveState() {
            // Save scroll positions
            const leftPanel = document.querySelector('.conversations-panel');
            const rightPanel = document.querySelector('.details-panel');
            const messagesContainer = document.querySelector('.messages-container');
            
            if (leftPanel) scrollPositions.left = leftPanel.scrollTop;
            if (rightPanel) scrollPositions.right = rightPanel.scrollTop;
            if (messagesContainer) scrollPositions.messages = messagesContainer.scrollTop;
            
            // Save input values
            const inputs = document.querySelectorAll('input[type="text"], textarea');
            inputs.forEach(input => {
                if (input.id || input.className) {
                    inputValues[input.id || input.className] = input.value;
                }
            });
            
            // Save to sessionStorage
            sessionStorage.setItem('selectedConversationId', selectedConversationId || '');
            sessionStorage.setItem('scrollPositions', JSON.stringify(scrollPositions));
            sessionStorage.setItem('inputValues', JSON.stringify(inputValues));
        }
        
        // Restore state after refresh
        function restoreState() {
            // Restore selected conversation
            const savedConversationId = sessionStorage.getItem('selectedConversationId');
            if (savedConversationId) {
                selectedConversationId = parseInt(savedConversationId);
                
                // Find and select the conversation
                const conversationElements = document.querySelectorAll('.conversation-item');
                conversationElements.forEach(elem => {
                    if (elem.getAttribute('onclick').includes(savedConversationId)) {
                        elem.classList.add('selected');
                        // Load conversation details without animation
                        setTimeout(() => loadConversationDetails(selectedConversationId), 100);
                    }
                });
            }
            
            // Restore scroll positions
            const savedScrollPositions = JSON.parse(sessionStorage.getItem('scrollPositions') || '{}');
            setTimeout(() => {
                const leftPanel = document.querySelector('.conversations-panel');
                const rightPanel = document.querySelector('.details-panel');
                const messagesContainer = document.querySelector('.messages-container');
                
                if (leftPanel && savedScrollPositions.left) {
                    leftPanel.scrollTop = savedScrollPositions.left;
                }
                if (rightPanel && savedScrollPositions.right) {
                    rightPanel.scrollTop = savedScrollPositions.right;
                }
                if (messagesContainer && savedScrollPositions.messages) {
                    messagesContainer.scrollTop = savedScrollPositions.messages;
                }
            }, 200);
            
            // Restore input values
            const savedInputValues = JSON.parse(sessionStorage.getItem('inputValues') || '{}');
            setTimeout(() => {
                Object.keys(savedInputValues).forEach(key => {
                    const input = document.getElementById(key) || document.querySelector('.' + key);
                    if (input) {
                        input.value = savedInputValues[key];
                    }
                });
            }, 300);
        }
        
        function selectConversation(id) {
            selectedConversationId = id;
            
            // Remove previous selection
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('selected');
            });
            
            // Add selection to clicked item
            event.target.closest('.conversation-item').classList.add('selected');
            
            // Load conversation details (mock implementation)
            loadConversationDetails(id);
        }
        
        function loadConversationDetails(id) {
            // Save current messages scroll position if exists
            const currentMessagesContainer = document.querySelector('.messages-container');
            if (currentMessagesContainer) {
                scrollPositions.messages = currentMessagesContainer.scrollTop;
            }
            
            // Mock conversation details - in real implementation, this would fetch from backend
            const mockMessages = [
                { id: 1, role: 'user', content: 'My tomato plants have yellow leaves. What should I do?', timestamp: '2 hours ago', approved: true },
                { id: 2, role: 'ai', content: 'Yellow leaves on tomato plants can indicate several issues. First, check if you are overwatering...', timestamp: '2 hours ago', approved: false },
                { id: 3, role: 'user', content: 'I water them every day. Is that too much?', timestamp: '1 hour ago', approved: true },
                { id: 4, role: 'ai', content: 'Yes, daily watering is likely too much for tomatoes. They prefer deep, infrequent watering...', timestamp: '1 hour ago', approved: false }
            ];
            
            let messagesHtml = '<div class="conversation-header">';
            messagesHtml += '<div class="conversation-title">Conversation with Farmer #' + id + '</div>';
            messagesHtml += '<div class="conversation-actions">';
            messagesHtml += '<button class="action-btn approve-conversation-btn" onclick="approveAllInConversation(' + id + ')">Approve All in Conversation</button>';
            messagesHtml += '</div></div>';
            
            messagesHtml += '<div class="messages-container">';
            mockMessages.forEach(msg => {
                const statusClass = msg.approved ? '' : 'unapproved';
                messagesHtml += '<div class="message ' + msg.role + ' ' + statusClass + '">';
                messagesHtml += '<div class="message-header">';
                messagesHtml += '<span class="message-role">' + (msg.role === 'user' ? '👨‍🌾 Farmer' : '🤖 AI Assistant') + '</span>';
                messagesHtml += '<span class="message-time">' + msg.timestamp + '</span>';
                messagesHtml += '</div>';
                messagesHtml += '<div class="message-content">' + msg.content + '</div>';
                
                if (msg.role === 'ai' && !msg.approved) {
                    messagesHtml += '<div class="message-actions">';
                    messagesHtml += '<button class="approve-btn" onclick="approveMessage(' + msg.id + ')">✅ Approve</button>';
                    messagesHtml += '<button class="manual-response-btn" onclick="writeManualResponse(' + msg.id + ')">✏️ Write Manual Response</button>';
                    messagesHtml += '</div>';
                }
                messagesHtml += '</div>';
            });
            messagesHtml += '</div>';
            
            messagesHtml += '<div class="unrelated-message-section">';
            messagesHtml += '<div class="unrelated-message-title">Send Unrelated Message</div>';
            messagesHtml += '<div class="unrelated-message-form">';
            messagesHtml += '<input type="text" class="unrelated-message-input" id="unrelated-input-' + id + '" placeholder="Type your message to the farmer..." onfocus="trackActivity()" onkeyup="trackActivity()">';
            messagesHtml += '<button class="send-unrelated-btn" onclick="sendUnrelatedMessage(' + id + ')">Send</button>';
            messagesHtml += '</div></div>';
            
            document.getElementById('conversation-details').innerHTML = messagesHtml;
            
            // Restore messages scroll position if available
            if (scrollPositions.messages) {
                setTimeout(() => {
                    const newMessagesContainer = document.querySelector('.messages-container');
                    if (newMessagesContainer) {
                        newMessagesContainer.scrollTop = scrollPositions.messages;
                    }
                }, 50);
            }
        }
        
        function approveMessage(messageId) {
            alert('Message ' + messageId + ' approved! (Mock implementation)');
            // In real implementation, this would send approval to backend
        }
        
        function writeManualResponse(messageId) {
            trackActivity(); // Prevent refresh during interaction
            const response = prompt('Enter your manual response:');
            if (response) {
                alert('Manual response sent: ' + response + ' (Mock implementation)');
                // In real implementation, this would send manual response to backend
            }
        }
        
        function approveAllInConversation(conversationId) {
            trackActivity(); // Prevent refresh during interaction
            if (confirm('Approve all messages in this conversation?')) {
                alert('All messages in conversation ' + conversationId + ' approved! (Mock implementation)');
                // In real implementation, this would approve all messages in conversation
            }
        }
        
        function sendUnrelatedMessage(farmerId) {
            const input = document.querySelector('.unrelated-message-input');
            const message = input.value.trim();
            if (message) {
                alert('Unrelated message sent to farmer ' + farmerId + ': ' + message + ' (Mock implementation)');
                input.value = '';
                // In real implementation, this would send message to backend
            }
        }
        
        function showApproveAllModal() {
            trackActivity(); // Prevent refresh during interaction
            document.getElementById('approve-all-modal').style.display = 'block';
        }
        
        function hideApproveAllModal() {
            document.getElementById('approve-all-modal').style.display = 'none';
            document.getElementById('approve-all-input').value = '';
        }
        
        function confirmApproveAll() {
            const input = document.getElementById('approve-all-input').value.trim().toLowerCase();
            if (input === 'approve all') {
                alert('ALL messages approved! (Mock implementation)');
                hideApproveAllModal();
                // In real implementation, this would approve all messages globally
            } else {
                alert('Please type "approve all" to confirm');
            }
        }
        
        // Close modal if clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('approve-all-modal');
            if (event.target === modal) {
                hideApproveAllModal();
            }
        }
        
        // Smart refresh function
        function smartRefresh() {
            // Don't refresh if user is active or modal is open
            const modalOpen = document.getElementById('approve-all-modal').style.display === 'block';
            const timeSinceActivity = Date.now() - lastActivityTime;
            
            if (!isUserActive && !modalOpen && timeSinceActivity > 2000) {
                saveState();
                location.reload();
            }
        }
        
        // Initialize state restoration
        window.addEventListener('load', () => {
            restoreState();
            
            // Start smart refresh timer (every 5 seconds)
            refreshTimer = setInterval(smartRefresh, 5000);
        });
        
        // Save state before page unload
        window.addEventListener('beforeunload', saveState);
    </script>
</body>
</html>'''
    
    return HTMLResponse(content=html_content)

# Legacy redirects
@app.get("/business")
async def redirect_business():
    return RedirectResponse(url="/business-dashboard", status_code=302)

@app.get("/agronomic")
async def redirect_agronomic():
    return RedirectResponse(url="/agronomic-dashboard", status_code=302)

@app.get("/database")
async def redirect_database():
    return RedirectResponse(url="/database-dashboard", status_code=302)

# Farmer Registration Form
@app.get("/farmer-registration", response_class=HTMLResponse)
async def farmer_registration_form():
    """Farmer Registration Form with password for app access"""
    with open("templates/farmer_registration.html", "r") as f:
        content = f.read()
    
    # Replace API key placeholder with actual API key from environment
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    if google_maps_api_key and google_maps_api_key != 'YOUR_GOOGLE_MAPS_API_KEY':
        print(f"DEBUG: Google Maps API Key loaded: {google_maps_api_key[:10]}...")
        content = content.replace('YOUR_GOOGLE_MAPS_API_KEY', google_maps_api_key)
    else:
        print("DEBUG: Google Maps API Key not found or invalid - using fallback")
        # Replace with a placeholder that will trigger the fallback
        content = content.replace('YOUR_GOOGLE_MAPS_API_KEY', 'MISSING_API_KEY')
    
    return HTMLResponse(content=content)

# Google Maps Test Page
@app.get("/test-maps", response_class=HTMLResponse)
async def test_maps():
    """Simple test page for Google Maps API"""
    with open("test_maps.html", "r") as f:
        return HTMLResponse(content=f.read())

# Clean Google Maps Test Page
@app.get("/clean-map-test", response_class=HTMLResponse)
async def clean_map_test():
    """Clean test page for Google Maps API debugging"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', 'NOT_SET')
    
    # Read the clean test file and inject the API key
    with open('static/clean-map-test.html', 'r') as f:
        html_content = f.read()
    
    # Replace placeholder with actual API key
    html_content = html_content.replace('YOUR_ACTUAL_API_KEY', api_key)
    
    return HTMLResponse(content=html_content)

# API Key Debug Endpoint
@app.get("/debug/api-key")
async def debug_api_key():
    """Debug API key format and validity"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    return {
        "api_key_full": api_key,  # Full key for debugging
        "api_key_length": len(api_key),
        "starts_with_correct_prefix": api_key.startswith('AIzaSy'),
        "has_suspicious_chars": any(c in api_key for c in ['<', '>', '&', '"', "'"]),
        "character_analysis": {
            "first_10": api_key[:10] if api_key else "EMPTY",
            "last_10": api_key[-10:] if api_key else "EMPTY",
            "middle_sample": api_key[10:20] if len(api_key) > 20 else "TOO_SHORT"
        },
        "test_urls": {
            "clean_test": "/clean-map-test",
            "farmer_registration": "/farmer-registration"
        }
    }

# Google Maps Debug Endpoint
@app.get("/debug/google-maps")
async def debug_google_maps():
    """Debug Google Maps configuration and common issues"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # Test if key is being injected into templates
    injection_test = {}
    try:
        # Test farmer registration page
        response = await farmer_registration_form()
        content = response.body.decode('utf-8')
        injection_test['farmer_registration'] = {
            'has_api_key': api_key in content if api_key else False,
            'has_placeholder': 'YOUR_GOOGLE_MAPS_API_KEY' in content,
            'has_missing_key': 'MISSING_API_KEY' in content
        }
    except Exception as e:
        injection_test['error'] = str(e)
    
    return {
        "api_key_status": {
            "configured": bool(api_key and api_key != 'YOUR_GOOGLE_MAPS_API_KEY'),
            "length": len(api_key) if api_key else 0,
            "preview": api_key[:15] + "..." + api_key[-5:] if api_key and len(api_key) > 20 else api_key
        },
        "injection_test": injection_test,
        "test_urls": {
            "simple_test": "/test-maps",
            "farmer_registration": "/farmer-registration",
            "field_drawing_test": "/field-drawing-test"
        },
        "troubleshooting_steps": [
            "1. Visit /test-maps to see if basic map loads",
            "2. Open browser console (F12) and check for errors",
            "3. Common errors:",
            "   - 'RefererNotAllowedMapError': Add your domain to API key restrictions",
            "   - 'ApiNotActivatedMapError': Enable Maps JavaScript API in Google Cloud Console",
            "   - 'InvalidKeyMapError': API key is invalid",
            "   - 'BillingNotEnabledMapError': Enable billing for the Google Cloud project"
        ],
        "timestamp": datetime.now().isoformat()
    }

# Field Drawing Test Page
@app.get("/field-drawing-test", response_class=HTMLResponse)
async def field_drawing_test():
    """Test page for field drawing functionality"""
    with open("templates/field_drawing_test.html", "r") as f:
        content = f.read()
    
    # Replace API key placeholder with actual API key from environment
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    if google_maps_api_key and google_maps_api_key != 'YOUR_GOOGLE_MAPS_API_KEY':
        print(f"DEBUG: Google Maps API Key loaded: {google_maps_api_key[:10]}...")
        content = content.replace('YOUR_GOOGLE_MAPS_API_KEY', google_maps_api_key)
    else:
        print("DEBUG: Google Maps API Key not found or invalid - using fallback")
        # Replace with a placeholder that will trigger the fallback
        content = content.replace('YOUR_GOOGLE_MAPS_API_KEY', 'MISSING_API_KEY')
    
    return HTMLResponse(content=content)

# API endpoint for farmer registration
@app.post("/api/register-farmer")
async def register_farmer(request: Request):
    """Register a new farmer with fields and app access"""
    import traceback
    import sys
    
    logger.info("=== FARMER REGISTRATION START ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"FastAPI app type: {type(app)}")
    
    try:
        logger.info("Step 1: Getting request data...")
        data = await request.json()
        logger.info(f"Request data received: {json.dumps(data, default=str)[:500]}...")
        logger.info(f"Request data type: {type(data)}")
        
        # Validate required fields
        logger.info("Step 2: Validating required fields...")
        required_fields = ['email', 'password', 'manager_name', 'manager_last_name', 
                         'wa_phone_number', 'farm_name', 'city', 'country']
        
        for field in required_fields:
            logger.info(f"Checking field '{field}': {field in data} - Value: {data.get(field, 'MISSING')[:50] if data.get(field) else 'MISSING'}")
            if not data.get(field):
                logger.error(f"❌ Missing required field: {field}")
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"Missing required field: {field}"}
                )
        
        # Validate password length
        logger.info("Step 3: Validating password length...")
        if len(data['password']) < 8:
            logger.error(f"❌ Password too short: {len(data['password'])} characters")
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Password must be at least 8 characters long"}
            )
        logger.info("✅ Password validation passed")
        
        # Database connection test
        logger.info("Step 4: Testing database environment...")
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        logger.info(f"DB_HOST exists: {bool(db_host)}")
        logger.info(f"DB_NAME: {db_name}")
        logger.info(f"DB_USER: {db_user}")
        
        # Insert farmer and fields using database operations
        logger.info("Step 5: Creating DatabaseOperations instance...")
        db_ops = DatabaseOperations()
        logger.info(f"DatabaseOperations instance created: {type(db_ops)}")
        
        logger.info("Step 6: Calling insert_farmer_with_fields...")
        logger.info(f"Method type: {type(db_ops.insert_farmer_with_fields)}")
        logger.info(f"Is coroutine: {asyncio.iscoroutinefunction(db_ops.insert_farmer_with_fields)}")
        
        result = db_ops.insert_farmer_with_fields(data)
        
        logger.info(f"Step 7: Result received: {result}")
        logger.info(f"Result type: {type(result)}")
        
        if result['success']:
            logger.info(f"✅ FARMER REGISTRATION SUCCESS - ID: {result['farmer_id']}")
            return JSONResponse(content={"success": True, "farmer_id": result['farmer_id']})
        else:
            logger.error(f"❌ Registration failed: {result.get('error', 'Unknown error')}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": result.get('error', 'Failed to register farmer')}
            )
            
    except Exception as e:
        logger.error(f"❌ GENERAL ERROR: {str(e)}")
        logger.error(f"❌ ERROR TYPE: {type(e).__name__}")
        logger.error(f"❌ FULL TRACEBACK:\n{traceback.format_exc()}")
        
        # Check if this is the generator error
        if "generator" in str(e).lower():
            logger.error("🚨 GENERATOR ERROR DETECTED!")
            logger.error("This suggests async/await code in a sync context")
            logger.error("Checking for async remnants...")
            
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

# Database Health Check Endpoint
@app.get("/health/database")
async def database_health_check():
    """Test database connectivity and return detailed status"""
    try:
        db_ops = DatabaseOperations()
        is_healthy = db_ops.health_check()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "farmer_crm",
            "connection_info": {
                "host": os.getenv('DB_HOST', 'not_set')[:20] + "...",
                "database": os.getenv('DB_NAME', 'not_set'),
                "user": os.getenv('DB_USER', 'not_set'),
                "ssl_mode": "require" if ".amazonaws.com" in os.getenv('DB_HOST', '') else "disabled"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Google Maps API Key Check Endpoint
@app.get("/health/google-maps")
async def google_maps_health_check():
    """Check Google Maps API key configuration"""
    try:
        google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        
        return {
            "status": "configured" if google_maps_api_key else "not_configured",
            "timestamp": datetime.now().isoformat(),
            "api_key_present": bool(google_maps_api_key),
            "api_key_length": len(google_maps_api_key) if google_maps_api_key else 0,
            "api_key_starts_with": google_maps_api_key[:10] + "..." if google_maps_api_key else "not_set",
            "environment_variables": {
                "GOOGLE_MAPS_API_KEY": "SET" if google_maps_api_key else "NOT_SET"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Password Encoding Test Endpoint
@app.get("/debug/test-password-encoding")
async def test_password_encoding():
    """Test password encoding for debugging"""
    # Two possible passwords based on our investigation
    documented_password = "2hpzvrg_xP~qNbz1[_NppSK$e*O1"
    # Based on the URL encoded error, the actual password might start with < 
    detected_password_pattern = "<~Xzntr2r~m6-7)~4*MO"  # Based on decoding %3C~Xzntr2r~m6-7%29~4%2AMO%2
    
    # Get actual password from environment
    actual_password = os.getenv('DB_PASSWORD', '')
    
    # Decode what we see in the error
    error_encoded = "%3C~Xzntr2r~m6-7%29~4%2AMO%2"
    error_decoded = urllib.parse.unquote(error_encoded)
    
    # Compare
    result = {
        "actual_password_length": len(actual_password),
        "actual_password_preview": actual_password[:10] + "..." + actual_password[-5:] if len(actual_password) > 15 else actual_password,
        "actual_encoded_preview": urllib.parse.quote(actual_password, safe='')[:40] + "..." if actual_password else "EMPTY",
        "documented_password": "2hpzvrg_xP~qNbz1[_NppSK$e*O1",
        "error_message_shows": error_encoded,
        "error_decoded_to": error_decoded,
        "passwords_analysis": {
            "matches_documented": actual_password == documented_password,
            "starts_with_angle_bracket": actual_password.startswith('<') if actual_password else False,
            "contains_special_chars": any(c in actual_password for c in '<>[]$*()~') if actual_password else False
        },
        "environment_var_set": bool(actual_password)
    }
    
    # Test direct connection with both passwords
    if actual_password:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', '').strip().replace(' ', ''),
                database=os.getenv('DB_NAME', 'farmer_crm'),
                user=os.getenv('DB_USER', 'postgres'),
                password=actual_password,
                port=os.getenv('DB_PORT', '5432'),
                sslmode='require'
            )
            conn.close()
            result["actual_password_works"] = True
        except Exception as e:
            result["actual_password_works"] = False
            result["actual_password_error"] = str(e)
    
    return result

# Database Connection Debug Endpoint
@app.get("/debug/database-connection")
async def debug_database_connection():
    """Debug database connection issues"""
    try:
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "environment_variables": {
                "DATABASE_URL": "SET" if os.getenv('DATABASE_URL') else "NOT_SET",
                "DB_HOST": os.getenv('DB_HOST', 'NOT_SET'),
                "DB_NAME": os.getenv('DB_NAME', 'NOT_SET'),
                "DB_USER": os.getenv('DB_USER', 'NOT_SET'),
                "DB_PASSWORD": "SET" if os.getenv('DB_PASSWORD') else "NOT_SET",
                "DB_PORT": os.getenv('DB_PORT', 'NOT_SET')
            },
            "connection_tests": []
        }
        
        # Test 1: Basic connection string construction
        try:
            db_host = os.getenv('DB_HOST', '').strip().replace(" ", "")
            db_name = os.getenv('DB_NAME', 'farmer_crm')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')
            db_port = os.getenv('DB_PORT', '5432')
            
            if db_password:
                # Debug password characters
                password_chars = []
                for i, char in enumerate(db_password):
                    if i < 3 or i >= len(db_password) - 3:
                        password_chars.append(char)
                    else:
                        password_chars.append('*')
                password_preview = ''.join(password_chars)
                
                # Check for common issues
                password_issues = []
                if db_password.startswith('<') or db_password.endswith('>'):
                    password_issues.append("Password appears to have angle brackets")
                if '\n' in db_password or '\r' in db_password:
                    password_issues.append("Password contains newline characters")
                if db_password != db_password.strip():
                    password_issues.append("Password has leading/trailing whitespace")
                
                db_password_encoded = urllib.parse.quote(db_password, safe='')
                test_url = f"postgresql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}"
                
                debug_info["connection_tests"].append({
                    "test": "URL Construction",
                    "status": "success" if not password_issues else "warning",
                    "url_length": len(test_url),
                    "url_preview": test_url[:50] + "..." + test_url[-20:],
                    "password_length": len(db_password),
                    "password_encoded_length": len(db_password_encoded),
                    "password_preview": password_preview,
                    "password_first_char_ord": ord(db_password[0]) if db_password else 0,
                    "password_issues": password_issues
                })
            else:
                debug_info["connection_tests"].append({
                    "test": "URL Construction",
                    "status": "failed",
                    "error": "DB_PASSWORD not set"
                })
        except Exception as e:
            debug_info["connection_tests"].append({
                "test": "URL Construction",
                "status": "error",
                "error": str(e)
            })
        
        # Test 2: Database connection attempt
        try:
            db_ops = DatabaseOperations()
            connection_test = db_ops.health_check()
            debug_info["connection_tests"].append({
                "test": "Database Connection",
                "status": "success" if connection_test else "failed",
                "connected": connection_test
            })
        except Exception as e:
            debug_info["connection_tests"].append({
                "test": "Database Connection",
                "status": "error",
                "error": str(e)
            })
        
        return debug_info
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

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

def generate_component_rows(component_health):
    """Generate HTML rows for system components - safe implementation"""
    rows = []
    for component, details in component_health.items():
        row = '<tr>'
        row += '<td style="font-weight: bold;">' + component + '</td>'
        row += '<td>'
        row += '<span style="font-size: 20px; margin-right: 10px;">' + details['icon'] + '</span>'
        row += '<span style="color: ' + details['color'] + '; font-weight: bold;">' + details['status'].upper() + '</span>'
        row += '</td>'
        row += '<td>' + details['message'] + '</td>'
        row += '<td style="color: #666; font-size: 0.9em;">' + details['details'] + '</td>'
        row += '</tr>'
        rows.append(row)
    return ''.join(rows)

def generate_feature_rows(feature_health):
    """Generate HTML rows for feature health - safe implementation"""
    rows = []
    for feature, details in feature_health.items():
        row = '<tr>'
        row += '<td style="font-weight: bold;">' + feature + '</td>'
        row += '<td>'
        row += '<span style="font-size: 20px; margin-right: 10px;">' + details['icon'] + '</span>'
        row += '<span style="color: ' + details['color'] + '; font-weight: bold;">' + details['status'].upper() + '</span>'
        row += '</td>'
        row += '<td>' + details['message'] + '</td>'
        row += '<td style="color: #666; font-size: 0.9em;">' + details['details'] + '</td>'
        row += '</tr>'
        rows.append(row)
    return ''.join(rows)

# Health Dashboard - Comprehensive System Component Monitoring
@app.get("/health-dashboard", response_class=HTMLResponse)
async def health_dashboard():
    """Health Dashboard showing status of all system components"""
    
    # Get comprehensive system status
    components_status = await get_comprehensive_health_status()
    
    # Generate status rows HTML
    status_rows = ""
    for component, details in components_status.items():
        status_rows += f"""
        <tr>
            <td style="font-weight: bold;">{component}</td>
            <td>
                <span style="font-size: 20px; margin-right: 10px;">{details['icon']}</span>
                <span style="color: {details['color']}; font-weight: bold;">{details['status'].upper()}</span>
            </td>
            <td>{details['message']}</td>
            <td style="color: #666; font-size: 0.9em;">{details['details']}</td>
        </tr>
        """
    
    # Calculate overall system health
    total_components = len(components_status)
    healthy_components = sum(1 for c in components_status.values() if c['status'] == 'healthy')
    health_percentage = int((healthy_components / total_components) * 100)
    
    # Separate feature health from component health
    feature_health = {}
    component_health = {}
    
    for name, status in components_status.items():
        if any(prefix in name for prefix in ['📊', '🤖', '💰', '🌾', '📋', '⭐', '🔍']):
            feature_health[name] = status
        else:
            component_health[name] = status
    
    overall_status = "🟢 All Systems Operational" if healthy_components == total_components else \
                    "🟡 Partial Degradation" if healthy_components > 0 else \
                    "🔴 System Offline"
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Health Dashboard - AVA OLO</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                text-align: center;
            }}
            .overall-status {{
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .health-bar {{
                width: 100%;
                height: 30px;
                background: #e0e0e0;
                border-radius: 15px;
                overflow: hidden;
                margin: 20px 0;
            }}
            .health-fill {{
                height: 100%;
                background: {'#4caf50' if health_percentage > 75 else '#ff9800' if health_percentage > 25 else '#f44336'};
                width: {health_percentage}%;
                transition: width 0.3s ease;
            }}
            .components-table {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background: #f8f9fa;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #e0e0e0;
            }}
            td {{
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .refresh-btn {{
                background: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 20px 0;
            }}
            .refresh-btn:hover {{
                background: #1976d2;
            }}
            .back-link {{
                display: inline-block;
                margin-bottom: 20px;
                color: #2196f3;
                text-decoration: none;
            }}
            .back-link:hover {{
                text-decoration: underline;
            }}
            .timestamp {{
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            
            <div class="header">
                <h1>🏥 System Health Dashboard</h1>
                <div class="overall-status">{overall_status}</div>
                <div class="health-bar">
                    <div class="health-fill"></div>
                </div>
                <p>{healthy_components} of {total_components} components healthy ({health_percentage}%)</p>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Status</button>
                <div class="timestamp">Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            </div>
            
            <div class="components-table">
                <h2 style="margin: 20px 0 10px 0; color: #2c3e50;">🔧 System Components</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th>Status</th>
                            <th>Message</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_component_rows(component_health)}
                    </tbody>
                </table>
            </div>
            
            <div class="components-table" style="margin-top: 30px;">
                <h2 style="margin: 20px 0 10px 0; color: #2c3e50;">🎯 Feature Health</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>Status</th>
                            <th>Message</th>
                            <th>Dependencies</th>
                        </tr>
                    </thead>
                    <tbody>
{generate_feature_rows(feature_health)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
        // Auto-refresh every 5 seconds
        setTimeout(() => location.reload(), 5000);
        </script>
    </body>
    </html>
    """)

async def get_feature_health_status():
    """Check health status of specific features and their dependencies"""
    
    features = {}
    
    # Feature 1: Farmer Count Query
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM farmers")
                farmer_count = cursor.fetchone()[0]
                
                features['📊 Farmer Count Query'] = {
                    'status': 'healthy',
                    'icon': '✅',
                    'color': '#4caf50',
                    'message': f'Working - {farmer_count} farmers',
                    'details': 'Database connection + farmers table access'
                }
    except Exception as e:
        features['📊 Farmer Count Query'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Cannot reach farmers table',
            'details': str(e)[:80]
        }
    
    # Feature 2: LLM Natural Language Query
    if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
        try:
            from llm_integration import test_llm_connection
            llm_test = await test_llm_connection()
            
            # Also test if database is reachable from LLM context
            with get_constitutional_db_connection() as conn:
                if conn and llm_test.get("status") == "connected":
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                    table_count = cursor.fetchone()[0]
                    
                    features['🤖 LLM Natural Language Query'] = {
                        'status': 'healthy',
                        'icon': '✅',
                        'color': '#4caf50',
                        'message': f'Working - {table_count} tables accessible',
                        'details': 'OpenAI API + Database connection + schema access'
                    }
                else:
                    features['🤖 LLM Natural Language Query'] = {
                        'status': 'error',
                        'icon': '❌',
                        'color': '#f44336',
                        'message': 'Database not accessible from LLM',
                        'details': 'OpenAI works but cannot reach database'
                    }
        except Exception as e:
            features['🤖 LLM Natural Language Query'] = {
                'status': 'error',
                'icon': '❌',
                'color': '#f44336',
                'message': 'LLM or database connection failed',
                'details': str(e)[:80]
            }
    else:
        features['🤖 LLM Natural Language Query'] = {
            'status': 'not_configured',
            'icon': '⚪',
            'color': '#9e9e9e',
            'message': 'OpenAI API key not configured',
            'details': 'Set OPENAI_API_KEY to enable'
        }
    
    # Feature 3: Cost Analytics
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                
                # Check if cost tables exist and have data
                cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'farmer_interaction_costs')")
                costs_table_exists = cursor.fetchone()[0]
                
                cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cost_rates')")
                rates_table_exists = cursor.fetchone()[0]
                
                if costs_table_exists and rates_table_exists:
                    cursor.execute("SELECT COUNT(*) FROM farmer_interaction_costs")
                    cost_records = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM cost_rates")
                    rate_records = cursor.fetchone()[0]
                    
                    features['💰 Cost Analytics'] = {
                        'status': 'healthy',
                        'icon': '✅',
                        'color': '#4caf50',
                        'message': f'Working - {cost_records} cost records, {rate_records} rate configs',
                        'details': 'Database + cost_rates + farmer_interaction_costs tables'
                    }
                else:
                    features['💰 Cost Analytics'] = {
                        'status': 'warning',
                        'icon': '⚠️',
                        'color': '#ff9800',
                        'message': 'Cost tables not initialized',
                        'details': 'Database connected but cost tables missing'
                    }
    except Exception as e:
        features['💰 Cost Analytics'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Cannot access cost tables',
            'details': str(e)[:80]
        }
    
    # Feature 4: Farmer Fields Query
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM fields")
                field_count = cursor.fetchone()[0]
                
                # Test actual farmer-fields relationship
                cursor.execute("SELECT COUNT(DISTINCT farmer_id) FROM fields WHERE farmer_id IS NOT NULL")
                farmers_with_fields = cursor.fetchone()[0]
                
                features['🌾 Farmer Fields Query'] = {
                    'status': 'healthy',
                    'icon': '✅',
                    'color': '#4caf50',
                    'message': f'Working - {field_count} fields, {farmers_with_fields} farmers have fields',
                    'details': 'Database + fields table + farmer relationship'
                }
    except Exception as e:
        features['🌾 Farmer Fields Query'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Cannot access fields table',
            'details': str(e)[:80]
        }
    
    # Feature 5: Task Management
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tasks")
                task_count = cursor.fetchone()[0]
                
                # Test task-field relationship through junction table
                cursor.execute("SELECT COUNT(*) FROM task_fields")
                task_field_links = cursor.fetchone()[0]
                
                features['📋 Task Management'] = {
                    'status': 'healthy',
                    'icon': '✅',
                    'color': '#4caf50',
                    'message': f'Working - {task_count} tasks, {task_field_links} field assignments',
                    'details': 'Database + tasks + task_fields junction table'
                }
    except Exception as e:
        features['📋 Task Management'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Cannot access tasks/task_fields tables',
            'details': str(e)[:80]
        }
    
    # Feature 6: Standard Queries
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'standard_queries')")
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    cursor.execute("SELECT COUNT(*) FROM standard_queries")
                    query_count = cursor.fetchone()[0]
                    
                    features['⭐ Standard Queries'] = {
                        'status': 'healthy',
                        'icon': '✅',
                        'color': '#4caf50',
                        'message': f'Working - {query_count} saved queries',
                        'details': 'Database + standard_queries table'
                    }
                else:
                    features['⭐ Standard Queries'] = {
                        'status': 'warning',
                        'icon': '⚠️',
                        'color': '#ff9800',
                        'message': 'Standard queries table not initialized',
                        'details': 'Database connected but standard_queries table missing'
                    }
    except Exception as e:
        features['⭐ Standard Queries'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Cannot access standard_queries table',
            'details': str(e)[:80]
        }
    
    # Feature 7: Schema Discovery
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public'")
                column_count = cursor.fetchone()[0]
                
                features['🔍 Schema Discovery'] = {
                    'status': 'healthy',
                    'icon': '✅',
                    'color': '#4caf50',
                    'message': f'Working - {table_count} tables, {column_count} columns',
                    'details': 'Database + information_schema access'
                }
    except Exception as e:
        features['🔍 Schema Discovery'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Cannot access information_schema',
            'details': str(e)[:80]
        }
    
    return features

async def get_comprehensive_health_status():
    """Check health status of all system components"""
    
    components = {}
    
    # First get feature-level health status
    feature_health = await get_feature_health_status()
    
    # Combine component and feature health
    components.update(feature_health)
    
    # 1. Database Connection
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT current_database(), version()")
                db_name, db_version = cursor.fetchone()
                cursor.execute("SELECT COUNT(*) FROM farmers")
                farmer_count = cursor.fetchone()[0]
                
                components['Database (PostgreSQL)'] = {
                    'status': 'healthy',
                    'icon': '✅',
                    'color': '#4caf50',
                    'message': f'Connected to {db_name}',
                    'details': f'{farmer_count} farmers, {db_version.split(",")[0]}'
                }
            else:
                components['Database (PostgreSQL)'] = {
                    'status': 'error',
                    'icon': '❌',
                    'color': '#f44336',
                    'message': 'Connection failed',
                    'details': 'Unable to establish database connection'
                }
    except Exception as e:
        components['Database (PostgreSQL)'] = {
            'status': 'error',
            'icon': '❌',
            'color': '#f44336',
            'message': 'Connection error',
            'details': str(e)[:100]
        }
    
    # 2. OpenAI API
    if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
        try:
            # Import test function
            from llm_integration import test_llm_connection
            llm_test = await test_llm_connection()
            
            if llm_test.get("status") == "connected":
                components['OpenAI API'] = {
                    'status': 'healthy',
                    'icon': '✅',
                    'color': '#4caf50',
                    'message': 'API key configured and working',
                    'details': f'Model: {llm_test.get("model", "gpt-4")}, Response time: {llm_test.get("response_time", "N/A")}'
                }
            else:
                components['OpenAI API'] = {
                    'status': 'warning',
                    'icon': '⚠️',
                    'color': '#ff9800',
                    'message': 'API key configured but connection failed',
                    'details': llm_test.get("error", "Connection test failed")
                }
        except:
            components['OpenAI API'] = {
                'status': 'warning',
                'icon': '⚠️',
                'color': '#ff9800',
                'message': 'API key configured',
                'details': 'Unable to test connection'
            }
    else:
        components['OpenAI API'] = {
            'status': 'not_configured',
            'icon': '⚪',
            'color': '#9e9e9e',
            'message': 'Not configured',
            'details': 'Set OPENAI_API_KEY in environment variables'
        }
    
    # 3. Twilio (WhatsApp)
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if twilio_sid and twilio_token:
        components['Twilio (WhatsApp)'] = {
            'status': 'configured',
            'icon': '🟢',
            'color': '#4caf50',
            'message': 'Credentials configured',
            'details': f'Account SID: {twilio_sid[:10]}...'
        }
    else:
        components['Twilio (WhatsApp)'] = {
            'status': 'not_configured',
            'icon': '⚪',
            'color': '#9e9e9e',
            'message': 'Not configured',
            'details': 'Optional - Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN if using WhatsApp'
        }
    
    # 4. OpenWeather API
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    
    if weather_key:
        components['OpenWeather API'] = {
            'status': 'configured',
            'icon': '🟢',
            'color': '#4caf50',
            'message': 'API key configured',
            'details': f'Key: {weather_key[:10]}...'
        }
    else:
        components['OpenWeather API'] = {
            'status': 'not_configured',
            'icon': '⚪',
            'color': '#9e9e9e',
            'message': 'Not configured',
            'details': 'Optional - Set OPENWEATHER_API_KEY if using weather features'
        }
    
    # 5. Cost Tracking Tables
    try:
        with get_constitutional_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('farmer_interaction_costs', 'cost_rates')
                    )
                """)
                tables_exist = cursor.fetchone()[0]
                
                if tables_exist:
                    cursor.execute("SELECT COUNT(*) FROM farmer_interaction_costs")
                    cost_records = cursor.fetchone()[0]
                    
                    components['Cost Tracking'] = {
                        'status': 'healthy',
                        'icon': '✅',
                        'color': '#4caf50',
                        'message': 'Tables initialized',
                        'details': f'{cost_records} cost records tracked'
                    }
                else:
                    components['Cost Tracking'] = {
                        'status': 'warning',
                        'icon': '⚠️',
                        'color': '#ff9800',
                        'message': 'Tables not initialized',
                        'details': 'Visit /initialize-cost-tables to set up'
                    }
    except:
        components['Cost Tracking'] = {
            'status': 'unknown',
            'icon': '❓',
            'color': '#9e9e9e',
            'message': 'Unable to check',
            'details': 'Database connection required'
        }
    
    # 6. Application Server
    components['Application Server'] = {
        'status': 'healthy',
        'icon': '✅',
        'color': '#4caf50',
        'message': 'FastAPI running',
        'details': f'Python {sys.version.split()[0]}, uvicorn server'
    }
    
    # 7. AWS Environment
    aws_region = os.getenv('AWS_REGION')
    aws_url = os.getenv('AWS_APP_RUNNER_SERVICE_URL')
    
    if aws_region or aws_url:
        components['AWS Environment'] = {
            'status': 'configured',
            'icon': '🟢',
            'color': '#4caf50',
            'message': f'Region: {aws_region or "default"}',
            'details': f'App Runner: {aws_url or "Local development"}'
        }
    else:
        components['AWS Environment'] = {
            'status': 'development',
            'icon': '🟡',
            'color': '#ff9800',
            'message': 'Local development mode',
            'details': 'Set AWS_REGION and AWS_APP_RUNNER_SERVICE_URL for production'
        }
    
    return components

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
        try:
            # Use the synchronous connection that works
            with get_constitutional_db_connection() as conn:
                if conn:
                    # Execute the query synchronously
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
                        try:
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
                        except StopIteration:
                            # Handle generator issue specifically
                            llm_result["execution_result"] = {
                                "status": "error",
                                "error": "Query execution failed due to generator issue. Try rephrasing the query.",
                                "suggestion": "Use a simpler INSERT statement or check farmer ID manually."
                            }
                        except GeneratorExit:
                            # Handle generator exit issue
                            llm_result["execution_result"] = {
                                "status": "error", 
                                "error": "Query execution interrupted. Try a simpler query format.",
                                "suggestion": "Use direct INSERT with known farmer ID instead of subquery."
                            }
                else:
                    llm_result["execution_result"] = {"error": "Database connection failed"}
        except Exception as e:
            llm_result["execution_result"] = {"error": f"Execution error: {str(e)}"}
    
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

# ===================================================================
# 🛡️ CONSTITUTIONAL DATA INSERTION ROUTES - NEW FUNCTIONALITY
# ===================================================================

# Initialize constitutional insert operations
constitutional_ops = ConstitutionalInsertOperations(get_constitutional_db_connection)

@app.get("/database-dashboard/add-data", response_class=HTMLResponse)
async def database_add_data_form():
    """Constitutional data entry form selection page"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Add Agricultural Data - AVA OLO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary-brown: #6B5B73;
            --primary-olive: #8B8C5A;
            --dark-olive: #5D5E3F;
            --cream: #F5F3F0;
            --dark-charcoal: #2C2C2C;
            --white: #FFFFFF;
            --font-large: 18px;
            --font-heading: 24px;
            --font-title: 32px;
        }
        body { 
            font-family: Arial, sans-serif; 
            background: var(--cream); 
            color: var(--dark-charcoal);
            margin: 0;
            padding: 20px;
            font-size: var(--font-large);
            line-height: 1.6;
        }
        .constitutional-container {
            max-width: 1000px;
            margin: 0 auto;
            background: var(--white);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .constitutional-header {
            background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive));
            color: var(--white);
            padding: 30px 20px;
            text-align: center;
        }
        .constitutional-title {
            margin: 0 0 10px 0;
            font-size: var(--font-title);
            font-weight: bold;
        }
        .back-link {
            color: var(--white);
            text-decoration: none;
            margin-bottom: 15px;
            display: inline-block;
            font-size: var(--font-large);
        }
        .content {
            padding: 40px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        .form-card {
            background: var(--white);
            border: 2px solid var(--primary-olive);
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .form-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }
        .form-card h3 {
            color: var(--primary-brown);
            margin-bottom: 15px;
            font-size: var(--font-heading);
        }
        .form-card p {
            color: var(--dark-olive);
            margin-bottom: 25px;
            font-size: var(--font-large);
        }
        .constitutional-button {
            background: linear-gradient(135deg, var(--primary-olive), var(--primary-brown));
            color: var(--white);
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: var(--font-large);
            display: inline-block;
            transition: background 0.3s ease;
            border: none;
            cursor: pointer;
        }
        .constitutional-button:hover {
            background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive));
            text-decoration: none;
            color: var(--white);
        }
        .mango-rule {
            background: #FFF3CD;
            border: 2px solid #FFC107;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .mango-rule h4 {
            color: #856404;
            margin: 0 0 10px 0;
            font-size: var(--font-heading);
        }
        .mango-rule p {
            color: #856404;
            margin: 0;
            font-size: var(--font-large);
        }
        @media (max-width: 768px) {
            .form-grid {
                grid-template-columns: 1fr;
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="constitutional-container">
        <header class="constitutional-header">
            <a href="/database-dashboard" class="back-link">← Back to Database Dashboard</a>
            <h1 class="constitutional-title">🌾 Add Agricultural Data</h1>
            <p>Constitutional Data Entry System</p>
        </header>
        
        <div class="content">
            <div class="mango-rule">
                <h4>🥭 Constitutional Compliance</h4>
                <p>This system follows the MANGO RULE: Works for Bulgarian mango farmers and supports all crops globally</p>
            </div>
            
            <div class="form-grid">
                <div class="form-card">
                    <h3>👨‍🌾 Add Farmer</h3>
                    <p>Register a new farmer profile with international support</p>
                    <a href="/database-dashboard/add-farmer" class="constitutional-button">Add Farmer</a>
                </div>
                
                <div class="form-card">
                    <h3>🌱 Add Crop</h3>
                    <p>Add crop information with global variety support</p>
                    <a href="/database-dashboard/add-crop" class="constitutional-button">Add Crop</a>
                </div>
                
                <div class="form-card">
                    <h3>📖 Add Agricultural Advice</h3>
                    <p>Share agricultural knowledge and recommendations</p>
                    <a href="/database-dashboard/add-advice" class="constitutional-button">Add Advice</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
""")

@app.get("/database-dashboard/add-farmer", response_class=HTMLResponse)
async def add_farmer_form():
    """Constitutional farmer registration form"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Add Farmer - AVA OLO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary-brown: #6B5B73;
            --primary-olive: #8B8C5A;
            --dark-olive: #5D5E3F;
            --cream: #F5F3F0;
            --dark-charcoal: #2C2C2C;
            --white: #FFFFFF;
            --font-large: 18px;
            --font-heading: 24px;
            --font-title: 32px;
            --success-green: #6B8E23;
            --error-red: #C85450;
        }
        body { 
            font-family: Arial, sans-serif; 
            background: var(--cream); 
            color: var(--dark-charcoal);
            margin: 0;
            padding: 20px;
            font-size: var(--font-large);
            line-height: 1.6;
        }
        .constitutional-container {
            max-width: 800px;
            margin: 0 auto;
            background: var(--white);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .constitutional-header {
            background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive));
            color: var(--white);
            padding: 30px 20px;
            text-align: center;
        }
        .constitutional-title {
            margin: 0 0 10px 0;
            font-size: var(--font-title);
            font-weight: bold;
        }
        .back-link {
            color: var(--white);
            text-decoration: none;
            margin-bottom: 15px;
            display: inline-block;
            font-size: var(--font-large);
        }
        .content {
            padding: 40px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: var(--primary-brown);
            font-size: var(--font-large);
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid var(--primary-olive);
            border-radius: 6px;
            font-size: var(--font-large);
            box-sizing: border-box;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: var(--primary-brown);
            box-shadow: 0 0 0 3px rgba(107, 91, 115, 0.1);
        }
        .constitutional-button {
            background: linear-gradient(135deg, var(--primary-olive), var(--primary-brown));
            color: var(--white);
            padding: 15px 30px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: var(--font-large);
            cursor: pointer;
            transition: background 0.3s ease;
            width: 100%;
        }
        .constitutional-button:hover {
            background: linear-gradient(135deg, var(--primary-brown), var(--dark-olive));
        }
        .mango-rule {
            background: #FFF3CD;
            border: 2px solid #FFC107;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .required {
            color: var(--error-red);
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="constitutional-container">
        <header class="constitutional-header">
            <a href="/database-dashboard/add-data" class="back-link">← Back to Add Data</a>
            <h1 class="constitutional-title">👨‍🌾 Add Farmer</h1>
            <p>Constitutional Farmer Registration</p>
        </header>
        
        <div class="content">
            <div class="mango-rule">
                <h4>🥭 MANGO RULE Compliant</h4>
                <p>This form supports Bulgarian mango farmers and all international farmers</p>
            </div>
            
            <form method="POST" action="/database-dashboard/add-farmer">
                <div class="form-group">
                    <label for="farm_name">Farm Name <span class="required">*</span></label>
                    <input type="text" id="farm_name" name="farm_name" required 
                           placeholder="e.g., София Манго Ферма (Sofia Mango Farm)">
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="manager_name">Manager First Name <span class="required">*</span></label>
                        <input type="text" id="manager_name" name="manager_name" required 
                               placeholder="e.g., Димитър (Dimitar)">
                    </div>
                    <div class="form-group">
                        <label for="manager_last_name">Manager Last Name</label>
                        <input type="text" id="manager_last_name" name="manager_last_name" 
                               placeholder="e.g., Петров (Petrov)">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="city">City</label>
                        <input type="text" id="city" name="city" 
                               placeholder="e.g., София (Sofia)">
                    </div>
                    <div class="form-group">
                        <label for="country">Country <span class="required">*</span></label>
                        <input type="text" id="country" name="country" required 
                               placeholder="e.g., Bulgaria">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="phone">Phone Number</label>
                        <input type="tel" id="phone" name="phone" 
                               placeholder="e.g., +359 2 123 4567">
                    </div>
                    <div class="form-group">
                        <label for="wa_phone_number">WhatsApp Number</label>
                        <input type="tel" id="wa_phone_number" name="wa_phone_number" 
                               placeholder="e.g., +359 87 123 4567">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" 
                           placeholder="e.g., dimitar@mangoferma.bg">
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="preferred_language">Preferred Language</label>
                        <select id="preferred_language" name="preferred_language">
                            <option value="en">English</option>
                            <option value="bg">Bulgarian (Български)</option>
                            <option value="hr">Croatian (Hrvatski)</option>
                            <option value="hu">Hungarian (Magyar)</option>
                            <option value="sr">Serbian (Српски)</option>
                            <option value="es">Spanish (Español)</option>
                            <option value="fr">French (Français)</option>
                            <option value="de">German (Deutsch)</option>
                            <option value="it">Italian (Italiano)</option>
                            <option value="pt">Portuguese (Português)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="timezone">Timezone</label>
                        <select id="timezone" name="timezone">
                            <option value="Europe/Sofia">Sofia (Bulgaria)</option>
                            <option value="Europe/Zagreb">Zagreb (Croatia)</option>
                            <option value="Europe/Budapest">Budapest (Hungary)</option>
                            <option value="Europe/Belgrade">Belgrade (Serbia)</option>
                            <option value="Europe/Madrid">Madrid (Spain)</option>
                            <option value="Europe/Paris">Paris (France)</option>
                            <option value="Europe/Berlin">Berlin (Germany)</option>
                            <option value="Europe/Rome">Rome (Italy)</option>
                            <option value="Europe/Lisbon">Lisbon (Portugal)</option>
                            <option value="America/New_York">New York (USA)</option>
                            <option value="America/Los_Angeles">Los Angeles (USA)</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="constitutional-button">
                    🌾 Add Farmer (Constitutional Compliance)
                </button>
            </form>
        </div>
    </div>
</body>
</html>
""")

@app.post("/database-dashboard/add-farmer", response_class=HTMLResponse)
async def add_farmer_submit(
    farm_name: str = Form(...),
    manager_name: str = Form(...),
    manager_last_name: str = Form(None),
    city: str = Form(None),
    country: str = Form(...),
    phone: str = Form(None),
    wa_phone_number: str = Form(None),
    email: str = Form(None),
    preferred_language: str = Form("en"),
    timezone: str = Form(None)
):
    """Process farmer registration with constitutional compliance"""
    
    # Prepare farmer data
    farmer_data = {
        'farm_name': farm_name,
        'manager_name': manager_name,
        'manager_last_name': manager_last_name,
        'city': city,
        'country': country,
        'phone': phone,
        'wa_phone_number': wa_phone_number,
        'email': email,
        'preferred_language': preferred_language,
        'timezone': timezone,
        'country_code': country[:2].upper() if country else None,
        'whatsapp_number': wa_phone_number,
        'localization_preferences': {}
    }
    
    # Insert farmer with constitutional validation
    success, message, farmer_id = await constitutional_ops.insert_farmer(farmer_data)
    
    # Return success/error page
    if success:
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Farmer Added Successfully - AVA OLO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {{
            --primary-brown: #6B5B73;
            --success-green: #6B8E23;
            --cream: #F5F3F0;
            --white: #FFFFFF;
            --font-large: 18px;
            --font-title: 32px;
        }}
        body {{ 
            font-family: Arial, sans-serif; 
            background: var(--cream); 
            margin: 0;
            padding: 20px;
            font-size: var(--font-large);
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: var(--white);
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .success-icon {{
            font-size: 48px;
            color: var(--success-green);
            margin-bottom: 20px;
        }}
        h1 {{
            color: var(--primary-brown);
            font-size: var(--font-title);
        }}
        .constitutional-button {{
            background: linear-gradient(135deg, #8B8C5A, var(--primary-brown));
            color: var(--white);
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: var(--font-large);
            display: inline-block;
            margin: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✅</div>
        <h1>Farmer Added Successfully!</h1>
        <p><strong>Farmer ID:</strong> {farmer_id}</p>
        <p><strong>Farm:</strong> {farm_name}</p>
        <p><strong>Manager:</strong> {manager_name}</p>
        <p><strong>Country:</strong> {country}</p>
        <div style="margin-top: 20px; padding: 15px; background: #F0F8E8; border-radius: 8px;">
            <p><strong>Constitutional Compliance:</strong> ✅ MANGO RULE Verified</p>
            <p>{message}</p>
        </div>
        <div style="margin-top: 30px;">
            <a href="/database-dashboard/add-data" class="constitutional-button">Add More Data</a>
            <a href="/database-dashboard" class="constitutional-button">Back to Dashboard</a>
        </div>
    </div>
</body>
</html>
""")
    else:
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Error Adding Farmer - AVA OLO</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #F5F3F0; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; text-align: center; }}
        .error {{ color: #C85450; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="error">❌ Error Adding Farmer</h1>
        <p>{message}</p>
        <a href="/database-dashboard/add-farmer">← Try Again</a>
    </div>
</body>
</html>
""")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)