#!/usr/bin/env python3
"""
CAVA API Routes
Handles conversational AI endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import logging
import os

from modules.cava.registration_flow import RegistrationFlow
from modules.cava.natural_registration import NaturalRegistrationFlow
from modules.cava.true_cava_registration import TrueCAVARegistration
from modules.cava.simple_chat import SimpleRegistrationChat
from modules.cava.pure_chat import PureChat
from modules.cava.enhanced_cava_registration import EnhancedCAVARegistration
from modules.cava.cava_registration_engine import get_cava_registration_engine
from modules.auth.routes import create_farmer_account, get_password_hash

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["cava"])

# Initialize registration flow managers
registration_flow = RegistrationFlow()  # Keep old flow for compatibility
natural_registration = NaturalRegistrationFlow()  # New natural flow
true_cava = TrueCAVARegistration()  # True CAVA - no hardcoding
simple_chat = SimpleRegistrationChat()  # Step 1 - Simple chat only
pure_chat = PureChat()  # Pure chat - NO validation or hardcoding
enhanced_cava = EnhancedCAVARegistration()  # Enhanced CAVA with full validation

# Setup logging
logger = logging.getLogger(__name__)

@router.post("/registration/cava")
async def cava_registration_chat(request: Request) -> JSONResponse:
    """Handle CAVA registration chat messages - ALWAYS USE LLM (Constitutional Amendment #15)"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("farmer_id", "")  # Use farmer_id as session_id for compatibility
        language = data.get("language", "en")
        
        # CRITICAL DIAGNOSTIC LOGGING
        logger.critical(f"🚨 REGISTRATION ENDPOINT CALLED: message='{message}', session_id='{session_id}'")
        logger.critical(f"🔑 OPENAI_KEY_STATUS: exists={bool(os.getenv('OPENAI_API_KEY'))}, length={len(os.getenv('OPENAI_API_KEY', ''))}")
        logger.critical(f"📍 REQUEST_PATH: {request.url.path}")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="farmer_id is required")
        
        # Check if engine can be loaded
        try:
            logger.critical("🔧 ATTEMPTING TO LOAD CAVA ENGINE...")
            cava_engine = get_cava_registration_engine()
            logger.critical(f"✅ CAVA ENGINE LOADED: has_key={bool(cava_engine.api_key)}")
        except Exception as engine_error:
            logger.critical(f"❌ CAVA ENGINE FAILED TO LOAD: {str(engine_error)}")
            return JSONResponse(
                status_code=500,
                content={
                    "response": "Registration system not available. Please check configuration.",
                    "error": True,
                    "diagnostic": f"Engine load failed: {str(engine_error)}",
                    "openai_key_exists": bool(os.getenv("OPENAI_API_KEY"))
                }
            )
        
        # ALWAYS use pure LLM engine - CONSTITUTIONAL REQUIREMENT Amendment #15
        logger.info(f"🏛️ CONSTITUTIONAL: Processing registration via pure LLM for session {session_id}")
        
        try:
            result = await cava_engine.process_message(session_id, message)
            logger.critical(f"✅ LLM RESPONSE RECEIVED: llm_used={result.get('llm_used', False)}")
        except Exception as process_error:
            logger.critical(f"❌ LLM PROCESSING FAILED: {str(process_error)}")
            raise
        
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
                cava_engine = get_cava_registration_engine()
                if session_id in cava_engine.sessions:
                    del cava_engine.sessions[session_id]
                
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

@router.post("/registration/cava/natural")
async def natural_registration_chat(request: Request) -> JSONResponse:
    """Handle natural CAVA registration chat messages"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Process message through natural registration flow
        result = await natural_registration.process_message(session_id, message)
        
        # If registration is complete, prepare account creation data
        if result.get("registration_complete") and "collected_data" in result:
            collected = result["collected_data"]
            
            # Map collected fields to database fields
            registration_data = {
                "manager_name": collected.get("first_name", ""),
                "manager_last_name": collected.get("last_name", ""),
                "wa_phone_number": collected.get("whatsapp", "")
            }
            
            result["registration_data"] = registration_data
            # Note: Actual account creation should be done by the frontend
            # after user confirms and adds any additional required fields
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Natural CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble understanding. Could you please try again?",
                "registration_complete": False,
                "error": True,
                "error_message": str(e)
            }
        )

@router.get("/registration/cava/natural/session/{session_id}")
async def get_natural_registration_session(session_id: str) -> JSONResponse:
    """Get current natural registration session status"""
    session_data = natural_registration.get_session_data(session_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active registration session"
        })
    
    missing_fields = natural_registration.get_missing_fields(session_data)
    
    return JSONResponse(content={
        "exists": True,
        "collected_data": session_data,
        "missing_fields": missing_fields,
        "registration_complete": len(missing_fields) == 0
    })

@router.delete("/registration/cava/natural/session/{session_id}")
async def clear_natural_registration_session(session_id: str) -> JSONResponse:
    """Clear a natural registration session"""
    natural_registration.clear_session(session_id)
    
    return JSONResponse(content={
        "success": True,
        "message": "Natural registration session cleared"
    })

@router.post("/registration/cava/true")
async def true_cava_registration(request: Request) -> JSONResponse:
    """Handle TRUE CAVA registration - pure LLM conversation"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Process message through true CAVA
        result = await true_cava.process_message(session_id, message)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"True CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble understanding. Could you please try again?",
                "registration_complete": False,
                "error": True
            }
        )

@router.get("/registration/cava/true/session/{session_id}")
async def get_true_cava_session(session_id: str) -> JSONResponse:
    """Get true CAVA session status"""
    session_data = true_cava.get_session_data(session_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active session"
        })
    
    return JSONResponse(content={
        "exists": True,
        "collected_data": session_data,
        "registration_complete": all(session_data.values())
    })

@router.post("/registration/cava/enhanced")
async def enhanced_cava_registration(request: Request) -> JSONResponse:
    """Enhanced CAVA registration with full validation and language support"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Process message through enhanced CAVA
        result = await enhanced_cava.process_message(session_id, message)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Enhanced CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble understanding. Could you please try again?",
                "registration_complete": False,
                "error": True
            }
        )

@router.get("/registration/cava/enhanced/session/{session_id}")
async def get_enhanced_cava_session(session_id: str) -> JSONResponse:
    """Get enhanced CAVA session status"""
    session_data = enhanced_cava.get_session_data(session_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active session"
        })
    
    return JSONResponse(content={
        "exists": True,
        "session_data": session_data,
        "registration_complete": session_data.get("complete", False)
    })

@router.post("/registration/chat")
async def registration_chat(request: Request) -> JSONResponse:
    """Simple chat endpoint - Step 1 of CAVA registration"""
    try:
        data = await request.json()
        
        session_id = data.get("session_id", "")
        message = data.get("message", "").strip()
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Pure chat - NO validation or hardcoding
        result = await pure_chat.chat(session_id, message)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Registration chat error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "Sorry, I'm having trouble right now. Please try again.",
                "error": True
            }
        )

@router.get("/registration/debug")
async def debug_registration():
    """Debug endpoint to verify OpenAI API status - CONSTITUTIONAL REQUIREMENT"""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "openai_key_set": bool(openai_key),
        "key_prefix": openai_key[:10] if openai_key else None,
        "cava_mode": "llm" if openai_key else "fallback"
    }

@router.get("/registration/llm-status")
async def check_llm_status(request: Request):
    """DIAGNOSTIC: Check actual LLM engine status in production"""
    from modules.core.config import VERSION
    from datetime import datetime
    import sys
    
    # Check if engine is loaded
    engine_error = None
    try:
        from modules.cava.cava_registration_engine import get_cava_registration_engine
        engine_loaded = True
        try:
            engine = get_cava_registration_engine()
            engine_initialized = True
            engine_has_key = bool(engine.api_key)
        except Exception as e:
            engine_initialized = False
            engine_has_key = False
            engine_error = str(e)
    except Exception as e:
        engine_loaded = False
        engine_initialized = False
        engine_has_key = False
        engine_error = str(e)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "🚨_DIAGNOSTIC_REPORT": "LLM Registration Status",
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "endpoint_path": str(request.url.path),
        "environment": {
            "openai_key_exists": bool(openai_key),
            "key_first_chars": openai_key[:7] if openai_key else None,
            "key_length": len(openai_key) if openai_key else 0,
            "python_path": sys.path[:3]  # First 3 paths
        },
        "engine_status": {
            "cava_engine_module_loaded": engine_loaded,
            "cava_engine_initialized": engine_initialized,
            "engine_has_api_key": engine_has_key,
            "engine_error": engine_error if not engine_initialized else None
        },
        "routes_loaded": {
            "registration_cava": any(r.path == "/api/v1/registration/cava" for r in router.routes),
            "registration_debug": any(r.path == "/api/v1/registration/debug" for r in router.routes),
            "registration_llm_status": True  # This endpoint
        },
        "critical_check": "🟢 READY" if (openai_key and engine_initialized) else "🔴 NOT READY"
    }

@router.get("/registration/all-endpoints")
async def list_registration_endpoints():
    """DIAGNOSTIC: List all registration-related endpoints"""
    from main import app
    
    registration_endpoints = []
    for route in app.routes:
        if hasattr(route, 'path') and 'register' in str(route.path).lower():
            registration_endpoints.append({
                "path": str(route.path),
                "methods": list(route.methods) if hasattr(route, 'methods') else [],
                "name": route.name if hasattr(route, 'name') else None
            })
    
    return {
        "🔍_REGISTRATION_ENDPOINTS": "All endpoints containing 'register'",
        "endpoints": sorted(registration_endpoints, key=lambda x: x['path']),
        "total_count": len(registration_endpoints),
        "llm_endpoints": [
            "/api/v1/registration/cava",
            "/api/v1/chat/register",
            "/api/v1/registration/cava/enhanced"
        ],
        "diagnostic_endpoints": [
            "/api/v1/registration/debug",
            "/api/v1/registration/llm-status",
            "/api/v1/registration/all-endpoints"
        ]
    }