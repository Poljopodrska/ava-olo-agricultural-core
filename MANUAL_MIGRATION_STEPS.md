# Manual Aurora Migration Steps

Since the automatic migration is having password issues, here are manual steps to create the authentication tables:

## Option 1: Using AWS Console (Recommended)

1. **Go to AWS RDS Console**
   - Find your Aurora database: `farmer-crm-production`
   - Click on "Query Editor" or "Connect"

2. **Run this SQL:**

```sql
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
-- Password is 'farm1' (bcrypt hash)
INSERT INTO farm_users (
    farmer_id, wa_phone_number, password_hash, 
    user_name, role, is_active
) VALUES (
    1, '+1234567890', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGv1sm7N1yO',
    'Farm Owner', 'owner', true
) ON CONFLICT (wa_phone_number) DO NOTHING;

-- Check if everything was created
SELECT 'farm_users' as table_name, COUNT(*) as record_count FROM farm_users
UNION ALL
SELECT 'farm_activity_log', COUNT(*) FROM farm_activity_log;
```

## Option 2: Using pgAdmin or DBeaver

1. **Connect to Aurora using:**
   - Host: `farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com`
   - Port: `5432`
   - Database: `farmer_crm`
   - Username: `postgres`
   - Password: `2hpzvrg_xP~qNbz1[_NppSK$e*O1`

2. **Run the SQL above**

## Option 3: Using Bastion Host (if available)

If you have a bastion host set up:

```bash
# SSH to bastion
ssh -i your-key.pem ec2-user@bastion-ip

# Connect to Aurora
PGPASSWORD='2hpzvrg_xP~qNbz1[_NppSK$e*O1' psql \
  -h farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d farmer_crm \
  -p 5432
```

Then paste the SQL commands.

## Default Login Credentials

After running the migration, you can login with:
- **Phone**: `+1234567890`
- **Password**: `farm1`

## Verify It Worked

Test login at:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"wa_phone_number": "+1234567890", "password": "farm1"}' \
  https://3ksdvgdtad.us-east-1.awsapprunner.com/api/v1/auth/login
```

You should get a JWT token back!