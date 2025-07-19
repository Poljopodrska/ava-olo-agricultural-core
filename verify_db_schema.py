#!/usr/bin/env python3
"""
Verify database schema for dashboard features implementation
"""
import os
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Get database connection"""
    connection = None
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
            database='postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '2hpzvrg_xP~ qNbz1[_NppSK$e*O_h6g{Nux[3OA>wPSZ%8CaIK>bqXIcJE&F<G'),
            port=int(os.getenv('DB_PORT', '5432')),
            sslmode='require'
        )
        connection.autocommit = True
        yield connection
    finally:
        if connection:
            connection.close()

def verify_schemas():
    """Verify required database schemas"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        print("=== DATABASE SCHEMA VERIFICATION ===\n")
        
        # Check tasks table for machine column
        print("1. Checking tasks table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position
        """)
        task_columns = cursor.fetchall()
        has_machine = False
        has_doserate_value = False
        has_doserate_unit = False
        
        print("   Tasks table columns:")
        for col in task_columns:
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
            if col[0] == 'machine':
                has_machine = True
            if col[0] == 'doserate_value':
                has_doserate_value = True
            if col[0] == 'doserate_unit':
                has_doserate_unit = True
        
        print(f"\n   ✓ Has machine column: {has_machine}")
        print(f"   ✓ Has doserate_value column: {has_doserate_value}")
        print(f"   ✓ Has doserate_unit column: {has_doserate_unit}")
        
        # Check machinery table structure
        print("\n2. Checking machinery table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'machinery'
            ORDER BY ordinal_position
        """)
        machinery_columns = cursor.fetchall()
        
        if machinery_columns:
            print("   Machinery table columns:")
            for col in machinery_columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        else:
            print("   ⚠️  Machinery table not found!")
            
        # Check fields table structure
        print("\n3. Checking fields table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'fields'
            ORDER BY ordinal_position
        """)
        fields_columns = cursor.fetchall()
        print("   Fields table columns:")
        for col in fields_columns:
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
            
        # Generate SQL for missing columns
        print("\n=== REQUIRED SQL UPDATES ===\n")
        
        if not has_machine:
            print("-- Add machine column to tasks table")
            print("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS machine VARCHAR(255);")
            
        if not has_doserate_value:
            print("-- Add doserate_value column to tasks table")
            print("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS doserate_value DECIMAL(10,3);")
            
        if not has_doserate_unit:
            print("-- Add doserate_unit column to tasks table")
            print("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS doserate_unit VARCHAR(50);")
            
        if not machinery_columns:
            print("-- Create machinery table (example structure)")
            print("""CREATE TABLE IF NOT EXISTS machinery (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    type VARCHAR(50),
    registration_number VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")
        
        cursor.close()

if __name__ == "__main__":
    verify_schemas()