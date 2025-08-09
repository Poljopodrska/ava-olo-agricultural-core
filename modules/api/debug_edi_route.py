#!/usr/bin/env python3
"""
Debug endpoint to check Edi's data
"""
from fastapi import APIRouter, HTTPException
from modules.core.simple_db import execute_simple_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/edi")
async def debug_edi_data():
    """
    Debug endpoint to check why FAVA can't see Edi's fields
    """
    results = {}
    
    # 1. Find all Edis
    edi_query = """
        SELECT id, manager_name, manager_last_name, wa_phone_number, phone, 
               farm_name, city, country
        FROM farmers 
        WHERE LOWER(manager_name) LIKE '%edi%' 
        ORDER BY id
    """
    edi_result = execute_simple_query(edi_query, ())
    
    if edi_result['success']:
        results['farmers_named_edi'] = []
        for row in edi_result['rows']:
            results['farmers_named_edi'].append({
                'id': row[0],
                'name': f"{row[1]} {row[2]}",
                'wa_phone': row[3],
                'phone': row[4],
                'farm': row[5],
                'location': f"{row[6]}, {row[7]}"
            })
    
    # 2. For each Edi, get their fields
    results['edi_fields'] = {}
    if edi_result['success']:
        for row in edi_result['rows']:
            farmer_id = row[0]
            farmer_name = f"{row[1]} {row[2]}"
            
            fields_query = """
                SELECT id, field_name, area_ha, latitude, longitude
                FROM fields 
                WHERE farmer_id = %s
                ORDER BY area_ha DESC
            """
            fields_result = execute_simple_query(fields_query, (farmer_id,))
            
            if fields_result['success']:
                fields_list = []
                for field in fields_result['rows']:
                    fields_list.append({
                        'id': field[0],
                        'name': field[1],
                        'area_ha': float(field[2]) if field[2] else 0,
                        'lat': float(field[3]) if field[3] else None,
                        'lon': float(field[4]) if field[4] else None
                    })
                
                results['edi_fields'][f"farmer_{farmer_id}_{farmer_name}"] = {
                    'count': len(fields_list),
                    'total_hectares': sum(f['area_ha'] for f in fields_list),
                    'fields': fields_list
                }
    
    # 3. Check phone number formats
    phone_check_query = """
        SELECT DISTINCT wa_phone_number, phone, COUNT(*) as count
        FROM farmers
        WHERE wa_phone_number IS NOT NULL OR phone IS NOT NULL
        GROUP BY wa_phone_number, phone
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """
    phone_result = execute_simple_query(phone_check_query, ())
    
    if phone_result['success']:
        results['duplicate_phones'] = []
        for row in phone_result['rows']:
            results['duplicate_phones'].append({
                'wa_phone': row[0],
                'phone': row[1],
                'count': row[2]
            })
    
    # 4. Check specific phone number
    test_phone = "+38651300564"  # Edi's known phone
    phone_variations = [
        test_phone,
        test_phone.lstrip('+'),
        "386" + test_phone.lstrip('+386'),
        "0" + test_phone.lstrip('+386')
    ]
    
    results['phone_lookup_test'] = {}
    for phone in phone_variations:
        lookup_query = """
            SELECT id, manager_name, manager_last_name
            FROM farmers
            WHERE wa_phone_number = %s OR phone = %s
        """
        lookup_result = execute_simple_query(lookup_query, (phone, phone))
        
        if lookup_result['success'] and lookup_result['rows']:
            results['phone_lookup_test'][phone] = {
                'found': True,
                'farmer': lookup_result['rows'][0]
            }
        else:
            results['phone_lookup_test'][phone] = {'found': False}
    
    # 5. Recent chat messages
    chat_query = """
        SELECT session_id, role, content, timestamp
        FROM chat_messages
        WHERE content LIKE '%field%' OR content LIKE '%Edi%'
        ORDER BY timestamp DESC
        LIMIT 10
    """
    chat_result = execute_simple_query(chat_query, ())
    
    if chat_result['success']:
        results['recent_field_chats'] = []
        for row in chat_result['rows']:
            results['recent_field_chats'].append({
                'session': row[0],
                'role': row[1],
                'content': row[2][:100],
                'time': str(row[3])
            })
    
    # 6. Summary
    results['summary'] = {
        'total_edis_found': len(results.get('farmers_named_edi', [])),
        'edis_with_fields': sum(1 for k, v in results.get('edi_fields', {}).items() if v['count'] > 0),
        'total_fields_across_all_edis': sum(v['count'] for v in results.get('edi_fields', {}).values()),
        'diagnostic_timestamp': str(datetime.now())
    }
    
    return results

@router.get("/debug/edi/{phone_number}")
async def debug_specific_phone(phone_number: str):
    """
    Debug a specific phone number lookup
    """
    # Clean the phone number
    phone_clean = phone_number.replace(' ', '').replace('-', '')
    
    variations = [
        phone_clean,
        '+' + phone_clean if not phone_clean.startswith('+') else phone_clean,
        phone_clean.lstrip('+'),
        '386' + phone_clean.lstrip('+386') if phone_clean.startswith('+386') else phone_clean
    ]
    
    results = {
        'original_input': phone_number,
        'variations_tested': variations,
        'results': {}
    }
    
    for variant in variations:
        query = """
            SELECT id, manager_name, manager_last_name, wa_phone_number, phone,
                   (SELECT COUNT(*) FROM fields WHERE farmer_id = farmers.id) as field_count
            FROM farmers
            WHERE wa_phone_number = %s OR phone = %s
        """
        result = execute_simple_query(query, (variant, variant))
        
        if result['success'] and result['rows']:
            row = result['rows'][0]
            results['results'][variant] = {
                'found': True,
                'farmer_id': row[0],
                'name': f"{row[1]} {row[2]}",
                'wa_phone_in_db': row[3],
                'phone_in_db': row[4],
                'field_count': row[5]
            }
        else:
            results['results'][variant] = {'found': False}
    
    # Also do a fuzzy search
    fuzzy_query = """
        SELECT id, manager_name, manager_last_name, wa_phone_number, phone
        FROM farmers
        WHERE wa_phone_number LIKE %s OR phone LIKE %s
        LIMIT 10
    """
    fuzzy_pattern = f"%{phone_clean[-6:]}%"  # Last 6 digits
    fuzzy_result = execute_simple_query(fuzzy_query, (fuzzy_pattern, fuzzy_pattern))
    
    if fuzzy_result['success'] and fuzzy_result['rows']:
        results['fuzzy_matches'] = []
        for row in fuzzy_result['rows']:
            results['fuzzy_matches'].append({
                'id': row[0],
                'name': f"{row[1]} {row[2]}",
                'wa_phone': row[3],
                'phone': row[4]
            })
    
    return results

# Import datetime at the top of the file
from datetime import datetime