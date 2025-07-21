#!/usr/bin/env python3
"""
Weather API routes for AVA OLO Farmer Portal
Provides weather endpoints for the dashboard
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.weather.service import weather_service

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