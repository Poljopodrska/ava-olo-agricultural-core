#!/usr/bin/env python3
"""
Weather API routes for AVA OLO Farmer Portal
Provides weather endpoints for the dashboard
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from modules.weather.service import weather_service
from modules.location.location_service import get_location_service
from modules.auth.routes import get_current_farmer

router = APIRouter(prefix="/api/weather", tags=["weather"])

@router.get("/current")
async def get_current_weather(lat: Optional[float] = None, lon: Optional[float] = None):
    """Get current weather conditions"""
    try:
        weather_data = await weather_service.get_current_weather(lat, lon)
        
        if not weather_data:
            raise HTTPException(status_code=503, detail="Weather service unavailable")
        
        return {
            "status": "success",
            "data": weather_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather service error: {str(e)}")

@router.get("/forecast")
async def get_weather_forecast(lat: Optional[float] = None, lon: Optional[float] = None, days: int = 5):
    """Get weather forecast"""
    try:
        if days < 1 or days > 7:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 7")
        
        forecast_data = await weather_service.get_weather_forecast(lat, lon, days)
        
        if not forecast_data:
            raise HTTPException(status_code=503, detail="Weather forecast service unavailable")
        
        return {
            "status": "success",
            "data": forecast_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather forecast error: {str(e)}")

@router.get("/alerts")
async def get_weather_alerts(lat: Optional[float] = None, lon: Optional[float] = None):
    """Get agricultural weather alerts"""
    try:
        alerts = await weather_service.get_weather_alerts(lat, lon)
        
        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "count": len(alerts)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather alerts error: {str(e)}")

@router.get("/locations/bulgaria")
async def get_bulgaria_weather():
    """Get weather specifically for Bulgarian mango farming regions"""
    try:
        # Major Bulgarian agricultural regions
        locations = [
            {"name": "Sofia", "lat": 42.7339, "lon": 23.3258},
            {"name": "Plovdiv", "lat": 42.1354, "lon": 24.7453},
            {"name": "Burgas", "lat": 42.5048, "lon": 27.4626},
            {"name": "Varna", "lat": 43.2141, "lon": 27.9147}
        ]
        
        results = []
        
        for location in locations:
            weather_data = await weather_service.get_current_weather(location["lat"], location["lon"])
            if weather_data:
                weather_data["region"] = location["name"]
                results.append(weather_data)
        
        return {
            "status": "success",
            "data": {
                "regions": results,
                "count": len(results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulgaria weather error: {str(e)}")

@router.get("/current-farmer")
async def get_current_farmer_weather(request: Request):
    """Get current weather for logged-in farmer's location"""
    try:
        # Get farmer info from session/cookies
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get farmer's location
        location_service = get_location_service()
        location = await location_service.get_farmer_location(farmer['farmer_id'])
        
        # Get weather for farmer's location
        weather_data = await weather_service.get_current_weather(location['lat'], location['lon'])
        
        if not weather_data:
            raise HTTPException(status_code=503, detail="Weather service unavailable")
        
        # Add location info to response
        weather_data['farmer_location'] = location_service.get_location_display(location)
        weather_data['coordinates'] = {
            'lat': location['lat'],
            'lon': location['lon']
        }
        
        return {
            "status": "success",
            "data": weather_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather service error: {str(e)}")

@router.get("/forecast-farmer")
async def get_farmer_weather_forecast(request: Request, days: int = 5):
    """Get weather forecast for logged-in farmer's location"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get farmer's location
        location_service = get_location_service()
        location = await location_service.get_farmer_location(farmer['farmer_id'])
        
        # Get forecast for farmer's location
        forecast_data = await weather_service.get_weather_forecast(location['lat'], location['lon'], days)
        
        if not forecast_data:
            raise HTTPException(status_code=503, detail="Weather forecast service unavailable")
        
        # Add location info
        forecast_data['farmer_location'] = location_service.get_location_display(location)
        
        return {
            "status": "success",
            "data": forecast_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather forecast error: {str(e)}")

@router.get("/hourly-farmer")
async def get_farmer_hourly_forecast(request: Request):
    """Get hourly forecast for logged-in farmer's location"""
    try:
        # Get farmer info
        farmer = await get_current_farmer(request)
        if not farmer:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get farmer's location
        location_service = get_location_service()
        location = await location_service.get_farmer_location(farmer['farmer_id'])
        
        # Get hourly forecast
        hourly_data = await weather_service.get_hourly_forecast(location['lat'], location['lon'])
        
        if not hourly_data:
            raise HTTPException(status_code=503, detail="Hourly forecast service unavailable")
        
        return {
            "status": "success",
            "data": {
                "hourly": hourly_data,
                "location": location_service.get_location_display(location)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hourly forecast error: {str(e)}")

@router.get("/health")
async def weather_service_health():
    """Check weather service health"""
    try:
        # Try to get current weather as health check
        test_weather = await weather_service.get_current_weather()
        
        if test_weather:
            return {
                "status": "healthy",
                "service": "weather",
                "api_key_configured": bool(weather_service.api_key),
                "last_check": test_weather.get("timestamp", "unknown")
            }
        else:
            return {
                "status": "degraded",
                "service": "weather",
                "api_key_configured": bool(weather_service.api_key),
                "message": "Using mock data"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "weather",
            "error": str(e)
        }