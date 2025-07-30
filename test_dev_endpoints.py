#!/usr/bin/env python3
"""
Test script for development database endpoints
Tests locally before deployment
"""

import os
import sys
import json
import asyncio
from fastapi.testclient import TestClient

# Set environment for testing
os.environ['ENVIRONMENT'] = 'development'
os.environ['DEV_ACCESS_KEY'] = 'temporary-dev-key-2025'

# Import the app after setting environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from monitoring_api import app
    client = TestClient(app)
    
    print("=== Development Database Endpoints Test ===\n")
    
    # Test headers
    headers = {"X-Dev-Key": "temporary-dev-key-2025"}
    
    # Test 1: List tables
    print("📋 Test 1: List Tables")
    try:
        response = client.get("/dev/db/tables", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Found {data['count']} tables")
                for table in data['tables'][:5]:  # Show first 5
                    print(f"  - {table['name']} ({table['columns']} columns, {table['rows']} rows)")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    
    # Test 2: Get schema
    print("\n📊 Test 2: Database Schema")
    try:
        response = client.get("/dev/db/schema", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Schema retrieved with {data['table_count']} tables")
                print(f"Tables: {', '.join(list(data['schema'].keys())[:5])}...")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    
    # Test 3: Simple query
    print("\n🔍 Test 3: Simple Query")
    try:
        query_data = {"query": "SELECT 1 as test_value"}
        response = client.post("/dev/db/query", headers=headers, json=query_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Query executed successfully")
                print(f"Result: {data['rows']}")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    
    # Test 4: Security check - invalid query
    print("\n🔒 Test 4: Security Check (Invalid Query)")
    try:
        query_data = {"query": "DELETE FROM test_table"}
        response = client.post("/dev/db/query", headers=headers, json=query_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            print("✅ Security check passed - DELETE query blocked")
        else:
            print(f"❌ Security check failed - DELETE query allowed")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    
    # Test 5: Invalid key
    print("\n🔐 Test 5: Authentication Check")
    try:
        bad_headers = {"X-Dev-Key": "wrong-key"}
        response = client.get("/dev/db/tables", headers=bad_headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication check passed - unauthorized access blocked")
        else:
            print(f"❌ Authentication check failed - unauthorized access allowed")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n=== Tests Complete ===")
    
except ImportError as e:
    print(f"❌ Cannot import monitoring_api: {e}")
    print("Make sure you're in the correct directory with the monitoring_api.py file")
except Exception as e:
    print(f"❌ Error running tests: {e}")