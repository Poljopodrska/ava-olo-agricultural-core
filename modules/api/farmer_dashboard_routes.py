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
from ..core.simple_db import execute_simple_query
from ..auth.routes import get_current_farmer, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farmer", tags=["farmer-dashboard"])

@router.get("/test-auth")
async def test_farmer_auth(farmer: dict = Depends(require_auth)):
    """Test endpoint to check if auth is working"""
    return {"status": "ok", "farmer": farmer}

@router.get("/test-farmer-info")
async def test_farmer_info(request: Request, farmer: dict = Depends(require_auth)):
    """Get detailed farmer info for debugging"""
    return JSONResponse(content={
        "farmer_from_auth": farmer,
        "farmer_id": farmer.get('farmer_id') if farmer else None,
        "farmer_name": farmer.get('name') if farmer else None,
        "cookies": dict(request.cookies),
        "farmer_id_type": type(farmer.get('farmer_id')).__name__ if farmer and 'farmer_id' in farmer else None
    })

@router.post("/test-post")
async def test_post(request: Request):
    """Test POST endpoint without auth to verify routing"""
    try:
        data = await request.json()
        logger.info(f"Test POST received data: {data}")
        return JSONResponse(content={"success": True, "received": data})
    except Exception as e:
        logger.error(f"Test POST error: {e}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@router.post("/test-field-simple")
async def test_field_simple(request: Request):
    """Test field creation with hardcoded values to isolate issue"""
    try:
        # Get next available ID first
        max_id_query = "SELECT COALESCE(MAX(id), 0) + 1 FROM fields"
        max_id_result = execute_simple_query(max_id_query, ())
        
        if not max_id_result.get('success') or not max_id_result.get('rows'):
            return JSONResponse(content={
                "success": False,
                "error": "Could not determine next field ID",
                "database_working": False
            }, status_code=500)
        
        next_id = max_id_result['rows'][0][0]
        
        # Test with hardcoded values (without timestamp columns)
        test_query = """
        INSERT INTO fields (id, farmer_id, field_name, area_ha, country)
        VALUES (%s, 1, 'Test Field', 5.5, 'Slovenia')
        RETURNING id
        """
        
        logger.info(f"Attempting test field insertion with ID {next_id}...")
        result = execute_simple_query(test_query, (next_id,))
        
        if result and result.get('success') and 'rows' in result and result['rows']:
            field_id = result['rows'][0][0]
            logger.info(f"Test field created with ID: {field_id}")
            
            # Now delete it
            delete_query = "DELETE FROM fields WHERE id = %s"
            execute_simple_query(delete_query, (field_id,))
            
            return JSONResponse(content={
                "success": True,
                "message": f"Test successful! Created and deleted field ID {field_id}",
                "database_working": True
            })
        else:
            return JSONResponse(content={
                "success": False,
                "error": result.get('error', 'No result from INSERT'),
                "database_working": False
            }, status_code=500)
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Test field error: {e}\n{error_detail}")
        
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "database_working": False,
            "traceback": error_detail
        }, status_code=500)

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
    try:
        # First try to get language preference
        query = """
        SELECT language_preference
        FROM farmers 
        WHERE id = %s
        """
        result = execute_simple_query(query, (farmer_id,))
        
        if result and result.get('success') and 'rows' in result and len(result['rows']) > 0:
            language = result['rows'][0][0]
            
            # If we have a language preference, use it
            if language:
                logger.info(f"Farmer {farmer_id} has language preference: {language}")
                return language
            
            # If no language preference, try to detect from WhatsApp
            logger.info(f"Farmer {farmer_id} has no language preference, checking WhatsApp")
            
            # Get WhatsApp number (try all possible columns)
            phone_query = """
            SELECT COALESCE(whatsapp_number, wa_phone_number, phone) as phone
            FROM farmers 
            WHERE id = %s
            """
            phone_result = execute_simple_query(phone_query, (farmer_id,))
            
            if phone_result and phone_result.get('success') and 'rows' in phone_result and len(phone_result['rows']) > 0:
                whatsapp = phone_result['rows'][0][0]
                if whatsapp:
                    logger.info(f"Found WhatsApp number for farmer {farmer_id}: {whatsapp}")
                    from ..core.language_service import get_language_service
                    service = get_language_service()
                    detected_language = service.detect_language_from_whatsapp(whatsapp)
                    logger.info(f"Detected language: {detected_language}")
                    
                    # Save it for next time
                    try:
                        update_query = "UPDATE farmers SET language_preference = %s WHERE id = %s"
                        execute_simple_query(update_query, (detected_language, farmer_id))
                        logger.info(f"Saved language preference {detected_language} for farmer {farmer_id}")
                    except Exception as update_error:
                        logger.error(f"Could not update language preference: {update_error}")
                    
                    return detected_language
        
        logger.info(f"Defaulting to English for farmer {farmer_id}")
        return 'en'
    except Exception as e:
        logger.error(f"Error fetching farmer language: {e}")
        return 'en'

def get_farmer_fields(farmer_id: int) -> List[Dict[str, Any]]:
    """Get all fields for a specific farmer with crop and last task info"""
    try:
        # Simplified query - just get fields first, avoid complex JOINs that might fail
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
            f.country
        FROM fields f
        WHERE f.farmer_id = %s
        ORDER BY f.field_name
        """
        results = execute_simple_query(query, (farmer_id,))
        
        fields = []
        if results and results.get('success') and 'rows' in results:
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
                    'crop_type': None,  # Will be fetched separately if needed
                    'variety': None,
                    'planting_date': None,
                    'last_task': None
                }
                
                # Optionally fetch crop info for this field
                if row[0]:  # if field has an ID
                    crop_query = """
                    SELECT crop_type, variety, planting_date
                    FROM field_crops
                    WHERE field_id = %s
                    ORDER BY planting_date DESC
                    LIMIT 1
                    """
                    crop_result = execute_simple_query(crop_query, (row[0],))
                    if crop_result and crop_result.get('success') and crop_result.get('rows'):
                        crop_row = crop_result['rows'][0]
                        field_data['crop_type'] = crop_row[0]
                        field_data['variety'] = crop_row[1]
                        field_data['planting_date'] = crop_row[2].strftime('%Y-%m-%d') if crop_row[2] else None
                
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
        
        # Get hourly forecast for next 24 hours
        hourly_data = await weather_service.get_hourly_forecast(LOGATEC_LAT, LOGATEC_LON)
        
        # Get 5-day forecast
        forecast_data = await weather_service.get_weather_forecast(LOGATEC_LAT, LOGATEC_LON, days=5)
        
        # Build response with new format
        weather_response = {
            'location': 'Logatec, Slovenia',
            'rainfall_24h': 0,  # Default
            'hourly': [],
            'forecast': []
        }
        
        # Add rainfall from current weather if available
        if current_weather:
            weather_response['rainfall_24h'] = current_weather.get('rainfall_24h', 0)
            weather_response['temperature'] = current_weather.get('temperature', '20°C')
            weather_response['conditions'] = current_weather.get('description', 'Clear')
            weather_response['humidity'] = current_weather.get('humidity', '60%')
            weather_response['wind_speed'] = current_weather.get('wind_speed', '10 km/h')
            weather_response['icon'] = current_weather.get('icon', '☀️')
        
        # Add hourly forecast
        if hourly_data:
            for hour in hourly_data:
                weather_response['hourly'].append({
                    'time': hour['time'],
                    'temp': hour['temp'],
                    'icon': hour['icon'],
                    'rainfall': hour.get('rainfall_mm', 0),
                    'wind': hour['wind']['speed']
                })
        
        # Add 5-day forecast
        if forecast_data and 'forecasts' in forecast_data:
            for day_forecast in forecast_data['forecasts'][:5]:
                # Extract temperature values
                temp_max = day_forecast.get('temp_max', '25°C')
                temp_min = day_forecast.get('temp_min', '18°C')
                
                # Remove °C if present
                if isinstance(temp_max, str) and '°C' in temp_max:
                    temp_max = temp_max.replace('°C', '')
                if isinstance(temp_min, str) and '°C' in temp_min:
                    temp_min = temp_min.replace('°C', '')
                
                weather_response['forecast'].append({
                    'day': day_forecast.get('day_name', 'Day'),
                    'high': temp_max,
                    'low': temp_min,
                    'conditions': day_forecast.get('description', 'Clear'),
                    'icon': day_forecast.get('icon', '☀️'),
                    'rainfall': day_forecast.get('rainfall', '0 mm')
                })
        
        # Add default data if missing
        if not weather_response['hourly']:
            # Generate sample hourly data
            import datetime
            current_hour = datetime.datetime.now().hour
            for i in range(24):
                hour = (current_hour + i) % 24
                weather_response['hourly'].append({
                    'time': f"{hour:02d}:00",
                    'temp': 20 + (i % 5),
                    'icon': '☀️' if 6 <= hour <= 18 else '🌙',
                    'rainfall': 0,
                    'wind': 10
                })
        
        if not weather_response['forecast']:
            # Default 5-day forecast
            weather_response['forecast'] = [
                {'day': 'Today', 'high': '22', 'low': '14', 'conditions': 'Clear', 'icon': '☀️', 'rainfall': '0 mm'},
                {'day': 'Tomorrow', 'high': '24', 'low': '16', 'conditions': 'Sunny', 'icon': '☀️', 'rainfall': '0 mm'},
                {'day': 'Wednesday', 'high': '23', 'low': '15', 'conditions': 'Partly Cloudy', 'icon': '⛅', 'rainfall': '0 mm'},
                {'day': 'Thursday', 'high': '21', 'low': '13', 'conditions': 'Cloudy', 'icon': '☁️', 'rainfall': '2 mm'},
                {'day': 'Friday', 'high': '22', 'low': '14', 'conditions': 'Clear', 'icon': '☀️', 'rainfall': '0 mm'}
            ]
        
        return weather_response
        
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Return default weather data with new format
    import datetime
    current_hour = datetime.datetime.now().hour
    hourly_default = []
    for i in range(24):
        hour = (current_hour + i) % 24
        hourly_default.append({
            'time': f"{hour:02d}:00",
            'temp': 20 + (i % 5),
            'icon': '☀️' if 6 <= hour <= 18 else '🌙',
            'rainfall': 0,
            'wind': 10
        })
    
    return {
        'location': 'Logatec, Slovenia',
        'rainfall_24h': 0,
        'hourly': hourly_default,
        'forecast': [
            {'day': 'Today', 'high': '22', 'low': '14', 'conditions': 'Clear', 'icon': '☀️', 'rainfall': '0 mm'},
            {'day': 'Tomorrow', 'high': '24', 'low': '16', 'conditions': 'Sunny', 'icon': '☀️', 'rainfall': '0 mm'},
            {'day': 'Wednesday', 'high': '23', 'low': '15', 'conditions': 'Partly Cloudy', 'icon': '⛅', 'rainfall': '0 mm'},
            {'day': 'Thursday', 'high': '21', 'low': '13', 'conditions': 'Cloudy', 'icon': '☁️', 'rainfall': '2 mm'},
            {'day': 'Friday', 'high': '22', 'low': '14', 'conditions': 'Clear', 'icon': '☀️', 'rainfall': '0 mm'}
        ]
    }

def get_farmer_messages(farmer_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    """Get last N messages for a farmer"""
    try:
        # Get farmer's WhatsApp number
        farmer_query = """
        SELECT COALESCE(whatsapp_number, wa_phone_number) 
        FROM farmers 
        WHERE id = %s
        """
        farmer_result = execute_simple_query(farmer_query, (farmer_id,))
        
        if not farmer_result or not farmer_result.get('success') or 'rows' not in farmer_result or not farmer_result['rows'] or not farmer_result['rows'][0][0]:
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
        results = execute_simple_query(query, (wa_number, limit))
        
        messages = []
        if results and results.get('success') and 'rows' in results:
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
        from ..core.translations import get_translations
        translations = get_translations(detected_language)
        
        logger.info(f"Loaded translations for language '{detected_language}': {translations}")
        
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
        # Log the incoming request with all details
        logger.info(f"=== FIELD CREATION START ===")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request cookies: {request.cookies}")
        logger.info(f"Farmer object from auth: {farmer}")
        logger.info(f"Farmer type: {type(farmer)}")
        
        data = await request.json()
        logger.info(f"Request data: {data}")
        
        # Check if farmer_id exists
        if not farmer or 'farmer_id' not in farmer:
            logger.error(f"Invalid farmer object: {farmer}")
            return JSONResponse(content={
                "success": False,
                "error": "Authentication error - no farmer ID found",
                "farmer_object": str(farmer)
            }, status_code=401)
        
        farmer_id = farmer['farmer_id']
        logger.info(f"Farmer ID extracted: {farmer_id}, type: {type(farmer_id)}")
        
        # Ensure farmer_id is an integer
        try:
            farmer_id = int(farmer_id)
            logger.info(f"Farmer ID converted to int: {farmer_id}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid farmer_id format: {farmer_id}, error: {e}")
            return JSONResponse(content={
                "success": False,
                "error": f"Invalid farmer ID format: {farmer_id}"
            }, status_code=400)
        
        db_manager = get_db_manager()
        
        logger.info(f"Adding field for farmer {farmer_id}: {data}")
        
        # Validate required fields
        if not data.get('field_name') or not data.get('area_ha'):
            return JSONResponse(content={
                "success": False,
                "error": "Field name and area are required"
            }, status_code=400)
        
        # Convert area_ha to float
        try:
            area_ha = float(data['area_ha'])
        except (ValueError, TypeError):
            return JSONResponse(content={
                "success": False,
                "error": "Invalid area value"
            }, status_code=400)
        
        # First, get the next available ID to avoid sequence issues
        max_id_query = "SELECT COALESCE(MAX(id), 0) + 1 FROM fields"
        max_id_result = execute_simple_query(max_id_query, ())
        
        if not max_id_result.get('success') or not max_id_result.get('rows'):
            return JSONResponse(content={
                "success": False,
                "error": "Could not determine next field ID"
            }, status_code=500)
        
        next_id = max_id_result['rows'][0][0]
        logger.info(f"Next available field ID: {next_id}")
        
        # Insert the new field with explicit ID to avoid sequence issues
        # Use simple_db to avoid context manager issues
        if data.get('center_lat') and data.get('center_lng'):
            insert_query = """
            INSERT INTO fields (id, farmer_id, field_name, area_ha, latitude, longitude, country)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            result = execute_simple_query(
                insert_query,
                (next_id, farmer_id, data['field_name'], area_ha, 
                 float(data['center_lat']), float(data['center_lng']),
                 data.get('country', farmer.get('country', 'Slovenia')))
            )
        else:
            insert_query = """
            INSERT INTO fields (id, farmer_id, field_name, area_ha, country)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """
            result = execute_simple_query(
                insert_query,
                (next_id, farmer_id, data['field_name'], area_ha, 
                 data.get('country', farmer.get('country', 'Slovenia')))
            )
        
        # Check if the query was successful
        if not result.get('success'):
            logger.error(f"Field creation failed: {result.get('error')}")
            return JSONResponse(content={
                "success": False,
                "error": f"Database error: {result.get('error', 'Unknown error')}"
            }, status_code=500)
        
        # Store polygon coordinates if provided
        if data.get('coordinates') and result.get('rows'):
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
                execute_simple_query(boundary_query, (f"COORDINATES:{coordinates_json}", field_id))
            except Exception as e:
                logger.warning(f"Could not store field coordinates: {e}")
        
        # Log the result
        logger.info(f"Field insert result: {result}")
        
        if result.get('success') and result.get('rows'):
            field_id = result['rows'][0][0]
            logger.info(f"Field created with ID: {field_id}")
            
            # If crop type is provided, add crop information
            if data.get('crop_type'):
                crop_query = """
                INSERT INTO field_crops (field_id, crop_type, variety, planting_date, status)
                VALUES (%s, %s, %s, CURRENT_DATE, 'active')
                """
                try:
                    crop_result = execute_simple_query(
                        crop_query,
                        (field_id, data['crop_type'], data.get('variety', ''))
                    )
                    if crop_result.get('success'):
                        logger.info(f"Crop type '{data['crop_type']}' added to field {field_id}")
                    else:
                        logger.warning(f"Could not add crop type: {crop_result.get('error')}")
                except Exception as e:
                    logger.warning(f"Could not add crop type: {e}")
            
            # Verify the field was created by fetching it
            verify_query = """
            SELECT id, field_name, area_ha FROM fields WHERE id = %s
            """
            verification = execute_simple_query(verify_query, (field_id,))
            
            if verification.get('success') and verification.get('rows'):
                logger.info(f"Field verified in database: {verification['rows'][0]}")
            else:
                logger.warning(f"Could not verify field {field_id} after creation")
            
            return JSONResponse(content={
                "success": True,
                "field_id": field_id,
                "message": "Field added successfully"
            })
        else:
            logger.error(f"Failed to get field ID from insert result: {result}")
            return JSONResponse(content={
                "success": False,
                "error": "Failed to add field to database"
            }, status_code=500)
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error adding field: {e}\n{error_detail}")
        
        # Return more specific error message
        error_message = str(e)
        if "fields" in error_message and "does not exist" in error_message:
            error_message = "Fields table does not exist in database. Please contact support."
        elif "field_crops" in error_message and "does not exist" in error_message:
            error_message = "Field crops table does not exist in database. Please contact support."
        elif "foreign key" in error_message.lower():
            error_message = "Invalid farmer ID or database constraint error."
        elif "connection" in error_message.lower():
            error_message = "Database connection error. Please try again."
        
        return JSONResponse(content={
            "success": False,
            "error": error_message,
            "details": str(e),
            "farmer_id": farmer_id if 'farmer_id' in locals() else "not_set"
        }, status_code=500)

@router.get("/api/stats", response_class=JSONResponse)
async def api_farmer_stats(farmer: dict = Depends(require_auth)):
    """API endpoint for farmer's statistics"""
    
    farmer_id = farmer['farmer_id']
    
    try:
        # Get field stats
        field_stats = execute_simple_query("""
            SELECT 
                COUNT(*) as total_fields,
                COALESCE(SUM(area_ha), 0) as total_area,
                COUNT(DISTINCT country) as countries
            FROM fields 
            WHERE farmer_id = %s
        """, (farmer_id,))
        
        # Get crop stats  
        crop_stats = execute_simple_query("""
            SELECT 
                COUNT(DISTINCT fc.crop_name) as crop_types,
                COUNT(*) as total_crops
            FROM field_crops fc
            JOIN fields f ON f.id = fc.field_id
            WHERE f.farmer_id = %s
        """, (farmer_id,))
        
        # Get task stats
        task_stats = execute_simple_query("""
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
                'total': field_stats['rows'][0][0] if field_stats and field_stats.get('success') and 'rows' in field_stats and field_stats['rows'] else 0,
                'total_area': float(field_stats['rows'][0][1]) if field_stats and field_stats.get('success') and 'rows' in field_stats and field_stats['rows'] else 0,
                'countries': field_stats['rows'][0][2] if field_stats and field_stats.get('success') and 'rows' in field_stats and field_stats['rows'] else 0
            },
            'crops': {
                'types': crop_stats['rows'][0][0] if crop_stats and crop_stats.get('success') and 'rows' in crop_stats and crop_stats['rows'] else 0,
                'total': crop_stats['rows'][0][1] if crop_stats and crop_stats.get('success') and 'rows' in crop_stats and crop_stats['rows'] else 0
            },
            'tasks': {
                'total': task_stats['rows'][0][0] if task_stats and task_stats.get('success') and 'rows' in task_stats and task_stats['rows'] else 0,
                'completed': task_stats['rows'][0][1] if task_stats and task_stats.get('success') and 'rows' in task_stats and task_stats['rows'] else 0
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
        
        result = execute_simple_query(
            update_query,
            (street_address, house_number, postal_code, city, country, 
             latitude, longitude, location_name, farmer['id'])
        )
        
        if result and result.get('success') and result.get('affected_rows', 0) > 0:
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
        
        result = execute_simple_query(query, (farmer['id'],))
        
        if result and result.get('success') and 'rows' in result and result['rows']:
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