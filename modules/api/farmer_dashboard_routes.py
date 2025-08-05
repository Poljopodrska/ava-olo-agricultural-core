#!/usr/bin/env python3
"""
Farmer Dashboard Routes - Personalized farmer data
Shows only the authenticated farmer's fields, weather, and messages
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from ..core.config import VERSION
from ..core.database_manager import get_db_manager
from ..auth.routes import get_current_farmer, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farmer", tags=["farmer-dashboard"])
templates = Jinja2Templates(directory="templates")

async def get_farmer_fields(farmer_id: int) -> List[Dict[str, Any]]:
    """Get all fields for a specific farmer with crop and last task info"""
    db_manager = get_db_manager()
    
    try:
        # Get fields with crop information and last task
        query = """
        SELECT 
            f.id, 
            f.field_name, 
            f.area_ha, 
            f.latitude, 
            f.longitude, 
            f.blok_id, 
            f.raba, 
            f.notes, 
            f.country,
            -- Get current crop info (most recent planting)
            fc.crop_type,
            fc.variety,
            fc.planting_date,
            -- Get last task info
            lt.task_type,
            lt.date_performed
        FROM fields f
        LEFT JOIN LATERAL (
            SELECT crop_type, variety, planting_date
            FROM field_crops
            WHERE field_id = f.id
            ORDER BY planting_date DESC
            LIMIT 1
        ) fc ON true
        LEFT JOIN LATERAL (
            SELECT task_type, date_performed
            FROM tasks
            WHERE field_id = f.id
            ORDER BY date_performed DESC
            LIMIT 1
        ) lt ON true
        WHERE f.farmer_id = %s
        ORDER BY f.field_name
        """
        results = db_manager.execute_query(query, (farmer_id,))
        
        fields = []
        if results and 'rows' in results:
            for row in results['rows']:
                field_data = {
                    'id': row[0],
                    'field_name': row[1],
                    'area_ha': row[2],
                    'latitude': row[3],
                    'longitude': row[4],
                    'blok_id': row[5],
                    'raba': row[6],
                    'notes': row[7],
                    'country': row[8],
                    'crop_type': row[9],
                    'variety': row[10],
                    'planting_date': row[11].strftime('%Y-%m-%d') if row[11] else None
                }
                
                # Add last task if exists
                if row[12]:  # task_type exists
                    field_data['last_task'] = {
                        'task_type': row[12],
                        'date_performed': row[13].strftime('%Y-%m-%d') if row[13] else None
                    }
                else:
                    field_data['last_task'] = None
                
                fields.append(field_data)
        
        return fields
    except Exception as e:
        logger.error(f"Error fetching farmer fields: {e}")
        return []

async def get_farmer_weather(farmer_id: int) -> Dict[str, Any]:
    """Get weather for farmer's location"""
    db_manager = get_db_manager()
    
    try:
        # Get farmer's city/location
        query = """
        SELECT city, country, latitude, longitude
        FROM farmers 
        WHERE id = %s
        """
        result = db_manager.execute_query(query, (farmer_id,))
        
        if result and 'rows' in result and len(result['rows']) > 0:
            city = result['rows'][0][0] or "Unknown"
            country = result['rows'][0][1] or "Unknown"
            
            # In production, this would call a weather API
            # For now, return mock data
            return {
                'location': f"{city}, {country}",
                'temperature': 22,
                'conditions': 'Partly Cloudy',
                'humidity': 65,
                'wind_speed': 12,
                'forecast': [
                    {'day': 'Today', 'high': 25, 'low': 18, 'conditions': 'Partly Cloudy'},
                    {'day': 'Tomorrow', 'high': 27, 'low': 19, 'conditions': 'Sunny'},
                    {'day': 'Day 3', 'high': 24, 'low': 17, 'conditions': 'Rainy'}
                ]
            }
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
    
    return {
        'location': 'Unknown',
        'temperature': '--',
        'conditions': 'Unavailable',
        'humidity': '--',
        'wind_speed': '--',
        'forecast': []
    }

async def get_farmer_messages(farmer_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    """Get last N messages for a farmer"""
    db_manager = get_db_manager()
    
    try:
        # Get farmer's WhatsApp number
        farmer_query = """
        SELECT COALESCE(whatsapp_number, wa_phone_number) 
        FROM farmers 
        WHERE id = %s
        """
        farmer_result = db_manager.execute_query(farmer_query, (farmer_id,))
        
        if not farmer_result or 'rows' not in farmer_result or not farmer_result['rows'] or not farmer_result['rows'][0][0]:
            return []
        
        wa_number = farmer_result['rows'][0][0]
        
        # Get messages
        query = """
        SELECT id, role, content, timestamp
        FROM chat_messages 
        WHERE wa_phone_number = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        results = db_manager.execute_query(query, (wa_number, limit))
        
        messages = []
        if results and 'rows' in results:
            for row in results['rows']:
                messages.append({
                    'id': row[0],
                    'role': row[1],
                    'content': row[2],
                    'timestamp': row[3].strftime('%Y-%m-%d %H:%M') if row[3] else '',
                    'is_farmer': row[1] == 'user'
                })
        
        # Reverse to show oldest first
        messages.reverse()
        
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return []

@router.get("/dashboard", response_class=HTMLResponse)
async def farmer_dashboard(request: Request, farmer: dict = Depends(require_auth)):
    """Main farmer dashboard - shows personalized data"""
    
    farmer_id = farmer['farmer_id']
    
    # Get farmer's data
    fields = await get_farmer_fields(farmer_id)
    weather = await get_farmer_weather(farmer_id)
    messages = await get_farmer_messages(farmer_id)
    
    # Calculate totals
    total_area = sum(field['area_ha'] for field in fields if field['area_ha'])
    
    # Get farmer's language preference and WhatsApp number
    db_manager = get_db_manager()
    farmer_result = db_manager.execute_query(
        "SELECT language_preference, COALESCE(whatsapp_number, wa_phone_number) as whatsapp_number FROM farmers WHERE id = %s", 
        (farmer_id,)
    )
    
    # Import language service
    from ..core.language_service import get_language_service
    language_service = get_language_service()
    
    detected_language = 'en'  # Default to English
    
    if farmer_result and 'rows' in farmer_result and farmer_result['rows']:
        stored_language = farmer_result['rows'][0][0]
        whatsapp_number = farmer_result['rows'][0][1]
        
        if stored_language:
            # Use stored language preference
            detected_language = stored_language
            logger.info(f"Using stored language preference for farmer {farmer_id}: {detected_language}")
        elif whatsapp_number:
            # Fall back to detecting from WhatsApp number
            detected_language = language_service.detect_language_from_whatsapp(whatsapp_number)
            logger.info(f"Language detected for farmer {farmer_id} from WhatsApp {whatsapp_number}: {detected_language}")
    
    # Get translations for the detected language
    from ..core.translations import get_translations, TranslationDict
    translations = get_translations(detected_language)
    
    # Wrap translations in TranslationDict for template attribute access
    if isinstance(translations, dict):
        translations = TranslationDict(translations)
    
    return templates.TemplateResponse("farmer/dashboard_v2.html", {
        "request": request,
        "version": VERSION,
        "farmer": farmer,
        "fields": fields,
        "total_fields": len(fields),
        "total_area": round(total_area, 2),
        "weather": weather,
        "messages": messages,
        "message_count": len(messages),
        "language": detected_language,
        "t": translations  # Add translations to template context
    })

@router.get("/api/fields", response_class=JSONResponse)
async def api_farmer_fields(farmer: dict = Depends(require_auth)):
    """API endpoint for farmer's fields"""
    fields = await get_farmer_fields(farmer['farmer_id'])
    return JSONResponse(content={
        "success": True,
        "fields": fields,
        "count": len(fields)
    })

@router.get("/api/weather", response_class=JSONResponse)
async def api_farmer_weather(farmer: dict = Depends(require_auth)):
    """API endpoint for farmer's weather"""
    weather = await get_farmer_weather(farmer['farmer_id'])
    return JSONResponse(content={
        "success": True,
        "weather": weather
    })

@router.get("/api/messages", response_class=JSONResponse)
async def api_farmer_messages(farmer: dict = Depends(require_auth), limit: int = 6):
    """API endpoint for farmer's messages"""
    messages = await get_farmer_messages(farmer['farmer_id'], limit)
    return JSONResponse(content={
        "success": True,
        "messages": messages,
        "count": len(messages)
    })

@router.post("/api/fields/add", response_class=JSONResponse)
async def api_add_field(request: Request, farmer: dict = Depends(require_auth)):
    """API endpoint to add a new field for the farmer"""
    
    try:
        data = await request.json()
        farmer_id = farmer['farmer_id']
        db_manager = get_db_manager()
        
        # Validate required fields
        if not data.get('field_name') or not data.get('area_ha'):
            return JSONResponse(content={
                "success": False,
                "error": "Field name and area are required"
            }, status_code=400)
        
        # Insert the new field with coordinates if provided
        if data.get('center_lat') and data.get('center_lng'):
            insert_query = """
            INSERT INTO fields (farmer_id, field_name, area_ha, latitude, longitude, country, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
            """
            result = db_manager.execute_query(
                insert_query,
                (farmer_id, data['field_name'], data['area_ha'], 
                 data['center_lat'], data['center_lng'],
                 data.get('country', farmer.get('country')))
            )
        else:
            insert_query = """
            INSERT INTO fields (farmer_id, field_name, area_ha, country, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id
            """
            result = db_manager.execute_query(
                insert_query,
                (farmer_id, data['field_name'], data['area_ha'], data.get('country', farmer.get('country')))
            )
        
        # Store polygon coordinates if provided
        if data.get('coordinates') and result and 'rows' in result and result['rows']:
            field_id = result['rows'][0][0]
            try:
                # Store coordinates as JSON in a separate table or field
                import json
                coordinates_json = json.dumps(data['coordinates'])
                
                # Check if field_boundaries table exists, if not store in notes column
                boundary_query = """
                UPDATE fields 
                SET notes = %s
                WHERE id = %s
                """
                db_manager.execute_query(boundary_query, (f"COORDINATES:{coordinates_json}", field_id))
            except Exception as e:
                logger.warning(f"Could not store field coordinates: {e}")
        
        result = result  # Keep the original result for further processing
        
        if result and 'rows' in result and result['rows']:
            field_id = result['rows'][0][0]
            
            # If crop type is provided, add crop information
            if data.get('crop_type'):
                crop_query = """
                INSERT INTO field_crops (field_id, crop_type, variety, planting_date, status)
                VALUES (%s, %s, %s, CURRENT_DATE, 'active')
                """
                db_manager.execute_query(
                    crop_query,
                    (field_id, data['crop_type'], data.get('variety', ''))
                )
            
            return JSONResponse(content={
                "success": True,
                "field_id": field_id,
                "message": "Field added successfully"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Failed to add field to database"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Error adding field: {e}")
        return JSONResponse(content={
            "success": False,
            "error": f"Failed to add field: {str(e)}"
        }, status_code=500)

@router.get("/api/stats", response_class=JSONResponse)
async def api_farmer_stats(farmer: dict = Depends(require_auth)):
    """API endpoint for farmer's statistics"""
    
    farmer_id = farmer['farmer_id']
    db_manager = get_db_manager()
    
    try:
        # Get field stats
        field_stats = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_fields,
                COALESCE(SUM(area_ha), 0) as total_area,
                COUNT(DISTINCT country) as countries
            FROM fields 
            WHERE farmer_id = %s
        """, (farmer_id,))
        
        # Get crop stats  
        crop_stats = db_manager.execute_query("""
            SELECT 
                COUNT(DISTINCT fc.crop_name) as crop_types,
                COUNT(*) as total_crops
            FROM field_crops fc
            JOIN fields f ON f.id = fc.field_id
            WHERE f.farmer_id = %s
        """, (farmer_id,))
        
        # Get task stats
        task_stats = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(*) FILTER (WHERE t.status = 'completed') as completed_tasks
            FROM tasks t
            JOIN task_fields tf ON t.id = tf.task_id
            JOIN fields f ON f.id = tf.field_id
            WHERE f.farmer_id = %s
        """, (farmer_id,))
        
        stats = {
            'fields': {
                'total': field_stats['rows'][0][0] if field_stats and 'rows' in field_stats and field_stats['rows'] else 0,
                'total_area': float(field_stats['rows'][0][1]) if field_stats and 'rows' in field_stats and field_stats['rows'] else 0,
                'countries': field_stats['rows'][0][2] if field_stats and 'rows' in field_stats and field_stats['rows'] else 0
            },
            'crops': {
                'types': crop_stats['rows'][0][0] if crop_stats and 'rows' in crop_stats and crop_stats['rows'] else 0,
                'total': crop_stats['rows'][0][1] if crop_stats and 'rows' in crop_stats and crop_stats['rows'] else 0
            },
            'tasks': {
                'total': task_stats['rows'][0][0] if task_stats and 'rows' in task_stats and task_stats['rows'] else 0,
                'completed': task_stats['rows'][0][1] if task_stats and 'rows' in task_stats and task_stats['rows'] else 0
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching farmer stats: {e}")
        return JSONResponse(content={
            "success": False,
            "error": "Failed to fetch statistics"
        }, status_code=500)