#!/usr/bin/env python3
"""
Task Management Routes - Agricultural task planning and tracking
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import logging
import json

from ..core.database_manager import get_db_manager
from ..auth.routes import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["task-management"])

@router.get("/templates", response_class=JSONResponse)
async def get_task_templates(farmer: dict = Depends(require_auth)):
    """Get available task templates"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT id, task_name, task_category, description, typical_duration_hours
        FROM task_templates
        ORDER BY task_category, task_name
        """
        result = db_manager.execute_query(query)
        
        templates = []
        if result and 'rows' in result:
            for row in result['rows']:
                templates.append({
                    'id': row[0],
                    'task_name': row[1],
                    'task_category': row[2],
                    'description': row[3],
                    'typical_duration_hours': float(row[4]) if row[4] else None
                })
        
        return JSONResponse(content={
            "success": True,
            "templates": templates
        })
    except Exception as e:
        logger.error(f"Error fetching task templates: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/materials", response_class=JSONResponse)
async def get_materials(material_type: Optional[str] = None, farmer: dict = Depends(require_auth)):
    """Get available materials/products"""
    db_manager = get_db_manager()
    
    try:
        if material_type:
            query = """
            SELECT id, material_name, material_type, manufacturer, unit, cost_per_unit
            FROM materials
            WHERE material_type = %s
            ORDER BY material_name
            """
            result = db_manager.execute_query(query, (material_type,))
        else:
            query = """
            SELECT id, material_name, material_type, manufacturer, unit, cost_per_unit
            FROM materials
            ORDER BY material_type, material_name
            """
            result = db_manager.execute_query(query)
        
        materials = []
        if result and 'rows' in result:
            for row in result['rows']:
                materials.append({
                    'id': row[0],
                    'material_name': row[1],
                    'material_type': row[2],
                    'manufacturer': row[3],
                    'unit': row[4],
                    'cost_per_unit': float(row[5]) if row[5] else None
                })
        
        return JSONResponse(content={
            "success": True,
            "materials": materials
        })
    except Exception as e:
        logger.error(f"Error fetching materials: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/list", response_class=JSONResponse)
async def get_farmer_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    farmer: dict = Depends(require_auth)
):
    """Get tasks for a farmer"""
    db_manager = get_db_manager()
    farmer_id = farmer['farmer_id']
    
    try:
        if status:
            query = """
            SELECT DISTINCT
                t.id, t.task_name, t.task_type, t.status, 
                t.planned_date, t.completed_date, t.notes,
                STRING_AGG(f.field_name, ', ') as field_names,
                COUNT(DISTINCT tf.field_id) as field_count,
                SUM(tf.area_covered) as total_area
            FROM tasks t
            JOIN task_fields tf ON t.id = tf.task_id
            JOIN fields f ON tf.field_id = f.id
            WHERE t.farmer_id = %s AND t.status = %s
            GROUP BY t.id
            ORDER BY t.planned_date DESC
            LIMIT %s
            """
            result = db_manager.execute_query(query, (farmer_id, status, limit))
        else:
            query = """
            SELECT DISTINCT
                t.id, t.task_name, t.task_type, t.status, 
                t.planned_date, t.completed_date, t.notes,
                STRING_AGG(f.field_name, ', ') as field_names,
                COUNT(DISTINCT tf.field_id) as field_count,
                SUM(tf.area_covered) as total_area
            FROM tasks t
            JOIN task_fields tf ON t.id = tf.task_id
            JOIN fields f ON tf.field_id = f.id
            WHERE t.farmer_id = %s
            GROUP BY t.id
            ORDER BY t.planned_date DESC
            LIMIT %s
            """
            result = db_manager.execute_query(query, (farmer_id, limit))
        
        tasks = []
        if result and 'rows' in result:
            for row in result['rows']:
                tasks.append({
                    'id': row[0],
                    'task_name': row[1],
                    'task_type': row[2],
                    'status': row[3],
                    'planned_date': row[4].isoformat() if row[4] else None,
                    'completed_date': row[5].isoformat() if row[5] else None,
                    'notes': row[6],
                    'field_names': row[7],
                    'field_count': row[8],
                    'total_area': float(row[9]) if row[9] else 0
                })
        
        return JSONResponse(content={
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        })
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/create", response_class=JSONResponse)
async def create_task(request: Request, farmer: dict = Depends(require_auth)):
    """Create a new task"""
    db_manager = get_db_manager()
    farmer_id = farmer['farmer_id']
    
    try:
        data = await request.json()
        
        # Validate required fields
        if not data.get('task_name') or not data.get('field_ids'):
            return JSONResponse(content={
                "success": False,
                "error": "Task name and at least one field are required"
            }, status_code=400)
        
        # Create task
        task_query = """
        INSERT INTO tasks (farmer_id, task_name, task_type, planned_date, notes, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        task_result = db_manager.execute_query(
            task_query,
            (
                farmer_id,
                data['task_name'],
                data.get('task_type', 'other'),
                data.get('planned_date'),
                data.get('notes'),
                farmer_id
            )
        )
        
        if not task_result or 'rows' not in task_result:
            raise Exception("Failed to create task")
        
        task_id = task_result['rows'][0][0]
        
        # Associate fields with task
        field_ids = data['field_ids']
        for field_id in field_ids:
            field_query = """
            INSERT INTO task_fields (task_id, field_id, area_covered)
            SELECT %s, %s, area_ha FROM fields WHERE id = %s
            """
            db_manager.execute_query(field_query, (task_id, field_id, field_id))
        
        # Add materials if provided
        if data.get('materials'):
            for material in data['materials']:
                material_query = """
                INSERT INTO task_materials (task_id, material_id, dose_rate, unit, notes)
                VALUES (%s, %s, %s, %s, %s)
                """
                db_manager.execute_query(
                    material_query,
                    (
                        task_id,
                        material['material_id'],
                        material.get('dose_rate'),
                        material.get('unit'),
                        material.get('notes')
                    )
                )
        
        return JSONResponse(content={
            "success": True,
            "task_id": task_id,
            "message": "Task created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/bulk-create", response_class=JSONResponse)
async def create_bulk_tasks(request: Request, farmer: dict = Depends(require_auth)):
    """Create tasks for multiple fields based on criteria"""
    db_manager = get_db_manager()
    farmer_id = farmer['farmer_id']
    
    try:
        data = await request.json()
        
        # Get fields based on criteria
        if data.get('all_fields'):
            field_query = "SELECT id FROM fields WHERE farmer_id = %s"
            field_result = db_manager.execute_query(field_query, (farmer_id,))
        elif data.get('crop_type'):
            field_query = """
            SELECT DISTINCT f.id 
            FROM fields f
            JOIN field_crops fc ON f.id = fc.field_id
            WHERE f.farmer_id = %s AND fc.crop_type = %s AND fc.status = 'active'
            """
            field_result = db_manager.execute_query(field_query, (farmer_id, data['crop_type']))
        elif data.get('field_ids'):
            field_ids = data['field_ids']
        else:
            return JSONResponse(content={
                "success": False,
                "error": "No field selection criteria provided"
            }, status_code=400)
        
        # Extract field IDs from query result if needed
        if not data.get('field_ids'):
            field_ids = [row[0] for row in field_result['rows']] if field_result and 'rows' in field_result else []
        
        if not field_ids:
            return JSONResponse(content={
                "success": False,
                "error": "No fields found matching criteria"
            }, status_code=400)
        
        # Use the bulk task creation function
        query = "SELECT create_bulk_task(%s, %s, %s, %s, %s, %s)"
        result = db_manager.execute_query(
            query,
            (
                farmer_id,
                data['task_name'],
                data.get('task_type', 'other'),
                data.get('planned_date'),
                field_ids,
                data.get('notes')
            )
        )
        
        if result and 'rows' in result:
            task_id = result['rows'][0][0]
            
            return JSONResponse(content={
                "success": True,
                "task_id": task_id,
                "field_count": len(field_ids),
                "message": f"Task created for {len(field_ids)} fields"
            })
        else:
            raise Exception("Failed to create bulk task")
            
    except Exception as e:
        logger.error(f"Error creating bulk tasks: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.put("/{task_id}/complete", response_class=JSONResponse)
async def complete_task(task_id: int, request: Request, farmer: dict = Depends(require_auth)):
    """Mark a task as completed"""
    db_manager = get_db_manager()
    farmer_id = farmer['farmer_id']
    
    try:
        data = await request.json()
        
        # Verify task belongs to farmer
        verify_query = "SELECT id FROM tasks WHERE id = %s AND farmer_id = %s"
        verify_result = db_manager.execute_query(verify_query, (task_id, farmer_id))
        
        if not verify_result or 'rows' not in verify_result or not verify_result['rows']:
            return JSONResponse(content={
                "success": False,
                "error": "Task not found"
            }, status_code=404)
        
        # Update task status
        update_query = """
        UPDATE tasks 
        SET status = 'completed', 
            completed_date = %s,
            weather_conditions = %s,
            notes = COALESCE(notes || E'\\n' || %s, %s),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        db_manager.execute_query(
            update_query,
            (
                data.get('completed_date', date.today().isoformat()),
                data.get('weather_conditions'),
                data.get('completion_notes'),
                data.get('completion_notes'),
                task_id
            )
        )
        
        # Update material quantities if provided
        if data.get('materials_used'):
            for material in data['materials_used']:
                material_update = """
                UPDATE task_materials
                SET total_quantity = %s,
                    cost = %s
                WHERE task_id = %s AND material_id = %s
                """
                db_manager.execute_query(
                    material_update,
                    (
                        material['total_quantity'],
                        material.get('cost'),
                        task_id,
                        material['material_id']
                    )
                )
        
        return JSONResponse(content={
            "success": True,
            "message": "Task completed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/field-history/{field_id}", response_class=JSONResponse)
async def get_field_history(
    field_id: int, 
    year: Optional[int] = None,
    farmer: dict = Depends(require_auth)
):
    """Get activity history for a field"""
    db_manager = get_db_manager()
    farmer_id = farmer['farmer_id']
    
    try:
        # Verify field belongs to farmer
        verify_query = "SELECT id FROM fields WHERE id = %s AND farmer_id = %s"
        verify_result = db_manager.execute_query(verify_query, (field_id, farmer_id))
        
        if not verify_result or 'rows' not in verify_result or not verify_result['rows']:
            return JSONResponse(content={
                "success": False,
                "error": "Field not found"
            }, status_code=404)
        
        if year:
            # Use the stored function for specific year
            query = "SELECT * FROM get_field_history_by_year(%s, %s)"
            result = db_manager.execute_query(query, (field_id, year))
        else:
            # Get all history
            query = """
            SELECT 
                fh.activity_date,
                fh.activity_type,
                fh.description,
                fh.materials_used,
                fh.cost,
                t.task_name,
                t.notes
            FROM field_history fh
            LEFT JOIN tasks t ON fh.task_id = t.id
            WHERE fh.field_id = %s
            ORDER BY fh.activity_date DESC
            """
            result = db_manager.execute_query(query, (field_id,))
        
        history = []
        if result and 'rows' in result:
            for row in result['rows']:
                history.append({
                    'activity_date': row[0].isoformat() if row[0] else None,
                    'activity_type': row[1],
                    'description': row[2],
                    'materials_used': row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else [],
                    'cost': float(row[4]) if row[4] else 0,
                    'task_name': row[5] if len(row) > 5 else None,
                    'notes': row[6] if len(row) > 6 else None
                })
        
        return JSONResponse(content={
            "success": True,
            "field_id": field_id,
            "year": year,
            "history": history,
            "count": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error fetching field history: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/upcoming", response_class=JSONResponse)
async def get_upcoming_tasks(farmer: dict = Depends(require_auth)):
    """Get upcoming tasks for the farmer"""
    db_manager = get_db_manager()
    farmer_id = farmer['farmer_id']
    
    try:
        query = """
        SELECT 
            id, task_name, task_type, planned_date, 
            status, fields, total_area
        FROM upcoming_tasks
        WHERE farmer_id = %s
        LIMIT 10
        """
        result = db_manager.execute_query(query, (farmer_id,))
        
        tasks = []
        if result and 'rows' in result:
            for row in result['rows']:
                tasks.append({
                    'id': row[0],
                    'task_name': row[1],
                    'task_type': row[2],
                    'planned_date': row[3].isoformat() if row[3] else None,
                    'status': row[4],
                    'fields': row[5],
                    'total_area': float(row[6]) if row[6] else 0
                })
        
        return JSONResponse(content={
            "success": True,
            "tasks": tasks
        })
        
    except Exception as e:
        logger.error(f"Error fetching upcoming tasks: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/material/add", response_class=JSONResponse)
async def add_material(request: Request, farmer: dict = Depends(require_auth)):
    """Add a new material/product"""
    db_manager = get_db_manager()
    
    try:
        data = await request.json()
        
        # Validate required fields
        if not data.get('material_name'):
            return JSONResponse(content={
                "success": False,
                "error": "Material name is required"
            }, status_code=400)
        
        query = """
        INSERT INTO materials (material_name, material_type, manufacturer, active_ingredient, unit, cost_per_unit, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        result = db_manager.execute_query(
            query,
            (
                data['material_name'],
                data.get('material_type', 'other'),
                data.get('manufacturer'),
                data.get('active_ingredient'),
                data.get('unit', 'kg'),
                data.get('cost_per_unit'),
                data.get('notes')
            )
        )
        
        if result and 'rows' in result:
            material_id = result['rows'][0][0]
            
            return JSONResponse(content={
                "success": True,
                "material_id": material_id,
                "message": "Material added successfully"
            })
        else:
            raise Exception("Failed to add material")
            
    except Exception as e:
        logger.error(f"Error adding material: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)