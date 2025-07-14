#!/usr/bin/env python3
"""
Test direct Aurora connection for authentication migration
"""
import psycopg2
import sys
import os

# Production Aurora credentials
db_config = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'farmer_crm', 
    'user': 'postgres',
    'password': '2hpzvrg_xP~qNbz1[_NppSK$e*O1',
    'port': 5432
}

def test_connection():
    """Test Aurora connection"""
    print("🔍 Testing Aurora connection...")
    
    ssl_modes = ['require', 'prefer', 'disable']
    
    for ssl_mode in ssl_modes:
        try:
            print(f"   Trying SSL mode: {ssl_mode}")
            
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port'],
                connect_timeout=10,
                sslmode=ssl_mode
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                result = cur.fetchone()
                print(f"   ✅ Connected! PostgreSQL version: {result[0][:50]}...")
                
                # Test if authentication tables exist
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('farm_users', 'farm_activity_log')
                """)
                tables = cur.fetchall()
                print(f"   📊 Authentication tables found: {[t[0] for t in tables]}")
                
            conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ SSL mode {ssl_mode} failed: {str(e)}")
            continue
    
    print("❌ All connection attempts failed")
    return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)