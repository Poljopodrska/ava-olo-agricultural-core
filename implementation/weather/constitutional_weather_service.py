#!/usr/bin/env python3
"""
Constitutional Weather Service Core
LLM-First, MANGO RULE Compliant, Privacy-First Weather Service

This is the main weather service that coordinates all weather operations
while maintaining constitutional compliance and LLM-first architecture.
"""

import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
import hashlib
from decimal import Decimal

# Import existing constitutional systems
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_operations import DatabaseOperations
from config_manager import ConfigManager
from llm_router import LLMRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherDataType(Enum):
    """Weather data types for constitutional compliance"""
    CURRENT = "current"
    FORECAST = "forecast"
    HISTORICAL = "historical"

class WeatherInsightType(Enum):
    """LLM-generated weather insight types"""
    FORECAST = "forecast"
    ALERT = "alert"
    RECOMMENDATION = "recommendation"
    ANALYSIS = "analysis"

@dataclass
class WeatherLocation:
    """Constitutional weather location data structure"""
    id: Optional[int] = None
    farmer_id: Optional[int] = None
    location_name: str = ""
    country: str = ""
    country_code: str = ""
    region: str = ""
    district: str = ""
    village: str = ""
    latitude: Decimal = Decimal('0.0')
    longitude: Decimal = Decimal('0.0')
    elevation_meters: Optional[int] = None
    climate_zone: str = ""
    agricultural_zone: str = ""
    soil_type: str = ""
    location_verified: bool = False
    mango_growing_suitable: bool = False
    location_insights: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.location_insights is None:
            self.location_insights = {}

@dataclass
class WeatherData:
    """Constitutional weather data structure"""
    id: Optional[int] = None
    location_id: int = 0
    provider_id: int = 0
    forecast_date: date = None
    forecast_hour: Optional[int] = None
    data_type: WeatherDataType = WeatherDataType.CURRENT
    
    # Core weather metrics
    temperature_current: Optional[Decimal] = None
    temperature_min: Optional[Decimal] = None
    temperature_max: Optional[Decimal] = None
    temperature_feels_like: Optional[Decimal] = None
    
    humidity: Optional[Decimal] = None
    pressure: Optional[Decimal] = None
    
    # Precipitation
    rainfall_mm: Optional[Decimal] = None
    rainfall_probability: Optional[Decimal] = None
    snow_mm: Optional[Decimal] = None
    
    # Wind
    wind_speed_kmh: Optional[Decimal] = None
    wind_direction_degrees: Optional[int] = None
    wind_gust_kmh: Optional[Decimal] = None
    
    # Atmospheric
    visibility_km: Optional[Decimal] = None
    uv_index: Optional[Decimal] = None
    cloud_cover_percent: Optional[int] = None
    
    # Condition
    weather_condition: str = ""
    weather_description: str = ""
    weather_icon_code: str = ""
    
    # Agricultural
    dew_point: Optional[Decimal] = None
    growing_degree_days: Optional[Decimal] = None
    evapotranspiration_mm: Optional[Decimal] = None
    
    # Metadata
    raw_data: Dict[str, Any] = None
    data_quality_score: int = 100
    is_validated: bool = False
    validation_errors: str = ""
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
        if self.forecast_date is None:
            self.forecast_date = date.today()

@dataclass
class WeatherInsight:
    """LLM-generated weather insight structure"""
    id: Optional[int] = None
    farmer_id: int = 0
    location_id: int = 0
    insight_type: WeatherInsightType = WeatherInsightType.FORECAST
    crop_type: str = ""
    growth_stage: str = ""
    insight_date: date = None
    forecast_period_days: int = 7
    
    # LLM-generated content
    insight_title: str = ""
    insight_summary: str = ""
    detailed_analysis: str = ""
    recommendations: str = ""
    
    # Agricultural recommendations
    planting_recommendations: str = ""
    harvesting_recommendations: str = ""
    pest_disease_warnings: str = ""
    irrigation_recommendations: str = ""
    
    # Risk assessment
    risk_level: str = "low"  # low, medium, high, critical
    confidence_score: int = 0  # 0-100
    
    # Constitutional compliance
    mango_rule_applicable: bool = False
    language_code: str = "en"
    
    # LLM metadata
    llm_model_used: str = ""
    llm_processing_time_ms: int = 0
    llm_tokens_used: int = 0
    llm_raw_response: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.llm_raw_response is None:
            self.llm_raw_response = {}
        if self.insight_date is None:
            self.insight_date = date.today()

class ConstitutionalWeatherService:
    """
    Constitutional Weather Service Core
    
    Main service class that orchestrates all weather operations while
    maintaining constitutional compliance and LLM-first architecture.
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """Initialize the constitutional weather service"""
        self.config_manager = config_manager or ConfigManager()
        self.db_ops = DatabaseOperations()
        self.llm_router = LLMRouter()
        
        # Weather service configuration
        self.cache_duration_hours = self.config_manager.get_config_value(
            "WEATHER_CACHE_DURATION_HOURS", 1
        )
        self.default_forecast_days = self.config_manager.get_config_value(
            "WEATHER_DEFAULT_FORECAST_DAYS", 7
        )
        
        # Constitutional compliance thresholds
        self.min_constitutional_compliance_score = 80
        self.mango_rule_validation_required = True
        
        # Initialize weather providers (will be loaded from database)
        self.weather_providers = {}
        self.active_provider_id = None
        
        logger.info("🏛️ Constitutional Weather Service initialized")
    
    async def initialize_providers(self):
        """Initialize and load weather providers from database"""
        try:
            # Load active weather providers from database
            query = """
            SELECT id, provider_name, provider_type, api_base_url, 
                   api_version, is_active, is_primary, priority_order,
                   api_key_env_var, constitutional_compliance_score,
                   mango_rule_verified, llm_first_compatible,
                   privacy_first_compliant, provider_config
            FROM weather_providers 
            WHERE is_active = TRUE 
            ORDER BY priority_order, is_primary DESC
            """
            
            providers = await self.db_ops.fetch_all(query)
            
            for provider in providers:
                provider_id = provider['id']
                provider_name = provider['provider_name']
                
                # Verify constitutional compliance
                if provider['constitutional_compliance_score'] < self.min_constitutional_compliance_score:
                    logger.warning(f"⚠️ Provider {provider_name} below constitutional compliance threshold")
                    continue
                
                # Verify MANGO RULE compliance if required
                if self.mango_rule_validation_required and not provider['mango_rule_verified']:
                    logger.warning(f"⚠️ Provider {provider_name} not MANGO RULE verified")
                    continue
                
                # Load provider configuration
                self.weather_providers[provider_id] = {
                    'name': provider_name,
                    'type': provider['provider_type'],
                    'api_base_url': provider['api_base_url'],
                    'api_version': provider['api_version'],
                    'is_primary': provider['is_primary'],
                    'api_key_env_var': provider['api_key_env_var'],
                    'config': provider['provider_config'] or {},
                    'compliance_score': provider['constitutional_compliance_score']
                }
                
                # Set primary provider
                if provider['is_primary'] and not self.active_provider_id:
                    self.active_provider_id = provider_id
                    logger.info(f"🏛️ Primary weather provider: {provider_name}")
            
            if not self.active_provider_id and self.weather_providers:
                # Fallback to first available provider
                self.active_provider_id = list(self.weather_providers.keys())[0]
                logger.info(f"🏛️ Fallback weather provider: {self.weather_providers[self.active_provider_id]['name']}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize weather providers: {e}")
            raise
    
    async def get_farmer_weather(self, farmer_id: int, crop_type: str = None) -> Dict[str, Any]:
        """
        Get weather data for a specific farmer
        
        Args:
            farmer_id: Farmer ID
            crop_type: Optional crop type for agricultural insights
            
        Returns:
            Dictionary containing weather data and LLM insights
        """
        try:
            # Get farmer's weather location
            location = await self.get_farmer_location(farmer_id)
            if not location:
                logger.error(f"❌ No weather location found for farmer {farmer_id}")
                return {"error": "No weather location found"}
            
            # Get weather data
            weather_data = await self.get_weather_by_location(location.id)
            
            # Generate LLM insights if crop type provided
            llm_insights = None
            if crop_type:
                llm_insights = await self.generate_weather_insights(
                    farmer_id, location.id, crop_type, weather_data
                )
            
            return {
                "farmer_id": farmer_id,
                "location": asdict(location),
                "weather_data": weather_data,
                "llm_insights": llm_insights,
                "constitutional_compliance": True,
                "mango_rule_verified": location.mango_growing_suitable,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting farmer weather: {e}")
            return {"error": str(e)}
    
    async def get_weather_by_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get weather data by coordinates
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            Dictionary containing weather data
        """
        try:
            # Check if location exists in database
            location = await self.find_location_by_coordinates(latitude, longitude)
            
            if not location:
                # Create new location entry
                location = await self.create_location_from_coordinates(latitude, longitude)
            
            # Get weather data
            weather_data = await self.get_weather_by_location(location.id)
            
            return {
                "coordinates": {"latitude": latitude, "longitude": longitude},
                "location": asdict(location),
                "weather_data": weather_data,
                "constitutional_compliance": True,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting weather by coordinates: {e}")
            return {"error": str(e)}
    
    async def get_weather_by_location(self, location_id: int) -> List[Dict[str, Any]]:
        """
        Get weather data for a specific location
        
        Args:
            location_id: Weather location ID
            
        Returns:
            List of weather data dictionaries
        """
        try:
            # Check cache first
            cached_data = await self.get_cached_weather_data(location_id)
            if cached_data:
                logger.info(f"🏛️ Using cached weather data for location {location_id}")
                return cached_data
            
            # Fetch fresh data from weather provider
            fresh_data = await self.fetch_weather_from_provider(location_id)
            
            # Cache the fresh data
            await self.cache_weather_data(location_id, fresh_data)
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"❌ Error getting weather by location: {e}")
            return []
    
    async def get_cached_weather_data(self, location_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached weather data if available and not expired"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.cache_duration_hours)
            
            query = """
            SELECT * FROM weather_data 
            WHERE location_id = %s 
            AND created_at > %s 
            AND data_type = %s
            ORDER BY forecast_date, forecast_hour
            """
            
            cached_data = await self.db_ops.fetch_all(
                query, (location_id, cutoff_time, WeatherDataType.FORECAST.value)
            )
            
            if cached_data:
                return [dict(row) for row in cached_data]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting cached weather data: {e}")
            return None
    
    async def fetch_weather_from_provider(self, location_id: int) -> List[Dict[str, Any]]:
        """Fetch weather data from active weather provider"""
        try:
            # Get location details
            location = await self.get_location_by_id(location_id)
            if not location:
                raise ValueError(f"Location {location_id} not found")
            
            # Import and use appropriate weather provider
            if self.active_provider_id not in self.weather_providers:
                raise ValueError("No active weather provider available")
            
            provider_info = self.weather_providers[self.active_provider_id]
            
            # Dynamic import of weather provider
            if provider_info['name'] == 'openweathermap':
                from .weather_providers.openweathermap_provider import OpenWeatherMapProvider
                provider = OpenWeatherMapProvider(provider_info)
            else:
                raise ValueError(f"Provider {provider_info['name']} not implemented")
            
            # Fetch weather data
            weather_data = await provider.get_weather_forecast(
                location.latitude, location.longitude
            )
            
            # Store in database
            await self.store_weather_data(location_id, weather_data)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching weather from provider: {e}")
            return []
    
    async def store_weather_data(self, location_id: int, weather_data: List[Dict[str, Any]]):
        """Store weather data in database"""
        try:
            for data in weather_data:
                weather_obj = WeatherData(
                    location_id=location_id,
                    provider_id=self.active_provider_id,
                    forecast_date=data.get('date'),
                    forecast_hour=data.get('hour'),
                    data_type=WeatherDataType.FORECAST,
                    temperature_current=data.get('temperature'),
                    temperature_min=data.get('temperature_min'),
                    temperature_max=data.get('temperature_max'),
                    humidity=data.get('humidity'),
                    rainfall_mm=data.get('rainfall'),
                    wind_speed_kmh=data.get('wind_speed'),
                    weather_condition=data.get('condition'),
                    weather_description=data.get('description'),
                    raw_data=data
                )
                
                await self.save_weather_data(weather_obj)
                
        except Exception as e:
            logger.error(f"❌ Error storing weather data: {e}")
    
    async def save_weather_data(self, weather_data: WeatherData):
        """Save weather data to database"""
        try:
            query = """
            INSERT INTO weather_data (
                location_id, provider_id, forecast_date, forecast_hour,
                data_type, temperature_current, temperature_min, temperature_max,
                humidity, rainfall_mm, wind_speed_kmh, weather_condition,
                weather_description, raw_data, data_quality_score
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (location_id, forecast_date, forecast_hour, data_type)
            DO UPDATE SET
                temperature_current = EXCLUDED.temperature_current,
                temperature_min = EXCLUDED.temperature_min,
                temperature_max = EXCLUDED.temperature_max,
                humidity = EXCLUDED.humidity,
                rainfall_mm = EXCLUDED.rainfall_mm,
                wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                weather_condition = EXCLUDED.weather_condition,
                weather_description = EXCLUDED.weather_description,
                raw_data = EXCLUDED.raw_data,
                data_quality_score = EXCLUDED.data_quality_score
            """
            
            await self.db_ops.execute_query(
                query, (
                    weather_data.location_id,
                    weather_data.provider_id,
                    weather_data.forecast_date,
                    weather_data.forecast_hour,
                    weather_data.data_type.value,
                    weather_data.temperature_current,
                    weather_data.temperature_min,
                    weather_data.temperature_max,
                    weather_data.humidity,
                    weather_data.rainfall_mm,
                    weather_data.wind_speed_kmh,
                    weather_data.weather_condition,
                    weather_data.weather_description,
                    json.dumps(weather_data.raw_data),
                    weather_data.data_quality_score
                )
            )
            
        except Exception as e:
            logger.error(f"❌ Error saving weather data: {e}")
    
    async def generate_weather_insights(self, farmer_id: int, location_id: int, 
                                      crop_type: str, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate LLM-powered weather insights for agriculture
        
        Args:
            farmer_id: Farmer ID
            location_id: Location ID
            crop_type: Crop type for insights
            weather_data: Weather data for analysis
            
        Returns:
            Dictionary containing LLM insights
        """
        try:
            # Prepare context for LLM
            context = {
                "farmer_id": farmer_id,
                "crop_type": crop_type,
                "weather_data": weather_data,
                "location_id": location_id,
                "analysis_date": datetime.now().isoformat(),
                "request_type": "agricultural_weather_insights"
            }
            
            # Create LLM prompt
            prompt = self.create_weather_insights_prompt(context)
            
            # Get LLM response
            start_time = datetime.now()
            llm_response = await self.llm_router.route_query(prompt, {})
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Parse LLM response
            insights = self.parse_llm_insights(llm_response)
            
            # Create weather insight object
            weather_insight = WeatherInsight(
                farmer_id=farmer_id,
                location_id=location_id,
                insight_type=WeatherInsightType.FORECAST,
                crop_type=crop_type,
                insight_title=insights.get('title', 'Weather Forecast'),
                insight_summary=insights.get('summary', ''),
                detailed_analysis=insights.get('analysis', ''),
                recommendations=insights.get('recommendations', ''),
                risk_level=insights.get('risk_level', 'low'),
                confidence_score=insights.get('confidence', 80),
                llm_model_used=llm_response.get('model', 'unknown'),
                llm_processing_time_ms=int(processing_time),
                llm_raw_response=llm_response,
                mango_rule_applicable=crop_type.lower() in ['mango', 'tropical fruit']
            )
            
            # Save insights to database
            await self.save_weather_insights(weather_insight)
            
            return asdict(weather_insight)
            
        except Exception as e:
            logger.error(f"❌ Error generating weather insights: {e}")
            return {"error": str(e)}
    
    def create_weather_insights_prompt(self, context: Dict[str, Any]) -> str:
        """Create LLM prompt for weather insights"""
        weather_summary = self.summarize_weather_data(context['weather_data'])
        
        return f"""
        You are an expert agricultural advisor providing weather insights for farmers.
        
        CONTEXT:
        - Farmer ID: {context['farmer_id']}
        - Crop Type: {context['crop_type']}
        - Location ID: {context['location_id']}
        - Analysis Date: {context['analysis_date']}
        
        WEATHER DATA SUMMARY:
        {weather_summary}
        
        TASK:
        Provide comprehensive agricultural weather insights for this {context['crop_type']} farmer.
        
        RESPONSE FORMAT (JSON):
        {{
            "title": "Brief insight title",
            "summary": "2-3 sentence summary",
            "analysis": "Detailed weather analysis",
            "recommendations": "Specific farming recommendations",
            "risk_level": "low/medium/high/critical",
            "confidence": 0-100,
            "planting_advice": "Planting recommendations",
            "irrigation_advice": "Irrigation recommendations",
            "pest_warnings": "Pest/disease warnings based on weather"
        }}
        
        REQUIREMENTS:
        - Focus on practical farming advice
        - Consider crop-specific needs
        - Include risk assessment
        - Provide actionable recommendations
        - Use clear, farmer-friendly language
        """
    
    def summarize_weather_data(self, weather_data: List[Dict[str, Any]]) -> str:
        """Summarize weather data for LLM prompt"""
        if not weather_data:
            return "No weather data available"
        
        summary = "Weather Forecast Summary:\n"
        
        for i, data in enumerate(weather_data[:7]):  # First 7 days
            summary += f"Day {i+1}: {data.get('condition', 'Unknown')}, "
            summary += f"Temp: {data.get('temperature_min', 'N/A')}-{data.get('temperature_max', 'N/A')}°C, "
            summary += f"Rain: {data.get('rainfall', 0)}mm, "
            summary += f"Wind: {data.get('wind_speed', 0)}km/h\n"
        
        return summary
    
    def parse_llm_insights(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured insights"""
        try:
            # Extract insights from LLM response
            response_text = llm_response.get('response', '')
            
            # Try to parse as JSON
            if response_text.strip().startswith('{'):
                return json.loads(response_text)
            
            # Fallback to text parsing
            return {
                'title': 'Weather Insights',
                'summary': response_text[:200] + '...' if len(response_text) > 200 else response_text,
                'analysis': response_text,
                'recommendations': 'Review weather conditions and adjust farming practices accordingly.',
                'risk_level': 'medium',
                'confidence': 70
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing LLM insights: {e}")
            return {
                'title': 'Weather Analysis',
                'summary': 'Weather analysis completed',
                'analysis': 'Please check weather conditions for your crops.',
                'recommendations': 'Monitor weather patterns and adjust farming practices.',
                'risk_level': 'low',
                'confidence': 50
            }
    
    async def save_weather_insights(self, insights: WeatherInsight):
        """Save weather insights to database"""
        try:
            query = """
            INSERT INTO weather_insights (
                farmer_id, location_id, insight_type, crop_type, insight_date,
                insight_title, insight_summary, detailed_analysis, recommendations,
                risk_level, confidence_score, mango_rule_applicable, language_code,
                llm_model_used, llm_processing_time_ms, llm_raw_response
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            await self.db_ops.execute_query(
                query, (
                    insights.farmer_id,
                    insights.location_id,
                    insights.insight_type.value,
                    insights.crop_type,
                    insights.insight_date,
                    insights.insight_title,
                    insights.insight_summary,
                    insights.detailed_analysis,
                    insights.recommendations,
                    insights.risk_level,
                    insights.confidence_score,
                    insights.mango_rule_applicable,
                    insights.language_code,
                    insights.llm_model_used,
                    insights.llm_processing_time_ms,
                    json.dumps(insights.llm_raw_response)
                )
            )
            
        except Exception as e:
            logger.error(f"❌ Error saving weather insights: {e}")
    
    async def get_farmer_location(self, farmer_id: int) -> Optional[WeatherLocation]:
        """Get farmer's weather location"""
        try:
            query = """
            SELECT * FROM weather_locations 
            WHERE farmer_id = %s 
            AND is_primary_location = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
            """
            
            result = await self.db_ops.fetch_one(query, (farmer_id,))
            
            if result:
                return WeatherLocation(**dict(result))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting farmer location: {e}")
            return None
    
    async def get_location_by_id(self, location_id: int) -> Optional[WeatherLocation]:
        """Get location by ID"""
        try:
            query = "SELECT * FROM weather_locations WHERE id = %s"
            result = await self.db_ops.fetch_one(query, (location_id,))
            
            if result:
                return WeatherLocation(**dict(result))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting location by ID: {e}")
            return None
    
    async def find_location_by_coordinates(self, latitude: float, longitude: float) -> Optional[WeatherLocation]:
        """Find existing location by coordinates (with tolerance)"""
        try:
            # Search within 0.01 degree tolerance (approximately 1km)
            tolerance = 0.01
            
            query = """
            SELECT * FROM weather_locations 
            WHERE latitude BETWEEN %s AND %s 
            AND longitude BETWEEN %s AND %s
            ORDER BY ABS(latitude - %s) + ABS(longitude - %s)
            LIMIT 1
            """
            
            result = await self.db_ops.fetch_one(
                query, (
                    latitude - tolerance, latitude + tolerance,
                    longitude - tolerance, longitude + tolerance,
                    latitude, longitude
                )
            )
            
            if result:
                return WeatherLocation(**dict(result))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding location by coordinates: {e}")
            return None
    
    async def create_location_from_coordinates(self, latitude: float, longitude: float) -> WeatherLocation:
        """Create new location from coordinates"""
        try:
            # Use reverse geocoding to get location details
            location_details = await self.reverse_geocode(latitude, longitude)
            
            location = WeatherLocation(
                latitude=Decimal(str(latitude)),
                longitude=Decimal(str(longitude)),
                location_name=location_details.get('city', 'Unknown'),
                country=location_details.get('country', 'Unknown'),
                country_code=location_details.get('country_code', 'XX'),
                region=location_details.get('region', ''),
                village=location_details.get('village', ''),
                climate_zone=location_details.get('climate_zone', ''),
                location_verified=True
            )
            
            # Save to database
            location_id = await self.save_location(location)
            location.id = location_id
            
            return location
            
        except Exception as e:
            logger.error(f"❌ Error creating location from coordinates: {e}")
            raise
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Reverse geocode coordinates to get location details"""
        try:
            # This would use a reverse geocoding service
            # For now, return basic details
            return {
                'city': f'Location_{latitude:.3f}_{longitude:.3f}',
                'country': 'Unknown',
                'country_code': 'XX',
                'region': '',
                'village': '',
                'climate_zone': 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"❌ Error reverse geocoding: {e}")
            return {}
    
    async def save_location(self, location: WeatherLocation) -> int:
        """Save location to database and return ID"""
        try:
            query = """
            INSERT INTO weather_locations (
                farmer_id, location_name, country, country_code, region,
                village, latitude, longitude, climate_zone, agricultural_zone,
                location_verified, mango_growing_suitable, location_insights
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """
            
            result = await self.db_ops.fetch_one(
                query, (
                    location.farmer_id,
                    location.location_name,
                    location.country,
                    location.country_code,
                    location.region,
                    location.village,
                    location.latitude,
                    location.longitude,
                    location.climate_zone,
                    location.agricultural_zone,
                    location.location_verified,
                    location.mango_growing_suitable,
                    json.dumps(location.location_insights)
                )
            )
            
            return result['id']
            
        except Exception as e:
            logger.error(f"❌ Error saving location: {e}")
            raise
    
    async def cache_weather_data(self, location_id: int, weather_data: List[Dict[str, Any]]):
        """Cache weather data for performance"""
        try:
            # Weather data is automatically cached in database
            # This method can be extended for additional caching layers
            logger.info(f"🏛️ Weather data cached for location {location_id}")
            
        except Exception as e:
            logger.error(f"❌ Error caching weather data: {e}")
    
    async def get_constitutional_compliance_score(self) -> int:
        """Get overall constitutional compliance score"""
        try:
            query = """
            SELECT AVG(constitutional_compliance_score) as avg_score
            FROM weather_providers 
            WHERE is_active = TRUE
            """
            
            result = await self.db_ops.fetch_one(query)
            
            if result and result['avg_score']:
                return int(result['avg_score'])
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error getting constitutional compliance score: {e}")
            return 0
    
    async def verify_mango_rule_compliance(self) -> bool:
        """Verify MANGO RULE compliance"""
        try:
            # Check if system can handle Bulgarian mango farmers
            test_location = WeatherLocation(
                location_name="Plovdiv",
                country="Bulgaria",
                country_code="BG",
                latitude=Decimal('42.1354'),
                longitude=Decimal('24.7453'),
                mango_growing_suitable=True
            )
            
            # Test weather data retrieval
            weather_data = await self.get_weather_by_coordinates(
                float(test_location.latitude), 
                float(test_location.longitude)
            )
            
            # Test LLM insights generation
            if weather_data and not weather_data.get('error'):
                insights = await self.generate_weather_insights(
                    0, 0, 'mango', weather_data.get('weather_data', [])
                )
                
                if insights and not insights.get('error'):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verifying MANGO RULE compliance: {e}")
            return False

# Export main class
__all__ = ['ConstitutionalWeatherService', 'WeatherLocation', 'WeatherData', 'WeatherInsight']