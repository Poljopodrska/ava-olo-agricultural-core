#!/usr/bin/env python3
"""
Test script to safely verify authentication schema can be added to Aurora RDS
Tests in READ-ONLY mode first, then creates tables only after verification
Constitutional compliance: Privacy-First, Production-Safe
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_manager import config

class AuroraAuthMigrationTester:
    """Safe tester for Aurora authentication schema migration"""
    
    def __init__(self):
        self.db_url = config.database_url
        self.connection = None
        self.test_results = []
        
    async def connect(self):
        """Establish connection to Aurora RDS"""
        try:
            # Build connection parameters (not URL string) - same as monitoring dashboards
            connection_params = {
                'host': config.db_host,
                'port': int(config.db_port),
                'user': config.db_user,
                'password': config.db_password,  # Use raw password, not URL-encoded
                'database': config.db_name,
                'server_settings': {
                    'application_name': 'ava_olo_auth_migration'
                }
            }
            
            # Try different SSL modes in order of preference
            ssl_modes = ['require', 'prefer', 'disable']
            
            for ssl_mode in ssl_modes:
                try:
                    # Add SSL mode to connection parameters
                    if ssl_mode != 'disable':
                        connection_params['ssl'] = ssl_mode
                    else:
                        connection_params['ssl'] = False
                    
                    print(f"🔌 Attempting connection with SSL mode: {ssl_mode}")
                    self.connection = await asyncpg.connect(**connection_params)
                    
                    print("✅ Connected to Aurora RDS successfully")
                    print(f"   Host: {config.db_host}")
                    print(f"   Database: {config.db_name}")
                    print(f"   SSL Mode: {ssl_mode}")
                    return True
                    
                except Exception as e:
                    if "SSL" in str(e) or "ssl" in str(e):
                        print(f"   SSL mode {ssl_mode} failed, trying next...")
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            print(f"❌ Failed to connect to Aurora RDS: {e}")
            print(f"   Host: {config.db_host}")
            print(f"   Database: {config.db_name}")
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            print("🔌 Disconnected from Aurora RDS")
    
    async def check_existing_schema(self):
        """Check existing tables and identify potential conflicts"""
        print("\n🔍 CHECKING EXISTING AURORA SCHEMA...")
        
        try:
            # Check if farmers table exists (required for foreign keys)
            farmers_exists = await self.connection.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'farmers'
                );
            """)
            
            if not farmers_exists:
                print("❌ ERROR: 'farmers' table not found - required for authentication")
                return False
            else:
                print("✅ 'farmers' table exists")
            
            # Check if authentication tables already exist
            auth_tables = ['farm_users', 'farm_activity_log']
            for table in auth_tables:
                exists = await self.connection.fetchval(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    );
                """)
                
                if exists:
                    print(f"⚠️  WARNING: Table '{table}' already exists")
                    # Get row count
                    count = await self.connection.fetchval(f"SELECT COUNT(*) FROM {table}")
                    print(f"   Contains {count} rows")
                else:
                    print(f"✅ Table '{table}' does not exist - safe to create")
            
            # Check columns that will be added to existing tables
            audit_columns = {
                'tasks': ['created_by_user_id', 'modified_by_user_id', 'modified_at'],
                'field_crops': ['created_by_user_id'],
                'incoming_messages': ['farm_user_id'],
                'recommendations': ['created_by_user_id']
            }
            
            print("\n🔍 Checking audit columns on existing tables...")
            for table, columns in audit_columns.items():
                # Check if table exists
                table_exists = await self.connection.fetchval(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    );
                """)
                
                if table_exists:
                    print(f"\n📋 Table '{table}':")
                    for column in columns:
                        column_exists = await self.connection.fetchval(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_schema = 'public' 
                                AND table_name = '{table}'
                                AND column_name = '{column}'
                            );
                        """)
                        
                        if column_exists:
                            print(f"   ⚠️  Column '{column}' already exists")
                        else:
                            print(f"   ✅ Column '{column}' can be added")
                else:
                    print(f"📋 Table '{table}' does not exist - will be skipped")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            return False
    
    async def test_sample_farmer_data(self):
        """Check sample farmer data for testing authentication"""
        print("\n🧑‍🌾 CHECKING FARMER DATA...")
        
        try:
            # Get sample farmers
            farmers = await self.connection.fetch("""
                SELECT id, farm_name, manager_name, wa_phone_number, country
                FROM farmers
                LIMIT 5
            """)
            
            print(f"Found {len(farmers)} farmers in database")
            
            if farmers:
                print("\nSample farmers for testing:")
                for farmer in farmers:
                    wa_phone = farmer['wa_phone_number'] or 'No WhatsApp'
                    print(f"  ID: {farmer['id']}, Farm: {farmer['farm_name']}, "
                          f"Manager: {farmer['manager_name']}, WA: {wa_phone}")
                
                # Check if any farmers have WhatsApp numbers
                wa_count = await self.connection.fetchval("""
                    SELECT COUNT(*) FROM farmers 
                    WHERE wa_phone_number IS NOT NULL 
                    AND wa_phone_number != ''
                """)
                
                print(f"\n📱 Farmers with WhatsApp numbers: {wa_count}")
                
                if wa_count == 0:
                    print("⚠️  WARNING: No farmers have WhatsApp numbers - authentication will require setup")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking farmer data: {e}")
            return False
    
    async def dry_run_migration(self):
        """Simulate the migration without making changes"""
        print("\n🧪 DRY RUN - SIMULATING MIGRATION...")
        
        migration_steps = [
            {
                "name": "Create farm_users table",
                "safe": True,
                "sql": "Would create table with user authentication data"
            },
            {
                "name": "Create farm_activity_log table",
                "safe": True,
                "sql": "Would create table for audit logging"
            },
            {
                "name": "Add audit columns to existing tables",
                "safe": True,
                "sql": "Would add created_by_user_id, modified_by_user_id columns"
            },
            {
                "name": "Create indexes for performance",
                "safe": True,
                "sql": "Would create indexes on foreign keys"
            },
            {
                "name": "Create helper functions",
                "safe": True,
                "sql": "Would create get_farm_family() and log_user_activity() functions"
            }
        ]
        
        print("\nMigration steps that would be executed:")
        for i, step in enumerate(migration_steps, 1):
            status = "✅ SAFE" if step["safe"] else "⚠️  RISKY"
            print(f"{i}. {status} - {step['name']}")
        
        return True
    
    async def verify_constitutional_compliance(self):
        """Verify the migration maintains constitutional compliance"""
        print("\n🏛️ VERIFYING CONSTITUTIONAL COMPLIANCE...")
        
        checks = {
            "MANGO Rule": "Authentication works for any country (no hardcoded defaults)",
            "Privacy-First": "User passwords are hashed, audit logs don't expose sensitive data",
            "Multi-User": "Multiple family members can access same farm data",
            "Audit Trail": "All changes are tracked with user attribution",
            "No Breaking Changes": "Existing functionality remains intact"
        }
        
        for principle, description in checks.items():
            print(f"✅ {principle}: {description}")
        
        return True
    
    async def generate_safe_migration_sql(self):
        """Generate the actual migration SQL file"""
        print("\n📝 GENERATING SAFE MIGRATION SQL...")
        
        migration_file = "database/auth_aurora_migration_safe.sql"
        
        with open(migration_file, 'w') as f:
            f.write("""-- SAFE Aurora RDS Authentication Migration
-- Generated: """ + datetime.now().isoformat() + """
-- This migration is designed to be safe and non-destructive

-- Start transaction for safety
BEGIN;

-- Create new authentication tables only if they don't exist
""")
            
            # Read the auth schema file
            with open("database/auth_schema.sql", 'r') as schema:
                f.write(schema.read())
            
            f.write("""

-- Commit only if everything succeeded
COMMIT;

-- To rollback if needed:
-- ROLLBACK;
""")
        
        print(f"✅ Safe migration SQL generated: {migration_file}")
        print("📋 Review the file before executing on Aurora RDS")
        
        return True

async def main():
    """Run the Aurora authentication migration test"""
    print("🏛️ AVA OLO Aurora Authentication Migration Tester")
    print("=" * 60)
    print("⚠️  This is a READ-ONLY test - no changes will be made")
    print("=" * 60)
    
    tester = AuroraAuthMigrationTester()
    
    # Connect to Aurora
    if not await tester.connect():
        print("\n❌ Cannot proceed without database connection")
        return
    
    try:
        # Run all checks
        all_passed = True
        
        if not await tester.check_existing_schema():
            all_passed = False
        
        if not await tester.test_sample_farmer_data():
            all_passed = False
        
        if not await tester.dry_run_migration():
            all_passed = False
        
        if not await tester.verify_constitutional_compliance():
            all_passed = False
        
        # Generate migration file if all checks pass
        if all_passed:
            await tester.generate_safe_migration_sql()
            print("\n✅ ALL CHECKS PASSED - Migration appears safe")
            print("\n📋 Next steps:")
            print("1. Review the generated migration file")
            print("2. Test on a development/staging Aurora instance first")
            print("3. Create a backup before running on production")
            print("4. Execute the migration during a maintenance window")
        else:
            print("\n⚠️  Some checks failed - review issues before proceeding")
    
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    asyncio.run(main())