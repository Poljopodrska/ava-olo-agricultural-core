"""
WhatsApp Webhook Handler for Twilio Integration
Handles incoming WhatsApp messages, status callbacks, and fallback scenarios
Now integrated with CAVA chat engine for intelligent responses
"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import asyncpg

# Try to import Twilio, but don't fail if it's not available
try:
    from twilio.request_validator import RequestValidator
    from twilio.twiml.messaging_response import MessagingResponse
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class RequestValidator:
        def __init__(self, *args, **kwargs):
            pass
        def validate(self, *args, **kwargs):
            return True
    
    class MessagingResponse:
        def __init__(self):
            self.body = ""
        def message(self, body=""):
            self.body = body
            return self
        def __str__(self):
            return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message><Body>{self.body}</Body></Message></Response>'

logger = logging.getLogger(__name__)

# Log Twilio availability status
if not TWILIO_AVAILABLE:
    logger.error("Twilio library not available - WhatsApp webhook will have limited functionality")

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

# Get environment variables
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
BASE_URL = os.getenv('BASE_URL', 'http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com')


async def get_or_create_farmer_by_phone(phone_number: str) -> Dict[str, Any]:
    """Get farmer by phone number or create a new one"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # First try to find farmer by WhatsApp phone
            farmer = await conn.fetchrow("""
                SELECT id, manager_name, farm_name, city 
                FROM farmers 
                WHERE wa_phone_number = $1 OR phone = $1
                LIMIT 1
            """, phone_number)
            
            if farmer:
                logger.info(f"Found existing farmer {farmer['id']} for phone {phone_number}")
                return dict(farmer)
            
            # If not found, create a basic farmer record
            logger.info(f"Creating new farmer for phone {phone_number}")
            new_farmer_id = await conn.fetchval("""
                INSERT INTO farmers (wa_phone_number, phone, manager_name, farm_name, city)
                VALUES ($1, $1, 'WhatsApp User', 'Farm', 'Unknown')
                ON CONFLICT (wa_phone_number) DO UPDATE
                SET phone = EXCLUDED.phone
                RETURNING id
            """, phone_number)
            
            return {
                'id': new_farmer_id,
                'manager_name': 'WhatsApp User',
                'farm_name': 'Farm',
                'city': 'Unknown'
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Database error in get_or_create_farmer: {e}")
        # Return a temporary farmer object
        return {
            'id': 0,
            'manager_name': 'WhatsApp User',
            'farm_name': 'Farm',
            'city': 'Unknown'
        }


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Main WhatsApp webhook endpoint"""
    if not TWILIO_AVAILABLE:
        logger.error("Twilio not available - webhook cannot process messages")
        return Response(content="Twilio not configured", status_code=503)
    
    try:
        # Get form data
        form_data = await request.form()
        
        # Log all incoming data for debugging
        logger.info(f"WhatsApp webhook received: {dict(form_data)}")
        
        # Validate Twilio signature if in production
        if os.getenv('ENVIRONMENT') == 'production' and TWILIO_AUTH_TOKEN:
            validator = RequestValidator(TWILIO_AUTH_TOKEN)
            
            # Get the request URL
            url = str(request.url)
            
            # Get signature from headers
            signature = request.headers.get('X-Twilio-Signature', '')
            
            # Validate
            if not validator.validate(url, dict(form_data), signature):
                logger.warning("Invalid Twilio signature")
                return Response(status_code=403)
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        to_number = form_data.get('To', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '')
        message_sid = form_data.get('MessageSid', '')
        
        # Get or create farmer
        farmer = await get_or_create_farmer_by_phone(from_number)
        
        # Process message through CAVA
        try:
            # Import CAVA here to avoid circular imports
            from modules.cava.true_cava_registration import process_whatsapp_message
            
            response = await process_whatsapp_message(
                farmer_id=farmer['id'],
                message=message_body,
                phone_number=from_number
            )
        except ImportError:
            logger.error("CAVA module not available")
            response = "🌾 Welcome to AVA OLO! Our agricultural assistant is temporarily unavailable. Please try again later."
        except Exception as e:
            logger.error(f"Error processing CAVA message: {e}")
            response = "🌾 I apologize, but I'm having trouble processing your message. Please try again."
        
        # Create Twilio response
        resp = MessagingResponse()
        resp.message(response)
        
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        # Return a basic response to prevent Twilio from retrying
        resp = MessagingResponse()
        resp.message("🌾 System temporarily unavailable. Please try again later.")
        return Response(content=str(resp), media_type="application/xml")


@router.post("/status")
async def whatsapp_status(request: Request):
    """Handle WhatsApp message status callbacks"""
    try:
        form_data = await request.form()
        logger.info(f"WhatsApp status callback: {dict(form_data)}")
        
        # Extract status details
        message_sid = form_data.get('MessageSid', '')
        message_status = form_data.get('MessageStatus', '')
        
        # Log status changes
        logger.info(f"Message {message_sid} status: {message_status}")
        
        # You can add database updates here to track message delivery
        
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"WhatsApp status callback error: {e}")
        return Response(status_code=200)  # Always return 200 to prevent retries


@router.get("/health")
async def whatsapp_health():
    """Health check for WhatsApp integration"""
    return {
        "status": "healthy" if TWILIO_AVAILABLE else "degraded",
        "twilio_available": TWILIO_AVAILABLE,
        "twilio_configured": bool(TWILIO_AUTH_TOKEN),
        "database_url": bool(DATABASE_URL),
        "timestamp": datetime.now().isoformat()
    }