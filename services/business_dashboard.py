"""
AVA OLO Business KPI Dashboard - Port 8004
Business metrics, statistics, and performance indicators
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
import sys
from typing import Dict, Any
from datetime import datetime, date
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Business Dashboard",
    description="Business KPIs, metrics and performance monitoring",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

# Initialize database
db_ops = DatabaseOperations()

class BusinessDashboard:
    """Business dashboard for KPIs and performance metrics"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def get_business_metrics(self) -> Dict[str, Any]:
        """Get key business metrics and KPIs"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                # Total conversations
                total_convs = session.execute(
                    text("SELECT COUNT(*) FROM incoming_messages")
                ).scalar() or 0
                
                # Total farmers
                total_farmers = session.execute(
                    text("SELECT COUNT(DISTINCT farmer_id) FROM incoming_messages WHERE farmer_id IS NOT NULL")
                ).scalar() or 0
                
                # Today's conversations
                today_convs = session.execute(
                    text("SELECT COUNT(*) FROM incoming_messages WHERE DATE(sent_at) = CURRENT_DATE")
                ).scalar() or 0
                
                # This week's conversations
                week_convs = session.execute(
                    text("SELECT COUNT(*) FROM incoming_messages WHERE sent_at >= CURRENT_DATE - INTERVAL '7 days'")
                ).scalar() or 0
                
                # Average confidence score
                avg_confidence = session.execute(
                    text("SELECT AVG(confidence_score) FROM incoming_messages WHERE confidence_score IS NOT NULL")
                ).scalar() or 0
                
                # Expert approval rate
                approved = session.execute(
                    text("SELECT COUNT(*) FROM incoming_messages WHERE expert_approved = TRUE")
                ).scalar() or 0
                
                approval_rate = (approved / total_convs * 100) if total_convs > 0 else 0
                
                return {
                    "total_conversations": total_convs,
                    "total_farmers": total_farmers,
                    "today_conversations": today_convs,
                    "week_conversations": week_convs,
                    "avg_confidence": float(avg_confidence),
                    "approval_rate": approval_rate,
                    "expert_approved": approved,
                    "growth_rate": self._calculate_growth_rate(session)
                }
                
        except Exception as e:
            logger.error(f"Error getting business metrics: {str(e)}")
            return {
                "total_conversations": 0,
                "total_farmers": 0,
                "today_conversations": 0,
                "week_conversations": 0,
                "avg_confidence": 0.0,
                "approval_rate": 0.0,
                "expert_approved": 0,
                "growth_rate": 0.0
            }
    
    def _calculate_growth_rate(self, session) -> float:
        """Calculate weekly growth rate"""
        try:
            from sqlalchemy import text
            
            # Current week conversations
            current_week = session.execute(
                text("SELECT COUNT(*) FROM incoming_messages WHERE sent_at >= CURRENT_DATE - INTERVAL '7 days'")
            ).scalar() or 0
            
            # Previous week conversations
            previous_week = session.execute(
                text("""
                    SELECT COUNT(*) FROM incoming_messages 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '14 days' 
                    AND created_at < CURRENT_DATE - INTERVAL '7 days'
                """)
            ).scalar() or 0
            
            if previous_week > 0:
                growth = ((current_week - previous_week) / previous_week) * 100
                return round(growth, 1)
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    async def get_conversation_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get conversation trends over time"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                results = session.execute(
                    text("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as conversations,
                        COUNT(DISTINCT farmer_id) as unique_farmers,
                        AVG(confidence_score) as avg_confidence
                    FROM incoming_messages 
                    WHERE created_at >= CURRENT_DATE - INTERVAL :days DAY
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT :days
                    """),
                    {"days": days}
                ).fetchall()
                
                trends = []
                for row in results:
                    trends.append({
                        "date": row[0].isoformat() if row[0] else None,
                        "conversations": row[1] or 0,
                        "unique_farmers": row[2] or 0,
                        "avg_confidence": float(row[3]) if row[3] else 0.0
                    })
                
                return {"trends": trends}
                
        except Exception as e:
            logger.error(f"Error getting conversation trends: {str(e)}")
            return {"trends": []}

# Initialize dashboard
dashboard = BusinessDashboard()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Business KPI Dashboard"""
    metrics = await dashboard.get_business_metrics()
    trends = await dashboard.get_conversation_trends(30)
    
    return templates.TemplateResponse("business_dashboard.html", {
        "request": request,
        "metrics": metrics,
        "trends": trends
    })

@app.get("/api/metrics")
async def get_metrics():
    """API endpoint for business metrics"""
    return await dashboard.get_business_metrics()

@app.get("/api/trends")
async def get_trends(days: int = 30):
    """API endpoint for conversation trends"""
    return await dashboard.get_conversation_trends(days)

@app.get("/health")
async def health_check():
    """Health check"""
    db_healthy = await db_ops.health_check()
    
    return {
        "service": "Business KPI Dashboard",
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
        "port": 8004,
        "purpose": "Business metrics and KPI monitoring"
    }

if __name__ == "__main__":
    import uvicorn
    print("📊 Starting AVA OLO Business Dashboard on port 8004")
    uvicorn.run(app, host="0.0.0.0", port=8004)