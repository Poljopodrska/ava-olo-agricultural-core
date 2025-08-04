#!/usr/bin/env python3
"""
Run database migrations during deployment
This script is executed by the container during startup
"""
import os
import sys
import logging
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

def run_task_management_migration():
    """Run the task management tables migration"""
    db_manager = get_db_manager()
    
    try:
        logger.info("Starting task management migration...")
        
        # Read migration file
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'migrations',
            'create_task_management_tables.sql'
        )
        
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        logger.info("Executing task management tables migration...")
        result = db_manager.execute_query(migration_sql)
        
        if result:
            logger.info("Task management migration completed successfully!")
            
            # Verify tables were created
            verify_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('materials', 'task_templates', 'tasks', 'task_fields', 
                                  'task_materials', 'field_history', 'crop_varieties')
            """
            verify_result = db_manager.execute_query(verify_query)
            
            if verify_result and 'rows' in verify_result:
                logger.info(f"Created/verified {len(verify_result['rows'])} task management tables")
                for row in verify_result['rows']:
                    logger.info(f"  - {row[0]}")
            
            return True
        else:
            logger.error("Migration execution returned no result")
            return False
            
    except Exception as e:
        logger.error(f"Error running task management migration: {e}")
        return False

def main():
    """Main migration runner"""
    # Wait for database to be ready
    logger.info("Waiting for database to be ready...")
    db_manager = get_db_manager()
    
    retries = 10
    while retries > 0:
        if db_manager.test_connection():
            logger.info("Database connection successful")
            break
        retries -= 1
        logger.info(f"Database not ready, retrying... ({retries} attempts left)")
        time.sleep(5)
    
    if retries == 0:
        logger.error("Failed to connect to database after multiple attempts")
        sys.exit(1)
    
    # Run migrations
    migrations_success = True
    
    # Run task management migration
    if not run_task_management_migration():
        logger.error("Task management migration failed")
        migrations_success = False
    
    if migrations_success:
        logger.info("All migrations completed successfully!")
    else:
        logger.error("Some migrations failed")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()