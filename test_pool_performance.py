#!/usr/bin/env python3
"""Test SQLAlchemy pool performance before deployment"""

import time
import os
from dotenv import load_dotenv

load_dotenv()

# Test imports
try:
    from database_pool import (
        init_connection_pool, get_db_session, get_db_connection,
        get_dashboard_metrics, get_database_schema, test_connection_pool
    )
    print("✅ SQLAlchemy pool module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import pool module: {e}")
    exit(1)

print("\n🧪 Testing SQLAlchemy Connection Pool Performance")
print("=" * 60)

# Test 1: Initialize pool
print("\n1. INITIALIZING CONNECTION POOL:")
start = time.time()
try:
    engine = init_connection_pool()
    print(f"   ✅ Pool initialized in {(time.time() - start)*1000:.0f}ms")
except Exception as e:
    print(f"   ❌ Pool initialization failed: {e}")
    exit(1)

# Test 2: Simple query performance
print("\n2. SIMPLE QUERY TEST (5 queries):")
for i in range(5):
    start = time.time()
    try:
        with get_db_session() as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            result.fetchone()
        elapsed = (time.time() - start) * 1000
        print(f"   Query {i+1}: {elapsed:.0f}ms")
    except Exception as e:
        print(f"   Query {i+1} failed: {e}")

# Test 3: Dashboard metrics
print("\n3. DASHBOARD METRICS TEST:")
start = time.time()
try:
    metrics = get_dashboard_metrics()
    print(f"   ✅ Metrics fetched in {metrics.get('query_time_ms', 0):.0f}ms")
    print(f"   - Total farmers: {metrics.get('total_farmers', 0)}")
    print(f"   - Total fields: {metrics.get('total_fields', 0)}")
    print(f"   - Total hectares: {metrics.get('total_hectares', 0):.1f}")
except Exception as e:
    print(f"   ❌ Metrics fetch failed: {e}")

# Test 4: Schema retrieval
print("\n4. DATABASE SCHEMA TEST:")
start = time.time()
try:
    schema = get_database_schema()
    elapsed = (time.time() - start) * 1000
    print(f"   ✅ Schema fetched in {elapsed:.0f}ms")
    print(f"   - Tables found: {len(schema)}")
    print(f"   - Sample tables: {', '.join(list(schema.keys())[:5])}")
except Exception as e:
    print(f"   ❌ Schema fetch failed: {e}")

# Test 5: Pool health
print("\n5. CONNECTION POOL HEALTH:")
try:
    health = test_connection_pool()
    print(f"   Pool initialized: {health.get('pool_initialized', False)}")
    print(f"   Pool size: {health.get('pool_size', 0)}")
    print(f"   Active connections: {health.get('pool_checked_out', 0)}")
    for test in health.get('tests', []):
        if test.get('success'):
            print(f"   ✅ {test['name']}: {test.get('time_ms', 'N/A')}ms")
        else:
            print(f"   ❌ {test['name']}: {test.get('error', 'Failed')}")
except Exception as e:
    print(f"   ❌ Pool health check failed: {e}")

# Summary
print("\n📊 PERFORMANCE SUMMARY:")
print("   Target: All queries <200ms")
print("   Result: Check times above")
print("\nIf all tests pass with <200ms times, the pool is ready for deployment!")