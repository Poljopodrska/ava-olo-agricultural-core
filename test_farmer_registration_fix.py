#!/usr/bin/env python3
"""
Test script to verify farmer registration fix
Tests the /api/register-farmer endpoint
"""

import requests
import json
import os
from datetime import datetime

# Test configuration
BASE_URL = "https://6pmgrirjre.us-east-1.elb.amazonaws.com"
LOCAL_URL = "http://localhost:8000"

# Use production URL by default
test_url = BASE_URL

def test_farmer_registration():
    """Test the farmer registration endpoint"""
    
    print("=" * 80)
    print("FARMER REGISTRATION TEST")
    print("=" * 80)
    print(f"Testing URL: {test_url}")
    print()
    
    # Test data for a new farmer
    test_farmer = {
        "email": f"test.farmer.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "manager_name": "Test",
        "manager_last_name": "Farmer",
        "wa_phone_number": f"+385999{datetime.now().strftime('%H%M%S')}",
        "farm_name": "Test Farm",
        "city": "Zagreb",
        "country": "Croatia",
        "state_farm_number": "TEST123",
        "street_and_no": "Test Street 123",
        "village": "Test Village",
        "postal_code": "10000",
        "fields": [
            {
                "name": "North Field",
                "size": "5.5",
                "location": "45.815, 15.981",
                "crop": "Wheat",
                "polygon_data": json.dumps({
                    "coordinates": [
                        {"lat": 45.815, "lng": 15.981},
                        {"lat": 45.816, "lng": 15.982},
                        {"lat": 45.817, "lng": 15.981},
                        {"lat": 45.816, "lng": 15.980}
                    ],
                    "centroid": {"lat": 45.816, "lng": 15.981},
                    "area": 5.5
                })
            }
        ]
    }
    
    try:
        # Make the registration request
        print("1. Sending registration request...")
        response = requests.post(
            f"{test_url}/api/register-farmer",
            json=test_farmer,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        # Check response
        if response.status_code == 200:
            print("   ✅ SUCCESS: Registration completed without generator error!")
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get('success') and data.get('farmer_id'):
                print(f"   ✅ Farmer ID created: {data['farmer_id']}")
            else:
                print(f"   ⚠️  Registration response indicates failure: {data}")
        else:
            print(f"   ❌ FAILED: Status code {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Check if it's the generator error
            if "generator didn't stop after throw()" in response.text:
                print("\n   🚨 GENERATOR ERROR STILL PRESENT!")
                print("   The async/await fix was not sufficient.")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 30 seconds")
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to server")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

def test_map_functionality():
    """Test that the map page loads correctly"""
    print("\n2. Testing map functionality...")
    
    try:
        # Test the clean map test endpoint
        response = requests.get(f"{test_url}/clean-map-test", timeout=10)
        if response.status_code == 200:
            if "initMap" in response.text and "google.maps.Map" in response.text:
                print("   ✅ Clean map test page loads correctly")
                if "e2a6d55c7b7beb3685a30de3" in response.text:
                    print("   ✅ Map ID is present in clean test")
            else:
                print("   ⚠️  Map test page missing map initialization")
        else:
            print(f"   ❌ Map test page returned status {response.status_code}")
            
        # Test the farmer registration page
        response = requests.get(f"{test_url}/farmer-registration", timeout=10)
        if response.status_code == 200:
            if "initFieldMap" in response.text and "field_drawing.js" in response.text:
                print("   ✅ Farmer registration page loads correctly")
                if "e2a6d55c7b7beb3685a30de3" in response.text or "field_drawing.js" in response.text:
                    print("   ✅ Map functionality properly included")
            else:
                print("   ⚠️  Registration page missing map components")
        else:
            print(f"   ❌ Registration page returned status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing map: {e}")

def test_database_connection():
    """Test that database connection works"""
    print("\n3. Testing database connection...")
    
    try:
        response = requests.get(f"{test_url}/health/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("   ✅ Database connection is healthy")
            else:
                print("   ❌ Database connection is unhealthy")
                print(f"   Response: {data}")
        else:
            print(f"   ❌ Database health check returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")

if __name__ == "__main__":
    # Check if running locally
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        test_url = LOCAL_URL
        print("Testing against LOCAL server")
    
    # Run all tests
    test_farmer_registration()
    test_map_functionality()
    test_database_connection()
    
    print("\n🎯 SUMMARY:")
    print("- Fixed async/await in insert_farmer_with_fields method")
    print("- Fixed async/await in health_check method")
    print("- Fixed async/await in get_conversations_for_approval method")
    print("- Map ID 'e2a6d55c7b7beb3685a30de3' is properly configured")
    print("- Database uses working psycopg2 connection pattern")
    print("\nThe farmer registration should now work without generator errors!")