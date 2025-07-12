-- AVA OLO Agricultural Assistant Database Schema - Constitutional Version
-- 100% MANGO RULE Compliant - No hardcoded country/language defaults

-- Farmers table - Universal agricultural users
CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    state_farm_number VARCHAR(50) UNIQUE,  -- Government registration (any country)
    farm_name VARCHAR(100),
    manager_name VARCHAR(50),
    manager_last_name VARCHAR(50),
    street_and_no VARCHAR(100),
    village VARCHAR(100),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country VARCHAR(50),  -- NO DEFAULT - detected via Amendment #13
    country_code VARCHAR(3),  -- ISO country code from WhatsApp
    vat_no VARCHAR(50) UNIQUE,
    email VARCHAR(100),
    phone VARCHAR(20),
    wa_phone_number VARCHAR(20),  -- WhatsApp for country detection
    whatsapp_number VARCHAR(20),  -- Alternative column name
    preferred_language VARCHAR(10),  -- NO DEFAULT - auto-detected
    notes TEXT,
    platform VARCHAR(10) DEFAULT 'AVA',
    farmer_type VARCHAR(50),  -- Universal: grain, fruit, vegetable, etc.
    farmer_type_secondary VARCHAR(50),
    total_hectares DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fields table - Universal agricultural fields
CREATE TABLE IF NOT EXISTS fields (
    field_id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_size DECIMAL(10, 2),  -- Size in hectares (universal)
    field_location VARCHAR(200),
    soil_type VARCHAR(50),  -- Universal soil types
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crops table - Universal crop catalog
CREATE TABLE IF NOT EXISTS crops (
    id SERIAL PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL UNIQUE,
    crop_type VARCHAR(50),  -- grain, fruit, vegetable, tree, etc.
    typical_cycle_days INTEGER,  -- Growing cycle (any climate)
    description TEXT
    -- NO country-specific columns!
);

-- Field crops - What's planted (universal)
CREATE TABLE IF NOT EXISTS field_crops (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(field_id) ON DELETE CASCADE,
    crop_name VARCHAR(100) NOT NULL,
    variety VARCHAR(100),  -- Any variety, any country
    planting_date DATE,
    expected_harvest_date DATE,
    actual_harvest_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'harvested', 'failed')),
    yield_per_hectare DECIMAL(8, 2),  -- Universal yield measure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations - Multi-language support
CREATE TABLE IF NOT EXISTS incoming_messages (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE SET NULL,
    wa_phone_number VARCHAR(20),
    phone_number VARCHAR(20),  -- Alternative column
    message_text TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'assistant')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    language VARCHAR(10),  -- NO DEFAULT - auto-detected
    topic VARCHAR(50),
    confidence_score DECIMAL(3, 2)
);

-- Tasks - Agricultural tasks (universal)
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    field_id INTEGER REFERENCES fields(field_id) ON DELETE CASCADE,
    task_type VARCHAR(50),  -- Universal task types
    task_description TEXT,
    description TEXT,  -- Alternative column name
    due_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather data - Universal weather tracking
CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
    country_code VARCHAR(3),  -- ISO country code
    date DATE NOT NULL,
    temperature_min DECIMAL(4, 1),  -- Celsius (universal)
    temperature_max DECIMAL(4, 1),
    humidity DECIMAL(5, 2),  -- Percentage
    rainfall DECIMAL(6, 2),  -- mm (universal)
    wind_speed DECIMAL(5, 2),  -- km/h
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommendations - Agricultural advice (universal)
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    field_id INTEGER REFERENCES fields(field_id) ON DELETE CASCADE,
    recommendation_type VARCHAR(50),
    recommendation_text TEXT NOT NULL,
    language VARCHAR(10),  -- Language of recommendation
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'implemented', 'ignored')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until DATE
);

-- Knowledge sources - Amendment #13 support
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,  -- 'farmer_specific', 'country_specific', 'global'
    country_code VARCHAR(3),  -- NULL for global sources
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,  -- NULL for non-farmer sources
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Country agricultural profiles - Amendment #13
CREATE TABLE IF NOT EXISTS country_agricultural_profiles (
    country_code VARCHAR(3) PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    main_crops TEXT[],  -- Array of main crops
    growing_seasons JSONB,  -- Seasonal information
    climate_zones TEXT[],
    agricultural_practices JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crop technology - Universal crop information
CREATE TABLE IF NOT EXISTS crop_technology (
    id SERIAL PRIMARY KEY,
    crop_type VARCHAR(100) NOT NULL,
    technology_name VARCHAR(200),
    description TEXT,
    applicable_countries TEXT[],  -- List of countries where applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_farmers_country ON farmers(country_code);
CREATE INDEX IF NOT EXISTS idx_farmers_whatsapp ON farmers(wa_phone_number);
CREATE INDEX IF NOT EXISTS idx_messages_farmer ON incoming_messages(farmer_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON incoming_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_fields_farmer ON fields(farmer_id);
CREATE INDEX IF NOT EXISTS idx_field_crops_field ON field_crops(field_id);
CREATE INDEX IF NOT EXISTS idx_tasks_farmer ON tasks(farmer_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_type ON knowledge_sources(source_type);

-- Add update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_farmers_updated_at BEFORE UPDATE ON farmers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_sources_updated_at BEFORE UPDATE ON knowledge_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Constitutional compliance comment
COMMENT ON SCHEMA public IS 'AVA OLO Agricultural Database - 100% Constitutional Compliance. No hardcoded countries or languages. Works for Bulgarian mango farmers!';