#!/usr/bin/env python3
"""
Weather location API routes
Allows fetching weather for any coordinates
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ..auth.routes import require_auth
from ..weather.service import weather_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/weather", tags=["weather-location"])

@router.get("/location")
async def get_weather_for_location(
    lat: float,
    lon: float,
    farmer: dict = Depends(require_auth)
):
    """Get weather for specific coordinates"""
    try:
        logger.info(f"Fetching weather for coordinates: {lat}, {lon}")
        
        # Get current weather
        current_weather = await weather_service.get_current_weather(lat, lon)
        
        if not current_weather:
            logger.warning(f"No weather data returned for {lat}, {lon}")
            return JSONResponse({
                "success": False,
                "error": "No weather data available for this location"
            })
        
        # Get hourly forecast for next 24 hours
        hourly_data = await weather_service.get_hourly_forecast(lat, lon)
        
        # Get 5-day forecast
        forecast_data = await weather_service.get_weather_forecast(lat, lon, days=5)
        
        # Format the response
        weather_response = {
            "temperature": current_weather.get('temperature', '20'),
            "conditions": current_weather.get('description', 'Clear'),
            "humidity": current_weather.get('humidity', '60%'),
            "wind_speed": current_weather.get('wind_speed', '10 km/h'),
            "icon": current_weather.get('icon', '🌤️'),
            "rainfall_24h": current_weather.get('rainfall_24h', 0),  # mm in last 24h
            "hourly": [],
            "forecast": []
        }
        
        # Add hourly forecast
        if hourly_data:
            for hour in hourly_data:
                weather_response['hourly'].append({
                    'time': hour['time'],
                    'temp': hour['temp'],
                    'icon': hour['icon'],
                    'rainfall': hour.get('rainfall_mm', 0),  # mm expected
                    'wind': hour['wind']['speed']
                })
        
        # Add 5-day forecast
        if forecast_data and 'forecasts' in forecast_data:
            for day_forecast in forecast_data['forecasts'][:5]:
                # Extract temperature values
                temp_max = day_forecast.get('temp_max', '25°C')
                temp_min = day_forecast.get('temp_min', '18°C')
                
                # Remove °C if present for consistency
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
        
        # Add proof of real API call
        if 'proof' in current_weather:
            weather_response['api_proof'] = current_weather['proof']
        
        return JSONResponse({
            "success": True,
            "weather": weather_response,
            "coordinates": {
                "lat": lat,
                "lon": lon
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching weather for location: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)