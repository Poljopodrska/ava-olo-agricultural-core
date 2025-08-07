#!/usr/bin/env python3
"""
Check fields table structure
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import urllib.parse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/fields-structure")
async def check_fields_structure():
    """Check fields table structure and Edi's fields"""
    
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
        
        # 1. Get fields table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'fields' 
            ORDER BY ordinal_position
        """)
        results['fields_columns'] = [
            {'name': row[0], 'type': row[1]} 
            for row in cursor.fetchall()
        ]
        
        # 2. Get all fields (first 10)
        cursor.execute("""
            SELECT * FROM fields LIMIT 10
        """)
        
        # Get column names from cursor description
        col_names = [desc[0] for desc in cursor.description]
        results['sample_fields'] = []
        for row in cursor.fetchall():
            field_dict = dict(zip(col_names, row))
            # Convert any non-serializable types
            for key, value in field_dict.items():
                if hasattr(value, 'isoformat'):
                    field_dict[key] = value.isoformat()
                elif isinstance(value, (int, float, str, bool, type(None))):
                    pass
                else:
                    field_dict[key] = str(value)
            results['sample_fields'].append(field_dict)
        
        # 3. Get Edi's fields specifically
        cursor.execute("""
            SELECT * FROM fields WHERE farmer_id = 49
        """)
        
        results['edi_fields'] = []
        for row in cursor.fetchall():
            field_dict = dict(zip(col_names, row))
            # Convert any non-serializable types
            for key, value in field_dict.items():
                if hasattr(value, 'isoformat'):
                    field_dict[key] = value.isoformat()
                elif isinstance(value, (int, float, str, bool, type(None))):
                    pass
                else:
                    field_dict[key] = str(value)
            results['edi_fields'].append(field_dict)
        
        # 4. Count total fields for Edi
        cursor.execute("""
            SELECT COUNT(*) FROM fields WHERE farmer_id = 49
        """)
        results['edi_field_count'] = cursor.fetchone()[0]
        
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