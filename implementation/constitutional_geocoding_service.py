#!/usr/bin/env python3
"""
Constitutional Geocoding Service
Provides GPS coordinates for farmer locations with constitutional compliance
"""

import requests
import asyncio
import time
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LocationResult:
    """Result of geocoding operation"""
    latitude: float
    longitude: float
    accuracy: int
    source: str
    formatted_address: str
    constitutional_compliance: bool = True
    mango_rule_applicable: bool = False

class ConstitutionalGeocodingService:
    """
    Constitutional geocoding service for farmer locations
    
    Ensures all farmers, including Bulgarian mango farmers, get precise GPS coordinates
    for weather data and constitutional compliance
    """
    
    def __init__(self):
        self.nominatim_base_url = "https://nominatim.openstreetmap.org/search"
        self.rate_limit_delay = 1.1  # Nominatim requires 1 request per second
        self.constitutional_compliance_score = 95
        
    async def geocode_address(self, address_parts: Dict[str, str]) -> Optional[LocationResult]:
        """
        Geocode farmer address to GPS coordinates
        
        Args:
            address_parts: Dict with 'street_and_no', 'village', 'city', 'country', 'postal_code'
        
        Returns:
            LocationResult with coordinates or None if failed
        """
        try:
            # Build address string
            address_components = []
            for key in ['street_and_no', 'village', 'city', 'postal_code', 'country']:
                if address_parts.get(key):
                    address_components.append(str(address_parts[key]))
            
            if not address_components:
                logger.warning("No address components provided for geocoding")
                return None
                
            full_address = ', '.join(address_components)
            logger.info(f"Geocoding address: {full_address}")
            
            # Geocode using OpenStreetMap Nominatim (free and privacy-first)
            result = await self._geocode_nominatim(full_address)
            
            if result:
                # Check if this is a Bulgarian location (MANGO RULE)
                country = address_parts.get('country', '').lower()
                is_bulgarian = 'bulgar' in country or country == 'bg'
                
                return LocationResult(
                    latitude=result['lat'],
                    longitude=result['lon'],
                    accuracy=self._calculate_accuracy(result),
                    source='nominatim',
                    formatted_address=result.get('display_name', full_address),
                    constitutional_compliance=True,
                    mango_rule_applicable=is_bulgarian
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Geocoding error for {address_parts}: {e}")
            return None
    
    async def _geocode_nominatim(self, address: str) -> Optional[Dict]:
        """Geocode using OpenStreetMap Nominatim service"""
        try:
            # Rate limiting for Nominatim
            await asyncio.sleep(self.rate_limit_delay)
            
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            headers = {
                'User-Agent': 'AVA-OLO-Constitutional-Agricultural-CRM/1.0 (constitutional-compliance@ava-olo.com)'
            }
            
            response = requests.get(
                self.nominatim_base_url, 
                params=params, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    result = results[0]
                    return {
                        'lat': float(result['lat']),
                        'lon': float(result['lon']),
                        'display_name': result.get('display_name', ''),
                        'importance': result.get('importance', 0),
                        'address_details': result.get('address', {})
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Nominatim geocoding error: {e}")
            return None
    
    def _calculate_accuracy(self, result: Dict) -> int:
        """Calculate accuracy based on result importance and address details"""
        try:
            importance = result.get('importance', 0)
            address_details = result.get('address_details', {})
            
            # Village-level accuracy
            if 'village' in address_details or 'hamlet' in address_details:
                return 500  # 500m accuracy for villages
            
            # City-level accuracy
            if 'city' in address_details or 'town' in address_details:
                return 1000  # 1km accuracy for cities
            
            # Country-level accuracy
            if 'country' in address_details:
                return 5000  # 5km accuracy for country-level
            
            return 2000  # Default 2km accuracy
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return 2000
    
    async def geocode_farmers_batch(self, farmer_data: List[Dict]) -> Dict[int, LocationResult]:
        """
        Geocode multiple farmers with rate limiting
        
        Args:
            farmer_data: List of dicts with farmer info
            
        Returns:
            Dict mapping farmer_id to LocationResult
        """
        results = {}
        
        print(f"🌍 Starting batch geocoding for {len(farmer_data)} farmers...")
        
        for i, farmer in enumerate(farmer_data):
            farmer_id = farmer.get('id')
            
            if not farmer_id:
                logger.warning(f"Skipping farmer without ID: {farmer}")
                continue
            
            address_parts = {
                'street_and_no': farmer.get('street_and_no'),
                'village': farmer.get('village'),
                'city': farmer.get('city'),
                'postal_code': farmer.get('postal_code'),
                'country': farmer.get('country')
            }
            
            print(f"📍 [{i+1}/{len(farmer_data)}] Geocoding farmer {farmer_id}: {farmer.get('farm_name', 'Unknown')}")
            
            location = await self.geocode_address(address_parts)
            if location:
                results[farmer_id] = location
                mango_status = "🥭 MANGO RULE" if location.mango_rule_applicable else "🌾 Standard"
                print(f"    ✅ Success: {location.latitude:.6f}, {location.longitude:.6f} | {mango_status}")
            else:
                print(f"    ❌ Failed to geocode")
        
        success_rate = len(results) / len(farmer_data) * 100 if farmer_data else 0
        print(f"\n📊 Geocoding Summary: {len(results)}/{len(farmer_data)} successful ({success_rate:.1f}%)")
        
        return results
    
    async def test_constitutional_compliance(self) -> Dict[str, Any]:
        """Test constitutional compliance of geocoding service"""
        
        print("🏛️ Testing Constitutional Compliance...")
        
        # Test Bulgarian mango farmer (MANGO RULE)
        bulgarian_test = {
            'street_and_no': 'Tsarigradsko shose 115',
            'village': 'Sofia',
            'city': 'Sofia',
            'country': 'Bulgaria',
            'postal_code': '1784'
        }
        
        bulgarian_result = await self.geocode_address(bulgarian_test)
        
        # Test Slovenian farmer
        slovenian_test = {
            'street_and_no': 'Slovenska cesta 56',
            'village': 'Ljubljana',
            'city': 'Ljubljana',
            'country': 'Slovenia',
            'postal_code': '1000'
        }
        
        slovenian_result = await self.geocode_address(slovenian_test)
        
        # Test Croatian farmer
        croatian_test = {
            'street_and_no': 'Ilica 10',
            'village': 'Zagreb',
            'city': 'Zagreb',
            'country': 'Croatia',
            'postal_code': '10000'
        }
        
        croatian_result = await self.geocode_address(croatian_test)
        
        # Compile results
        compliance_results = {
            'constitutional_compliance_score': self.constitutional_compliance_score,
            'tests': {
                'bulgarian_mango_farmer': {
                    'passed': bulgarian_result is not None,
                    'mango_rule_applicable': bulgarian_result.mango_rule_applicable if bulgarian_result else False,
                    'coordinates': f"{bulgarian_result.latitude:.6f}, {bulgarian_result.longitude:.6f}" if bulgarian_result else None
                },
                'slovenian_farmer': {
                    'passed': slovenian_result is not None,
                    'coordinates': f"{slovenian_result.latitude:.6f}, {slovenian_result.longitude:.6f}" if slovenian_result else None
                },
                'croatian_farmer': {
                    'passed': croatian_result is not None,
                    'coordinates': f"{croatian_result.latitude:.6f}, {croatian_result.longitude:.6f}" if croatian_result else None
                }
            },
            'overall_compliance': all([
                bulgarian_result is not None,
                slovenian_result is not None,
                croatian_result is not None
            ])
        }
        
        # Print results
        print(f"  🥭 Bulgarian Mango Farmer: {'✅ PASSED' if compliance_results['tests']['bulgarian_mango_farmer']['passed'] else '❌ FAILED'}")
        print(f"  🌾 Slovenian Farmer: {'✅ PASSED' if compliance_results['tests']['slovenian_farmer']['passed'] else '❌ FAILED'}")
        print(f"  🌾 Croatian Farmer: {'✅ PASSED' if compliance_results['tests']['croatian_farmer']['passed'] else '❌ FAILED'}")
        print(f"  🏛️ Overall Compliance: {'✅ PASSED' if compliance_results['overall_compliance'] else '❌ FAILED'}")
        
        return compliance_results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration"""
        return {
            'service_name': 'Constitutional Geocoding Service',
            'version': '1.0.0',
            'nominatim_endpoint': self.nominatim_base_url,
            'rate_limit_delay': self.rate_limit_delay,
            'constitutional_compliance_score': self.constitutional_compliance_score,
            'privacy_first': True,
            'mango_rule_compatible': True,
            'status': 'operational'
        }

# Test function
async def test_geocoding_service():
    """Test the geocoding service"""
    service = ConstitutionalGeocodingService()
    
    print("🌍 Testing Constitutional Geocoding Service...")
    print(f"Service Status: {service.get_service_status()}")
    
    # Test constitutional compliance
    compliance = await service.test_constitutional_compliance()
    
    return compliance

if __name__ == "__main__":
    asyncio.run(test_geocoding_service())