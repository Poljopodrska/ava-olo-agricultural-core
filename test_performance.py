#!/usr/bin/env python3
"""Performance testing for monitoring dashboards"""

import time
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def time_operation(operation_name, func):
    """Time an operation and print results"""
    print(f"\n🔍 Testing: {operation_name}")
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        print(f"✅ Success in {elapsed:.2f}s")
        return result, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Failed after {elapsed:.2f}s: {str(e)}")
        return None, elapsed

def test_basic_connection():
    """Test basic database connection"""
    db_config = {
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'farmer_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
        'port': os.getenv('DB_PORT', '5432'),
        'connect_timeout': 5  # 5 second timeout
    }
    
    conn = psycopg2.connect(**db_config)
    conn.close()
    return "Connected"

def test_simple_query():
    """Test a simple SELECT 1 query"""
    db_config = {
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'farmer_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
        'port': os.getenv('DB_PORT', '5432'),
        'connect_timeout': 5
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def test_farmer_count():
    """Test farmer count query"""
    db_config = {
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'farmer_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
        'port': os.getenv('DB_PORT', '5432'),
        'connect_timeout': 5
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM farmers")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return f"{count} farmers"

def test_dashboard_query():
    """Test full dashboard query"""
    db_config = {
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'farmer_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
        'port': os.getenv('DB_PORT', '5432'),
        'connect_timeout': 5
    }
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Total farmers
    cursor.execute("SELECT COUNT(*) FROM farmers")
    farmers = cursor.fetchone()[0]
    
    # Total hectares
    cursor.execute("SELECT COALESCE(SUM(size_hectares), 0) FROM fields")
    hectares = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return f"{farmers} farmers, {hectares} hectares"

def check_connection_pooling():
    """Check if connection pooling would help"""
    print("\n🔄 Testing repeated connections vs reusing connection:")
    
    db_config = {
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'farmer_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
        'port': os.getenv('DB_PORT', '5432'),
        'connect_timeout': 5
    }
    
    # Test 1: New connection each time
    start = time.time()
    for i in range(5):
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
    new_conn_time = time.time() - start
    print(f"  5 queries with new connections: {new_conn_time:.2f}s")
    
    # Test 2: Reuse connection
    start = time.time()
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    for i in range(5):
        cursor.execute("SELECT 1")
        cursor.fetchone()
    cursor.close()
    conn.close()
    reuse_time = time.time() - start
    print(f"  5 queries reusing connection: {reuse_time:.2f}s")
    
    print(f"  💡 Speedup with connection reuse: {new_conn_time/reuse_time:.1f}x faster")

def main():
    print("🚀 AVA OLO Monitoring Dashboards - Performance Test")
    print("=" * 60)
    
    # Run tests
    time_operation("Basic Connection", test_basic_connection)
    time_operation("Simple Query (SELECT 1)", test_simple_query)
    time_operation("Farmer Count Query", test_farmer_count)
    time_operation("Full Dashboard Query", test_dashboard_query)
    
    # Connection pooling test
    check_connection_pooling()
    
    print("\n📊 Summary:")
    print("If connection takes >1s, the issue is likely:")
    print("  - Network latency to RDS")
    print("  - RDS instance cold start")
    print("  - Security group/VPC configuration")
    print("\nRecommendations:")
    print("  - Implement connection pooling")
    print("  - Use persistent connections")
    print("  - Add caching for dashboard metrics")

if __name__ == "__main__":
    main()