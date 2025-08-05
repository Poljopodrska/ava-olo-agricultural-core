#!/usr/bin/env python3
"""
Debug endpoint for Edi Kante fields issue
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import logging

from ..core.database_manager import get_db_manager
from ..auth.routes import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/edi-kante-fields", response_class=JSONResponse)
async def debug_edi_kante_fields(request: Request, current_user=Depends(get_current_user_optional)):
    """Debug endpoint to check Edi Kante's fields and why they might not be displaying"""
    
    if not current_user or current_user.get('username') != 'admin':
        return JSONResponse(content={
            "error": "Unauthorized - Admin access required"
        }, status_code=403)
    
    db_manager = get_db_manager()
    results = {}
    
    try:
        # 1. Check if Edi Kante exists as a farmer
        farmer_query = """
        SELECT id, name, email, phone, whatsapp_number, wa_phone_number, 
               city, country, created_at, auth_user_id
        FROM farmers 
        WHERE LOWER(name) LIKE '%edi%kante%' 
           OR LOWER(email) LIKE '%edi%kante%'
           OR phone LIKE '%38640187648%'
           OR whatsapp_number LIKE '%38640187648%'
           OR wa_phone_number LIKE '%38640187648%'
        """
        farmer_result = db_manager.execute_query(farmer_query)
        
        if farmer_result and 'rows' in farmer_result and farmer_result['rows']:
            farmer_data = []
            for row in farmer_result['rows']:
                farmer_data.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'whatsapp_number': row[4],
                    'wa_phone_number': row[5],
                    'city': row[6],
                    'country': row[7],
                    'created_at': row[8].isoformat() if row[8] else None,
                    'auth_user_id': row[9]
                })
            results['farmer'] = farmer_data
            
            # 2. Check fields for each farmer found
            for farmer in farmer_data:
                fields_query = """
                SELECT id, field_name, area_ha, latitude, longitude, 
                       country, created_at, updated_at
                FROM fields 
                WHERE farmer_id = %s
                ORDER BY created_at DESC
                """
                fields_result = db_manager.execute_query(fields_query, (farmer['id'],))
                
                if fields_result and 'rows' in fields_result:
                    farmer['fields'] = []
                    for row in fields_result['rows']:
                        farmer['fields'].append({
                            'id': row[0],
                            'field_name': row[1],
                            'area_ha': float(row[2]) if row[2] else None,
                            'latitude': float(row[3]) if row[3] else None,
                            'longitude': float(row[4]) if row[4] else None,
                            'country': row[5],
                            'created_at': row[6].isoformat() if row[6] else None,
                            'updated_at': row[7].isoformat() if row[7] else None
                        })
                    farmer['field_count'] = len(farmer['fields'])
                else:
                    farmer['fields'] = []
                    farmer['field_count'] = 0
                
                # 3. Check auth_users table connection
                if farmer['auth_user_id']:
                    auth_query = """
                    SELECT id, username, email, is_active, created_at
                    FROM auth_users
                    WHERE id = %s
                    """
                    auth_result = db_manager.execute_query(auth_query, (farmer['auth_user_id'],))
                    
                    if auth_result and 'rows' in auth_result and auth_result['rows']:
                        row = auth_result['rows'][0]
                        farmer['auth_user'] = {
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'is_active': row[3],
                            'created_at': row[4].isoformat() if row[4] else None
                        }
                    else:
                        farmer['auth_user'] = None
                        
                # 4. Check if there are any field_crops entries
                if farmer['fields']:
                    for field in farmer['fields']:
                        crops_query = """
                        SELECT id, crop_type, variety, planting_date, status
                        FROM field_crops
                        WHERE field_id = %s
                        ORDER BY planting_date DESC
                        """
                        crops_result = db_manager.execute_query(crops_query, (field['id'],))
                        
                        if crops_result and 'rows' in crops_result:
                            field['crops'] = []
                            for row in crops_result['rows']:
                                field['crops'].append({
                                    'id': row[0],
                                    'crop_type': row[1],
                                    'variety': row[2],
                                    'planting_date': row[3].isoformat() if row[3] else None,
                                    'status': row[4]
                                })
                        else:
                            field['crops'] = []
            
            # 5. Analysis of potential issues
            results['analysis'] = {
                'farmers_found': len(farmer_data),
                'total_fields': sum(f['field_count'] for f in farmer_data),
                'potential_issues': []
            }
            
            for farmer in farmer_data:
                if farmer['field_count'] == 0:
                    results['analysis']['potential_issues'].append(
                        f"Farmer {farmer['name']} (ID: {farmer['id']}) has no fields"
                    )
                if not farmer.get('auth_user'):
                    results['analysis']['potential_issues'].append(
                        f"Farmer {farmer['name']} has no linked auth_user account"
                    )
                elif farmer.get('auth_user') and not farmer['auth_user']['is_active']:
                    results['analysis']['potential_issues'].append(
                        f"Farmer {farmer['name']}'s auth account is inactive"
                    )
        else:
            results['farmer'] = None
            results['analysis'] = {
                'farmers_found': 0,
                'error': 'No farmer found with name containing "Edi Kante" or phone +38640187648'
            }
            
            # Check if there's any similar name
            similar_query = """
            SELECT id, name, phone, whatsapp_number, wa_phone_number
            FROM farmers
            WHERE LOWER(name) LIKE '%edi%' OR LOWER(name) LIKE '%kante%'
            LIMIT 10
            """
            similar_result = db_manager.execute_query(similar_query)
            
            if similar_result and 'rows' in similar_result and similar_result['rows']:
                results['similar_farmers'] = []
                for row in similar_result['rows']:
                    results['similar_farmers'].append({
                        'id': row[0],
                        'name': row[1],
                        'phone': row[2],
                        'whatsapp_number': row[3],
                        'wa_phone_number': row[4]
                    })
        
        # 6. Check authentication configuration
        results['auth_check'] = {
            'login_url': '/auth/login',
            'dashboard_url': '/farmer/dashboard',
            'requires_auth': True
        }
        
        return JSONResponse(content={
            "success": True,
            "debug_results": results,
            "recommendations": [
                "1. Ensure Edi Kante is logged in with correct credentials",
                "2. Check if auth_user account is active",
                "3. Verify fields are associated with correct farmer_id",
                "4. Check browser console for any JavaScript errors",
                "5. Clear browser cache and cookies, then login again"
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in Edi Kante debug: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)