#!/usr/bin/env python3
"""
Simple cleanup endpoint
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

from ..core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/simple", tags=["simple"])

@router.post("/cleanup-keep-vrzel")
async def cleanup_keep_vrzel():
    """Simple cleanup - keep only Blaz Vrzel"""
    db_manager = get_db_manager()
    
    try:
        # Direct SQL to keep only Blaz Vrzel
        delete_query = """
        DELETE FROM farmers
        WHERE id NOT IN (
            SELECT id FROM farmers 
            WHERE LOWER(farm_name) LIKE '%vrzel%' 
            OR LOWER(manager_last_name) LIKE '%vrzel%'
            LIMIT 1
        )
        """
        
        # Get count before
        count_before = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
        before = count_before['rows'][0][0] if count_before else 0
        
        # Execute delete
        db_manager.execute_query(delete_query)
        
        # Get count after
        count_after = db_manager.execute_query("SELECT COUNT(*) FROM farmers")
        after = count_after['rows'][0][0] if count_after else 0
        
        return JSONResponse(content={
            "success": True,
            "before": before,
            "after": after,
            "deleted": before - after,
            "message": f"Kept {after} farmer(s) (Vrzel family)"
        })
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)