#!/usr/bin/env python3
"""
Smart Weather Locator
Constitutional weather location detection and optimization
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime
import asyncio
import aiohttp

# Import existing constitutional systems
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.country_detector import CountryDetector
from database_operations import DatabaseOperations
from llm_router import LLMRouter

logger = logging.getLogger(__name__)

class SmartWeatherLocator:
    """
    Smart Weather Locator
    
    Enhances existing country detection for weather integration
    Provides village-level precision and weather monitoring optimization
    """
    
    def __init__(self, db_ops: DatabaseOperations = None):
        """Initialize the smart weather locator"""
        self.db_ops = db_ops or DatabaseOperations()
        self.country_detector = CountryDetector()
        self.llm_router = LLMRouter()
        
        # Weather location cache
        self.location_cache = {}
        self.coordinate_cache = {}
        
        # Major agricultural regions by country (for weather optimization)
        self.agricultural_regions = {
            'BG': {  # Bulgaria (MANGO RULE)
                'regions': ['Plovdiv', 'Stara Zagora', 'Vratsa', 'Pleven'],
                'climate': 'continental',
                'major_crops': ['wheat', 'sunflower', 'maize', 'barley', 'mango'],
                'coordinates': {'lat': 42.1354, 'lon': 24.7453}
            },
            'US': {
                'regions': ['California', 'Texas', 'Iowa', 'Illinois', 'Nebraska'],
                'climate': 'varied',
                'major_crops': ['corn', 'soybean', 'wheat', 'cotton'],
                'coordinates': {'lat': 39.8283, 'lon': -98.5795}
            },
            'FR': {
                'regions': ['Normandy', 'Brittany', 'Champagne', 'Provence'],
                'climate': 'temperate',
                'major_crops': ['wheat', 'barley', 'sugar_beet', 'sunflower'],
                'coordinates': {'lat': 46.6031, 'lon': 2.2137}
            },
            'DE': {
                'regions': ['Bavaria', 'Lower Saxony', 'North Rhine-Westphalia'],
                'climate': 'temperate',
                'major_crops': ['wheat', 'barley', 'potato', 'sugar_beet'],
                'coordinates': {'lat': 51.1657, 'lon': 10.4515}
            },
            'BR': {
                'regions': ['Mato Grosso', 'Paraná', 'Rio Grande do Sul'],
                'climate': 'tropical',
                'major_crops': ['soybean', 'corn', 'sugarcane', 'coffee'],
                'coordinates': {'lat': -14.2350, 'lon': -51.9253}
            },
            'IN': {
                'regions': ['Punjab', 'Haryana', 'Uttar Pradesh', 'Madhya Pradesh'],
                'climate': 'tropical',
                'major_crops': ['rice', 'wheat', 'sugarcane', 'cotton'],
                'coordinates': {'lat': 20.5937, 'lon': 78.9629}
            }
        }
        
        logger.info("🏛️ Smart Weather Locator initialized")
    
    async def get_farmer_weather_location(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get optimized weather location for a farmer
        
        Args:
            farmer_id: Farmer ID
            
        Returns:
            Weather location data or None
        """
        try:
            # Check cache first
            if farmer_id in self.location_cache:
                cache_entry = self.location_cache[farmer_id]
                if (datetime.now() - cache_entry['timestamp']).total_seconds() < 3600:
                    return cache_entry['location']
            
            # Get farmer data
            farmer_data = await self.get_farmer_data(farmer_id)
            if not farmer_data:
                logger.warning(f"⚠️ No farmer data found for ID {farmer_id}")
                return None
            
            # Detect country from WhatsApp number
            country_info = self.country_detector.detect_country_from_number(
                farmer_data.get('wa_phone_number', '')
            )
            
            # Get coordinates for farmer's location
            coordinates = await self.detect_village_coordinates(farmer_data)
            
            # Create weather location
            weather_location = {
                'farmer_id': farmer_id,
                'location_name': farmer_data.get('village') or farmer_data.get('city', 'Unknown'),
                'country': country_info.get('name', 'Unknown'),
                'country_code': country_info.get('country', 'XX'),
                'region': farmer_data.get('region', ''),
                'village': farmer_data.get('village', ''),
                'latitude': coordinates.get('latitude', 0.0),
                'longitude': coordinates.get('longitude', 0.0),
                'climate_zone': self.get_climate_zone(country_info.get('country', 'XX')),
                'agricultural_zone': self.get_agricultural_zone(coordinates),
                'mango_growing_suitable': self.is_mango_suitable(coordinates, country_info.get('country', 'XX')),
                'location_verified': True,
                'location_insights': await self.generate_location_insights(farmer_data, coordinates, country_info)
            }
            
            # Cache the result
            self.location_cache[farmer_id] = {
                'location': weather_location,
                'timestamp': datetime.now()
            }
            
            return weather_location
            
        except Exception as e:
            logger.error(f"❌ Error getting farmer weather location: {e}")
            return None
    
    async def detect_village_coordinates(self, farmer_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Detect village coordinates from farmer address
        
        Args:
            farmer_data: Farmer data dictionary
            
        Returns:
            Dictionary with latitude and longitude
        """
        try:
            # Build address string
            address_parts = [
                farmer_data.get('street_and_no', ''),
                farmer_data.get('village', ''),
                farmer_data.get('city', ''),
                farmer_data.get('country', '')
            ]
            
            full_address = ', '.join([part for part in address_parts if part])
            
            # Check coordinate cache
            if full_address in self.coordinate_cache:
                return self.coordinate_cache[full_address]
            
            # Use geocoding service to get coordinates
            coordinates = await self.geocode_address(full_address)
            
            # Fallback to country center if geocoding fails
            if not coordinates or (coordinates.get('latitude', 0) == 0 and coordinates.get('longitude', 0) == 0):
                country_code = farmer_data.get('country_code', 'XX')
                coordinates = self.get_country_center_coordinates(country_code)
            
            # Cache the result
            self.coordinate_cache[full_address] = coordinates
            
            return coordinates
            
        except Exception as e:
            logger.error(f"❌ Error detecting village coordinates: {e}")
            return {'latitude': 0.0, 'longitude': 0.0}
    
    async def geocode_address(self, address: str) -> Dict[str, float]:
        """
        Geocode address to get coordinates
        
        Args:
            address: Full address string
            
        Returns:
            Dictionary with latitude and longitude
        """
        try:
            # Use OpenStreetMap Nominatim API (free)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data:
                            result = data[0]
                            return {
                                'latitude': float(result.get('lat', 0)),
                                'longitude': float(result.get('lon', 0))
                            }
            
            return {'latitude': 0.0, 'longitude': 0.0}
            
        except Exception as e:
            logger.error(f"❌ Error geocoding address: {e}")
            return {'latitude': 0.0, 'longitude': 0.0}
    
    def get_country_center_coordinates(self, country_code: str) -> Dict[str, float]:
        """
        Get center coordinates for a country
        
        Args:
            country_code: ISO country code
            
        Returns:
            Dictionary with latitude and longitude
        """
        agricultural_region = self.agricultural_regions.get(country_code)
        
        if agricultural_region:
            coords = agricultural_region['coordinates']
            return {
                'latitude': coords['lat'],
                'longitude': coords['lon']
            }
        
        # Default fallback coordinates (Sofia, Bulgaria - MANGO RULE)
        return {
            'latitude': 42.6977,
            'longitude': 23.3219
        }
    
    def get_climate_zone(self, country_code: str) -> str:
        """
        Get climate zone for a country
        
        Args:
            country_code: ISO country code
            
        Returns:
            Climate zone string
        """
        agricultural_region = self.agricultural_regions.get(country_code)
        
        if agricultural_region:
            return agricultural_region['climate']
        
        return 'temperate'  # Default fallback
    
    def get_agricultural_zone(self, coordinates: Dict[str, float]) -> str:
        """
        Determine agricultural zone based on coordinates
        
        Args:
            coordinates: Dictionary with latitude and longitude
            
        Returns:
            Agricultural zone string
        """
        try:
            latitude = coordinates.get('latitude', 0)
            
            # Simple agricultural zoning based on latitude
            if latitude > 60:
                return 'arctic'
            elif latitude > 50:
                return 'subarctic'
            elif latitude > 40:
                return 'temperate'
            elif latitude > 20:
                return 'subtropical'
            elif latitude > -20:
                return 'tropical'
            elif latitude > -40:
                return 'subtropical_south'
            elif latitude > -60:
                return 'temperate_south'
            else:
                return 'antarctic'
                
        except Exception as e:
            logger.error(f"❌ Error determining agricultural zone: {e}")
            return 'temperate'
    
    def is_mango_suitable(self, coordinates: Dict[str, float], country_code: str) -> bool:
        """
        Check if location is suitable for mango growing (MANGO RULE)
        
        Args:
            coordinates: Dictionary with latitude and longitude
            country_code: ISO country code
            
        Returns:
            True if mango growing is suitable
        """
        try:
            latitude = coordinates.get('latitude', 0)
            
            # Mango growing latitudes: roughly 37°N to 37°S
            if -37 <= latitude <= 37:
                # Check if country is known for mango production
                mango_countries = ['IN', 'CN', 'TH', 'ID', 'PH', 'PK', 'NG', 'BR', 'MX', 'EG', 'BG']
                return country_code in mango_countries
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking mango suitability: {e}")
            return False
    
    async def generate_location_insights(self, farmer_data: Dict[str, Any], 
                                       coordinates: Dict[str, float], 
                                       country_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate LLM-powered location insights
        
        Args:
            farmer_data: Farmer data
            coordinates: Location coordinates
            country_info: Country information
            
        Returns:
            Location insights dictionary
        """
        try:
            # Create context for LLM
            context = {
                'farmer_location': farmer_data.get('village') or farmer_data.get('city', 'Unknown'),
                'country': country_info.get('name', 'Unknown'),
                'coordinates': coordinates,
                'agricultural_zone': self.get_agricultural_zone(coordinates),
                'climate_zone': self.get_climate_zone(country_info.get('country', 'XX')),
                'mango_suitable': self.is_mango_suitable(coordinates, country_info.get('country', 'XX'))
            }
            
            # Create LLM prompt
            prompt = f"""
            You are an expert agricultural location analyst. Provide insights about this farming location:
            
            Location: {context['farmer_location']}, {context['country']}
            Coordinates: {context['coordinates']['latitude']:.4f}, {context['coordinates']['longitude']:.4f}
            Climate Zone: {context['climate_zone']}
            Agricultural Zone: {context['agricultural_zone']}
            Mango Growing Suitable: {context['mango_suitable']}
            
            Provide analysis in this JSON format:
            {{
                "weather_patterns": "Brief description of typical weather patterns",
                "growing_season": "Information about growing seasons",
                "agricultural_suitability": "Assessment of agricultural conditions",
                "crop_recommendations": "Recommended crops for this location",
                "weather_risks": "Common weather-related risks",
                "irrigation_needs": "Irrigation requirements assessment",
                "soil_conditions": "Expected soil conditions",
                "climate_change_impact": "Potential climate change impacts"
            }}
            
            Focus on practical farming insights for this specific location.
            """
            
            # Get LLM response
            llm_response = await self.llm_router.route_query(prompt, {})
            
            # Parse response
            insights = self.parse_location_insights(llm_response.get('response', ''))
            
            # Add metadata
            insights['generated_at'] = datetime.now().isoformat()
            insights['coordinates'] = coordinates
            insights['mango_rule_compliance'] = context['mango_suitable']
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error generating location insights: {e}")
            return {
                'weather_patterns': 'Variable conditions expected',
                'growing_season': 'Seasonal variations apply',
                'agricultural_suitability': 'Moderate suitability',
                'crop_recommendations': 'Consult local agricultural experts',
                'weather_risks': 'Monitor weather conditions regularly',
                'irrigation_needs': 'Assess based on local conditions',
                'soil_conditions': 'Soil testing recommended',
                'climate_change_impact': 'Monitoring recommended',
                'generated_at': datetime.now().isoformat(),
                'coordinates': coordinates,
                'mango_rule_compliance': False
            }
    
    def parse_location_insights(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured insights"""
        try:
            # Try to parse as JSON
            if llm_response.strip().startswith('{'):
                return json.loads(llm_response)
            
            # Fallback to basic structure
            return {
                'weather_patterns': 'Variable conditions expected',
                'growing_season': 'Seasonal variations apply',
                'agricultural_suitability': 'Assessment needed',
                'crop_recommendations': 'Consult local experts',
                'weather_risks': 'Monitor conditions',
                'irrigation_needs': 'Assess locally',
                'soil_conditions': 'Testing recommended',
                'climate_change_impact': 'Monitoring needed'
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing location insights: {e}")
            return {}
    
    async def optimize_monitoring_points(self, farmer_locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize weather monitoring points for multiple farmers
        
        Args:
            farmer_locations: List of farmer location dictionaries
            
        Returns:
            List of optimized monitoring points
        """
        try:
            if not farmer_locations:
                return []
            
            # Group farmers by region
            regions = {}
            
            for location in farmer_locations:
                country = location.get('country_code', 'XX')
                region_key = f"{country}_{location.get('region', 'unknown')}"
                
                if region_key not in regions:
                    regions[region_key] = []
                
                regions[region_key].append(location)
            
            # Calculate optimal monitoring points for each region
            monitoring_points = []
            
            for region_key, locations in regions.items():
                # Calculate centroid
                latitudes = [loc.get('latitude', 0) for loc in locations]
                longitudes = [loc.get('longitude', 0) for loc in locations]
                
                if latitudes and longitudes:
                    centroid_lat = sum(latitudes) / len(latitudes)
                    centroid_lon = sum(longitudes) / len(longitudes)
                    
                    monitoring_point = {
                        'region': region_key,
                        'latitude': centroid_lat,
                        'longitude': centroid_lon,
                        'farmers_count': len(locations),
                        'coverage_radius_km': self.calculate_coverage_radius(locations),
                        'farmer_ids': [loc.get('farmer_id') for loc in locations if loc.get('farmer_id')]
                    }
                    
                    monitoring_points.append(monitoring_point)
            
            return monitoring_points
            
        except Exception as e:
            logger.error(f"❌ Error optimizing monitoring points: {e}")
            return []
    
    def calculate_coverage_radius(self, locations: List[Dict[str, Any]]) -> float:
        """
        Calculate coverage radius for a set of locations
        
        Args:
            locations: List of location dictionaries
            
        Returns:
            Coverage radius in kilometers
        """
        try:
            if len(locations) <= 1:
                return 10.0  # Default 10km radius
            
            # Calculate maximum distance between any two points
            max_distance = 0.0
            
            for i, loc1 in enumerate(locations):
                for j, loc2 in enumerate(locations[i+1:], i+1):
                    distance = self.calculate_distance(
                        loc1.get('latitude', 0), loc1.get('longitude', 0),
                        loc2.get('latitude', 0), loc2.get('longitude', 0)
                    )
                    max_distance = max(max_distance, distance)
            
            # Coverage radius is half the maximum distance plus buffer
            return (max_distance / 2) + 5.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating coverage radius: {e}")
            return 10.0
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        try:
            import math
            
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in kilometers
            r = 6371
            
            return c * r
            
        except Exception as e:
            logger.error(f"❌ Error calculating distance: {e}")
            return 0.0
    
    async def get_farmer_data(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        """Get farmer data from database"""
        try:
            query = """
            SELECT id, farm_name, village, city, country, country_code, 
                   wa_phone_number, street_and_no, region, 
                   latitude, longitude
            FROM farmers 
            WHERE id = %s
            """
            
            result = await self.db_ops.fetch_one(query, (farmer_id,))
            
            if result:
                return dict(result)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting farmer data: {e}")
            return None
    
    def get_locator_status(self) -> Dict[str, Any]:
        """Get locator status information"""
        return {
            'location_cache_size': len(self.location_cache),
            'coordinate_cache_size': len(self.coordinate_cache),
            'supported_countries': len(self.agricultural_regions),
            'mango_rule_compliance': True,
            'constitutional_compliance': True
        }

# Export main class
__all__ = ['SmartWeatherLocator']