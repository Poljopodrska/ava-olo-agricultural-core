#!/usr/bin/env python3
"""
CAVA Natural Registration Flow
Handles conversational registration using LLM for natural language understanding
"""
from typing import Dict, Optional, List, Tuple
import re
import json
import logging
from datetime import datetime
from modules.chat.openai_chat import get_openai_chat

logger = logging.getLogger(__name__)

class NaturalRegistrationFlow:
    """Manages natural conversational registration flow using LLM"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.chat_service = get_openai_chat()
        
        # Required fields for registration
        self.required_fields = {
            "first_name": "first name",
            "last_name": "last name", 
            "whatsapp": "WhatsApp number"
        }
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "collected_data": {},
                "history": [],
                "created_at": datetime.utcnow(),
                "digression_count": 0,
                "last_activity": datetime.utcnow(),
                "registration_complete": False,
                "language": None
            }
        else:
            self.sessions[session_id]["last_activity"] = datetime.utcnow()
        return self.sessions[session_id]
    
    def get_missing_fields(self, collected_data: Dict) -> List[str]:
        """Get list of fields still needed"""
        missing = []
        for field, display_name in self.required_fields.items():
            if field not in collected_data or not collected_data[field]:
                missing.append(display_name)
        return missing
    
    def extract_phone_number(self, text: str) -> Optional[str]:
        """Extract phone number from text - very permissive"""
        # Look for patterns that might be phone numbers
        # Accept anything with 8+ digits, with or without country code
        patterns = [
            r'\+?\d{1,3}[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4}',  # With country code
            r'\d{8,15}',  # Just digits
            r'\d{3}[\s.-]\d{3}[\s.-]\d{4}',  # US format
            r'\d{2}[\s.-]\d{3}[\s.-]\d{2}[\s.-]\d{2}',  # European formats
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Clean up the number
                number = match.group()
                # Remove all non-digits except +
                cleaned = re.sub(r'[^\d+]', '', number)
                # Ensure it has enough digits
                if len(re.sub(r'[^\d]', '', cleaned)) >= 8:
                    return cleaned
        
        return None
    
    def build_llm_prompt(self, user_message: str, session: Dict) -> str:
        """Build prompt for LLM to handle registration naturally"""
        collected = session["collected_data"]
        missing = self.get_missing_fields(collected)
        digression_count = session["digression_count"]
        
        # Build conversation history context
        history_context = ""
        if session["history"]:
            # Include last 5 exchanges for context
            recent_history = session["history"][-10:]
            for entry in recent_history:
                history_context += f"\n{entry['role']}: {entry['message']}"
        
        prompt = f"""You are AVA, a friendly agricultural assistant helping a farmer register.

REGISTRATION PURPOSE: Collect first name, last name, and WhatsApp number to create their farmer account.

Currently collected:
- First name: {collected.get('first_name', 'NOT PROVIDED')}
- Last name: {collected.get('last_name', 'NOT PROVIDED')}  
- WhatsApp: {collected.get('whatsapp', 'NOT PROVIDED')}

Still need: {', '.join(missing) if missing else 'Nothing - registration complete!'}

Recent conversation:{history_context}

User just said: "{user_message}"

IMPORTANT INSTRUCTIONS:
1. Extract ANY registration data from their message (names, phone numbers)
2. Respond in the same language the user is using
3. If they provide all info at once (e.g., "I'm Peter Horvat, +38641348050"), acknowledge all of it
4. If they ask why you need info, explain: "We use this to send you personalized farming advice and weather alerts"
5. If they go off-topic (pets, stories, etc.), acknowledge briefly then gently guide back
6. After {3 if digression_count < 3 else 5} off-topic messages, add gentle urgency
7. Be natural, friendly, and conversational - not robotic
8. Accept ANY phone format - don't validate strictly

RESPONSE STRATEGIES:
- Cooperation: Thank them and ask for next missing piece
- Question about privacy: Reassure about data protection
- Digression: "That's interesting about your [topic]! While we're here, could you share your [missing field]?"
- Resistance: "I understand your concern. This helps us provide better farming support. Shall we continue?"
- All info provided: Celebrate and confirm the data

Respond naturally and extract any available data. Format your response as JSON:
{{
    "response": "Your natural response here",
    "extracted_data": {{
        "first_name": "value if found",
        "last_name": "value if found",
        "whatsapp": "value if found"
    }},
    "is_digression": true/false,
    "detected_language": "en/sl/bg/etc"
}}"""
        
        return prompt
    
    async def process_message(self, session_id: str, message: str) -> Dict:
        """Process a message from the farmer using LLM"""
        session = self.get_or_create_session(session_id)
        
        # Add user message to history
        session["history"].append({
            "role": "user",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check if registration is already complete
        if session["registration_complete"]:
            return {
                "response": "Your registration is already complete! You can start using AVA OLO now.",
                "registration_complete": True,
                "registration_data": session["collected_data"]
            }
        
        try:
            # Build LLM prompt
            prompt = self.build_llm_prompt(message, session)
            
            # Get LLM response
            llm_result = await self.chat_service.send_message(
                f"registration_{session_id}",
                prompt,
                {"system_prompt_override": "You are a registration assistant. Always respond in valid JSON format."}
            )
            
            # Parse LLM response
            response_text = llm_result.get("response", "")
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    response_data = json.loads(json_match.group())
                else:
                    # Fallback if no JSON found
                    response_data = {
                        "response": response_text,
                        "extracted_data": {},
                        "is_digression": False
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM JSON response: {response_text}")
                # Use simple extraction as fallback
                response_data = self._fallback_extraction(message, response_text)
            
            # Update collected data
            extracted = response_data.get("extracted_data", {})
            for field, value in extracted.items():
                if value and value.lower() not in ["not provided", "none", "null"]:
                    session["collected_data"][field] = value
            
            # Also try to extract phone number directly
            if "whatsapp" not in session["collected_data"] or not session["collected_data"]["whatsapp"]:
                phone = self.extract_phone_number(message)
                if phone:
                    session["collected_data"]["whatsapp"] = phone
            
            # Update language if detected
            if response_data.get("detected_language"):
                session["language"] = response_data["detected_language"]
            
            # Track digressions
            if response_data.get("is_digression", False):
                session["digression_count"] += 1
            else:
                # Reset digression count on productive interaction
                session["digression_count"] = 0
            
            # Check if registration is complete
            missing_fields = self.get_missing_fields(session["collected_data"])
            if not missing_fields:
                session["registration_complete"] = True
                response = response_data.get("response", "Great! I have all your information. Click 'Complete Registration' to finish setting up your account!")
                if not "complete" in response.lower() and not "finish" in response.lower():
                    response += "\n\n✅ All information collected! Click 'Complete Registration' to create your account."
            else:
                response = response_data.get("response", f"Thanks! I still need your {', '.join(missing_fields)}.")
            
            # Add assistant response to history
            session["history"].append({
                "role": "assistant", 
                "message": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "response": response,
                "registration_complete": session["registration_complete"],
                "collected_data": session["collected_data"],
                "missing_fields": missing_fields,
                "digression_count": session["digression_count"]
            }
            
        except Exception as e:
            logger.error(f"Error in natural registration: {e}")
            # Fallback to simple pattern matching
            return self._simple_fallback(session_id, message)
    
    def _fallback_extraction(self, message: str, llm_response: str) -> Dict:
        """Fallback extraction when JSON parsing fails"""
        result = {
            "response": llm_response if llm_response else "I understand. Could you please share the information needed for registration?",
            "extracted_data": {},
            "is_digression": False
        }
        
        # Simple name extraction
        words = message.split()
        if len(words) >= 2 and words[0][0].isupper() and words[1][0].isupper():
            result["extracted_data"]["first_name"] = words[0]
            result["extracted_data"]["last_name"] = words[1]
        elif len(words) == 1 and words[0][0].isupper():
            # Could be first name
            result["extracted_data"]["first_name"] = words[0]
        
        # Phone extraction
        phone = self.extract_phone_number(message)
        if phone:
            result["extracted_data"]["whatsapp"] = phone
        
        return result
    
    def _simple_fallback(self, session_id: str, message: str) -> Dict:
        """Simple fallback when LLM is not available"""
        session = self.sessions[session_id]
        collected = session["collected_data"]
        
        # Try to extract data
        extracted_data = {}
        
        # Phone number extraction
        phone = self.extract_phone_number(message)
        if phone:
            extracted_data["whatsapp"] = phone
        
        # Simple name detection
        words = message.split()
        if not collected.get("first_name") and len(words) >= 1:
            # Check if first word is capitalized and looks like a name
            if words[0][0].isupper() and len(words[0]) > 1:
                extracted_data["first_name"] = words[0]
                if len(words) >= 2 and words[1][0].isupper():
                    extracted_data["last_name"] = words[1]
        elif collected.get("first_name") and not collected.get("last_name"):
            # We have first name, looking for last name
            for word in words:
                if word[0].isupper() and len(word) > 1:
                    extracted_data["last_name"] = word
                    break
        
        # Update collected data
        for field, value in extracted_data.items():
            if value:
                collected[field] = value
        
        # Generate response
        missing = self.get_missing_fields(collected)
        
        if not missing:
            response = f"Perfect! I have all your information. Welcome to AVA OLO, {collected['first_name']}!"
            session["registration_complete"] = True
        elif "first_name" in extracted_data:
            response = f"Nice to meet you, {extracted_data['first_name']}! What's your last name?"
        elif "last_name" in extracted_data:
            response = f"Thank you, {collected['first_name']} {extracted_data['last_name']}! What's your WhatsApp number?"
        elif "whatsapp" in extracted_data:
            if not collected.get("first_name"):
                response = "Thanks for the number! What's your first name?"
            elif not collected.get("last_name"):
                response = f"Got it, {collected['first_name']}! What's your last name?"
            else:
                response = "Perfect! I have all your information."
        else:
            # No data extracted
            if not collected:
                response = "Hello! I'm AVA, here to help you register. What's your first name?"
            elif not collected.get("last_name"):
                response = f"Hi {collected['first_name']}! What's your last name?"
            elif not collected.get("whatsapp"):
                response = "Last thing - what's your WhatsApp number so we can send you updates?"
            else:
                response = "Could you please provide the remaining information for registration?"
        
        # Add to history
        session["history"].append({
            "role": "assistant",
            "message": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "response": response,
            "registration_complete": session.get("registration_complete", False),
            "collected_data": collected,
            "missing_fields": missing
        }
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get registration data for a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]["collected_data"]
        return None
    
    def clear_session(self, session_id: str):
        """Clear a session after registration"""
        if session_id in self.sessions:
            del self.sessions[session_id]