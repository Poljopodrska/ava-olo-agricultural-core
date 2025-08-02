#!/usr/bin/env python3
"""
Quick check for phone number
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os

router = APIRouter(prefix="/api/v1/quick", tags=["quick"])

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'AVAolo2024Production!'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

@router.post("/check-phone")
async def check_phone():
    """Check for farmers with phone +38641348050"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        phone = "+38641348050"
        
        # Query all farmers
        cursor.execute("""
            SELECT id, farm_name, phone, wa_phone_number, whatsapp_number
            FROM farmers
            ORDER BY id
        """)
        
        all_farmers = cursor.fetchall()
        
        # Check which ones have the phone
        matching_farmers = []
        for f in all_farmers:
            if phone in [f[2], f[3], f[4]]:
                matching_farmers.append({
                    "id": f[0],
                    "farm_name": f[1],
                    "phone": f[2],
                    "wa_phone_number": f[3],
                    "whatsapp_number": f[4]
                })
        
        return JSONResponse(content={
            "phone_searched": phone,
            "total_farmers": len(all_farmers),
            "matching_farmers": matching_farmers,
            "all_farmers": [
                {
                    "id": f[0],
                    "farm_name": f[1],
                    "phone": f[2],
                    "wa_phone_number": f[3],
                    "whatsapp_number": f[4]
                }
                for f in all_farmers
            ]
        })
        
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()