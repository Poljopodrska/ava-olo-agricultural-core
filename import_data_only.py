#!/usr/bin/env python3
"""
Import only DATA from SQL file (skip CREATE TABLE statements)
Handles PostgreSQL COPY format
"""

import re
import psycopg2
from io import StringIO

# Database configuration
DB_CONFIG = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'postgres',
    'user': 'postgres',
    'password': '2hpzvrg_xP~qNbz1[_NppSK$e*O1',
    'port': 5432
}

def extract_copy_data(sql_file_path):
    """Extract COPY data blocks from SQL file"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all COPY statements with their data
    copy_pattern = r'COPY\s+"public"\."(\w+)"\s*\([^)]+\)\s+FROM\s+stdin;(.*?)\\\.'
    matches = re.findall(copy_pattern, content, re.DOTALL | re.MULTILINE)
    
    copy_data = []
    for table_name, data in matches:
        # Clean the data
        data = data.strip()
        if data:
            copy_data.append({
                'table': table_name,
                'data': data
            })
    
    return copy_data

def import_copy_data(copy_data):
    """Import COPY data into database"""
    conn = None
    try:
        print("🔌 Connecting to AWS RDS...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for item in copy_data:
            table_name = item['table']
            data = item['data']
            
            print(f"\n📊 Processing table: {table_name}")
            
            # Count existing records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            before_count = cursor.fetchone()[0]
            print(f"   Current records: {before_count}")
            
            if before_count > 0:
                print(f"   ⚠️  Table already has data, skipping...")
                continue
            
            # Create a file-like object from the data
            data_io = StringIO(data)
            
            # Get column names
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            try:
                # Use COPY to import data
                cursor.copy_from(
                    data_io,
                    table_name,
                    columns=columns,
                    sep='\t',
                    null='\\N'
                )
                conn.commit()
                
                # Count after import
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                after_count = cursor.fetchone()[0]
                added = after_count - before_count
                
                print(f"   ✅ Added {added} records")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                conn.rollback()
        
        print("\n✅ Data import completed!")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        if conn:
            conn.close()

def main():
    print("🚀 AVA OLO Data Import Tool")
    print("=" * 50)
    
    sql_file = 'farmer_crm_full_with_data.sql'
    
    print(f"📄 Reading SQL file: {sql_file}")
    copy_data = extract_copy_data(sql_file)
    
    print(f"\n📊 Found data for {len(copy_data)} tables:")
    for item in copy_data:
        # Count lines of data
        lines = item['data'].strip().split('\n')
        print(f"   - {item['table']}: {len(lines)} rows")
    
    if copy_data:
        print("\n🔄 Starting import to AWS RDS...")
        import_copy_data(copy_data)
    else:
        print("\n⚠️  No COPY data found in file")

if __name__ == "__main__":
    main()