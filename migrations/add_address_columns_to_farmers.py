#!/usr/bin/env python3
"""
Migration to add address columns to farmers table
"""
import psycopg2
import os
from datetime import datetime

def get_connection():
    """Get database connection"""
    db_host = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'j2D8J4LH:~eFrUz>$:kkNT(P$Rq_')
    
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=5432
    )

def run_migration():
    """Add address columns to farmers table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("Starting migration: Adding address columns to farmers table")
        
        # Add address columns
        columns_to_add = [
            ("city", "VARCHAR(100)"),
            ("street_address", "VARCHAR(255)"),
            ("postal_code", "VARCHAR(20)"),
            ("weather_latitude", "DECIMAL(10, 8)"),
            ("weather_longitude", "DECIMAL(11, 8)"),
            ("weather_location_name", "VARCHAR(255)"),
            ("vat_number", "VARCHAR(50)"),
            ("address_collected", "BOOLEAN DEFAULT FALSE")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE farmers 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                """)
                print(f"✓ Added column: {column_name}")
            except Exception as e:
                print(f"✗ Error adding column {column_name}: {e}")
        
        # Update existing farmers to set address_collected = false
        cursor.execute("""
            UPDATE farmers 
            SET address_collected = FALSE 
            WHERE address_collected IS NULL
        """)
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show current schema
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'farmers'
            AND column_name IN ('city', 'street_address', 'postal_code', 
                              'weather_latitude', 'weather_longitude', 
                              'weather_location_name', 'vat_number', 'address_collected')
            ORDER BY ordinal_position
        """)
        
        print("\nAdded columns:")
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