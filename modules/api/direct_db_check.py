#!/usr/bin/env python3
"""
Direct database check - run this inside the container
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dbcheck", tags=["database"])

@router.get("/full")
async def full_database_check():
    """Complete database inspection directly"""
    
    # Try to connect using environment-based configuration first
    import os
    import urllib.parse
    
    # Get from environment or use defaults (same as config.py)
    db_host = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
    db_name = os.getenv('DB_NAME', 'postgres')  
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'j2D8J4LH:~eFrUz>$:kkNT(P$Rq_')
    db_port = os.getenv('DB_PORT', '5432')
    
    # URL encode the password for special characters
    password_encoded = urllib.parse.quote_plus(db_password)
    DB_URL = f"postgresql://{db_user}:{password_encoded}@{db_host}:{db_port}/{db_name}"
    
    logger.info(f"Connecting to database: {db_name} at {db_host}")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        results = {}
        
        # 1. Farmers table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'farmers' 
            ORDER BY ordinal_position
        """)
        results['farmers_columns'] = [
            {'name': row[0], 'type': row[1]} 
            for row in cursor.fetchall()
        ]
        
        # 2. Check farmer 49
        cursor.execute("""
            SELECT id, manager_name, manager_last_name, 
                   whatsapp_number, wa_phone_number, email 
            FROM farmers 
            WHERE id = 49
        """)
        farmer49 = cursor.fetchone()
        results['farmer_49'] = {
            'exists': bool(farmer49),
            'data': farmer49 if farmer49 else None
        }
        
        # 3. All farmers
        cursor.execute("""
            SELECT id, manager_name, manager_last_name, 
                   whatsapp_number, wa_phone_number 
            FROM farmers 
            ORDER BY id
        """)
        results['all_farmers'] = [
            {
                'id': row[0],
                'name': f"{row[1]} {row[2]}",
                'whatsapp': row[3],
                'wa_phone': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # 4. Count farmers
        cursor.execute("SELECT COUNT(*) FROM farmers")
        results['total_farmers'] = cursor.fetchone()[0]
        
        # 5. Chat messages structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' 
            ORDER BY ordinal_position
        """)
        results['chat_messages_columns'] = [
            {'name': row[0], 'type': row[1]} 
            for row in cursor.fetchall()
        ]
        
        # 6. Messages by phone
        cursor.execute("""
            SELECT wa_phone_number, COUNT(*) 
            FROM chat_messages 
            GROUP BY wa_phone_number
            ORDER BY COUNT(*) DESC
        """)
        results['messages_by_phone'] = [
            {'phone': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
        # 7. Recent messages
        cursor.execute("""
            SELECT wa_phone_number, role, LEFT(content, 50)
            FROM chat_messages 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        results['recent_messages'] = [
            {'phone': row[0], 'role': row[1], 'content': row[2]}
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "database_inspection": results
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)