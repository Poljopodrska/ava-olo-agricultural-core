#!/usr/bin/env python3
"""
Clear Redis cache for a specific farmer to force rebuild with new structure
"""
from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/debug/redis/clear/{farmer_id}")
async def clear_farmer_cache(farmer_id: int):
    """
    Clear Redis cache for a specific farmer
    This forces a rebuild with the new comprehensive structure
    """
    try:
        from modules.core.redis_config import RedisConfig
        
        redis_client = RedisConfig.get_redis_client()
        
        if not redis_client:
            return {"error": "Redis not configured"}
        
        cache_key = f"welcome_package:{farmer_id}"
        
        # Delete the old cache
        deleted = redis_client.delete(cache_key)
        
        if deleted:
            logger.info(f"Cleared Redis cache for farmer {farmer_id}")
            return {
                "success": True,
                "message": f"Cache cleared for farmer {farmer_id}",
                "cache_key": cache_key,
                "note": "Next request will rebuild with comprehensive data"
            }
        else:
            return {
                "success": False,
                "message": f"No cache found for farmer {farmer_id}",
                "cache_key": cache_key
            }
            
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/redis/ttl/{farmer_id}")
async def check_cache_ttl(farmer_id: int):
    """
    Check TTL (time to live) for a farmer's cache
    """
    try:
        from modules.core.redis_config import RedisConfig
        
        redis_client = RedisConfig.get_redis_client()
        
        if not redis_client:
            return {"error": "Redis not configured"}
        
        cache_key = f"welcome_package:{farmer_id}"
        
        # Get TTL
        ttl = redis_client.ttl(cache_key)
        
        if ttl == -2:
            return {
                "exists": False,
                "message": f"No cache for farmer {farmer_id}"
            }
        elif ttl == -1:
            return {
                "exists": True,
                "ttl": "No expiration",
                "message": "Cache exists but has no expiration"
            }
        else:
            hours = ttl // 3600
            minutes = (ttl % 3600) // 60
            return {
                "exists": True,
                "ttl_seconds": ttl,
                "ttl_human": f"{hours}h {minutes}m",
                "message": f"Cache expires in {hours}h {minutes}m"
            }
            
    except Exception as e:
        logger.error(f"Failed to check TTL: {e}")
        raise HTTPException(status_code=500, detail=str(e))