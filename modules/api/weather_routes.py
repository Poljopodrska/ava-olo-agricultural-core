#!/usr/bin/env python3
"""
Weather API routes for AVA OLO Agricultural Core
DEPRECATED: Use modules/weather/routes.py instead
This file is kept for backward compatibility but redirects to the main weather routes
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import logging

from ..auth.routes import get_current_user_optional

logger = logging.getLogger(__name__)

# Note: This router is intentionally empty to avoid conflicts
# All weather routes are handled by modules/weather/routes.py
router = APIRouter(prefix="/api/weather-legacy", tags=["weather-legacy"])

@router.get("/info")
async def weather_info():
    """Information about weather API"""
    return JSONResponse(content={
        "status": "info",
        "message": "Weather API has been moved to /api/weather",
        "endpoints": [
            "/api/weather/current",
            "/api/weather/forecast", 
            "/api/weather/alerts",
            "/api/weather/current-farmer",
            "/api/weather/health"
        ]
    })