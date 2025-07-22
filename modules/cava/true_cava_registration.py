#!/usr/bin/env python3
"""
True CAVA Registration - Pure LLM-driven conversation
No hardcoding, no fixed sequences, just intelligent conversation
"""
from typing import Dict, Optional
import logging
from datetime import datetime
from modules.chat.openai_chat import get_openai_chat

logger = logging.getLogger(__name__)

class TrueCAVARegistration:
    """Pure conversational registration - no hardcoding"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.chat_service = get_openai_chat()
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """Get or create registration session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "collected": {
                    "first_name": None,
                    "last_name": None,
                    "whatsapp": None
                },
                "conversation_history": [],
                "created_at": datetime.utcnow(),
                "complete": False
            }
        return self.sessions[session_id]
    
    def is_complete(self, collected: Dict) -> bool:
        """Check if all required fields are collected"""
        return all(collected.values())
    
    async def process_message(self, session_id: str, message: str) -> Dict:
        """Process user message with pure LLM conversation"""
        session = self.get_or_create_session(session_id)
        
        # Add user message to history
        session["conversation_history"].append(f"User: {message}")
        
        # If already complete, just confirm
        if session["complete"]:
            return {
                "response": "Your registration is complete! You can now use AVA OLO.",
                "registration_complete": True,
                "collected_data": session["collected"]
            }
        
        # Build LLM prompt
        prompt = f"""You are helping a farmer register for AVA OLO. You need to collect ONLY these 3 pieces of information:
- First name
- Last name  
- WhatsApp number

Currently collected:
- First name: {session['collected']['first_name'] or 'NOT PROVIDED'}
- Last name: {session['collected']['last_name'] or 'NOT PROVIDED'}
- WhatsApp: {session['collected']['whatsapp'] or 'NOT PROVIDED'}

Conversation so far:
{chr(10).join(session['conversation_history'][-10:])}

User just said: "{message}"

IMPORTANT INSTRUCTIONS:
1. Extract ANY of the 3 required pieces from their message
2. Respond in the SAME LANGUAGE the user is using
3. Be natural and conversational - not robotic
4. If they ask why you need this info, explain: "We use this to personalize your farming advice and send weather alerts"
5. If they provide all info at once, acknowledge it naturally
6. Once all 3 pieces are collected, celebrate and tell them registration is complete
7. Accept ANY phone number format - don't validate strictly

Respond as JSON:
{{
    "response": "Your natural response here",
    "extracted": {{
        "first_name": "value if found or null",
        "last_name": "value if found or null",
        "whatsapp": "value if found or null"
    }}
}}"""

        try:
            # Get LLM response
            llm_result = await self.chat_service.send_message(
                f"cava_reg_{session_id}",
                prompt,
                {"system_prompt_override": "You are a helpful registration assistant. Always respond in valid JSON."}
            )
            
            import json
            import re
            
            response_text = llm_result.get("response", "")
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_data = json.loads(json_match.group())
            else:
                # Fallback response
                response_data = {
                    "response": "I'd be happy to help you register. Could you please share your first name?",
                    "extracted": {}
                }
            
            # Update collected data
            extracted = response_data.get("extracted", {})
            for field in ["first_name", "last_name", "whatsapp"]:
                if extracted.get(field) and extracted[field] != "null":
                    session["collected"][field] = extracted[field]
            
            # Add assistant response to history
            assistant_response = response_data.get("response", "Let me help you register.")
            session["conversation_history"].append(f"Assistant: {assistant_response}")
            
            # Check if complete
            if self.is_complete(session["collected"]):
                session["complete"] = True
                if "complete" not in assistant_response.lower() and "registration" not in assistant_response.lower():
                    assistant_response += "\n\n✅ Great! I have all your information. Your registration is complete!"
            
            return {
                "response": assistant_response,
                "registration_complete": session["complete"],
                "collected_data": session["collected"]
            }
            
        except Exception as e:
            logger.error(f"Error in true CAVA registration: {e}")
            # Simple fallback
            return self._simple_fallback(session, message)
    
    def _simple_fallback(self, session: Dict, message: str) -> Dict:
        """Simple fallback when LLM fails"""
        collected = session["collected"]
        
        # Try to extract data from message
        words = message.split()
        
        # Look for phone number
        import re
        phone_match = re.search(r'\+?\d{8,15}', message)
        if phone_match and not collected["whatsapp"]:
            collected["whatsapp"] = phone_match.group()
        
        # Look for names (capitalized words)
        capitalized_words = [w for w in words if len(w) > 1 and w[0].isupper()]
        
        if not collected["first_name"] and capitalized_words:
            collected["first_name"] = capitalized_words[0]
            if len(capitalized_words) > 1 and not collected["last_name"]:
                collected["last_name"] = capitalized_words[1]
        elif not collected["last_name"] and capitalized_words:
            for word in capitalized_words:
                if word != collected["first_name"]:
                    collected["last_name"] = word
                    break
        
        # Generate response
        if not collected["first_name"]:
            response = "Hello! I'm here to help you register. What's your first name?"
        elif not collected["last_name"]:
            response = f"Nice to meet you, {collected['first_name']}! What's your last name?"
        elif not collected["whatsapp"]:
            response = f"Thanks {collected['first_name']} {collected['last_name']}! What's your WhatsApp number?"
        else:
            session["complete"] = True
            response = f"Perfect! Welcome to AVA OLO, {collected['first_name']}! Your registration is complete."
        
        return {
            "response": response,
            "registration_complete": session.get("complete", False),
            "collected_data": collected
        }
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if session_id in self.sessions:
            return self.sessions[session_id]["collected"]
        return None
    
    def clear_session(self, session_id: str):
        """Clear session after registration"""
        if session_id in self.sessions:
            del self.sessions[session_id]