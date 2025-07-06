#!/usr/bin/env python3
"""
Test script for Business Dashboard structure and API endpoints
Tests the business dashboard without requiring database connection
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_imports():
    """Test that all dashboard components can be imported"""
    print("=== Testing Dashboard Imports ===")
    
    try:
        # Test basic imports
        from monitoring.business_dashboard import (
            UsageMetrics, SystemMetrics, BusinessInsights, 
            BusinessDashboard, router
        )
        print("✅ All dashboard classes imported successfully")
        
        # Test pydantic models
        usage = UsageMetrics(
            total_queries=100,
            unique_users=25,
            daily_active_users=5,
            average_session_length=0.0,
            top_features=[],
            growth_rate=15.2
        )
        print("✅ UsageMetrics model working")
        
        system = SystemMetrics(
            uptime_percentage=99.5,
            average_response_time=150.0,
            error_rate=1.2,
            api_calls_per_day=200,
            peak_usage_hours=[9, 14, 16],
            system_load={"cpu": 0.0, "memory": 0.0, "storage": 0.0}
        )
        print("✅ SystemMetrics model working")
        
        insights = BusinessInsights(
            farmer_adoption_rate=68.5,
            geographic_distribution={"Zagreb": 25, "Split": 12},
            crop_coverage={"Corn": 45, "Wheat": 32},
            seasonal_trends={"monthly_activity": [0] * 12},
            user_satisfaction=87.3
        )
        print("✅ BusinessInsights model working")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_api_routes():
    """Test that API routes are properly configured"""
    print("\n=== Testing API Routes ===")
    
    try:
        from monitoring.business_dashboard import router
        
        # Count routes
        routes = [route for route in router.routes if hasattr(route, 'path')]
        print(f"✅ Found {len(routes)} API routes")
        
        # Expected endpoints
        expected_endpoints = [
            '/api/v1/business/usage',
            '/api/v1/business/system',
            '/api/v1/business/insights',
            '/api/v1/business/projections',
            '/api/v1/business/summary'
        ]
        
        # Check each endpoint
        found_endpoints = []
        for route in routes:
            if hasattr(route, 'path'):
                found_endpoints.append(route.path)
                methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'Unknown'
                print(f"   📍 {methods} {route.path}")
        
        # Verify all expected endpoints exist
        missing = set(expected_endpoints) - set(found_endpoints)
        if missing:
            print(f"❌ Missing endpoints: {missing}")
            return False
        else:
            print("✅ All expected endpoints found")
            return True
            
    except Exception as e:
        print(f"❌ Route testing failed: {str(e)}")
        return False

def test_api_integration():
    """Test integration with main API gateway"""
    print("\n=== Testing API Integration ===")
    
    try:
        # Test import in API gateway context
        from interfaces.api_gateway import app
        
        # Check if business router is included
        has_business_routes = False
        for route in app.routes:
            if hasattr(route, 'path') and '/api/v1/business' in route.path:
                has_business_routes = True
                break
        
        if has_business_routes:
            print("✅ Business dashboard routes integrated into main API")
            return True
        else:
            print("❌ Business dashboard routes not found in main API")
            return False
            
    except Exception as e:
        print(f"❌ API integration test failed: {str(e)}")
        return False

def test_sql_queries():
    """Test SQL query structure without database connection"""
    print("\n=== Testing SQL Query Structure ===")
    
    try:
        # Read the business dashboard file to analyze SQL queries
        with open('/mnt/c/Users/HP/ava_olo_project/monitoring/business_dashboard.py', 'r') as f:
            content = f.read()
        
        # Check for key SQL patterns
        sql_patterns = [
            'SELECT COUNT(*) FROM ava_conversations',
            'SELECT COUNT(DISTINCT farmer_id)',
            'INTERVAL ',
            'GROUP BY',
            'ORDER BY',
            'LEFT JOIN',
            'EXTRACT(MONTH FROM created_at)',
            'DATE_TRUNC'
        ]
        
        found_patterns = []
        for pattern in sql_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        print(f"✅ Found {len(found_patterns)}/{len(sql_patterns)} expected SQL patterns")
        
        # Check for Croatian-specific elements
        croatian_elements = [
            'ava_farmers',
            'ava_conversations',
            'ava_field_crops',
            'system_health_log',
            'llm_debug_log'
        ]
        
        found_croatian = [elem for elem in croatian_elements if elem in content]
        print(f"✅ Found {len(found_croatian)}/{len(croatian_elements)} Croatian schema elements")
        
        return len(found_patterns) >= len(sql_patterns) * 0.8  # 80% of patterns found
        
    except Exception as e:
        print(f"❌ SQL structure test failed: {str(e)}")
        return False

def test_database_schema():
    """Test database schema structure"""
    print("\n=== Testing Database Schema ===")
    
    try:
        # Read schema file
        with open('/mnt/c/Users/HP/ava_olo_project/create_schema.sql', 'r') as f:
            schema_content = f.read()
        
        # Check for required tables
        required_tables = [
            'ava_farmers',
            'ava_conversations',
            'ava_fields',
            'ava_field_crops',
            'system_health_log',
            'llm_debug_log',
            'farm_tasks'
        ]
        
        found_tables = []
        for table in required_tables:
            if f'CREATE TABLE {table}' in schema_content:
                found_tables.append(table)
        
        print(f"✅ Found {len(found_tables)}/{len(required_tables)} required tables")
        
        # Check for indexes
        index_count = schema_content.count('CREATE INDEX')
        print(f"✅ Found {index_count} database indexes")
        
        # Check for Croatian crop data
        croatian_crops = ['Kukuruz', 'Pšenica', 'Suncokret', 'Rajčica']
        found_crops = [crop for crop in croatian_crops if crop in schema_content]
        print(f"✅ Found {len(found_crops)}/{len(croatian_crops)} Croatian crop names")
        
        return len(found_tables) == len(required_tables)
        
    except Exception as e:
        print(f"❌ Schema test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling in dashboard code"""
    print("\n=== Testing Error Handling ===")
    
    try:
        with open('/mnt/c/Users/HP/ava_olo_project/monitoring/business_dashboard.py', 'r') as f:
            content = f.read()
        
        # Check for error handling patterns
        error_patterns = [
            'try:',
            'except Exception as e:',
            'logger.error(',
            'HTTPException(',
            'return.*{.*}',  # Default return values
        ]
        
        found_errors = []
        for pattern in error_patterns:
            if pattern in content:
                found_errors.append(pattern)
        
        print(f"✅ Found {len(found_errors)}/{len(error_patterns)} error handling patterns")
        
        # Count try/except blocks
        try_count = content.count('try:')
        except_count = content.count('except Exception as e:')
        
        print(f"✅ Found {try_count} try blocks and {except_count} except blocks")
        
        return try_count >= 4 and except_count >= 4  # Should have multiple error handlers
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all structural tests"""
    print("AVA OLO Business Dashboard - Structural Testing")
    print("=" * 60)
    
    tests = [
        ("Dashboard Imports", test_dashboard_imports),
        ("API Routes", test_api_routes),
        ("API Integration", test_api_integration),
        ("SQL Queries", test_sql_queries),
        ("Database Schema", test_database_schema),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All structural tests passed!")
        print("\n📋 Business Dashboard Status: READY")
        print("\n🚀 Next Steps:")
        print("1. Set up PostgreSQL database")
        print("2. Install required dependencies (asyncpg, sqlalchemy)")
        print("3. Run: python interfaces/api_gateway.py")
        print("4. Test endpoints at: http://localhost:8000/api/v1/business/")
        print("5. View API docs at: http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)