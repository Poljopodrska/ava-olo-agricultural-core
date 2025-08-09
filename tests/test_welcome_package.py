#!/usr/bin/env python3
"""
Test Welcome Package System for Redis-based farmer context caching
"""
import time
import json
from datetime import datetime
from modules.core.redis_config import RedisConfig
from modules.core.welcome_package_manager import WelcomePackageManager
from modules.core.simple_db import execute_simple_query

def test_redis_connection():
    """Test basic Redis connectivity"""
    print("Testing Redis connection...")
    
    if RedisConfig.test_redis_connection():
        print("✅ Redis connection successful")
        info = RedisConfig.get_redis_info()
        print(f"  Redis version: {info.get('redis_version', 'unknown')}")
        print(f"  Memory usage: {info.get('used_memory_human', 'unknown')}")
        return True
    else:
        print("❌ Redis connection failed")
        return False

def test_welcome_package_lifecycle():
    """
    Test complete welcome package workflow
    Create, use, update, verify
    """
    print("\nTesting Welcome Package lifecycle...")
    
    # Initialize components
    redis_client = RedisConfig.get_redis_client()
    if not redis_client:
        print("❌ Cannot test - Redis not available")
        return False
    
    # Create DB wrapper
    class SimpleDBOps:
        def execute_query(self, query, params):
            return execute_simple_query(query, params)
    
    db_ops = SimpleDBOps()
    welcome_package_manager = WelcomePackageManager(redis_client, db_ops)
    
    # Test with a real farmer ID (adjust based on your database)
    # First, let's find a farmer
    result = execute_simple_query("SELECT id, manager_name FROM farmers LIMIT 1", ())
    if not result.get('success') or not result.get('rows'):
        print("❌ No farmers found in database")
        return False
    
    farmer_id = result['rows'][0][0]
    farmer_name = result['rows'][0][1]
    print(f"  Testing with farmer: {farmer_name} (ID: {farmer_id})")
    
    # 1. First access - should build from database
    print("  1. Building package from database...")
    start_time = time.time()
    package1 = welcome_package_manager.get_welcome_package(farmer_id)
    db_time = time.time() - start_time
    
    assert package1['farmer_id'] == farmer_id
    assert 'fields' in package1
    assert 'source' in package1
    print(f"  ✅ Package built from database in {db_time:.3f} seconds")
    print(f"     - Fields: {package1['total_fields']}")
    print(f"     - Hectares: {package1['total_hectares']}")
    
    # 2. Second access - should come from Redis (much faster)
    print("  2. Loading package from Redis...")
    start_time = time.time()
    package2 = welcome_package_manager.get_welcome_package(farmer_id)
    redis_time = time.time() - start_time
    
    assert package1['generated_at'] == package2['generated_at']  # Same timestamp = from cache
    print(f"  ✅ Package loaded from Redis in {redis_time:.3f} seconds")
    print(f"     - Speed improvement: {db_time/redis_time:.1f}x faster")
    
    # 3. Check package stats
    stats = welcome_package_manager.get_package_stats(farmer_id)
    print(f"  3. Package stats:")
    print(f"     - Exists in Redis: {stats['exists']}")
    print(f"     - TTL remaining: {stats['ttl_hours']:.2f} hours")
    
    # 4. Update package
    print("  4. Updating package...")
    welcome_package_manager.update_package_data(farmer_id, {
        "fields": package2['fields'],
        "test_update": True
    })
    
    # 5. Verify update
    package3 = welcome_package_manager.get_welcome_package(farmer_id)
    assert 'last_updated' in package3
    print("  ✅ Package updated successfully")
    
    # 6. Clear and rebuild
    print("  5. Testing cache clear and rebuild...")
    welcome_package_manager.clear_package(farmer_id)
    stats_after_clear = welcome_package_manager.get_package_stats(farmer_id)
    assert not stats_after_clear['exists']
    print("  ✅ Package cleared from cache")
    
    # Rebuild
    package4 = welcome_package_manager.get_welcome_package(farmer_id)
    assert package4['generated_at'] != package1['generated_at']  # Different timestamp = rebuilt
    print("  ✅ Package rebuilt from database")
    
    print("\n✅ Welcome package lifecycle test passed!")
    return True

def test_performance():
    """Test response time improvement with Redis caching"""
    print("\nTesting performance improvement...")
    
    redis_client = RedisConfig.get_redis_client()
    if not redis_client:
        print("❌ Cannot test performance - Redis not available")
        return False
    
    # Create components
    class SimpleDBOps:
        def execute_query(self, query, params):
            return execute_simple_query(query, params)
    
    db_ops = SimpleDBOps()
    welcome_package_manager = WelcomePackageManager(redis_client, db_ops)
    
    # Get all farmers for testing
    result = execute_simple_query("SELECT id FROM farmers LIMIT 5", ())
    if not result.get('success') or not result.get('rows'):
        print("❌ No farmers found")
        return False
    
    farmer_ids = [row[0] for row in result['rows']]
    
    # Test database access times
    print(f"  Testing with {len(farmer_ids)} farmers...")
    db_times = []
    for farmer_id in farmer_ids:
        # Clear cache first
        welcome_package_manager.clear_package(farmer_id)
        
        # Time database access
        start = time.time()
        package = welcome_package_manager.get_welcome_package(farmer_id)
        db_times.append(time.time() - start)
    
    avg_db_time = sum(db_times) / len(db_times)
    print(f"  Average database access time: {avg_db_time:.3f} seconds")
    
    # Test Redis access times
    redis_times = []
    for farmer_id in farmer_ids:
        # Access from cache
        start = time.time()
        package = welcome_package_manager.get_welcome_package(farmer_id)
        redis_times.append(time.time() - start)
    
    avg_redis_time = sum(redis_times) / len(redis_times)
    print(f"  Average Redis access time: {avg_redis_time:.3f} seconds")
    
    # Performance metrics
    improvement = avg_db_time / avg_redis_time
    print(f"\n  📊 Performance Results:")
    print(f"     - Speed improvement: {improvement:.1f}x faster")
    print(f"     - Time saved per request: {(avg_db_time - avg_redis_time)*1000:.0f}ms")
    
    # Check if meets target (<100ms)
    if avg_redis_time < 0.1:
        print(f"  ✅ Meets performance target (<100ms)")
    else:
        print(f"  ⚠️  Redis access slower than target: {avg_redis_time*1000:.0f}ms")
    
    print("\n✅ Performance test completed!")
    return True

def main():
    """Run all welcome package tests"""
    print("=" * 60)
    print("REDIS WELCOME PACKAGE SYSTEM TESTS")
    print("=" * 60)
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_redis_connection():
        tests_passed += 1
    
    if test_welcome_package_lifecycle():
        tests_passed += 1
    
    if test_performance():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Welcome Package system ready for production.")
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Please check Redis configuration.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()