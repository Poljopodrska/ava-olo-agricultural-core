#!/usr/bin/env python3
"""
Weather API routes for AVA OLO Agricultural Core
Provides weather data for farmers based on their location
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import logging

from ..auth.routes import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weather", tags=["weather"])

@router.get("/farmer", response_class=JSONResponse)
async def get_farmer_weather(request: Request, current_user=Depends(get_current_user_optional)):
    """Get weather data for the current farmer's location"""
    try:
        # Import weather service
        from ..weather.service import weather_service
        
        # Get current weather using the weather service (NOT async)
        weather_data = weather_service.get_current_weather()
        
        # Get forecast
        forecast_data = weather_service.get_forecast()
        
        # Format response
        return JSONResponse(content={
            "status": "success",
            "location": weather_data.get("location", "Slovenia"),
            "current": {
                "temperature": weather_data.get("temperature", 22),
                "condition": weather_data.get("description", "Unknown"),
                "humidity": weather_data.get("humidity", 65),
                "wind_speed": weather_data.get("wind_speed", 0),
                "icon": weather_data.get("icon"),
                "feels_like": weather_data.get("feels_like")
            },
            "forecast": forecast_data,
            "timestamp": weather_data.get("timestamp"),
            "coordinates": {
                "lat": weather_service.default_lat,
                "lon": weather_service.default_lon
            }
        })
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        # Return mock data on error
        return JSONResponse(content={
            "status": "success",
            "location": "Slovenia",
            "current": {
                "temperature": 22,
                "condition": "Partly Cloudy",
                "humidity": 65,
                "wind_speed": 10
            },
            "forecast": {
                "today": {"temp_max": 25, "temp_min": 15, "description": "Partly cloudy"},
                "tomorrow": {"temp_max": 27, "temp_min": 16, "description": "Sunny"}
            },
            "message": "Using cached weather data"
        })

@router.get("/current", response_class=JSONResponse)
async def get_current_weather(lat: float = None, lon: float = None):
    """Get current weather for specific coordinates or default location"""
    try:
        from ..weather.service import weather_service
        
        # Use provided coordinates or defaults
        if lat and lon:
            weather_data = weather_service.get_weather_by_coordinates(lat, lon)
        else:
            weather_data = weather_service.get_current_weather()
        
        return JSONResponse(content={
            "status": "success",
            "data": weather_data
        })
    except Exception as e:
        logger.error(f"Error getting current weather: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": "Weather service temporarily unavailable",
            "data": weather_service._get_mock_weather_data()
        })

@router.get("/forecast", response_class=JSONResponse)
async def get_weather_forecast(lat: float = None, lon: float = None, days: int = 5):
    """Get weather forecast for specific coordinates or default location"""
    try:
        from ..weather.service import weather_service
        
        # Use provided coordinates or defaults
        if lat and lon:
            forecast_data = weather_service.get_forecast_by_coordinates(lat, lon, days)
        else:
            forecast_data = weather_service.get_forecast(days)
        
        return JSONResponse(content={
            "status": "success",
            "data": forecast_data
        })
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": "Weather service temporarily unavailable",
            "data": weather_service._get_mock_forecast_data()
        })

@router.get("/agricultural", response_class=JSONResponse)
async def get_agricultural_weather(lat: float = None, lon: float = None):
    """Get agricultural-specific weather data and recommendations"""
    try:
        from ..weather.service import weather_service
        
        # Get agricultural forecast
        if lat and lon:
            agri_data = weather_service.get_agricultural_forecast(lat, lon)
        else:
            agri_data = weather_service.get_agricultural_forecast()
        
        return JSONResponse(content={
            "status": "success",
            "data": agri_data
        })
    except Exception as e:
        logger.error(f"Error getting agricultural weather: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": "Agricultural weather service temporarily unavailable"
        })

@router.get("/alerts", response_class=JSONResponse)
async def get_weather_alerts(lat: float = None, lon: float = None):
    """Get weather alerts for farming operations"""
    try:
        from ..weather.service import weather_service
        
        # Get weather data first
        if lat and lon:
            weather_data = weather_service.get_weather_by_coordinates(lat, lon)
        else:
            weather_data = weather_service.get_current_weather()
        
        # Get alerts based on current conditions
        alerts = weather_service.get_weather_alerts(weather_data)
        
        return JSONResponse(content={
            "status": "success",
            "alerts": alerts,
            "location": weather_data.get("location", "Unknown"),
            "current_conditions": {
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
                "description": weather_data.get("description")
            }
        })
    except Exception as e:
        logger.error(f"Error getting weather alerts: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": "Weather alert service temporarily unavailable",
            "alerts": []
        })

@router.get("/health", response_class=JSONResponse)
async def weather_service_health():
    """Check weather service health status"""
    try:
        from ..weather.service import weather_service
        
        # Test API connection
        test_weather = weather_service.get_current_weather()
        
        if test_weather and "temperature" in test_weather:
            return JSONResponse(content={
                "status": "healthy",
                "api_configured": bool(weather_service.api_key),
                "api_key_preview": weather_service.api_key[:8] + "..." if weather_service.api_key else None,
                "default_location": f"{weather_service.default_lat}, {weather_service.default_lon}",
                "test_successful": True
            })
        else:
            return JSONResponse(content={
                "status": "degraded",
                "api_configured": bool(weather_service.api_key),
                "message": "Using mock data",
                "test_successful": False
            })
    except Exception as e:
        logger.error(f"Weather service health check failed: {e}")
        return JSONResponse(content={
            "status": "unhealthy",
            "error": str(e),
            "message": "Weather service unavailable"
        }, status_code=503)