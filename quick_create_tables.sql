-- Essential tables for AVA OLO Database Explorer
-- Run this in AWS RDS Query Editor

-- 1. Farmers table
CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    farm_name VARCHAR(255) NOT NULL,
    farmer_name VARCHAR(255),
    manager_name VARCHAR(255),
    phone_number VARCHAR(50),
    email VARCHAR(255),
    street VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Fields table
CREATE TABLE IF NOT EXISTS fields (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    field_name VARCHAR(255),
    area_hectares DECIMAL(10,2),
    location VARCHAR(255),
    soil_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Incoming messages
CREATE TABLE IF NOT EXISTS incoming_messages (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    message_text TEXT,
    phone_number VARCHAR(50),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_sent BOOLEAN DEFAULT FALSE
);

-- 4. Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    task_name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Add some sample data
INSERT INTO farmers (farm_name, farmer_name, city, country) VALUES 
('Green Valley Farm', 'John Smith', 'Zagreb', 'Croatia'),
('Sunny Hills', 'Maria Garcia', 'Split', 'Croatia'),
('River Bend Farm', 'Peter Johnson', 'Osijek', 'Croatia');

-- Verify tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';