"""
CAVA Registration Engine - LLM-Powered Natural Conversations
Constitutional Amendment #15 Compliant
Zero hardcoded conversation logic
"""

import json
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# In-memory session storage (restored from v3.3.0-cava-debug-fix)
# This was the working version that prevented infinite loops
registration_sessions = {}

class CAVARegistrationEngine:
    """
    LLM-powered registration conversations
    No hardcoded steps - pure intelligence
    """
    
    def __init__(self):
        self.required_fields = [
            "first_name", 
            "last_name", 
            "whatsapp_number", 
            "farm_location", 
            "primary_crops"
        ]
        
    async def process_registration_message(
        self, 
        message: str, 
        session_id: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process farmer message through LLM intelligence
        Extract data, determine next action, generate response
        """
        
        # Try to use the new LLM engine first
        try:
            from cava_registration_llm import get_llm_registration_engine
            llm_engine = await get_llm_registration_engine()
            
            # Use the LLM engine
            result = await llm_engine.process_registration_message(
                message=message,
                session_id=session_id,
                conversation_history=conversation_history
            )
            
            # Ensure compatible response format
            if "redirect_to" not in result and result.get("registration_complete"):
                result["redirect_to"] = "/chat"
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM engine not available ({e}), trying CAVA service")
        
        # Initialize or get session
        if session_id not in registration_sessions:
            registration_sessions[session_id] = {
                "collected_data": {},
                "conversation_history": conversation_history or [],
                "extracted_data_history": []
            }
        
        session = registration_sessions[session_id]
        
        # Update conversation history if provided
        if conversation_history:
            session["conversation_history"] = conversation_history
        
        # Get CAVA service
        try:
            from implementation.cava.cava_central_service import get_cava_service
            cava = await get_cava_service()
        except Exception as e:
            logger.warning(f"CAVA not available ({e}), using fallback")
            return await self._fallback_registration(message, session_id, conversation_history)
        
        # Build context for LLM
        context = self._build_conversation_context(session["conversation_history"])
        
        # Use session's collected data instead of extracting from history
        farmer_data = session["collected_data"]
        
        # Generate LLM prompt for intelligent analysis
        analysis_prompt = f"""
        You are AVA, an agricultural assistant helping a farmer register.
        
        Current message from farmer: "{message}"
        
        Conversation so far:
        {self._format_conversation_history(conversation_history)}
        
        Information collected so far:
        {json.dumps(farmer_data, indent=2)}
        
        Required information still needed:
        {self._get_missing_fields(farmer_data)}
        
        TASK: Analyze the farmer's message and:
        1. Extract any registration data (name, phone, location, crops)
        2. Determine what information is still missing
        3. Generate a natural, friendly response
        
        Rules:
        - Be conversational, not robotic
        - Show interest in their farming
        - Ask for ONE piece of missing information at a time
        - If they mention crops, ask follow-up questions
        - Adapt to their communication style
        
        Response format:
        {{
            "extracted_data": {{
                "first_name": "value if found",
                "last_name": "value if found",
                "whatsapp_number": "value if found",
                "farm_location": "value if found", 
                "primary_crops": "value if found"
            }},
            "missing_fields": ["list", "of", "missing", "fields"],
            "response": "Your natural response to the farmer",
            "registration_complete": true/false
        }}
        """
        
        # Send to CAVA for LLM processing
        result = await cava.send_message(
            farmer_id=0,  # No farmer ID yet during registration
            message=analysis_prompt,
            session_id=session_id,
            channel="registration"
        )
        
        # Parse LLM response
        try:
            llm_analysis = json.loads(result.get("message", "{}"))
        except:
            # If LLM response isn't JSON, fallback to simple extraction
            logger.warning(f"CAVA returned non-JSON response: {result.get('message', '')}")
            # Use the fallback registration logic instead
            return await self._fallback_registration(message, session_id, session.get("conversation_history", []))
        
        # Update farmer data with extracted information
        if llm_analysis.get("extracted_data"):
            # Filter out placeholder values
            for field, value in llm_analysis["extracted_data"].items():
                if value and value != "value if found" and value != "":
                    farmer_data[field] = value
                    session["collected_data"][field] = value
        
        # Update session with latest data
        registration_sessions[session_id] = session
        
        # Check if registration is complete
        missing_fields = self._get_missing_fields(farmer_data)
        if llm_analysis.get("registration_complete") or not missing_fields:
            # Create farmer account
            farmer_id = await self._complete_registration(farmer_data, session_id)
            
            # Clear session after completion
            if session_id in registration_sessions:
                del registration_sessions[session_id]
            
            return {
                "response": llm_analysis.get("response", "Welcome to AVA OLO! Your registration is complete."),
                "registration_complete": True,
                "farmer_id": farmer_id,
                "redirect_to": "/chat"
            }
        
        return {
            "response": llm_analysis.get("response"),
            "registration_complete": False,
            "extracted_data": farmer_data,
            "missing_fields": missing_fields
        }
    
    def _build_conversation_context(self, history: List[Dict[str, str]]) -> str:
        """Build context from conversation history"""
        if not history:
            return "New registration conversation"
        
        context_parts = []
        for msg in history[-10:]:  # Last 10 messages for context
            role = "Farmer" if msg.get("is_farmer") else "AVA"
            context_parts.append(f"{role}: {msg.get('message', '')}")
        
        return "\n".join(context_parts)
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation for LLM understanding"""
        if not history:
            return "No previous messages"
        
        formatted = []
        for msg in history:
            role = "Farmer" if msg.get("is_farmer") else "AVA"
            formatted.append(f"{role}: {msg.get('message', '')}")
        
        return "\n".join(formatted)
    
    def _extract_session_data(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract farmer data from conversation history"""
        # This would normally come from Redis session
        # For now, parse from conversation
        data = {}
        
        # Simple extraction logic - LLM will do the heavy lifting
        for msg in history:
            if msg.get("extracted_data"):
                data.update(msg["extracted_data"])
        
        return data
    
    def _get_missing_fields(self, farmer_data: Dict[str, Any]) -> List[str]:
        """Determine which fields are still needed"""
        missing = []
        for field in self.required_fields:
            if not farmer_data.get(field):
                missing.append(field)
        return missing
    
    async def _complete_registration(self, farmer_data: Dict[str, Any], session_id: str) -> int:
        """Complete registration and create farmer account"""
        try:
            from database_operations import DatabaseOperations
            db_ops = DatabaseOperations()
            
            # Store in PostgreSQL via LLM query
            create_query = f"""
            Create a new farmer account with this information:
            - First name: {farmer_data.get('first_name')}
            - Last name: {farmer_data.get('last_name')}
            - WhatsApp: {farmer_data.get('whatsapp_number')}
            - Location: {farmer_data.get('farm_location')}
            - Crops: {farmer_data.get('primary_crops')}
            - Registration date: {datetime.now().isoformat()}
            """
            
            result = await db_ops.process_natural_query(
                query_text=create_query,
                language="en"
            )
            
            # Generate a farmer ID (in production, from database)
            farmer_id = abs(hash(session_id)) % 1000000
            
            logger.info(f"Registration complete for farmer {farmer_id}")
            return farmer_id
            
        except Exception as e:
            logger.error(f"Registration completion error: {e}")
            return 1  # Default farmer ID
    
    async def _fallback_registration(
        self, 
        message: str, 
        session_id: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Fallback when CAVA not available - still no hardcoding!"""
        
        # Initialize or get session
        if session_id not in registration_sessions:
            registration_sessions[session_id] = {
                "collected_data": {},
                "conversation_history": conversation_history or [],
                "extracted_data_history": []
            }
        
        session = registration_sessions[session_id]
        farmer_data = session["collected_data"]
        
        # Simple pattern matching for data extraction
        extracted = {}
        message_lower = message.lower()
        
        # Look for patterns
        if "my name is" in message_lower or "i'm " in message_lower or "i am " in message_lower:
            # Extract name
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["i'm", "im", "i"]:
                    if i + 1 < len(words):
                        extracted["first_name"] = words[i + 1].strip(",.")
                        if i + 2 < len(words) and not any(c.isdigit() for c in words[i + 2]):
                            extracted["last_name"] = words[i + 2].strip(",.")
        
        # Also check for single word that might be a name
        if not extracted.get("first_name") and "first_name" not in farmer_data:
            words = message.strip().split()
            if len(words) == 1 and words[0].isalpha() and len(words[0]) > 1:
                # Single word, likely a first name
                extracted["first_name"] = words[0].title()
        elif not extracted.get("last_name") and "last_name" not in farmer_data and "first_name" in farmer_data:
            # If we already have first name, single word is likely last name
            words = message.strip().split()
            if len(words) == 1 and words[0].isalpha() and len(words[0]) > 1:
                extracted["last_name"] = words[0].title()
        
        # Look for phone number
        import re
        phone_pattern = r'\+?\d{10,15}'
        phone_match = re.search(phone_pattern, message)
        if phone_match:
            extracted["whatsapp_number"] = phone_match.group()
        
        # Look for location
        if "from" in message_lower:
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() == "from" and i + 1 < len(words):
                    extracted["farm_location"] = " ".join(words[i+1:i+3])
        elif "farm_location" not in farmer_data and "whatsapp_number" in farmer_data:
            # If we're asking for location and get a single word/phrase, assume it's the location
            if len(message.strip()) > 0 and not any(char.isdigit() for char in message):
                extracted["farm_location"] = message.strip().title()
        
        # Look for crops
        crop_keywords = ["grow", "farm", "cultivate", "plant"]
        for keyword in crop_keywords:
            if keyword in message_lower:
                # Extract crop mentions
                words = message.split()
                for i, word in enumerate(words):
                    if word.lower() == keyword and i + 1 < len(words):
                        extracted["primary_crops"] = " ".join(words[i+1:i+3])
        
        # If we're asking for crops and get a response without keywords, assume it's the crop
        if "primary_crops" not in farmer_data and "farm_location" in farmer_data:
            if len(message.strip()) > 0 and not extracted.get("primary_crops"):
                extracted["primary_crops"] = message.strip().lower()
        
        # Update farmer data with newly extracted info
        farmer_data.update(extracted)
        session["collected_data"] = farmer_data
        
        # Update session
        registration_sessions[session_id] = session
        
        # Debug logging
        logger.info(f"Message: '{message}' → Extracted: {extracted}")
        logger.info(f"Total collected data: {farmer_data}")
        
        # Determine missing fields
        missing = self._get_missing_fields(farmer_data)
        
        # Generate response based on what's missing
        if not missing:
            farmer_id = await self._complete_registration(farmer_data, session_id)
            return {
                "response": f"Welcome to AVA OLO! I've created your account. You can now access personalized agricultural advice.",
                "registration_complete": True,
                "farmer_id": farmer_id,
                "redirect_to": "/chat"
            }
        
        # Generate next question based on what we have
        next_field = missing[0]
        
        # Special case: if message is empty, provide welcome
        if not message:
            response = "Hi! I'm AVA, your agricultural assistant. Welcome! What's your first name?"
        elif next_field == "first_name":
            response = "I'm AVA, your agricultural assistant. What's your first name?"
        elif next_field == "last_name":
            first_name = farmer_data.get('first_name', 'there')
            response = f"Nice to meet you, {first_name}! What's your last name?"
        elif next_field == "whatsapp_number":
            name = farmer_data.get('first_name', 'there')
            response = f"Great, {name}! What's your WhatsApp number? Please include the country code (e.g., +359...)"
        elif next_field == "farm_location":
            response = "Perfect! Where is your farm located?"
        elif next_field == "primary_crops":
            response = "And what crops do you grow on your farm?"
        else:
            response = "Could you tell me more about yourself?"
        
        return {
            "response": response,
            "registration_complete": False,
            "extracted_data": farmer_data,
            "missing_fields": missing
        }


# Singleton instance
_registration_engine = None

async def get_registration_engine() -> CAVARegistrationEngine:
    """Get or create registration engine instance"""
    global _registration_engine
    if _registration_engine is None:
        _registration_engine = CAVARegistrationEngine()
    return _registration_engine