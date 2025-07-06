"""
Agronomic Dashboard - Expert monitoring for agricultural advisors
Provides detailed insights into farming activities and AI performance
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging
import os
import sys
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

router = APIRouter()
db_ops = DatabaseOperations()

class FarmActivityStats(BaseModel):
    total_farmers: int
    active_conversations: int
    total_fields: int
    total_hectares: float
    top_crops: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]

class AIPerformanceStats(BaseModel):
    total_queries: int
    average_confidence: float
    response_time_avg: float
    error_rate: float
    query_types: Dict[str, int]
    language_distribution: Dict[str, int]

class AgronomicDashboard:
    """
    Dashboard for agricultural experts to monitor farming activities
    """
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def get_farm_statistics(self, 
                                days: int = 30,
                                region: Optional[str] = None) -> FarmActivityStats:
        """Get comprehensive farm statistics"""
        try:
            with self.db_ops.get_session() as session:
                # Basic counts
                farmers_count = session.execute(
                    text("SELECT COUNT(*) FROM ava_farmers WHERE created_at > CURRENT_DATE - INTERVAL ':days days'"),
                    {"days": days}
                ).scalar()
                
                conversations_count = session.execute(
                    text("SELECT COUNT(*) FROM ava_conversations WHERE created_at > CURRENT_DATE - INTERVAL ':days days'"),
                    {"days": days}
                ).scalar()
                
                fields_count = session.execute(
                    text("SELECT COUNT(*) FROM ava_fields")
                ).scalar()
                
                total_hectares = session.execute(
                    text("SELECT COALESCE(SUM(field_size), 0) FROM ava_fields")
                ).scalar()
                
                # Top crops
                top_crops_results = session.execute(
                    text("""
                    SELECT fc.crop_name, c.croatian_name, COUNT(*) as field_count,
                           SUM(f.field_size) as total_hectares
                    FROM ava_field_crops fc
                    JOIN ava_fields f ON fc.field_id = f.field_id
                    LEFT JOIN ava_crops c ON fc.crop_name = c.crop_name
                    WHERE fc.status = 'active'
                    GROUP BY fc.crop_name, c.croatian_name
                    ORDER BY field_count DESC
                    LIMIT 10
                    """)
                ).fetchall()
                
                top_crops = []
                for row in top_crops_results:
                    top_crops.append({
                        "crop_name": row[0],
                        "croatian_name": row[1],
                        "field_count": row[2],
                        "total_hectares": float(row[3]) if row[3] else 0
                    })
                
                # Recent activities
                recent_activities_results = session.execute(
                    text("""
                    SELECT ft.task_type, ft.task_description, ft.task_date,
                           f.farm_name, fld.field_name
                    FROM farm_tasks ft
                    JOIN ava_farmers f ON ft.farmer_id = f.id
                    LEFT JOIN ava_fields fld ON ft.field_id = fld.field_id
                    WHERE ft.created_at > CURRENT_DATE - INTERVAL ':days days'
                    ORDER BY ft.created_at DESC
                    LIMIT 20
                    """),
                    {"days": days}
                ).fetchall()
                
                recent_activities = []
                for row in recent_activities_results:
                    recent_activities.append({
                        "task_type": row[0],
                        "task_description": row[1],
                        "task_date": row[2].isoformat() if row[2] else None,
                        "farm_name": row[3],
                        "field_name": row[4]
                    })
                
                return FarmActivityStats(
                    total_farmers=farmers_count or 0,
                    active_conversations=conversations_count or 0,
                    total_fields=fields_count or 0,
                    total_hectares=float(total_hectares) if total_hectares else 0.0,
                    top_crops=top_crops,
                    recent_activities=recent_activities
                )
                
        except Exception as e:
            logger.error(f"Error getting farm statistics: {str(e)}")
            return FarmActivityStats(
                total_farmers=0,
                active_conversations=0,
                total_fields=0,
                total_hectares=0.0,
                top_crops=[],
                recent_activities=[]
            )
    
    async def get_ai_performance(self, days: int = 7) -> AIPerformanceStats:
        """Get AI performance statistics"""
        try:
            with self.db_ops.get_session() as session:
                # Query performance stats
                total_queries = session.execute(
                    text("""
                    SELECT COUNT(*) FROM llm_debug_log 
                    WHERE operation_type = 'query' 
                    AND created_at > CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days}
                ).scalar()
                
                avg_confidence = session.execute(
                    text("""
                    SELECT AVG(confidence_score) FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    AND confidence_score IS NOT NULL
                    """),
                    {"days": days}
                ).scalar()
                
                avg_response_time = session.execute(
                    text("""
                    SELECT AVG(latency_ms) FROM llm_debug_log 
                    WHERE operation_type = 'query' 
                    AND created_at > CURRENT_DATE - INTERVAL ':days days'
                    AND latency_ms IS NOT NULL
                    """),
                    {"days": days}
                ).scalar()
                
                error_count = session.execute(
                    text("""
                    SELECT COUNT(*) FROM llm_debug_log 
                    WHERE success = FALSE 
                    AND created_at > CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days}
                ).scalar()
                
                # Query types distribution
                query_types_results = session.execute(
                    text("""
                    SELECT topic, COUNT(*) as count FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    AND topic IS NOT NULL
                    GROUP BY topic
                    ORDER BY count DESC
                    """),
                    {"days": days}
                ).fetchall()
                
                query_types = {row[0]: row[1] for row in query_types_results}
                
                # Language distribution
                language_results = session.execute(
                    text("""
                    SELECT language, COUNT(*) as count FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY language
                    ORDER BY count DESC
                    """),
                    {"days": days}
                ).fetchall()
                
                language_distribution = {row[0]: row[1] for row in language_results}
                
                error_rate = 0.0
                if total_queries and total_queries > 0:
                    error_rate = (error_count or 0) / total_queries
                
                return AIPerformanceStats(
                    total_queries=total_queries or 0,
                    average_confidence=float(avg_confidence) if avg_confidence else 0.0,
                    response_time_avg=float(avg_response_time) if avg_response_time else 0.0,
                    error_rate=error_rate,
                    query_types=query_types,
                    language_distribution=language_distribution
                )
                
        except Exception as e:
            logger.error(f"Error getting AI performance: {str(e)}")
            return AIPerformanceStats(
                total_queries=0,
                average_confidence=0.0,
                response_time_avg=0.0,
                error_rate=0.0,
                query_types={},
                language_distribution={}
            )
    
    async def get_crop_health_alerts(self) -> List[Dict[str, Any]]:
        """Get crop health alerts and recommendations"""
        try:
            with self.db_ops.get_session() as session:
                # Get urgent recommendations
                alerts = session.execute(
                    text("""
                    SELECT r.recommendation_text, r.priority, r.created_at,
                           f.farm_name, fld.field_name, fc.crop_name
                    FROM ava_recommendations r
                    JOIN ava_farmers f ON r.farmer_id = f.id
                    LEFT JOIN ava_fields fld ON r.field_id = fld.field_id
                    LEFT JOIN ava_field_crops fc ON fld.field_id = fc.field_id AND fc.status = 'active'
                    WHERE r.status = 'pending'
                    AND r.priority IN ('high', 'urgent')
                    ORDER BY 
                        CASE r.priority 
                            WHEN 'urgent' THEN 1
                            WHEN 'high' THEN 2
                            ELSE 3
                        END,
                        r.created_at DESC
                    LIMIT 20
                    """)
                ).fetchall()
                
                alert_list = []
                for row in alerts:
                    alert_list.append({
                        "recommendation": row[0],
                        "priority": row[1],
                        "created_at": row[2].isoformat() if row[2] else None,
                        "farm_name": row[3],
                        "field_name": row[4],
                        "crop_name": row[5]
                    })
                
                return alert_list
                
        except Exception as e:
            logger.error(f"Error getting crop health alerts: {str(e)}")
            return []
    
    async def get_seasonal_insights(self, current_date: date = None) -> Dict[str, Any]:
        """Get seasonal agricultural insights"""
        if not current_date:
            current_date = date.today()
        
        try:
            with self.db_ops.get_session() as session:
                # Get crops that should be planted soon
                planting_season = session.execute(
                    text("""
                    SELECT c.crop_name, c.croatian_name, c.typical_cycle_days,
                           COUNT(fc.id) as current_plantings
                    FROM ava_crops c
                    LEFT JOIN ava_field_crops fc ON c.crop_name = fc.crop_name 
                        AND fc.status = 'active'
                        AND fc.planting_date > CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY c.crop_name, c.croatian_name, c.typical_cycle_days
                    ORDER BY current_plantings DESC
                    """)
                ).fetchall()
                
                # Get crops ready for harvest
                harvest_ready = session.execute(
                    text("""
                    SELECT fc.crop_name, f.farm_name, fld.field_name,
                           fc.expected_harvest_date, fc.planting_date
                    FROM ava_field_crops fc
                    JOIN ava_fields fld ON fc.field_id = fld.field_id
                    JOIN ava_farmers f ON fld.farmer_id = f.id
                    WHERE fc.status = 'active'
                    AND fc.expected_harvest_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '14 days'
                    ORDER BY fc.expected_harvest_date
                    """)
                ).fetchall()
                
                planting_insights = []
                for row in planting_season:
                    planting_insights.append({
                        "crop_name": row[0],
                        "croatian_name": row[1],
                        "cycle_days": row[2],
                        "recent_plantings": row[3]
                    })
                
                harvest_insights = []
                for row in harvest_ready:
                    harvest_insights.append({
                        "crop_name": row[0],
                        "farm_name": row[1],
                        "field_name": row[2],
                        "expected_harvest": row[3].isoformat() if row[3] else None,
                        "planting_date": row[4].isoformat() if row[4] else None
                    })
                
                return {
                    "current_season": self._get_season(current_date),
                    "planting_trends": planting_insights,
                    "upcoming_harvests": harvest_insights,
                    "seasonal_recommendations": self._get_seasonal_recommendations(current_date)
                }
                
        except Exception as e:
            logger.error(f"Error getting seasonal insights: {str(e)}")
            return {
                "current_season": "unknown",
                "planting_trends": [],
                "upcoming_harvests": [],
                "seasonal_recommendations": []
            }
    
    def _get_season(self, current_date: date) -> str:
        """Determine current season"""
        month = current_date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _get_seasonal_recommendations(self, current_date: date) -> List[str]:
        """Get seasonal recommendations"""
        season = self._get_season(current_date)
        
        recommendations = {
            "spring": [
                "Prepare fields for spring planting",
                "Check soil moisture and temperature",
                "Plan fertilization schedule",
                "Inspect equipment before planting season"
            ],
            "summer": [
                "Monitor crop growth and health",
                "Implement irrigation if needed",
                "Scout for pests and diseases",
                "Plan harvest logistics"
            ],
            "autumn": [
                "Complete harvest operations",
                "Prepare fields for winter",
                "Plan crop rotation for next year",
                "Store harvested crops properly"
            ],
            "winter": [
                "Plan for next growing season",
                "Maintain and repair equipment",
                "Analyze previous year's performance",
                "Prepare seed and input orders"
            ]
        }
        
        return recommendations.get(season, [])

# Create dashboard instance
dashboard = AgronomicDashboard()

# API Routes
@router.get("/api/v1/agronomic/farm-stats")
async def get_farm_stats(days: int = Query(30, description="Number of days to analyze")):
    """Get farm activity statistics"""
    try:
        stats = await dashboard.get_farm_statistics(days)
        return stats
    except Exception as e:
        logger.error(f"Farm stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/agronomic/ai-performance")
async def get_ai_performance(days: int = Query(7, description="Number of days to analyze")):
    """Get AI performance statistics"""
    try:
        performance = await dashboard.get_ai_performance(days)
        return performance
    except Exception as e:
        logger.error(f"AI performance error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/agronomic/alerts")
async def get_crop_alerts():
    """Get crop health alerts"""
    try:
        alerts = await dashboard.get_crop_health_alerts()
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Crop alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/agronomic/seasonal")
async def get_seasonal_insights():
    """Get seasonal agricultural insights"""
    try:
        insights = await dashboard.get_seasonal_insights()
        return insights
    except Exception as e:
        logger.error(f"Seasonal insights error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/agronomic/summary")
async def get_dashboard_summary():
    """Get complete dashboard summary"""
    try:
        farm_stats = await dashboard.get_farm_statistics()
        ai_performance = await dashboard.get_ai_performance()
        alerts = await dashboard.get_crop_health_alerts()
        seasonal = await dashboard.get_seasonal_insights()
        
        return {
            "farm_statistics": farm_stats,
            "ai_performance": ai_performance,
            "alerts": alerts[:5],  # Top 5 alerts
            "seasonal_insights": seasonal,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))