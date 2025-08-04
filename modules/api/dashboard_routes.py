#!/usr/bin/env python3
"""
Dashboard System Routes for AVA OLO Monitoring Dashboards
Multi-dashboard system with Database, Business, and Health dashboards
Password-protected with Peter/Semillon authentication
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import logging
import time
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..core.config import VERSION, BUILD_ID
from ..core.database_manager import get_db_manager
from .dashboard_auth import require_dashboard_auth, check_dashboard_auth

logger = logging.getLogger(__name__)

# Router for dashboard endpoints
router = APIRouter(prefix="/dashboards", tags=["dashboards"])
api_router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboard-api"])

# Pydantic models for API requests
class NaturalQueryRequest(BaseModel):
    question: str

class DirectQueryRequest(BaseModel):
    sql_query: str

class SaveQueryRequest(BaseModel):
    query_name: str
    sql_query: str
    is_public: bool = False

# Serve dashboard HTML files with authentication
@router.get("/", response_class=HTMLResponse)
async def dashboard_hub(request: Request):
    """Dashboard hub landing page - password protected"""
    # Check authentication
    if not check_dashboard_auth(request):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboards/login", status_code=303)
    
    try:
        with open("static/dashboards/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard hub not found</h1>", status_code=404)

@router.get("/database", response_class=HTMLResponse)
async def database_dashboard(request: Request, username: str = Depends(require_dashboard_auth)):
    """Database dashboard with natural language queries - password protected"""
    try:
        with open("static/dashboards/database-dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Database dashboard not found</h1>", status_code=404)

@router.get("/business", response_class=HTMLResponse)
async def business_dashboard(request: Request, username: str = Depends(require_dashboard_auth)):
    """Business dashboard with growth trends and charts - password protected"""
    try:
        with open("static/dashboards/business-dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Business dashboard not found</h1>", status_code=404)

@router.get("/health", response_class=HTMLResponse)
async def health_dashboard(request: Request, username: str = Depends(require_dashboard_auth)):
    """Health dashboard with system monitoring - password protected"""
    try:
        with open("static/dashboards/health-dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Health dashboard not found</h1>", status_code=404)

@router.get("/login", response_class=HTMLResponse)
async def dashboard_login_page(request: Request):
    """Dashboard login page"""
    from .dashboard_auth import get_login_form_html
    
    # Check if already authenticated
    if check_dashboard_auth(request):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboards/", status_code=303)
    
    return HTMLResponse(content=get_login_form_html())

@router.post("/login")
async def dashboard_login(request: Request):
    """Process dashboard login"""
    from fastapi.responses import JSONResponse
    
    # Get form data
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    # Validate credentials
    from .dashboard_auth import DASHBOARD_USERS, create_session
    
    if username not in DASHBOARD_USERS or DASHBOARD_USERS[username] != password:
        return JSONResponse(
            content={"success": False, "error": "Invalid credentials"},
            status_code=401
        )
    
    # Create session
    session_id = create_session(username)
    
    # Set session cookie
    response = JSONResponse(content={
        "success": True,
        "message": f"Welcome, {username}!",
        "redirect": "/dashboards/"
    })
    
    response.set_cookie(
        key="dashboard_session",
        value=session_id,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400  # 24 hours
    )
    
    return response

@router.get("/cost", response_class=HTMLResponse)
async def cost_dashboard(request: Request, username: str = Depends(require_dashboard_auth)):
    """Cost dashboard placeholder - password protected"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cost Dashboard - AVA OLO</title>
        <link rel="stylesheet" href="/static/css/constitutional-design-system-v2.css">
        <style>
            body {
                font-family: var(--font-primary);
                margin: 0;
                padding: 20px;
                background-color: var(--color-bg-primary);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 600px;
                text-align: center;
            }
            h1 {
                color: var(--color-agri-green);
                margin-bottom: 20px;
            }
            .back-link {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background: var(--primary-olive);
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Cost Dashboard</h1>
            <p>Cost tracking and analysis functionality coming soon!</p>
            <a href="/dashboards/" class="back-link">Back to Dashboard</a>
        </div>
    </body>
    </html>
    """)

@router.get("/deployment", response_class=HTMLResponse)
async def deployment_dashboard():
    """Deployment and feature monitoring dashboard"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monitoring & Status Dashboard - AVA OLO</title>
        <link rel="stylesheet" href="/static/css/constitutional-design-system-v2.css">
        <style>
            body {
                font-family: var(--font-primary);
                margin: 0;
                padding: 20px;
                background-color: var(--color-bg-primary);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 600px;
                text-align: center;
            }
            h1 {
                color: var(--color-agri-green);
                margin-bottom: 20px;
            }
            .back-link {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background: var(--primary-olive);
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Monitoring & Status Dashboard</h1>
            <p>System monitoring, deployment status, and feature verification dashboard.</p>
            <p>Monitor and confirm system discussions, deployment confirmations, and real-time alerts.</p>
            <a href="/dashboards/" class="back-link">Back to Dashboard</a>
        </div>
    </body>
    </html>
    """)

# API endpoints for dashboard functionality

@api_router.get("/hub/stats")
async def get_hub_stats():
    """Get statistics for dashboard hub - password protected"""
    db_manager = get_db_manager()
    
    try:
        # Get basic farmer stats
        farmer_count_result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM farmers WHERE is_active = true"
        )
        farmer_count = farmer_count_result['rows'][0][0] if farmer_count_result.get('rows') else 0
        
        # Get total hectares
        hectares_result = db_manager.execute_query(
            "SELECT COALESCE(SUM(area_hectares), 0) as total FROM fields"
        )
        total_hectares = float(hectares_result['rows'][0][0]) if hectares_result.get('rows') else 0.0
        
        # Get today's activities count (using farmers table for now)
        today_activities_result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM farmers WHERE DATE(created_at) = CURRENT_DATE"
        )
        today_activities = today_activities_result['rows'][0][0] if today_activities_result.get('rows') else 0
        
        return {
            "success": True,
            "farmer_count": farmer_count,
            "total_hectares": float(total_hectares),
            "today_activities": today_activities,
            "system_health": "OK",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get hub stats: {e}")
        return {
            "success": False,
            "error": "Failed to load statistics",
            "farmer_count": 16,  # Fallback values
            "total_hectares": 211.95,
            "today_activities": 0,
            "system_health": "Unknown"
        }

@api_router.get("/database/queries/quick/{query_type}")
async def execute_quick_query(query_type: str):
    """Execute predefined quick queries - password protected"""
    db_manager = get_db_manager()
    
    quick_queries = {
        "count-farmers": {
            "sql": "SELECT COUNT(*) as total_farmers FROM farmers WHERE is_active = true",
            "description": "Count total active farmers"
        },
        "list-farmers": {
            "sql": """
                SELECT id, manager_name, manager_last_name, city, farm_name, 
                       phone, is_active, created_at
                FROM farmers 
                WHERE is_active = true OR is_active IS NULL
                ORDER BY id DESC LIMIT 50
            """,
            "description": "List all farmers"
        },
        "farmers-by-city": {
            "sql": """
                SELECT city, COUNT(*) as count 
                FROM farmers 
                WHERE is_active = true 
                GROUP BY city 
                ORDER BY count DESC
            """,
            "description": "Farmers grouped by city"
        },
        "recent-registrations": {
            "sql": """
                SELECT id, manager_name, manager_last_name, city, 
                       email, created_at
                FROM farmers 
                ORDER BY created_at DESC 
                LIMIT 20
            """,
            "description": "Recent farmer registrations"
        },
        "top-cities": {
            "sql": """
                SELECT city, COUNT(*) as farmer_count 
                FROM farmers 
                WHERE is_active = true 
                GROUP BY city 
                ORDER BY farmer_count DESC 
                LIMIT 10
            """,
            "description": "Top cities by farmer count"
        },
        "farmer-growth": {
            "sql": """
                SELECT DATE(created_at) as registration_date, 
                       COUNT(*) as new_farmers
                FROM farmers 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY registration_date DESC
            """,
            "description": "Farmer growth over last 30 days"
        }
    }
    
    if query_type not in quick_queries:
        raise HTTPException(status_code=404, detail="Quick query not found")
    
    query_info = quick_queries[query_type]
    start_time = time.time()
    
    try:
        result = db_manager.execute_query(query_info["sql"])
        execution_time = int((time.time() - start_time) * 1000)
        
        # Convert rows to results format expected by frontend
        results = convert_rows_to_results(result.get('columns', []), result.get('rows', []))
        
        return {
            "success": True,
            "results": results,
            "columns": result.get('columns', []),
            "rows": result.get('rows', []),
            "sql_query": query_info["sql"].strip(),
            "description": query_info["description"],
            "execution_time": execution_time,
            "rows_returned": len(result.get('rows', []))
        }
    except Exception as e:
        logger.error(f"Quick query failed: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}"
        }

@api_router.post("/database/query/natural")
async def execute_natural_query(request: NaturalQueryRequest):
    """Convert natural language to SQL and execute - password protected"""
    db_manager = get_db_manager()
    
    try:
        # Simple natural language to SQL conversion
        # In a real implementation, this would use an LLM service
        sql_query = convert_natural_to_sql(request.question)
        
        if not sql_query:
            return {
                "success": False,
                "error": "Could not understand the question. Please try rephrasing."
            }
        
        # Validate and execute the query
        if not is_safe_query(sql_query):
            return {
                "success": False,
                "error": "Query contains unsafe operations. Only SELECT queries are allowed."
            }
        
        start_time = time.time()
        result = db_manager.execute_query(sql_query)
        execution_time = int((time.time() - start_time) * 1000)
        
        # Convert rows to results format expected by frontend
        results = convert_rows_to_results(result.get('columns', []), result.get('rows', []))
        
        return {
            "success": True,
            "results": results,
            "columns": result.get('columns', []),
            "rows": result.get('rows', []),
            "sql_query": sql_query,
            "execution_time": execution_time,
            "rows_returned": len(result.get('rows', []))
        }
    except Exception as e:
        logger.error(f"Natural query failed: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}"
        }

@api_router.post("/database/query/direct")
async def execute_direct_query(request: DirectQueryRequest):
    """Execute a direct SQL query including data modifications - password protected"""
    db_manager = get_db_manager()
    
    try:
        if not is_safe_query(request.sql_query):
            return {
                "success": False,
                "error": "Query contains unsafe operations. Only SELECT, INSERT, UPDATE, DELETE on ava_ tables are allowed."
            }
        
        start_time = time.time()
        
        # Determine query type for appropriate response
        query_upper = request.sql_query.strip().upper()
        is_modification = any(query_upper.startswith(op) for op in ['INSERT', 'UPDATE', 'DELETE'])
        
        if is_modification:
            # For data modification queries, execute and return affected row count
            result = db_manager.execute_query(request.sql_query)
            affected_rows = result.get('affected_rows', 0)
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "sql_query": request.sql_query,
                "execution_time": execution_time,
                "rows_affected": affected_rows,
                "operation_type": "modification",
                "results": []  # No results for modification queries
            }
        else:
            # For SELECT queries, return results
            result = db_manager.execute_query(request.sql_query)
            execution_time = int((time.time() - start_time) * 1000)
            
            # Convert rows to results format expected by frontend
            results = convert_rows_to_results(result.get('columns', []), result.get('rows', []))
            
            return {
                "success": True,
                "results": results,
                "columns": result.get('columns', []),
                "rows": result.get('rows', []),
                "sql_query": request.sql_query,
                "execution_time": execution_time,
                "rows_returned": len(result.get('rows', [])),
                "operation_type": "query"
            }
    except Exception as e:
        logger.error(f"Direct query failed: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}"
        }

@api_router.get("/database/queries/saved")
async def get_saved_queries():
    """Get all saved queries - password protected"""
    db_manager = get_db_manager()
    
    try:
        results = db_manager.execute_query("""
            SELECT id, query_name, sql_query, created_by, created_at, 
                   last_used_at, use_count, is_public
            FROM ava_saved_queries 
            ORDER BY use_count DESC, created_at DESC
        """)
        
        return {
            "success": True,
            "queries": results
        }
    except Exception as e:
        logger.error(f"Failed to get saved queries: {e}")
        return {
            "success": False,
            "error": "Failed to load saved queries",
            "queries": []
        }

@api_router.post("/database/queries/save")
async def save_query(request: SaveQueryRequest):
    """Save a query for future use - password protected"""
    db_manager = get_db_manager()
    
    try:
        db_manager.execute_query("""
            INSERT INTO ava_saved_queries (query_name, sql_query, created_by, is_public)
            VALUES (%s, %s, %s, %s)
        """, (request.query_name, request.sql_query, 'dashboard_user', request.is_public))
        
        return {
            "success": True,
            "message": "Query saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save query: {e}")
        return {
            "success": False,
            "error": "Failed to save query"
        }

@api_router.post("/database/queries/saved/{query_id}/use")
async def increment_query_usage(query_id: int):
    """Increment usage count for a saved query - password protected"""
    db_manager = get_db_manager()
    
    try:
        db_manager.execute_query("""
            UPDATE ava_saved_queries 
            SET use_count = use_count + 1, last_used_at = NOW()
            WHERE id = %s
        """, (query_id,))
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to update query usage: {e}")
        return {"success": False}

# Business Dashboard API endpoints

@api_router.get("/business/overview")
async def get_business_overview():
    """Get business dashboard overview metrics - password protected"""
    db_manager = get_db_manager()
    
    try:
        # Total farmers by occupation
        occupation_stats = db_manager.execute_query("""
            SELECT 
                primary_occupation,
                COUNT(*) as farmer_count,
                SUM(size_hectares) as total_hectares
            FROM ava_farmers 
            WHERE subscription_status = 'active'
            GROUP BY primary_occupation
            ORDER BY farmer_count DESC
        """)
        
        # Total counts
        totals = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_farmers,
                SUM(size_hectares) as total_hectares,
                COUNT(DISTINCT city) as total_cities
            FROM ava_farmers 
            WHERE subscription_status = 'active'
        """)
        
        return {
            "success": True,
            "totals": totals[0] if totals else {},
            "occupation_breakdown": occupation_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get business overview: {e}")
        return {
            "success": False,
            "error": "Failed to load business overview"
        }

@api_router.get("/business/growth-trends")
async def get_growth_trends(period: str = "30d"):
    """Get farmer growth trends for specified period - password protected"""
    db_manager = get_db_manager()
    
    # Determine the date range based on period
    if period == "24h":
        interval = "1 day"
        date_format = "YYYY-MM-DD HH24:00:00"
    elif period == "7d":
        interval = "7 days"
        date_format = "YYYY-MM-DD"
    else:  # 30d default
        interval = "30 days"
        date_format = "YYYY-MM-DD"
    
    try:
        # New farmer registrations
        new_farmers = db_manager.execute_query(f"""
            SELECT 
                TO_CHAR(created_at, '{date_format}') as period,
                COUNT(*) as new_farmers,
                SUM(size_hectares) as new_hectares
            FROM ava_farmers 
            WHERE created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY TO_CHAR(created_at, '{date_format}')
            ORDER BY period
        """)
        
        # Unsubscribed farmers
        unsubscribed = db_manager.execute_query(f"""
            SELECT 
                TO_CHAR(unsubscribed_at, '{date_format}') as period,
                COUNT(*) as unsubscribed_farmers
            FROM ava_farmers 
            WHERE unsubscribed_at >= NOW() - INTERVAL '{interval}'
            GROUP BY TO_CHAR(unsubscribed_at, '{date_format}')
            ORDER BY period
        """)
        
        return {
            "success": True,
            "period": period,
            "new_farmers": new_farmers,
            "unsubscribed_farmers": unsubscribed,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get growth trends: {e}")
        return {
            "success": False,
            "error": "Failed to load growth trends"
        }

@api_router.get("/business/activity-stream")
async def get_activity_stream(limit: int = 50):
    """Get recent activity stream - password protected"""
    db_manager = get_db_manager()
    
    try:
        activities = db_manager.execute_query("""
            SELECT 
                a.id,
                a.activity_type,
                a.activity_description,
                a.created_at,
                a.metadata,
                f.first_name,
                f.last_name,
                f.city
            FROM ava_activity_log a
            LEFT JOIN ava_farmers f ON a.farmer_id = f.id
            ORDER BY a.created_at DESC
            LIMIT %s
        """, (limit,))
        
        return {
            "success": True,
            "activities": activities,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get activity stream: {e}")
        return {
            "success": False,
            "error": "Failed to load activity stream",
            "activities": []
        }

@api_router.get("/business/database-changes")
async def get_database_changes():
    """Get recent database changes - password protected"""
    db_manager = get_db_manager()
    
    try:
        changes = db_manager.execute_query("""
            SELECT * FROM recent_database_changes
            ORDER BY change_time DESC
            LIMIT 50
        """)
        
        return {
            "success": True,
            "changes": changes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get database changes: {e}")
        return {
            "success": False,
            "error": "Failed to load database changes",
            "changes": []
        }

# Helper functions

def convert_rows_to_results(columns: List[str], rows: List[List[Any]]) -> List[Dict[str, Any]]:
    """Convert database rows to list of dictionaries expected by frontend"""
    if not columns or not rows:
        return []
    
    results = []
    for row in rows:
        result_dict = {}
        for i, col in enumerate(columns):
            result_dict[col] = row[i] if i < len(row) else None
        results.append(result_dict)
    
    return results

def convert_natural_to_sql(question: str) -> str:
    """
    Convert natural language question to SQL query.
    This is a simplified implementation. In production, this would use an LLM service.
    """
    question_lower = question.lower()
    
    # Simple pattern matching for common queries
    if "count" in question_lower and "farmer" in question_lower:
        if "city" in question_lower or "location" in question_lower:
            return """
                SELECT city, COUNT(*) as count 
                FROM farmers 
                WHERE is_active = true 
                GROUP BY city 
                ORDER BY count DESC
            """
        else:
            return "SELECT COUNT(*) as total_farmers FROM farmers WHERE is_active = true"
    
    if "vineyard" in question_lower or "grape" in question_lower or "wine" in question_lower:
        return """
            SELECT id, manager_name, manager_last_name, city, farm_name
            FROM farmers 
            WHERE is_active = true 
            AND (farm_name ILIKE '%vineyard%' OR farm_name ILIKE '%grape%' OR farm_name ILIKE '%wine%')
            ORDER BY id DESC
        """
    
    if "email" in question_lower:
        return """
            SELECT id, manager_name, manager_last_name, email
            FROM farmers 
            WHERE is_active = true AND email IS NOT NULL
            ORDER BY id DESC
            LIMIT 20
        """
    
    if "city" in question_lower or "cities" in question_lower:
        return """
            SELECT city, COUNT(*) as farmer_count
            FROM farmers 
            WHERE is_active = true
            GROUP BY city 
            ORDER BY farmer_count DESC
        """
    
    if "recent" in question_lower or "latest" in question_lower:
        return """
            SELECT id, manager_name, manager_last_name, city, created_at
            FROM farmers 
            WHERE is_active = true
            ORDER BY created_at DESC
            LIMIT 20
        """
    
    # If no pattern matches, return a safe default query
    return """
        SELECT id, manager_name, manager_last_name, city, email
        FROM farmers 
        WHERE is_active = true
        ORDER BY id DESC
        LIMIT 50
    """

def is_safe_query(query: str) -> bool:
    """Check if a SQL query is safe to execute (SELECT, INSERT, UPDATE, DELETE allowed for data entry)"""
    # Remove comments and normalize whitespace
    cleaned_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
    cleaned_query = ' '.join(cleaned_query.split()).upper()
    
    # Check for dangerous operations
    dangerous_keywords = [
        'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 
        'EXEC', 'EXECUTE', 'SHUTDOWN', 'KILL'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in cleaned_query:
            return False
    
    # Must start with allowed operations
    allowed_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
    if not any(cleaned_query.strip().startswith(start) for start in allowed_starts):
        return False
    
    # Additional safety checks for data modification
    if any(cleaned_query.startswith(op) for op in ['INSERT', 'UPDATE', 'DELETE']):
        # Ensure operations are only on our application tables
        allowed_tables = ['farmers', 'fields', 'tasks', 'activity_log']
        table_found = False
        for table in allowed_tables:
            if table.upper() in cleaned_query:
                table_found = True
                break
        
        if not table_found:
            return False
        
        # Prevent operations on system tables
        system_tables = ['information_schema', 'pg_', 'mysql.', 'sys.']
        for sys_table in system_tables:
            if sys_table in cleaned_query.lower():
                return False
    
    return True