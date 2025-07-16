#!/usr/bin/env python3
"""
Test script for farmer registration functionality
"""
import requests
import json

# Test data
test_farmer = {
    "email": "test@example.com",
    "password": "testpassword123",
    "manager_name": "John",
    "manager_last_name": "Doe",
    "wa_phone_number": "+385912345678",
    "phone": "+385912345678",
    "farm_name": "Test Farm",
    "state_farm_number": "12345",
    "street_and_no": "Test Street 123",
    "village": "Test Village",
    "city": "Zagreb",
    "postal_code": "10000",
    "country": "Croatia",
    "fields": [
        {
            "name": "North Field",
            "size": 5.5,
            "location": "45.8150° N, 15.9819° E"
        },
        {
            "name": "South Field", 
            "size": 3.2,
            "location": "45.8100° N, 15.9800° E"
        }
    ]
}

def test_farmer_registration():
    """Test farmer registration endpoint"""
    url = "http://localhost:8000/api/register-farmer"
    
    try:
        response = requests.post(url, json=test_farmer)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Farmer registration successful!")
                print(f"Farmer ID: {result.get('farmer_id')}")
            else:
                print(f"❌ Registration failed: {result.get('message')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure server is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_farmer_registration()