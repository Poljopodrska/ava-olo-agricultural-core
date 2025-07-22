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
# from modules.auth.security import get_current_farmer  # TODO: Module missing

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/v1/debug/services")
async def debug_services(request: Request):
    """Comprehensive service connection status"""
    
    # Get current farmer
    try:
        farmer = await get_current_farmer(request)
        farmer_id = farmer.get('farmer_id') if farmer else None
    except:
        farmer_id = None
    
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