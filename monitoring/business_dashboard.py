"""
Business Dashboard - Analytics and business metrics for AVA OLO
Provides insights into system usage, growth, and business performance
"""
from fastapi import APIRouter, Depends, HTTPException, Query
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

class UsageMetrics(BaseModel):
    total_queries: int
    unique_users: int
    daily_active_users: int
    average_session_length: float
    top_features: List[Dict[str, Any]]
    growth_rate: float

class SystemMetrics(BaseModel):
    uptime_percentage: float
    average_response_time: float
    error_rate: float
    api_calls_per_day: int
    peak_usage_hours: List[int]
    system_load: Dict[str, float]

class BusinessInsights(BaseModel):
    farmer_adoption_rate: float
    geographic_distribution: Dict[str, int]
    crop_coverage: Dict[str, int]
    seasonal_trends: Dict[str, List[float]]
    user_satisfaction: float

class BusinessDashboard:
    """
    Business analytics dashboard for AVA OLO
    """
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def get_usage_metrics(self, days: int = 30) -> UsageMetrics:
        """Get usage and engagement metrics"""
        try:
            with self.db_ops.get_session() as session:
                # Total queries
                total_queries = session.execute(
                    text("""
                    SELECT COUNT(*) FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days}
                ).scalar()
                
                # Unique users (farmers)
                unique_users = session.execute(
                    text("""
                    SELECT COUNT(DISTINCT farmer_id) FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    AND farmer_id IS NOT NULL
                    """),
                    {"days": days}
                ).scalar()
                
                # Daily active users (last 24 hours)
                daily_active = session.execute(
                    text("""
                    SELECT COUNT(DISTINCT farmer_id) FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL '1 day'
                    AND farmer_id IS NOT NULL
                    """)
                ).scalar()
                
                # Top features (query types)
                top_features_results = session.execute(
                    text("""
                    SELECT topic, COUNT(*) as usage_count
                    FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    AND topic IS NOT NULL
                    GROUP BY topic
                    ORDER BY usage_count DESC
                    LIMIT 10
                    """),
                    {"days": days}
                ).fetchall()
                
                top_features = []
                for row in top_features_results:
                    top_features.append({
                        "feature": row[0],
                        "usage_count": row[1],
                        "percentage": (row[1] / total_queries * 100) if total_queries > 0 else 0
                    })
                
                # Growth rate (compare with previous period)
                previous_period_queries = session.execute(
                    text("""
                    SELECT COUNT(*) FROM ava_conversations 
                    WHERE created_at BETWEEN CURRENT_DATE - INTERVAL ':days2 days' 
                    AND CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days, "days2": days * 2}
                ).scalar()
                
                growth_rate = 0.0
                if previous_period_queries and previous_period_queries > 0:
                    growth_rate = ((total_queries - previous_period_queries) / previous_period_queries) * 100
                
                return UsageMetrics(
                    total_queries=total_queries or 0,
                    unique_users=unique_users or 0,
                    daily_active_users=daily_active or 0,
                    average_session_length=0.0,  # Would need session tracking
                    top_features=top_features,
                    growth_rate=growth_rate
                )
                
        except Exception as e:
            logger.error(f"Error getting usage metrics: {str(e)}")
            return UsageMetrics(
                total_queries=0,
                unique_users=0,
                daily_active_users=0,
                average_session_length=0.0,
                top_features=[],
                growth_rate=0.0
            )
    
    async def get_system_metrics(self, days: int = 7) -> SystemMetrics:
        """Get system performance metrics"""
        try:
            with self.db_ops.get_session() as session:
                # System health data
                health_stats = session.execute(
                    text("""
                    SELECT 
                        AVG(CASE WHEN status = 'healthy' THEN 1.0 ELSE 0.0 END) * 100 as uptime_pct,
                        AVG(response_time_ms) as avg_response_time
                    FROM system_health_log 
                    WHERE checked_at > CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days}
                ).fetchone()
                
                # Error rate from LLM operations
                error_stats = session.execute(
                    text("""
                    SELECT 
                        COUNT(*) as total_ops,
                        SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) as errors
                    FROM llm_debug_log 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days}
                ).fetchone()
                
                # Daily API calls
                daily_calls = session.execute(
                    text("""
                    SELECT COUNT(*) / :days as avg_daily_calls
                    FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    """),
                    {"days": days}
                ).scalar()
                
                # Peak usage hours
                peak_hours_results = session.execute(
                    text("""
                    SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
                    FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY count DESC
                    LIMIT 5
                    """),
                    {"days": days}
                ).fetchall()
                
                peak_hours = [int(row[0]) for row in peak_hours_results]
                
                # Calculate metrics
                uptime_percentage = float(health_stats[0]) if health_stats[0] else 0.0
                avg_response_time = float(health_stats[1]) if health_stats[1] else 0.0
                
                error_rate = 0.0
                if error_stats[0] and error_stats[0] > 0:
                    error_rate = (error_stats[1] / error_stats[0]) * 100
                
                return SystemMetrics(
                    uptime_percentage=uptime_percentage,
                    average_response_time=avg_response_time,
                    error_rate=error_rate,
                    api_calls_per_day=int(daily_calls) if daily_calls else 0,
                    peak_usage_hours=peak_hours,
                    system_load={
                        "cpu": 0.0,  # Would integrate with monitoring system
                        "memory": 0.0,
                        "storage": 0.0
                    }
                )
                
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return SystemMetrics(
                uptime_percentage=0.0,
                average_response_time=0.0,
                error_rate=0.0,
                api_calls_per_day=0,
                peak_usage_hours=[],
                system_load={"cpu": 0.0, "memory": 0.0, "storage": 0.0}
            )
    
    async def get_business_insights(self) -> BusinessInsights:
        """Get business intelligence insights"""
        try:
            with self.db_ops.get_session() as session:
                # Farmer adoption rate (farmers with recent activity)
                total_farmers = session.execute(
                    text("SELECT COUNT(*) FROM ava_farmers")
                ).scalar()
                
                active_farmers = session.execute(
                    text("""
                    SELECT COUNT(DISTINCT farmer_id) FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
                    AND farmer_id IS NOT NULL
                    """)
                ).scalar()
                
                adoption_rate = 0.0
                if total_farmers and total_farmers > 0:
                    adoption_rate = (active_farmers / total_farmers) * 100
                
                # Geographic distribution
                geo_results = session.execute(
                    text("""
                    SELECT city, COUNT(*) as farmer_count
                    FROM ava_farmers 
                    WHERE city IS NOT NULL
                    GROUP BY city
                    ORDER BY farmer_count DESC
                    LIMIT 10
                    """)
                ).fetchall()
                
                geographic_distribution = {row[0]: row[1] for row in geo_results}
                
                # Crop coverage
                crop_results = session.execute(
                    text("""
                    SELECT fc.crop_name, COUNT(DISTINCT f.farmer_id) as farmer_count
                    FROM ava_field_crops fc
                    JOIN ava_fields fld ON fc.field_id = fld.field_id
                    JOIN ava_farmers f ON fld.farmer_id = f.id
                    WHERE fc.status = 'active'
                    GROUP BY fc.crop_name
                    ORDER BY farmer_count DESC
                    """)
                ).fetchall()
                
                crop_coverage = {row[0]: row[1] for row in crop_results}
                
                # Seasonal trends (monthly activity for past year)
                seasonal_results = session.execute(
                    text("""
                    SELECT 
                        EXTRACT(MONTH FROM created_at) as month,
                        COUNT(*) as activity_count
                    FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL '12 months'
                    GROUP BY EXTRACT(MONTH FROM created_at)
                    ORDER BY month
                    """)
                ).fetchall()
                
                seasonal_trends = {"monthly_activity": [0] * 12}
                for row in seasonal_results:
                    month_idx = int(row[0]) - 1  # Convert to 0-based index
                    if 0 <= month_idx < 12:
                        seasonal_trends["monthly_activity"][month_idx] = row[1]
                
                # User satisfaction (based on confidence scores)
                avg_confidence = session.execute(
                    text("""
                    SELECT AVG(confidence_score) FROM ava_conversations 
                    WHERE confidence_score IS NOT NULL
                    AND created_at > CURRENT_DATE - INTERVAL '30 days'
                    """)
                ).scalar()
                
                user_satisfaction = float(avg_confidence * 100) if avg_confidence else 0.0
                
                return BusinessInsights(
                    farmer_adoption_rate=adoption_rate,
                    geographic_distribution=geographic_distribution,
                    crop_coverage=crop_coverage,
                    seasonal_trends=seasonal_trends,
                    user_satisfaction=user_satisfaction
                )
                
        except Exception as e:
            logger.error(f"Error getting business insights: {str(e)}")
            return BusinessInsights(
                farmer_adoption_rate=0.0,
                geographic_distribution={},
                crop_coverage={},
                seasonal_trends={"monthly_activity": [0] * 12},
                user_satisfaction=0.0
            )
    
    async def get_growth_projections(self, months: int = 6) -> Dict[str, Any]:
        """Get growth projections based on current trends"""
        try:
            with self.db_ops.get_session() as session:
                # Get historical data for trend analysis
                monthly_data = session.execute(
                    text("""
                    SELECT 
                        DATE_TRUNC('month', created_at) as month,
                        COUNT(DISTINCT farmer_id) as active_farmers,
                        COUNT(*) as total_queries
                    FROM ava_conversations 
                    WHERE created_at > CURRENT_DATE - INTERVAL '6 months'
                    AND farmer_id IS NOT NULL
                    GROUP BY DATE_TRUNC('month', created_at)
                    ORDER BY month
                    """)
                ).fetchall()
                
                # Simple linear projection (would use more sophisticated models in production)
                if len(monthly_data) >= 2:
                    recent_farmers = monthly_data[-1][1]
                    prev_farmers = monthly_data[-2][1]
                    monthly_growth = recent_farmers - prev_farmers
                    
                    projected_farmers = recent_farmers + (monthly_growth * months)
                    
                    recent_queries = monthly_data[-1][2]
                    prev_queries = monthly_data[-2][2]
                    query_growth = recent_queries - prev_queries
                    
                    projected_queries = recent_queries + (query_growth * months)
                else:
                    projected_farmers = 0
                    projected_queries = 0
                
                return {
                    "projection_period_months": months,
                    "projected_active_farmers": max(0, projected_farmers),
                    "projected_monthly_queries": max(0, projected_queries),
                    "confidence": "low" if len(monthly_data) < 3 else "medium",
                    "historical_data": [
                        {
                            "month": row[0].isoformat(),
                            "active_farmers": row[1],
                            "total_queries": row[2]
                        }
                        for row in monthly_data
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting growth projections: {str(e)}")
            return {
                "projection_period_months": months,
                "projected_active_farmers": 0,
                "projected_monthly_queries": 0,
                "confidence": "none",
                "historical_data": []
            }

# Create dashboard instance
dashboard = BusinessDashboard()

# API Routes
@router.get("/api/v1/business/usage")
async def get_usage_metrics(days: int = Query(30, description="Number of days to analyze")):
    """Get usage and engagement metrics"""
    try:
        metrics = await dashboard.get_usage_metrics(days)
        return metrics
    except Exception as e:
        logger.error(f"Usage metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/business/system")
async def get_system_metrics(days: int = Query(7, description="Number of days to analyze")):
    """Get system performance metrics"""
    try:
        metrics = await dashboard.get_system_metrics(days)
        return metrics
    except Exception as e:
        logger.error(f"System metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/business/insights")
async def get_business_insights():
    """Get business intelligence insights"""
    try:
        insights = await dashboard.get_business_insights()
        return insights
    except Exception as e:
        logger.error(f"Business insights error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/business/projections")
async def get_growth_projections(months: int = Query(6, description="Projection period in months")):
    """Get growth projections"""
    try:
        projections = await dashboard.get_growth_projections(months)
        return projections
    except Exception as e:
        logger.error(f"Growth projections error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/business/summary")
async def get_business_summary():
    """Get complete business dashboard summary"""
    try:
        usage = await dashboard.get_usage_metrics()
        system = await dashboard.get_system_metrics()
        insights = await dashboard.get_business_insights()
        projections = await dashboard.get_growth_projections()
        
        return {
            "usage_metrics": usage,
            "system_metrics": system,
            "business_insights": insights,
            "growth_projections": projections,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_farmers": insights.farmer_adoption_rate,
                "system_health": "healthy" if system.uptime_percentage > 95 else "degraded",
                "growth_trend": "positive" if usage.growth_rate > 0 else "negative"
            }
        }
    except Exception as e:
        logger.error(f"Business summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))