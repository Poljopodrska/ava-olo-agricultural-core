#!/usr/bin/env python3
"""
Check Edi Kante's messages endpoint
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import urllib.parse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/edi-messages")
async def check_edi_messages():
    """Check all messages for Edi Kante"""
    
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
        
        # Check Edi's data
        cursor.execute("""
            SELECT id, manager_name, manager_last_name, 
                   whatsapp_number, wa_phone_number, email
            FROM farmers 
            WHERE id = 49
        """)
        edi = cursor.fetchone()
        
        if edi:
            results['edi_data'] = {
                'id': edi[0],
                'name': f"{edi[1]} {edi[2]}",
                'whatsapp_number': edi[3],
                'wa_phone_number': edi[4],
                'email': edi[5]
            }
            
            # Check messages for all possible phone formats
            possible_phones = [
                edi[3],  # whatsapp_number
                edi[4],  # wa_phone_number
                f"+farmer_49",  # Old format
                "+393484446808",  # Direct number
                "393484446808",  # Without +
            ]
            
            results['message_counts'] = {}
            results['recent_messages'] = {}
            
            for phone in possible_phones:
                if phone:
                    # Count messages
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM chat_messages 
                        WHERE wa_phone_number = %s
                    """, (phone,))
                    count = cursor.fetchone()[0]
                    results['message_counts'][phone] = count
                    
                    if count > 0:
                        # Get last 10 messages
                        cursor.execute("""
                            SELECT role, content, timestamp
                            FROM chat_messages 
                            WHERE wa_phone_number = %s
                            ORDER BY timestamp DESC
                            LIMIT 10
                        """, (phone,))
                        messages = cursor.fetchall()
                        results['recent_messages'][phone] = [
                            {
                                'role': msg[0],
                                'content': msg[1][:200],  # First 200 chars
                                'timestamp': msg[2].isoformat() if msg[2] else None
                            }
                            for msg in messages
                        ]
        
        # Get all unique phone numbers with messages
        cursor.execute("""
            SELECT wa_phone_number, COUNT(*) as msg_count
            FROM chat_messages 
            GROUP BY wa_phone_number
            ORDER BY msg_count DESC
            LIMIT 30
        """)
        results['all_phones_with_messages'] = [
            {'phone': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
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