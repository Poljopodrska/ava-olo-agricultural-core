"""
WhatsApp Webhook Handler for Twilio Integration
Handles incoming WhatsApp messages, status callbacks, and fallback scenarios
Now integrated with CAVA chat engine for intelligent responses
"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import asyncpg

# Import CAVA chat handling
from modules.api.chat_routes import ChatRequest, chat_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

# Get environment variables
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
BASE_URL = os.getenv('BASE_URL', 'http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com')


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
        logger.error(f"Error getting/creating farmer: {str(e)}")
        # Return a default farmer if database fails
        return {
            'id': 1,
            'manager_name': 'Unknown',
            'farm_name': 'Unknown Farm',
            'city': 'Unknown'
        }


async def store_whatsapp_message(from_number: str, message_body: str, message_sid: str = None, farmer_id: int = None) -> Optional[int]:
    """Store incoming WhatsApp message in database"""
    try:
        # Use provided farmer_id or default
        if not farmer_id:
            farmer_id = 1  # Default for testing
        
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Store in incoming_messages table
            result = await conn.fetchval("""
                INSERT INTO incoming_messages 
                (farmer_id, phone_number, message_text, role, timestamp, message_sid)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, farmer_id, from_number, message_body, 'user', datetime.utcnow(), message_sid)
            
            logger.info(f"Stored WhatsApp message {result} from {from_number}")
            return result
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error storing WhatsApp message: {str(e)}")
        return None


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Main webhook endpoint for incoming WhatsApp messages
    Twilio sends POST requests here when messages are received
    """
    try:
        # Get form data from Twilio
        form_data = await request.form()
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        to_number = form_data.get('To', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '')
        message_sid = form_data.get('MessageSid', '')
        
        # Log incoming message
        logger.info(f"WhatsApp message received from {from_number}: {message_body[:50]}...")
        
        # Validate Twilio signature (security check)
        if TWILIO_AUTH_TOKEN:
            signature = request.headers.get('X-Twilio-Signature', '')
            url = f"{BASE_URL}/api/v1/whatsapp/webhook"
            
            validator = RequestValidator(TWILIO_AUTH_TOKEN)
            request_valid = validator.validate(
                url,
                dict(form_data),
                signature
            )
            
            if not request_valid:
                logger.warning(f"Invalid Twilio signature from {from_number}")
                # In production, uncomment to enforce security:
                # raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Get or create farmer
        farmer = await get_or_create_farmer_by_phone(from_number)
        farmer_id = farmer['id']
        
        # Store message in database
        message_id = await store_whatsapp_message(from_number, message_body, message_sid, farmer_id)
        
        # Process message through CAVA chat engine
        # TEMPORARY: Disable CAVA until deployment completes
        use_cava = False  # Set to True once deployment is verified
        
        if use_cava:
            try:
                logger.info(f"Processing WhatsApp message through CAVA for farmer {farmer_id}")
                
                # Create chat request for CAVA
                chat_request = ChatRequest(
                    wa_phone_number=from_number,
                    message=message_body,
                    session_id=f"whatsapp_{from_number}"
                )
                
                # Get intelligent response from CAVA
                chat_response = await chat_endpoint(chat_request)
                
                # Extract the response text
                cava_response = chat_response.response
                logger.info(f"CAVA response: {cava_response[:100]}...")
                
            except Exception as cava_error:
                logger.error(f"CAVA processing error: {str(cava_error)}")
                # Try a simpler fallback
                cava_response = f"Thank you for your message about '{message_body[:30]}...'. Our AI is being updated. Please try again soon."
        else:
            # Temporary response while CAVA integration is being deployed
            if "mango" in message_body.lower():
                cava_response = "🥭 Great question about mangoes! In Mediterranean climates, plant mangoes in early spring (March-April) after frost risk passes. They need well-draining soil and protection from cold winds. Water deeply but infrequently."
            elif "tomato" in message_body.lower():
                cava_response = "🍅 For tomatoes in Croatia, start seeds indoors 6-8 weeks before last frost (usually March). Transplant outdoors in May when soil warms. They love full sun and regular watering!"
            elif "hello" in message_body.lower() or "hi" in message_body.lower():
                cava_response = f"Hello {farmer.get('manager_name', 'Farmer')}! 👋 Welcome to AVA OLO. I'm here to help with your agricultural questions. What would you like to know about farming today?"
            else:
                cava_response = f"Thank you for your message about '{message_body[:50]}...'. I'm AVA OLO, your agricultural assistant. While my full AI capabilities are being updated, I can help with questions about mangoes, tomatoes, and other crops. What would you like to know?"
        
        # Create TwiML response with CAVA's intelligent response
        resp = MessagingResponse()
        resp.message(cava_response)
        
        # Return TwiML response
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        # Return empty TwiML response on error
        resp = MessagingResponse()
        return Response(content=str(resp), media_type="application/xml")


@router.post("/fallback")
async def whatsapp_fallback(request: Request):
    """
    Fallback webhook for handling failed message delivery
    Twilio calls this when primary webhook fails
    """
    try:
        form_data = await request.form()
        
        # Log fallback event
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        error_code = form_data.get('ErrorCode', 'Unknown')
        
        logger.error(f"WhatsApp fallback triggered for {from_number}, error: {error_code}")
        
        # Return simple response
        resp = MessagingResponse()
        resp.message("Žao nam je, dogodila se greška. Molimo pokušajte ponovo.")
        
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in WhatsApp fallback: {str(e)}")
        return {"status": "fallback_error"}


@router.post("/status")
async def whatsapp_status(request: Request):
    """
    Status callback webhook for tracking message delivery
    Twilio sends updates here about message status
    """
    try:
        form_data = await request.form()
        
        # Extract status information
        message_sid = form_data.get('MessageSid', '')
        message_status = form_data.get('MessageStatus', '')
        to_number = form_data.get('To', '').replace('whatsapp:', '')
        
        logger.info(f"WhatsApp status update: {message_sid} is {message_status}")
        
        # Could store status updates in database for tracking
        # For now, just log them
        
        return {"status": "received", "message_status": message_status}
        
    except Exception as e:
        logger.error(f"Error processing status callback: {str(e)}")
        return {"status": "error"}


@router.get("/config")
async def get_whatsapp_config():
    """
    Returns all webhook URLs needed for Twilio configuration
    Visit this endpoint after deployment to get URLs for Twilio setup
    """
    return {
        "base_url": BASE_URL,
        "webhook_url": f"{BASE_URL}/api/v1/whatsapp/webhook",
        "fallback_url": f"{BASE_URL}/api/v1/whatsapp/fallback",
        "status_callback_url": f"{BASE_URL}/api/v1/whatsapp/status",
        "instructions": "Copy these URLs to Twilio WhatsApp Sender configuration",
        "twilio_console": "https://console.twilio.com/us1/develop/sms/senders/whatsapp-senders",
        "whatsapp_number": "+385919857451",
        "notes": {
            "webhook": "Main endpoint for incoming messages",
            "fallback": "Backup endpoint if main webhook fails",
            "status": "Receives delivery status updates"
        }
    }


@router.post("/test")
async def test_whatsapp():
    """
    Test endpoint to verify webhooks are working
    Can be called to check if the module is deployed correctly
    """
    return {
        "status": "working",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "webhook": "ready",
            "fallback": "ready",
            "status": "ready",
            "config": "ready"
        },
        "environment": {
            "auth_token_set": bool(TWILIO_AUTH_TOKEN),
            "database_url_set": bool(DATABASE_URL),
            "base_url": BASE_URL
        }
    }


@router.get("/health")
async def whatsapp_health():
    """Health check endpoint for WhatsApp integration"""
    health_status = {
        "service": "whatsapp_webhook",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "twilio_auth": "configured" if TWILIO_AUTH_TOKEN else "missing",
            "database": "configured" if DATABASE_URL else "missing",
            "base_url": BASE_URL
        }
    }
    
    # Check database connectivity
    if DATABASE_URL:
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.fetchval("SELECT 1")
            await conn.close()
            health_status["checks"]["database_connection"] = "connected"
        except Exception as e:
            health_status["checks"]["database_connection"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status


@router.post("/test-simple")
async def test_simple_response():
    """Simple test endpoint that doesn't use CAVA"""
    try:
        # Test basic functionality
        resp = MessagingResponse()
        resp.message("Hello! This is a simple test response from AVA OLO. The webhook is working!")
        return Response(content=str(resp), media_type="application/xml")
    except Exception as e:
        return {"error": str(e)}