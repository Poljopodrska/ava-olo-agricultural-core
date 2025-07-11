#!/usr/bin/env python3
"""
Script to check AWS RDS database for data and add test data if tables are empty.
"""

import psycopg2
from psycopg2 import sql
import sys
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'postgres',
    'user': 'postgres',
    'password': '2hpzvrg_xP~qNbz1[_NppSK$e*O1',
    'port': 5432
}

def connect_to_database():
    """Establish connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Successfully connected to the database")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        sys.exit(1)

def get_all_tables(conn):
    """Get all tables in the database (excluding system tables)."""
    cursor = conn.cursor()
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    cursor.execute(query)
    tables = cursor.fetchall()
    cursor.close()
    return [table[0] for table in tables]

def check_table_data(conn, table_name):
    """Check if a table contains any data."""
    cursor = conn.cursor()
    try:
        query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name))
        cursor.execute(query)
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error checking table {table_name}: {e}")
        return -1
    finally:
        cursor.close()

def create_farmers_table_if_not_exists(conn):
    """Create farmers table if it doesn't exist."""
    cursor = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS farmers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        phone VARCHAR(50),
        farm_name VARCHAR(255),
        location VARCHAR(255),
        crop_types TEXT,
        farm_size_acres DECIMAL(10, 2),
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    """
    try:
        cursor.execute(create_table_query)
        conn.commit()
        print("✓ Farmers table created or already exists")
    except Exception as e:
        print(f"✗ Error creating farmers table: {e}")
        conn.rollback()
    finally:
        cursor.close()

def add_test_data_to_farmers(conn):
    """Add test data to the farmers table."""
    cursor = conn.cursor()
    
    test_farmers = [
        ('John Smith', 'john.smith@example.com', '+1-555-0101', 'Smith Family Farm', 
         'Iowa, USA', 'Corn, Soybeans', 500.50, True),
        ('Maria Garcia', 'maria.garcia@example.com', '+1-555-0102', 'Garcia Organic Produce', 
         'California, USA', 'Tomatoes, Lettuce, Peppers', 75.25, True),
        ('Robert Johnson', 'robert.j@example.com', '+1-555-0103', 'Johnson Dairy Farm', 
         'Wisconsin, USA', 'Dairy, Hay', 320.00, True),
        ('Sarah Williams', 'sarah.w@example.com', '+1-555-0104', 'Williams Vineyard', 
         'Oregon, USA', 'Grapes, Wine Production', 120.75, True),
        ('David Chen', 'david.chen@example.com', '+1-555-0105', 'Chen Brothers Agriculture', 
         'Texas, USA', 'Cotton, Wheat', 850.00, True),
    ]
    
    insert_query = """
    INSERT INTO farmers (name, email, phone, farm_name, location, crop_types, farm_size_acres, is_active)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    try:
        for farmer in test_farmers:
            cursor.execute(insert_query, farmer)
        conn.commit()
        print(f"✓ Successfully added {len(test_farmers)} test farmers to the database")
    except Exception as e:
        print(f"✗ Error adding test data: {e}")
        conn.rollback()
    finally:
        cursor.close()

def fetch_and_display_farmers(conn):
    """Fetch and display all farmers from the database."""
    cursor = conn.cursor()
    query = """
    SELECT id, name, email, farm_name, location, farm_size_acres, registration_date 
    FROM farmers 
    ORDER BY id;
    """
    
    try:
        cursor.execute(query)
        farmers = cursor.fetchall()
        
        if farmers:
            print("\n=== Farmers in Database ===")
            print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Farm Name':<25} {'Location':<20} {'Size (acres)':<12} {'Registered'}")
            print("-" * 135)
            
            for farmer in farmers:
                id, name, email, farm_name, location, size, reg_date = farmer
                reg_date_str = reg_date.strftime('%Y-%m-%d %H:%M') if reg_date else 'N/A'
                print(f"{id:<5} {name:<20} {email:<30} {farm_name:<25} {location:<20} {size:<12.2f} {reg_date_str}")
        else:
            print("\nNo farmers found in the database.")
            
    except Exception as e:
        print(f"✗ Error fetching farmers: {e}")
    finally:
        cursor.close()

def main():
    """Main function to orchestrate database operations."""
    print("=== AWS RDS Database Check and Data Addition Script ===\n")
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        # Get all tables
        tables = get_all_tables(conn)
        
        if not tables:
            print("\nNo tables found in the database.")
            print("Creating farmers table...")
            create_farmers_table_if_not_exists(conn)
            tables = get_all_tables(conn)
        
        # Check data in all tables
        print("\n=== Checking Tables for Data ===")
        empty_tables = []
        
        for table in tables:
            count = check_table_data(conn, table)
            if count >= 0:
                status = "EMPTY" if count == 0 else f"{count} rows"
                print(f"Table '{table}': {status}")
                if count == 0:
                    empty_tables.append(table)
        
        # Check if farmers table exists and is empty
        if 'farmers' not in tables:
            print("\nFarmers table doesn't exist. Creating it...")
            create_farmers_table_if_not_exists(conn)
            empty_tables.append('farmers')
        elif 'farmers' in empty_tables:
            print("\nFarmers table is empty.")
        
        # Add test data if farmers table is empty
        if 'farmers' in empty_tables or ('farmers' in tables and check_table_data(conn, 'farmers') == 0):
            print("\nAdding test data to farmers table...")
            add_test_data_to_farmers(conn)
            
            # Verify data was added
            print("\nVerifying data was added...")
            fetch_and_display_farmers(conn)
        else:
            print("\nFarmers table already contains data.")
            fetch_and_display_farmers(conn)
            
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()