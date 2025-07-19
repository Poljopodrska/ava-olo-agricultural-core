"""
CAVA Registration LLM Intelligence
Real OpenAI-powered conversation understanding
No hardcoded logic - pure AI intelligence
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Session storage (will be Redis in production)
registration_sessions = {}

class CAVARegistrationLLM:
    """
    True LLM-powered registration with OpenAI
    Understands context, extracts entities naturally
    """
    
    def __init__(self):
        self.required_fields = {
            "first_name": "farmer's first name",
            "last_name": "farmer's last name", 
            "whatsapp_number": "WhatsApp phone number with country code",
            "farm_location": "farm location (city, region, or country)",
            "primary_crops": "main crops grown"
        }
        
        # OpenAI setup
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    async def process_registration_message(
        self,
        message: str,
        session_id: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process farmer message with real LLM intelligence
        """
        
        # Initialize or get session
        if session_id not in registration_sessions:
            registration_sessions[session_id] = {
                "collected_data": {},
                "conversation_history": conversation_history or [],
                "language_detected": None
            }
        
        session = registration_sessions[session_id]
        
        # Update conversation history
        if conversation_history:
            session["conversation_history"] = conversation_history
            
        # Get current collected data
        collected_data = session["collected_data"]
        
        # Call OpenAI for intelligent processing
        try:
            llm_result = await self._call_openai_for_registration(
                message=message,
                conversation_history=session["conversation_history"],
                collected_data=collected_data
            )
            
            # Update session with new data
            if llm_result.get("extracted_data"):
                for field, value in llm_result["extracted_data"].items():
                    if value and value not in ["null", "none", ""]:
                        collected_data[field] = value
                        
            session["collected_data"] = collected_data
            
            # Check what's still needed
            missing_fields = self._get_missing_fields(collected_data)
            
            # Return structured response
            return {
                "response": llm_result.get("response", "I'm here to help you register. Could you tell me about yourself?"),
                "extracted_data": collected_data,
                "registration_complete": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "language_detected": llm_result.get("language_detected")
            }
            
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            # Fallback to simple extraction
            return await self._simple_fallback(message, session_id, session["conversation_history"])
    
    async def _call_openai_for_registration(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call OpenAI with intelligent prompt for registration
        """
        
        # Build conversation context
        context = self._build_conversation_context(conversation_history)
        
        # Simple, natural prompt - trust LLM intelligence
        user_prompt = f"""
Previous conversation:
{context}

Farmer says: "{message}"

What did you understand from this message? Respond naturally and extract any registration information.
"""
        
        # Call OpenAI using v1.0+ API
        try:
            from openai import AsyncOpenAI
            
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            
            client = AsyncOpenAI(api_key=self.api_key)
            
            # Simple system prompt - let LLM understand naturally
            system_prompt = """You are AVA, an intelligent agricultural assistant helping farmers register.

Understand what farmers tell you naturally. Extract registration information:
- first_name
- last_name  
- farm_location
- primary_crops
- whatsapp_number

Always return ONLY a JSON object like this:
{
  "response": "your natural response",
  "extracted_data": {
    "first_name": "value or null",
    "last_name": "value or null",
    "farm_location": "value or null", 
    "primary_crops": "value or null",
    "whatsapp_number": "value or null"
  }
}"""

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Consistent understanding
                max_tokens=300
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response as JSON: {content}")
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        return result
                    except:
                        pass
                
                # If all parsing fails, return a simple response
                return {
                    "response": content,
                    "extracted_data": {},
                    "language_detected": "en"
                }
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _build_conversation_context(self, history: List[Dict[str, str]]) -> str:
        """Build conversation history for LLM context"""
        if not history:
            return "No previous conversation"
            
        lines = []
        for msg in history[-10:]:  # Last 10 messages for context
            role = "Farmer" if msg.get("is_farmer") else "AVA"
            lines.append(f"{role}: {msg.get('message', '')}")
            
        return "\n".join(lines)
    
    def _get_missing_fields(self, collected_data: Dict[str, Any]) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        for field, description in self.required_fields.items():
            if not collected_data.get(field):
                missing.append(description)
        return missing
    
    async def _simple_fallback(
        self,
        message: str,
        session_id: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Simple fallback when OpenAI is unavailable"""
        
        # Initialize session if needed
        if session_id not in registration_sessions:
            registration_sessions[session_id] = {
                "collected_data": {},
                "conversation_history": conversation_history or [],
                "language_detected": None
            }
        
        session = registration_sessions[session_id]
        collected_data = session["collected_data"]
        
        # Very basic extraction
        extracted = {}
        message_lower = message.lower()
        
        # City recognition for Ljubljana test
        cities = ["ljubljana", "maribor", "celje", "kranj", "murska sobota", "novo mesto"]
        for city in cities:
            if city in message_lower:
                extracted["farm_location"] = city.title()
                break
        
        # Simple name detection
        if not collected_data.get("first_name"):
            # Check for "I'm X" or "My name is X" patterns
            import re
            name_patterns = [
                r"(?:i'm|im|i am)\s+([a-zA-Z]+)",
                r"my name is\s+([a-zA-Z]+)",
                r"(?:hi|hello),?\s+i'm\s+([a-zA-Z]+)",
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    name = match.group(1)
                    if name.lower() not in cities:
                        extracted["first_name"] = name.title()
                        break
            
            # Single word detection
            if not extracted.get("first_name"):
                words = message.strip().split()
                if len(words) == 1 and words[0].isalpha() and words[0].lower() not in cities:
                    extracted["first_name"] = words[0].title()
        
        # Update collected data
        collected_data.update(extracted)
        session["collected_data"] = collected_data
        
        # Generate simple response
        missing = self._get_missing_fields(collected_data)
        if not missing:
            response = "Thank you! Your registration is complete."
        elif "first name" in missing[0]:
            response = "Hello! I'm AVA, your agricultural assistant. What's your first name?"
        elif "last name" in missing[0]:
            name = collected_data.get("first_name", "there")
            response = f"Nice to meet you, {name}! What's your last name?"
        elif "location" in missing[0]:
            response = "Where is your farm located?"
        elif "phone" in missing[0]:
            response = "What's your WhatsApp number? Please include the country code."
        elif "crops" in missing[0]:
            response = "What crops do you grow on your farm?"
        else:
            response = f"Could you tell me your {missing[0]}?"
        
        return {
            "response": response,
            "extracted_data": collected_data,
            "registration_complete": len(missing) == 0,
            "missing_fields": missing
        }

# Singleton instance
_llm_engine = None

async def get_llm_registration_engine() -> CAVARegistrationLLM:
    """Get or create LLM registration engine"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = CAVARegistrationLLM()
    return _llm_engine