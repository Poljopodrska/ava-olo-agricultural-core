#!/usr/bin/env python3
"""
Performance patch for main.py - apply these changes to fix slow loading
"""

# CHANGE 1: Add these imports at the top of main.py after existing imports
"""
from psycopg2 import pool
from functools import lru_cache
import time
"""

# CHANGE 2: Add this after imports, before the app = FastAPI() line
"""
# Global connection pool for performance
db_pool = None

def init_db_pool():
    \"\"\"Initialize database connection pool\"\"\"
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,  # min 1, max 10 connections
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', '5432')),
            connect_timeout=2,  # 2 seconds max
            sslmode='require'
        )
        logger.info("✅ Database connection pool initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Connection pool failed: {e}")
        return False
"""

# CHANGE 3: Replace the entire get_constitutional_db_connection() function with:
"""
@contextmanager
def get_constitutional_db_connection():
    \"\"\"Get connection from pool for fast access\"\"\"
    global db_pool
    connection = None
    
    try:
        # Initialize pool if needed
        if db_pool is None:
            init_db_pool()
        
        if db_pool:
            # Get from pool (fast!)
            connection = db_pool.getconn()
        else:
            # Fallback to direct connection
            connection = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME', 'farmer_crm'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=int(os.getenv('DB_PORT', '5432')),
                connect_timeout=2,
                sslmode='require'
            )
        
        yield connection
        
    except Exception as e:
        logger.error(f"Connection error: {e}")
        yield None
    finally:
        if connection and db_pool:
            db_pool.putconn(connection)  # Return to pool
        elif connection:
            connection.close()  # Close if no pool
"""

# CHANGE 4: Add caching for dashboard metrics
"""
# Cache dashboard metrics for 1 minute
dashboard_cache = {
    'data': None,
    'timestamp': 0
}

def get_cached_dashboard_metrics():
    \"\"\"Get dashboard metrics with 1-minute cache\"\"\"
    global dashboard_cache
    
    # Check if cache is valid (less than 60 seconds old)
    if dashboard_cache['data'] and (time.time() - dashboard_cache['timestamp'] < 60):
        return dashboard_cache['data']
    
    # Fetch fresh data
    metrics = {
        "total_farmers": 0,
        "total_hectares": 0,
        "total_fields": 0
    }
    
    with get_constitutional_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            # Single query for all metrics
            cursor.execute(\"\"\"
                SELECT 
                    (SELECT COUNT(*) FROM farmers) as farmers,
                    (SELECT COUNT(*) FROM fields) as fields,
                    (SELECT COALESCE(SUM(size_hectares), 0) FROM fields) as hectares
            \"\"\")
            result = cursor.fetchone()
            if result:
                metrics["total_farmers"] = result[0]
                metrics["total_fields"] = result[1]
                metrics["total_hectares"] = float(result[2])
            cursor.close()
    
    # Update cache
    dashboard_cache['data'] = metrics
    dashboard_cache['timestamp'] = time.time()
    
    return metrics
"""

# CHANGE 5: Add app startup/shutdown events
"""
@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize resources on startup\"\"\"
    init_db_pool()
    logger.info("🚀 Application started with connection pool")

@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"Cleanup on shutdown\"\"\"
    global db_pool
    if db_pool:
        db_pool.closeall()
        logger.info("✅ Connection pool closed")
"""

# CHANGE 6: Update the /register-farmer endpoint to test performance
"""
# Add this simple test endpoint
@app.get("/test/speed")
async def test_speed():
    \"\"\"Quick performance test\"\"\"
    start = time.time()
    
    with get_constitutional_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
    elapsed = time.time() - start
    return {
        "query_time_ms": int(elapsed * 1000),
        "status": "fast" if elapsed < 0.1 else "slow"
    }
"""