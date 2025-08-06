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

@router.get("/test-auth")
async def test_farmer_auth(farmer: dict = Depends(require_auth)):
    """Test endpoint to check if auth is working"""
    return {"status": "ok", "farmer": farmer}

@router.get("/test-simple-dashboard", response_class=HTMLResponse)
async def test_simple_dashboard(request: Request, farmer: dict = Depends(require_auth)):
    """Simple test dashboard without complex data fetching"""
    return templates.TemplateResponse("farmer/dashboard.html", {
        "request": request,
        "version": VERSION,
        "farmer": farmer,
        "fields": [],
        "total_fields": 0,
        "total_area": 0,
        "weather": {"temperature": "20°C", "condition": "Sunny"},
        "messages": [],
        "message_count": 0
    })
templates = Jinja2Templates(directory="templates")

def get_farmer_language(farmer_id: int) -> str:
    """Get farmer's language preference from database"""
    db_manager = get_db_manager()
    
    try:
        query = """
        SELECT language_preference, whatsapp_number, country
        FROM farmers 
        WHERE id = %s
        """
        result = db_manager.execute_query(query, (farmer_id,))
        
        if result and 'rows' in result and len(result['rows']) > 0:
            language = result['rows'][0][0]
            whatsapp = result['rows'][0][1]
            country = result['rows'][0][2]
            logger.info(f"Farmer {farmer_id}: language={language}, whatsapp={whatsapp}, country={country}")
            
            # If language is not set, try to detect from WhatsApp number
            if not language and whatsapp:
                from ..core.language_service import get_language_service
                service = get_language_service()
                language = service.detect_language_from_whatsapp(whatsapp)
                logger.info(f"Detected language from WhatsApp {whatsapp}: {language}")
                
                # Update the database with detected language
                update_query = "UPDATE farmers SET language_preference = %s WHERE id = %s"
                db_manager.execute_query(update_query, (language, farmer_id))
                
            return language if language else 'en'
        return 'en'
    except Exception as e:
        logger.error(f"Error fetching farmer language: {e}")
        return 'en'

def get_farmer_fields(farmer_id: int) -> List[Dict[str, Any]]:
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
    """Get weather for farmer's location - Fixed to Logatec, Slovenia"""
    try:
        # Logatec, Slovenia coordinates
        LOGATEC_LAT = 45.9144
        LOGATEC_LON = 14.2258
        
        # Import weather service
        from ..weather.service import weather_service
        
        # Get current weather for Logatec
        current_weather = await weather_service.get_current_weather(LOGATEC_LAT, LOGATEC_LON)
        
        if current_weather:
            # Extract numeric temperature value
            temp_str = current_weather.get('temperature', '20°C')
            temperature = float(temp_str.replace('°C', '')) if '°C' in str(temp_str) else 20
            
            # Extract numeric humidity value
            humidity_str = current_weather.get('humidity', '60%')
            humidity = int(humidity_str.replace('%', '')) if '%' in str(humidity_str) else 60
            
            # Extract numeric wind speed
            wind_str = current_weather.get('wind_speed', '10 km/h')
            wind_speed = int(wind_str.split()[0]) if 'km/h' in str(wind_str) else 10
            
            # Get forecast data
            forecast_data = await weather_service.get_weather_forecast(LOGATEC_LAT, LOGATEC_LON, days=3)
            
            # Format forecast
            forecast = []
            if forecast_data and 'forecasts' in forecast_data:
                for i, day_forecast in enumerate(forecast_data['forecasts'][:3]):
                    day_names = ['Today', 'Tomorrow', 'Day 3']
                    # Extract numeric values from forecast
                    high_str = day_forecast.get('temp_max', '25°C')
                    low_str = day_forecast.get('temp_min', '18°C')
                    high = int(high_str.replace('°C', '')) if '°C' in str(high_str) else 25
                    low = int(low_str.replace('°C', '')) if '°C' in str(low_str) else 18
                    
                    forecast.append({
                        'day': day_names[i],
                        'high': high,
                        'low': low,
                        'conditions': day_forecast.get('description', 'Clear'),
                        'icon': day_forecast.get('icon', '☀️')
                    })
            else:
                # Default forecast if API fails
                forecast = [
                    {'day': 'Today', 'high': 25, 'low': 18, 'conditions': 'Partly Cloudy', 'icon': '⛅'},
                    {'day': 'Tomorrow', 'high': 27, 'low': 19, 'conditions': 'Sunny', 'icon': '☀️'},
                    {'day': 'Day 3', 'high': 24, 'low': 17, 'conditions': 'Cloudy', 'icon': '☁️'}
                ]
            
            return {
                'location': 'Logatec, Slovenia',
                'temperature': temperature,
                'conditions': current_weather.get('description', 'Clear'),
                'humidity': humidity,
                'wind_speed': wind_speed,
                'icon': current_weather.get('icon', '☀️'),
                'forecast': forecast
            }
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
    
    # Return default weather data for Logatec if API fails
    return {
        'location': 'Logatec, Slovenia',
        'temperature': 20,
        'conditions': 'Clear',
        'humidity': 60,
        'wind_speed': 10,
        'icon': '☀️',
        'forecast': [
            {'day': 'Today', 'high': 22, 'low': 14, 'conditions': 'Clear', 'icon': '☀️'},
            {'day': 'Tomorrow', 'high': 24, 'low': 16, 'conditions': 'Sunny', 'icon': '☀️'},
            {'day': 'Day 3', 'high': 23, 'low': 15, 'conditions': 'Partly Cloudy', 'icon': '⛅'}
        ]
    }

def get_farmer_messages(farmer_id: int, limit: int = 6) -> List[Dict[str, Any]]:
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
    
    try:
        farmer_id = farmer['farmer_id']
        
        # Get farmer's data
        fields = get_farmer_fields(farmer_id)
        weather = await get_farmer_weather(farmer_id)  # Now async with real weather data
        messages = get_farmer_messages(farmer_id)
        
        # Calculate totals
        total_area = sum(field['area_ha'] for field in fields if field['area_ha'])
        
        # Get farmer's language preference from database
        detected_language = get_farmer_language(farmer_id)
        logger.info(f"Farmer {farmer_id} language preference: {detected_language}")
        
        # Get translations
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
    except Exception as e:
        logger.error(f"Error rendering farmer dashboard: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@router.get("/api/fields", response_class=JSONResponse)
async def api_farmer_fields(farmer: dict = Depends(require_auth)):
    """API endpoint for farmer's fields"""
    fields = get_farmer_fields(farmer['farmer_id'])
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
    messages = get_farmer_messages(farmer['farmer_id'], limit)
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

@router.post("/update-location")
async def update_farmer_location(
    request: Request,
    farmer: dict = Depends(require_auth)
):
    """Update farmer's location information"""
    try:
        data = await request.json()
        db_manager = get_db_manager()
        
        # Extract location data
        street_address = data.get('street_address', '')
        house_number = data.get('house_number', '')
        postal_code = data.get('postal_code', '')
        city = data.get('city', '')
        country = data.get('country', '')
        
        # Optional: Get lat/lon from address (to be implemented with geocoding service)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Update farmer's location in database
        update_query = """
        UPDATE farmers 
        SET 
            street_address = %s,
            house_number = %s,
            postal_code = %s,
            city = %s,
            country = %s,
            weather_latitude = %s,
            weather_longitude = %s,
            weather_location_name = %s,
            address_collected = TRUE,
            location_prompt_shown = TRUE,
            location_updated_at = NOW()
        WHERE id = %s
        """
        
        # Create location name for weather service
        location_name = f"{city}, {country}" if city and country else None
        
        result = db_manager.execute_query(
            update_query,
            (street_address, house_number, postal_code, city, country, 
             latitude, longitude, location_name, farmer['id'])
        )
        
        if result and result.get('affected_rows', 0) > 0:
            return JSONResponse(content={
                "success": True,
                "message": "Location updated successfully"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": "Failed to update location"
            }, status_code=400)
            
    except Exception as e:
        logger.error(f"Error updating farmer location: {e}")
        return JSONResponse(content={
            "success": False,
            "error": f"Failed to update location: {str(e)}"
        }, status_code=500)

@router.get("/check-location")
async def check_farmer_location(farmer: dict = Depends(require_auth)):
    """Check if farmer has location data"""
    try:
        db_manager = get_db_manager()
        
        query = """
        SELECT 
            address_collected,
            street_address,
            house_number,
            postal_code,
            city,
            country,
            weather_latitude,
            weather_longitude,
            whatsapp_number
        FROM farmers 
        WHERE id = %s
        """
        
        result = db_manager.execute_query(query, (farmer['id'],))
        
        if result and 'rows' in result and result['rows']:
            row = result['rows'][0]
            return JSONResponse(content={
                "success": True,
                "has_location": bool(row[0]),  # address_collected
                "location": {
                    "street_address": row[1],
                    "house_number": row[2],
                    "postal_code": row[3],
                    "city": row[4],
                    "country": row[5],
                    "latitude": float(row[6]) if row[6] else None,
                    "longitude": float(row[7]) if row[7] else None
                },
                "whatsapp_number": row[8]
            })
        
        return JSONResponse(content={
            "success": False,
            "has_location": False
        })
        
    except Exception as e:
        logger.error(f"Error checking farmer location: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)