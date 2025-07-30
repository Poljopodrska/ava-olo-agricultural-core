"""WhatsApp webhook handler for Twilio integration"""
import os
import logging
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, Form
from fastapi.responses import PlainTextResponse
import aiohttp
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])


class TwilioWhatsAppHandler:
    """Handle WhatsApp messages via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "+38591857451")
        self.enabled = os.getenv("TWILIO_ENABLED", "false").lower() == "true"
        self.base_url = os.getenv("BASE_URL", "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com")
        
    def validate_twilio_signature(self, request_url: str, post_data: Dict[str, str], signature: str) -> bool:
        """Validate Twilio webhook signature"""
        if not self.auth_token:
            logger.warning("No auth token configured, skipping signature validation")
            return True
            
        # Construct the validation string
        s = request_url
        if post_data:
            for k in sorted(post_data.keys()):
                s += k + post_data[k]
        
        # Calculate expected signature
        mac = hmac.new(
            self.auth_token.encode('utf-8'),
            s.encode('utf-8'),
            hashlib.sha1
        )
        expected = mac.digest().hex()
        
        # Compare signatures
        return hmac.compare_digest(expected, signature)
    
    async def send_whatsapp_message(self, to_number: str, message: str) -> bool:
        """Send WhatsApp message via Twilio"""
        if not self.enabled:
            logger.warning("Twilio WhatsApp is not enabled")
            return False
            
        if not (self.account_sid and self.auth_token):
            logger.error("Twilio credentials not configured")
            return False
        
        # Ensure phone number is in WhatsApp format
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        from_number = f"whatsapp:{self.phone_number}"
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
        data = {
            "From": from_number,
            "To": to_number,
            "Body": message
        }
        
        try:
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(url, data=data) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        logger.info(f"Message sent successfully: {result['sid']}")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to send message: {resp.status} - {error}")
                        return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    async def process_incoming_message(self, message_data: Dict[str, str]) -> str:
        """Process incoming WhatsApp message"""
        # Extract message details
        from_number = message_data.get("From", "").replace("whatsapp:", "")
        message_body = message_data.get("Body", "")
        message_sid = message_data.get("MessageSid", "")
        
        logger.info(f"Processing WhatsApp message from {from_number}: {message_body[:50]}...")
        
        # Store message in database
        try:
            conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            await conn.execute("""
                INSERT INTO whatsapp_messages (
                    message_sid, from_number, message_body, received_at
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (message_sid) DO NOTHING
            """, message_sid, from_number, message_body, datetime.utcnow())
            await conn.close()
        except Exception as e:
            logger.error(f"Failed to store message in database: {e}")
        
        # Get intelligent response from CAVA
        response = await self.get_cava_response(from_number, message_body)
        
        return response
    
    async def get_cava_response(self, phone_number: str, message: str) -> str:
        """Get response from CAVA system"""
        # For now, return a simple acknowledgment
        # This will be integrated with CAVA registration engine
        
        # Detect language (simple check for Bulgarian/Croatian)
        if any(char in message for char in "чшщъьюя"):
            # Bulgarian detected
            return "Благодаря за съобщението! AVA OLO получи вашето запитване и скоро ще ви отговори. 🌱"
        else:
            # Default to Croatian
            return "Hvala na poruci! AVA OLO je primila vašu poruku i uskoro će vam odgovoriti. 🌱"


# Initialize handler
whatsapp_handler = TwilioWhatsAppHandler()


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Twilio webhook verification endpoint"""
    # Twilio sends a GET request to verify the webhook URL
    # We just need to respond with 200 OK
    return PlainTextResponse("Webhook verified", status_code=200)


@router.post("/webhook")
async def receive_whatsapp_message(
    request: Request,
    MessageSid: str = Form(None),
    From: str = Form(None),
    Body: str = Form(None),
    To: str = Form(None),
    NumMedia: str = Form("0")
):
    """Receive WhatsApp messages from Twilio"""
    try:
        # Get form data for signature validation
        form_data = await request.form()
        post_data = {k: v for k, v in form_data.items()}
        
        # Validate Twilio signature (optional but recommended)
        signature = request.headers.get("X-Twilio-Signature", "")
        request_url = str(request.url)
        
        # Log incoming webhook
        logger.info(f"WhatsApp webhook called: {MessageSid} from {From}")
        
        if not MessageSid or not From:
            logger.warning("Missing required fields in webhook request")
            return Response(status_code=400)
        
        # Process the message
        response_text = await whatsapp_handler.process_incoming_message(post_data)
        
        # Send response back via Twilio
        if response_text:
            success = await whatsapp_handler.send_whatsapp_message(From, response_text)
            if not success:
                logger.error("Failed to send response message")
        
        # Return 200 OK to acknowledge receipt
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}", exc_info=True)
        return Response(status_code=500)


@router.post("/fallback")
async def fallback_webhook(request: Request):
    """Fallback webhook for failed message delivery"""
    try:
        data = await request.form()
        logger.warning(f"WhatsApp fallback triggered: {dict(data)}")
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Fallback webhook error: {e}")
        return Response(status_code=500)


@router.post("/status")
async def status_callback(request: Request):
    """Status callback for message delivery updates"""
    try:
        data = await request.form()
        message_sid = data.get("MessageSid")
        message_status = data.get("MessageStatus")
        
        logger.info(f"WhatsApp status update: {message_sid} - {message_status}")
        
        # Update message status in database if needed
        if message_sid and message_status:
            try:
                conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
                await conn.execute("""
                    UPDATE whatsapp_messages 
                    SET status = $1, updated_at = $2 
                    WHERE message_sid = $3
                """, message_status, datetime.utcnow(), message_sid)
                await conn.close()
            except Exception as e:
                logger.error(f"Failed to update message status: {e}")
        
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Status callback error: {e}")
        return Response(status_code=500)


@router.get("/config")
async def get_whatsapp_config():
    """Get WhatsApp configuration and webhook URLs"""
    base_url = whatsapp_handler.base_url
    
    return {
        "enabled": whatsapp_handler.enabled,
        "phone_number": whatsapp_handler.phone_number,
        "webhook_urls": {
            "primary": f"{base_url}/api/v1/whatsapp/webhook",
            "fallback": f"{base_url}/api/v1/whatsapp/fallback",
            "status": f"{base_url}/api/v1/whatsapp/status"
        },
        "configuration_status": {
            "credentials_configured": bool(whatsapp_handler.account_sid and whatsapp_handler.auth_token),
            "base_url_configured": bool(base_url),
            "phone_number_configured": bool(whatsapp_handler.phone_number)
        },
        "instructions": {
            "twilio_console": "Configure these webhook URLs in your Twilio WhatsApp sandbox or production number",
            "primary_webhook": "Set as the 'When a message comes in' webhook",
            "fallback_webhook": "Set as the 'Primary handler fails' webhook",
            "status_webhook": "Set as the 'Status callback URL' for delivery receipts"
        }
    }


@router.get("/health")
async def whatsapp_health_check():
    """Check WhatsApp integration health"""
    health_status = {
        "service": "whatsapp",
        "status": "healthy",
        "enabled": whatsapp_handler.enabled,
        "checks": {
            "credentials": bool(whatsapp_handler.account_sid and whatsapp_handler.auth_token),
            "phone_number": bool(whatsapp_handler.phone_number),
            "base_url": bool(whatsapp_handler.base_url)
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Determine overall health
    if not whatsapp_handler.enabled:
        health_status["status"] = "disabled"
    elif not all(health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status


@router.post("/test-send")
async def test_send_message(phone_number: str, message: str = "Test message from AVA OLO"):
    """Test endpoint to send a WhatsApp message"""
    if not whatsapp_handler.enabled:
        raise HTTPException(status_code=503, detail="WhatsApp integration is disabled")
    
    success = await whatsapp_handler.send_whatsapp_message(phone_number, message)
    
    if success:
        return {"success": True, "message": "Message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


# Diagnostic endpoint
@router.get("/diagnostic")
async def run_diagnostic():
    """Run WhatsApp diagnostic and return results"""
    from modules.whatsapp_diagnostics.whatsapp_diagnostic import WhatsAppDiagnostic
    
    diagnostic = WhatsAppDiagnostic()
    
    # Run basic checks
    await diagnostic.test_webhook_accessibility()
    diagnostic.check_credentials_configured()
    
    return {
        "diagnostic_results": diagnostic.test_results,
        "recommendations": diagnostic.generate_diagnostic_report()
    }