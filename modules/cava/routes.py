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
import re

from modules.cava.registration_flow import RegistrationFlow
from modules.cava.natural_registration import NaturalRegistrationFlow
from modules.cava.true_cava_registration import TrueCAVARegistration
from modules.cava.simple_chat import SimpleRegistrationChat
from modules.cava.pure_chat import PureChat
from modules.cava.enhanced_cava_registration import EnhancedCAVARegistration
from modules.cava.cava_registration_engine import get_cava_registration_engine
from modules.auth.routes import create_farmer_account, get_password_hash

# Import the WORKING LLM client from main chat
from modules.chat.openai_key_manager import get_openai_client

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

# Registration sessions storage (in-memory for now)
registration_sessions = {}

def detect_question_type(llm_response: str) -> str:
    """Detect what the LLM is asking for based on its response"""
    response_lower = llm_response.lower()
    
    if "first name" in response_lower or "what's your name" in response_lower or "called" in response_lower:
        return "first_name"
    elif "last name" in response_lower or "surname" in response_lower or "family name" in response_lower:
        return "last_name"
    elif "whatsapp" in response_lower or "phone" in response_lower or "number" in response_lower:
        return "whatsapp"
    elif "password" in response_lower:
        return "password"
    else:
        return "unknown"

def extract_registration_data(user_message: str, last_question_type: str = "", collected_data: Dict[str, str] = None) -> Dict[str, str]:
    """Extract registration data based on conversation flow and what was just asked"""
    if collected_data is None:
        collected_data = {}
    
    extracted = {}
    message = user_message.strip()
    
    # Simple single-word responses to specific questions
    if last_question_type == "first_name" and not collected_data.get('first_name'):
        # User likely gave their first name
        words = message.split()
        if len(words) == 1 and words[0][0].isupper():
            extracted['first_name'] = words[0].capitalize()
        elif len(words) <= 2 and message[0].isupper():
            # Handle "My name is Peter" or just "Peter"
            name_match = re.search(r'(?:my name is |i am |call me )?([A-Z][a-zA-ZÀ-ÿ]+)', message, re.IGNORECASE)
            if name_match:
                extracted['first_name'] = name_match.group(1).capitalize()
    
    elif last_question_type == "last_name" and not collected_data.get('last_name'):
        # User likely gave their last name
        words = message.split()
        if len(words) == 1 and words[0][0].isupper():
            extracted['last_name'] = words[0].capitalize()
        elif len(words) <= 2:
            # Handle various last name formats
            name_match = re.search(r'([A-Z][a-zA-ZÀ-ÿčšžđćž]+)', message, re.IGNORECASE)
            if name_match:
                extracted['last_name'] = name_match.group(1).capitalize()
    
    elif last_question_type == "whatsapp" and not collected_data.get('whatsapp'):
        # Extract phone number
        phone_patterns = [
            r'\+\d{1,4}\s?\d{6,14}',  # +country code
            r'\d{9,15}',  # Simple number
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, message.replace(' ', '').replace('-', ''))
            if match:
                phone = match.group()
                if not phone.startswith('+'):
                    phone = '+359' + phone.lstrip('0')  # Default to Bulgaria
                extracted['whatsapp'] = phone
                break
    
    elif last_question_type == "password" and not collected_data.get('password'):
        # Extract password
        words = message.split()
        for word in words:
            if len(word) >= 8:
                extracted['password'] = word
                break
    
    # Fallback: Try to extract from common patterns regardless of question type
    if not extracted:
        # Look for explicit statements
        patterns = [
            (r"my name is ([A-Z][a-zA-ZÀ-ÿ]+)", 'first_name'),
            (r"i am ([A-Z][a-zA-ZÀ-ÿ]+)", 'first_name'),
            (r"call me ([A-Z][a-zA-ZÀ-ÿ]+)", 'first_name'),
        ]
        
        for pattern, field_type in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and not collected_data.get(field_type):
                extracted[field_type] = match.group(1).capitalize()
                break
    
    return extracted

def is_registration_complete(collected_data: Dict[str, str]) -> bool:
    """Check if all required fields are collected"""
    required_fields = ['first_name', 'last_name', 'whatsapp', 'password']
    return all(field in collected_data and collected_data[field] for field in required_fields)

@router.post("/registration/cava")
async def cava_registration_chat(request: Request) -> JSONResponse:
    """Handle CAVA registration chat messages using WORKING LLM from main chat"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("farmer_id", "")  # Use farmer_id as session_id for compatibility
        language = data.get("language", "en")
        
        logger.info(f"🏛️ REGISTRATION LLM: message='{message}', session_id='{session_id}'")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="farmer_id is required")
        
        # Use the SAME working LLM client from main chat
        client = get_openai_client()
        
        if not client:
            logger.error("Could not create OpenAI client for registration")
            return JSONResponse(
                status_code=500,
                content={
                    "response": "Registration system is temporarily unavailable. Please try again later.",
                    "error": True,
                    "error_type": "llm_unavailable"
                }
            )
        
        # Get or create session
        session = registration_sessions.get(session_id, {
            "messages": [],
            "collected_data": {},
            "language": language,
            "last_question_type": "unknown"
        })
        
        # Build messages for registration context with smart memory tracking
        collected = session.get("collected_data", {})
        
        # Create checkmark status for system prompt
        status_first = '✅ ' + collected.get('first_name', '') if collected.get('first_name') else '❌ NOT YET'
        status_last = '✅ ' + collected.get('last_name', '') if collected.get('last_name') else '❌ NOT YET'
        status_whatsapp = '✅ ' + collected.get('whatsapp', '') if collected.get('whatsapp') else '❌ NOT YET'
        status_password = '✅ SET' if collected.get('password') else '❌ NOT YET'
        
        # Determine what to ask for next
        next_field = None
        if not collected.get('first_name'):
            next_field = "first name"
        elif not collected.get('last_name'):
            next_field = "last name"
        elif not collected.get('whatsapp'):
            next_field = "WhatsApp number with country code"
        elif not collected.get('password'):
            next_field = "password (minimum 8 characters)"
        
        system_content = f"""You are AVA's friendly registration assistant helping farmers register.

CURRENT STATUS:
- First name: {status_first}
- Last name: {status_last}
- WhatsApp: {status_whatsapp}
- Password: {status_password}

CRITICAL INSTRUCTIONS:
🚫 NEVER ask for fields marked with ✅ - they are already collected!
🎯 ONLY ask for the next missing field: {next_field if next_field else "ALL COMPLETE!"}

{f"You should ask for their {next_field} next." if next_field else "All fields collected! Complete the registration."}

RULES:
- Ask ONE question at a time
- Be warm and conversational
- For WhatsApp, require country code (+359, +386, etc.)
- If user asks off-topic questions, politely redirect to registration

Respond in {language} if possible."""

        messages = [{"role": "system", "content": system_content}]
        
        # Add recent conversation history
        for msg in session["messages"][-6:]:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            # Call OpenAI using GPT-3.5-turbo for cost savings (15x cheaper than GPT-4)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Changed from gpt-4 for cost optimization
                messages=messages,
                temperature=0.7,
                max_tokens=300  # Reduced for efficiency
            )
            
            llm_response = response.choices[0].message.content
            logger.info(f"✅ REGISTRATION LLM (GPT-3.5): {llm_response[:100]}...")
            
            # FIRST: Extract data from user input using previous question context
            last_question_type = session.get("last_question_type", "unknown")
            collected = session.get("collected_data", {})
            extracted_data = extract_registration_data(message, last_question_type, collected)
            
            # Update collected data with extracted information
            for field, value in extracted_data.items():
                if value and not collected.get(field):  # Only add if not already collected
                    collected[field] = value
                    logger.info(f"🎯 EXTRACTED {field}: {value} (was asking for: {last_question_type})")
            
            # SECOND: Detect what the LLM is now asking for (for next user response)
            current_question_type = detect_question_type(llm_response)
            
            # Update session with new data
            session["messages"].append({"role": "user", "content": message})
            session["messages"].append({"role": "assistant", "content": llm_response})
            session["collected_data"] = collected
            session["last_question_type"] = current_question_type
            
            logger.info(f"🔄 FLOW: Asked for {last_question_type} → Now asking for {current_question_type}")
            
            # Check if registration is complete
            is_complete = is_registration_complete(collected)
            
            # Save updated session
            registration_sessions[session_id] = session
            
            result = {
                "response": llm_response,
                "registration_complete": is_complete,
                "llm_used": True,
                "model_used": "gpt-3.5-turbo",
                "constitutional_compliance": True,
                "session_id": session_id,
                "collected_data": collected,
                "progress_percentage": (len([v for v in collected.values() if v]) / 4) * 100
            }
            
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"Registration LLM error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "response": "I'm having trouble processing that. Please try again.",
                    "error": True,
                    "error_type": "llm_processing_error"
                }
            )
        
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

@router.get("/registration/llm-test")
async def test_registration_llm():
    """Test if registration can use the same LLM as main chat"""
    try:
        client = get_openai_client()
        
        if not client:
            return {
                "test": "failed",
                "error": "Could not get OpenAI client",
                "same_as_chat": False
            }
        
        # Test with registration-like message
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a registration assistant. When someone says they want to register, ask for their first name."},
                {"role": "user", "content": "I want to register"}
            ],
            max_tokens=100
        )
        
        return {
            "test": "success",
            "response": response.choices[0].message.content,
            "model": "gpt-4",
            "same_as_chat": True,
            "client_source": "modules.chat.openai_key_manager"
        }
        
    except Exception as e:
        return {
            "test": "failed",
            "error": str(e),
            "same_as_chat": False
        }

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