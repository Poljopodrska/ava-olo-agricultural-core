#!/usr/bin/env python3
"""Test database connection for monitoring dashboards"""

import os
import psycopg2
import time
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test database connection with credentials from environment"""
    
    # Get credentials
    db_config = {
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'farmer_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '<~Xzntr2r~m6-7)~4*MO(Mul>#YW'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print(f"Testing connection to {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        # Test connection
        start = time.time()
        conn = psycopg2.connect(**db_config)
        connect_time = time.time() - start
        print(f"✅ Connected successfully in {connect_time:.2f} seconds")
        
        # Test query
        cursor = conn.cursor()
        
        # Check farmers count
        cursor.execute("SELECT COUNT(*) FROM farmers")
        farmer_count = cursor.fetchone()[0]
        print(f"✅ Farmers in database: {farmer_count}")
        
        # Check fields count
        cursor.execute("SELECT COUNT(*) FROM fields")
        field_count = cursor.fetchone()[0]
        print(f"✅ Fields in database: {field_count}")
        
        # Check total hectares
        cursor.execute("SELECT COALESCE(SUM(size_hectares), 0) FROM fields")
        total_hectares = cursor.fetchone()[0]
        print(f"✅ Total hectares: {total_hectares}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\n📊 Available tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_connection()