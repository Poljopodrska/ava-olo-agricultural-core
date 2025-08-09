#!/usr/bin/env python3
"""
Debug endpoint to check field_crops data for Edi
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/edi/crops")
async def debug_edi_crops():
    """Check what crops Edi has and how they're associated with fields"""
    from ..core.simple_db import execute_simple_query
    
    results = {}
    
    # Get Edi's fields
    fields_query = """
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = 49
        ORDER BY id
    """
    fields_result = execute_simple_query(fields_query, ())
    
    results['fields'] = []
    field_map = {}
    
    if fields_result.get('success') and fields_result.get('rows'):
        for field in fields_result['rows']:
            field_data = {
                'id': field[0],
                'name': field[1],
                'area_ha': float(field[2]) if field[2] else 0
            }
            results['fields'].append(field_data)
            field_map[field[0]] = field[1]
    
    # Try to get crops with crop_name column
    results['crops_with_crop_name'] = []
    crops_query1 = """
        SELECT 
            fc.field_id,
            fc.crop_name,
            fc.variety,
            fc.start_date,
            f.field_name
        FROM field_crops fc
        JOIN fields f ON fc.field_id = f.id
        WHERE f.farmer_id = 49
        ORDER BY fc.field_id
    """
    
    result1 = execute_simple_query(crops_query1, ())
    if result1.get('success'):
        if result1.get('rows'):
            for crop in result1['rows']:
                results['crops_with_crop_name'].append({
                    'field_id': crop[0],
                    'field_name': crop[4],
                    'crop_name': crop[1],
                    'variety': crop[2],
                    'start_date': str(crop[3]) if crop[3] else None
                })
        results['crop_name_column_works'] = True
    else:
        results['crop_name_column_error'] = result1.get('error')
    
    # Check if field 66 has ID 66 or if it's something else
    field_66_query = """
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = 49 AND (id = 66 OR field_name = '66')
    """
    field_66_result = execute_simple_query(field_66_query, ())
    
    if field_66_result.get('success') and field_66_result.get('rows'):
        results['field_66_details'] = {
            'id': field_66_result['rows'][0][0],
            'name': field_66_result['rows'][0][1],
            'area_ha': float(field_66_result['rows'][0][2]) if field_66_result['rows'][0][2] else 0
        }
    
    # Check Tinetova lukna specifically
    tinetova_query = """
        SELECT id, field_name, area_ha
        FROM fields
        WHERE farmer_id = 49 AND field_name ILIKE '%tinetova%'
    """
    tinetova_result = execute_simple_query(tinetova_query, ())
    
    if tinetova_result.get('success') and tinetova_result.get('rows'):
        results['tinetova_field'] = {
            'id': tinetova_result['rows'][0][0],
            'name': tinetova_result['rows'][0][1],
            'area_ha': float(tinetova_result['rows'][0][2]) if tinetova_result['rows'][0][2] else 0
        }
    
    # Get column names from field_crops
    columns_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'field_crops'
        AND column_name IN ('crop_name', 'crop_type', 'crop')
    """
    columns_result = execute_simple_query(columns_query, ())
    
    if columns_result.get('success') and columns_result.get('rows'):
        results['crop_columns_found'] = [row[0] for row in columns_result['rows']]
    
    return JSONResponse(content=results)