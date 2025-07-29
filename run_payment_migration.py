#!/usr/bin/env python3
"""
Run payment migration to create Stripe payment tables
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

async def run_migration():
    """Run the payment migration"""
    print("Running Stripe payment migration...")
    
    # Read migration file
    with open('migrations/002_add_stripe_payments.sql', 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Execute migration
        await conn.execute(migration_sql)
        print("✅ Migration completed successfully!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('subscription_config', 'usage_tracking', 'payment_history', 'config_audit_log')
        """)
        
        print(f"\nCreated tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check if farmers table was updated
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farmers' 
            AND column_name IN ('stripe_customer_id', 'subscription_status', 'trial_end_date')
        """)
        
        print(f"\nAdded columns to farmers table:")
        for col in columns:
            print(f"  - {col['column_name']}")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())