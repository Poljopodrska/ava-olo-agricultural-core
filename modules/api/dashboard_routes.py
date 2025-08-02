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
from .dashboard_auth import require_dashboard_auth, check_dashboard_auth, get_login_form_html

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
async def dashboard_hub(username: str = Depends(authenticate_dashboard)):
    """Dashboard hub landing page - password protected with Peter/Semillon"""
    # User is authenticated, serve the dashboard hub
    try:
        with open("static/dashboards/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard hub not found</h1>", status_code=404)

@router.get("/database", response_class=HTMLResponse)
async def database_dashboard(username: str = Depends(authenticate_dashboard)):
    """Database dashboard with natural language queries - password protected"""
    try:
        with open("static/dashboards/database-dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Database dashboard not found</h1>", status_code=404)

@router.get("/business", response_class=HTMLResponse)
async def business_dashboard(username: str = Depends(authenticate_dashboard)):
    """Business dashboard with growth trends and charts - password protected"""
    try:
        with open("static/dashboards/business-dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Business dashboard not found</h1>", status_code=404)

@router.get("/health", response_class=HTMLResponse)
async def health_dashboard(username: str = Depends(authenticate_dashboard)):
    """Health dashboard with system monitoring - password protected"""
    try:
        with open("static/dashboards/health-dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Health dashboard not found</h1>", status_code=404)

@router.get("/cost", response_class=HTMLResponse)
async def cost_dashboard(username: str = Depends(authenticate_dashboard)):
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
            <a href="/" class="back-link">Back to Dashboard</a>
        </div>
    </body>
    </html>
    """)

# API endpoints for dashboard functionality

@api_router.get("/hub/stats")
async def get_hub_stats(username: str = Depends(authenticate_dashboard)):
    """Get statistics for dashboard hub - password protected"""
    db_manager = get_db_manager()
    
    try:
        # Get basic farmer stats
        farmer_count_result = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM ava_farmers WHERE subscription_status = 'active'"
        )
        farmer_count = farmer_count_result[0]['count'] if farmer_count_result else 0
        
        # Get total hectares
        hectares_result = await db_manager.execute_query(
            "SELECT SUM(size_hectares) as total FROM ava_farmers WHERE subscription_status = 'active'"
        )
        total_hectares = hectares_result[0]['total'] if hectares_result and hectares_result[0]['total'] else 0
        
        # Get today's activities
        today_activities_result = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM ava_activity_log WHERE DATE(created_at) = CURRENT_DATE"
        )
        today_activities = today_activities_result[0]['count'] if today_activities_result else 0
        
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
async def execute_quick_query(query_type: str, username: str = Depends(authenticate_dashboard)):
    """Execute predefined quick queries - password protected"""
    db_manager = get_db_manager()
    
    quick_queries = {
        "count-farmers": {
            "sql": "SELECT COUNT(*) as total_farmers FROM ava_farmers WHERE subscription_status = 'active'",
            "description": "Count total active farmers"
        },
        "list-farmers": {
            "sql": """
                SELECT id, first_name, last_name, city, primary_occupation, 
                       size_hectares, created_at
                FROM ava_farmers 
                WHERE subscription_status = 'active'
                ORDER BY id DESC LIMIT 50
            """,
            "description": "List all farmers"
        },
        "farmers-by-occupation": {
            "sql": """
                SELECT primary_occupation, COUNT(*) as count 
                FROM ava_farmers 
                WHERE subscription_status = 'active' 
                GROUP BY primary_occupation 
                ORDER BY count DESC
            """,
            "description": "Farmers grouped by occupation"
        },
        "recent-activities": {
            "sql": """
                SELECT a.*, f.first_name, f.last_name 
                FROM ava_activity_log a 
                LEFT JOIN ava_farmers f ON a.farmer_id = f.id 
                ORDER BY a.created_at DESC 
                LIMIT 20
            """,
            "description": "Recent farmer activities"
        },
        "top-cities": {
            "sql": """
                SELECT city, COUNT(*) as farmer_count 
                FROM ava_farmers 
                WHERE subscription_status = 'active' 
                GROUP BY city 
                ORDER BY farmer_count DESC 
                LIMIT 10
            """,
            "description": "Top cities by farmer count"
        },
        "farmer-growth": {
            "sql": """
                SELECT DATE(created_at) as registration_date, 
                       COUNT(*) as new_farmers,
                       SUM(size_hectares) as total_hectares_added
                FROM ava_farmers 
                WHERE created_at >= NOW() - INTERVAL '30 days'
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
        results = await db_manager.execute_query(query_info["sql"])
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "results": results,
            "sql_query": query_info["sql"].strip(),
            "description": query_info["description"],
            "execution_time": execution_time,
            "rows_returned": len(results)
        }
    except Exception as e:
        logger.error(f"Quick query failed: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}"
        }

@api_router.post("/database/query/natural")
async def execute_natural_query(request: NaturalQueryRequest, username: str = Depends(authenticate_dashboard)):
    """Convert natural language to SQL and execute - password protected"""
    db_manager = get_db_manager()
    
    try:
        # Simple natural language to SQL conversion
        # In a real implementation, this would use an LLM service
        sql_query = await convert_natural_to_sql(request.question)
        
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
        results = await db_manager.execute_query(sql_query)
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "results": results,
            "sql_query": sql_query,
            "execution_time": execution_time,
            "rows_returned": len(results)
        }
    except Exception as e:
        logger.error(f"Natural query failed: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}"
        }

@api_router.post("/database/query/direct")
async def execute_direct_query(request: DirectQueryRequest, username: str = Depends(authenticate_dashboard)):
    """Execute a direct SQL query - password protected"""
    db_manager = get_db_manager()
    
    try:
        if not is_safe_query(request.sql_query):
            return {
                "success": False,
                "error": "Query contains unsafe operations. Only SELECT queries are allowed."
            }
        
        start_time = time.time()
        results = await db_manager.execute_query(request.sql_query)
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "results": results,
            "sql_query": request.sql_query,
            "execution_time": execution_time,
            "rows_returned": len(results)
        }
    except Exception as e:
        logger.error(f"Direct query failed: {e}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}"
        }

@api_router.get("/database/queries/saved")
async def get_saved_queries(username: str = Depends(authenticate_dashboard)):
    """Get all saved queries - password protected"""
    db_manager = get_db_manager()
    
    try:
        results = await db_manager.execute_query("""
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
async def save_query(request: SaveQueryRequest, username: str = Depends(authenticate_dashboard)):
    """Save a query for future use - password protected"""
    db_manager = get_db_manager()
    
    try:
        await db_manager.execute_query("""
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
async def increment_query_usage(query_id: int, username: str = Depends(authenticate_dashboard)):
    """Increment usage count for a saved query - password protected"""
    db_manager = get_db_manager()
    
    try:
        await db_manager.execute_query("""
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
async def get_business_overview(username: str = Depends(authenticate_dashboard)):
    """Get business dashboard overview metrics - password protected"""
    db_manager = get_db_manager()
    
    try:
        # Total farmers by occupation
        occupation_stats = await db_manager.execute_query("""
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
        totals = await db_manager.execute_query("""
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
async def get_growth_trends(period: str = "30d", username: str = Depends(authenticate_dashboard)):
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
        new_farmers = await db_manager.execute_query(f"""
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
        unsubscribed = await db_manager.execute_query(f"""
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
async def get_activity_stream(limit: int = 50, username: str = Depends(authenticate_dashboard)):
    """Get recent activity stream - password protected"""
    db_manager = get_db_manager()
    
    try:
        activities = await db_manager.execute_query("""
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
async def get_database_changes(username: str = Depends(authenticate_dashboard)):
    """Get recent database changes - password protected"""
    db_manager = get_db_manager()
    
    try:
        changes = await db_manager.execute_query("""
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

async def convert_natural_to_sql(question: str) -> str:
    """
    Convert natural language question to SQL query.
    This is a simplified implementation. In production, this would use an LLM service.
    """
    question_lower = question.lower()
    
    # Simple pattern matching for common queries
    if "count" in question_lower and "farmer" in question_lower:
        if "occupation" in question_lower or "job" in question_lower:
            return """
                SELECT primary_occupation, COUNT(*) as count 
                FROM ava_farmers 
                WHERE subscription_status = 'active' 
                GROUP BY primary_occupation 
                ORDER BY count DESC
            """
        else:
            return "SELECT COUNT(*) as total_farmers FROM ava_farmers WHERE subscription_status = 'active'"
    
    if "vineyard" in question_lower or "grape" in question_lower:
        return """
            SELECT id, first_name, last_name, city, size_hectares
            FROM ava_farmers 
            WHERE subscription_status = 'active' 
            AND (primary_occupation = 'vineyard_farming' OR crop_type ILIKE '%grape%')
            ORDER BY size_hectares DESC
        """
    
    if "hectares" in question_lower and ("most" in question_lower or "largest" in question_lower):
        return """
            SELECT first_name, last_name, city, size_hectares, primary_occupation
            FROM ava_farmers 
            WHERE subscription_status = 'active'
            ORDER BY size_hectares DESC
            LIMIT 10
        """
    
    if "city" in question_lower or "cities" in question_lower:
        return """
            SELECT city, COUNT(*) as farmer_count, SUM(size_hectares) as total_hectares
            FROM ava_farmers 
            WHERE subscription_status = 'active'
            GROUP BY city 
            ORDER BY farmer_count DESC
        """
    
    if "recent" in question_lower or "latest" in question_lower:
        return """
            SELECT first_name, last_name, city, primary_occupation, created_at
            FROM ava_farmers 
            WHERE subscription_status = 'active'
            ORDER BY created_at DESC
            LIMIT 20
        """
    
    # If no pattern matches, return a safe default query
    return """
        SELECT id, first_name, last_name, city, primary_occupation, size_hectares
        FROM ava_farmers 
        WHERE subscription_status = 'active'
        ORDER BY id DESC
        LIMIT 50
    """

def is_safe_query(query: str) -> bool:
    """Check if a SQL query is safe to execute (SELECT only)"""
    # Remove comments and normalize whitespace
    cleaned_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
    cleaned_query = ' '.join(cleaned_query.split()).upper()
    
    # Check for unsafe operations
    unsafe_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]
    
    for keyword in unsafe_keywords:
        if keyword in cleaned_query:
            return False
    
    # Must start with SELECT
    if not cleaned_query.strip().startswith('SELECT'):
        return False
    
    return True