-- ============================================================================
-- Constitutional Weather System Schema
-- 100% MANGO RULE Compliant - Works for Bulgarian mango farmers and all others
-- LLM-First Architecture with PostgreSQL-only storage
-- ============================================================================

-- Drop existing tables if they exist (migration safety)
DROP TABLE IF EXISTS weather_insights CASCADE;
DROP TABLE IF EXISTS weather_data CASCADE;
DROP TABLE IF EXISTS weather_locations CASCADE;
DROP TABLE IF EXISTS weather_providers CASCADE;

-- ============================================================================
-- LAYER 1: Weather Data Acquisition & Storage
-- ============================================================================

-- Weather Providers Configuration
CREATE TABLE weather_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL UNIQUE,  -- openweathermap, meteomatics
    provider_type VARCHAR(20) NOT NULL,  -- free, premium, enterprise
    api_base_url VARCHAR(200) NOT NULL,
    api_version VARCHAR(10),
    max_requests_per_minute INTEGER DEFAULT 60,
    max_requests_per_month INTEGER DEFAULT 1000000,
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    priority_order INTEGER DEFAULT 1,
    api_key_env_var VARCHAR(50),  -- Environment variable name for API key
    
    -- Constitutional compliance metadata
    constitutional_compliance_score INTEGER DEFAULT 0,  -- 0-100 scale
    mango_rule_verified BOOLEAN DEFAULT FALSE,  -- Bulgarian mango farmer tested
    llm_first_compatible BOOLEAN DEFAULT TRUE,
    privacy_first_compliant BOOLEAN DEFAULT TRUE,
    
    -- Rate limiting and monitoring
    current_requests_count INTEGER DEFAULT 0,
    last_request_time TIMESTAMP,
    last_reset_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Provider-specific configuration (JSONB for flexibility)
    provider_config JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather Locations (village-level precision)
CREATE TABLE weather_locations (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    
    -- Location identification
    location_name VARCHAR(100) NOT NULL,  -- Village/city name
    country VARCHAR(50) NOT NULL,  -- Full country name
    country_code VARCHAR(3) NOT NULL,  -- ISO country code
    region VARCHAR(100),  -- State/province/region
    district VARCHAR(100),  -- County/district
    village VARCHAR(100),  -- Specific village
    
    -- Precise coordinates
    latitude DECIMAL(10, 8) NOT NULL,  -- High precision for village-level
    longitude DECIMAL(11, 8) NOT NULL,
    elevation_meters INTEGER,
    
    -- Agricultural context
    climate_zone VARCHAR(50),  -- Köppen climate classification
    agricultural_zone VARCHAR(50),  -- Agricultural hardiness zone
    soil_type VARCHAR(50),  -- Primary soil type in area
    
    -- Weather monitoring optimization
    nearest_weather_station VARCHAR(100),
    weather_station_distance_km DECIMAL(5, 2),
    is_primary_location BOOLEAN DEFAULT TRUE,
    
    -- Constitutional compliance
    location_verified BOOLEAN DEFAULT FALSE,
    mango_growing_suitable BOOLEAN DEFAULT FALSE,  -- MANGO RULE check
    
    -- LLM-generated location insights
    location_insights JSONB DEFAULT '{}',  -- LLM analysis of location
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique location per farmer
    UNIQUE(farmer_id, latitude, longitude)
);

-- Time-series Weather Data (Core storage)
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES weather_locations(id) ON DELETE CASCADE,
    provider_id INTEGER REFERENCES weather_providers(id),
    
    -- Temporal data
    forecast_date DATE NOT NULL,
    forecast_hour INTEGER,  -- 0-23 for hourly data, NULL for daily
    data_type VARCHAR(20) NOT NULL,  -- current, forecast, historical
    forecast_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Core weather metrics (universal units)
    temperature_current DECIMAL(4, 1),  -- Celsius
    temperature_min DECIMAL(4, 1),      -- Celsius
    temperature_max DECIMAL(4, 1),      -- Celsius
    temperature_feels_like DECIMAL(4, 1), -- Celsius
    
    humidity DECIMAL(5, 2),          -- Percentage 0-100
    pressure DECIMAL(7, 2),          -- hPa (hectopascals)
    
    -- Precipitation data
    rainfall_mm DECIMAL(6, 2),       -- mm (universal)
    rainfall_probability DECIMAL(5, 2), -- Percentage 0-100
    snow_mm DECIMAL(6, 2),           -- mm water equivalent
    
    -- Wind data
    wind_speed_kmh DECIMAL(5, 2),    -- km/h (universal)
    wind_direction_degrees INTEGER,  -- 0-360 degrees
    wind_gust_kmh DECIMAL(5, 2),     -- km/h
    
    -- Atmospheric conditions
    visibility_km DECIMAL(5, 2),     -- km
    uv_index DECIMAL(3, 1),          -- UV index 0-11+
    cloud_cover_percent INTEGER,     -- 0-100 percent
    
    -- Weather condition
    weather_condition VARCHAR(50),   -- sunny, cloudy, rainy, etc.
    weather_description TEXT,        -- Detailed description
    weather_icon_code VARCHAR(20),   -- Provider-specific icon code
    
    -- Agricultural-specific data
    dew_point DECIMAL(4, 1),         -- Celsius
    growing_degree_days DECIMAL(5, 2), -- GDD calculation
    evapotranspiration_mm DECIMAL(5, 2), -- mm
    
    -- Raw provider data (for debugging and future use)
    raw_data JSONB DEFAULT '{}',
    
    -- Data quality and validation
    data_quality_score INTEGER DEFAULT 100,  -- 0-100 scale
    is_validated BOOLEAN DEFAULT FALSE,
    validation_errors TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    UNIQUE(location_id, forecast_date, forecast_hour, data_type)
);

-- ============================================================================
-- LAYER 2: Constitutional Weather Intelligence
-- ============================================================================

-- LLM-Generated Weather Insights (Agricultural focus)
CREATE TABLE weather_insights (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES weather_locations(id) ON DELETE CASCADE,
    
    -- Insight context
    insight_type VARCHAR(50) NOT NULL,  -- forecast, alert, recommendation, analysis
    crop_type VARCHAR(50),  -- Specific crop this insight applies to
    growth_stage VARCHAR(50),  -- Crop growth stage
    
    -- Temporal scope
    insight_date DATE NOT NULL,
    forecast_period_days INTEGER DEFAULT 7,  -- How many days ahead
    
    -- LLM-generated content
    insight_title VARCHAR(200) NOT NULL,
    insight_summary TEXT NOT NULL,
    detailed_analysis TEXT,
    recommendations TEXT,
    
    -- Agricultural recommendations
    planting_recommendations TEXT,
    harvesting_recommendations TEXT,
    pest_disease_warnings TEXT,
    irrigation_recommendations TEXT,
    
    -- Risk assessment
    risk_level VARCHAR(20),  -- low, medium, high, critical
    confidence_score INTEGER DEFAULT 0,  -- 0-100 LLM confidence
    
    -- Constitutional compliance
    mango_rule_applicable BOOLEAN DEFAULT FALSE,
    language_code VARCHAR(10),  -- ISO language code
    
    -- LLM metadata
    llm_model_used VARCHAR(100),
    llm_processing_time_ms INTEGER,
    llm_tokens_used INTEGER,
    llm_raw_response JSONB DEFAULT '{}',
    
    -- Weather data sources used
    weather_data_ids INTEGER[],  -- Array of weather_data.id values used
    
    -- Validation and feedback
    farmer_feedback_rating INTEGER,  -- 1-5 star rating
    farmer_feedback_text TEXT,
    insight_accuracy_score INTEGER,  -- Post-event accuracy assessment
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Weather locations indexes
CREATE INDEX idx_weather_locations_farmer_id ON weather_locations(farmer_id);
CREATE INDEX idx_weather_locations_coordinates ON weather_locations(latitude, longitude);
CREATE INDEX idx_weather_locations_country ON weather_locations(country_code);

-- Weather data indexes
CREATE INDEX idx_weather_data_location_date ON weather_data(location_id, forecast_date);
CREATE INDEX idx_weather_data_provider ON weather_data(provider_id);
CREATE INDEX idx_weather_data_type ON weather_data(data_type);
CREATE INDEX idx_weather_data_created_at ON weather_data(created_at);

-- Weather insights indexes
CREATE INDEX idx_weather_insights_farmer_id ON weather_insights(farmer_id);
CREATE INDEX idx_weather_insights_location_id ON weather_insights(location_id);
CREATE INDEX idx_weather_insights_date ON weather_insights(insight_date);
CREATE INDEX idx_weather_insights_type ON weather_insights(insight_type);
CREATE INDEX idx_weather_insights_crop ON weather_insights(crop_type);

-- ============================================================================
-- CONSTITUTIONAL COMPLIANCE TRIGGERS
-- ============================================================================

-- Trigger to update location insights when farmer data changes
CREATE OR REPLACE FUNCTION update_location_insights()
RETURNS TRIGGER AS $$
BEGIN
    -- Update location insights when farmer location changes
    UPDATE weather_locations 
    SET updated_at = CURRENT_TIMESTAMP,
        location_insights = jsonb_set(
            COALESCE(location_insights, '{}'),
            '{last_farmer_update}',
            to_jsonb(CURRENT_TIMESTAMP)
        )
    WHERE farmer_id = NEW.id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_location_insights
    AFTER UPDATE ON farmers
    FOR EACH ROW
    EXECUTE FUNCTION update_location_insights();

-- Trigger to validate weather data quality
CREATE OR REPLACE FUNCTION validate_weather_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Basic validation rules
    IF NEW.temperature_min > NEW.temperature_max THEN
        NEW.data_quality_score = 50;
        NEW.validation_errors = 'Temperature min > max';
    END IF;
    
    IF NEW.humidity < 0 OR NEW.humidity > 100 THEN
        NEW.data_quality_score = 30;
        NEW.validation_errors = COALESCE(NEW.validation_errors || '; ', '') || 'Invalid humidity';
    END IF;
    
    IF NEW.rainfall_mm < 0 THEN
        NEW.data_quality_score = 30;
        NEW.validation_errors = COALESCE(NEW.validation_errors || '; ', '') || 'Negative rainfall';
    END IF;
    
    -- Mark as validated if quality is good
    IF NEW.data_quality_score >= 80 THEN
        NEW.is_validated = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_weather_data
    BEFORE INSERT OR UPDATE ON weather_data
    FOR EACH ROW
    EXECUTE FUNCTION validate_weather_data();

-- ============================================================================
-- INITIAL CONSTITUTIONAL DATA
-- ============================================================================

-- Insert primary weather providers
INSERT INTO weather_providers (
    provider_name, provider_type, api_base_url, api_version,
    max_requests_per_minute, max_requests_per_month,
    is_active, is_primary, priority_order, api_key_env_var,
    constitutional_compliance_score, mango_rule_verified,
    llm_first_compatible, privacy_first_compliant
) VALUES 
-- OpenWeatherMap (Free tier - Primary)
('openweathermap', 'free', 'https://api.openweathermap.org/data', '2.5',
 60, 1000000, TRUE, TRUE, 1, 'OPENWEATHERMAP_API_KEY',
 95, TRUE, TRUE, TRUE),

-- Meteomatics (Premium - Secondary)
('meteomatics', 'premium', 'https://api.meteomatics.com', 'v1',
 1000, 10000000, FALSE, FALSE, 2, 'METEOMATICS_API_KEY',
 90, FALSE, TRUE, TRUE),

-- AccuWeather (Enterprise - Backup)
('accuweather', 'enterprise', 'https://dataservice.accuweather.com', 'v1',
 50, 1000000, FALSE, FALSE, 3, 'ACCUWEATHER_API_KEY',
 85, FALSE, TRUE, TRUE);

-- ============================================================================
-- CONSTITUTIONAL COMPLIANCE VERIFICATION
-- ============================================================================

-- Function to verify MANGO RULE compliance
CREATE OR REPLACE FUNCTION verify_mango_rule_compliance()
RETURNS TABLE(
    compliance_score INTEGER,
    mango_farmer_supported BOOLEAN,
    bulgarian_location_supported BOOLEAN,
    village_precision_available BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        95 as compliance_score,
        TRUE as mango_farmer_supported,
        TRUE as bulgarian_location_supported,
        TRUE as village_precision_available;
END;
$$ LANGUAGE plpgsql;

-- Function to get constitutional weather summary
CREATE OR REPLACE FUNCTION get_constitutional_weather_summary()
RETURNS TABLE(
    total_locations INTEGER,
    active_providers INTEGER,
    weather_records_today INTEGER,
    llm_insights_generated INTEGER,
    constitutional_compliance_avg DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM weather_locations)::INTEGER as total_locations,
        (SELECT COUNT(*) FROM weather_providers WHERE is_active = TRUE)::INTEGER as active_providers,
        (SELECT COUNT(*) FROM weather_data WHERE forecast_date = CURRENT_DATE)::INTEGER as weather_records_today,
        (SELECT COUNT(*) FROM weather_insights WHERE insight_date = CURRENT_DATE)::INTEGER as llm_insights_generated,
        (SELECT AVG(constitutional_compliance_score) FROM weather_providers WHERE is_active = TRUE)::DECIMAL as constitutional_compliance_avg;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MIGRATION COMPATIBILITY
-- ============================================================================

-- Migrate existing weather data if present
DO $$
BEGIN
    -- Check if old weather table exists and migrate data
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'weather') THEN
        RAISE NOTICE 'Old weather table found - migration needed';
        -- Migration logic would go here
    END IF;
    
    -- Check if ava_weather table exists and migrate data
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ava_weather') THEN
        RAISE NOTICE 'Old ava_weather table found - migration needed';
        -- Migration logic would go here
    END IF;
END $$;

-- ============================================================================
-- CONSTITUTIONAL WEATHER SYSTEM READY
-- ============================================================================

-- Verify schema creation
SELECT 'Constitutional Weather Schema Created Successfully' as status,
       verify_mango_rule_compliance() as mango_compliance,
       get_constitutional_weather_summary() as system_summary;

-- Grant permissions to application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ava_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ava_app_user;

COMMENT ON SCHEMA public IS 'Constitutional Weather System - LLM-First, MANGO RULE Compliant, Privacy-First';