#!/usr/bin/env python3
"""
Unified API for farmer data - ensures dashboard and chat get the same data
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/farmer/{farmer_id}/complete-data")
async def get_farmer_complete_data(farmer_id: int):
    """
    Get complete farmer data for both dashboard display and chat context
    This ensures both interfaces show exactly the same data
    """
    from ..core.simple_db import execute_simple_query
    
    logger.info(f"📊 Fetching complete data for farmer {farmer_id}")
    
    result = {
        "farmer_id": farmer_id,
        "fields": [],
        "crops": [],
        "activities": [],
        "tasks": [],
        "summary": {}
    }
    
    try:
        # 1. Get farmer details
        farmer_query = """
            SELECT 
                id, farm_name, 
                CONCAT(manager_name, ' ', manager_last_name) as full_name,
                city, country, wa_phone_number
            FROM farmers 
            WHERE id = %s
        """
        farmer_result = execute_simple_query(farmer_query, (farmer_id,))
        
        if farmer_result.get('success') and farmer_result.get('rows'):
            farmer = farmer_result['rows'][0]
            result['farmer'] = {
                'id': farmer[0],
                'farm_name': farmer[1],
                'name': farmer[2],
                'city': farmer[3],
                'country': farmer[4],
                'phone': farmer[5]
            }
        
        # 2. Get fields with proper structure
        fields_query = """
            SELECT 
                id, field_name, area_ha, 
                latitude, longitude, country
            FROM fields 
            WHERE farmer_id = %s
            ORDER BY field_name
        """
        fields_result = execute_simple_query(fields_query, (farmer_id,))
        
        if fields_result.get('success') and fields_result.get('rows'):
            total_area = 0
            for field in fields_result['rows']:
                field_data = {
                    'id': field[0],
                    'name': field[1],
                    'area_ha': float(field[2]) if field[2] else 0,
                    'latitude': field[3],
                    'longitude': field[4],
                    'country': field[5]
                }
                result['fields'].append(field_data)
                total_area += field_data['area_ha']
            
            result['summary']['total_fields'] = len(result['fields'])
            result['summary']['total_area_ha'] = round(total_area, 2)
        
        # 3. Get crops with correct column names
        # First try crop_name (what dashboard uses)
        crops_query = """
            SELECT 
                fc.field_id,
                f.field_name,
                fc.crop_name,
                fc.variety,
                fc.start_date,
                fc.status,
                f.area_ha
            FROM field_crops fc
            JOIN fields f ON fc.field_id = f.id
            WHERE f.farmer_id = %s
            ORDER BY f.field_name, fc.start_date DESC
        """
        crops_result = execute_simple_query(crops_query, (farmer_id,))
        
        if crops_result.get('success') and crops_result.get('rows'):
            for crop in crops_result['rows']:
                crop_data = {
                    'field_id': crop[0],
                    'field_name': crop[1],
                    'crop': crop[2],
                    'variety': crop[3],
                    'planting_date': str(crop[4]) if crop[4] else None,
                    'status': crop[5],
                    'field_area_ha': float(crop[6]) if crop[6] else 0
                }
                result['crops'].append(crop_data)
                
                # Log corn specifically for debugging
                if crop[2] and 'corn' in crop[2].lower():
                    logger.info(f"🌽 CORN found on field '{crop[1]}' (ID={crop[0]})")
        
        # 4. Get recent activities from field_activities table
        activities_query = """
            SELECT 
                fa.field_id,
                f.field_name,
                fa.activity_type,
                fa.product_name,
                fa.activity_date,
                fa.dose_amount,
                fa.dose_unit,
                fa.notes
            FROM field_activities fa
            JOIN fields f ON fa.field_id = f.id
            WHERE f.farmer_id = %s
            ORDER BY fa.activity_date DESC
            LIMIT 20
        """
        activities_result = execute_simple_query(activities_query, (farmer_id,))
        
        if activities_result.get('success') and activities_result.get('rows'):
            for activity in activities_result['rows']:
                activity_desc = activity[2]  # activity_type
                if activity[3]:  # product_name
                    activity_desc += f" - {activity[3]}"
                    if activity[5] and activity[6]:  # dose
                        activity_desc += f" ({activity[5]} {activity[6]})"
                
                activity_data = {
                    'field_id': activity[0],
                    'field_name': activity[1],
                    'type': activity[2],
                    'description': activity_desc,
                    'product': activity[3],
                    'date': str(activity[4]) if activity[4] else None,
                    'dose': f"{activity[5]} {activity[6]}" if activity[5] and activity[6] else None,
                    'notes': activity[7]
                }
                result['activities'].append(activity_data)
        
        # 5. Add data quality check
        result['data_quality'] = {
            'has_fields': len(result['fields']) > 0,
            'has_crops': len(result['crops']) > 0,
            'has_activities': len(result['activities']) > 0,
            'corn_location': None
        }
        
        # Find where corn is
        for crop in result['crops']:
            if crop['crop'] and 'corn' in crop['crop'].lower():
                result['data_quality']['corn_location'] = crop['field_name']
                break
        
        logger.info(f"✅ Complete data fetched for farmer {farmer_id}: "
                   f"{len(result['fields'])} fields, {len(result['crops'])} crops, "
                   f"{len(result['activities'])} activities")
        
        if result['data_quality']['corn_location']:
            logger.info(f"🌽 Corn is on field: {result['data_quality']['corn_location']}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error fetching farmer data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/farmer/{farmer_id}/fields-summary")
async def get_fields_summary(farmer_id: int):
    """
    Get a summary of farmer's fields with crops for dashboard display
    """
    from ..core.simple_db import execute_simple_query
    
    # Combined query to get fields with their current crops
    query = """
        SELECT 
            f.id,
            f.field_name,
            f.area_ha,
            fc.crop_name,
            fc.variety,
            fa.activity_type,
            fa.product_name,
            fa.activity_date,
            fa.dose_amount,
            fa.dose_unit
        FROM fields f
        LEFT JOIN field_crops fc ON f.id = fc.field_id 
            AND fc.status = 'active'
        LEFT JOIN LATERAL (
            SELECT activity_type, product_name, activity_date, dose_amount, dose_unit
            FROM field_activities
            WHERE field_id = f.id
            ORDER BY activity_date DESC
            LIMIT 1
        ) fa ON true
        WHERE f.farmer_id = %s
        ORDER BY f.field_name
    """
    
    result = execute_simple_query(query, (farmer_id,))
    
    if result.get('success') and result.get('rows'):
        fields = []
        for row in result['rows']:
            # Format last activity
            last_activity = "No activities yet"
            if row[5]:  # activity_type exists
                last_activity = row[5]
                if row[6]:  # product_name
                    last_activity += f" - {row[6]}"
                    if row[8] and row[9]:  # dose
                        last_activity += f" ({row[8]} {row[9]})"
                if row[7]:  # date
                    last_activity += f"\n{row[7]}"
            
            fields.append({
                'id': row[0],
                'name': row[1],
                'size_ha': row[2],
                'crop': row[3] or '-',
                'variety': row[4] or '-',
                'last_activity': last_activity
            })
        
        return JSONResponse(content={'success': True, 'fields': fields})
    
    return JSONResponse(content={'success': False, 'fields': []})