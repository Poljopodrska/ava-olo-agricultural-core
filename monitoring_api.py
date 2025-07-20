#!/usr/bin/env python3
"""
AVA OLO Monitoring API - Real-time business dashboard backend
Connects to actual PostgreSQL database with Croatian farmer data
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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

class GrowthTrends(BaseModel):
    new_farmers_24h: int
    new_farmers_7d: int
    new_farmers_30d: int
    new_fields_24h: int
    new_fields_7d: int
    new_fields_30d: int
    growth_rate_daily: float
    growth_rate_weekly: float

class ActivityToday(BaseModel):
    new_fields: int
    new_crops: int
    new_tasks: int
    new_conversations: int
    active_farmers: int
    total_activity: int

class GrowthChartData(BaseModel):
    date: str
    cumulative_farmers: int
    new_farmers: int
    cumulative_fields: int
    new_fields: int

class ChurnData(BaseModel):
    date: str
    active_farmers: int
    churned_farmers: int
    churn_rate: float

class LiveActivity(BaseModel):
    id: int
    table_name: str
    activity_type: str
    description: str
    farmer_name: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove failed connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# FastAPI app
app = FastAPI(
    title="AVA OLO Monitoring API",
    description="Real-time monitoring dashboard for Croatian agricultural assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def to_croatia_time(dt: datetime) -> datetime:
    """Convert datetime to Croatian timezone"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CROATIA_TZ)

def decimal_to_float(value) -> float:
    """Convert Decimal to float for JSON serialization"""
    return float(value) if isinstance(value, Decimal) else value

async def get_farmer_name(session: Session, farmer_id: int) -> Optional[str]:
    """Get farmer name by ID"""
    try:
        result = session.execute(
            text("SELECT manager_name, manager_last_name FROM ava_farmers WHERE id = :farmer_id"),
            {"farmer_id": farmer_id}
        ).fetchone()
        if result:
            return f"{result[0]} {result[1]}"
        return None
    except:
        return None

# API Endpoints

@app.get("/api/stats/overview", response_model=StatsOverview)
async def get_stats_overview():
    """Get comprehensive overview statistics"""
    try:
        with db.get_session() as session:
            # Total farmers
            total_farmers = session.execute(
                text("SELECT COUNT(*) FROM ava_farmers")
            ).scalar()
            
            # Total fields
            total_fields = session.execute(
                text("SELECT COUNT(*) FROM ava_fields")
            ).scalar()
            
            # Total hectares
            total_hectares = session.execute(
                text("SELECT COALESCE(SUM(total_hectares), 0) FROM ava_farmers")
            ).scalar()
            
            # Active crops
            active_crops = session.execute(
                text("SELECT COUNT(*) FROM ava_field_crops WHERE status = 'active'")
            ).scalar()
            
            # Total conversations
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
                FROM ava_farmers 
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
                FROM ava_farmers 
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

@app.get("/api/stats/growth-trends", response_model=GrowthTrends)
async def get_growth_trends():
    """Get growth trends for different time periods"""
    try:
        with db.get_session() as session:
            # New farmers in different periods
            new_farmers_24h = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_farmers 
                WHERE created_at > NOW() - INTERVAL '1 day'
                """)
            ).scalar()
            
            new_farmers_7d = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_farmers 
                WHERE created_at > NOW() - INTERVAL '7 days'
                """)
            ).scalar()
            
            new_farmers_30d = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_farmers 
                WHERE created_at > NOW() - INTERVAL '30 days'
                """)
            ).scalar()
            
            # New fields in different periods
            new_fields_24h = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_fields 
                WHERE created_at > NOW() - INTERVAL '1 day'
                """)
            ).scalar()
            
            new_fields_7d = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_fields 
                WHERE created_at > NOW() - INTERVAL '7 days'
                """)
            ).scalar()
            
            new_fields_30d = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_fields 
                WHERE created_at > NOW() - INTERVAL '30 days'
                """)
            ).scalar()
            
            # Calculate growth rates
            total_farmers = session.execute(
                text("SELECT COUNT(*) FROM ava_farmers")
            ).scalar()
            
            growth_rate_daily = (new_farmers_24h / total_farmers * 100) if total_farmers > 0 else 0
            growth_rate_weekly = (new_farmers_7d / total_farmers * 100) if total_farmers > 0 else 0
            
            return GrowthTrends(
                new_farmers_24h=new_farmers_24h or 0,
                new_farmers_7d=new_farmers_7d or 0,
                new_farmers_30d=new_farmers_30d or 0,
                new_fields_24h=new_fields_24h or 0,
                new_fields_7d=new_fields_7d or 0,
                new_fields_30d=new_fields_30d or 0,
                growth_rate_daily=growth_rate_daily,
                growth_rate_weekly=growth_rate_weekly
            )
            
    except Exception as e:
        logger.error(f"Error in get_growth_trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/activity-today", response_model=ActivityToday)
async def get_activity_today():
    """Get today's activity statistics"""
    try:
        with db.get_session() as session:
            # Activity for today
            new_fields = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_fields 
                WHERE DATE(created_at) = CURRENT_DATE
                """)
            ).scalar()
            
            new_crops = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_field_crops 
                WHERE DATE(created_at) = CURRENT_DATE
                """)
            ).scalar()
            
            new_tasks = session.execute(
                text("""
                SELECT COUNT(*) FROM farm_tasks 
                WHERE DATE(created_at) = CURRENT_DATE
                """)
            ).scalar()
            
            new_conversations = session.execute(
                text("""
                SELECT COUNT(*) FROM ava_conversations 
                WHERE DATE(created_at) = CURRENT_DATE
                """)
            ).scalar()
            
            # Active farmers (farmers with activity in last 24h)
            active_farmers = session.execute(
                text("""
                SELECT COUNT(DISTINCT farmer_id) FROM ava_conversations
                WHERE created_at > NOW() - INTERVAL '1 day'
                AND farmer_id IS NOT NULL
                """)
            ).scalar()
            
            total_activity = (new_fields or 0) + (new_crops or 0) + (new_tasks or 0) + (new_conversations or 0)
            
            return ActivityToday(
                new_fields=new_fields or 0,
                new_crops=new_crops or 0,
                new_tasks=new_tasks or 0,
                new_conversations=new_conversations or 0,
                active_farmers=active_farmers or 0,
                total_activity=total_activity
            )
            
    except Exception as e:
        logger.error(f"Error in get_activity_today: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/growth-chart", response_model=List[GrowthChartData])
async def get_growth_chart(period: int = Query(30, description="Number of days to analyze")):
    """Get cumulative growth chart data"""
    try:
        with db.get_session() as session:
            # Get daily farmer growth
            farmer_growth = session.execute(
                text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as new_farmers
                FROM ava_farmers 
                WHERE created_at > NOW() - INTERVAL ':period days'
                GROUP BY DATE(created_at)
                ORDER BY date
                """),
                {"period": period}
            ).fetchall()
            
            # Get daily field growth
            field_growth = session.execute(
                text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as new_fields
                FROM ava_fields 
                WHERE created_at > NOW() - INTERVAL ':period days'
                GROUP BY DATE(created_at)
                ORDER BY date
                """),
                {"period": period}
            ).fetchall()
            
            # Convert to dictionaries for easier processing
            farmer_dict = {row[0]: row[1] for row in farmer_growth}
            field_dict = {row[0]: row[1] for row in field_growth}
            
            # Generate date range and calculate cumulative values
            chart_data = []
            cumulative_farmers = 0
            cumulative_fields = 0
            
            for i in range(period):
                date = datetime.now().date() - timedelta(days=period - i - 1)
                
                new_farmers = farmer_dict.get(date, 0)
                new_fields = field_dict.get(date, 0)
                
                cumulative_farmers += new_farmers
                cumulative_fields += new_fields
                
                chart_data.append(GrowthChartData(
                    date=date.isoformat(),
                    cumulative_farmers=cumulative_farmers,
                    new_farmers=new_farmers,
                    cumulative_fields=cumulative_fields,
                    new_fields=new_fields
                ))
            
            return chart_data
            
    except Exception as e:
        logger.error(f"Error in get_growth_chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/churn-chart", response_model=List[ChurnData])
async def get_churn_chart(period: int = Query(30, description="Number of days to analyze")):
    """Get churn rate analysis"""
    try:
        with db.get_session() as session:
            # Get daily activity data
            activity_data = session.execute(
                text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(DISTINCT farmer_id) as active_farmers
                FROM ava_conversations
                WHERE created_at > NOW() - INTERVAL ':period days'
                AND farmer_id IS NOT NULL
                GROUP BY DATE(created_at)
                ORDER BY date
                """),
                {"period": period}
            ).fetchall()
            
            # Convert to dictionary
            activity_dict = {row[0]: row[1] for row in activity_data}
            
            # Calculate churn data
            churn_data = []
            prev_active = 0
            
            for i in range(period):
                date = datetime.now().date() - timedelta(days=period - i - 1)
                active_farmers = activity_dict.get(date, 0)
                
                # Simple churn calculation: farmers who were active yesterday but not today
                churned_farmers = max(0, prev_active - active_farmers) if prev_active > 0 else 0
                churn_rate = (churned_farmers / prev_active * 100) if prev_active > 0 else 0
                
                churn_data.append(ChurnData(
                    date=date.isoformat(),
                    active_farmers=active_farmers,
                    churned_farmers=churned_farmers,
                    churn_rate=churn_rate
                ))
                
                prev_active = active_farmers
            
            return churn_data
            
    except Exception as e:
        logger.error(f"Error in get_churn_chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity/live-feed", response_model=List[LiveActivity])
async def get_live_feed():
    """Get last 50 activities across all tables"""
    try:
        with db.get_session() as session:
            activities = []
            
            # Recent conversations
            conversations = session.execute(
                text("""
                SELECT 
                    c.id, c.farmer_id, c.question, c.topic, c.created_at,
                    f.manager_name, f.manager_last_name
                FROM ava_conversations c
                LEFT JOIN ava_farmers f ON c.farmer_id = f.id
                ORDER BY c.created_at DESC
                LIMIT 15
                """)
            ).fetchall()
            
            for conv in conversations:
                farmer_name = f"{conv[5]} {conv[6]}" if conv[5] and conv[6] else "Unknown"
                activities.append(LiveActivity(
                    id=conv[0],
                    table_name="ava_conversations",
                    activity_type="conversation",
                    description=f"New conversation: {conv[3] or 'General'}",
                    farmer_name=farmer_name,
                    timestamp=conv[4],
                    details={"topic": conv[3], "question": conv[2][:100]}
                ))
            
            # Recent fields
            fields = session.execute(
                text("""
                SELECT 
                    fld.field_id, fld.farmer_id, fld.field_name, fld.field_size, fld.created_at,
                    f.manager_name, f.manager_last_name
                FROM ava_fields fld
                LEFT JOIN ava_farmers f ON fld.farmer_id = f.id
                ORDER BY fld.created_at DESC
                LIMIT 15
                """)
            ).fetchall()
            
            for field in fields:
                farmer_name = f"{field[5]} {field[6]}" if field[5] and field[6] else "Unknown"
                activities.append(LiveActivity(
                    id=field[0],
                    table_name="ava_fields",
                    activity_type="field_created",
                    description=f"New field: {field[2]} ({field[3]}ha)",
                    farmer_name=farmer_name,
                    timestamp=field[4],
                    details={"field_name": field[2], "field_size": decimal_to_float(field[3])}
                ))
            
            # Recent tasks
            tasks = session.execute(
                text("""
                SELECT 
                    t.id, t.farmer_id, t.task_type, t.task_description, t.created_at,
                    f.manager_name, f.manager_last_name
                FROM farm_tasks t
                LEFT JOIN ava_farmers f ON t.farmer_id = f.id
                ORDER BY t.created_at DESC
                LIMIT 15
                """)
            ).fetchall()
            
            for task in tasks:
                farmer_name = f"{task[5]} {task[6]}" if task[5] and task[6] else "Unknown"
                activities.append(LiveActivity(
                    id=task[0],
                    table_name="farm_tasks",
                    activity_type="task_logged",
                    description=f"Task: {task[2]}",
                    farmer_name=farmer_name,
                    timestamp=task[4],
                    details={"task_type": task[2], "description": task[3][:100]}
                ))
            
            # Sort all activities by timestamp and limit to 50
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            return activities[:50]
            
    except Exception as e:
        logger.error(f"Error in get_live_feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity/recent-entries")
async def get_recent_entries():
    """Get last 30 database entries across all tables"""
    try:
        with db.get_session() as session:
            entries = []
            
            # Table configurations
            tables = [
                ("ava_farmers", "id", "created_at", "farm_name"),
                ("ava_fields", "field_id", "created_at", "field_name"),
                ("ava_field_crops", "id", "created_at", "crop_name"),
                ("ava_conversations", "id", "created_at", "topic"),
                ("farm_tasks", "id", "created_at", "task_type"),
                ("system_health_log", "id", "checked_at", "component_name")
            ]
            
            for table_name, id_col, time_col, desc_col in tables:
                try:
                    results = session.execute(
                        text(f"""
                        SELECT {id_col}, {time_col}, {desc_col}
                        FROM {table_name}
                        ORDER BY {time_col} DESC
                        LIMIT 10
                        """)
                    ).fetchall()
                    
                    for row in results:
                        entries.append({
                            "table": table_name,
                            "id": row[0],
                            "timestamp": row[1].isoformat(),
                            "description": row[2]
                        })
                        
                except Exception as table_error:
                    logger.warning(f"Error querying {table_name}: {table_error}")
                    continue
            
            # Sort by timestamp and limit
            entries.sort(key=lambda x: x["timestamp"], reverse=True)
            return {"entries": entries[:30]}
            
    except Exception as e:
        logger.error(f"Error in get_recent_entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity/recent-deletions")
async def get_recent_deletions():
    """Get recent deletions (placeholder - would need audit logging)"""
    # This would require an audit log table to track deletions
    return {
        "message": "Deletion tracking not implemented yet",
        "suggestion": "Add audit logging to track deletions",
        "deletions": []
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Get current stats
            try:
                with db.get_session() as session:
                    active_farmers = session.execute(
                        text("""
                        SELECT COUNT(DISTINCT farmer_id) FROM ava_conversations
                        WHERE created_at > NOW() - INTERVAL '1 day'
                        AND farmer_id IS NOT NULL
                        """)
                    ).scalar()
                    
                    update_data = {
                        "type": "stats_update",
                        "data": {
                            "active_farmers": active_farmers or 0,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    await manager.send_personal_message(json.dumps(update_data), websocket)
                    
            except Exception as e:
                logger.error(f"WebSocket update error: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_healthy = await db.health_check()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Development Database Endpoints
import re
from fastapi import Request

@app.post("/dev/db/query")
async def dev_database_query(request: Request):
    """Development endpoint for safe database queries (SELECT only)"""
    # Check development mode
    if os.getenv('ENVIRONMENT') != 'development':
        raise HTTPException(status_code=403, detail="Not available in production")
    
    # Check secret header
    dev_key = request.headers.get('X-Dev-Key')
    if dev_key != os.getenv('DEV_ACCESS_KEY', 'temporary-dev-key-2025'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Get query from request body
        body = await request.json()
        query = body.get('query', '').strip()
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Safety check - only allow SELECT
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
                # Convert row to dict, handling Decimal objects
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if isinstance(value, Decimal):
                        value = float(value)
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                rows.append(row_dict)
            
            # Log query for audit
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

@app.get("/dev/db/schema")
async def dev_database_schema(request: Request):
    """Development endpoint to explore database schema"""
    # Check development mode
    if os.getenv('ENVIRONMENT') != 'development':
        raise HTTPException(status_code=403, detail="Not available in production")
        
    # Check secret header
    dev_key = request.headers.get('X-Dev-Key')
    if dev_key != os.getenv('DEV_ACCESS_KEY', 'temporary-dev-key-2025'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        with db.get_session() as session:
            # Get all tables and columns
            schema_query = """
            SELECT 
                table_name, 
                column_name, 
                data_type, 
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
            
            result = session.execute(text(schema_query))
            
            # Organize by table
            schema = {}
            for row in result:
                table = row[0]
                if table not in schema:
                    schema[table] = {
                        'columns': [],
                        'column_count': 0
                    }
                
                schema[table]['columns'].append({
                    'name': row[1],
                    'type': row[2],
                    'nullable': row[3] == 'YES',
                    'default': row[4],
                    'max_length': row[5]
                })
                schema[table]['column_count'] += 1
            
            # Get table row counts
            for table_name in schema.keys():
                try:
                    count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    schema[table_name]['row_count'] = count_result.scalar()
                except:
                    schema[table_name]['row_count'] = 'N/A'
            
            # Log schema access for audit
            logger.info("DEV SCHEMA ACCESSED")
            
            return {
                'success': True,
                'schema': schema,
                'tables': list(schema.keys()),
                'table_count': len(schema),
                'accessed_at': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in dev_database_schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dev/db/tables")
async def dev_list_tables(request: Request):
    """Development endpoint to list all database tables"""
    # Check development mode
    if os.getenv('ENVIRONMENT') != 'development':
        raise HTTPException(status_code=403, detail="Not available in production")
        
    # Check secret header
    dev_key = request.headers.get('X-Dev-Key')
    if dev_key != os.getenv('DEV_ACCESS_KEY', 'temporary-dev-key-2025'):
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
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")