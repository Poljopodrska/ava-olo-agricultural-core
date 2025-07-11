#!/usr/bin/env python3
import requests
import json

# Base URL for the database explorer
BASE_URL = "https://6pmgrirjre.us-east-1.awsapprunner.com/database"

print("🔍 Checking database for existing data...\n")

# Get list of all tables
response = requests.get(f"{BASE_URL}/api/tables")
if response.status_code == 200:
    tables_data = response.json()
    tables = tables_data.get("tables", [])
    
    print(f"Found {len(tables)} tables in database:\n")
    
    # Check each table for data
    tables_with_data = []
    empty_tables = []
    
    for table in tables:
        table_name = table["name"]
        # Get table info which includes row count
        info_response = requests.get(f"{BASE_URL}/api/table/{table_name}/info")
        if info_response.status_code == 200:
            info = info_response.json()
            total_records = info.get("total_records", 0)
            
            if total_records > 0:
                tables_with_data.append((table_name, total_records))
                print(f"  ✅ {table_name}: {total_records} records")
            else:
                empty_tables.append(table_name)
                print(f"  ⚪ {table_name}: empty")
    
    print(f"\n📊 Summary:")
    print(f"  - Tables with data: {len(tables_with_data)}")
    print(f"  - Empty tables: {len(empty_tables)}")
    
    if tables_with_data:
        print(f"\n🎯 Tables containing data:")
        for table_name, count in tables_with_data:
            print(f"  - {table_name}: {count} records")
    else:
        print("\n❗ All tables are empty. The database structure exists but contains no data.")
        print("\n💡 To add test data, you can:")
        print("  1. Use the AI Query feature in the Database Explorer")
        print("  2. Import data from a SQL file")
        print("  3. Use the application to create records")
else:
    print(f"❌ Failed to get tables list: {response.status_code}")