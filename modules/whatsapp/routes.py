#!/usr/bin/env python3
"""
WhatsApp Routes for Twilio Integration
Handles Twilio webhook endpoints for WhatsApp messaging
"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
import logging

from modules.whatsapp.twilio_handler import get_whatsapp_handler

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...), 
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    NumMedia: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None)
):
    """
    Twilio WhatsApp webhook endpoint
    Receives incoming WhatsApp messages and processes them through CAVA
    
    Expected Twilio parameters:
    - From: sender's WhatsApp number (whatsapp:+1234567890)
    - To: our WhatsApp number (whatsapp:+1234567890)
    - Body: message content
    - MessageSid: Twilio message ID
    - NumMedia: number of media attachments (optional)
    """
    try:
        logger.info(f"=== TWILIO WHATSAPP WEBHOOK ===")
        logger.info(f"From: {From}")
        logger.info(f"To: {To}")
        logger.info(f"Body: {Body}")
        logger.info(f"MessageSid: {MessageSid}")
        logger.info(f"NumMedia: {NumMedia}")
        
        # Handle media attachments if present
        if NumMedia and int(NumMedia) > 0:
            logger.info(f"Media received: {MediaUrl0} (type: {MediaContentType0})")
            # For now, we'll acknowledge media but focus on text
            Body += f" [Media attachment: {MediaContentType0}]"
        
        # Get WhatsApp handler
        handler = get_whatsapp_handler()
        
        # Process the message
        response_message = await handler.handle_incoming_message(From, Body, MessageSid)
        
        # Create TwiML response
        twiml_response = handler.create_twiml_response(response_message)
        
        logger.info(f"Sending TwiML response: {twiml_response}")
        
        # Return TwiML response with correct content type
        return Response(
            content=twiml_response,
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {str(e)}")
        
        # Return error TwiML response
        from twilio.twiml.messaging_response import MessagingResponse
        response = MessagingResponse()
        response.message("I'm sorry, I encountered an error. Please try again later.")
        
        return Response(
            content=str(response),
            media_type="application/xml"
        )

@router.get("/webhook")
async def whatsapp_webhook_verification(request: Request):
    """
    Handle Twilio webhook verification (GET request)
    This is called by Twilio to verify the webhook URL
    """
    try:
        logger.info("WhatsApp webhook verification requested")
        
        # Twilio webhook verification - just return 200 OK
        return {"status": "webhook_verified", "message": "AVA OLO WhatsApp webhook is ready"}
        
    except Exception as e:
        logger.error(f"Error in webhook verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook verification failed")

@router.post("/send")
async def send_whatsapp_message(request: Request):
    """
    API endpoint to send WhatsApp messages programmatically
    Used for testing and administrative purposes
    """
    try:
        data = await request.json()
        
        to_number = data.get("to")
        message = data.get("message")
        
        if not to_number or not message:
            raise HTTPException(status_code=400, detail="Both 'to' and 'message' are required")
        
        handler = get_whatsapp_handler()
        success = await handler.send_whatsapp_message(to_number, message)
        
        if success:
            return {"success": True, "message": "WhatsApp message sent successfully"}
        else:
            return {"success": False, "error": "Failed to send WhatsApp message"}
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{phone_number}")
async def get_whatsapp_history(phone_number: str, limit: int = 50):
    """
    Get WhatsApp conversation history for a phone number
    """
    try:
        # Remove any prefixes and clean the phone number
        clean_number = phone_number.replace('whatsapp:', '').replace('+', '').replace('-', '').replace(' ', '')
        
        # Re-add the + prefix for database lookup
        if not clean_number.startswith('+'):
            clean_number = '+' + clean_number
        
        handler = get_whatsapp_handler()
        history = handler.get_conversation_history_sync(clean_number, limit)
        
        return {
            "success": True,
            "phone_number": clean_number,
            "conversation_count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error getting WhatsApp history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def whatsapp_status():
    """
    Check WhatsApp integration status
    """
    try:
        import os
        
        # Check configuration
        config_status = {
            "twilio_account_sid": bool(os.getenv('TWILIO_ACCOUNT_SID')),
            "twilio_auth_token": bool(os.getenv('TWILIO_AUTH_TOKEN')),
            "twilio_whatsapp_number": bool(os.getenv('TWILIO_WHATSAPP_NUMBER'))
        }
        
        all_configured = all(config_status.values())
        
        # Try to initialize handler if configured
        handler_status = "not_initialized"
        if all_configured:
            try:
                handler = get_whatsapp_handler()
                handler_status = "initialized"
            except Exception as e:
                handler_status = f"error: {str(e)}"
        
        return {
            "status": "ready" if all_configured and handler_status == "initialized" else "not_ready",
            "configuration": config_status,
            "handler": handler_status,
            "webhook_url": "/api/v1/whatsapp/webhook",
            "send_endpoint": "/api/v1/whatsapp/send"
        }
        
    except Exception as e:
        logger.error(f"Error checking WhatsApp status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }