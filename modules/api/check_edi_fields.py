#!/usr/bin/env python3
"""
Check Edi Kante's fields in the database
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import urllib.parse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/edi-fields")
async def check_edi_fields():
    """Check all fields for Edi Kante"""
    
    # Get from environment or use defaults (same as config.py)
    db_host = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
    db_name = os.getenv('DB_NAME', 'postgres')  
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'j2D8J4LH:~eFrUz>$:kkNT(P$Rq_')
    db_port = os.getenv('DB_PORT', '5432')
    
    # URL encode the password for special characters
    password_encoded = urllib.parse.quote_plus(db_password)
    DB_URL = f"postgresql://{db_user}:{password_encoded}@{db_host}:{db_port}/{db_name}"
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        results = {}
        
        # 1. Check Edi's basic info
        cursor.execute("""
            SELECT id, manager_name, manager_last_name, 
                   whatsapp_number, wa_phone_number, email
            FROM farmers 
            WHERE id = 49
        """)
        edi = cursor.fetchone()
        
        if edi:
            results['farmer_info'] = {
                'id': edi[0],
                'name': f"{edi[1]} {edi[2]}",
                'whatsapp': edi[3],
                'wa_phone': edi[4],
                'email': edi[5]
            }
            
            # 2. Get all fields for Edi
            cursor.execute("""
                SELECT 
                    id,
                    field_name,
                    area_ha,
                    location,
                    country,
                    created_at
                FROM fields 
                WHERE farmer_id = 49
                ORDER BY id
            """)
            fields = cursor.fetchall()
            
            results['fields'] = []
            for field in fields:
                field_data = {
                    'field_id': field[0],
                    'field_name': field[1],
                    'area_ha': float(field[2]) if field[2] else None,
                    'location': field[3],
                    'country': field[4],
                    'created_at': field[5].isoformat() if field[5] else None
                }
                
                # Get crops for this field
                cursor.execute("""
                    SELECT 
                        crop_name,
                        variety,
                        start_year_int,
                        start_date,
                        end_date,
                        area_ha
                    FROM field_crops 
                    WHERE field_id = %s
                    ORDER BY start_year_int DESC
                """, (field[0],))
                crops = cursor.fetchall()
                
                field_data['crops'] = []
                for crop in crops:
                    field_data['crops'].append({
                        'crop_name': crop[0],
                        'variety': crop[1],
                        'year': crop[2],
                        'start_date': crop[3].isoformat() if crop[3] else None,
                        'end_date': crop[4].isoformat() if crop[4] else None,
                        'area_ha': float(crop[5]) if crop[5] else None
                    })
                
                # Get recent activities for this field
                cursor.execute("""
                    SELECT 
                        activity_type,
                        activity_date,
                        description,
                        status
                    FROM field_activities 
                    WHERE field_id = %s
                    ORDER BY activity_date DESC
                    LIMIT 5
                """, (field[0],))
                activities = cursor.fetchall()
                
                field_data['recent_activities'] = []
                for activity in activities:
                    field_data['recent_activities'].append({
                        'type': activity[0],
                        'date': activity[1].isoformat() if activity[1] else None,
                        'description': activity[2],
                        'status': activity[3]
                    })
                
                results['fields'].append(field_data)
            
            # 3. Summary statistics
            results['summary'] = {
                'total_fields': len(fields),
                'total_area_ha': sum(f[2] for f in fields if f[2]),
                'field_names': [f[1] for f in fields]
            }
        else:
            results['error'] = 'Edi Kante (ID 49) not found'
        
        cursor.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "data": results
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)