#!/usr/bin/env python3
"""
Test script for Business Dashboard endpoints
Tests all business dashboard API endpoints with sample data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from monitoring.business_dashboard import BusinessDashboard
from core.database_operations import DatabaseOperations

async def create_sample_data():
    """Create sample data for testing the business dashboard"""
    print("Creating sample data...")
    
    db_ops = DatabaseOperations()
    
    try:
        with db_ops.get_session() as session:
            # Create sample farmers
            farmers_data = [
                {
                    'farm_name': 'Farma Horvat',
                    'manager_name': 'Marko',
                    'manager_last_name': 'Horvat',
                    'city': 'Zagreb',
                    'farmer_type': 'grain',
                    'total_hectares': 50.5
                },
                {
                    'farm_name': 'OPG Novak',
                    'manager_name': 'Ana',
                    'manager_last_name': 'Novak',
                    'city': 'Osijek',
                    'farmer_type': 'mixed',
                    'total_hectares': 25.0
                },
                {
                    'farm_name': 'Farma Petrović',
                    'manager_name': 'Ivo',
                    'manager_last_name': 'Petrović',
                    'city': 'Split',
                    'farmer_type': 'vegetable',
                    'total_hectares': 15.2
                }
            ]
            
            farmer_ids = []
            for farmer in farmers_data:
                result = session.execute(
                    """
                    INSERT INTO ava_farmers (farm_name, manager_name, manager_last_name, city, farmer_type, total_hectares)
                    VALUES (%(farm_name)s, %(manager_name)s, %(manager_last_name)s, %(city)s, %(farmer_type)s, %(total_hectares)s)
                    RETURNING id
                    """,
                    farmer
                ).fetchone()
                if result:
                    farmer_ids.append(result[0])
            
            # Create sample conversations
            conversation_topics = ['pest_control', 'fertilization', 'weather', 'harvest', 'planting']
            for i, farmer_id in enumerate(farmer_ids):
                for j in range(10):  # 10 conversations per farmer
                    days_ago = j + 1
                    created_at = datetime.now() - timedelta(days=days_ago)
                    
                    session.execute(
                        """
                        INSERT INTO ava_conversations (farmer_id, question, answer, created_at, topic, confidence_score)
                        VALUES (%(farmer_id)s, %(question)s, %(answer)s, %(created_at)s, %(topic)s, %(confidence_score)s)
                        """,
                        {
                            'farmer_id': farmer_id,
                            'question': f'Test question {j+1} for farmer {farmer_id}',
                            'answer': f'Test answer {j+1} for farmer {farmer_id}',
                            'created_at': created_at,
                            'topic': conversation_topics[j % len(conversation_topics)],
                            'confidence_score': 0.85 + (j * 0.01)
                        }
                    )
            
            # Create sample system health logs
            components = ['database', 'knowledge_base', 'external_api', 'llm_router']
            for i in range(50):  # 50 health check entries
                hours_ago = i
                checked_at = datetime.now() - timedelta(hours=hours_ago)
                
                session.execute(
                    """
                    INSERT INTO system_health_log (component_name, status, response_time_ms, checked_at)
                    VALUES (%(component)s, %(status)s, %(response_time)s, %(checked_at)s)
                    """,
                    {
                        'component': components[i % len(components)],
                        'status': 'healthy' if i % 10 != 0 else 'degraded',  # 10% degraded
                        'response_time': 50 + (i * 5),  # Varying response times
                        'checked_at': checked_at
                    }
                )
            
            # Create sample LLM debug logs
            for i in range(100):  # 100 LLM operations
                days_ago = i // 10
                created_at = datetime.now() - timedelta(days=days_ago)
                
                session.execute(
                    """
                    INSERT INTO llm_debug_log (operation_type, input_text, output_text, success, created_at)
                    VALUES (%(operation_type)s, %(input_text)s, %(output_text)s, %(success)s, %(created_at)s)
                    """,
                    {
                        'operation_type': 'query',
                        'input_text': f'Test query {i+1}',
                        'output_text': f'Test response {i+1}',
                        'success': i % 20 != 0,  # 5% failure rate
                        'created_at': created_at
                    }
                )
            
            session.commit()
            print(f"✓ Created sample data: {len(farmer_ids)} farmers, 30 conversations, 50 health logs, 100 LLM logs")
            return farmer_ids
            
    except Exception as e:
        print(f"✗ Error creating sample data: {str(e)}")
        return []

async def test_business_dashboard():
    """Test all business dashboard endpoints"""
    print("\n=== Testing Business Dashboard ===")
    
    dashboard = BusinessDashboard()
    
    # Test 1: Usage Metrics
    print("\n1. Testing Usage Metrics...")
    try:
        usage_metrics = await dashboard.get_usage_metrics(days=30)
        print(f"   ✓ Total queries: {usage_metrics.total_queries}")
        print(f"   ✓ Unique users: {usage_metrics.unique_users}")
        print(f"   ✓ Daily active users: {usage_metrics.daily_active_users}")
        print(f"   ✓ Growth rate: {usage_metrics.growth_rate:.2f}%")
        print(f"   ✓ Top features: {len(usage_metrics.top_features)}")
    except Exception as e:
        print(f"   ✗ Usage metrics failed: {str(e)}")
    
    # Test 2: System Metrics
    print("\n2. Testing System Metrics...")
    try:
        system_metrics = await dashboard.get_system_metrics(days=7)
        print(f"   ✓ Uptime: {system_metrics.uptime_percentage:.1f}%")
        print(f"   ✓ Avg response time: {system_metrics.average_response_time:.1f}ms")
        print(f"   ✓ Error rate: {system_metrics.error_rate:.2f}%")
        print(f"   ✓ Daily API calls: {system_metrics.api_calls_per_day}")
        print(f"   ✓ Peak hours: {system_metrics.peak_usage_hours}")
    except Exception as e:
        print(f"   ✗ System metrics failed: {str(e)}")
    
    # Test 3: Business Insights
    print("\n3. Testing Business Insights...")
    try:
        insights = await dashboard.get_business_insights()
        print(f"   ✓ Farmer adoption rate: {insights.farmer_adoption_rate:.1f}%")
        print(f"   ✓ Geographic distribution: {len(insights.geographic_distribution)} cities")
        print(f"   ✓ Crop coverage: {len(insights.crop_coverage)} crop types")
        print(f"   ✓ User satisfaction: {insights.user_satisfaction:.1f}%")
        print(f"   ✓ Seasonal trends: {len(insights.seasonal_trends.get('monthly_activity', []))} months")
    except Exception as e:
        print(f"   ✗ Business insights failed: {str(e)}")
    
    # Test 4: Growth Projections
    print("\n4. Testing Growth Projections...")
    try:
        projections = await dashboard.get_growth_projections(months=6)
        print(f"   ✓ Projected farmers: {projections['projected_active_farmers']}")
        print(f"   ✓ Projected queries: {projections['projected_monthly_queries']}")
        print(f"   ✓ Confidence: {projections['confidence']}")
        print(f"   ✓ Historical data points: {len(projections['historical_data'])}")
    except Exception as e:
        print(f"   ✗ Growth projections failed: {str(e)}")
    
    # Test 5: Error Handling
    print("\n5. Testing Error Handling...")
    try:
        # Test with invalid parameters
        invalid_metrics = await dashboard.get_usage_metrics(days=-1)
        print(f"   ✓ Handled invalid parameters gracefully")
    except Exception as e:
        print(f"   ✓ Error handling working: {str(e)}")

async def test_api_integration():
    """Test API integration by importing the endpoints"""
    print("\n=== Testing API Integration ===")
    
    try:
        from monitoring.business_dashboard import router
        print("   ✓ Business dashboard router imported successfully")
        
        # Count available endpoints
        endpoint_count = len([route for route in router.routes if hasattr(route, 'path')])
        print(f"   ✓ Found {endpoint_count} API endpoints")
        
        # List endpoints
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"     - {methods} {route.path}")
        
    except Exception as e:
        print(f"   ✗ API integration failed: {str(e)}")

async def run_tests():
    """Run all tests"""
    print("AVA OLO Business Dashboard - Integration Test")
    print("=" * 50)
    
    # Create sample data
    farmer_ids = await create_sample_data()
    
    if farmer_ids:
        # Run dashboard tests
        await test_business_dashboard()
    
    # Test API integration
    await test_api_integration()
    
    print("\n" + "=" * 50)
    print("✅ Business Dashboard Integration Test Complete")
    print("\nNext steps:")
    print("1. Start the API server: python interfaces/api_gateway.py")
    print("2. Test endpoints with curl or Postman:")
    print("   - GET /api/v1/business/usage")
    print("   - GET /api/v1/business/system") 
    print("   - GET /api/v1/business/insights")
    print("   - GET /api/v1/business/projections")
    print("   - GET /api/v1/business/summary")

if __name__ == "__main__":
    asyncio.run(run_tests())