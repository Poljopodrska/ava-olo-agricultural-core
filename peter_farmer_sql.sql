-- SQL Commands to create Peter Knaflič's farmer account
-- Run these commands in your AWS RDS PostgreSQL database

-- 1. First, create the farmer record
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

-- 2. Get the farmer_id from above query (let's assume it's 1 for now)
-- You'll need to replace [FARMER_ID] with the actual ID returned

-- 3. Create the user account with bcrypt hashed password
-- This is a bcrypt hash for 'Viognier' - generated with cost factor 12
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
    '$2b$12$KxwgM8Gh2I5NGDKpEOLFXuXE7jV1B5YzH.xVxxfAU8kYvzxf5.Wjy',  -- bcrypt hash of 'Viognier'
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

-- 4. Create the fields (optional)
-- First get the farmer_id
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

-- Verification query - run this to confirm everything worked
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