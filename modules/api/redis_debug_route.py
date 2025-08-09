#!/usr/bin/env python3
"""
Debug Redis and welcome package for Edi
"""
from fastapi import APIRouter, HTTPException
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/redis/{phone_number}")
async def debug_redis_for_phone(phone_number: str):
    """
    Debug Redis welcome package for a specific phone number
    """
    results = {
        "phone_input": phone_number,
        "redis_status": "unknown",
        "farmer_lookup": {},
        "welcome_package": {},
        "redis_direct": {},
        "errors": []
    }
    
    # 1. Check Redis configuration
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT', '6379')
    results["redis_config"] = {
        "host": redis_host if redis_host else "NOT CONFIGURED",
        "port": redis_port,
        "configured": bool(redis_host)
    }
    
    # 2. Find farmer by phone number
    from modules.core.simple_db import execute_simple_query
    
    # Try with + and without
    phone_variants = [phone_number, phone_number.lstrip('+'), '+' + phone_number.lstrip('+')]
    farmer_id = None
    
    for variant in phone_variants:
        query = """
            SELECT id, manager_name, manager_last_name, wa_phone_number, phone
            FROM farmers 
            WHERE wa_phone_number = %s OR phone = %s
            LIMIT 1
        """
        result = execute_simple_query(query, (variant, variant))
        
        if result['success'] and result['rows']:
            row = result['rows'][0]
            farmer_id = row[0]
            results["farmer_lookup"] = {
                "found": True,
                "variant_matched": variant,
                "farmer_id": farmer_id,
                "name": f"{row[1]} {row[2]}",
                "wa_phone": row[3],
                "phone": row[4]
            }
            break
    
    if not farmer_id:
        results["farmer_lookup"]["found"] = False
        results["errors"].append(f"No farmer found for phone {phone_number}")
        return results
    
    # 3. Check if Redis is actually available
    try:
        from modules.core.redis_config import RedisConfig
        redis_client = RedisConfig.get_redis_client()
        
        if redis_client:
            results["redis_status"] = "connected"
            
            # 4. Check if welcome package exists in Redis
            cache_key = f"welcome_package:{farmer_id}"
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    import json
                    package = json.loads(cached_data)
                    results["welcome_package"] = {
                        "exists": True,
                        "cache_key": cache_key,
                        "fields_count": len(package.get('fields', [])),
                        "fields": package.get('fields', [])[:3],  # First 3 fields
                        "farmer_info": package.get('farmer_info', {}),
                        "generated_at": package.get('generated_at', 'unknown')
                    }
                else:
                    results["welcome_package"]["exists"] = False
                    results["welcome_package"]["cache_key"] = cache_key
                    
                    # Try to build it now
                    logger.info(f"Building welcome package for farmer {farmer_id}")
                    from modules.core.welcome_package_manager import WelcomePackageManager
                    
                    class SimpleDBOps:
                        def execute_query(self, query, params):
                            return execute_simple_query(query, params)
                    
                    db_ops = SimpleDBOps()
                    manager = WelcomePackageManager(redis_client, db_ops)
                    
                    # Force build
                    package = manager._build_and_cache_package(farmer_id)
                    
                    results["welcome_package"]["built_now"] = True
                    results["welcome_package"]["fields_count"] = len(package.get('fields', []))
                    results["welcome_package"]["fields"] = package.get('fields', [])[:3]
                    
            except Exception as e:
                results["errors"].append(f"Redis operation error: {str(e)}")
                results["redis_status"] = f"error: {str(e)}"
        else:
            results["redis_status"] = "not_available"
            results["errors"].append("Redis client is None - not configured")
            
    except Exception as e:
        results["redis_status"] = f"connection_failed: {str(e)}"
        results["errors"].append(f"Redis connection failed: {str(e)}")
    
    # 5. Get fields directly from database for comparison
    fields_query = """
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = %s
    """
    fields_result = execute_simple_query(fields_query, (farmer_id,))
    
    if fields_result['success']:
        results["database_fields"] = {
            "count": len(fields_result['rows']),
            "fields": [
                {
                    "id": row[0],
                    "name": row[1],
                    "area_ha": float(row[2]) if row[2] else 0
                }
                for row in fields_result['rows']
            ]
        }
    
    # 6. Summary
    results["summary"] = {
        "farmer_found": bool(farmer_id),
        "farmer_id": farmer_id,
        "redis_available": results["redis_status"] == "connected",
        "welcome_package_exists": results.get("welcome_package", {}).get("exists", False),
        "fields_in_db": results.get("database_fields", {}).get("count", 0),
        "fields_in_redis": results.get("welcome_package", {}).get("fields_count", 0)
    }
    
    return results

@router.post("/debug/redis/rebuild/{farmer_id}")
async def rebuild_welcome_package(farmer_id: int):
    """
    Force rebuild welcome package for a farmer
    """
    try:
        from modules.core.redis_config import RedisConfig
        from modules.core.welcome_package_manager import WelcomePackageManager
        from modules.core.simple_db import execute_simple_query
        
        redis_client = RedisConfig.get_redis_client()
        
        if not redis_client:
            return {"error": "Redis not configured"}
        
        class SimpleDBOps:
            def execute_query(self, query, params):
                return execute_simple_query(query, params)
        
        db_ops = SimpleDBOps()
        manager = WelcomePackageManager(redis_client, db_ops)
        
        # Force rebuild
        package = manager._build_and_cache_package(farmer_id)
        
        return {
            "success": True,
            "farmer_id": farmer_id,
            "fields_count": len(package.get('fields', [])),
            "package_keys": list(package.keys())
        }
        
    except Exception as e:
        return {"error": str(e)}