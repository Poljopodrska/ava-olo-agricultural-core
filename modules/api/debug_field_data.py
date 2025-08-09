#!/usr/bin/env python3
"""
Debug endpoint to diagnose field/crop mismatch for Edi
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/edi-field-mismatch")
async def debug_edi_fields():
    """
    Diagnose why field "66" shows corn when it shouldn't
    """
    from ..core.simple_db import execute_simple_query
    
    result = {
        "issue": "Field 66 shows corn but shouldn't have any crop",
        "diagnostics": {}
    }
    
    # 1. Get Edi's fields with IDs
    fields_query = """
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = 49
        ORDER BY field_name
    """
    fields_result = execute_simple_query(fields_query, ())
    
    if fields_result.get('success') and fields_result.get('rows'):
        result['diagnostics']['edi_fields'] = []
        for field in fields_result['rows']:
            field_data = {
                'id': field[0],
                'name': field[1],
                'area_ha': float(field[2]) if field[2] else 0
            }
            result['diagnostics']['edi_fields'].append(field_data)
            
            # Find specific fields
            if field[1] == '66':
                result['diagnostics']['field_66_id'] = field[0]
            elif field[1] == 'Tinetova lukna':
                result['diagnostics']['tinetova_id'] = field[0]
            elif field[1] == 'Biljenski':
                result['diagnostics']['biljenski_id'] = field[0]
    
    # 2. Get raw field_crops data
    crops_query = """
        SELECT field_id, crop_name, variety
        FROM field_crops
        WHERE field_id IN (SELECT id FROM fields WHERE farmer_id = 49)
        ORDER BY field_id
    """
    crops_result = execute_simple_query(crops_query, ())
    
    if crops_result.get('success') and crops_result.get('rows'):
        result['diagnostics']['raw_crops'] = []
        for crop in crops_result['rows']:
            crop_data = {
                'field_id': crop[0],
                'crop_name': crop[1],
                'variety': crop[2]
            }
            result['diagnostics']['raw_crops'].append(crop_data)
    
    # 3. Get joined data (what FAVA sees)
    joined_query = """
        SELECT 
            f.id as field_id,
            f.field_name,
            fc.crop_name,
            fc.variety
        FROM fields f
        LEFT JOIN field_crops fc ON f.id = fc.field_id
        WHERE f.farmer_id = 49
        ORDER BY f.field_name
    """
    joined_result = execute_simple_query(joined_query, ())
    
    if joined_result.get('success') and joined_result.get('rows'):
        result['diagnostics']['joined_data'] = []
        for row in joined_result['rows']:
            joined_data = {
                'field_id': row[0],
                'field_name': row[1],
                'crop_name': row[2],
                'variety': row[3],
                'issue': None
            }
            
            # Check for issues
            if row[1] == '66' and row[2]:
                joined_data['issue'] = f"❌ Field 66 shouldn't have crop but has: {row[2]}"
            elif row[1] == 'Tinetova lukna' and row[2] != 'Corn':
                joined_data['issue'] = f"❌ Tinetova should have Corn but has: {row[2]}"
            elif row[1] == 'Biljenski' and row[2] != 'Vineyards':
                joined_data['issue'] = f"❌ Biljenski should have Vineyards but has: {row[2]}"
            
            result['diagnostics']['joined_data'].append(joined_data)
    
    # 4. Find where corn actually is
    corn_query = """
        SELECT 
            fc.field_id,
            f.field_name,
            fc.crop_name,
            fc.variety
        FROM field_crops fc
        JOIN fields f ON fc.field_id = f.id
        WHERE f.farmer_id = 49
          AND (fc.crop_name ILIKE '%corn%' OR fc.crop_name ILIKE '%mais%')
    """
    corn_result = execute_simple_query(corn_query, ())
    
    if corn_result.get('success') and corn_result.get('rows'):
        result['diagnostics']['corn_location'] = []
        for corn in corn_result['rows']:
            corn_data = {
                'field_id': corn[0],
                'field_name': corn[1],
                'crop_name': corn[2],
                'variety': corn[3]
            }
            result['diagnostics']['corn_location'].append(corn_data)
    
    # 5. Summary
    result['summary'] = {
        'field_66_has_id': result['diagnostics'].get('field_66_id'),
        'tinetova_has_id': result['diagnostics'].get('tinetova_id'),
        'corn_is_on_field_id': result['diagnostics']['corn_location'][0]['field_id'] if result['diagnostics'].get('corn_location') else None,
        'corn_is_on_field_name': result['diagnostics']['corn_location'][0]['field_name'] if result['diagnostics'].get('corn_location') else None
    }
    
    # Determine the issue
    if result['summary']['corn_is_on_field_name'] == '66':
        result['conclusion'] = "❌ WRONG: Corn is incorrectly associated with field '66' in the database!"
    elif result['summary']['corn_is_on_field_id'] == result['summary']['field_66_has_id']:
        result['conclusion'] = "❌ WRONG: Corn has field_id that points to field '66'!"
    else:
        result['conclusion'] = "✅ Database looks correct, issue might be in caching or display"
    
    return JSONResponse(content=result)