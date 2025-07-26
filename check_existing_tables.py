#!/usr/bin/env python3
"""
Check existing tables in RDS database
"""
import asyncio
import asyncpg
from modules.core.config import get_database_config

async def check_tables():
    config = get_database_config()
    
    # Connect to database
    conn = await asyncpg.connect(
        host=config['host'],
        database=config['database'],
        user=config['user'],
        password=config['password'],
        port=config['port']
    )
    
    try:
        # Get all tables in public schema
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        print("=== EXISTING TABLES IN DATABASE ===")
        print(f"Database: {config['database']} on {config['host']}")
        print(f"Total tables: {len(tables)}")
        print("\nTables:")
        
        chat_related = []
        llm_related = []
        
        for table in tables:
            table_name = table['table_name']
            print(f"  - {table_name}")
            
            # Check for chat/message related tables
            if 'chat' in table_name.lower() or 'message' in table_name.lower():
                chat_related.append(table_name)
            
            # Check for LLM related tables
            if 'llm' in table_name.lower() or 'usage' in table_name.lower():
                llm_related.append(table_name)
        
        print("\n=== ANALYSIS ===")
        
        # Check for chat_messages specifically
        chat_messages_exists = any(t['table_name'] == 'chat_messages' for t in tables)
        print(f"\nchat_messages table exists: {'YES' if chat_messages_exists else 'NO'}")
        
        if chat_related:
            print(f"\nChat/Message related tables found:")
            for t in chat_related:
                print(f"  - {t}")
        
        if llm_related:
            print(f"\nLLM/Usage related tables found:")
            for t in llm_related:
                print(f"  - {t}")
        
        # Check for alternative message storage tables
        possible_chat_tables = ['messages', 'conversation_messages', 'whatsapp_messages', 'farmer_messages']
        alternatives_found = []
        
        for table in tables:
            if table['table_name'] in possible_chat_tables:
                alternatives_found.append(table['table_name'])
        
        if alternatives_found:
            print(f"\nPossible alternative message tables:")
            for t in alternatives_found:
                print(f"  - {t}")
        
        # If chat_messages doesn't exist, check what might be the actual table
        if not chat_messages_exists:
            print("\n⚠️  chat_messages table NOT FOUND")
            
            # Look for columns that might indicate message storage
            for table in chat_related + alternatives_found:
                print(f"\nChecking columns in '{table}':")
                columns = await conn.fetch("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = $1 
                    ORDER BY ordinal_position;
                """, table)
                
                for col in columns[:10]:  # Show first 10 columns
                    print(f"    - {col['column_name']} ({col['data_type']})")
                
                if len(columns) > 10:
                    print(f"    ... and {len(columns) - 10} more columns")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_tables())