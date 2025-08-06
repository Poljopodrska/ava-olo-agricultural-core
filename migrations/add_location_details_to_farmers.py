#!/usr/bin/env python3
"""
Migration to add house_number and country columns to farmers table
Version: v4.14.0
Date: 2025-01-06
"""
import psycopg2
import os
from datetime import datetime

def get_connection():
    """Get database connection from central config"""
    # Import from shared central config
    import sys
    sys.path.append('C:\\AVA-Projects\\ava-olo-shared')
    from environments.central_config import CentralConfig
    
    return psycopg2.connect(
        host=CentralConfig.DB_HOST,
        database=CentralConfig.DB_NAME,
        user=CentralConfig.DB_USER,
        password=CentralConfig.DB_PASSWORD,
        port=CentralConfig.DB_PORT
    )

def run_migration():
    """Add house_number and country columns to farmers table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("Starting migration: Adding location detail columns to farmers table")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Add missing address columns
        columns_to_add = [
            ("house_number", "VARCHAR(20)"),
            ("country", "VARCHAR(100)"),
            ("location_prompt_shown", "BOOLEAN DEFAULT FALSE"),
            ("location_updated_at", "TIMESTAMP")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE farmers 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                """)
                print(f"✓ Added column: {column_name}")
            except Exception as e:
                print(f"ℹ Column {column_name} might already exist: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show current schema for location-related columns
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'farmers'
            AND column_name IN ('street_address', 'house_number', 'postal_code', 'city', 'country',
                              'weather_latitude', 'weather_longitude', 
                              'weather_location_name', 'address_collected', 
                              'location_prompt_shown', 'location_updated_at')
            ORDER BY ordinal_position
        """)
        
        print("\nLocation-related columns in farmers table:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}" + (f"({row[2]})" if row[2] else ""))
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()