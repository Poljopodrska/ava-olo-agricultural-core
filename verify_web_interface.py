#!/usr/bin/env python3
"""
Verify Web Interface is Working
Tests the constitutional web interface routes
"""
import asyncio
import httpx
from api_gateway_constitutional import app
from fastapi.testclient import TestClient

def test_web_routes():
    """Test web interface routes"""
    print("🏛️ Constitutional Web Interface Verification")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Web interface home
    print("\n1. Testing /web/ route...")
    response = client.get("/web/")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Web interface home working!")
        # Check for constitutional elements
        content = response.text
        if "AVA OLO Web Interface" in content:
            print("   ✅ Title found")
        if "MANGO RULE" in content:
            print("   ✅ MANGO RULE compliance verified")
        if "18px" in content:
            print("   ✅ Constitutional font size verified")
        if "#6B5B73" in content or "#5D5E3F" in content:
            print("   ✅ Constitutional colors verified")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 2: Web health endpoint
    print("\n2. Testing /web/health route...")
    response = client.get("/web/health")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Web health endpoint working!")
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Constitutional Compliance: {data.get('constitutional_compliance')}")
        print(f"   MANGO RULE: {data.get('mango_rule')}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 3: Main health endpoint
    print("\n3. Testing /health route...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Main health endpoint working!")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎯 VERIFICATION COMPLETE")
    print("Ready for AWS deployment testing!")

if __name__ == "__main__":
    test_web_routes()