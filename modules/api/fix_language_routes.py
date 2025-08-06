#!/usr/bin/env python3
"""
Fix language preferences for existing users
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from ..core.database_manager import get_db_manager
from ..core.language_service import get_language_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fix", tags=["fix-language"])

@router.get("/italian-users-language")
async def fix_italian_users_language():
    """Fix language preferences for Italian users"""
    db_manager = get_db_manager()
    language_service = get_language_service()
    
    try:
        # Find all Italian users
        query = """
        SELECT id, name, whatsapp_number, language_preference
        FROM farmers 
        WHERE whatsapp_number LIKE '+39%' 
           OR whatsapp_number LIKE '39%'
        """
        
        result = db_manager.execute_query(query)
        
        if not result or 'rows' not in result:
            return JSONResponse({
                "status": "no_users",
                "message": "No Italian users found"
            })
        
        fixed_users = []
        already_correct = []
        
        for row in result['rows']:
            user_id, name, whatsapp, current_lang = row
            
            if current_lang != 'it':
                # Update to Italian
                update_query = """
                UPDATE farmers 
                SET language_preference = 'it' 
                WHERE id = %s
                """
                db_manager.execute_query(update_query, (user_id,))
                fixed_users.append({
                    "id": user_id,
                    "name": name,
                    "whatsapp": whatsapp,
                    "old_language": current_lang,
                    "new_language": "it"
                })
                logger.info(f"Updated user {user_id} ({name}) from {current_lang} to 'it'")
            else:
                already_correct.append({
                    "id": user_id,
                    "name": name,
                    "whatsapp": whatsapp,
                    "language": "it"
                })
        
        return JSONResponse({
            "status": "success",
            "fixed_users": fixed_users,
            "already_correct": already_correct,
            "total_fixed": len(fixed_users),
            "total_correct": len(already_correct)
        })
        
    except Exception as e:
        logger.error(f"Error fixing Italian users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all-users-language")
async def fix_all_users_language():
    """Auto-detect and fix language for all users based on WhatsApp"""
    db_manager = get_db_manager()
    language_service = get_language_service()
    
    try:
        # Get all users
        query = """
        SELECT id, name, whatsapp_number, language_preference
        FROM farmers 
        WHERE whatsapp_number IS NOT NULL
        ORDER BY id DESC
        """
        
        result = db_manager.execute_query(query)
        
        if not result or 'rows' not in result:
            return JSONResponse({
                "status": "no_users",
                "message": "No users found"
            })
        
        fixed_users = []
        already_correct = []
        
        for row in result['rows']:
            user_id, name, whatsapp, current_lang = row
            
            if whatsapp:
                # Detect language from WhatsApp
                detected_lang = language_service.detect_language_from_whatsapp(whatsapp)
                
                if current_lang != detected_lang:
                    # Update to detected language
                    update_query = """
                    UPDATE farmers 
                    SET language_preference = %s 
                    WHERE id = %s
                    """
                    db_manager.execute_query(update_query, (detected_lang, user_id))
                    fixed_users.append({
                        "id": user_id,
                        "name": name,
                        "whatsapp": whatsapp,
                        "old_language": current_lang,
                        "new_language": detected_lang
                    })
                    logger.info(f"Updated user {user_id} from {current_lang} to {detected_lang}")
                else:
                    already_correct.append({
                        "id": user_id,
                        "name": name,
                        "whatsapp": whatsapp,
                        "language": detected_lang
                    })
        
        return JSONResponse({
            "status": "success",
            "fixed_users": fixed_users,
            "already_correct": already_correct,
            "total_fixed": len(fixed_users),
            "total_correct": len(already_correct),
            "message": f"Fixed {len(fixed_users)} users, {len(already_correct)} were already correct"
        })
        
    except Exception as e:
        logger.error(f"Error fixing all users: {e}")
        raise HTTPException(status_code=500, detail=str(e))