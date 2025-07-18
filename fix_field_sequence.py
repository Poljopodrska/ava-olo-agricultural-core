#!/usr/bin/env python3
"""
Fix the fields table ID sequence to prevent duplicate key errors
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
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', '5432')),
            sslmode='require'
        )
        yield connection
    except psycopg2.OperationalError:
        # Try connecting to postgres database
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database='postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', '5432')),
            sslmode='require'
        )
        yield connection
    finally:
        if connection:
            connection.close()

def check_and_fix_sequence():
    """Check and fix the fields table sequence"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check current max ID
        cursor.execute("SELECT MAX(id) FROM fields")
        max_id = cursor.fetchone()[0]
        print(f"Current max ID in fields table: {max_id}")
        
        # Check if there's a sequence
        cursor.execute("""
            SELECT c.relname 
            FROM pg_class c 
            WHERE c.relkind = 'S' 
            AND c.relname LIKE '%fields%'
        """)
        sequences = cursor.fetchall()
        print(f"Found sequences: {sequences}")
        
        if sequences:
            # Try to reset the sequence
            seq_name = sequences[0][0]
            print(f"Resetting sequence {seq_name}")
            cursor.execute(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM fields), 0) + 1, false)")
            conn.commit()
            print("✅ Sequence reset successfully")
        else:
            print("⚠️ No sequence found - fields table might not have auto-increment")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'fields'
                AND column_name = 'id'
            """)
            id_info = cursor.fetchone()
            print(f"ID column info: {id_info}")

if __name__ == "__main__":
    check_and_fix_sequence()