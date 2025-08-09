#!/usr/bin/env python3
"""
Debug endpoint to see what's actually in the Redis welcome package
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/edi-welcome-package")
async def debug_edi_welcome_package():
    """
    Show what's in Edi's welcome package (Redis cache)
    """
    from ..core.redis_manager import get_redis_client
    from ..core.welcome_package_manager import WelcomePackageManager
    from ..core.database_manager import get_db_manager
    
    result = {
        "farmer_id": 49,
        "redis_status": "unknown",
        "welcome_package": None,
        "crops_in_package": [],
        "fields_in_package": [],
        "issue_analysis": {}
    }
    
    try:
        # Get Redis client
        redis_client = get_redis_client()
        if redis_client:
            result['redis_status'] = "connected"
            
            # Try to get cached package
            cache_key = "welcome_package:49"
            cached_data = redis_client.get(cache_key)
            
            if cached_data:
                package = json.loads(cached_data)
                result['welcome_package'] = {
                    'exists': True,
                    'generated_at': package.get('generated_at'),
                    'expires_at': package.get('expires_at'),
                    'source': package.get('source')
                }
                
                # Extract crops
                for crop in package.get('all_crops', []):
                    crop_summary = {
                        'field_id': crop.get('field_id'),
                        'field_name': crop.get('field_name'),
                        'crop': crop.get('crop'),
                        'variety': crop.get('variety')
                    }
                    result['crops_in_package'].append(crop_summary)
                    
                    # Check for issues
                    if crop.get('field_name') == '66' and crop.get('crop'):
                        result['issue_analysis']['field_66_has_crop'] = f"❌ Field 66 has {crop.get('crop')} in cache!"
                    if crop.get('field_name') == 'Tinetova lukna' and crop.get('crop') == 'Corn':
                        result['issue_analysis']['tinetova_correct'] = "✅ Tinetova has Corn correctly"
                    if crop.get('field_name') == 'Biljenski' and crop.get('crop') == 'Vineyards':
                        result['issue_analysis']['biljenski_correct'] = "✅ Biljenski has Vineyards correctly"
                
                # Extract fields
                for field in package.get('fields', []):
                    field_summary = {
                        'id': field.get('id'),
                        'name': field.get('name') or field.get('field_name'),
                        'area_ha': field.get('area_ha'),
                        'crops': field.get('crops', [])
                    }
                    result['fields_in_package'].append(field_summary)
                    
                # Check TTL
                ttl = redis_client.ttl(cache_key)
                result['ttl_seconds'] = ttl
                result['ttl_info'] = f"Cache expires in {ttl} seconds ({ttl/60:.1f} minutes)"
                
            else:
                result['welcome_package'] = {'exists': False}
                result['ttl_info'] = "No cache found - will rebuild from database on next request"
        else:
            result['redis_status'] = "not connected"
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Debug error: {e}")
    
    # Try to build fresh from database
    try:
        db_manager = get_db_manager()
        wpm = WelcomePackageManager(redis_client, db_manager)
        
        # Force rebuild from database
        fresh_package = wpm._build_package_from_database(49)
        
        result['fresh_from_db'] = {
            'crops_count': len(fresh_package.get('all_crops', [])),
            'fields_count': len(fresh_package.get('fields', [])),
            'crops': []
        }
        
        for crop in fresh_package.get('all_crops', []):
            result['fresh_from_db']['crops'].append({
                'field_name': crop.get('field_name'),
                'crop': crop.get('crop'),
                'variety': crop.get('variety')
            })
            
    except Exception as e:
        result['fresh_from_db'] = {'error': str(e)}
    
    return JSONResponse(content=result)

@router.get("/debug/clear-edi-cache")
async def clear_edi_cache():
    """
    Force clear Edi's cache
    """
    from ..core.redis_manager import get_redis_client
    
    try:
        redis_client = get_redis_client()
        if redis_client:
            # Clear welcome package
            cache_key = "welcome_package:49"
            deleted = redis_client.delete(cache_key)
            
            # Clear conversation cache
            conv_keys = [
                "conversation:+393484446808",
                "conversation:393484446808",
                "chat_history:+393484446808"
            ]
            
            deleted_conv = 0
            for key in conv_keys:
                deleted_conv += redis_client.delete(key)
            
            return JSONResponse(content={
                'success': True,
                'welcome_package_deleted': bool(deleted),
                'conversation_keys_deleted': deleted_conv,
                'message': 'Cache cleared - next request will rebuild from database'
            })
        else:
            return JSONResponse(content={
                'success': False,
                'message': 'Redis not connected'
            })
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        })