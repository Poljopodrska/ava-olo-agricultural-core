#!/usr/bin/env python3
"""
Manual Aurora migration script for authentication tables
Run this directly to create the authentication tables
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct connection configuration
DB_CONFIG = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'farmer_crm',
    'user': 'postgres',
    'password': '2hpzvrg_xP~qNbz1[_NppSK$e*O1',
    'port': 5432
}

def run_migration():
    """Run the authentication migration"""
    logger.info("🚀 Starting Aurora authentication migration...")
    
    # Read the SQL schema
    with open('database/auth_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Try different SSL modes
    ssl_modes = ['require', 'prefer', 'disable']
    
    for ssl_mode in ssl_modes:
        try:
            logger.info(f"Attempting connection with SSL mode: {ssl_mode}")
            
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                port=DB_CONFIG['port'],
                connect_timeout=30,
                sslmode=ssl_mode,
                cursor_factory=RealDictCursor
            )
            
            logger.info("✅ Connected to Aurora RDS!")
            
            with conn.cursor() as cur:
                # Check if tables exist
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('farm_users', 'farm_activity_log')
                """)
                existing_tables = [row['table_name'] for row in cur.fetchall()]
                
                if 'farm_users' in existing_tables and 'farm_activity_log' in existing_tables:
                    logger.info("✅ Authentication tables already exist!")
                    
                    # Check if we have any users
                    cur.execute("SELECT COUNT(*) as count FROM farm_users")
                    user_count = cur.fetchone()['count']
                    logger.info(f"   Current users: {user_count}")
                    
                    return True
                
                # Run the migration
                logger.info("📦 Creating authentication tables...")
                cur.execute(schema_sql)
                conn.commit()
                
                logger.info("✅ Authentication tables created successfully!")
                
                # Create default admin user for farmer 1
                logger.info("👤 Creating default admin user...")
                cur.execute("""
                    INSERT INTO farm_users (
                        farmer_id, wa_phone_number, password_hash, 
                        user_name, role, is_active
                    ) VALUES (
                        1, '+1234567890', 
                        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGv1sm7N1yO',
                        'Farm Owner', 'owner', true
                    ) ON CONFLICT (wa_phone_number) DO NOTHING
                    RETURNING id
                """)
                
                result = cur.fetchone()
                if result:
                    logger.info(f"✅ Default admin user created with ID: {result['id']}")
                    logger.info("   Phone: +1234567890")
                    logger.info("   Password: farm1")
                else:
                    logger.info("ℹ️  Default admin user already exists")
                
                conn.commit()
                
            conn.close()
            logger.info("🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed with SSL mode {ssl_mode}: {str(e)}")
            continue
    
    logger.error("❌ All connection attempts failed!")
    return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🏛️ CONSTITUTIONAL FARM AUTHENTICATION MIGRATION")
    logger.info("=" * 60)
    
    success = run_migration()
    
    if success:
        logger.info("✅ MIGRATION SUCCESSFUL!")
        logger.info("You can now use the authentication system")
        sys.exit(0)
    else:
        logger.error("❌ MIGRATION FAILED!")
        logger.error("This script requires VPC access to Aurora RDS")
        logger.error("Please run from AWS App Runner or EC2 instance")
        sys.exit(1)