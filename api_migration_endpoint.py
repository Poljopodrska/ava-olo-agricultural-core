"""
Special migration endpoint for Aurora authentication tables
Temporary endpoint with hardcoded credentials to run migration
"""
from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.post("/migrate-auth-aurora")
async def migrate_auth_tables():
    """Run Aurora migration with hardcoded credentials"""
    try:
        # Hardcoded credentials to avoid environment variable issues
        conn = psycopg2.connect(
            host='farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
            database='farmer_crm',
            user='postgres',
            password='2hpzvrg_xP~qNbz1[_NppSK$e*O1',
            port=5432,
            connect_timeout=30,
            sslmode='prefer',
            cursor_factory=RealDictCursor
        )
        
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('farm_users', 'farm_activity_log')
            """)
            existing_tables = [row['table_name'] for row in cur.fetchall()]
            
            if 'farm_users' in existing_tables and 'farm_activity_log' in existing_tables:
                return {
                    "success": True,
                    "message": "Tables already exist",
                    "existing_tables": existing_tables
                }
            
            # Create tables
            cur.execute("""
                -- Create farm_users table for multi-user authentication
                CREATE TABLE IF NOT EXISTS farm_users (
                    id SERIAL PRIMARY KEY,
                    farmer_id INTEGER REFERENCES farmers(id) NOT NULL,
                    wa_phone_number VARCHAR(20) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    user_name VARCHAR(100) NOT NULL,
                    role VARCHAR(50) DEFAULT 'member',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    created_by_user_id INTEGER REFERENCES farm_users(id)
                );

                -- Create farm_activity_log for audit trail
                CREATE TABLE IF NOT EXISTS farm_activity_log (
                    id SERIAL PRIMARY KEY,
                    farmer_id INTEGER REFERENCES farmers(id) NOT NULL,
                    user_id INTEGER REFERENCES farm_users(id) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    details JSONB,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_farm_users_farmer_id ON farm_users(farmer_id);
                CREATE INDEX IF NOT EXISTS idx_farm_users_phone ON farm_users(wa_phone_number);
                CREATE INDEX IF NOT EXISTS idx_farm_activity_farmer_id ON farm_activity_log(farmer_id);
                CREATE INDEX IF NOT EXISTS idx_farm_activity_user_id ON farm_activity_log(user_id);
                CREATE INDEX IF NOT EXISTS idx_farm_activity_created_at ON farm_activity_log(created_at);
            """)
            
            # Create default admin user
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
            
            new_user = cur.fetchone()
            conn.commit()
            
            return {
                "success": True,
                "message": "Migration completed successfully",
                "tables_created": ["farm_users", "farm_activity_log"],
                "default_user_created": bool(new_user),
                "default_credentials": {
                    "phone": "+1234567890",
                    "password": "farm1"
                }
            }
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)