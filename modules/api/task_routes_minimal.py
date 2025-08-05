from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    field_id: Optional[int] = None
    due_date: Optional[str] = None

# Mock task storage
tasks = [
    {"id": 1, "title": "Water North Field", "status": "pending", "field_id": 1},
    {"id": 2, "title": "Check soil moisture", "status": "completed", "field_id": 1},
    {"id": 3, "title": "Apply fertilizer", "status": "pending", "field_id": 2}
]

@router.get("")
async def get_tasks(farmer_id: int = 1, status: Optional[str] = None):
    """Get farmer tasks"""
    filtered_tasks = tasks
    if status:
        filtered_tasks = [t for t in tasks if t["status"] == status]
    
    return JSONResponse(content={
        "tasks": filtered_tasks,
        "farmer_id": farmer_id,
        "total": len(filtered_tasks)
    })

@router.post("")
async def create_task(task: TaskCreate, farmer_id: int = 1):
    """Create new task"""
    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "description": task.description,
        "field_id": task.field_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "farmer_id": farmer_id
    }
    tasks.append(new_task)
    
    return JSONResponse(content={
        "success": True,
        "task": new_task
    })

@router.put("/{task_id}/status")
async def update_task_status(task_id: int, status: str):
    """Update task status"""
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = status
            return JSONResponse(content={
                "success": True,
                "task": task
            })
    
    return JSONResponse(content={
        "success": False,
        "message": "Task not found"
    }, status_code=404)