#!/usr/bin/env python3
"""
Create tables in AWS RDS - run this from App Runner or EC2
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Get the farmers table definition first
FARMERS_TABLE = """
CREATE TABLE IF NOT EXISTS public.farmers (
    id SERIAL PRIMARY KEY,
    farm_name VARCHAR(255) NOT NULL,
    farmer_name VARCHAR(255),
    manager_name VARCHAR(255),
    phone_number VARCHAR(50),
    email VARCHAR(255),
    street VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

FIELDS_TABLE = """
CREATE TABLE IF NOT EXISTS public.fields (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    field_name VARCHAR(255),
    area_hectares DECIMAL(10,2),
    location VARCHAR(255),
    soil_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS public.incoming_messages (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    message_text TEXT,
    phone_number VARCHAR(50),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_sent BOOLEAN DEFAULT FALSE
);
"""

TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS public.tasks (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    task_name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def main():
    # Database connection
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return
    
    print(f"🔌 Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    tables = [
        ("farmers", FARMERS_TABLE),
        ("fields", FIELDS_TABLE),
        ("incoming_messages", MESSAGES_TABLE),
        ("tasks", TASKS_TABLE)
    ]
    
    with engine.connect() as conn:
        for table_name, create_sql in tables:
            try:
                print(f"📋 Creating table: {table_name}")
                conn.execute(text(create_sql))
                conn.commit()
                print(f"✅ Table {table_name} created successfully")
            except Exception as e:
                print(f"❌ Error creating {table_name}: {e}")
        
        # Verify tables were created
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        
        tables = result.fetchall()
        print(f"\n📊 Total tables in database: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")

if __name__ == "__main__":
    main()