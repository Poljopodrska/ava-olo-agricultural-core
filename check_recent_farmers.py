#!/usr/bin/env python3
"""
Check recent farmer entries in the database
"""
import os
import psycopg2
from datetime import datetime
import json

# Get connection details from environment
db_config = {
    'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
    'database': 'postgres',  # Use postgres database since farmer_crm might not exist
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '2hpzvrg_xP~ qNbz1[_NppSK$e*O_h6g{Nux[3OA>wPSZ%8CaIK>bqXIcJE&F<G'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

try:
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(
        host=db_config['host'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        port=db_config['port'],
        sslmode='require'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Get the 10 most recent farmers
    print("\n=== 10 Most Recent Farmers ===")
    cursor.execute("""
        SELECT id, farm_name, manager_name, manager_last_name, email, 
               wa_phone_number, city, country, created_at
        FROM farmers 
        ORDER BY id DESC 
        LIMIT 10
    """)
    
    farmers = cursor.fetchall()
    for farmer in farmers:
        print(f"\nID: {farmer[0]}")
        print(f"  Farm: {farmer[1]}")
        print(f"  Manager: {farmer[2]} {farmer[3]}")
        print(f"  Email: {farmer[4]}")
        print(f"  WhatsApp: {farmer[5]}")
        print(f"  Location: {farmer[6]}, {farmer[7]}")
        print(f"  Created: {farmer[8] if farmer[8] else 'No timestamp'}")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM farmers")
    total = cursor.fetchone()[0]
    print(f"\nTotal farmers in database: {total}")
    
    # Get the newest farmer (highest ID)
    cursor.execute("""
        SELECT id, farm_name, manager_name, manager_last_name, email
        FROM farmers 
        WHERE id = (SELECT MAX(id) FROM farmers)
    """)
    newest = cursor.fetchone()
    if newest:
        print(f"\n=== Newest Farmer (by ID) ===")
        print(f"ID: {newest[0]}")
        print(f"Farm: {newest[1]}")
        print(f"Manager: {newest[2]} {newest[3]}")
        print(f"Email: {newest[4]}")
    
    # Check for any farmers added today
    cursor.execute("""
        SELECT id, farm_name, manager_name, email, created_at
        FROM farmers 
        WHERE created_at >= CURRENT_DATE
        ORDER BY created_at DESC
    """)
    today_farmers = cursor.fetchall()
    if today_farmers:
        print(f"\n=== Farmers Added Today ({len(today_farmers)} total) ===")
        for farmer in today_farmers:
            print(f"ID {farmer[0]}: {farmer[1]} - {farmer[2]} ({farmer[3]})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()