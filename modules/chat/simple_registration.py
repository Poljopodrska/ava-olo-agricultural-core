#!/usr/bin/env python3
"""
Simple Registration Chat - Minimal code, maximum LLM
Let the LLM handle extraction and conversation flow
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
from modules.chat.openai_chat import get_openai_chat
from modules.core.database_manager import get_db_manager
import hashlib
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["registration-simple"])

class ChatRequest(BaseModel):
    """Simple chat request"""
    message: str
    session_id: Optional[str] = None

# Simple in-memory session storage
registration_sessions: Dict[str, Dict] = {}

def format_collected_fields(data: Dict) -> str:
    """Format what we already have - NEVER ask for these!"""
    collected = []
    fields = {
        'first_name': 'First Name',
        'last_name': 'Last Name', 
        'whatsapp': 'WhatsApp',
        'password': 'Password'
    }
    
    for key, label in fields.items():
        if data.get(key):
            collected.append(f"✅ {label}: {data[key]}")
    
    return "\n".join(collected) if collected else "Nothing collected yet"

def format_missing_fields(data: Dict) -> str:
    """Format what we still need - ONLY ask for these!"""
    missing = []
    fields = {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'whatsapp': 'WhatsApp Number',
        'password': 'Password'
    }
    
    for key, label in fields.items():
        if not data.get(key):
            missing.append(f"⏳ {label}")
    
    return "\n".join(missing) if missing else "Nothing - all complete!"

def get_next_missing_field_prompt(data: Dict) -> str:
    """Get prompt for next missing field only"""
    if not data.get('first_name'):
        return "What's your first name?"
    elif not data.get('last_name'):
        return "Thanks! What's your last name?"
    elif not data.get('whatsapp'):
        return "Great! What's your WhatsApp number?"
    elif not data.get('password'):
        return "Almost done! Please create a password."
    else:
        return "Perfect! Registration complete! 🎉"

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

async def save_farmer_to_db(data: Dict) -> int:
    """Save completed registration to database"""
    try:
        db_manager = get_db_manager()
        
        # Check if database is connected
        if not db_manager.test_connection():
            logger.warning("Database not connected, using mock farmer ID")
            return 99999  # Mock ID
        
        # Hash password before saving
        hashed_password = hash_password(data['password'])
        
        # Create farmer record
        query = """
        INSERT INTO farmers 
        (first_name, last_name, whatsapp_number, password_hash, created_at, is_active) 
        VALUES (%s, %s, %s, %s, %s, %s) 
        RETURNING farmer_id
        """
        
        result = db_manager.execute_query(
            query,
            (
                data['first_name'],
                data['last_name'],
                data['whatsapp'],
                hashed_password,
                datetime.now(),
                True
            )
        )
        
        if result and result.get('rows'):
            farmer_id = result['rows'][0][0]
            logger.info(f"Farmer registered with ID: {farmer_id}")
            return farmer_id
        else:
            logger.warning("No farmer ID returned, using mock ID")
            return 99999
            
    except Exception as e:
        logger.error(f"Error saving farmer: {e}")
        return 99999  # Return mock ID on error

@router.post("/register")
async def simple_registration_chat(request: ChatRequest):
    """One simple endpoint - let LLM do the work"""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        session = registration_sessions.get(session_id, {
            "messages": [],
            "data": {}
        })
        
        # Add user message
        session["messages"].append({
            "role": "user",
            "content": request.message
        })
        
        # Create CRYSTAL CLEAR prompt for LLM
        collected_info = format_collected_fields(session["data"])
        missing_info = format_missing_fields(session["data"])
        
        prompt = f"""You are helping with farmer registration.

✅ ALREADY HAVE (DO NOT ASK FOR THESE):
{collected_info}

⏳ STILL NEED (ONLY ASK FOR THESE):
{missing_info}

User just said: "{request.message}"

CRITICAL RULES:
1. NEVER ask for anything marked with ✅ above
2. ONLY ask for things marked with ⏳ above
3. If user provides data, acknowledge it and move to next ⏳ item
4. Be very brief (under 30 words)
5. If all complete, say "Perfect! Registration complete!"

Examples:
- If First Name ✅, NEVER say "what's your first name"
- If Last Name ⏳, you CAN ask "What's your last name?"
- If user says just "Peter", that's the first name
- If user says just "Knaflič", that's probably the last name

IMPORTANT: Respond with this exact JSON format:
{{
    "response": "your brief message (ONLY ask for ⏳ items)",
    "extracted_data": {{
        "first_name": "value if found",
        "last_name": "value if found", 
        "whatsapp": "value if found",
        "password": "value if found"
    }},
    "is_complete": true/false
}}

Remember: NEVER ask for ✅ items, ONLY ask for ⏳ items!
"""
        
        # Get LLM response
        chat_service = get_openai_chat()
        
        # Send as a system message to get JSON response
        llm_response = await chat_service.send_message(
            f"reg_{session_id}",
            prompt,
            {"location": "Registration", "fields": [], "weather": "N/A"}
        )
        
        # Parse LLM response
        try:
            # Extract JSON from response
            response_text = llm_response.get("response", "{}")
            
            # Try to parse as JSON
            result = json.loads(response_text)
            
            # Update session data with any new extracted data
            extracted = result.get("extracted_data", {})
            for key, value in extracted.items():
                if value and key in ["first_name", "last_name", "whatsapp", "password"]:
                    session["data"][key] = value
            
            # Safety check - override if LLM asks for collected data
            response_text = result.get("response", "")
            
            # Debug logging
            logger.info(f"Session {session_id}: Collected={collected_info}")
            logger.info(f"Session {session_id}: Missing={missing_info}")
            logger.info(f"Session {session_id}: LLM Response={response_text}")
            
            # Check if LLM is asking for something we already have
            if session["data"].get("first_name") and "first name" in response_text.lower():
                logger.warning(f"LLM asking for first name but we have: {session['data']['first_name']}")
                response_text = get_next_missing_field_prompt(session["data"])
                
            if session["data"].get("last_name") and "last name" in response_text.lower():
                logger.warning(f"LLM asking for last name but we have: {session['data']['last_name']}")
                response_text = get_next_missing_field_prompt(session["data"])
                
            if session["data"].get("whatsapp") and any(word in response_text.lower() for word in ["whatsapp", "phone", "number"]):
                logger.warning(f"LLM asking for phone but we have: {session['data']['whatsapp']}")
                response_text = get_next_missing_field_prompt(session["data"])
            
            # Add assistant response to history
            session["messages"].append({
                "role": "assistant",
                "content": response_text
            })
            
            # Check if complete
            required_fields = ["first_name", "last_name", "whatsapp", "password"]
            is_complete = all(session["data"].get(field) for field in required_fields)
            
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            logger.warning("LLM did not return valid JSON, using text response")
            result = {
                "response": response_text,
                "is_complete": False
            }
            
            session["messages"].append({
                "role": "assistant", 
                "content": response_text
            })
            
            is_complete = False
        
        # Handle completion
        if is_complete and not session.get("completed"):
            # Mark as completed
            session["completed"] = True
            
            # Save to database
            farmer_id = await save_farmer_to_db(session["data"])
            session["farmer_id"] = farmer_id
            
            # Create completion message with login instructions
            completion_message = f"""🎉 Perfect! Registration complete!

Your login credentials:
📱 Username: {session["data"]['whatsapp']}
🔒 Password: {session["data"]['password']}

You can now sign in to AVA OLO using your WhatsApp number as username."""
            
            # Override response with completion message
            response_text = completion_message
            show_app_button = True
        else:
            # Use the safety-checked response text (already set above)
            show_app_button = False
        
        # Save session
        registration_sessions[session_id] = session
        
        # Log for debugging
        logger.info(f"Session {session_id}: Data={session['data']}, Complete={is_complete}")
        
        # Return response
        return {
            "response": response_text,
            "session_id": session_id,
            "collected_data": session["data"],
            "completed": is_complete,
            "progress_percentage": len([v for v in session["data"].values() if v]) * 25,  # 4 fields = 25% each
            "show_app_button": show_app_button
        }
        
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return {
            "response": "I'm having trouble right now. Please try again.",
            "session_id": session_id,
            "collected_data": {},
            "completed": False,
            "progress_percentage": 0,
            "error": str(e)
        }

@router.get("/register/status")
async def registration_status():
    """Simple status check"""
    chat_service = get_openai_chat()
    
    return {
        "status": "healthy",
        "sessions_active": len(registration_sessions),
        "openai_connected": bool(chat_service.api_key),
        "endpoint": "/api/v1/chat/register"
    }

@router.get("/registration/debug")
async def debug_registration():
    """Debug endpoint to verify OpenAI API status - EXACT AS SPECIFIED"""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "openai_key_set": bool(openai_key),
        "key_prefix": openai_key[:10] if openai_key else None,
        "cava_mode": "llm" if openai_key else "fallback"
    }