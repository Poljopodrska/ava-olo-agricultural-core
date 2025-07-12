#!/usr/bin/env python3
"""Quick schema check for business dashboard debugging"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME', 'farmer_crm'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )
    cursor = conn.cursor()
    
    print("Connected to database successfully!")
    
    # Check farmers table columns
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'farmers'
        ORDER BY ordinal_position
    """)
    
    print("\nFarmers table columns:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    
    # Test basic queries that business dashboard uses
    print("\nTesting business dashboard queries:")
    
    # Test 1: Basic farmer count
    try:
        cursor.execute("SELECT COUNT(DISTINCT id) FROM farmers WHERE is_active = TRUE")
        result = cursor.fetchone()[0]
        print(f"✅ Active farmers count: {result}")
    except Exception as e:
        print(f"❌ Active farmers query failed: {e}")
    
    # Test 2: Check for created_at column
    try:
        cursor.execute("SELECT COUNT(*) FROM farmers WHERE created_at IS NOT NULL")
        result = cursor.fetchone()[0]
        print(f"✅ Farmers with created_at: {result}")
    except Exception as e:
        print(f"❌ created_at query failed: {e}")
    
    # Test 3: Check for is_active column
    try:
        cursor.execute("SELECT COUNT(*) FROM farmers WHERE is_active = FALSE")
        result = cursor.fetchone()[0]
        print(f"✅ Inactive farmers: {result}")
    except Exception as e:
        print(f"❌ is_active query failed: {e}")
    
    conn.close()
    
except Exception as e:
    print(f"Database connection failed: {e}")