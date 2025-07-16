#!/usr/bin/env python3
"""
Test Weather API with Farmer Coordinates
Verify weather endpoints work with real farmer GPS coordinates
"""

import requests
import json
import asyncio
from datetime import datetime
from implementation.constitutional_geocoding_service import ConstitutionalGeocodingService

class FarmerWeatherTester:
    """Test weather API endpoints with farmer coordinates"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Local development
        self.aws_url = "https://your-app-runner-url.com"  # AWS deployment
        self.geocoder = ConstitutionalGeocodingService()
    
    async def test_weather_endpoints(self):
        """Test weather endpoints with real farmer coordinates"""
        
        print("🌤️ Testing Weather API with Farmer Coordinates...")
        
        # Test farmers from different countries
        test_farmers = [
            {
                'id': 1,
                'name': 'Bulgarian Mango Farmer',
                'address': {
                    'street_and_no': 'Plovdiv Street 123',
                    'village': 'Plovdiv',
                    'city': 'Plovdiv',
                    'country': 'Bulgaria',
                    'postal_code': '4000'
                },
                'mango_rule': True
            },
            {
                'id': 2,
                'name': 'Slovenian Farmer',
                'address': {
                    'street_and_no': 'Slovenska cesta 56',
                    'village': 'Ljubljana',
                    'city': 'Ljubljana',
                    'country': 'Slovenia',
                    'postal_code': '1000'
                },
                'mango_rule': False
            },
            {
                'id': 3,
                'name': 'Croatian Farmer',
                'address': {
                    'street_and_no': 'Ilica 10',
                    'village': 'Zagreb',
                    'city': 'Zagreb',
                    'country': 'Croatia',
                    'postal_code': '10000'
                },
                'mango_rule': False
            }
        ]
        
        results = []
        
        for farmer in test_farmers:
            print(f"\n📍 Testing {farmer['name']}...")
            
            # Get GPS coordinates
            location_result = await self.geocoder.geocode_address(farmer['address'])
            
            if not location_result:
                print(f"❌ Failed to get GPS coordinates for {farmer['name']}")
                continue
            
            print(f"   📍 GPS: {location_result.latitude:.6f}, {location_result.longitude:.6f}")
            
            # Test weather endpoints
            farmer_results = await self.test_farmer_weather_endpoints(
                farmer['id'], 
                location_result.latitude, 
                location_result.longitude,
                farmer['name'],
                farmer['mango_rule']
            )
            
            results.append({
                'farmer': farmer,
                'location': location_result,
                'weather_tests': farmer_results
            })
        
        return results
    
    async def test_farmer_weather_endpoints(self, farmer_id, lat, lon, farmer_name, mango_rule):
        """Test weather endpoints for a specific farmer"""
        
        endpoints_to_test = [
            {
                'name': 'Weather by Location',
                'url': f"/api/weather/location?lat={lat}&lon={lon}",
                'method': 'GET'
            },
            {
                'name': 'Weather Forecast',
                'url': f"/api/weather/forecast/farmer/{farmer_id}",
                'method': 'GET'
            },
            {
                'name': 'Weather Insights',
                'url': f"/api/weather/insights/farmer/{farmer_id}/crop/tomato",
                'method': 'GET'
            },
            {
                'name': 'Weather System Status',
                'url': f"/api/weather/status",
                'method': 'GET'
            }
        ]
        
        test_results = []
        
        for endpoint in endpoints_to_test:
            print(f"   🔍 Testing {endpoint['name']}...")
            
            result = await self.test_single_endpoint(
                endpoint['url'], 
                endpoint['method'],
                farmer_name,
                mango_rule
            )
            
            test_results.append({
                'endpoint': endpoint,
                'result': result
            })
        
        return test_results
    
    async def test_single_endpoint(self, endpoint_url, method, farmer_name, mango_rule):
        """Test a single weather endpoint"""
        
        try:
            # Try local development first
            url = f"{self.base_url}{endpoint_url}"
            
            print(f"      🌐 Testing: {url}")
            
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check constitutional compliance
                constitutional_compliance = data.get('constitutional_compliance', False)
                mango_rule_verified = data.get('mango_rule_verified', False)
                
                status = "✅ SUCCESS"
                if constitutional_compliance:
                    status += " | 🏛️ Constitutional"
                if mango_rule and mango_rule_verified:
                    status += " | 🥭 MANGO RULE"
                
                print(f"      {status}")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'constitutional_compliance': constitutional_compliance,
                    'mango_rule_verified': mango_rule_verified,
                    'response_data': data
                }
            else:
                print(f"      ❌ ERROR {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.ConnectionError:
            print(f"      ⚠️ Connection refused (service may not be running)")
            return {
                'success': False,
                'error': 'Connection refused - service not running'
            }
        except Exception as e:
            print(f"      ❌ Request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_weather_api_key(self):
        """Test weather API key validity"""
        
        print("🔑 Testing Weather API Key...")
        
        import os
        api_key = os.getenv('OPENWEATHERMAP_API_KEY', 'f1cc1e5b670d617592f00c3f37fd9db0')
        
        if not api_key:
            print("❌ OPENWEATHERMAP_API_KEY not found in environment")
            return False
        
        print(f"🔑 Testing API key: {api_key[:8]}...")
        
        # Test with Sofia, Bulgaria coordinates (MANGO RULE)
        lat, lon = 42.6977, 23.3219
        
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API key works!")
                print(f"   Location: {data.get('name', 'Unknown')}")
                print(f"   Temperature: {data.get('main', {}).get('temp', 'N/A')}°C")
                print(f"   Condition: {data.get('weather', [{}])[0].get('description', 'N/A')}")
                print(f"   Humidity: {data.get('main', {}).get('humidity', 'N/A')}%")
                return True
            elif response.status_code == 401:
                print("❌ API key is invalid")
                return False
            else:
                print(f"❌ API request failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing API key: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive weather API test"""
        
        print("🌤️ COMPREHENSIVE WEATHER API TEST")
        print("=" * 60)
        
        # Test 1: API Key
        api_key_valid = self.test_weather_api_key()
        
        # Test 2: Weather endpoints with farmer coordinates
        print("\n📍 Testing Weather Endpoints with Farmer Coordinates...")
        farmer_results = await self.test_weather_endpoints()
        
        # Test 3: Constitutional compliance summary
        print("\n🏛️ CONSTITUTIONAL COMPLIANCE SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        constitutional_compliant = 0
        mango_rule_verified = 0
        
        for farmer_result in farmer_results:
            farmer_name = farmer_result['farmer']['name']
            is_bulgarian = farmer_result['farmer']['mango_rule']
            
            print(f"\n{farmer_name}:")
            
            for test in farmer_result['weather_tests']:
                total_tests += 1
                endpoint_name = test['endpoint']['name']
                result = test['result']
                
                if result['success']:
                    passed_tests += 1
                    status = "✅ PASSED"
                    
                    if result.get('constitutional_compliance'):
                        constitutional_compliant += 1
                        status += " | 🏛️ Constitutional"
                    
                    if result.get('mango_rule_verified') and is_bulgarian:
                        mango_rule_verified += 1
                        status += " | 🥭 MANGO RULE"
                    
                    print(f"  {endpoint_name}: {status}")
                else:
                    print(f"  {endpoint_name}: ❌ FAILED - {result.get('error', 'Unknown error')}")
        
        # Final summary
        print(f"\n📊 FINAL RESULTS:")
        print(f"  API Key Valid: {'✅ YES' if api_key_valid else '❌ NO'}")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed Tests: {passed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"  Constitutional Compliance: {constitutional_compliant}/{total_tests} ({(constitutional_compliant/total_tests)*100:.1f}%)")
        print(f"  MANGO RULE Verification: {mango_rule_verified} Bulgarian tests")
        
        overall_success = api_key_valid and passed_tests == total_tests
        
        print(f"\n🎯 OVERALL STATUS: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        if overall_success:
            print("🚀 Weather API is ready for production!")
            print("🏛️ Constitutional compliance verified")
            print("🥭 MANGO RULE compatibility confirmed")
        else:
            print("⚠️ Weather API needs attention before production")
        
        return {
            'api_key_valid': api_key_valid,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'constitutional_compliant': constitutional_compliant,
            'mango_rule_verified': mango_rule_verified,
            'overall_success': overall_success,
            'farmer_results': farmer_results
        }

# Main execution
async def main():
    """Main test execution"""
    tester = FarmerWeatherTester()
    results = await tester.run_comprehensive_test()
    return results

if __name__ == "__main__":
    asyncio.run(main())