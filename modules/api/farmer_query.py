#!/usr/bin/env python3
"""
Query farmers by phone number
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/query", tags=["query"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.get("/farmers-by-phone/{phone_number}")
async def get_farmers_by_phone(phone_number: str):
    """Get all farmers with a specific phone number"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query farmers with this phone number in any phone field
        cursor.execute("""
            SELECT id, farm_name, manager_name, manager_last_name, 
                   phone, wa_phone_number, whatsapp_number, email,
                   city, country
            FROM farmers 
            WHERE phone = %s 
               OR wa_phone_number = %s 
               OR whatsapp_number = %s
            ORDER BY id
        """, (phone_number, phone_number, phone_number))
        
        farmers = cursor.fetchall()
        
        farmer_list = []
        for f in farmers:
            farmer_list.append({
                "id": f[0],
                "farm_name": f[1],
                "manager_name": f[2],
                "manager_last_name": f[3],
                "phone": f[4],
                "wa_phone_number": f[5],
                "whatsapp_number": f[6],
                "email": f[7],
                "city": f[8],
                "country": f[9]
            })
        
        return JSONResponse(content={
            "success": True,
            "phone_searched": phone_number,
            "farmers_found": len(farmer_list),
            "farmers": farmer_list
        })
        
    except Exception as e:
        logger.error(f"Phone query error: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()