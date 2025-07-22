#!/usr/bin/env python3
"""
Context-Aware Registration Chat - Phase 4
Enhances registration with farmer recognition and context awareness
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import uuid
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from modules.chat.openai_chat import get_openai_chat
from modules.farmers.context_search import (
    search_farmers_flexibly, 
    extract_search_criteria_from_message,
    get_farmer_details,
    format_farmer_matches
)
from modules.core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["registration-context"])

class EnhancedRegistrationState:
    """Registration state with farming context awareness"""
    def __init__(self):
        self.messages: List[Dict] = []
        self.collected_data = {
            "first_name": None,
            "last_name": None, 
            "whatsapp": None
        }
        self.completed = False
        self.created_at = datetime.now()
        
        # Context awareness
        self.recognized_farmer_id: Optional[int] = None
        self.potential_matches: List[Dict] = []
        self.farming_context: Dict = {}
        self.mentioned_crops: List[str] = []
        self.mentioned_locations: List[str] = []
        self.confidence_score: float = 0.0
        self.is_returning: bool = False
        self.incomplete_registration_id: Optional[str] = None
        
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
    
    def update_farming_context(self, message: str):
        """Extract and update farming context from message"""
        message_lower = message.lower()
        
        # Extract crops
        crop_keywords = [
            'corn', 'wheat', 'barley', 'potato', 'tomato', 'pepper', 'cucumber',
            'apple', 'pear', 'plum', 'grape', 'strawberry', 'raspberry',
            'lettuce', 'cabbage', 'carrot', 'onion', 'garlic',
            'sunflower', 'soybean', 'rapeseed', 'mango', 'mangoes', 'olive'
        ]
        
        for crop in crop_keywords:
            if crop in message_lower and crop not in self.mentioned_crops:
                self.mentioned_crops.append(crop)
        
        # Extract locations
        location_patterns = [
            r"from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"near\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for location in matches:
                if location not in self.mentioned_locations:
                    self.mentioned_locations.append(location)
        
        # Update farming context
        if self.mentioned_crops:
            self.farming_context['crops'] = self.mentioned_crops
        if self.mentioned_locations:
            self.farming_context['locations'] = self.mentioned_locations

class ChatMessage(BaseModel):
    """Chat message model"""
    content: str

class ContextAwareChatResponse(BaseModel):
    """Enhanced chat response with context"""
    response: str
    timestamp: str
    model: str
    connected: bool = True
    collected_data: Dict = {}
    completed: bool = False
    progress_percentage: int = 0
    recognized_farmer_id: Optional[int] = None
    potential_matches: List[Dict] = []
    is_returning: bool = False

# In-memory storage for registration sessions
context_registration_sessions: Dict[str, EnhancedRegistrationState] = {}

# Store incomplete registrations (in production, use database)
incomplete_registrations: Dict[str, Dict] = {}

async def check_incomplete_registration(partial_data: Dict) -> Optional[Dict]:
    """Check for recent incomplete registrations"""
    # In production, this would query the database
    # For now, check in-memory storage
    
    for reg_id, reg_data in incomplete_registrations.items():
        # Check if created within last 24 hours
        if datetime.now() - reg_data['created_at'] > timedelta(hours=24):
            continue
            
        # Match by name or phone
        if (partial_data.get('first_name') and 
            partial_data['first_name'] == reg_data['data'].get('first_name')):
            return reg_data
        
        if (partial_data.get('whatsapp') and 
            partial_data['whatsapp'] == reg_data['data'].get('whatsapp')):
            return reg_data
    
    return None

def extract_from_single_message(message: str) -> Dict:
    """Extract data from a single message IMMEDIATELY"""
    extracted = {}
    import re
    
    # Phone number patterns - VERY flexible
    phone_patterns = [
        r"([+]?[0-9]{8,15})",  # Any sequence of 8-15 digits with optional +
        r"whatsapp.{0,20}?([+]?[0-9]{8,15})",
        r"phone.{0,20}?([+]?[0-9]{8,15})",
        r"number.{0,20}?([+]?[0-9]{8,15})",
        r"contact.{0,20}?([+]?[0-9]{8,15})"
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            phone = match.group(1).strip()
            # Clean and format phone number
            phone = re.sub(r'[^0-9+]', '', phone)  # Remove non-numeric chars
            if len(phone) >= 8:  # Valid phone length
                if not phone.startswith('+') and len(phone) >= 10:
                    phone = '+' + phone
                extracted['whatsapp'] = phone
                logger.info(f"Extracted phone from '{message}': {phone}")
                break
    
    # Full name patterns (First Last)
    full_name_patterns = [
        r"i'm\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"my name is\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"i am\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"^([A-Z][a-z]+)\s+([A-Z][a-z]+)$",  # Just "Peter Knaflic"
        r"it's\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)"
    ]
    
    for pattern in full_name_patterns:
        match = re.search(pattern, message.strip(), re.IGNORECASE)
        if match:
            extracted['first_name'] = match.group(1).strip().title()
            extracted['last_name'] = match.group(2).strip().title()
            logger.info(f"Extracted full name from '{message}': {extracted['first_name']} {extracted['last_name']}")
            break
    
    # Single first name patterns (if no full name found)
    if not extracted.get('first_name'):
        first_name_patterns = [
            r"i'm\s+([A-Z][a-z]+)(?:\s|$)",
            r"my name is\s+([A-Z][a-z]+)(?:\s|$)",
            r"i am\s+([A-Z][a-z]+)(?:\s|$)",
            r"call me\s+([A-Z][a-z]+)(?:\s|$)",
            r"this is\s+([A-Z][a-z]+)(?:\s|$)"
        ]
        
        for pattern in first_name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted['first_name'] = match.group(1).strip().title()
                logger.info(f"Extracted first name from '{message}': {extracted['first_name']}")
                break
    
    # Last name patterns (standalone)
    if not extracted.get('last_name'):
        surname_patterns = [
            r"surname is\s+([A-Z][a-z]+)",
            r"last name is\s+([A-Z][a-z]+)",
            r"family name is\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)\s+is my (?:family name|surname|last name)"
        ]
        
        for pattern in surname_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted['last_name'] = match.group(1).strip().title()
                logger.info(f"Extracted last name from '{message}': {extracted['last_name']}")
                break
    
    return extracted

def simple_extract_registration_data(messages: List[Dict]) -> Dict:
    """Simple rule-based extraction (from Phase 2)"""
    extracted = {}
    
    # Process each message individually for better accuracy
    for msg in messages:
        if msg.get("role") == "user":
            msg_data = extract_from_single_message(msg.get("content", ""))
            # Update only if we don't have the data yet
            for key, value in msg_data.items():
                if value and not extracted.get(key):
                    extracted[key] = value
    
    return extracted

def create_context_aware_prompt(state: EnhancedRegistrationState, message: str) -> str:
    """Create context-aware prompt for registration conversation"""
    
    # Format conversation history
    history_text = ""
    if state.messages:
        for msg in state.messages[-6:]:  # Last 6 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
    
    # Build context info
    context_info = ""
    
    # Add potential matches info
    if state.potential_matches:
        context_info += f"""
Possible existing farmer matches found:
{format_farmer_matches(state.potential_matches)}

If the user seems to be one of these farmers, acknowledge it naturally but don't force it.
Only confirm if you're confident based on their response.
"""
    
    # Add incomplete registration info
    if state.incomplete_registration_id:
        context_info += f"""
This appears to be resuming an incomplete registration.
Welcome them back naturally.
"""
    
    # Add farming context
    if state.farming_context:
        context_info += f"""
Farming context mentioned:
- Crops: {', '.join(state.farming_context.get('crops', []))}
- Locations: {', '.join(state.farming_context.get('locations', []))}
"""
    
    # Show collection status
    collected_status = []
    for field, value in state.collected_data.items():
        if value:
            collected_status.append(f"✅ {field.replace('_', ' ').title()}: {value}")
        else:
            collected_status.append(f"❌ {field.replace('_', ' ').title()}: needed")
    
    status_text = "\n".join(collected_status)
    
    prompt = f"""You are AVA, a friendly registration assistant helping farmers sign up.

CURRENT STATUS:
{status_text}

{context_info}

CONVERSATION HISTORY:
{history_text}

USER'S LATEST MESSAGE: "{message}"

CRITICAL RULES - NEVER BREAK THESE:
1. NEVER ask for information that's already collected (marked with ✅)
2. ONLY ask for fields marked with ❌
3. If user just provided phone number, NEVER ask for phone again
4. If user just provided their name, NEVER ask for name again
5. Keep responses SHORT and natural (1-2 sentences max)

Additional rules:
- If you recognize them as an existing farmer, acknowledge it naturally
- Use their farming context when relevant (e.g., "Still growing mangoes?")
- Be conversational, not robotic

Good responses when data is provided:
- After phone: "Thanks! What's your name?"
- After first name only: "Nice to meet you {name}! What's your last name?"
- After full name: "Great! What's your WhatsApp number?"
- When complete: "Perfect! Welcome to AVA OLO, {name}! 🎉"

BAD responses (NEVER DO THIS):
- Asking for phone after they just gave it
- Asking for name after they just gave it
- Repeating requests for collected data

RESPOND BRIEFLY AND NATURALLY:"""

    return prompt

@router.post("/registration/context")
async def send_context_aware_registration_message(request: Request, message: ChatMessage):
    """Context-aware registration chat endpoint"""
    try:
        # Get or create session ID
        session_id = request.cookies.get("chat_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get or create registration state
        if session_id not in context_registration_sessions:
            context_registration_sessions[session_id] = EnhancedRegistrationState()
        
        state = context_registration_sessions[session_id]
        
        # CRITICAL FIX: Extract from current message FIRST, before anything else
        current_msg_data = extract_from_single_message(message.content)
        logger.info(f"Current message: '{message.content}'")
        logger.info(f"Extracted from current: {current_msg_data}")
        
        # Update state with current message data IMMEDIATELY
        for key, value in current_msg_data.items():
            if value and not state.collected_data.get(key):
                state.collected_data[key] = value
                logger.info(f"Updated {key} to: {value}")
        
        # Add user message to state
        state.add_message("user", message.content)
        
        # Update farming context
        state.update_farming_context(message.content)
        
        # Extract data from all messages (for any missed data)
        all_extracted_data = simple_extract_registration_data(state.messages)
        state.update_collected_data(all_extracted_data)
        
        # Search for existing farmer context
        search_criteria = await extract_search_criteria_from_message(
            message.content, 
            state.collected_data
        )
        
        if search_criteria and not state.recognized_farmer_id:
            potential_matches = await search_farmers_flexibly(search_criteria)
            state.potential_matches = potential_matches
            
            # If high confidence match, pre-fill data
            if potential_matches and potential_matches[0]['match_confidence'] >= 0.8:
                top_match = potential_matches[0]
                if not state.collected_data.get('first_name'):
                    state.collected_data['first_name'] = top_match['first_name']
                if not state.collected_data.get('last_name'):
                    state.collected_data['last_name'] = top_match.get('last_name')
                if not state.collected_data.get('whatsapp'):
                    state.collected_data['whatsapp'] = top_match.get('whatsapp_number')
                state.confidence_score = top_match['match_confidence']
        
        # Check for incomplete registration
        if not state.incomplete_registration_id:
            incomplete = await check_incomplete_registration(state.collected_data)
            if incomplete:
                state.incomplete_registration_id = incomplete.get('id')
                state.is_returning = True
                # Merge previous data
                for key, value in incomplete['data'].items():
                    if not state.collected_data.get(key) and value:
                        state.collected_data[key] = value
        
        # Create context-aware prompt
        registration_prompt = create_context_aware_prompt(state, message.content)
        
        # Get chat service
        chat_service = get_openai_chat()
        
        # Send to LLM with minimal farmer context
        response_data = await chat_service.send_message(
            f"reg_context_{session_id}",
            registration_prompt,
            {
                "location": "Unknown",
                "fields": [],
                "weather": "Unknown",
                "temperature": "Unknown",
                "humidity": "Unknown"
            }
        )
        
        # Add assistant response to state
        assistant_response = response_data.get("response", "I'm here to help you register.")
        state.add_message("assistant", assistant_response)
        
        # Check if registration is complete
        is_complete = state.check_completion()
        progress = state.get_progress_percentage()
        
        # Store incomplete registration if partially filled
        if not is_complete and progress > 0:
            incomplete_registrations[session_id] = {
                'id': session_id,
                'data': state.collected_data.copy(),
                'created_at': state.created_at,
                'farming_context': state.farming_context
            }
        elif is_complete and session_id in incomplete_registrations:
            # Remove from incomplete if completed
            del incomplete_registrations[session_id]
        
        # Log for debugging
        logger.info(f"Context session {session_id}: Progress {progress}%, Matches: {len(state.potential_matches)}")
        
        # Create response
        response_json = {
            "response": assistant_response,
            "timestamp": datetime.now().isoformat(),
            "model": response_data.get("model", "gpt-4"),
            "connected": response_data.get("connected", True),
            "collected_data": state.collected_data,
            "completed": is_complete,
            "progress_percentage": progress,
            "recognized_farmer_id": state.recognized_farmer_id,
            "potential_matches": [
                {
                    "name": f"{m['first_name']} {m.get('last_name', '')}",
                    "location": m.get('city', ''),
                    "confidence": m['match_confidence']
                } 
                for m in state.potential_matches[:3]
            ],
            "is_returning": state.is_returning
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
        logger.error(f"Context registration chat error: {e}")
        return {
            "response": "I'm having trouble connecting. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "model": "error",
            "connected": False,
            "collected_data": {},
            "completed": False,
            "progress_percentage": 0
        }

@router.get("/registration/context/status")
async def registration_context_status():
    """Get context-aware registration status"""
    try:
        chat_service = get_openai_chat()
        db_manager = get_db_manager()
        
        return {
            "status": "healthy",
            "connected": bool(chat_service.api_key),
            "has_api_key": bool(chat_service.api_key),
            "database_connected": db_manager.test_connection(),
            "api_key_prefix": chat_service.api_key[:8] + "..." if chat_service.api_key else "Not configured",
            "model": chat_service.model,
            "active_sessions": len(context_registration_sessions),
            "incomplete_registrations": len(incomplete_registrations),
            "features": {
                "memory": True,
                "state_tracking": True,
                "progress_indicators": True,
                "data_extraction": True,
                "farmer_recognition": True,
                "context_awareness": True,
                "incomplete_resume": True
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }