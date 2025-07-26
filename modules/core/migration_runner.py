#!/usr/bin/env python3
"""
Migration Runner for CAVA System
Handles database migrations on application startup
"""
import os
import logging
import psycopg2
from typing import List, Dict
from modules.core.config import get_database_config

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles database migration execution"""
    
    def __init__(self):
        self.config = get_database_config()
        self.migrations_dir = "migrations"
    
    def run_migrations(self) -> Dict[str, any]:
        """
        Run all pending migrations
        Returns status information
        """
        try:
            logger.info("🔄 Starting database migrations...")
            
            # Get list of migration files
            migration_files = self._get_migration_files()
            
            if not migration_files:
                logger.info("✅ No migration files found")
                return {"success": True, "migrations_run": 0, "message": "No migrations to run"}
            
            # Connect to database
            conn = psycopg2.connect(
                host=self.config['host'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                port=self.config['port']
            )
            
            try:
                # Ensure migration tracking table exists
                self._ensure_migration_table(conn)
                
                # Get already applied migrations
                applied_migrations = self._get_applied_migrations(conn)
                
                # Run pending migrations
                migrations_run = 0
                for migration_file in migration_files:
                    version = self._extract_version(migration_file)
                    
                    if version not in applied_migrations:
                        logger.info(f"🔄 Running migration: {migration_file}")
                        self._run_migration_file(conn, migration_file)
                        migrations_run += 1
                        logger.info(f"✅ Completed migration: {migration_file}")
                    else:
                        logger.info(f"⏭️  Skipping already applied migration: {migration_file}")
                
                conn.commit()
                
                logger.info(f"✅ Database migrations completed. {migrations_run} migrations applied.")
                return {
                    "success": True, 
                    "migrations_run": migrations_run,
                    "total_migrations": len(migration_files),
                    "message": f"Successfully applied {migrations_run} migrations"
                }
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            return {
                "success": False, 
                "error": str(e),
                "message": f"Migration failed: {str(e)}"
            }
    
    def _get_migration_files(self) -> List[str]:
        """Get sorted list of migration files"""
        if not os.path.exists(self.migrations_dir):
            return []
        
        files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        return sorted(files)
    
    def _extract_version(self, filename: str) -> str:
        """Extract version number from migration filename"""
        # Extract version from filename like "001_create_tables.sql"
        return filename.split('_')[0]
    
    def _ensure_migration_table(self, conn):
        """Ensure schema_migrations table exists"""
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT NOW(),
                    description TEXT
                )
            """)
    
    def _get_applied_migrations(self, conn) -> set:
        """Get set of already applied migration versions"""
        with conn.cursor() as cursor:
            cursor.execute("SELECT version FROM schema_migrations")
            return {row[0] for row in cursor.fetchall()}
    
    def _run_migration_file(self, conn, filename: str):
        """Execute a single migration file"""
        migration_path = os.path.join(self.migrations_dir, filename)
        
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        with conn.cursor() as cursor:
            # Execute the migration SQL
            cursor.execute(migration_sql)

def run_startup_migrations() -> Dict[str, any]:
    """
    Convenience function to run migrations on application startup
    """
    runner = MigrationRunner()
    return runner.run_migrations()