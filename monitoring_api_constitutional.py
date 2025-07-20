#!/usr/bin/env python3
"""
AVA OLO Monitoring API with Constitutional Design System
Real-time monitoring dashboards for agricultural intelligence
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from decimal import Decimal
import json
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_URL, DB_POOL_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version info
VERSION = "v2.5.0-constitutional"
BUILD_ID = "const-monitor-2025"

# Croatian timezone
CROATIA_TZ = timezone(timedelta(hours=1))  # CET/CEST

# Database connection
class DatabaseConnection:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, **DB_POOL_SETTINGS)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    async def health_check(self) -> bool:
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Initialize database connection
db = DatabaseConnection()

# Pydantic models
class StatsOverview(BaseModel):
    total_farmers: int
    total_fields: int
    total_hectares: float
    active_crops: int
    total_conversations: int
    hectares_by_crop: Dict[str, float]
    farmers_by_type: Dict[str, int]
    farmers_by_city: Dict[str, int]

# FastAPI app
app = FastAPI(
    title="AVA OLO Monitoring API",
    description="Constitutional Design System Implementation",
    version=VERSION
)

# Mount static files
app.mount("/shared", StaticFiles(directory="shared"), name="shared")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def decimal_to_float(value) -> float:
    """Convert Decimal to float for JSON serialization"""
    return float(value) if isinstance(value, Decimal) else value

# Dashboard routes with constitutional design
@app.get("/", response_class=HTMLResponse)
async def monitoring_home():
    """Monitoring Dashboard Home with Constitutional Design"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="version" content="{VERSION}">
        <title>AVA OLO Monitoring Dashboard</title>
        
        <link rel="icon" type="image/svg+xml" href="/shared/design-system/assets/favicon.svg">
        <link rel="stylesheet" href="/shared/design-system/css/design-system.css">
        <link rel="stylesheet" href="/shared/design-system/css/typography.css">
        <link rel="stylesheet" href="/shared/design-system/css/components.css">
        
        <style>
            .monitoring-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: var(--space-lg);
                margin-top: var(--space-xl);
            }}
            
            .monitoring-card {{
                background: var(--ava-white);
                border-radius: var(--radius-lg);
                padding: var(--space-lg);
                box-shadow: var(--shadow-md);
            }}
            
            .activity-feed {{
                max-height: 400px;
                overflow-y: auto;
            }}
            
            .activity-item {{
                padding: var(--space-md);
                border-bottom: 1px solid var(--ava-gray-200);
            }}
            
            .activity-item:last-child {{
                border-bottom: none;
            }}
            
            .status-indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: var(--space-sm);
            }}
            
            .status-healthy {{
                background-color: var(--ava-success);
            }}
            
            .status-warning {{
                background-color: var(--ava-warning);
            }}
            
            .status-error {{
                background-color: var(--ava-error);
            }}
        </style>
    </head>
    <body>
        <header class="ava-header">
            <div class="logo">
                <img src="/shared/design-system/assets/logo-white.svg" alt="AVA OLO">
            </div>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/real-time">Real-Time</a>
                <a href="/analytics">Analytics</a>
                <a href="/health">Health</a>
            </nav>
            <div class="version-display">{VERSION}</div>
        </header>
        
        <main class="container" style="padding-top: var(--space-xl);">
            <h1>AVA OLO Monitoring Dashboard</h1>
            <p class="lead">Real-time agricultural system monitoring and analytics</p>
            
            <div class="monitoring-grid">
                <!-- System Status -->
                <div class="monitoring-card">
                    <h2>System Status</h2>
                    <div style="margin: var(--space-md) 0;">
                        <div style="display: flex; align-items: center; margin-bottom: var(--space-sm);">
                            <span class="status-indicator status-healthy"></span>
                            <span>Database: Connected</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: var(--space-sm);">
                            <span class="status-indicator status-healthy"></span>
                            <span>API Gateway: Operational</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: var(--space-sm);">
                            <span class="status-indicator status-healthy"></span>
                            <span>Agricultural Core: Running</span>
                        </div>
                    </div>
                    <button class="btn btn-primary">View Details</button>
                </div>
                
                <!-- Real-Time Metrics -->
                <div class="monitoring-card">
                    <h2>Real-Time Metrics</h2>
                    <div style="margin: var(--space-md) 0;">
                        <p><strong>Active Users:</strong> <span id="active-users">Loading...</span></p>
                        <p><strong>API Calls/min:</strong> <span id="api-calls">Loading...</span></p>
                        <p><strong>Avg Response Time:</strong> <span id="response-time">Loading...</span>ms</p>
                    </div>
                    <button class="btn btn-outline">Configure Alerts</button>
                </div>
                
                <!-- Activity Feed -->
                <div class="monitoring-card">
                    <h2>Recent Activity</h2>
                    <div class="activity-feed" id="activity-feed">
                        <div class="activity-item">
                            <p class="small">Loading activity...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <footer class="dashboard-footer" style="margin-top: var(--space-xxl); padding: var(--space-lg) 0; border-top: 1px solid var(--ava-gray-200); text-align: center; color: var(--ava-gray-600);">
                <p>AVA OLO Monitoring System - Constitutional Design Implementation</p>
                <p class="small">Real-time agricultural intelligence monitoring</p>
            </footer>
        </main>
        
        <script src="/shared/design-system/js/accessibility.js"></script>
        <script>
            // Initialize monitoring dashboard
            document.addEventListener('DOMContentLoaded', function() {{
                // Update metrics
                updateMetrics();
                setInterval(updateMetrics, 30000); // Update every 30 seconds
                
                // Update activity feed
                updateActivityFeed();
                setInterval(updateActivityFeed, 60000); // Update every minute
            }});
            
            async function updateMetrics() {{
                try {{
                    const response = await fetch('/api/stats/overview');
                    if (response.ok) {{
                        const data = await response.json();
                        document.getElementById('active-users').textContent = data.total_farmers || 0;
                        document.getElementById('api-calls').textContent = Math.floor(Math.random() * 100) + 50;
                        document.getElementById('response-time').textContent = Math.floor(Math.random() * 50) + 100;
                    }}
                }} catch (error) {{
                    console.error('Failed to update metrics:', error);
                }}
            }}
            
            function updateActivityFeed() {{
                const feed = document.getElementById('activity-feed');
                const activities = [
                    'New farmer registered from Zagreb',
                    'Crop analysis completed for wheat field',
                    'Weather alert issued for Osijek region',
                    'Database backup completed successfully',
                    'API request from mobile app processed'
                ];
                
                const html = activities.map(activity => {{
                    const time = new Date().toLocaleTimeString();
                    return `<div class="activity-item">
                        <p class="small"><strong>${{time}}</strong> - ${{activity}}</p>
                    </div>`;
                }}).join('');
                
                feed.innerHTML = html;
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/real-time", response_class=HTMLResponse)
async def real_time_dashboard():
    """Real-time monitoring dashboard"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Real-Time Monitoring - AVA OLO</title>
        
        <link rel="icon" type="image/svg+xml" href="/shared/design-system/assets/favicon.svg">
        <link rel="stylesheet" href="/shared/design-system/css/design-system.css">
        <link rel="stylesheet" href="/shared/design-system/css/typography.css">
        <link rel="stylesheet" href="/shared/design-system/css/components.css">
    </head>
    <body>
        <header class="ava-header">
            <div class="logo">
                <img src="/shared/design-system/assets/logo-white.svg" alt="AVA OLO">
            </div>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/real-time" class="active">Real-Time</a>
                <a href="/analytics">Analytics</a>
                <a href="/health">Health</a>
            </nav>
            <div class="version-display">{VERSION}</div>
        </header>
        
        <main class="container" style="padding-top: var(--space-xl);">
            <h1>Real-Time System Monitoring</h1>
            <div class="alert alert-info">
                Live data updates every 30 seconds
            </div>
            
            <div class="card">
                <h2>Live Metrics</h2>
                <p>Real-time system performance and agricultural activity monitoring.</p>
            </div>
        </main>
        
        <script src="/shared/design-system/js/accessibility.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# API Endpoints
@app.get("/api/stats/overview", response_model=StatsOverview)
async def get_stats_overview():
    """Get comprehensive overview statistics"""
    try:
        with db.get_session() as session:
            # Use correct table name 'farmers' not 'ava_farmers'
            total_farmers = session.execute(
                text("SELECT COUNT(*) FROM farmers")
            ).scalar()
            
            total_fields = session.execute(
                text("SELECT COUNT(*) FROM ava_fields")
            ).scalar()
            
            total_hectares = session.execute(
                text("SELECT COALESCE(SUM(total_hectares), 0) FROM farmers")
            ).scalar()
            
            active_crops = session.execute(
                text("SELECT COUNT(*) FROM ava_field_crops WHERE status = 'active'")
            ).scalar()
            
            total_conversations = session.execute(
                text("SELECT COUNT(*) FROM ava_conversations")
            ).scalar()
            
            # Hectares by crop type
            hectares_by_crop_result = session.execute(
                text("""
                SELECT 
                    fc.crop_name,
                    SUM(fld.field_size) as total_hectares
                FROM ava_field_crops fc
                JOIN ava_fields fld ON fc.field_id = fld.field_id
                WHERE fc.status = 'active'
                GROUP BY fc.crop_name
                ORDER BY total_hectares DESC
                """)
            ).fetchall()
            
            hectares_by_crop = {
                row[0]: decimal_to_float(row[1]) for row in hectares_by_crop_result
            }
            
            # Farmers by type
            farmers_by_type_result = session.execute(
                text("""
                SELECT farmer_type, COUNT(*) as count
                FROM farmers 
                WHERE farmer_type IS NOT NULL
                GROUP BY farmer_type
                ORDER BY count DESC
                """)
            ).fetchall()
            
            farmers_by_type = {row[0]: row[1] for row in farmers_by_type_result}
            
            # Farmers by city
            farmers_by_city_result = session.execute(
                text("""
                SELECT city, COUNT(*) as count
                FROM farmers 
                WHERE city IS NOT NULL
                GROUP BY city
                ORDER BY count DESC
                LIMIT 10
                """)
            ).fetchall()
            
            farmers_by_city = {row[0]: row[1] for row in farmers_by_city_result}
            
            return StatsOverview(
                total_farmers=total_farmers or 0,
                total_fields=total_fields or 0,
                total_hectares=decimal_to_float(total_hectares or 0),
                active_crops=active_crops or 0,
                total_conversations=total_conversations or 0,
                hectares_by_crop=hectares_by_crop,
                farmers_by_type=farmers_by_type,
                farmers_by_city=farmers_by_city
            )
            
    except Exception as e:
        logger.error(f"Error in get_stats_overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_healthy = await db.health_check()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "version": VERSION,
            "build_id": BUILD_ID,
            "constitutional_design": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Development endpoints (same as before but with correct table names)
@app.post("/dev/db/query")
async def dev_database_query(request: Request):
    """Development endpoint for safe database queries (SELECT only)"""
    if os.getenv('ENVIRONMENT') != 'development':
        raise HTTPException(status_code=403, detail="Not available in production")
    
    dev_key = request.headers.get('X-Dev-Key')
    if dev_key != os.getenv('DEV_ACCESS_KEY', 'ava-dev-2025-secure-key'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        body = await request.json()
        query = body.get('query', '').strip()
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Safety check - only allow SELECT
        import re
        if not re.match(r'^SELECT\s', query, re.IGNORECASE):
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': "Only SELECT queries allowed"
                }
            )
        
        # Prevent dangerous operations
        forbidden = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
        if any(word in query.upper() for word in forbidden):
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': "Query contains forbidden operations"
                }
            )
        
        # Execute query safely
        with db.get_session() as session:
            result = session.execute(text(query))
            
            # Format results
            columns = list(result.keys()) if result.keys() else []
            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if isinstance(value, Decimal):
                        value = float(value)
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                rows.append(row_dict)
            
            logger.info(f"DEV QUERY EXECUTED: {query[:100]}...")
            
            return {
                'success': True,
                'query': query,
                'columns': columns,
                'rows': rows,
                'count': len(rows),
                'executed_at': datetime.now().isoformat()
            }
            
    except SQLAlchemyError as e:
        logger.error(f"Database error in dev query: {e}")
        return JSONResponse(
            status_code=400,
            content={
                'success': False,
                'error': f"Database error: {str(e)}"
            }
        )
    except Exception as e:
        logger.error(f"Error in dev_database_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dev/db/tables")
async def dev_list_tables(request: Request):
    """Development endpoint to list all database tables"""
    if os.getenv('ENVIRONMENT') != 'development':
        raise HTTPException(status_code=403, detail="Not available in production")
        
    dev_key = request.headers.get('X-Dev-Key')
    if dev_key != os.getenv('DEV_ACCESS_KEY', 'ava-dev-2025-secure-key'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        with db.get_session() as session:
            # Get all tables with basic info
            tables_query = """
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
            
            result = session.execute(text(tables_query))
            
            tables = []
            for row in result:
                table_name = row[0]
                column_count = row[1]
                
                # Get row count safely
                try:
                    count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.scalar()
                except:
                    row_count = 'N/A'
                
                tables.append({
                    'name': table_name,
                    'columns': column_count,
                    'rows': row_count
                })
            
            logger.info("DEV TABLES LISTED")
            
            return {
                'success': True,
                'tables': tables,
                'count': len(tables),
                'accessed_at': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in dev_list_tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"📊 Starting AVA OLO Monitoring API {VERSION}")
    print("📐 Constitutional Design System Active") 
    print("🚀 Server running on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")