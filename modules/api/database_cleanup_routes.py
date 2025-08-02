#!/usr/bin/env python3
"""
Database cleanup routes - Clean up test data
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, List

from ..core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cleanup", tags=["cleanup"])

@router.get("/list-farmers")
async def list_farmers():
    """List all farmers in the database"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT 
            id,
            COALESCE(manager_name, '') as first_name,
            COALESCE(manager_last_name, '') as last_name,
            COALESCE(farm_name, '') as farm_name,
            COALESCE(whatsapp_number, wa_phone_number, phone) as phone,
            email,
            created_at
        FROM farmers
        ORDER BY id
        """
        
        result = db_manager.execute_query(query)
        
        farmers = []
        if result and 'rows' in result:
            for row in result['rows']:
                farmers.append({
                    "id": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "full_name": f"{row[1]} {row[2]}".strip(),
                    "farm_name": row[3],
                    "phone": row[4],
                    "email": row[5],
                    "created_at": str(row[6]) if row[6] else None
                })
        
        return JSONResponse(content={
            "success": True,
            "total": len(farmers),
            "farmers": farmers
        })
        
    except Exception as e:
        logger.error(f"Failed to list farmers: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/remove-test-farmers")
async def remove_test_farmers():
    """Remove all farmers except Blaz Vrzel (kmetija vrzel)"""
    db_manager = get_db_manager()
    
    try:
        # First, find Blaz Vrzel's ID
        find_blaz_query = """
        SELECT id, manager_name, manager_last_name, farm_name
        FROM farmers
        WHERE 
            LOWER(manager_name) LIKE '%blaz%' 
            OR LOWER(manager_last_name) LIKE '%vrzel%'
            OR LOWER(farm_name) LIKE '%vrzel%'
        """
        
        result = db_manager.execute_query(find_blaz_query)
        
        blaz_ids = []
        blaz_info = []
        if result and 'rows' in result:
            for row in result['rows']:
                blaz_ids.append(row[0])
                blaz_info.append({
                    "id": row[0],
                    "name": f"{row[1]} {row[2]}".strip(),
                    "farm": row[3]
                })
        
        if not blaz_ids:
            return JSONResponse(content={
                "success": False,
                "error": "Could not find Blaz Vrzel in the database",
                "message": "No farmers were deleted"
            })
        
        # Count farmers before deletion
        count_before_result = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
        count_before = count_before_result['rows'][0][0] if count_before_result and 'rows' in count_before_result else 0
        
        # Delete all farmers except Blaz Vrzel
        delete_query = """
        DELETE FROM farmers
        WHERE id NOT IN (%s)
        """ % ','.join(['%s'] * len(blaz_ids))
        
        db_manager.execute_query(delete_query, tuple(blaz_ids))
        
        # Count farmers after deletion
        count_after_result = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
        count_after = count_after_result['rows'][0][0] if count_after_result and 'rows' in count_after_result else 0
        
        deleted_count = count_before - count_after
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully removed {deleted_count} test farmers",
            "kept_farmers": blaz_info,
            "stats": {
                "before": count_before,
                "after": count_after,
                "deleted": deleted_count
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to remove test farmers: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/cleanup-specific")
async def cleanup_specific(farmer_ids: List[int]):
    """Remove specific farmers by ID"""
    db_manager = get_db_manager()
    
    try:
        if not farmer_ids:
            return JSONResponse(content={
                "success": False,
                "error": "No farmer IDs provided"
            })
        
        # Delete specified farmers
        delete_query = """
        DELETE FROM farmers
        WHERE id IN (%s)
        """ % ','.join(['%s'] * len(farmer_ids))
        
        db_manager.execute_query(delete_query, tuple(farmer_ids))
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully removed {len(farmer_ids)} farmers",
            "deleted_ids": farmer_ids
        })
        
    except Exception as e:
        logger.error(f"Failed to remove farmers: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)