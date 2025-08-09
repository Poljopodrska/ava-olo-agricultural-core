#!/usr/bin/env python3
"""
Direct test of what's in the database for Edi
"""
import sys
import os
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

from modules.core.simple_db import execute_simple_query

print("Testing Edi's data directly...")
print("=" * 60)

# 1. Get Edi's fields
print("\n1. EDI'S FIELDS:")
fields_query = """
    SELECT id, field_name, area_ha
    FROM fields
    WHERE farmer_id = 49
    ORDER BY field_name
"""
fields_result = execute_simple_query(fields_query, ())

field_map = {}
if fields_result.get('success') and fields_result.get('rows'):
    for field in fields_result['rows']:
        field_id, field_name, area = field
        field_map[field_id] = field_name
        print(f"  ID={field_id:3} | Name='{field_name:20}' | Size={area} ha")

print("\n" + "=" * 60)

# 2. Check for field "66" specifically
print("\n2. FIELD '66' DETAILS:")
field_66_query = """
    SELECT id, field_name, area_ha, farmer_id
    FROM fields
    WHERE (field_name = '66' OR id = 66) AND farmer_id = 49
"""
result = execute_simple_query(field_66_query, ())
if result.get('success') and result.get('rows'):
    for row in result['rows']:
        print(f"  Found: ID={row[0]}, Name='{row[1]}', Size={row[2]} ha, Farmer={row[3]}")
else:
    print("  No field with name '66' or ID 66 for farmer 49")

print("\n" + "=" * 60)

# 3. Check crops using crop_name
print("\n3. CROPS (using 'crop_name' column):")
crops_query = """
    SELECT 
        fc.field_id,
        f.field_name,
        fc.crop_name,
        fc.variety,
        fc.start_date
    FROM field_crops fc
    JOIN fields f ON fc.field_id = f.id
    WHERE f.farmer_id = 49
    ORDER BY f.field_name
"""
result = execute_simple_query(crops_query, ())

if result.get('success'):
    if result.get('rows'):
        for crop in result['rows']:
            field_id, field_name, crop_name, variety, start_date = crop
            print(f"  Field ID={field_id:3} | Name='{field_name:20}' | Crop='{crop_name:15}' | Variety='{variety}'")
            if crop_name and 'corn' in crop_name.lower():
                print(f"    *** CORN FOUND on field '{field_name}' (ID={field_id}) ***")
    else:
        print("  No crops found")
else:
    print(f"  Error with crop_name: {result.get('error')}")

print("\n" + "=" * 60)

# 4. Find where corn is
print("\n4. SEARCHING FOR CORN:")
corn_query = """
    SELECT 
        fc.field_id,
        f.field_name,
        f.area_ha,
        fc.crop_name,
        fc.variety
    FROM field_crops fc
    JOIN fields f ON fc.field_id = f.id
    WHERE f.farmer_id = 49
    AND (LOWER(fc.crop_name) LIKE '%corn%' OR fc.crop_name = 'Corn')
"""
result = execute_simple_query(corn_query, ())

if result.get('success') and result.get('rows'):
    print("  CORN LOCATIONS:")
    for row in result['rows']:
        field_id, field_name, area, crop_name, variety = row
        print(f"    Field ID={field_id} | Name='{field_name}' | Size={area} ha")
        print(f"    Crop='{crop_name}' | Variety='{variety}'")
else:
    print("  No corn found for Edi")

print("\n" + "=" * 60)
print("\nSUMMARY:")
print(f"  Total fields found: {len(field_map)}")
if field_map:
    print(f"  Field IDs: {list(field_map.keys())}")
    print(f"  Field Names: {list(field_map.values())}")