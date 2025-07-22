#!/usr/bin/env python3
"""
Registration Chat with Memory & State Tracking - Phase 2
Enhances existing registration chat with conversation memory and progress tracking
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from modules.chat.openai_chat import get_openai_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["registration-memory"])

class RegistrationState:
    """Track registration conversation state"""
    def __init__(self):
        self.messages: List[Dict] = []
        self.collected_data = {
            "first_name": None,
            "last_name": None,
            "whatsapp": None
        }
        self.completed = False
        self.created_at = datetime.now().isoformat()
        
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_collected_data(self, data: Dict):
        """Update collected registration data"""
        for key, value in data.items():
            if key in self.collected_data and value:
                self.collected_data[key] = value
    
    def check_completion(self) -> bool:
        """Check if all required data is collected"""
        self.completed = all(self.collected_data.values())
        return self.completed
    
    def get_progress_percentage(self) -> int:
        """Get completion percentage"""
        collected = sum(1 for v in self.collected_data.values() if v)
        return int((collected / len(self.collected_data)) * 100)

class ChatMessage(BaseModel):
    """Chat message model"""
    content: str

class ChatResponse(BaseModel):
    """Enhanced chat response with state tracking"""
    response: str
    timestamp: str
    model: str
    connected: bool = True
    collected_data: Dict = {}
    completed: bool = False
    progress_percentage: int = 0

# In-memory storage for registration sessions
registration_sessions: Dict[str, RegistrationState] = {}

async def extract_registration_data(messages: List[Dict]) -> Dict:
    """Use LLM to extract registration data from conversation"""
    chat_service = get_openai_chat()
    
    if not chat_service.api_key:
        return {}
    
    # Format conversation for extraction
    conversation_text = ""
    for msg in messages[-10:]:  # Last 10 messages for context
        role = msg.get("role", "")
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n"
    
    extraction_prompt = f"""From this registration conversation, extract ONLY the following information:
- first_name: person's first name only (not full name)
- last_name: person's last name/surname only  
- whatsapp: phone number (with or without country code)

Return ONLY a JSON object with these exact fields. Use null for missing values.
Be very precise - only extract if clearly stated.

Conversation:
{conversation_text}

Extract as JSON:"""
    
    try:
        # Create minimal context for extraction
        extraction_context = {
            "purpose": "data_extraction",
            "fields_needed": ["first_name", "last_name", "whatsapp"],
            "instructions": "Extract registration data from conversation and return as JSON only.",
            "local_time": datetime.now().strftime("%H:%M"),
            "local_date": datetime.now().strftime("%B %d, %Y")
        }
        
        # Use a separate session for extraction to avoid contaminating conversation
        extraction_session = f"extract_{uuid.uuid4()}"
        
        response = await chat_service.send_message(
            extraction_session,
            extraction_prompt,
            extraction_context
        )
        
        # Clean up extraction session
        if extraction_session in chat_service.conversations:
            del chat_service.conversations[extraction_session]
        
        # Parse JSON response
        response_text = response.get("response", "{}")
        
        # Try to extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            extracted_data = json.loads(json_text)
            
            # Validate and clean extracted data
            clean_data = {}
            for key in ["first_name", "last_name", "whatsapp"]:
                value = extracted_data.get(key)
                if value and isinstance(value, str) and value.strip() and value.lower() != "null":
                    clean_data[key] = value.strip()
                    
            return clean_data
            
    except Exception as e:
        logger.warning(f"Data extraction error: {e}")
    
    return {}

def create_registration_prompt(state: RegistrationState, message: str) -> str:
    """Create context-aware prompt for registration conversation"""
    
    # Format conversation history
    history_text = ""
    if state.messages:
        for msg in state.messages[-8:]:  # Last 8 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
    
    # Show what's been collected
    collected_status = []
    for field, value in state.collected_data.items():
        status = "✅ COLLECTED" if value else "❌ MISSING"
        collected_status.append(f"- {field.replace('_', ' ').title()}: {status}")
    
    status_text = "\n".join(collected_status)
    
    prompt = f"""You are AVA, a friendly registration assistant helping a farmer sign up for AVA OLO.

CURRENT REGISTRATION STATUS:
{status_text}

CONVERSATION HISTORY:
{history_text}

USER'S LATEST MESSAGE: "{message}"

YOUR ROLE:
- Have a natural, friendly conversation
- Collect missing information: first name, last name, and WhatsApp number
- Acknowledge what they've told you previously (use their name if you know it)
- Don't repeat questions for information you already have
- If they share unrelated topics, acknowledge them briefly then guide back to registration
- Be conversational and helpful, not robotic

RESPOND NATURALLY:"""

    return prompt

@router.post("/registration/message")
async def send_registration_message_with_memory(request: Request, message: ChatMessage):
    """Enhanced registration chat with memory and state tracking"""
    try:
        # Get or create session ID
        session_id = request.cookies.get("chat_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get or create registration state
        if session_id not in registration_sessions:
            registration_sessions[session_id] = RegistrationState()
        
        state = registration_sessions[session_id]
        
        # Add user message to state
        state.add_message("user", message.content)
        
        # Create context-aware prompt
        registration_prompt = create_registration_prompt(state, message.content)
        
        # Get chat service
        chat_service = get_openai_chat()
        
        # Create registration context
        registration_context = {
            "purpose": "registration_with_memory",
            "fields_needed": ["first_name", "last_name", "whatsapp"],
            "instructions": "Natural conversation for registration with memory of previous messages",
            "local_time": datetime.now().strftime("%H:%M"),
            "local_date": datetime.now().strftime("%B %d, %Y"),
            "conversation_history": state.messages[-5:]  # Recent context
        }
        
        # Send to LLM - use registration-specific session to maintain conversation
        response_data = await chat_service.send_message(
            f"reg_{session_id}",  # Separate namespace for registration
            registration_prompt,
            registration_context
        )
        
        # Add assistant response to state
        assistant_response = response_data.get("response", "I'm here to help you register.")
        state.add_message("assistant", assistant_response)
        
        # Extract data from conversation
        extracted_data = await extract_registration_data(state.messages)
        
        # Update collected data
        state.update_collected_data(extracted_data)
        
        # Check if registration is complete
        is_complete = state.check_completion()
        progress = state.get_progress_percentage()
        
        # Log progress for debugging
        logger.info(f"Session {session_id}: Progress {progress}%, Collected: {state.collected_data}")
        
        # Create enhanced response
        response_json = {
            "response": assistant_response,
            "timestamp": datetime.now().isoformat(),
            "model": response_data.get("model", "gpt-4"),
            "connected": response_data.get("connected", True),
            "collected_data": state.collected_data,
            "completed": is_complete,
            "progress_percentage": progress
        }
        
        # Create response with session cookie
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=response_json)
        response.set_cookie(
            key="chat_session_id",
            value=session_id,
            httponly=True,
            max_age=86400  # 24 hours
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Registration memory chat error: {e}")
        return {
            "response": "I'm having trouble connecting. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "model": "error",
            "connected": False,
            "collected_data": {},
            "completed": False,
            "progress_percentage": 0
        }

@router.get("/registration/status")
async def registration_status_with_memory():
    """Get registration chat status with memory info"""
    try:
        chat_service = get_openai_chat()
        
        return {
            "status": "healthy",
            "connected": bool(chat_service.api_key),
            "has_api_key": bool(chat_service.api_key),
            "api_key_prefix": chat_service.api_key[:8] + "..." if chat_service.api_key else "Not configured",
            "model": chat_service.model,
            "active_sessions": len(registration_sessions),
            "features": {
                "memory": True,
                "state_tracking": True,
                "progress_indicators": True,
                "data_extraction": True
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "has_api_key": False,
            "api_key_prefix": "Error",
            "model": "none",
            "active_sessions": 0,
            "error": str(e)
        }

@router.get("/registration/session/{session_id}")
async def get_registration_session(session_id: str):
    """Get registration session state for debugging"""
    if session_id in registration_sessions:
        state = registration_sessions[session_id]
        return {
            "session_id": session_id,
            "collected_data": state.collected_data,
            "completed": state.completed,
            "progress_percentage": state.get_progress_percentage(),
            "message_count": len(state.messages),
            "created_at": state.created_at
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")