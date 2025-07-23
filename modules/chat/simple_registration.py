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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["registration-simple"])

class ChatRequest(BaseModel):
    """Simple chat request"""
    message: str
    session_id: Optional[str] = None

# Simple in-memory session storage
registration_sessions: Dict[str, Dict] = {}

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
        
        # Create simple prompt for LLM
        prompt = f"""You are helping with farmer registration. 

Your task is to:
1. Collect these 4 pieces of information:
   - first_name
   - last_name  
   - whatsapp (phone number)
   - password (ask them to create a secure password)

2. Extract any data from the conversation
3. Respond naturally and briefly
4. Never ask for information you already have
5. If all 4 pieces collected, say "Perfect! Registration complete!"

Current conversation:
{json.dumps(session["messages"][-10:], indent=2)}

Data collected so far:
{json.dumps(session["data"], indent=2)}

IMPORTANT: Respond with this exact JSON format:
{{
    "response": "your brief message to the user",
    "extracted_data": {{
        "first_name": "value if found",
        "last_name": "value if found", 
        "whatsapp": "value if found",
        "password": "value if found"
    }},
    "is_complete": true/false
}}

Notes:
- Only include fields in extracted_data if you found new values
- Set is_complete to true when all 4 fields are collected
- Keep responses short and friendly
- If they provide a phone number, that's the whatsapp field
- For passwords, accept what they provide (don't enforce complexity)
- NEVER ask for anything after all 4 are collected
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
            
            # Add assistant response to history
            session["messages"].append({
                "role": "assistant",
                "content": result.get("response", "I'm here to help with registration.")
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
            response_text = result.get("response", "Hello! I'll help you register.")
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