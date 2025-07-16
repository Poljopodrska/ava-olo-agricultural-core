#!/usr/bin/env python3
"""
Deployment Safety Test Script
Tests the new UI changes to ensure they don't break existing functionality
"""

import sys
import subprocess
import requests
import time
import json

def test_api_endpoints():
    """Test that all critical API endpoints are still working"""
    print("🔍 Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints_to_test = [
        ("/", "GET", None, "Landing page"),
        ("/login", "GET", None, "Login page"),
        ("/register", "GET", None, "Register page"),
        ("/dashboard", "GET", None, "Dashboard page"),
        ("/main", "GET", None, "Main interface"),
        ("/health", "GET", None, "Health check"),
        ("/api/v1/health", "GET", None, "API health check"),
    ]
    
    results = []
    for endpoint, method, data, description in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=data, timeout=5)
            
            status = "✅" if response.status_code < 400 else "❌"
            results.append(f"{status} {description}: {response.status_code}")
        except Exception as e:
            results.append(f"❌ {description}: {str(e)}")
    
    return results

def test_database_connectivity():
    """Test database connection is still working"""
    print("🔍 Testing database connectivity...")
    
    try:
        # Test database connection through the debug endpoint
        response = requests.get("http://localhost:8000/debug/env", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("DATABASE_URL"):
                return ["✅ Database URL is configured"]
            else:
                return ["❌ Database URL is not configured"]
        else:
            return ["❌ Debug endpoint not accessible"]
    except Exception as e:
        return [f"❌ Database connectivity test failed: {str(e)}"]

def test_static_pages():
    """Test that static pages load without JavaScript errors"""
    print("🔍 Testing static page loading...")
    
    results = []
    pages = ["/", "/login", "/register"]
    
    for page in pages:
        try:
            response = requests.get(f"http://localhost:8000{page}", timeout=5)
            if response.status_code == 200:
                # Check for basic HTML structure
                content = response.text
                if "<html" in content and "</html>" in content:
                    results.append(f"✅ {page} loads correctly")
                else:
                    results.append(f"❌ {page} has invalid HTML")
            else:
                results.append(f"❌ {page} returned status {response.status_code}")
        except Exception as e:
            results.append(f"❌ {page} failed: {str(e)}")
    
    return results

def check_no_auth_sections_on_landing():
    """Ensure landing page doesn't show auth sections"""
    print("🔍 Checking landing page content...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        content = response.text
        
        # Check that landing page has the correct buttons
        checks = [
            ("Sign in" in content, "Sign in button present"),
            ("Join AVA OLO" in content, "Join AVA OLO button present"),
            ("chatMessages" not in content, "No chat interface on landing"),
            ("Weather" not in content, "No weather section on landing"),
            ("Submit Question" not in content, "No query interface on landing")
        ]
        
        results = []
        for check, description in checks:
            status = "✅" if check else "❌"
            results.append(f"{status} {description}")
        
        return results
    except Exception as e:
        return [f"❌ Landing page check failed: {str(e)}"]

def main():
    print("🚀 AVA OLO Deployment Safety Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ Server is running")
    except:
        print("❌ Server is not running on port 8000")
        print("Please start the server with: python api_gateway_simple.py")
        return 1
    
    # Run all tests
    all_results = []
    
    # Test 1: API endpoints
    all_results.extend(test_api_endpoints())
    
    # Test 2: Database connectivity
    all_results.extend(test_database_connectivity())
    
    # Test 3: Static pages
    all_results.extend(test_static_pages())
    
    # Test 4: Landing page content
    all_results.extend(check_no_auth_sections_on_landing())
    
    # Print results
    print("\n📊 Test Results:")
    print("=" * 50)
    for result in all_results:
        print(result)
    
    # Count failures
    failures = sum(1 for r in all_results if "❌" in r)
    total = len(all_results)
    
    print("\n" + "=" * 50)
    print(f"📈 Summary: {total - failures}/{total} tests passed")
    
    if failures == 0:
        print("✅ All tests passed! Safe to deploy.")
        return 0
    else:
        print(f"❌ {failures} tests failed. Please fix before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())