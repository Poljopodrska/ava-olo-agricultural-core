#!/usr/bin/env python3
"""
Migration to add authentication columns to farmers table
Adds password_hash and is_active columns for farmer authentication
"""
import os
import asyncio
import asyncpg
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

async def run_migration():
    """Run the migration to add authentication columns"""
    
    if not DB_CONFIG['password']:
        print("❌ DB_PASSWORD environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**DB_CONFIG)
        print(f"✅ Connected to database: {DB_CONFIG['host']}")
        
        # Check if columns already exist
        column_check = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'farmers' 
            AND column_name IN ('password_hash', 'is_active')
        """)
        
        if column_check >= 2:
            print("ℹ️ Authentication columns already exist in farmers table")
            await conn.close()
            return True
        
        # Add password_hash column if not exists
        try:
            await conn.execute("""
                ALTER TABLE farmers 
                ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
            """)
            print("✅ Added password_hash column")
        except Exception as e:
            print(f"⚠️ Failed to add password_hash column: {e}")
        
        # Add is_active column if not exists
        try:
            await conn.execute("""
                ALTER TABLE farmers 
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true
            """)
            print("✅ Added is_active column")
        except Exception as e:
            print(f"⚠️ Failed to add is_active column: {e}")
        
        # Add created_at column if not exists
        try:
            await conn.execute("""
                ALTER TABLE farmers 
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            print("✅ Added created_at column")
        except Exception as e:
            print(f"⚠️ Failed to add created_at column: {e}")
        
        # Add name column (for compatibility with auth routes) if not exists
        try:
            # Check if name column exists
            name_exists = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'farmers' 
                AND column_name = 'name'
            """)
            
            if name_exists == 0:
                # Create name column as computed from manager_name and manager_last_name
                await conn.execute("""
                    ALTER TABLE farmers 
                    ADD COLUMN IF NOT EXISTS name VARCHAR(255) 
                    GENERATED ALWAYS AS (
                        COALESCE(manager_name, '') || 
                        CASE 
                            WHEN manager_name IS NOT NULL AND manager_last_name IS NOT NULL THEN ' ' 
                            ELSE '' 
                        END || 
                        COALESCE(manager_last_name, '')
                    ) STORED
                """)
                print("✅ Added name column as computed column")
        except Exception as e:
            print(f"⚠️ Failed to add name column: {e}")
        
        # Add whatsapp_number column (alias for wa_phone_number) if not exists
        try:
            # Check if whatsapp_number column exists
            wa_exists = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'farmers' 
                AND column_name = 'whatsapp_number'
            """)
            
            if wa_exists == 0:
                # Create whatsapp_number as an alias
                await conn.execute("""
                    ALTER TABLE farmers 
                    ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20)
                """)
                
                # Copy existing wa_phone_number data
                await conn.execute("""
                    UPDATE farmers 
                    SET whatsapp_number = wa_phone_number 
                    WHERE whatsapp_number IS NULL AND wa_phone_number IS NOT NULL
                """)
                
                print("✅ Added whatsapp_number column")
        except Exception as e:
            print(f"⚠️ Failed to add whatsapp_number column: {e}")
        
        # Create index on whatsapp_number for faster lookups
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_farmers_whatsapp_number 
                ON farmers(whatsapp_number)
            """)
            print("✅ Created index on whatsapp_number")
        except Exception as e:
            print(f"⚠️ Failed to create index: {e}")
        
        # Verify migration
        final_check = await conn.fetchrow("""
            SELECT 
                COUNT(*) FILTER (WHERE column_name = 'password_hash') as has_password_hash,
                COUNT(*) FILTER (WHERE column_name = 'is_active') as has_is_active,
                COUNT(*) FILTER (WHERE column_name = 'created_at') as has_created_at,
                COUNT(*) FILTER (WHERE column_name = 'name') as has_name,
                COUNT(*) FILTER (WHERE column_name = 'whatsapp_number') as has_whatsapp_number
            FROM information_schema.columns 
            WHERE table_name = 'farmers'
        """)
        
        print("\n📊 Migration Summary:")
        print(f"   password_hash column: {'✅' if final_check['has_password_hash'] else '❌'}")
        print(f"   is_active column: {'✅' if final_check['has_is_active'] else '❌'}")
        print(f"   created_at column: {'✅' if final_check['has_created_at'] else '❌'}")
        print(f"   name column: {'✅' if final_check['has_name'] else '❌'}")
        print(f"   whatsapp_number column: {'✅' if final_check['has_whatsapp_number'] else '❌'}")
        
        await conn.close()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    # Run migration
    result = asyncio.run(run_migration())
    exit(0 if result else 1)