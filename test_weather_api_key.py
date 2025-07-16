#!/usr/bin/env python3
"""
Test OpenWeatherMap API Key
Quick test to verify the weather API key works
"""

import os
import requests
import json

def test_openweathermap_key():
    """Test OpenWeatherMap API key"""
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    
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

if __name__ == "__main__":
    success = test_openweathermap_key()
    exit(0 if success else 1)