#!/usr/bin/env python3
"""
Debug Services Endpoint
Verify AI connection and weather location
"""
import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import logging

from modules.core.database_manager import get_db_manager
from modules.chat.openai_chat import get_openai_chat
from modules.location.location_service import get_location_service
from modules.weather.service import weather_service
# from modules.auth.security import get_current_farmer  # TODO: Module missing

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/v1/debug/services")
async def debug_services(request: Request):
    """Comprehensive service connection status"""
    
    # Get current farmer from session
    farmer_id = request.session.get('farmer_id', 1)  # Default to farmer 1 for testing
    
    # Test OpenAI
    openai_status = await test_openai_connection()
    
    # Test Weather
    weather_status = await test_weather_service(farmer_id)
    
    # Get farmer location
    location_info = await get_farmer_location_info(farmer_id)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "farmer_id": farmer_id,
        "services": {
            "openai": openai_status,
            "weather": weather_status,
            "location": location_info,
            "database": {
                "connected": True,  # Obviously true if this endpoint works
                "farmer_logged_in": farmer_id is not None
            }
        }
    }

async def test_openai_connection():
    """Test OpenAI connection and functionality"""
    result = {
        "api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "api_key_preview": os.getenv("OPENAI_API_KEY", "")[:10] + "..." if os.getenv("OPENAI_API_KEY") else None,
        "connection_test": "Not tested",
        "chat_instance_connected": False,
        "test_response": None
    }
    
    try:
        # Get chat instance
        chat_service = get_openai_chat()
        result["chat_instance_connected"] = chat_service.connected
        
        # Test actual API call
        if result["api_key_set"]:
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "What is 2+2? Answer with just the number."}
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data['choices'][0]['message']['content'].strip()
                    result["connection_test"] = "✅ Working"
                    result["test_response"] = answer
                    
                    # If AI works but shows as disconnected, this is the issue
                    if answer == "4" and not chat_service.connected:
                        result["issue_found"] = "AI works but shows disconnected - connection test needs fix"
                else:
                    result["connection_test"] = f"❌ Failed: HTTP {response.status_code}"
                    result["error"] = response.text
                    
    except Exception as e:
        result["connection_test"] = f"❌ Error: {str(e)}"
        result["error"] = str(e)
    
    return result

async def test_weather_service(farmer_id: int = None):
    """Test weather service and location"""
    result = {
        "api_key_set": bool(os.getenv("OPENWEATHER_API_KEY")),
        "test_location": "Ljubljana, Slovenia",
        "coordinates": {"lat": 46.0569, "lon": 14.5058},
        "weather_data": None,
        "actual_location": None
    }
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        result["error"] = "No API key"
        return result
    
    try:
        # Test with Ljubljana coordinates
        lat, lon = 46.0569, 14.5058
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result["weather_data"] = {
                    "temperature": data['main']['temp'],
                    "description": data['weather'][0]['description'],
                    "humidity": data['main']['humidity'],
                    "wind_speed": data['wind']['speed']
                }
                result["actual_location"] = f"{data['name']}, {data['sys']['country']}"
                result["status"] = "✅ Working"
            else:
                result["status"] = f"❌ Failed: HTTP {response.status_code}"
                
    except Exception as e:
        result["status"] = f"❌ Error: {str(e)}"
        result["error"] = str(e)
    
    return result

async def get_farmer_location_info(farmer_id: int = None):
    """Get farmer location information"""
    if not farmer_id:
        return {"status": "No farmer logged in"}
    
    try:
        db_manager = get_db_manager()
        query = """
        SELECT name, city, address, country, latitude, longitude
        FROM farmers
        WHERE farmer_id = %s
        """
        
        result = db_manager.execute_query(query, (farmer_id,))
        
        if result and result.get('rows'):
            row = result['rows'][0]
            name, city, address, country, lat, lon = row
            
            return {
                "farmer_name": name,
                "city": city or "Ljubljana",
                "country": country or "Slovenia",
                "address": address,
                "coordinates": {
                    "lat": float(lat) if lat else 46.0569,
                    "lon": float(lon) if lon else 14.5058,
                    "source": "database" if lat else "default"
                }
            }
    except Exception as e:
        logger.error(f"Error getting farmer location: {e}")
        
    return {"status": "Error getting location", "using_default": True}

@router.post("/api/v1/chat/test")
async def test_chat_farming():
    """Test chat with farming questions"""
    
    test_questions = [
        "What's the best time to plant tomatoes in Ljubljana?",
        "How much water do mango trees need?",
        "When should I harvest corn in Slovenia?"
    ]
    
    results = []
    chat_service = get_openai_chat()
    
    for question in test_questions:
        try:
            # Use the actual chat service method
            response = await chat_service.send_message(
                session_id="test_session",
                message=question,
                farmer_context={
                    "location": "Ljubljana, Slovenia",
                    "test": True
                }
            )
            
            results.append({
                "question": question,
                "response": response[:200] + "..." if len(response) > 200 else response,
                "success": True,
                "length": len(response)
            })
        except Exception as e:
            results.append({
                "question": question,
                "error": str(e),
                "success": False
            })
    
    return {
        "test_results": results,
        "all_successful": all(r["success"] for r in results),
        "chat_connected": chat_service.connected
    }

@router.get("/api/v1/debug/services/detailed")
async def debug_services_detailed(request: Request):
    """Detailed service status with proof"""
    
    farmer_id = request.session.get("farmer_id", 1)  # Default to farmer 1
    
    # Test OpenAI with actual question
    openai_test = {}
    try:
        chat_service = get_openai_chat()
        test_result = await chat_service.send_message(
            "test_debug_session",
            "What's the best time to plant tomatoes in Ljubljana?",
            {"location": "Ljubljana, Slovenia", "weather": "Partly Cloudy", "temperature": 18}
        )
        openai_test = {
            "status": "connected" if chat_service.connected else "disconnected",
            "api_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "api_key_preview": os.getenv("OPENAI_API_KEY", "")[:8] + "..." if os.getenv("OPENAI_API_KEY") else None,
            "test_response": test_result.get('response', '')[:100] + "...",
            "model": test_result.get('model', 'unknown'),
            "connected": test_result.get('connected', False),
            "timestamp": test_result.get('timestamp')
        }
    except Exception as e:
        openai_test = {"status": "error", "error": str(e)}
    
    # Test Weather with proof
    weather_test = {}
    try:
        # Get weather for Ljubljana
        weather_data = await weather_service.get_current_weather()
        weather_test = {
            "status": "connected" if weather_service.api_key else "no_api_key",
            "api_key_set": bool(weather_service.api_key),
            "api_key_preview": weather_service.api_key[:8] + "..." if weather_service.api_key else None,
            "current_weather": {
                "temperature": weather_data.get('temperature'),
                "description": weather_data.get('description'),
                "humidity": weather_data.get('humidity'),
                "location": weather_data.get('location')
            },
            "proof": weather_data.get('proof', {}),
            "timestamp": weather_data.get('timestamp')
        }
    except Exception as e:
        weather_test = {"status": "error", "error": str(e)}
    
    # Get farmer location
    location_test = {}
    try:
        db_manager = get_db_manager()
        query = """
        SELECT f.id, f.name, f.city, f.country,
               COUNT(DISTINCT fi.id) as field_count,
               COALESCE(SUM(fi.size_hectares), 0) as total_hectares
        FROM ava_farmers f
        LEFT JOIN ava_fields fi ON f.id = fi.farmer_id
        WHERE f.id = %s
        GROUP BY f.id, f.name, f.city, f.country
        """
        
        result = db_manager.execute_query(query, (farmer_id,))
        
        if result and result.get('rows'):
            row = result['rows'][0]
            location_test = {
                "farmer_id": row[0],
                "farmer_name": row[1],
                "city": row[2] or "Ljubljana",
                "country": row[3] or "Slovenia",
                "field_count": row[4],
                "total_hectares": float(row[5]) if row[5] else 0
            }
    except Exception as e:
        location_test = {"status": "error", "error": str(e)}
    
    return {
        "timestamp": datetime.now().isoformat(),
        "openai": openai_test,
        "weather": weather_test,
        "farmer": location_test,
        "environment": {
            "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT SET",
            "OPENWEATHER_API_KEY": "SET" if os.getenv("OPENWEATHER_API_KEY") else "NOT SET",
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development")
        }
    }

@router.get("/api/v1/debug/check-edi-kante")
async def check_edi_kante_fields():
    """Debug endpoint to check if Edi Kante has fields in database"""
    
    try:
        db_manager = get_db_manager()
        
        # Step 1: Search for Edi Kante in farmers table
        search_query = """
        SELECT id, manager_name, manager_last_name, farm_name, email, 
               phone, wa_phone_number, created_at, city, country
        FROM farmers 
        WHERE LOWER(manager_name) LIKE '%edi%' 
           OR LOWER(manager_last_name) LIKE '%kante%'
           OR LOWER(farm_name) LIKE '%edi%'
           OR LOWER(farm_name) LIKE '%kante%'
        ORDER BY created_at DESC
        """
        
        farmer_result = db_manager.execute_query(search_query)
        
        if not farmer_result or 'rows' not in farmer_result or len(farmer_result['rows']) == 0:
            # Get some sample farmers for reference
            sample_query = """
            SELECT manager_name, manager_last_name, farm_name, city, created_at
            FROM farmers 
            ORDER BY created_at DESC 
            LIMIT 10
            """
            sample_result = db_manager.execute_query(sample_query)
            
            total_query = "SELECT COUNT(*) FROM farmers"
            total_result = db_manager.execute_query(total_query)
            total_farmers = total_result['rows'][0][0] if total_result and 'rows' in total_result else 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "edi_kante_found": False,
                "assessment": "FARMER NOT FOUND - FAVA registration failing",
                "total_farmers": total_farmers,
                "recent_farmers": [
                    {
                        "name": f"{row[0] or ''} {row[1] or ''}".strip(),
                        "farm": row[2] or "No farm name",
                        "city": row[3] or "No city",
                        "created": str(row[4]) if row[4] else "No date"
                    } for row in sample_result['rows']
                ] if sample_result and 'rows' in sample_result else [],
                "recommendation": "Check FAVA farmer registration process - Edi Kante not in database"
            }
        
        # Found farmer(s) - get their details
        farmers_found = []
        all_fields = []
        
        for row in farmer_result['rows']:
            farmer_id = row[0]
            name = f"{row[1] or ''} {row[2] or ''}".strip()
            farm_name = row[3] or 'No farm name'
            city = row[8] or 'No city'
            country = row[9] or 'No country'
            
            farmer_info = {
                "farmer_id": farmer_id,
                "name": name,
                "farm_name": farm_name,
                "location": f"{city}, {country}",
                "created": str(row[7]) if row[7] else "No date"
            }
            
            # Step 2: Get fields for this farmer
            fields_query = """
            SELECT id, field_name, area_ha, latitude, longitude, 
                   created_at, blok_id, raba
            FROM fields 
            WHERE farmer_id = %s
            ORDER BY created_at DESC
            """
            
            fields_result = db_manager.execute_query(fields_query, (farmer_id,))
            
            farmer_fields = []
            if fields_result and 'rows' in fields_result:
                for field_row in fields_result['rows']:
                    field_info = {
                        "field_id": field_row[0],
                        "field_name": field_row[1] or 'Unnamed field',
                        "area_ha": float(field_row[2]) if field_row[2] else 0,
                        "coordinates": {
                            "lat": float(field_row[3]) if field_row[3] else None,
                            "lon": float(field_row[4]) if field_row[4] else None
                        },
                        "created": str(field_row[5]) if field_row[5] else "No date",
                        "block_id": field_row[6],
                        "land_use": field_row[7]
                    }
                    
                    # Step 3: Get crops for this field
                    crops_query = """
                    SELECT crop_name, variety, planting_date, status
                    FROM field_crops 
                    WHERE field_id = %s
                    ORDER BY planting_date DESC
                    """
                    
                    crops_result = db_manager.execute_query(crops_query, (field_row[0],))
                    
                    field_crops = []
                    if crops_result and 'rows' in crops_result:
                        for crop_row in crops_result['rows']:
                            field_crops.append({
                                "crop_name": crop_row[0] or 'Unknown crop',
                                "variety": crop_row[1] or 'No variety',
                                "planting_date": str(crop_row[2]) if crop_row[2] else "No date",
                                "status": crop_row[3] or 'No status'
                            })
                    
                    field_info["crops"] = field_crops
                    farmer_fields.append(field_info)
                    all_fields.append(field_info)
            
            farmer_info["fields"] = farmer_fields
            farmer_info["field_count"] = len(farmer_fields)
            farmers_found.append(farmer_info)
        
        # Assessment
        total_fields = len(all_fields)
        total_area = sum(f['area_ha'] for f in all_fields)
        
        if total_fields > 0:
            assessment = "SUCCESS - Edi Kante found WITH fields"
            recommendation = "FAVA is working correctly. If fields not showing in dashboard, check frontend display code."
        else:
            assessment = "PARTIAL - Edi Kante found but NO fields"
            recommendation = "FAVA registers farmers but fails to save field data. Check field entry process."
        
        return {
            "timestamp": datetime.now().isoformat(),
            "edi_kante_found": True,
            "farmers_found": len(farmers_found),
            "total_fields": total_fields,
            "total_area_ha": round(total_area, 2),
            "assessment": assessment,
            "recommendation": recommendation,
            "farmers": farmers_found,
            "summary": {
                "farmer_registration": "✅ Working" if len(farmers_found) > 0 else "❌ Failed",
                "field_entry": "✅ Working" if total_fields > 0 else "❌ Failed",
                "crop_data": "✅ Present" if any(len(f.get('crops', [])) > 0 for f in all_fields) else "❌ Missing"
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking Edi Kante: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "assessment": "ERROR - Database query failed",
            "recommendation": "Check database connectivity and query syntax"
        }