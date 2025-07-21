#!/usr/bin/env python3
"""
CAVA API Routes
Handles conversational AI endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import logging

from modules.cava.registration_flow import RegistrationFlow
from modules.auth.routes import create_farmer_account, get_password_hash

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["cava"])

# Initialize registration flow manager
registration_flow = RegistrationFlow()

# Setup logging
logger = logging.getLogger(__name__)

@router.post("/registration/cava")
async def cava_registration_chat(request: Request) -> JSONResponse:
    """Handle CAVA registration chat messages"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        farmer_id = data.get("farmer_id", "")
        language = data.get("language", "en")
        
        if not farmer_id:
            raise HTTPException(status_code=400, detail="farmer_id is required")
        
        # Process message through registration flow
        result = await registration_flow.process_message(farmer_id, message)
        
        # If registration is complete, create the account
        if result.get("registration_complete") and "registration_data" in result:
            reg_data = result["registration_data"]
            
            try:
                # Create farmer account
                new_farmer_id = await create_farmer_account(
                    name=reg_data["name"],
                    whatsapp_number=reg_data["whatsapp_number"],
                    email=reg_data["email"],
                    password=reg_data["password"]
                )
                
                # Clear the session
                registration_flow.clear_session(farmer_id)
                
                # Add success info to result
                result["account_created"] = True
                result["farmer_id"] = new_farmer_id
                
            except HTTPException as e:
                # Handle duplicate account or other errors
                result["response"] = f"❌ {e.detail}\n\nPlease try with a different WhatsApp number or sign in if you already have an account."
                result["registration_complete"] = False
                result["error"] = True
            except Exception as e:
                logger.error(f"Error creating farmer account: {e}")
                result["response"] = "❌ There was an error creating your account. Please try again."
                result["registration_complete"] = False
                result["error"] = True
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble processing your message. Please try again.",
                "registration_complete": False,
                "error": True
            }
        )

@router.get("/registration/cava/session/{farmer_id}")
async def get_registration_session(farmer_id: str) -> JSONResponse:
    """Get current registration session status"""
    session_data = registration_flow.get_session_data(farmer_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active registration session"
        })
    
    # Don't expose password in response
    safe_data = {k: v for k, v in session_data.items() if k not in ["password", "confirm_password"]}
    
    return JSONResponse(content={
        "exists": True,
        "data": safe_data,
        "fields_collected": len(safe_data)
    })

@router.delete("/registration/cava/session/{farmer_id}")
async def clear_registration_session(farmer_id: str) -> JSONResponse:
    """Clear a registration session"""
    registration_flow.clear_session(farmer_id)
    
    return JSONResponse(content={
        "success": True,
        "message": "Registration session cleared"
    })