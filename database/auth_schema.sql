-- AVA OLO Farm Authentication Schema Updates for Aurora RDS
-- This adds authentication tables to the EXISTING Aurora database
-- Constitutional compliance: MANGO Rule, Privacy-First, Multi-User Support

-- ====================================================================
-- PHASE 1: NEW AUTHENTICATION TABLES
-- ====================================================================

-- Multi-user farm access table
CREATE TABLE IF NOT EXISTS farm_users (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) NOT NULL,
    wa_phone_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_name VARCHAR(100) NOT NULL,  -- "Marko", "Ivo (Son)", etc.
    role VARCHAR(50) DEFAULT 'member',  -- 'owner', 'member', 'worker'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    created_by_user_id INTEGER REFERENCES farm_users(id)
);

-- Index for fast WA number lookups
CREATE INDEX IF NOT EXISTS idx_farm_users_wa_phone ON farm_users(wa_phone_number);
CREATE INDEX IF NOT EXISTS idx_farm_users_farmer_id ON farm_users(farmer_id);

-- Comprehensive family activity tracking (who did what)
CREATE TABLE IF NOT EXISTS farm_activity_log (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) NOT NULL,
    user_id INTEGER REFERENCES farm_users(id) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'deleted'
    table_name VARCHAR(50) NOT NULL,   -- 'tasks', 'inventory', etc.
    record_id INTEGER,                 -- ID of the record changed
    old_values JSONB,                  -- What it was before
    new_values JSONB,                  -- What it became  
    description TEXT,                  -- Human readable description
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_log_farmer ON farm_activity_log(farmer_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_user ON farm_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON farm_activity_log(timestamp);

-- ====================================================================
-- PHASE 2: ADD AUDIT FIELDS TO EXISTING TABLES
-- ====================================================================

-- Tasks table audit fields (only add if columns don't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='created_by_user_id') THEN
        ALTER TABLE tasks ADD COLUMN created_by_user_id INTEGER REFERENCES farm_users(id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='modified_by_user_id') THEN
        ALTER TABLE tasks ADD COLUMN modified_by_user_id INTEGER REFERENCES farm_users(id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='tasks' AND column_name='modified_at') THEN
        ALTER TABLE tasks ADD COLUMN modified_at TIMESTAMP;
    END IF;
END $$;

-- Field crops table audit fields
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='field_crops' AND column_name='created_by_user_id') THEN
        ALTER TABLE field_crops ADD COLUMN created_by_user_id INTEGER REFERENCES farm_users(id);
    END IF;
END $$;

-- Incoming messages (track who sent what)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='incoming_messages' AND column_name='farm_user_id') THEN
        ALTER TABLE incoming_messages ADD COLUMN farm_user_id INTEGER REFERENCES farm_users(id);
    END IF;
END $$;

-- Recommendations table audit fields
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='recommendations' AND column_name='created_by_user_id') THEN
        ALTER TABLE recommendations ADD COLUMN created_by_user_id INTEGER REFERENCES farm_users(id);
    END IF;
END $$;

-- ====================================================================
-- PHASE 3: CREATE INVENTORY TABLE WITH AUDIT SUPPORT (if needed)
-- ====================================================================

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    item_type VARCHAR(50),  -- 'seed', 'fertilizer', 'pesticide', 'equipment', etc.
    quantity DECIMAL(10, 2),
    unit VARCHAR(20),  -- 'kg', 'liters', 'bags', etc.
    location VARCHAR(100),
    purchase_date DATE,
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES farm_users(id),
    modified_by_user_id INTEGER REFERENCES farm_users(id),
    modified_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_farmer ON inventory(farmer_id);
CREATE INDEX IF NOT EXISTS idx_inventory_type ON inventory(item_type);

-- ====================================================================
-- PHASE 4: CREATE GROWTH STAGE REPORTS TABLE (if needed)
-- ====================================================================

CREATE TABLE IF NOT EXISTS growth_stage_reports (
    id SERIAL PRIMARY KEY,
    field_crop_id INTEGER REFERENCES field_crops(id) NOT NULL,
    growth_stage VARCHAR(50),  -- 'germination', 'vegetative', 'flowering', 'fruiting', 'harvest'
    observation_date DATE NOT NULL,
    notes TEXT,
    photos_url TEXT,  -- URL to photos stored elsewhere
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES farm_users(id)
);

CREATE INDEX IF NOT EXISTS idx_growth_reports_crop ON growth_stage_reports(field_crop_id);

-- ====================================================================
-- PHASE 5: CREATE FIELD SOIL DATA TABLE (if needed)
-- ====================================================================

CREATE TABLE IF NOT EXISTS field_soil_data (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(field_id) NOT NULL,
    test_date DATE NOT NULL,
    ph_level DECIMAL(3, 1),
    nitrogen_ppm DECIMAL(8, 2),
    phosphorus_ppm DECIMAL(8, 2),
    potassium_ppm DECIMAL(8, 2),
    organic_matter_percent DECIMAL(5, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES farm_users(id)
);

CREATE INDEX IF NOT EXISTS idx_soil_data_field ON field_soil_data(field_id);

-- ====================================================================
-- PHASE 6: ADD UPDATE TRIGGERS FOR MODIFIED_AT COLUMNS
-- ====================================================================

CREATE OR REPLACE FUNCTION update_modified_columns()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    -- Note: modified_by_user_id should be set by the application
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to tables with modified_at columns
DROP TRIGGER IF EXISTS update_tasks_modified ON tasks;
CREATE TRIGGER update_tasks_modified 
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_modified_columns();

DROP TRIGGER IF EXISTS update_inventory_modified ON inventory;
CREATE TRIGGER update_inventory_modified 
    BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_modified_columns();

-- ====================================================================
-- PHASE 7: AUTHENTICATION SUPPORT FUNCTIONS
-- ====================================================================

-- Function to get all family members for a farm
CREATE OR REPLACE FUNCTION get_farm_family(p_farmer_id INTEGER)
RETURNS TABLE (
    user_id INTEGER,
    user_name VARCHAR(100),
    role VARCHAR(50),
    wa_phone_number VARCHAR(20),
    is_active BOOLEAN,
    last_login TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fu.id,
        fu.user_name,
        fu.role,
        fu.wa_phone_number,
        fu.is_active,
        fu.last_login
    FROM farm_users fu
    WHERE fu.farmer_id = p_farmer_id
    ORDER BY 
        CASE fu.role 
            WHEN 'owner' THEN 1 
            WHEN 'member' THEN 2 
            WHEN 'worker' THEN 3 
            ELSE 4 
        END,
        fu.created_at;
END;
$$ LANGUAGE plpgsql;

-- Function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity(
    p_farmer_id INTEGER,
    p_user_id INTEGER,
    p_action_type VARCHAR(50),
    p_table_name VARCHAR(50),
    p_record_id INTEGER,
    p_description TEXT,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL
) RETURNS void AS $$
BEGIN
    INSERT INTO farm_activity_log (
        farmer_id, user_id, action_type, table_name, 
        record_id, description, old_values, new_values
    ) VALUES (
        p_farmer_id, p_user_id, p_action_type, p_table_name,
        p_record_id, p_description, p_old_values, p_new_values
    );
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- PHASE 8: SAMPLE DATA FOR TESTING
-- ====================================================================

-- Note: Only run this in development/testing environments
-- DO $$ 
-- BEGIN
--     -- Add sample farm owner user for testing
--     IF NOT EXISTS (SELECT 1 FROM farm_users WHERE wa_phone_number = '+1234567890') THEN
--         INSERT INTO farm_users (farmer_id, wa_phone_number, password_hash, user_name, role)
--         VALUES (
--             1, 
--             '+1234567890', 
--             '$2b$12$sample.hash.for.testing', -- Password: 'test123'
--             'Test Farm Owner',
--             'owner'
--         );
--     END IF;
-- END $$;

-- ====================================================================
-- PHASE 9: CONSTITUTIONAL COMPLIANCE COMMENT
-- ====================================================================

COMMENT ON TABLE farm_users IS 'Multi-user authentication for AVA OLO farms - Constitutional compliance with MANGO Rule, Privacy-First';
COMMENT ON TABLE farm_activity_log IS 'Complete audit trail for family farm activities - prevents conflicts, maintains transparency';