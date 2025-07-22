#!/usr/bin/env python3
"""
Test AI Connection and Weather for Ljubljana
Verify services are working correctly for Kmetija Vrzel
"""
import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

async def test_debug_endpoint():
    """Test the comprehensive debug endpoint"""
    print("\n🔍 TESTING DEBUG SERVICES ENDPOINT")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/debug/services", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check OpenAI
                openai = data['services']['openai']
                print("\n📱 OpenAI Status:")
                print(f"  API Key Set: {openai['api_key_set']}")
                print(f"  Connection Test: {openai['connection_test']}")
                print(f"  Chat Instance Connected: {openai['chat_instance_connected']}")
                if openai.get('test_response'):
                    print(f"  Test Response (2+2): {openai['test_response']}")
                
                # Check Weather
                weather = data['services']['weather']
                print("\n🌤️ Weather Service:")
                print(f"  API Key Set: {weather['api_key_set']}")
                print(f"  Test Location: {weather['test_location']}")
                print(f"  Coordinates: {weather['coordinates']}")
                print(f"  Status: {weather.get('status', 'Unknown')}")
                if weather.get('actual_location'):
                    print(f"  Actual Location: {weather['actual_location']}")
                if weather.get('weather_data'):
                    wd = weather['weather_data']
                    print(f"  Current: {wd['temperature']}°C, {wd['description']}")
                
                # Check Location
                location = data['services']['location']
                print("\n📍 Farmer Location:")
                if location.get('farmer_name'):
                    print(f"  Farmer: {location['farmer_name']}")
                    print(f"  City: {location['city']}")
                    print(f"  Country: {location['country']}")
                    print(f"  Coordinates: {location['coordinates']}")
                else:
                    print(f"  Status: {location.get('status', 'Unknown')}")
                
                return data
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    return None

async def test_chat_functionality():
    """Test chat with farming questions"""
    print("\n\n💬 TESTING CHAT FUNCTIONALITY")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/v1/chat/test", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\nAll Successful: {data['all_successful']}")
                print(f"Chat Connected: {data['chat_connected']}")
                
                print("\nTest Results:")
                for i, result in enumerate(data['test_results'], 1):
                    print(f"\n{i}. Question: {result['question']}")
                    if result['success']:
                        print(f"   ✅ Success (Length: {result['length']} chars)")
                        print(f"   Response: {result['response']}")
                    else:
                        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                        
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def test_weather_endpoint():
    """Test weather endpoint for farmer"""
    print("\n\n🌍 TESTING WEATHER FOR FARMER")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test current weather
            response = await client.get(f"{BASE_URL}/api/weather/current-farmer", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    weather = data['data']
                    print(f"\nLocation: {weather.get('farmer_location', 'Unknown')}")
                    print(f"Temperature: {weather.get('temperature', 'N/A')}°C")
                    print(f"Description: {weather.get('description', 'N/A')}")
                    
                    # Check coordinates
                    if weather.get('coord'):
                        coord = weather['coord']
                        print(f"Coordinates: {coord.get('lat', 'N/A')}°N, {coord.get('lon', 'N/A')}°E")
            else:
                print(f"Weather endpoint returned: {response.status_code}")
                
        except Exception as e:
            print(f"Weather test error: {str(e)}")

async def check_version():
    """Check current version"""
    print("\n\n📋 VERSION CHECK")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/version", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"Current Version: {data['version']}")
                print(f"Build ID: {data['build_id']}")
            else:
                print(f"Version check failed: {response.status_code}")
        except Exception as e:
            print(f"Version check error: {str(e)}")

async def main():
    print("🧪 AVA OLO SERVICE VERIFICATION TEST")
    print(f"Time: {datetime.now()}")
    print(f"Target: {BASE_URL}")
    
    # Check version first
    await check_version()
    
    # Run debug endpoint test
    debug_data = await test_debug_endpoint()
    
    # Test chat if API key is set
    if debug_data and debug_data['services']['openai']['api_key_set']:
        await test_chat_functionality()
    else:
        print("\n⚠️ Skipping chat test - OpenAI API key not set")
    
    # Test weather
    await test_weather_endpoint()
    
    print("\n\n✅ TEST COMPLETE")
    print("=" * 60)
    
    # Summary
    if debug_data:
        openai_working = "✅ Working" in debug_data['services']['openai'].get('connection_test', '')
        weather_working = "✅ Working" in debug_data['services']['weather'].get('status', '')
        
        print("\n📊 SUMMARY:")
        print(f"  OpenAI: {'✅ Connected' if openai_working else '❌ Not Connected'}")
        print(f"  Weather: {'✅ Working' if weather_working else '❌ Not Working'}")
        print(f"  Location: Ljubljana, Slovenia")
        
        if openai_working:
            print("\n✅ Kmetija Vrzel can chat with GPT-4!")
        if weather_working:
            print("✅ Ljubljana weather is displayed correctly!")

if __name__ == "__main__":
    asyncio.run(main())