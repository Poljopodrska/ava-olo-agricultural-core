#!/usr/bin/env python3
"""
Location Service
Handles farmer location retrieval and geocoding
"""
import logging
from typing import Dict, Optional, Tuple
import httpx
import asyncio
from urllib.parse import quote

from modules.core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

class LocationService:
    """Service for managing farmer locations"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        # Default location for Slovenia (Ljubljana)
        self.default_location = {
            "lat": 46.0569,
            "lon": 14.5058,
            "city": "Ljubljana",
            "country": "Slovenia"
        }
    
    async def get_farmer_location(self, farmer_id: int) -> Dict[str, any]:
        """Get farmer's location from database"""
        try:
            # Try to get farmer location from database
            query = """
            SELECT name, city, address, country, latitude, longitude
            FROM farmers
            WHERE farmer_id = %s
            """
            
            result = self.db_manager.execute_query(query, (farmer_id,))
            
            if result and result.get('rows'):
                row = result['rows'][0]
                name, city, address, country, lat, lon = row
                
                # If we have coordinates, use them
                if lat and lon:
                    return {
                        "lat": float(lat),
                        "lon": float(lon),
                        "city": city or "Unknown",
                        "country": country or "Slovenia",
                        "address": address,
                        "name": name
                    }
                
                # If we have city/address, geocode them
                if city or address:
                    location_str = f"{address}, {city}, {country}" if address else f"{city}, {country}"
                    coords = await self.geocode_address(location_str)
                    if coords:
                        # Update database with coordinates for future use
                        await self._update_farmer_coordinates(farmer_id, coords[0], coords[1])
                        return {
                            "lat": coords[0],
                            "lon": coords[1],
                            "city": city or "Unknown",
                            "country": country or "Slovenia",
                            "address": address,
                            "name": name
                        }
            
            # Check if this might be Kmetija Vrzel specifically
            if await self._check_if_kmetija_vrzel(farmer_id):
                # Known location for Kmetija Vrzel in Slovenia
                return {
                    "lat": 46.2397,  # Maribor area
                    "lon": 15.6444,
                    "city": "Maribor",
                    "country": "Slovenia",
                    "address": "Kmetija Vrzel",
                    "name": "Kmetija Vrzel"
                }
            
        except Exception as e:
            logger.error(f"Error getting farmer location: {e}")
        
        # Return default location if nothing found
        logger.warning(f"No location found for farmer {farmer_id}, using default")
        return self.default_location
    
    async def _check_if_kmetija_vrzel(self, farmer_id: int) -> bool:
        """Check if this farmer is Kmetija Vrzel"""
        try:
            query = """
            SELECT name, whatsapp_number
            FROM farmers
            WHERE farmer_id = %s
            AND (name ILIKE '%vrzel%' OR name ILIKE '%kmetija%')
            """
            
            result = self.db_manager.execute_query(query, (farmer_id,))
            return result and len(result.get('rows', [])) > 0
        except:
            return False
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode an address using OpenStreetMap Nominatim"""
        try:
            # Use OpenStreetMap Nominatim (free, no API key needed)
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": "AVA-OLO-Agricultural-Platform/1.0"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        lat = float(data[0]["lat"])
                        lon = float(data[0]["lon"])
                        logger.info(f"Geocoded '{address}' to ({lat}, {lon})")
                        return (lat, lon)
                
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
        
        return None
    
    async def _update_farmer_coordinates(self, farmer_id: int, lat: float, lon: float):
        """Update farmer's coordinates in database"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if latitude/longitude columns exist
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'farmers' 
                        AND column_name IN ('latitude', 'longitude')
                    """)
                    
                    columns = [row[0] for row in cur.fetchall()]
                    
                    if 'latitude' in columns and 'longitude' in columns:
                        cur.execute("""
                            UPDATE farmers 
                            SET latitude = %s, longitude = %s 
                            WHERE farmer_id = %s
                        """, (lat, lon, farmer_id))
                        conn.commit()
                        logger.info(f"Updated coordinates for farmer {farmer_id}")
        except Exception as e:
            logger.error(f"Failed to update farmer coordinates: {e}")
    
    def get_location_display(self, location: Dict[str, any]) -> str:
        """Get a display string for the location"""
        city = location.get('city', 'Unknown')
        country = location.get('country', '')
        
        if city and country:
            return f"{city}, {country}"
        elif city:
            return city
        else:
            return "Location not set"

# Singleton instance
_location_service = None

def get_location_service() -> LocationService:
    """Get or create location service instance"""
    global _location_service
    if _location_service is None:
        _location_service = LocationService()
    return _location_service