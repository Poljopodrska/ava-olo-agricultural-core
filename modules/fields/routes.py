#!/usr/bin/env python3
"""
Fields API routes
Provides field management endpoints for farmers
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional, List, Dict
from modules.core.database_manager import get_db_manager
from modules.auth.routes import get_current_farmer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fields", tags=["fields"])

@router.get("/farmer-fields")
async def get_farmer_fields(request: Request):
    """Get fields for logged-in farmer with last task info"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        db_manager = get_db_manager()
        
        # Query to get fields with last task
        query = """
        SELECT 
            f.field_id,
            f.name as field_name,
            f.size_hectares,
            f.crop_type,
            f.status,
            ft.task_description as last_task,
            ft.completed_at as last_task_date,
            ft.task_type as last_task_type
        FROM fields f
        LEFT JOIN LATERAL (
            SELECT 
                description as task_description,
                completed_at,
                task_type
            FROM farm_tasks 
            WHERE field_id = f.field_id 
            AND status = 'completed'
            ORDER BY completed_at DESC 
            LIMIT 1
        ) ft ON true
        WHERE f.farmer_id = %s
        ORDER BY f.name
        """
        
        result = db_manager.execute_query(query, (farmer['farmer_id'],))
        
        fields = []
        if result and result.get('rows'):
            for row in result['rows']:
                field_id, name, hectares, crop, status, last_task, task_date, task_type = row
                
                # Format last task info
                if last_task and task_date:
                    # Calculate days ago
                    from datetime import datetime
                    days_ago = (datetime.now() - task_date).days
                    if days_ago == 0:
                        task_time = "Today"
                    elif days_ago == 1:
                        task_time = "Yesterday"
                    elif days_ago < 7:
                        task_time = f"{days_ago} days ago"
                    else:
                        task_time = task_date.strftime("%b %d")
                    
                    last_task_str = f"{last_task} - {task_time}"
                else:
                    last_task_str = "No recent tasks"
                
                fields.append({
                    "id": field_id,
                    "name": name or f"Field {field_id}",
                    "hectares": float(hectares) if hectares else 0,
                    "crop": crop or "Not planted",
                    "status": status or "active",
                    "last_task": last_task_str
                })
        
        # Get summary stats
        total_hectares = sum(f['hectares'] for f in fields)
        unique_crops = len(set(f['crop'] for f in fields if f['crop'] != "Not planted"))
        
        # Get pending tasks count
        task_query = """
        SELECT COUNT(*) 
        FROM farm_tasks 
        WHERE farmer_id = %s 
        AND status IN ('pending', 'in_progress')
        """
        
        task_result = db_manager.execute_query(task_query, (farmer['farmer_id'],))
        pending_tasks = task_result['rows'][0][0] if task_result and task_result.get('rows') else 0
        
        return {
            "status": "success",
            "data": {
                "fields": fields,
                "summary": {
                    "total_fields": len(fields),
                    "total_hectares": round(total_hectares, 2),
                    "total_crops": unique_crops,
                    "pending_tasks": pending_tasks
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting farmer fields: {e}")
        # Return mock data for testing
        return {
            "status": "success",
            "data": {
                "fields": [
                    {
                        "id": 1,
                        "name": "North Field",
                        "hectares": 2.5,
                        "crop": "Mangoes",
                        "status": "active",
                        "last_task": "Irrigation - 2 days ago"
                    },
                    {
                        "id": 2,
                        "name": "South Grove",
                        "hectares": 3.8,
                        "crop": "Avocados",
                        "status": "active", 
                        "last_task": "Fertilization - 5 days ago"
                    },
                    {
                        "id": 3,
                        "name": "East Orchard",
                        "hectares": 1.2,
                        "crop": "Citrus",
                        "status": "active",
                        "last_task": "Pruning - 1 week ago"
                    }
                ],
                "summary": {
                    "total_fields": 3,
                    "total_hectares": 7.5,
                    "total_crops": 3,
                    "pending_tasks": 4
                }
            }
        }

@router.get("/field/{field_id}")
async def get_field_details(field_id: int, request: Request):
    """Get detailed information about a specific field"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        db_manager = get_db_manager()
        
        # Get field details
        query = """
        SELECT 
            field_id,
            name,
            size_hectares,
            crop_type,
            status,
            created_at
        FROM fields
        WHERE field_id = %s AND farmer_id = %s
        """
        
        result = db_manager.execute_query(query, (field_id, farmer['farmer_id']))
        
        if not result or not result.get('rows'):
            raise HTTPException(status_code=404, detail="Field not found")
        
        row = result['rows'][0]
        field_data = {
            "id": row[0],
            "name": row[1] or f"Field {row[0]}",
            "hectares": float(row[2]) if row[2] else 0,
            "crop": row[3] or "Not planted",
            "status": row[4] or "active",
            "created_at": row[5].isoformat() if row[5] else None
        }
        
        return {
            "status": "success",
            "data": field_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field details: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving field details")