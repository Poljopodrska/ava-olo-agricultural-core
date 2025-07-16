#!/usr/bin/env python3
"""
Constitutional Weather API Endpoints
FastAPI endpoints for weather services with constitutional compliance
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging
import asyncio

# Import constitutional weather system
from .constitutional_weather_service import ConstitutionalWeatherService, WeatherInsightType
from .smart_weather_locator import SmartWeatherLocator
from .weather_providers.provider_factory import WeatherProviderFactory

logger = logging.getLogger(__name__)

# Pydantic models for API
class WeatherLocationRequest(BaseModel):
    """Weather location request model"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")

class WeatherFarmerRequest(BaseModel):
    """Weather farmer request model"""
    farmer_id: int = Field(..., gt=0, description="Farmer ID")
    crop_type: Optional[str] = Field(None, description="Crop type for agricultural insights")
    days: Optional[int] = Field(7, ge=1, le=14, description="Number of forecast days")

class WeatherInsightRequest(BaseModel):
    """Weather insight request model"""
    farmer_id: int = Field(..., gt=0, description="Farmer ID")
    crop_type: str = Field(..., description="Crop type")
    growth_stage: Optional[str] = Field(None, description="Crop growth stage")
    insight_type: str = Field("forecast", description="Type of insight (forecast, alert, recommendation)")

class BulkWeatherRequest(BaseModel):
    """Bulk weather request model"""
    farmer_ids: List[int] = Field(..., description="List of farmer IDs")
    crop_type: Optional[str] = Field(None, description="Crop type for insights")
    include_insights: bool = Field(True, description="Include LLM insights")

class WeatherResponse(BaseModel):
    """Weather response model"""
    success: bool = Field(..., description="Request success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Weather data")
    error: Optional[str] = Field(None, description="Error message if any")
    constitutional_compliance: bool = Field(True, description="Constitutional compliance status")
    mango_rule_verified: bool = Field(False, description="MANGO RULE compliance")
    generated_at: str = Field(..., description="Response generation timestamp")

class WeatherAPIEndpoints:
    """
    Constitutional Weather API Endpoints
    
    Provides RESTful weather endpoints with constitutional compliance
    """
    
    def __init__(self, app: FastAPI):
        """Initialize weather API endpoints"""
        self.app = app
        self.weather_service = ConstitutionalWeatherService()
        self.location_service = SmartWeatherLocator()
        self.provider_factory = WeatherProviderFactory()
        
        # Initialize providers
        self._initialize_providers()
        
        # Register endpoints
        self._register_endpoints()
        
        logger.info("🏛️ Constitutional Weather API Endpoints initialized")
    
    def _initialize_providers(self):
        """Initialize weather providers"""
        try:
            # This would normally load from database
            # For now, create a basic OpenWeatherMap provider
            import os
            
            openweathermap_config = {
                'name': 'openweathermap',
                'api_base_url': 'https://api.openweathermap.org/data/2.5',
                'api_version': '2.5',
                'api_key_env_var': 'OPENWEATHERMAP_API_KEY',
                'compliance_score': 95,
                'mango_rule_verified': True,
                'is_active': True,
                'is_primary': True
            }
            
            from .weather_providers.provider_factory import WeatherProviderType
            self.provider_factory.create_provider(
                WeatherProviderType.OPENWEATHERMAP, 
                openweathermap_config
            )
            
        except Exception as e:
            logger.error(f"❌ Error initializing weather providers: {e}")
    
    def _register_endpoints(self):
        """Register all weather endpoints"""
        
        @self.app.get("/api/weather/farmer/{farmer_id}", response_model=WeatherResponse)
        async def get_farmer_weather(
            farmer_id: int = Path(..., gt=0, description="Farmer ID"),
            crop_type: Optional[str] = Query(None, description="Crop type for insights"),
            days: int = Query(7, ge=1, le=14, description="Number of forecast days")
        ):
            """
            Get weather data for a specific farmer
            
            Returns weather data and optional LLM insights for the farmer's location
            """
            try:
                # Get farmer weather data
                weather_data = await self.weather_service.get_farmer_weather(farmer_id, crop_type)
                
                if weather_data.get('error'):
                    return WeatherResponse(
                        success=False,
                        error=weather_data['error'],
                        constitutional_compliance=True,
                        mango_rule_verified=False,
                        generated_at=datetime.now().isoformat()
                    )
                
                return WeatherResponse(
                    success=True,
                    data=weather_data,
                    constitutional_compliance=weather_data.get('constitutional_compliance', True),
                    mango_rule_verified=weather_data.get('mango_rule_verified', False),
                    generated_at=datetime.now().isoformat()
                )
                
            except Exception as e:
                logger.error(f"❌ Error getting farmer weather: {e}")
                return WeatherResponse(
                    success=False,
                    error=str(e),
                    constitutional_compliance=True,
                    mango_rule_verified=False,
                    generated_at=datetime.now().isoformat()
                )
        
        @self.app.get("/api/weather/location", response_model=WeatherResponse)
        async def get_weather_by_location(
            lat: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
            lon: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
            days: int = Query(7, ge=1, le=14, description="Number of forecast days")
        ):
            """
            Get weather data by coordinates
            
            Returns weather data for specific latitude/longitude coordinates
            """
            try:
                # Get weather by coordinates
                weather_data = await self.weather_service.get_weather_by_coordinates(lat, lon)
                
                if weather_data.get('error'):
                    return WeatherResponse(
                        success=False,
                        error=weather_data['error'],
                        constitutional_compliance=True,
                        mango_rule_verified=False,
                        generated_at=datetime.now().isoformat()
                    )
                
                return WeatherResponse(
                    success=True,
                    data=weather_data,
                    constitutional_compliance=weather_data.get('constitutional_compliance', True),
                    mango_rule_verified=weather_data.get('mango_rule_verified', False),
                    generated_at=datetime.now().isoformat()
                )
                
            except Exception as e:
                logger.error(f"❌ Error getting weather by location: {e}")
                return WeatherResponse(
                    success=False,
                    error=str(e),
                    constitutional_compliance=True,
                    mango_rule_verified=False,
                    generated_at=datetime.now().isoformat()
                )
        
        @self.app.get("/api/weather/forecast/farmer/{farmer_id}", response_model=WeatherResponse)
        async def get_farmer_forecast(
            farmer_id: int = Path(..., gt=0, description="Farmer ID"),
            days: int = Query(7, ge=1, le=14, description="Number of forecast days")
        ):
            """
            Get detailed weather forecast for a farmer
            
            Returns extended weather forecast for the farmer's location
            """
            try:
                # Get farmer's location
                location = await self.location_service.get_farmer_weather_location(farmer_id)
                
                if not location:
                    return WeatherResponse(
                        success=False,
                        error="Farmer location not found",
                        constitutional_compliance=True,
                        mango_rule_verified=False,
                        generated_at=datetime.now().isoformat()
                    )
                
                # Get weather forecast
                weather_data = await self.weather_service.get_weather_by_coordinates(
                    location['latitude'], location['longitude']
                )
                
                if weather_data.get('error'):
                    return WeatherResponse(
                        success=False,
                        error=weather_data['error'],
                        constitutional_compliance=True,
                        mango_rule_verified=False,
                        generated_at=datetime.now().isoformat()
                    )
                
                # Enhanced response with forecast details
                forecast_data = {\n                    'farmer_id': farmer_id,\n                    'location': location,\n                    'forecast_days': days,\n                    'weather_data': weather_data.get('weather_data', []),\n                    'forecast_generated_at': datetime.now().isoformat()\n                }\n                \n                return WeatherResponse(\n                    success=True,\n                    data=forecast_data,\n                    constitutional_compliance=True,\n                    mango_rule_verified=location.get('mango_growing_suitable', False),\n                    generated_at=datetime.now().isoformat()\n                )\n                \n            except Exception as e:\n                logger.error(f\"❌ Error getting farmer forecast: {e}\")\n                return WeatherResponse(\n                    success=False,\n                    error=str(e),\n                    constitutional_compliance=True,\n                    mango_rule_verified=False,\n                    generated_at=datetime.now().isoformat()\n                )\n        \n        @self.app.get(\"/api/weather/insights/farmer/{farmer_id}/crop/{crop_type}\", response_model=WeatherResponse)\n        async def get_weather_insights(\n            farmer_id: int = Path(..., gt=0, description=\"Farmer ID\"),\n            crop_type: str = Path(..., description=\"Crop type\"),\n            growth_stage: Optional[str] = Query(None, description=\"Crop growth stage\"),\n            insight_type: str = Query(\"forecast\", description=\"Type of insight\")\n        ):\n            \"\"\"\n            Get LLM-generated weather insights for crop management\n            \n            Returns agricultural weather insights and recommendations\n            \"\"\"\n            try:\n                # Get farmer's location\n                location = await self.location_service.get_farmer_weather_location(farmer_id)\n                \n                if not location:\n                    return WeatherResponse(\n                        success=False,\n                        error=\"Farmer location not found\",\n                        constitutional_compliance=True,\n                        mango_rule_verified=False,\n                        generated_at=datetime.now().isoformat()\n                    )\n                \n                # Get weather data\n                weather_data = await self.weather_service.get_weather_by_location(location['id'])\n                \n                # Generate insights\n                insights = await self.weather_service.generate_weather_insights(\n                    farmer_id, location['id'], crop_type, weather_data\n                )\n                \n                if insights.get('error'):\n                    return WeatherResponse(\n                        success=False,\n                        error=insights['error'],\n                        constitutional_compliance=True,\n                        mango_rule_verified=False,\n                        generated_at=datetime.now().isoformat()\n                    )\n                \n                # Enhanced insights response\n                insights_data = {\n                    'farmer_id': farmer_id,\n                    'crop_type': crop_type,\n                    'growth_stage': growth_stage,\n                    'insight_type': insight_type,\n                    'location': location,\n                    'insights': insights,\n                    'weather_summary': self._summarize_weather_data(weather_data),\n                    'generated_at': datetime.now().isoformat()\n                }\n                \n                return WeatherResponse(\n                    success=True,\n                    data=insights_data,\n                    constitutional_compliance=True,\n                    mango_rule_verified=insights.get('mango_rule_applicable', False),\n                    generated_at=datetime.now().isoformat()\n                )\n                \n            except Exception as e:\n                logger.error(f\"❌ Error getting weather insights: {e}\")\n                return WeatherResponse(\n                    success=False,\n                    error=str(e),\n                    constitutional_compliance=True,\n                    mango_rule_verified=False,\n                    generated_at=datetime.now().isoformat()\n                )\n        \n        @self.app.post(\"/api/weather/bulk\", response_model=WeatherResponse)\n        async def get_bulk_weather(\n            request: BulkWeatherRequest\n        ):\n            \"\"\"\n            Get weather data for multiple farmers\n            \n            Returns weather data for multiple farmers in batch\n            \"\"\"\n            try:\n                if len(request.farmer_ids) > 100:\n                    return WeatherResponse(\n                        success=False,\n                        error=\"Maximum 100 farmers allowed per request\",\n                        constitutional_compliance=True,\n                        mango_rule_verified=False,\n                        generated_at=datetime.now().isoformat()\n                    )\n                \n                # Process farmers in parallel\n                tasks = []\n                for farmer_id in request.farmer_ids:\n                    task = self.weather_service.get_farmer_weather(\n                        farmer_id, \n                        request.crop_type if request.include_insights else None\n                    )\n                    tasks.append(task)\n                \n                # Wait for all tasks to complete\n                results = await asyncio.gather(*tasks, return_exceptions=True)\n                \n                # Process results\n                bulk_data = {\n                    'total_farmers': len(request.farmer_ids),\n                    'successful_requests': 0,\n                    'failed_requests': 0,\n                    'weather_data': [],\n                    'errors': []\n                }\n                \n                for i, result in enumerate(results):\n                    farmer_id = request.farmer_ids[i]\n                    \n                    if isinstance(result, Exception):\n                        bulk_data['failed_requests'] += 1\n                        bulk_data['errors'].append({\n                            'farmer_id': farmer_id,\n                            'error': str(result)\n                        })\n                    elif result.get('error'):\n                        bulk_data['failed_requests'] += 1\n                        bulk_data['errors'].append({\n                            'farmer_id': farmer_id,\n                            'error': result['error']\n                        })\n                    else:\n                        bulk_data['successful_requests'] += 1\n                        bulk_data['weather_data'].append(result)\n                \n                return WeatherResponse(\n                    success=True,\n                    data=bulk_data,\n                    constitutional_compliance=True,\n                    mango_rule_verified=any(\n                        data.get('mango_rule_verified', False) \n                        for data in bulk_data['weather_data']\n                    ),\n                    generated_at=datetime.now().isoformat()\n                )\n                \n            except Exception as e:\n                logger.error(f\"❌ Error getting bulk weather: {e}\")\n                return WeatherResponse(\n                    success=False,\n                    error=str(e),\n                    constitutional_compliance=True,\n                    mango_rule_verified=False,\n                    generated_at=datetime.now().isoformat()\n                )\n        \n        @self.app.get(\"/api/weather/status\", response_model=WeatherResponse)\n        async def get_weather_system_status():\n            \"\"\"\n            Get weather system status and compliance information\n            \n            Returns system status, provider information, and compliance scores\n            \"\"\"\n            try:\n                # Get system status\n                compliance_score = await self.weather_service.get_constitutional_compliance_score()\n                mango_compliance = await self.weather_service.verify_mango_rule_compliance()\n                \n                status_data = {\n                    'system_status': 'operational',\n                    'constitutional_compliance_score': compliance_score,\n                    'mango_rule_compliance': mango_compliance,\n                    'active_providers': len(self.provider_factory.get_active_providers()),\n                    'primary_provider': self.provider_factory.get_primary_provider().provider_name if self.provider_factory.get_primary_provider() else None,\n                    'factory_status': self.provider_factory.get_factory_status(),\n                    'locator_status': self.location_service.get_locator_status(),\n                    'last_updated': datetime.now().isoformat()\n                }\n                \n                return WeatherResponse(\n                    success=True,\n                    data=status_data,\n                    constitutional_compliance=compliance_score >= 80,\n                    mango_rule_verified=mango_compliance,\n                    generated_at=datetime.now().isoformat()\n                )\n                \n            except Exception as e:\n                logger.error(f\"❌ Error getting weather system status: {e}\")\n                return WeatherResponse(\n                    success=False,\n                    error=str(e),\n                    constitutional_compliance=True,\n                    mango_rule_verified=False,\n                    generated_at=datetime.now().isoformat()\n                )\n    \n    def _summarize_weather_data(self, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:\n        \"\"\"Summarize weather data for API response\"\"\"\n        if not weather_data:\n            return {}\n        \n        try:\n            # Calculate summary statistics\n            temperatures = [d.get('temperature', 0) for d in weather_data if d.get('temperature')]\n            rainfalls = [d.get('rainfall', 0) for d in weather_data if d.get('rainfall')]\n            \n            return {\n                'total_days': len(weather_data),\n                'temperature_range': {\n                    'min': min(temperatures) if temperatures else 0,\n                    'max': max(temperatures) if temperatures else 0,\n                    'avg': sum(temperatures) / len(temperatures) if temperatures else 0\n                },\n                'total_rainfall': sum(rainfalls) if rainfalls else 0,\n                'rainy_days': len([r for r in rainfalls if r > 0]),\n                'conditions': list(set([d.get('condition', 'unknown') for d in weather_data]))\n            }\n            \n        except Exception as e:\n            logger.error(f\"❌ Error summarizing weather data: {e}\")\n            return {}\n\n# Function to add weather endpoints to existing FastAPI app\ndef add_weather_endpoints(app: FastAPI) -> WeatherAPIEndpoints:\n    \"\"\"\n    Add constitutional weather endpoints to existing FastAPI application\n    \n    Args:\n        app: FastAPI application instance\n        \n    Returns:\n        WeatherAPIEndpoints instance\n    \"\"\"\n    weather_endpoints = WeatherAPIEndpoints(app)\n    logger.info(\"✅ Constitutional weather endpoints added to FastAPI app\")\n    return weather_endpoints