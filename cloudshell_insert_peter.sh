#!/bin/bash
# Script to run in AWS CloudShell to insert Peter's data

echo "🌾 AWS CloudShell - Insert Peter Knaflič Data"
echo "============================================="

# Get RDS endpoint from environment or set it here
RDS_ENDPOINT="farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
RDS_PORT="5432"
RDS_DATABASE="farmer_crm"
RDS_USER="postgres"

# You'll need to provide the password when prompted
echo "📋 Database details:"
echo "   Host: $RDS_ENDPOINT"
echo "   Database: $RDS_DATABASE"
echo "   User: $RDS_USER"
echo ""

# Create SQL file
cat > /tmp/peter_farmer.sql << 'EOF'
-- Create Peter Knaflič's farmer account

-- 1. Create or update farmer record
INSERT INTO farmers (
    name, 
    wa_phone_number, 
    location, 
    farm_size_hectares, 
    farm_name,
    latitude, 
    longitude,
    created_at, 
    last_message_at
) VALUES (
    'Peter Knaflič',
    '+38641348050',
    'Pavšičeva 18, 1370 Logatec, Slovenia',
    28.0,
    'Knaflič Farm',
    45.9144,
    14.2242,
    NOW(),
    NOW()
) 
ON CONFLICT (wa_phone_number) 
DO UPDATE SET 
    name = EXCLUDED.name,
    location = EXCLUDED.location,
    farm_size_hectares = EXCLUDED.farm_size_hectares,
    farm_name = EXCLUDED.farm_name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    last_message_at = NOW()
RETURNING id;

-- 2. Create user account with bcrypt hashed password
INSERT INTO farm_users (
    farmer_id,
    wa_phone_number,
    password_hash,
    user_name,
    role,
    is_active,
    created_at
) VALUES (
    (SELECT id FROM farmers WHERE wa_phone_number = '+38641348050'),
    '+38641348050',
    '$2b$12$KxwgM8Gh2I5NGDKpEOLFXuXE7jV1B5YzH.xVxxfAU8kYvzxf5.Wjy',
    'Peter Knaflič',
    'owner',
    true,
    NOW()
)
ON CONFLICT (wa_phone_number) 
DO UPDATE SET 
    password_hash = EXCLUDED.password_hash,
    user_name = EXCLUDED.user_name,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active;

-- 3. Create fields
WITH farmer AS (
    SELECT id FROM farmers WHERE wa_phone_number = '+38641348050'
)
INSERT INTO fields (farmer_id, field_name, size_hectares, location, created_at) 
SELECT 
    farmer.id,
    field.name,
    field.size,
    field.location,
    NOW()
FROM farmer,
(VALUES 
    ('Skirca', 1.0, 'Skirca, Logatec'),
    ('Kalce', 2.0, 'Kalce, Logatec'),
    ('Javornik', 25.0, 'Javornik, Logatec')
) AS field(name, size, location)
ON CONFLICT (farmer_id, field_name) 
DO UPDATE SET 
    size_hectares = EXCLUDED.size_hectares,
    location = EXCLUDED.location;

-- 4. Verify the data was created
SELECT 
    f.id as farmer_id,
    f.name as farmer_name,
    f.wa_phone_number,
    f.farm_name,
    fu.id as user_id,
    fu.user_name,
    fu.role,
    fu.is_active
FROM farmers f
JOIN farm_users fu ON f.id = fu.farmer_id
WHERE f.wa_phone_number = '+38641348050';
EOF

echo "✅ SQL file created at /tmp/peter_farmer.sql"
echo ""
echo "🔐 You'll need to enter the RDS password when prompted."
echo "   The password contains special characters including brackets []"
echo ""
echo "📝 Running SQL commands..."

# Run psql command
# Note: You'll be prompted for the password
psql -h "$RDS_ENDPOINT" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DATABASE" -f /tmp/peter_farmer.sql

echo ""
echo "✅ Done! If successful, you can now login at:"
echo "   https://3ksdvgdtad.us-east-1.awsapprunner.com/login"
echo "   WhatsApp: +38641348050"
echo "   Password: Viognier"