#!/usr/bin/env python3
"""Test performance improvements locally before deploying"""

import time
import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv()

# Test configuration
db_config = {
    'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'farmer_crm'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
    'port': os.getenv('DB_PORT', '5432')
}

print("🧪 Testing Performance Improvements")
print("=" * 60)

# Test 1: Current implementation (multiple connection attempts)
print("\n1. CURRENT IMPLEMENTATION (10s timeout, 3 strategies):")
start = time.time()
try:
    # Try SSL required
    conn = psycopg2.connect(**db_config, connect_timeout=10, sslmode='require')
    conn.close()
    print(f"   ✅ Connected in {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ❌ Failed after {time.time() - start:.2f}s")

# Test 2: Optimized single connection
print("\n2. OPTIMIZED (2s timeout, direct connection):")
start = time.time()
try:
    conn = psycopg2.connect(**db_config, connect_timeout=2, sslmode='require')
    conn.close()
    print(f"   ✅ Connected in {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ❌ Failed after {time.time() - start:.2f}s: {e}")

# Test 3: Connection pool
print("\n3. CONNECTION POOL:")
try:
    start = time.time()
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 5,
        **db_config,
        connect_timeout=2,
        sslmode='require'
    )
    print(f"   ✅ Pool created in {time.time() - start:.2f}s")
    
    # Test getting connections from pool
    print("   Testing pool performance:")
    for i in range(3):
        start = time.time()
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        db_pool.putconn(conn)
        print(f"   Query {i+1}: {(time.time() - start)*1000:.0f}ms")
    
    db_pool.closeall()
except Exception as e:
    print(f"   ❌ Pool failed: {e}")

# Test 4: Dashboard query performance
print("\n4. DASHBOARD QUERY PERFORMANCE:")
try:
    conn = psycopg2.connect(**db_config, connect_timeout=2, sslmode='require')
    cursor = conn.cursor()
    
    # Test individual queries
    queries = [
        ("Farmer count", "SELECT COUNT(*) FROM farmers"),
        ("Field count", "SELECT COUNT(*) FROM fields"),
        ("Total hectares", "SELECT COALESCE(SUM(size_hectares), 0) FROM fields"),
    ]
    
    for name, query in queries:
        start = time.time()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        elapsed = (time.time() - start) * 1000
        print(f"   {name}: {result} ({elapsed:.0f}ms)")
    
    # Test combined query
    start = time.time()
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM farmers) as farmers,
            (SELECT COUNT(*) FROM fields) as fields,
            (SELECT COALESCE(SUM(size_hectares), 0) FROM fields) as hectares
    """)
    result = cursor.fetchone()
    elapsed = (time.time() - start) * 1000
    print(f"   Combined query: {elapsed:.0f}ms")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ❌ Query test failed: {e}")

print("\n📊 RECOMMENDATIONS:")
print("- If connection takes >1s, implement connection pooling")
print("- If queries are slow, add database indexes")
print("- Cache dashboard metrics for 60 seconds")
print("- Use 2-3 second timeout instead of 10")