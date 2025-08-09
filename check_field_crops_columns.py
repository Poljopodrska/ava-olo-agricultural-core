#!/usr/bin/env python3
"""
Check the actual column names in field_crops table
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DB_CONFIG = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'j2D8J4LH:~eFrUz>$:kkNT(P$Rq_',
    'port': '5432'
}

def check_columns():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get column information
    cur.execute("""
        SELECT column_name, data_type, ordinal_position
        FROM information_schema.columns 
        WHERE table_name = 'field_crops'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    
    print("field_crops table columns:")
    print("-" * 50)
    for col in columns:
        print(f"{col['ordinal_position']:2}. {col['column_name']:20} ({col['data_type']})")
    
    # Now check data for farmer 49 (Edi)
    print("\n\nData for farmer 49 (Edi Kante):")
    print("-" * 50)
    
    cur.execute("""
        SELECT 
            fc.*,
            f.field_name
        FROM field_crops fc
        JOIN fields f ON fc.field_id = f.id
        WHERE f.farmer_id = 49
    """)
    
    crops = cur.fetchall()
    
    if crops:
        print(f"Found {len(crops)} crop entries:")
        for crop in crops:
            print(f"\nField ID: {crop.get('field_id')}")
            print(f"Field Name: {crop.get('field_name')}")
            for key, value in crop.items():
                if key not in ['field_id', 'field_name']:
                    print(f"  {key}: {value}")
    else:
        print("No crops found for farmer 49")
    
    # Also check fields for farmer 49
    print("\n\nFields for farmer 49:")
    print("-" * 50)
    
    cur.execute("""
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = 49
        ORDER BY field_name
    """)
    
    fields = cur.fetchall()
    for field in fields:
        print(f"ID: {field['id']:3} | Name: {field['field_name']:20} | Size: {field['area_ha']} ha")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_columns()