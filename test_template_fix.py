#!/usr/bin/env python3
"""Test template loading issue"""

# Check if we can access the UI dashboard directly
import requests

url = "https://6pmgrirjre.us-east-1.awsapprunner.com"

print("Testing template loading...")

# Test 1: Check if templates are accessible
endpoints = [
    '/ui-dashboard',
    '/database-explorer', 
    '/register-fields',
    '/static/css/constitutional-design.css'
]

for endpoint in endpoints:
    try:
        resp = requests.get(f"{url}{endpoint}", timeout=5)
        print(f"{endpoint}: {resp.status_code}")
        if resp.status_code == 500:
            # Try to get error details
            print(f"  Error: {resp.text[:100]}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {str(e)}")

# Test 2: Check if old dashboard still works
print("\nChecking old dashboards:")
old_endpoints = ['/database-dashboard', '/agronomic-dashboard', '/business-dashboard']
for endpoint in old_endpoints:
    try:
        resp = requests.get(f"{url}{endpoint}", timeout=5)
        print(f"{endpoint}: {resp.status_code}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {str(e)}")