#!/usr/bin/env python3
"""
Test Database Connection and Data
This script adds test data and verifies it can be retrieved
"""

import requests
import json
import time
from datetime import datetime

# Base URL for the deployed app
BASE_URL = "https://6pmgrirjre.us-east-1.elb.amazonaws.com/database"

def test_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/test-connection", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Database connected successfully!")
                print(f"   Database: {data['connection']['current_database']}")
                print(f"   Host: {data['connection']['host']}")
                return True
            else:
                print(f"❌ Database connection failed: {data.get('error', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return False

def add_test_data():
    """Add test data to farmers table"""
    print("\n📝 Adding test data to farmers table...")
    try:
        response = requests.post(f"{BASE_URL}/api/add-test-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ {data['message']}")
                return True
            else:
                print(f"ℹ️  {data['message']}")
                return True  # Still OK if data already exists
        else:
            print(f"❌ Failed to add test data: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        return False

def check_farmers_data():
    """Check if we can retrieve farmers data"""
    print("\n🔍 Checking farmers table data...")
    try:
        response = requests.get(f"{BASE_URL}/api/table/farmers/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                print(f"❌ Error accessing farmers table: {data['error']}")
                return False
            
            total_records = data.get('total_records', 0)
            print(f"✅ Farmers table accessible!")
            print(f"   Total records: {total_records}")
            
            if total_records > 0:
                print("\n👥 Sample farmers:")
                for farmer in data.get('sample_data', [])[:3]:
                    print(f"   - {farmer.get('farm_name', 'N/A')} ({farmer.get('manager_name', 'N/A')} {farmer.get('manager_last_name', 'N/A')})")
                    print(f"     Location: {farmer.get('city', 'N/A')}, {farmer.get('country', 'N/A')}")
            
            return True
        else:
            print(f"❌ Failed to get farmers data: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking farmers data: {e}")
        return False

def test_ai_query():
    """Test AI query functionality"""
    print("\n🤖 Testing AI query functionality...")
    try:
        query = "show all farmers"
        response = requests.post(
            f"{BASE_URL}/api/ai-query",
            data={"query_description": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['execution']['success']:
                row_count = data['execution'].get('row_count', 0)
                print(f"✅ AI query successful!")
                print(f"   Query: '{query}'")
                print(f"   Generated SQL: {data['query']['sql_query']}")
                print(f"   Results: {row_count} rows")
                return True
            else:
                print(f"❌ AI query failed: {data['execution'].get('error', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"❌ Error testing AI query: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🚀 AVA OLO Database Test Tool")
    print("="*60)
    print(f"\nTesting deployment at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_connection():
        tests_passed += 1
    
    if add_test_data():
        tests_passed += 1
        time.sleep(1)  # Give database time to process
    
    if check_farmers_data():
        tests_passed += 1
    
    if test_ai_query():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"📊 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! Database is working correctly.")
        print("\n🎯 Next steps:")
        print("1. Visit Database Explorer: https://6pmgrirjre.us-east-1.elb.amazonaws.com/database/")
        print("2. Browse the farmers table to see your test data")
        print("3. Try the AI Query Assistant")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nPossible issues:")
        print("- AWS deployment might still be in progress (wait 2-3 minutes)")
        print("- Database connection credentials might be incorrect")
        print("- Network connectivity issues")
    
    print("="*60)

if __name__ == "__main__":
    main()