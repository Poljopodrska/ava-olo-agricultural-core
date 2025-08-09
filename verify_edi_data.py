#!/usr/bin/env python3
"""
Comprehensive test to verify Edi's data structure and fix any issues
"""
import sys
import os
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

from modules.core.simple_db import execute_simple_query
import json

def test_edi_data():
    print("=" * 80)
    print("COMPREHENSIVE EDI DATA VERIFICATION")
    print("=" * 80)
    
    results = {}
    
    # 1. Check what columns exist in field_crops table
    print("\n1. CHECKING field_crops TABLE STRUCTURE:")
    print("-" * 40)
    
    columns_query = """
        SELECT column_name, data_type, ordinal_position
        FROM information_schema.columns
        WHERE table_name = 'field_crops'
        ORDER BY ordinal_position
    """
    
    columns_result = execute_simple_query(columns_query, ())
    if columns_result.get('success') and columns_result.get('rows'):
        print("Columns in field_crops:")
        crop_column_name = None
        for col in columns_result['rows']:
            col_name = col[0]
            print(f"  {col[2]:2}. {col_name:25} ({col[1]})")
            if 'crop' in col_name.lower():
                crop_column_name = col_name
                print(f"      ^ Found crop column: {col_name}")
        results['crop_column'] = crop_column_name
    
    # 2. Get Edi's fields
    print("\n2. EDI'S FIELDS (farmer_id=49):")
    print("-" * 40)
    
    fields_query = """
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = 49
        ORDER BY field_name
    """
    
    fields_result = execute_simple_query(fields_query, ())
    field_map = {}
    
    if fields_result.get('success') and fields_result.get('rows'):
        print(f"Found {len(fields_result['rows'])} fields:")
        for field in fields_result['rows']:
            field_id, field_name, area = field
            field_map[field_id] = field_name
            print(f"  ID={field_id:4} | Name='{field_name:20}' | Size={area:6.1f} ha")
            
            # Special checks
            if field_name == '66' or field_id == 66:
                print(f"    *** Field '66' found with ID={field_id}")
            if 'tinetova' in field_name.lower():
                print(f"    *** Tinetova lukna found with ID={field_id}")
        
        results['fields'] = field_map
    
    # 3. Check crops - try both possible column names
    print("\n3. CROPS DATA:")
    print("-" * 40)
    
    # Try with crop_name first
    print("\nTrying with 'crop_name' column:")
    crops_query1 = """
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
    
    crops_result = execute_simple_query(crops_query1, ())
    
    if crops_result.get('success'):
        if crops_result.get('rows'):
            print(f"SUCCESS! Found {len(crops_result['rows'])} crops:")
            results['crops'] = []
            for crop in crops_result['rows']:
                field_id, field_name, crop_name, variety, start_date = crop
                print(f"  Field ID={field_id:4} | Name='{field_name:20}' | Crop='{crop_name:15}' | Variety='{variety or 'N/A':15}'")
                
                # Check for corn
                if crop_name and 'corn' in crop_name.lower():
                    print(f"    🌽 CORN FOUND on field '{field_name}' (ID={field_id})")
                    results['corn_field'] = field_name
                    results['corn_field_id'] = field_id
                
                results['crops'].append({
                    'field_id': field_id,
                    'field_name': field_name,
                    'crop_name': crop_name,
                    'variety': variety
                })
        else:
            print("  No crops found - trying with 'crop_type' column...")
            
            # Try with crop_type
            crops_query2 = """
                SELECT 
                    fc.field_id,
                    f.field_name,
                    fc.crop_type,
                    fc.variety,
                    fc.planting_date
                FROM field_crops fc
                JOIN fields f ON fc.field_id = f.id
                WHERE f.farmer_id = 49
                ORDER BY f.field_name
            """
            
            crops_result2 = execute_simple_query(crops_query2, ())
            if crops_result2.get('success') and crops_result2.get('rows'):
                print(f"Found {len(crops_result2['rows'])} crops using 'crop_type':")
                for crop in crops_result2['rows']:
                    print(f"  Field: {crop[1]:20} | Crop: {crop[2]:15} | Variety: {crop[3]}")
    else:
        print(f"  Error: {crops_result.get('error')}")
    
    # 4. Check activities
    print("\n4. FIELD ACTIVITIES:")
    print("-" * 40)
    
    activities_query = """
        SELECT 
            fa.field_id,
            f.field_name,
            fa.activity_type,
            fa.product_name,
            fa.activity_date,
            fa.dose_amount,
            fa.dose_unit
        FROM field_activities fa
        JOIN fields f ON fa.field_id = f.id
        WHERE f.farmer_id = 49
        ORDER BY fa.activity_date DESC
        LIMIT 10
    """
    
    activities_result = execute_simple_query(activities_query, ())
    if activities_result.get('success') and activities_result.get('rows'):
        print(f"Found {len(activities_result['rows'])} recent activities:")
        for activity in activities_result['rows'][:5]:
            field_id, field_name, activity_type, product, date, dose, unit = activity
            activity_desc = f"{activity_type}"
            if product:
                activity_desc += f" - {product}"
                if dose and unit:
                    activity_desc += f" ({dose} {unit})"
            print(f"  {date} | {field_name:20} | {activity_desc}")
    
    # 5. Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("-" * 40)
    
    if 'corn_field' in results:
        print(f"✅ Corn is correctly located on field: {results['corn_field']} (ID={results['corn_field_id']})")
    else:
        print("❌ No corn found in field_crops table")
    
    print(f"\nTotal fields: {len(field_map)}")
    print(f"Field IDs: {list(field_map.keys())}")
    print(f"Field names: {list(field_map.values())}")
    
    # Save results to file
    with open('edi_data_verification.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\nResults saved to edi_data_verification.json")
    
    return results

if __name__ == "__main__":
    test_edi_data()