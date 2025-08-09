#!/usr/bin/env python3
"""
Simple debug endpoints for cache investigation
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
import json
import redis
import os

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/cache-status")
async def cache_status():
    """Simple cache status check"""
    try:
        # Direct Redis connection
        redis_host = os.getenv('REDIS_HOST', 'ava-redis-cluster.rwoelf.0001.use1.cache.amazonaws.com')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        # Test connection
        r.ping()
        
        # Check for Edi's cache
        cache_key = "welcome_package:49"
        exists = r.exists(cache_key)
        ttl = r.ttl(cache_key) if exists else 0
        
        result = {
            'redis_connected': True,
            'cache_exists': bool(exists),
            'ttl_seconds': ttl,
            'ttl_minutes': round(ttl / 60, 1) if ttl > 0 else 0
        }
        
        if exists:
            # Get the cached data
            cached_data = r.get(cache_key)
            if cached_data:
                package = json.loads(cached_data)
                
                # Extract key info
                result['cached_crops'] = []
                for crop in package.get('all_crops', []):
                    result['cached_crops'].append({
                        'field_name': crop.get('field_name'),
                        'crop': crop.get('crop'),
                        'variety': crop.get('variety')
                    })
                
                result['issue_found'] = None
                # Check for the issue
                for crop in result['cached_crops']:
                    if crop['field_name'] == '66' and crop['crop']:
                        result['issue_found'] = f"❌ Field 66 has {crop['crop']} in cache!"
                    elif crop['field_name'] == 'Tinetova lukna' and crop['crop'] == 'Corn':
                        result['tinetova_status'] = "✅ Tinetova has Corn"
                
        return JSONResponse(content=result)
        
    except redis.ConnectionError:
        return JSONResponse(content={
            'redis_connected': False,
            'error': 'Cannot connect to Redis'
        })
    except Exception as e:
        return JSONResponse(content={
            'error': str(e)
        })

@router.get("/debug/clear-cache")
async def clear_cache():
    """Clear Edi's cache"""
    try:
        redis_host = os.getenv('REDIS_HOST', 'ava-redis-cluster.rwoelf.0001.use1.cache.amazonaws.com')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        # Clear caches
        keys_deleted = 0
        keys_to_delete = [
            "welcome_package:49",
            "conversation:+393484446808",
            "conversation:393484446808",
            "chat_history:+393484446808"
        ]
        
        for key in keys_to_delete:
            keys_deleted += r.delete(key)
        
        return JSONResponse(content={
            'success': True,
            'keys_deleted': keys_deleted,
            'message': 'Cache cleared - next request will rebuild from database'
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        })