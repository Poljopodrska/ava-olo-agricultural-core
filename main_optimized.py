#!/usr/bin/env python3
# DEPLOYMENT TIMESTAMP: 1752936600 - v2.1.11-performance-fix
"""
AVA OLO Monitoring Dashboards Service - Performance Optimized
Main entry point with connection pooling and caching
"""

# ... [keeping all imports and initial setup the same until the connection function]

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import time
from functools import lru_cache

# Create a global connection pool
db_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,  # min 1, max 20 connections
            host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
            port=int(os.getenv('DB_PORT', '5432')),
            connect_timeout=3,  # Reduced from 10 to 3 seconds
            sslmode='require'
        )
        print("✅ Database connection pool initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize connection pool: {e}")
        return False

@contextmanager
def get_db_connection():
    """Get a connection from the pool"""
    global db_pool
    connection = None
    try:
        # Initialize pool if not already done
        if db_pool is None:
            init_db_pool()
        
        # Get connection from pool
        connection = db_pool.getconn()
        yield connection
    except Exception as e:
        print(f"Database connection error: {e}")
        yield None
    finally:
        if connection and db_pool:
            db_pool.putconn(connection)

# Cache for dashboard metrics (5 minute TTL)
@lru_cache(maxsize=1)
def get_cached_dashboard_metrics(cache_key: str):
    """Get cached dashboard metrics"""
    metrics = {
        "total_farmers": 0,
        "total_hectares": 0,
        "total_fields": 0,
        "last_updated": time.time()
    }
    
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            
            # Get all metrics in one query
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM farmers) as farmer_count,
                    (SELECT COUNT(*) FROM fields) as field_count,
                    (SELECT COALESCE(SUM(size_hectares), 0) FROM fields) as total_hectares
            """)
            
            result = cursor.fetchone()
            if result:
                metrics["total_farmers"] = result[0]
                metrics["total_fields"] = result[1]
                metrics["total_hectares"] = float(result[2])
            
            cursor.close()
    
    return metrics

# Clear cache every 5 minutes
def get_dashboard_metrics():
    """Get dashboard metrics with caching"""
    cache_key = f"metrics_{int(time.time() // 300)}"  # 5 minute buckets
    return get_cached_dashboard_metrics(cache_key)

# Fast health check endpoint
@app.get("/health/fast")
async def health_fast():
    """Quick health check without database"""
    return {
        "status": "healthy",
        "version": "v2.1.11-performance-fix",
        "timestamp": time.time()
    }

# Test endpoint for performance
@app.get("/test/performance")
async def test_performance():
    """Test database performance"""
    results = {}
    
    # Test 1: Connection from pool
    start = time.time()
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
    results["pool_connection_ms"] = int((time.time() - start) * 1000)
    
    # Test 2: Cached metrics
    start = time.time()
    metrics = get_dashboard_metrics()
    results["cached_metrics_ms"] = int((time.time() - start) * 1000)
    
    # Test 3: Direct query
    start = time.time()
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM farmers")
            cursor.fetchone()
            cursor.close()
    results["direct_query_ms"] = int((time.time() - start) * 1000)
    
    results["metrics"] = metrics
    results["pool_status"] = "active" if db_pool else "not initialized"
    
    return results

# Initialize the pool on startup
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    init_db_pool()
    # Pre-warm the cache
    get_dashboard_metrics()
    print("✅ Application startup complete")

# Close pool on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_pool
    if db_pool:
        db_pool.closeall()
        print("✅ Connection pool closed")