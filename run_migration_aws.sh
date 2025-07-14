#!/bin/bash
# AWS App Runner migration script
# Run this from the App Runner console or via SSH

echo "🏛️ RUNNING AURORA AUTHENTICATION MIGRATION"
echo "========================================"

# Direct psql command with proper escaping
PGPASSWORD='2hpzvrg_xP~qNbz1[_NppSK$e*O1' psql \
  -h farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d farmer_crm \
  -p 5432 \
  -c "
-- Create farm_users table
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

-- Create farm_activity_log table
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

-- Create default admin user
INSERT INTO farm_users (
    farmer_id, wa_phone_number, password_hash, 
    user_name, role, is_active
) VALUES (
    1, '+1234567890', 
    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGv1sm7N1yO',
    'Farm Owner', 'owner', true
) ON CONFLICT (wa_phone_number) DO NOTHING;
"

echo "✅ Migration completed!"
echo "Default user created:"
echo "  Phone: +1234567890"
echo "  Password: farm1"