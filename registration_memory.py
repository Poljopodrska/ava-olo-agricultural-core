#!/usr/bin/env python3
"""
CAVA-Powered Registration System
Drop-in replacement for registration_memory.py that uses CAVA
Maintains exact same interface for backward compatibility
"""
import uuid
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import os

# Import CAVA components conditionally
logger = logging.getLogger(__name__)

CAVA_DISABLED = os.getenv('DISABLE_CAVA', 'false').lower() == 'true'

if not CAVA_DISABLED:
    try:
        from implementation.cava.cava_central_service import get_cava_service
    except Exception as e:
        logger.error(f"Failed to import CAVA: {e}")
        CAVA_DISABLED = True

class RegistrationChatWithMemory:
    """
    CAVA-powered registration that maintains the same interface
    as the original LangChain implementation
    """
    
    def __init__(self, openai_api_key: str):
        # Keep same init signature for compatibility
        self.openai_api_key = openai_api_key
        self.conversation_id = str(uuid.uuid4())
        self.session_id = None
        self.farmer_id = None
        
        # Maintain same data structure for compatibility
        self.required_data = {
            "full_name": None,
            "wa_phone_number": None, 
            "password": None,
            "farm_name": None
        }
        
        # Track state
        self.temp_password_for_confirmation = None
        self.conversation_history = []
        
        # Fallback registration state
        self.fallback_state = {
            "step": "name",  # name, phone, password, complete
            "collected_data": {}
        }
        self.last_ava_message = "Hi! What's your full name? (first and last name)"
    
    async def process_message(self, user_input: str) -> Dict[str, Any]:
        """Process user message through CAVA (maintains same interface)"""
        
        try:
            # If CAVA is disabled, use fallback
            if CAVA_DISABLED:
                logger.info("Using fallback registration (CAVA disabled)")
                raise Exception("CAVA disabled by configuration")
                
            # Generate farmer ID if not set
            if not self.farmer_id:
                # Use conversation ID hash as farmer ID for consistency
                self.farmer_id = abs(hash(self.conversation_id)) % 1000000
            
            # Get CAVA service
            cava = await get_cava_service()
            
            # Send to CAVA
            result = await cava.send_message(
                farmer_id=self.farmer_id,
                message=user_input,
                session_id=self.session_id,
                channel="registration"
            )
            
            # Update session ID from CAVA
            if result.get("session_id"):
                self.session_id = result["session_id"]
            
            # Get AVA's response
            ava_response = result.get("message", self.last_ava_message)
            self.last_ava_message = ava_response
            
            # Add to conversation history (maintain compatibility)
            self.conversation_history.append({
                "role": "user", 
                "content": user_input, 
                "timestamp": datetime.now().isoformat()
            })
            self.conversation_history.append({
                "role": "ava", 
                "content": ava_response, 
                "timestamp": datetime.now().isoformat()
            })
            
            # Extract data from CAVA response to maintain compatibility
            self._extract_data_from_cava_flow(user_input, ava_response, result)
            
            # Check if registration is complete
            status = "COMPLETE" if self._is_registration_complete() else "collecting"
            
            # Return in exact same format as original
            return {
                "message": ava_response,
                "extracted_data": self.required_data.copy(),
                "status": status,
                "conversation_history": self.conversation_history,
                "last_ava_message": ava_response,
                "memory_enabled": True,
                "conversation_id": self.conversation_id  # For CAVA tracking
            }
            
        except Exception as e:
            import traceback
            logger.error(f"CAVA registration error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Use fallback registration logic
            return await self._fallback_registration(user_input)
    
    async def _fallback_registration(self, user_input: str) -> Dict[str, Any]:
        """Simple fallback registration when CAVA is unavailable"""
        
        logger.info(f"🔄 Fallback registration - Step: {self.fallback_state['step']}, Input: '{user_input}'")
        
        # Process based on current step
        if self.fallback_state["step"] == "name":
            # Check if it looks like a name (2+ words, mostly alphabetic)
            words = user_input.strip().split()
            if len(words) >= 2 and all(w.replace("-", "").replace("'", "").isalpha() for w in words):
                self.fallback_state["collected_data"]["full_name"] = user_input.strip()
                self.fallback_state["step"] = "phone"
                response = f"Thanks {words[0]}! What's your phone number?"
            else:
                response = "Please provide your full name (first and last name):"
        
        elif self.fallback_state["step"] == "phone":
            # Check if it looks like a phone number
            if "+" in user_input or len(user_input.replace(" ", "").replace("-", "")) >= 10:
                self.fallback_state["collected_data"]["wa_phone_number"] = user_input.strip()
                self.fallback_state["step"] = "password"
                response = "Great! Now create a password for your account:"
            else:
                response = "Please provide your phone number (with country code like +385...):"
        
        elif self.fallback_state["step"] == "password":
            # Any non-empty input as password
            if len(user_input.strip()) >= 6:
                self.fallback_state["collected_data"]["password"] = user_input.strip()
                self.fallback_state["step"] = "complete"
                response = f"✅ Registration complete! Welcome {self.fallback_state['collected_data'].get('full_name', 'farmer')}!"
            else:
                response = "Please create a password (at least 6 characters):"
        
        else:
            response = "Registration is complete! How can I help you?"
        
        # Update required_data for compatibility
        self.required_data.update(self.fallback_state["collected_data"])
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user", 
            "content": user_input, 
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "ava", 
            "content": response, 
            "timestamp": datetime.now().isoformat()
        })
        
        status = "COMPLETE" if self.fallback_state["step"] == "complete" else "collecting"
        
        return {
            "message": response,
            "extracted_data": self.required_data.copy(),
            "status": status,
            "conversation_history": self.conversation_history,
            "last_ava_message": response,
            "memory_enabled": True,
            "conversation_id": self.conversation_id,
            "fallback_mode": True
        }
    
    def _extract_data_from_cava_flow(self, user_input: str, ava_response: str, cava_result: Dict):
        """
        Extract registration data based on CAVA's flow
        This maintains compatibility with the original data structure
        """
        # Lower case for easier checking
        response_lower = ava_response.lower()
        
        # Smart extraction based on what CAVA is asking for
        if "phone" in response_lower and not self.required_data["wa_phone_number"]:
            # CAVA is asking for phone, so previous input was likely name
            if not self.required_data["full_name"] and len(user_input.strip()) > 0:
                self.required_data["full_name"] = user_input.strip()
        
        elif "password" in response_lower and not self.required_data["password"]:
            # CAVA is asking for password, so previous input was likely phone
            if not self.required_data["wa_phone_number"] and '+' in user_input:
                self.required_data["wa_phone_number"] = user_input.strip()
        
        elif "farm" in response_lower and not self.required_data["farm_name"]:
            # CAVA is asking for farm name, so previous input was likely password
            if not self.required_data["password"] and len(user_input) >= 6:
                self.required_data["password"] = user_input.strip()
        
        elif "complete" in response_lower or "welcome" in response_lower:
            # Registration complete, last input was likely farm name
            if not self.required_data["farm_name"] and self.required_data["password"]:
                self.required_data["farm_name"] = user_input.strip()
        
        # Also check the current input for obvious data types
        if not self.required_data["wa_phone_number"] and '+' in user_input and len(user_input) > 8:
            self.required_data["wa_phone_number"] = user_input.strip()
        
        # If we have all other data and get any input, assume it's farm name
        if (self.required_data["full_name"] and 
            self.required_data["wa_phone_number"] and 
            self.required_data["password"] and 
            not self.required_data["farm_name"] and
            len(user_input.strip()) > 0):
            self.required_data["farm_name"] = user_input.strip()
    
    def _is_registration_complete(self) -> bool:
        """Check if all required data is collected"""
        return all(value is not None for value in self.required_data.values())
    
    # Maintain compatibility methods
    def _create_checklist_display(self) -> str:
        """Compatibility method - not used with CAVA"""
        return "Using CAVA for registration"
    
    def _get_conversation_summary(self) -> str:
        """Compatibility method - returns CAVA conversation"""
        if not self.conversation_history:
            return "This is the start of our conversation."
        
        messages = []
        for msg in self.conversation_history[-6:]:
            role = "User" if msg["role"] == "user" else "AVA"
            messages.append(f"{role}: {msg['content']}")
        
        return "\n".join(messages)
    
    def _get_message_history(self) -> list:
        """Get message history in standard format"""
        return self.conversation_history


# Global memory storage for different conversations (maintains compatibility)
_conversation_memories: Dict[str, RegistrationChatWithMemory] = {}

def get_conversation_memory(conversation_id: str, openai_api_key: str) -> RegistrationChatWithMemory:
    """Get or create memory for a conversation (CAVA-powered)"""
    if conversation_id not in _conversation_memories:
        _conversation_memories[conversation_id] = RegistrationChatWithMemory(openai_api_key)
    return _conversation_memories[conversation_id]

def clear_conversation_memory(conversation_id: str):
    """Clear memory for a conversation"""
    if conversation_id in _conversation_memories:
        del _conversation_memories[conversation_id]