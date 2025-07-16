#!/usr/bin/env python3
"""
Check Farmers Table Schema and Add GPS Columns
Quick script to inspect farmers table and add GPS enhancement
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def check_farmers_table():
    """Check farmers table structure and add GPS columns if needed"""
    
    # Database connection
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'farmer_crm'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '2hpzvrg_xP~qNbz1[_NppSK$e*O1'),
        port=os.getenv('DB_PORT', '5432')
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("🔍 Checking farmers table structure...")
            
            # Check current columns
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'farmers'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            print(f"📊 Current farmers table columns ({len(columns)} total):")
            
            gps_columns_exist = False
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
                if col['column_name'] in ['latitude', 'longitude']:
                    gps_columns_exist = True
            
            if not gps_columns_exist:
                print("\n📍 Adding GPS columns to farmers table...")
                
                # Add GPS coordinate columns
                cur.execute("""
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,8);
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS longitude DECIMAL(11,8);
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS gps_source VARCHAR(50) DEFAULT 'geocoded';
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS location_accuracy INTEGER;
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP;
                """)
                
                conn.commit()
                print("✅ GPS columns added successfully")
            else:
                print("✅ GPS columns already exist")
            
            # Check farmer location data
            cur.execute("""
                SELECT 
                    COUNT(*) as total_farmers,
                    COUNT(latitude) as farmers_with_gps,
                    COUNT(CASE WHEN street_and_no IS NOT NULL AND village IS NOT NULL THEN 1 END) as complete_address,
                    COUNT(CASE WHEN city IS NOT NULL AND country IS NOT NULL THEN 1 END) as city_country,
                    COUNT(CASE WHEN country IS NOT NULL THEN 1 END) as has_country
                FROM farmers;
            """)
            
            stats = cur.fetchone()
            print(f"\n📈 Farmer Location Statistics:")
            print(f"  Total farmers: {stats['total_farmers']}")
            print(f"  Farmers with GPS: {stats['farmers_with_gps']}")
            print(f"  Complete addresses: {stats['complete_address']}")
            print(f"  City + Country: {stats['city_country']}")
            print(f"  Has country: {stats['has_country']}")
            
            # Show some sample farmer data
            cur.execute("""
                SELECT id, farm_name, manager_name, street_and_no, village, city, country, latitude, longitude
                FROM farmers
                ORDER BY id
                LIMIT 5;
            """)
            
            samples = cur.fetchall()
            print(f"\n📋 Sample farmer data:")
            for farmer in samples:
                print(f"  ID {farmer['id']}: {farmer['farm_name']} - {farmer['city']}, {farmer['country']} | GPS: {farmer['latitude']}, {farmer['longitude']}")
            
            # Check for Bulgarian farmers (MANGO RULE)
            cur.execute("""
                SELECT id, farm_name, manager_name, city, country, latitude, longitude
                FROM farmers
                WHERE country ILIKE '%bulgar%' OR country = 'BG'
                ORDER BY id;
            """)
            
            bulgarian_farmers = cur.fetchall()
            print(f"\n🥭 Bulgarian farmers (MANGO RULE): {len(bulgarian_farmers)} found")
            for farmer in bulgarian_farmers:
                gps_status = "✅ Has GPS" if farmer['latitude'] else "❌ Needs GPS"
                print(f"  ID {farmer['id']}: {farmer['farm_name']} - {farmer['city']} | {gps_status}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    success = check_farmers_table()
    exit(0 if success else 1)