#!/usr/bin/env python3
"""
Migration script to add authentication tables to Aurora RDS
Runs the authentication schema migration safely

Constitutional compliance: Production-Safe, Transparency-First
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_manager import config
from implementation.farm_auth import FarmAuthManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthMigrator:
    """
    Safe migration of authentication tables to Aurora RDS
    
    Follows the same connection pattern as monitoring dashboards
    """
    
    def __init__(self):
        self.db_config = {
            'host': config.db_host,
            'database': config.db_name,
            'user': config.db_user,
            'password': config.db_password,
            'port': config.db_port
        }
        self.connection = None
        
    def connect(self):
        """Connect to Aurora RDS (same method as dashboards)"""
        ssl_modes = ['require', 'prefer', 'disable']
        
        for ssl_mode in ssl_modes:
            try:
                logger.info(f"Attempting connection with SSL mode: {ssl_mode}")
                self.connection = psycopg2.connect(
                    host=self.db_config['host'],
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    port=self.db_config['port'],
                    connect_timeout=30,
                    sslmode=ssl_mode,
                    cursor_factory=RealDictCursor
                )
                logger.info(f"✅ Connected to Aurora with SSL mode: {ssl_mode}")
                return True
                
            except psycopg2.OperationalError as e:
                if "SSL" in str(e) or "ssl" in str(e):
                    logger.warning(f"SSL mode {ssl_mode} failed, trying next...")
                    continue
                else:
                    raise e
                    
        raise Exception("Failed to connect to Aurora RDS with all SSL modes")
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Disconnected from Aurora RDS")
    
    def check_prerequisites(self) -> bool:
        """Check if migration can proceed safely"""
        logger.info("🔍 Checking migration prerequisites...")
        
        cursor = self.connection.cursor()
        
        # Check if farmers table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'farmers'
            );
        """)
        
        farmers_exists = cursor.fetchone()[0]
        if not farmers_exists:
            logger.error("❌ Prerequisites failed: 'farmers' table not found")
            return False
        
        logger.info("✅ Prerequisites check passed")
        return True
    
    def check_existing_tables(self) -> Dict[str, bool]:
        """Check which authentication tables already exist"""
        logger.info("🔍 Checking existing authentication tables...")
        
        cursor = self.connection.cursor()
        
        auth_tables = ['farm_users', 'farm_activity_log', 'inventory', 'growth_stage_reports', 'field_soil_data']
        existing_tables = {}
        
        for table in auth_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
            """)
            
            exists = cursor.fetchone()[0]
            existing_tables[table] = exists
            
            if exists:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"⚠️  Table '{table}' already exists with {count} rows")
            else:
                logger.info(f"✅ Table '{table}' does not exist - safe to create")
        
        return existing_tables
    
    def backup_existing_data(self):
        """Create backup of existing data before migration"""
        logger.info("💾 Creating backup of existing data...")
        
        cursor = self.connection.cursor()
        
        # Create backup schema
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS auth_migration_backup;
        """)
        
        # Backup existing auth tables if they exist
        auth_tables = ['farm_users', 'farm_activity_log']
        
        for table in auth_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
            """)
            
            if cursor.fetchone()[0]:
                backup_table = f"{table}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"📋 Backing up {table} to {backup_table}")
                
                cursor.execute(f"""
                    CREATE TABLE auth_migration_backup.{backup_table} AS 
                    SELECT * FROM {table};
                """)
        
        self.connection.commit()
        logger.info("✅ Backup completed")
    
    def run_migration(self) -> bool:
        """Run the authentication schema migration"""
        logger.info("🚀 Starting authentication schema migration...")
        
        try:
            cursor = self.connection.cursor()
            
            # Read the migration SQL
            migration_file = Path(__file__).parent.parent / "database" / "auth_schema.sql"
            
            if not migration_file.exists():
                logger.error(f"❌ Migration file not found: {migration_file}")
                return False
            
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration in a transaction
            cursor.execute("BEGIN;")
            logger.info("📋 Executing migration SQL...")
            
            # Split SQL into individual statements and execute
            statements = migration_sql.split(';')
            
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        logger.debug(f"Executed statement {i+1}/{len(statements)}")
                    except Exception as e:
                        logger.error(f"Error in statement {i+1}: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
                        raise
            
            cursor.execute("COMMIT;")
            logger.info("✅ Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            cursor.execute("ROLLBACK;")
            logger.info("🔄 Migration rolled back")
            return False
    
    def verify_migration(self) -> bool:
        """Verify that migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        cursor = self.connection.cursor()
        
        # Check that all required tables exist
        required_tables = ['farm_users', 'farm_activity_log']
        
        for table in required_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
            """)
            
            if not cursor.fetchone()[0]:
                logger.error(f"❌ Verification failed: Table '{table}' not found")
                return False
        
        # Check that functions exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.routines
                WHERE routine_schema = 'public'
                AND routine_name = 'get_farm_family'
            );
        """)
        
        if not cursor.fetchone()[0]:
            logger.error("❌ Verification failed: Function 'get_farm_family' not found")
            return False
        
        logger.info("✅ Migration verification passed")
        return True
    
    def migrate_existing_farmers(self) -> bool:
        """Migrate existing farmers to the new authentication system"""
        logger.info("👥 Migrating existing farmers to authentication system...")
        
        cursor = self.connection.cursor()
        
        # Get existing farmers with WhatsApp numbers
        cursor.execute("""
            SELECT id, wa_phone_number, manager_name, farm_name
            FROM farmers 
            WHERE wa_phone_number IS NOT NULL 
            AND wa_phone_number != ''
            AND id NOT IN (
                SELECT farmer_id FROM farm_users WHERE farmer_id IS NOT NULL
            )
        """)
        
        farmers = cursor.fetchall()
        logger.info(f"Found {len(farmers)} farmers to migrate")
        
        if not farmers:
            logger.info("No farmers to migrate")
            return True
        
        # Create FarmAuthManager for registration
        auth_manager = FarmAuthManager(self.db_config)
        
        migrated_count = 0
        
        for farmer in farmers:
            try:
                # Generate temporary password
                temp_password = f"farm{farmer['id']}"
                
                # Register farmer as owner
                auth_manager.register_farm_user(
                    farmer_id=farmer['id'],
                    wa_phone=farmer['wa_phone_number'],
                    password=temp_password,
                    user_name=farmer['manager_name'] or f"Farm Owner {farmer['id']}",
                    role='owner'
                )
                
                migrated_count += 1
                logger.info(f"✅ Migrated: {farmer['manager_name']} ({farmer['wa_phone_number']}) - temp password: {temp_password}")
                
            except Exception as e:
                logger.error(f"❌ Failed to migrate farmer {farmer['id']}: {e}")
        
        logger.info(f"✅ Successfully migrated {migrated_count}/{len(farmers)} farmers")
        return True
    
    def full_migration(self) -> bool:
        """Run complete migration process"""
        logger.info("🏛️ Starting AVA OLO Authentication Migration")
        logger.info("=" * 60)
        
        try:
            # Connect to Aurora
            if not self.connect():
                logger.error("❌ Failed to connect to Aurora RDS")
                return False
            
            # Check prerequisites
            if not self.check_prerequisites():
                logger.error("❌ Prerequisites check failed")
                return False
            
            # Check existing tables
            existing_tables = self.check_existing_tables()
            
            # Create backup
            self.backup_existing_data()
            
            # Run migration
            if not self.run_migration():
                logger.error("❌ Migration failed")
                return False
            
            # Verify migration
            if not self.verify_migration():
                logger.error("❌ Migration verification failed")
                return False
            
            # Migrate existing farmers
            if not self.migrate_existing_farmers():
                logger.error("❌ Farmer migration failed")
                return False
            
            logger.info("✅ Authentication migration completed successfully!")
            logger.info("🔐 Farmers can now login with their WhatsApp numbers")
            logger.info("📋 Check migration logs for temporary passwords")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed with error: {e}")
            return False
            
        finally:
            self.disconnect()


def main():
    """Main migration function"""
    migrator = AuthMigrator()
    
    # Run migration
    success = migrator.full_migration()
    
    if success:
        print("\n🎉 MIGRATION SUCCESSFUL!")
        print("Authentication system is now ready for use.")
        print("Deploy the agricultural core with authentication enabled.")
    else:
        print("\n💥 MIGRATION FAILED!")
        print("Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()