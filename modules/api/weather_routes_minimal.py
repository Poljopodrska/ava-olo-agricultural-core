from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import random

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])

@router.get("/current")
async def get_current_weather(location: str = "Sofia"):
    """Get current weather"""
    # Mock weather data
    weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain"]
    
    return JSONResponse(content={
        "location": location,
        "temperature": random.randint(15, 30),
        "condition": random.choice(weather_conditions),
        "humidity": random.randint(40, 80),
        "wind_speed": random.randint(5, 20),
        "timestamp": datetime.now().isoformat()
    })

@router.get("/forecast")
async def get_weather_forecast(location: str = "Sofia", days: int = 5):
    """Get weather forecast"""
    forecast = []
    for i in range(days):
        forecast.append({
            "day": i + 1,
            "temperature_high": random.randint(20, 30),
            "temperature_low": random.randint(10, 20),
            "condition": random.choice(["Sunny", "Partly Cloudy", "Cloudy", "Rain"])
        })
    
    return JSONResponse(content={
        "location": location,
        "forecast": forecast,
        "timestamp": datetime.now().isoformat()
    })