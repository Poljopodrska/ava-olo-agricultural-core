#!/usr/bin/env python3
"""
Weather API routes for AVA OLO Farmer Portal
Provides weather endpoints for the dashboard
TEMPORARY: All endpoints return mock data until service import issue is resolved
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from datetime import datetime, timedelta
from modules.auth.routes import get_current_farmer

router = APIRouter(prefix="/api/weather", tags=["weather"])

def _get_mock_weather_data():
    """Get mock weather data for testing"""
    return {
        'location': 'Ljubljana, Slovenia',
        'temperature': '18°C',
        'feels_like': '17°C',
        'humidity': '72%',
        'description': 'Partly Cloudy',
        'icon': '⛅',
        'wind_speed': '8 km/h',
        'pressure': '1015 hPa',
        'visibility': '10 km',
        'timestamp': datetime.now().strftime('%H:%M'),
        'raw_temp': 18.0,
        'raw_humidity': 72,
        'weather_code': '02d'
    }

def _get_mock_forecast_data(days: int = 5):
    """Get mock forecast data"""
    forecasts = []
    base_date = datetime.now()
    
    for i in range(min(days, 5)):
        date = base_date + timedelta(days=i)
        temp_base = 16 + (i * 2)
        
        forecasts.append({
            'date': date.strftime('%Y-%m-%d'),
            'day_name': date.strftime('%A'),
            'temp_min': f"{temp_base - 3}°C",
            'temp_max': f"{temp_base + 5}°C",
            'description': ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Sunny'][i % 5],
            'icon': ['☀️', '⛅', '☁️', '🌧️', '☀️'][i % 5],
            'humidity': f"{65 + i * 5}%",
            'wind_speed': f"{8 + i * 2} km/h",
            'wind_direction': ['N', 'NE', 'E', 'SE', 'S'][i % 5],
            'precipitation': '0 mm' if i != 3 else '2.5 mm'
        })
    
    return {
        'location': 'Ljubljana, Slovenia',
        'forecasts': forecasts
    }

@router.get("/current")
async def get_current_weather(lat: Optional[float] = None, lon: Optional[float] = None):
    """Get current weather conditions"""
    return {
        "status": "success",
        "data": _get_mock_weather_data()
    }

@router.get("/forecast")
async def get_weather_forecast(lat: Optional[float] = None, lon: Optional[float] = None, days: int = 5):
    """Get weather forecast"""
    if days < 1 or days > 7:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 7")
    
    return {
        "status": "success",
        "data": _get_mock_forecast_data(days)
    }

@router.get("/alerts")
async def get_weather_alerts(lat: Optional[float] = None, lon: Optional[float] = None):
    """Get agricultural weather alerts"""
    return {
        "status": "success",
        "data": {
            "alerts": [
                {
                    "type": "temperature",
                    "severity": "low",
                    "title": "🌡️ Optimal Temperature",
                    "message": "Current temperature is ideal for most crops",
                    "action": "Continue normal operations"
                }
            ],
            "count": 1
        }
    }

@router.get("/locations/bulgaria")
async def get_bulgaria_weather():
    """Get weather specifically for Bulgarian mango farming regions"""
    # Mock data for Bulgarian regions
    locations = [
        {"name": "Sofia", "lat": 42.7339, "lon": 23.3258},
        {"name": "Plovdiv", "lat": 42.1354, "lon": 24.7453},
        {"name": "Burgas", "lat": 42.5048, "lon": 27.4626},
        {"name": "Varna", "lat": 43.2141, "lon": 27.9147}
    ]
    
    results = []
    for i, location in enumerate(locations):
        weather_data = _get_mock_weather_data()
        weather_data["region"] = location["name"]
        weather_data["temperature"] = f"{20 + i}°C"  # Vary temperatures slightly
        results.append(weather_data)
    
    return {
        "status": "success",
        "data": {
            "regions": results,
            "count": len(results)
        }
    }

@router.get("/current-farmer")
async def get_current_farmer_weather(request: Request):
    """Get current weather for logged-in farmer's location"""
    # Get farmer info from session/cookies
    farmer = await get_current_farmer(request)
    if not farmer:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Return mock weather data
    weather_data = _get_mock_weather_data()
    weather_data['farmer_location'] = "Slovenia"
    weather_data['coordinates'] = {
        'lat': 46.0569,
        'lon': 14.5058
    }
    
    return {
        "status": "success",
        "data": weather_data
    }

@router.get("/forecast-farmer")
async def get_farmer_weather_forecast(request: Request, days: int = 5):
    """Get weather forecast for logged-in farmer's location"""
    # Get farmer info
    farmer = await get_current_farmer(request)
    if not farmer:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get mock forecast
    forecast_data = _get_mock_forecast_data(days)
    forecast_data['farmer_location'] = "Slovenia"
    
    return {
        "status": "success",
        "data": forecast_data
    }

@router.get("/hourly-farmer")
async def get_farmer_hourly_forecast(request: Request):
    """Get hourly forecast for logged-in farmer's location"""
    # Get farmer info
    farmer = await get_current_farmer(request)
    if not farmer:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Mock hourly data
    hourly_data = []
    current_hour = datetime.now().hour
    
    for i in range(8):  # 8 3-hour intervals = 24 hours
        hour = (current_hour + i * 3) % 24
        temp = 20 + (5 * (1 if hour < 12 else -1))  # Temperature curve
        
        hourly_data.append({
            'time': f"{hour:02d}:00",
            'hour': hour,
            'temp': temp + i,
            'icon': '☀️' if 6 <= hour <= 18 else '🌙',
            'description': 'Clear' if i % 3 == 0 else 'Partly Cloudy',
            'wind': {
                'speed': 10 + i * 2,
                'direction': ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][i % 8]
            },
            'precipitation': 0 if i < 5 else 2.5,
            'humidity': 60 + i * 2
        })
    
    return {
        "status": "success",
        "data": {
            "hourly": hourly_data,
            "location": "Slovenia"
        }
    }

@router.get("/health")
async def weather_service_health():
    """Check weather service health"""
    return {
        "status": "degraded",
        "service": "weather",
        "api_key_configured": True,
        "message": "Using mock data temporarily"
    }