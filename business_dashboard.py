"""
AVA OLO Business KPI Dashboard - Port 8004
Comprehensive business metrics and analytics
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import os
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta, date
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Business Dashboard",
    description="Comprehensive business KPIs and analytics",
    version="3.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize database
db_ops = DatabaseOperations()

class BusinessAnalytics:
    """Business analytics and KPI calculations"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    # 1. DATABASE OVERVIEW
    async def get_total_farmers(self) -> Dict[str, Any]:
        """Get total number of farmers and recent change"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                # Total farmers
                total = session.execute(
                    text("SELECT COUNT(DISTINCT id) FROM farmers WHERE is_active = TRUE")
                ).scalar() or 0
                
                # New farmers in last 24h
                yesterday = datetime.now() - timedelta(days=1)
                new_24h = session.execute(
                    text("SELECT COUNT(*) FROM farmers WHERE created_at >= :yesterday"),
                    {"yesterday": yesterday}
                ).scalar() or 0
                
                return {"count": total, "change": f"+{new_24h}" if new_24h > 0 else "0"}
                
        except Exception as e:
            logger.error(f"Error getting total farmers: {e}")
            return {"count": 0, "change": "0"}
    
    async def get_total_hectares(self) -> Dict[str, Any]:
        """Get total hectares managed"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                # Total hectares
                total = session.execute(
                    text("SELECT COALESCE(SUM(area_hectares), 0) FROM fields WHERE is_active = TRUE")
                ).scalar() or 0
                
                # New hectares in last 24h
                yesterday = datetime.now() - timedelta(days=1)
                new_24h = session.execute(
                    text("SELECT COALESCE(SUM(area_hectares), 0) FROM fields WHERE created_at >= :yesterday"),
                    {"yesterday": yesterday}
                ).scalar() or 0
                
                return {"count": round(total, 2), "change": f"+{round(new_24h, 2)}" if new_24h > 0 else "0"}
                
        except Exception as e:
            logger.error(f"Error getting total hectares: {e}")
            return {"count": 0, "change": "0"}
    
    async def get_hectare_breakdown(self) -> Dict[str, float]:
        """Get hectare breakdown by crop type"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                results = session.execute(
                    text("""
                        SELECT 
                            COALESCE(crop_type, 'others') as crop_type,
                            SUM(area_hectares) as total_hectares
                        FROM fields 
                        WHERE is_active = TRUE
                        GROUP BY crop_type
                    """)
                ).fetchall()
                
                breakdown = {
                    "arable_crops": 0,
                    "vineyards": 0,
                    "orchards": 0,
                    "others": 0
                }
                
                for row in results:
                    crop_type = row[0].lower() if row[0] else 'others'
                    hectares = row[1] or 0
                    
                    if 'wheat' in crop_type or 'corn' in crop_type or 'grain' in crop_type:
                        breakdown["arable_crops"] += hectares
                    elif 'vine' in crop_type or 'grape' in crop_type:
                        breakdown["vineyards"] += hectares
                    elif 'orchard' in crop_type or 'fruit' in crop_type:
                        breakdown["orchards"] += hectares
                    else:
                        breakdown["others"] += hectares
                
                return {k: round(v, 2) for k, v in breakdown.items()}
                
        except Exception as e:
            logger.error(f"Error getting hectare breakdown: {e}")
            return {"arable_crops": 0, "vineyards": 0, "orchards": 0, "others": 0}
    
    # 2. GROWTH TRENDS
    async def get_growth_trends(self) -> Dict[str, Dict[str, int]]:
        """Get growth trends for 24h, 7d, 30d"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                trends = {}
                periods = {
                    "24h": 1,
                    "7d": 7,
                    "30d": 30
                }
                
                for period_name, days in periods.items():
                    start_date = datetime.now() - timedelta(days=days)
                    
                    # New farmers
                    new_farmers = session.execute(
                        text("SELECT COUNT(*) FROM farmers WHERE created_at >= :start_date"),
                        {"start_date": start_date}
                    ).scalar() or 0
                    
                    # Unsubscribed farmers
                    unsubscribed = session.execute(
                        text("SELECT COUNT(*) FROM farmers WHERE is_active = FALSE AND updated_at >= :start_date"),
                        {"start_date": start_date}
                    ).scalar() or 0
                    
                    # New hectares
                    new_hectares = session.execute(
                        text("SELECT COALESCE(SUM(area_hectares), 0) FROM fields WHERE created_at >= :start_date"),
                        {"start_date": start_date}
                    ).scalar() or 0
                    
                    trends[period_name] = {
                        "new_farmers": new_farmers,
                        "unsubscribed": unsubscribed,
                        "new_hectares": round(new_hectares, 2)
                    }
                
                return trends
                
        except Exception as e:
            logger.error(f"Error getting growth trends: {e}")
            return {
                "24h": {"new_farmers": 0, "unsubscribed": 0, "new_hectares": 0},
                "7d": {"new_farmers": 0, "unsubscribed": 0, "new_hectares": 0},
                "30d": {"new_farmers": 0, "unsubscribed": 0, "new_hectares": 0}
            }
    
    # 3. FARMER GROWTH CHARTS
    async def get_farmer_growth_daily(self) -> Dict[str, List]:
        """Get daily farmer growth for last 30 days"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                dates = []
                new_farmers = []
                unsubscribed = []
                
                for i in range(29, -1, -1):
                    day = datetime.now() - timedelta(days=i)
                    day_start = day.replace(hour=0, minute=0, second=0)
                    day_end = day_start + timedelta(days=1)
                    
                    dates.append(day.strftime("%Y-%m-%d"))
                    
                    # New farmers for this day
                    new_count = session.execute(
                        text("SELECT COUNT(*) FROM farmers WHERE created_at >= :start AND created_at < :end"),
                        {"start": day_start, "end": day_end}
                    ).scalar() or 0
                    new_farmers.append(new_count)
                    
                    # Unsubscribed for this day
                    unsub_count = session.execute(
                        text("SELECT COUNT(*) FROM farmers WHERE is_active = FALSE AND updated_at >= :start AND updated_at < :end"),
                        {"start": day_start, "end": day_end}
                    ).scalar() or 0
                    unsubscribed.append(unsub_count)
                
                return {
                    "dates": dates,
                    "new_farmers": new_farmers,
                    "unsubscribed": unsubscribed
                }
                
        except Exception as e:
            logger.error(f"Error getting daily farmer growth: {e}")
            return {
                "dates": [],
                "new_farmers": [],
                "unsubscribed": []
            }
    
    async def get_farmer_growth_cumulative(self) -> Dict[str, List]:
        """Get cumulative farmer growth over 30 days"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                dates = []
                cumulative = []
                
                # Get total farmers 30 days ago
                start_date = datetime.now() - timedelta(days=30)
                base_count = session.execute(
                    text("SELECT COUNT(*) FROM farmers WHERE created_at < :start_date"),
                    {"start_date": start_date}
                ).scalar() or 0
                
                running_total = base_count
                
                for i in range(29, -1, -1):
                    day = datetime.now() - timedelta(days=i)
                    dates.append(day.strftime("%Y-%m-%d"))
                    
                    # Count for this specific day
                    day_start = day.replace(hour=0, minute=0, second=0)
                    day_end = day_start + timedelta(days=1)
                    
                    new_count = session.execute(
                        text("SELECT COUNT(*) FROM farmers WHERE created_at >= :start AND created_at < :end"),
                        {"start": day_start, "end": day_end}
                    ).scalar() or 0
                    
                    unsub_count = session.execute(
                        text("SELECT COUNT(*) FROM farmers WHERE is_active = FALSE AND updated_at >= :start AND updated_at < :end"),
                        {"start": day_start, "end": day_end}
                    ).scalar() or 0
                    
                    running_total += (new_count - unsub_count)
                    cumulative.append(running_total)
                
                return {
                    "dates": dates,
                    "cumulative": cumulative
                }
                
        except Exception as e:
            logger.error(f"Error getting cumulative growth: {e}")
            return {
                "dates": [],
                "cumulative": []
            }
    
    # 4. TODAY'S ACTIVITY
    async def get_todays_activity(self) -> Dict[str, int]:
        """Get today's activity metrics"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                today_start = datetime.now().replace(hour=0, minute=0, second=0)
                
                # New fields today
                new_fields = session.execute(
                    text("SELECT COUNT(*) FROM fields WHERE created_at >= :today"),
                    {"today": today_start}
                ).scalar() or 0
                
                # Crops planted today
                crops_planted = session.execute(
                    text("SELECT COUNT(*) FROM tasks WHERE task_type = 'planting' AND created_at >= :today"),
                    {"today": today_start}
                ).scalar() or 0
                
                # New operations today
                new_operations = session.execute(
                    text("SELECT COUNT(*) FROM tasks WHERE created_at >= :today"),
                    {"today": today_start}
                ).scalar() or 0
                
                # Questions asked today
                questions_asked = session.execute(
                    text("SELECT COUNT(*) FROM incoming_messages WHERE created_at >= :today"),
                    {"today": today_start}
                ).scalar() or 0
                
                # Active farmers today
                active_farmers = session.execute(
                    text("SELECT COUNT(DISTINCT farmer_id) FROM incoming_messages WHERE created_at >= :today"),
                    {"today": today_start}
                ).scalar() or 0
                
                return {
                    "new_fields": new_fields,
                    "crops_planted": crops_planted,
                    "new_operations": new_operations,
                    "questions_asked": questions_asked,
                    "active_farmers": active_farmers
                }
                
        except Exception as e:
            logger.error(f"Error getting today's activity: {e}")
            return {
                "new_fields": 0,
                "crops_planted": 0,
                "new_operations": 0,
                "questions_asked": 0,
                "active_farmers": 0
            }
    
    # 5. ACTIVITY STREAM
    async def get_activity_stream(self) -> List[Dict[str, str]]:
        """Get recent activity stream"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                activities = []
                
                # Get recent farmers
                recent_farmers = session.execute(
                    text("""
                        SELECT first_name, last_name, created_at 
                        FROM farmers 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                ).fetchall()
                
                for farmer in recent_farmers:
                    time_diff = datetime.now() - farmer[2]
                    time_ago = self._format_time_ago(time_diff)
                    activities.append({
                        "time": time_ago,
                        "action": "New farmer registered",
                        "details": f"{farmer[0]} {farmer[1]}"
                    })
                
                # Get recent messages
                recent_messages = session.execute(
                    text("""
                        SELECT message_content, created_at 
                        FROM incoming_messages 
                        ORDER BY created_at DESC 
                        LIMIT 3
                    """)
                ).fetchall()
                
                for msg in recent_messages:
                    time_diff = datetime.now() - msg[1]
                    time_ago = self._format_time_ago(time_diff)
                    content = msg[0][:50] + "..." if len(msg[0]) > 50 else msg[0]
                    activities.append({
                        "time": time_ago,
                        "action": "Question asked",
                        "details": content
                    })
                
                # Sort by time and return top 5
                activities.sort(key=lambda x: x["time"])
                return activities[:5]
                
        except Exception as e:
            logger.error(f"Error getting activity stream: {e}")
            return []
    
    # 6. RECENT DATABASE CHANGES
    async def get_recent_database_changes(self) -> List[Dict[str, str]]:
        """Get recent database changes"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                changes = []
                
                # Recent farmer changes
                farmer_changes = session.execute(
                    text("""
                        SELECT 'farmers' as table_name, 
                               CASE WHEN is_active THEN 'INSERT' ELSE 'UPDATE' END as action,
                               id, created_at, updated_at
                        FROM farmers 
                        ORDER BY GREATEST(created_at, updated_at) DESC 
                        LIMIT 5
                    """)
                ).fetchall()
                
                for change in farmer_changes:
                    timestamp = change[4] if change[1] == 'UPDATE' else change[3]
                    changes.append({
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M"),
                        "table": change[0],
                        "action": change[1],
                        "details": f"Farmer ID {change[2]}"
                    })
                
                # Recent field changes
                field_changes = session.execute(
                    text("""
                        SELECT 'fields' as table_name, 
                               'INSERT' as action,
                               id, area_hectares, created_at
                        FROM fields 
                        ORDER BY created_at DESC 
                        LIMIT 3
                    """)
                ).fetchall()
                
                for change in field_changes:
                    changes.append({
                        "timestamp": change[4].strftime("%Y-%m-%d %H:%M"),
                        "table": change[0],
                        "action": change[1],
                        "details": f"Field ID {change[2]} - {change[3]} hectares"
                    })
                
                # Sort by timestamp and return top 5
                changes.sort(key=lambda x: x["timestamp"], reverse=True)
                return changes[:5]
                
        except Exception as e:
            logger.error(f"Error getting database changes: {e}")
            return []
    
    def _format_time_ago(self, time_diff: timedelta) -> str:
        """Format time difference as human readable"""
        seconds = time_diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} sec ago"
        elif seconds < 3600:
            return f"{int(seconds/60)} min ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)} hours ago"
        else:
            return f"{int(seconds/86400)} days ago"

# Initialize analytics
analytics = BusinessAnalytics()

@app.get("/", response_class=HTMLResponse)
async def business_dashboard(request: Request):
    """Main business dashboard with comprehensive KPIs"""
    
    # Fetch all data concurrently for performance
    total_farmers = await analytics.get_total_farmers()
    total_hectares = await analytics.get_total_hectares()
    hectare_breakdown = await analytics.get_hectare_breakdown()
    growth_trends = await analytics.get_growth_trends()
    farmer_growth_daily = await analytics.get_farmer_growth_daily()
    farmer_growth_cumulative = await analytics.get_farmer_growth_cumulative()
    todays_activity = await analytics.get_todays_activity()
    activity_stream = await analytics.get_activity_stream()
    recent_changes = await analytics.get_recent_database_changes()
    
    return templates.TemplateResponse(
        "business_dashboard.html",
        {
            "request": request,
            "total_farmers": total_farmers,
            "total_hectares": total_hectares,
            "hectare_breakdown": hectare_breakdown,
            "growth_trends": growth_trends,
            "farmer_growth_daily": farmer_growth_daily,
            "farmer_growth_cumulative": farmer_growth_cumulative,
            "todays_activity": todays_activity,
            "activity_stream": activity_stream,
            "recent_changes": recent_changes,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.get("/api/metrics")
async def get_metrics():
    """API endpoint for real-time metrics"""
    return {
        "total_farmers": await analytics.get_total_farmers(),
        "total_hectares": await analytics.get_total_hectares(),
        "growth_trends": await analytics.get_growth_trends(),
        "todays_activity": await analytics.get_todays_activity()
    }

@app.get("/api/charts/farmer-growth")
async def get_farmer_growth_charts():
    """API endpoint for farmer growth charts data"""
    return {
        "daily": await analytics.get_farmer_growth_daily(),
        "cumulative": await analytics.get_farmer_growth_cumulative()
    }

@app.get("/api/activity-stream")
async def get_activity_stream():
    """API endpoint for activity stream"""
    return await analytics.get_activity_stream()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = await db_ops.health_check()
    
    return {
        "service": "Business KPI Dashboard",
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
        "port": 8004,
        "purpose": "Comprehensive business metrics and analytics"
    }

if __name__ == "__main__":
    import uvicorn
    print("📊 Starting AVA OLO Business Dashboard on port 8004")
    uvicorn.run(app, host="0.0.0.0", port=8004)