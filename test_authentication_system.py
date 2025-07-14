#!/usr/bin/env python3
"""
Comprehensive test for AVA OLO authentication system
Tests all authentication endpoints and functionality
"""
import requests
import json
import sys
import time
from datetime import datetime

# Production URL
BASE_URL = "https://3ksdvgdtad.us-east-1.awsapprunner.com"

# Test credentials
DEFAULT_USER = {
    "phone": "+1234567890",
    "password": "farm1"
}

def test_health():
    """Test basic health endpoint"""
    print("1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_farmers_api():
    """Test existing farmers API (should work without auth)"""
    print("\n2️⃣ Testing existing farmers API...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/farmers", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {len(data.get('farmers', []))} farmers")
            return True
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_auth_status():
    """Test authentication status endpoint"""
    print("\n3️⃣ Testing auth status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/status", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def run_migration():
    """Run Aurora migration"""
    print("\n4️⃣ Running Aurora migration...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/migrate", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            return data.get('success', False)
        else:
            print(f"   Response: {response.text}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n5️⃣ Testing user login...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "wa_phone_number": DEFAULT_USER["phone"],
                "password": DEFAULT_USER["password"]
            },
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Login successful!")
                print(f"   Token: {data.get('token', '')[:50]}...")
                print(f"   User: {data.get('user', {}).get('user_name')}")
                return True, data.get('token')
            else:
                print(f"   ❌ Login failed: {data.get('message')}")
        else:
            print(f"   Response: {response.text}")
        return False, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def test_authenticated_endpoints(token):
    """Test endpoints that require authentication"""
    print("\n6️⃣ Testing authenticated endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /api/v1/auth/me
    print("\n   Testing /api/v1/auth/me...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Current user: {data.get('user', {}).get('user_name')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test /api/v1/auth/family
    print("\n   Testing /api/v1/auth/family...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/family",
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            members = data.get('family_members', [])
            print(f"   ✅ Family members: {len(members)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test /api/v1/farmers/me
    print("\n   Testing /api/v1/farmers/me...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/farmers/me",
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            farmer = data.get('farmer', {})
            print(f"   ✅ Farm: {farmer.get('farm_name')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🏛️ AVA OLO AUTHENTICATION SYSTEM TEST")
    print("=" * 60)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    # Run tests
    health_ok = test_health()
    farmers_ok = test_farmers_api()
    auth_status_ok = test_auth_status()
    
    # Run migration if needed
    if auth_status_ok:
        migration_ok = run_migration()
        
        # Test login
        if migration_ok or True:  # Try login even if migration says tables exist
            login_ok, token = test_login()
            
            if login_ok and token:
                test_authenticated_endpoints(token)
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()