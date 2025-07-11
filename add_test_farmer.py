#!/usr/bin/env python3
import psycopg2
from datetime import datetime

# RDS Connection Details
RDS_CONFIG = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'postgres',
    'user': 'postgres', 
    'password': '2hpzvrg_xP~qNbz1[_NppSK$e*O1',
    'port': 5432
}

print("🌱 Adding test farmer to database...")

try:
    # Connect to RDS
    conn = psycopg2.connect(**RDS_CONFIG)
    cursor = conn.cursor()
    
    # Add a test farmer
    insert_query = """
    INSERT INTO farmers (
        state_farm_number, farm_name, manager_name, manager_last_name,
        street_and_no, village, postal_code, city, country,
        vat_no, email, phone, wa_phone_number, notes
    ) VALUES (
        'TEST001', 'Test Farm Inc', 'John', 'Doe',
        '123 Farm Road', 'Farmville', '10000', 'Zagreb', 'Croatia',
        'HR12345678901', 'john.doe@testfarm.com', '+385911234567', '+385911234567',
        'This is a test farmer record created for verification'
    ) RETURNING id;
    """
    
    cursor.execute(insert_query)
    farmer_id = cursor.fetchone()[0]
    conn.commit()
    
    print(f"✅ Test farmer added successfully with ID: {farmer_id}")
    
    # Verify by counting
    cursor.execute("SELECT COUNT(*) FROM farmers")
    count = cursor.fetchone()[0]
    print(f"📊 Total farmers in database: {count}")
    
    # Fetch the farmer we just added
    cursor.execute("SELECT * FROM farmers WHERE id = %s", (farmer_id,))
    farmer = cursor.fetchone()
    
    if farmer:
        print("\n🧑‍🌾 Added farmer details:")
        print(f"  - Farm Name: {farmer[2]}")
        print(f"  - Manager: {farmer[3]} {farmer[4]}")
        print(f"  - Location: {farmer[8]}, {farmer[9]}")
        print(f"  - Email: {farmer[11]}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Test completed! Check the Database Explorer to see the new farmer.")
    
except Exception as e:
    print(f"❌ Error: {e}")