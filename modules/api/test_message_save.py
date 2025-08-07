#!/usr/bin/env python3
"""
Test message saving for Edi Kante
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg2
import os
import urllib.parse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["test"])

@router.get("/save-edi-message")
async def test_save_edi_message():
    """Test saving a message for Edi Kante"""
    
    # Get from environment or use defaults (same as config.py)
    db_host = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
    db_name = os.getenv('DB_NAME', 'postgres')  
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'j2D8J4LH:~eFrUz>$:kkNT(P$Rq_')
    db_port = os.getenv('DB_PORT', '5432')
    
    # URL encode the password for special characters
    password_encoded = urllib.parse.quote_plus(db_password)
    DB_URL = f"postgresql://{db_user}:{password_encoded}@{db_host}:{db_port}/{db_name}"
    
    results = {}
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Test 1: Try to save with Edi's WhatsApp number
        test_message = f"Test message from Edi at {datetime.now()}"
        wa_phone = "+393484446808"
        
        try:
            cursor.execute("""
                INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                VALUES (%s, %s, %s, NOW())
                RETURNING id
            """, (wa_phone, 'user', test_message))
            
            msg_id = cursor.fetchone()[0]
            conn.commit()
            results['test1_direct_whatsapp'] = {
                'success': True,
                'message_id': msg_id,
                'wa_phone': wa_phone
            }
        except Exception as e:
            conn.rollback()
            results['test1_direct_whatsapp'] = {
                'success': False,
                'error': str(e),
                'wa_phone': wa_phone
            }
        
        # Test 2: Try with +farmer_49 format
        wa_phone2 = "+farmer_49"
        test_message2 = f"Test message with farmer_49 format at {datetime.now()}"
        
        try:
            cursor.execute("""
                INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                VALUES (%s, %s, %s, NOW())
                RETURNING id
            """, (wa_phone2, 'user', test_message2))
            
            msg_id = cursor.fetchone()[0]
            conn.commit()
            results['test2_farmer_format'] = {
                'success': True,
                'message_id': msg_id,
                'wa_phone': wa_phone2
            }
        except Exception as e:
            conn.rollback()
            results['test2_farmer_format'] = {
                'success': False,
                'error': str(e),
                'wa_phone': wa_phone2
            }
        
        # Test 3: Check what execute_simple_query would do
        from modules.core.simple_db import execute_simple_query
        
        test_message3 = f"Test via execute_simple_query at {datetime.now()}"
        try:
            result = execute_simple_query("""
                INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                VALUES (%s, %s, %s, NOW())
                RETURNING id
            """, ("+393484446808", 'user', test_message3))
            
            results['test3_simple_db'] = {
                'success': result.get('success', False),
                'result': result
            }
        except Exception as e:
            results['test3_simple_db'] = {
                'success': False,
                'error': str(e)
            }
        
        # Now count messages for Edi
        cursor.execute("""
            SELECT wa_phone_number, COUNT(*) 
            FROM chat_messages 
            WHERE wa_phone_number IN ('+393484446808', '+farmer_49', '393484446808')
            GROUP BY wa_phone_number
        """)
        results['message_counts_after_test'] = {
            row[0]: row[1] for row in cursor.fetchall()
        }
        
        cursor.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "test_results": results
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)