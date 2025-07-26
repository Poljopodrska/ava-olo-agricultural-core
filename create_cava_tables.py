#!/usr/bin/env python3
"""
Create CAVA required tables in RDS database
According to DATABASE_SCHEMA.md and CAVA implementation
"""
import psycopg2
from modules.core.config import get_database_config

def create_tables():
    config = get_database_config()
    
    # Connect to database
    conn = psycopg2.connect(
        host=config['host'],
        database=config['database'],
        user=config['user'],
        password=config['password'],
        port=config['port']
    )
    
    try:
        with conn.cursor() as cursor:
            # First check what tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('chat_messages', 'llm_usage_log')
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"Existing CAVA tables: {existing_tables}")
            
            # Create chat_messages table as per DATABASE_SCHEMA.md
            if 'chat_messages' not in existing_tables:
                print("Creating chat_messages table...")
                cursor.execute("""
                    CREATE TABLE chat_messages (
                        id SERIAL PRIMARY KEY,
                        wa_phone_number VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Add indexes for performance
                    CREATE INDEX idx_chat_messages_phone ON chat_messages(wa_phone_number);
                    CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
                    CREATE INDEX idx_chat_messages_role ON chat_messages(role);
                """)
                print("✅ chat_messages table created")
            else:
                print("✓ chat_messages table already exists")
                
                # Check if it has the correct columns
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'chat_messages'
                """)
                columns = [row[0] for row in cursor.fetchall()]
                print(f"  Columns: {columns}")
                
                # Check if we need to add missing columns
                required_columns = ['id', 'wa_phone_number', 'role', 'content', 'timestamp']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"  ⚠️  Missing columns: {missing_columns}")
                    # Handle column name differences
                    if 'role' not in columns and 'direction' in columns:
                        print("  Converting 'direction' column to 'role'...")
                        cursor.execute("ALTER TABLE chat_messages RENAME COLUMN direction TO role;")
                    
                    if 'content' not in columns and 'message_content' in columns:
                        print("  Converting 'message_content' column to 'content'...")
                        cursor.execute("ALTER TABLE chat_messages RENAME COLUMN message_content TO content;")
                    
                    if 'timestamp' not in columns and 'created_at' in columns:
                        print("  Converting 'created_at' column to 'timestamp'...")
                        cursor.execute("ALTER TABLE chat_messages RENAME COLUMN created_at TO timestamp;")
            
            # Create llm_usage_log table for cost tracking
            if 'llm_usage_log' not in existing_tables:
                print("\nCreating llm_usage_log table...")
                cursor.execute("""
                    CREATE TABLE llm_usage_log (
                        id SERIAL PRIMARY KEY,
                        farmer_phone VARCHAR(20),
                        model VARCHAR(50),
                        tokens_in INTEGER,
                        tokens_out INTEGER,
                        cost DECIMAL(10,6),
                        timestamp TIMESTAMP DEFAULT NOW()
                    );
                    
                    CREATE INDEX idx_llm_usage_phone ON llm_usage_log(farmer_phone);
                    CREATE INDEX idx_llm_usage_timestamp ON llm_usage_log(timestamp);
                """)
                print("✅ llm_usage_log table created")
            else:
                print("✓ llm_usage_log table already exists")
            
            # Commit changes
            conn.commit()
            
            print("\n=== CAVA Tables Setup Complete ===")
            
            # Show current status
            cursor.execute("""
                SELECT 
                    'chat_messages' as table_name,
                    COUNT(*) as row_count
                FROM chat_messages
                UNION ALL
                SELECT 
                    'llm_usage_log' as table_name,
                    COUNT(*) as row_count
                FROM llm_usage_log
            """)
            
            print("\nTable status:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} rows")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
        raise
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()