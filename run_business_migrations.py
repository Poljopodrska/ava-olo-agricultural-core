#!/usr/bin/env python3
"""
Run migrations for business dashboard
Adds timestamp columns needed for metrics tracking
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MIGRATION_SQL = """
-- Add timestamp columns for business metrics tracking
-- Constitutional: Privacy-first, only track creation time not user behavior

-- Add created_at to farmers table if missing
ALTER TABLE farmers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- Add created_at to fields table if missing  
ALTER TABLE fields ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- Add created_at to tasks table if missing
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- Optional: Add status tracking for farmers (for churn analysis)
-- Only add if you want to track active/inactive status
-- ALTER TABLE farmers ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
-- ALTER TABLE farmers ADD COLUMN IF NOT EXISTS unsubscribed_at TIMESTAMP NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_farmers_created_at ON farmers(created_at);
CREATE INDEX IF NOT EXISTS idx_fields_created_at ON fields(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_incoming_messages_timestamp ON incoming_messages(timestamp);

-- Update existing records to have reasonable created_at values
-- This sets created_at based on ID order (earlier IDs = earlier dates)
UPDATE farmers 
SET created_at = NOW() - (INTERVAL '1 day' * (
    SELECT MAX(id) - id + 1 FROM farmers f2 WHERE f2.id = farmers.id
))
WHERE created_at IS NULL;

UPDATE fields 
SET created_at = NOW() - (INTERVAL '1 day' * (
    SELECT MAX(id) - id + 1 FROM fields f2 WHERE f2.id = fields.id
))
WHERE created_at IS NULL;

UPDATE tasks 
SET created_at = NOW() - (INTERVAL '1 day' * (
    SELECT MAX(id) - id + 1 FROM tasks t2 WHERE t2.id = tasks.id
))
WHERE created_at IS NULL;
"""

def run_migration():
    """Run the migration"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', '5432'))
        )
        
        cursor = conn.cursor()
        
        print("🔄 Running business dashboard migrations...")
        
        # Execute migration
        cursor.execute(MIGRATION_SQL)
        
        # Check what was added
        cursor.execute("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE column_name = 'created_at' 
            AND table_name IN ('farmers', 'fields', 'tasks')
            ORDER BY table_name
        """)
        
        print("\n✅ Timestamp columns verified:")
        for table, column in cursor.fetchall():
            print(f"   - {table}.{column}")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE indexname LIKE 'idx_%_created_at'
        """)
        
        print("\n✅ Indexes created:")
        for (index_name,) in cursor.fetchall():
            print(f"   - {index_name}")
        
        conn.commit()
        print("\n🎉 Migration completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("📊 AVA OLO Business Dashboard Migration Tool")
    print("=" * 50)
    
    if run_migration():
        print("\n✨ Your database is now ready for the business dashboard!")
        print("   Run: python run_business_dashboard.py")
    else:
        print("\n⚠️ Please fix the errors and try again.")