#!/usr/bin/env python3
"""
Run migration to create standard_queries table
"""

import os
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Get database connection"""
    connection = None
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        print(f"Connecting to {host}:{port}/{database} as {user}")
        
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            connect_timeout=10,
            sslmode='require'
        )
        yield connection
    except Exception as e:
        print(f"Connection failed: {e}")
        yield None
    finally:
        if connection:
            connection.close()

def run_migration():
    """Run the migration to create standard_queries table"""
    with get_db_connection() as conn:
        if not conn:
            print("ERROR: Could not connect to database")
            return False
            
        cursor = conn.cursor()
        
        try:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'standard_queries'
                )
            """)
            
            if cursor.fetchone()[0]:
                print("Table 'standard_queries' already exists!")
                return True
                
            print("Creating standard_queries table...")
            
            # Create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS standard_queries (
                    id SERIAL PRIMARY KEY,
                    query_name VARCHAR(255) NOT NULL,
                    sql_query TEXT NOT NULL,
                    description TEXT,
                    natural_language_query TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
                    usage_count INTEGER DEFAULT 0,
                    is_global BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_standard_queries_farmer ON standard_queries(farmer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_standard_queries_usage ON standard_queries(usage_count DESC)")
            
            # Insert default queries
            cursor.execute("""
                INSERT INTO standard_queries (query_name, sql_query, description, natural_language_query, is_global) VALUES
                ('Total Farmers', 'SELECT COUNT(*) as farmer_count FROM farmers', 'Get total number of farmers', 'How many farmers do we have?', TRUE),
                ('All Fields', 'SELECT f.farm_name, fi.field_name, fi.area_ha FROM farmers f JOIN fields fi ON f.id = fi.farmer_id ORDER BY f.farm_name, fi.field_name', 'List all fields with farmer names', 'Show me all fields', TRUE),
                ('Recent Tasks', 'SELECT t.date_performed, f.farm_name, fi.field_name, t.task_type, t.description FROM tasks t JOIN task_fields tf ON t.id = tf.task_id JOIN fields fi ON tf.field_id = fi.id JOIN farmers f ON fi.farmer_id = f.id WHERE t.date_performed >= CURRENT_DATE - INTERVAL ''7 days'' ORDER BY t.date_performed DESC', 'Tasks performed in last 7 days', 'What happened in the last week?', TRUE)
            """)
            
            conn.commit()
            print("SUCCESS: Table created and default queries added!")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run migration
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")