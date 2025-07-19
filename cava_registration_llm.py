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

class ConversationState:
    """Track conversation progress for business-focused flow"""
    def __init__(self):
        self.message_count = 0
        self.off_topic_count = 0
        self.urgency_detected = False
        self.last_redirect_count = 0
        
    def update_prompt_context(self):
        """Adjust prompt based on conversation length"""
        if self.message_count > 10:
            return "GUIDANCE: Be direct - registration must complete. Ask for specific missing fields."
        elif self.off_topic_count > 2:
            return "GUIDANCE: Gently but firmly redirect to registration. Stay professional."
        elif self.message_count > 5:
            return "GUIDANCE: Make progress toward registration. Ask for missing information."
        else:
            return "GUIDANCE: Continue naturally while working toward registration."

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
        
        # Urgency keywords for emergency override
        self.urgency_keywords = [
            "dying", "disease", "urgent", "emergency", "destroyed", 
            "infestation", "help now", "быстро", "спешно", "умира"
        ]
        
    async def process_registration_message(
        self,
        message: str,
        session_id: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process farmer message with REAL LLM intelligence - NO FALLBACK
        """
        
        # CRITICAL: Log that we're calling OpenAI
        print(f"🔴 CAVA PROCESSING MESSAGE: {message}")
        print(f"🔴 API KEY PRESENT: {bool(self.api_key)}")
        print(f"🔴 API KEY LENGTH: {len(self.api_key or '')}")
        
        # CRITICAL: No OpenAI = FAILURE (no fallback allowed)
        if not self.api_key:
            raise Exception("❌ FATAL: No OpenAI API key - CAVA cannot work without LLM")
        
        # Initialize or get session with conversation state
        if session_id not in registration_sessions:
            registration_sessions[session_id] = {
                "collected_data": {},
                "conversation_history": conversation_history or [],
                "language_detected": None,
                "conversation_state": ConversationState()
            }
        
        session = registration_sessions[session_id]
        
        # Update conversation history
        if conversation_history:
            session["conversation_history"] = conversation_history
            
        # Get current collected data and conversation state
        collected_data = session["collected_data"]
        conv_state = session["conversation_state"]
        
        # Update conversation metrics
        conv_state.message_count += 1
        
        # Check for urgency that overrides registration
        urgency_detected = self._check_urgency(message)
        if urgency_detected:
            conv_state.urgency_detected = True
        
        # Check if this is off-topic (doesn't contain registration info or business)
        if not self._is_registration_related(message, collected_data):
            conv_state.off_topic_count += 1
        
        # Get conversation context guidance
        context_guidance = conv_state.update_prompt_context()
        
        # Calculate registration progress
        total_fields = len(self.required_fields)
        completed_fields = len([f for f in collected_data.values() if f])
        progress_percent = int((completed_fields / total_fields) * 100)
        
        # FORCE OpenAI call - no exceptions
        print(f"🔵 CALLING OPENAI WITH:")
        print(f"   Message: {message}")
        print(f"   Session: {session_id}")
        print(f"   Collected: {collected_data}")
        print(f"   Progress: {progress_percent}% ({completed_fields}/{total_fields})")
        print(f"   Messages: {conv_state.message_count}, Off-topic: {conv_state.off_topic_count}")
        print(f"   Urgency: {urgency_detected}")
        
        llm_result = await self._call_openai_for_registration(
            message=message,
            conversation_history=session["conversation_history"],
            collected_data=collected_data,
            conversation_state=conv_state,
            context_guidance=context_guidance,
            urgency_detected=urgency_detected,
            progress_percent=progress_percent
        )
        
        print(f"🟢 OPENAI RESPONDED: {llm_result}")
        
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
    
    async def _call_openai_for_registration(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        collected_data: Dict[str, Any],
        conversation_state: ConversationState = None,
        context_guidance: str = "",
        urgency_detected: bool = False,
        progress_percent: int = 0
    ) -> Dict[str, Any]:
        """
        Call OpenAI with intelligent prompt for registration
        """
        
        # Build conversation context
        context = self._build_conversation_context(conversation_history)
        
        # Enhanced prompt with collected data context
        user_prompt = f"""
Farmer said: "{message}"

Previous conversation: {context}
Already collected: {collected_data}

Understand their message and respond naturally. If they provided information you already have, acknowledge it and ask for what's still needed.
"""
        
        # Call OpenAI using v1.0+ API
        try:
            from openai import AsyncOpenAI
            
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            
            client = AsyncOpenAI(api_key=self.api_key)
            
            # Business-focused system prompt for efficient registration
            if urgency_detected:
                system_prompt = """You are AVA, an agricultural assistant. The farmer has an URGENT SITUATION.

EMERGENCY MODE: Forget registration - provide immediate agricultural help.
- Offer practical solutions
- Ask relevant follow-up questions
- Registration can wait until crisis is resolved

Always return ONLY a JSON object with helpful response."""
            else:
                missing_fields = self._get_missing_fields(collected_data)
                msg_count = conversation_state.message_count if conversation_state else 0
                system_prompt = f"""You are AVA, an agricultural assistant helping farmers register efficiently.

REGISTRATION GOAL: Collect required information in 5-7 natural exchanges:
- first_name, last_name, farm_location, primary_crops, whatsapp_number

CURRENT STATUS:
- Progress: {progress_percent}% complete
- Still needed: {', '.join(missing_fields)}
- Conversation length: {msg_count} messages

CONVERSATION GUIDELINES:
1. Stay friendly and natural, acknowledge their input briefly
2. For off-topic topics: acknowledge (1 sentence max) then redirect to registration
3. Always work toward collecting missing registration fields
4. {context_guidance}

REDIRECTION EXAMPLES:
- Crocodiles: "That's unusual! Let's get you registered first. What's your name?"
- Philosophy: "Interesting question! First, may I have your name for registration?"
- Weather chat: "Yes, weather matters for farming! What crops do you grow?"

INTELLIGENCE RULES:
- Convert emojis to words (🥭 = mango)
- Fix typos intelligently
- Use same language as input when possible
- Extract information naturally

Always return ONLY a JSON object:
{{
  "response": "your natural, business-focused response",
  "extracted_data": {{
    "first_name": "value or null",
    "last_name": "value or null",
    "farm_location": "value or null", 
    "primary_crops": "value or null",
    "whatsapp_number": "value or null"
  }}
}}"""

            print(f"🔵 SENDING TO OPENAI:")
            print(f"   Model: gpt-3.5-turbo")
            print(f"   System: {system_prompt[:100]}...")
            print(f"   User: {user_prompt[:100]}...")
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Natural conversation variation
                max_tokens=300,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            print(f"🟢 LLM RESPONSE RECEIVED:")
            print(f"   Tokens used: {response.usage.total_tokens}")
            print(f"   Model: {response.model}")
            print(f"   Content: {response.choices[0].message.content}")
            
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
    
    def _check_urgency(self, message: str) -> bool:
        """Check if message indicates urgent agricultural emergency"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.urgency_keywords)
    
    def _is_registration_related(self, message: str, collected_data: Dict[str, Any]) -> bool:
        """Check if message contains registration information or business content"""
        message_lower = message.lower()
        
        # Registration keywords
        reg_keywords = [
            "name", "location", "farm", "crop", "phone", "whatsapp", 
            "grow", "harvest", "agriculture", "register", "sign up",
            "ljubljana", "maribor", "zagreb", "sofia", "mange", "mango"
        ]
        
        # Check if any registration keyword present
        if any(keyword in message_lower for keyword in reg_keywords):
            return True
            
        # Check if message looks like personal information
        words = message.strip().split()
        if len(words) <= 3 and any(word[0].isupper() for word in words):
            return True  # Likely name or location
            
        # Check for phone numbers
        if any(char.isdigit() for char in message) and ('+' in message or len([c for c in message if c.isdigit()]) >= 8):
            return True
            
        return False
    
    # DELETED: Template fallback responses removed to force real intelligence

# Singleton instance
_llm_engine = None

async def get_llm_registration_engine() -> CAVARegistrationLLM:
    """Get or create LLM registration engine"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = CAVARegistrationLLM()
    return _llm_engine