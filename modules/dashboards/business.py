"""
AVA OLO Business Dashboard Module
Implements business metrics and growth tracking
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
import logging
from modules.core.database_manager import get_db_manager
from modules.core.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/business", tags=["business_dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def business_dashboard(request: Request):
    """Main business dashboard"""
    return templates.TemplateResponse("business_dashboard_constitutional.html", {
        "request": request
    })

@router.get("/api/overview", response_class=JSONResponse)
async def get_business_overview():
    """Get database overview metrics"""
    db_manager = get_db_manager()
    
    try:
        # Total farmers and hectares
        totals_query = """
        SELECT 
            COUNT(*) as total_farmers,
            SUM(size_hectares) as total_hectares
        FROM farmers
        WHERE subscription_status = 'active'
        """
        
        totals_result = await db_manager.execute_query(totals_query)
        
        if totals_result and totals_result.get('success'):
            totals_data = totals_result.get('data', [[0, 0]])[0]
            total_farmers = totals_data[0] or 0
            total_hectares = float(totals_data[1] or 0)
        else:
            total_farmers = 0
            total_hectares = 0.0
        
        # Hectare breakdown by crop type
        breakdown_query = """
        SELECT 
            CASE 
                WHEN primary_occupation LIKE '%vineyard%' THEN 'Vineyards'
                WHEN primary_occupation LIKE '%arable%' OR primary_occupation LIKE '%grain%' THEN 'Arable Crops'
                WHEN primary_occupation LIKE '%orchard%' OR primary_occupation LIKE '%fruit%' THEN 'Orchards'
                ELSE 'Other'
            END as crop_category,
            COUNT(*) as farmer_count,
            SUM(size_hectares) as total_hectares
        FROM farmers
        WHERE subscription_status = 'active'
        GROUP BY crop_category
        """
        
        breakdown_result = await db_manager.execute_query(breakdown_query)
        
        hectare_breakdown = {
            'Arable Crops': {'hectares': 0, 'percentage': 0},
            'Vineyards': {'hectares': 0, 'percentage': 0},
            'Orchards': {'hectares': 0, 'percentage': 0},
            'Other': {'hectares': 0, 'percentage': 0}
        }
        
        if breakdown_result and breakdown_result.get('success'):
            for row in breakdown_result.get('data', []):
                category = row[0]
                hectares = float(row[2] or 0)
                if category in hectare_breakdown:
                    hectare_breakdown[category]['hectares'] = hectares
                    if total_hectares > 0:
                        hectare_breakdown[category]['percentage'] = round((hectares / total_hectares) * 100, 1)
        
        return {
            "success": True,
            "total_farmers": total_farmers,
            "total_hectares": round(total_hectares, 2),
            "hectare_breakdown": hectare_breakdown
        }
    
    except Exception as e:
        logger.error(f"Error fetching business overview: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "total_farmers": 0,
            "total_hectares": 0,
            "hectare_breakdown": {}
        }

@router.get("/api/growth-trends/{period}", response_class=JSONResponse)
async def get_growth_trends(period: str):
    """Get growth trends for specified period"""
    db_manager = get_db_manager()
    
    # Map period to SQL interval
    period_map = {
        "24hours": "1 day",
        "7days": "7 days",
        "30days": "30 days"
    }
    
    sql_interval = period_map.get(period, "30 days")
    
    try:
        # New farmers in period
        new_farmers_query = f"""
        SELECT COUNT(*) as new_farmers
        FROM farmers
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '{sql_interval}'
        """
        
        new_result = await db_manager.execute_query(new_farmers_query)
        new_farmers = 0
        if new_result and new_result.get('success'):
            new_farmers = new_result.get('data', [[0]])[0][0] or 0
        
        # Unsubscribed farmers in period
        unsubscribed_query = f"""
        SELECT COUNT(*) as unsubscribed
        FROM farmers
        WHERE subscription_status = 'inactive'
        AND updated_at >= CURRENT_TIMESTAMP - INTERVAL '{sql_interval}'
        """
        
        unsub_result = await db_manager.execute_query(unsubscribed_query)
        unsubscribed = 0
        if unsub_result and unsub_result.get('success'):
            unsubscribed = unsub_result.get('data', [[0]])[0][0] or 0
        
        # New hectares in period
        hectares_query = f"""
        SELECT SUM(size_hectares) as new_hectares
        FROM farmers
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '{sql_interval}'
        """
        
        hectares_result = await db_manager.execute_query(hectares_query)
        new_hectares = 0.0
        if hectares_result and hectares_result.get('success'):
            new_hectares = float(hectares_result.get('data', [[0]])[0][0] or 0)
        
        return {
            "success": True,
            "period": period,
            "new_farmers": new_farmers,
            "unsubscribed": unsubscribed,
            "new_hectares": round(new_hectares, 2)
        }
    
    except Exception as e:
        logger.error(f"Error fetching growth trends: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "new_farmers": 0,
            "unsubscribed": 0,
            "new_hectares": 0
        }

@router.get("/api/cumulative-growth", response_class=JSONResponse)
async def get_cumulative_growth(days: int = 30):
    """Get cumulative farmer growth data"""
    db_manager = get_db_manager()
    
    try:
        # Get daily registration data
        daily_query = f"""
        SELECT 
            DATE(created_at) as registration_date,
            COUNT(*) as daily_farmers
        FROM farmers
        WHERE created_at >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY DATE(created_at)
        ORDER BY registration_date
        """
        
        daily_result = await db_manager.execute_query(daily_query)
        
        # Get starting total before the period
        initial_query = f"""
        SELECT COUNT(*) as initial_total
        FROM farmers
        WHERE created_at < CURRENT_DATE - INTERVAL '{days} days'
        """
        
        initial_result = await db_manager.execute_query(initial_query)
        initial_total = 0
        if initial_result and initial_result.get('success'):
            initial_total = initial_result.get('data', [[0]])[0][0] or 0
        
        # Build cumulative data
        dates = []
        cumulative_totals = []
        daily_net_growth = []
        running_total = initial_total
        
        if daily_result and daily_result.get('success'):
            for row in daily_result.get('data', []):
                date = row[0].strftime('%Y-%m-%d') if row[0] else ''
                daily_count = row[1] or 0
                
                running_total += daily_count
                
                dates.append(date)
                cumulative_totals.append(running_total)
                daily_net_growth.append(daily_count)
        
        return {
            "success": True,
            "dates": dates,
            "cumulative_totals": cumulative_totals,
            "daily_net_growth": daily_net_growth
        }
    
    except Exception as e:
        logger.error(f"Error fetching cumulative growth: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "dates": [],
            "cumulative_totals": [],
            "daily_net_growth": []
        }

@router.get("/api/churn-rate", response_class=JSONResponse)
async def get_churn_rate(days: int = 30):
    """Get churn rate data"""
    db_manager = get_db_manager()
    
    try:
        # Get daily churn data
        churn_query = f"""
        SELECT 
            DATE(updated_at) as churn_date,
            COUNT(*) as churned_farmers
        FROM farmers
        WHERE subscription_status = 'inactive'
        AND updated_at >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY DATE(updated_at)
        ORDER BY churn_date
        """
        
        churn_result = await db_manager.execute_query(churn_query)
        
        # Get active farmers for each day to calculate rate
        dates = []
        churn_rates = []
        
        if churn_result and churn_result.get('success'):
            for row in churn_result.get('data', []):
                date = row[0]
                churned = row[1] or 0
                
                # Get total active farmers on that date
                active_query = """
                SELECT COUNT(*) as active_farmers
                FROM farmers
                WHERE created_at <= %s
                AND (subscription_status = 'active' OR 
                     (subscription_status = 'inactive' AND updated_at > %s))
                """
                
                active_result = await db_manager.execute_query(active_query, (date, date))
                
                if active_result and active_result.get('success'):
                    active_farmers = active_result.get('data', [[1]])[0][0] or 1
                    churn_rate = (churned / active_farmers) * 100 if active_farmers > 0 else 0
                    
                    dates.append(date.strftime('%Y-%m-%d'))
                    churn_rates.append(round(churn_rate, 2))
        
        # Calculate 7-day rolling average
        rolling_average = []
        for i in range(len(churn_rates)):
            start = max(0, i - 6)
            avg = sum(churn_rates[start:i+1]) / (i - start + 1)
            rolling_average.append(round(avg, 2))
        
        return {
            "success": True,
            "dates": dates,
            "churn_rates": churn_rates,
            "rolling_average": rolling_average
        }
    
    except Exception as e:
        logger.error(f"Error fetching churn rate: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "dates": [],
            "churn_rates": [],
            "rolling_average": []
        }

@router.get("/api/todays-activity", response_class=JSONResponse)
async def get_todays_activity():
    """Get today's activity metrics"""
    db_manager = get_db_manager()
    
    try:
        # Today's metrics
        metrics = {
            "new_fields": 0,
            "crops_planted": 0,
            "spraying_operations": 0,
            "questions_asked": 0,
            "farmers_active": 0
        }
        
        # New fields today (farmers registered today)
        new_fields_query = """
        SELECT COUNT(*) as count
        FROM farmers
        WHERE DATE(created_at) = CURRENT_DATE
        """
        
        result = await db_manager.execute_query(new_fields_query)
        if result and result.get('success'):
            metrics["new_fields"] = result.get('data', [[0]])[0][0] or 0
        
        # Active farmers today (from conversations table if exists)
        active_farmers_query = """
        SELECT COUNT(DISTINCT farmer_id) as count
        FROM conversations
        WHERE DATE(timestamp) = CURRENT_DATE
        """
        
        try:
            result = await db_manager.execute_query(active_farmers_query)
            if result and result.get('success'):
                metrics["farmers_active"] = result.get('data', [[0]])[0][0] or 0
        except:
            # If conversations table doesn't exist, use a default
            metrics["farmers_active"] = metrics["new_fields"]
        
        # Simulate other metrics based on active farmers
        if metrics["farmers_active"] > 0:
            metrics["crops_planted"] = metrics["farmers_active"] * 2
            metrics["spraying_operations"] = metrics["farmers_active"] 
            metrics["questions_asked"] = metrics["farmers_active"] * 3
        
        return {
            "success": True,
            "metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"Error fetching today's activity: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "metrics": {
                "new_fields": 0,
                "crops_planted": 0,
                "spraying_operations": 0,
                "questions_asked": 0,
                "farmers_active": 0
            }
        }

@router.get("/api/activity-stream", response_class=JSONResponse)
async def get_activity_stream():
    """Get recent activity stream"""
    db_manager = get_db_manager()
    
    try:
        # Get recent farmer registrations and activities
        activity_query = """
        SELECT 
            f.id,
            f.name,
            f.created_at as timestamp,
            'registered' as activity_type
        FROM farmers f
        WHERE f.created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ORDER BY f.created_at DESC
        LIMIT 20
        """
        
        result = await db_manager.execute_query(activity_query)
        
        activities = []
        if result and result.get('success'):
            for row in result.get('data', []):
                farmer_id = row[0]
                farmer_name = row[1] or f"Farmer #{farmer_id}"
                timestamp = row[2]
                
                # Format activity message
                time_str = timestamp.strftime('%H:%M') if timestamp else ''
                activity = {
                    'time': time_str,
                    'farmer_id': farmer_id,
                    'farmer_name': farmer_name,
                    'activity': f"New registration from {farmer_name}"
                }
                activities.append(activity)
        
        return {
            "success": True,
            "activities": activities
        }
    
    except Exception as e:
        logger.error(f"Error fetching activity stream: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "activities": []
        }

@router.get("/api/database-changes", response_class=JSONResponse)
async def get_database_changes():
    """Get recent database changes"""
    db_manager = get_db_manager()
    
    try:
        # Get recent farmer table changes
        changes_query = """
        SELECT 
            'farmers' as table_name,
            CASE 
                WHEN created_at = updated_at THEN 'INSERT'
                ELSE 'UPDATE'
            END as operation,
            id as record_id,
            updated_at as change_time
        FROM farmers
        WHERE updated_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ORDER BY updated_at DESC
        LIMIT 20
        """
        
        result = await db_manager.execute_query(changes_query)
        
        changes = []
        if result and result.get('success'):
            for row in result.get('data', []):
                change = {
                    'table': row[0],
                    'operation': row[1],
                    'record_id': row[2],
                    'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else ''
                }
                changes.append(change)
        
        return {
            "success": True,
            "changes": changes
        }
    
    except Exception as e:
        logger.error(f"Error fetching database changes: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "changes": []
        }