#!/usr/bin/env python3
"""
Enhanced CAVA Registration - Pure LLM-driven conversation with full validation
Collects: first_name, last_name, whatsapp_number, password (with confirmation)
Language-aware, validates WhatsApp format, checks duplicates, enforces password rules
"""
from typing import Dict, Optional, Tuple
import logging
import re
import json
import asyncio
from datetime import datetime, timedelta
from langdetect import detect, LangDetectException
from passlib.context import CryptContext

from modules.chat.openai_chat import get_openai_chat
from modules.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class EnhancedCAVARegistration:
    """Pure LLM-driven registration with validation and multi-language support"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.chat_service = get_openai_chat()
        self.db_manager = DatabaseManager()
        
        # Start session cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """Get or create registration session with timeout tracking"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "collected": {
                    "first_name": None,
                    "last_name": None,
                    "whatsapp": None,
                    "password": None,
                    "password_confirmed": False
                },
                "conversation_history": [],
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "complete": False,
                "language": "en",  # Default to English
                "awaiting_password_confirmation": False,
                "temp_password": None
            }
        else:
            # Update last activity
            self.sessions[session_id]["last_activity"] = datetime.utcnow()
            
        return self.sessions[session_id]
    
    def detect_language(self, text: str) -> str:
        """Detect language from text"""
        try:
            if len(text.strip()) > 3:
                lang = detect(text)
                # Map to our supported languages
                lang_map = {
                    'bg': 'bg',  # Bulgarian
                    'sl': 'sl',  # Slovenian  
                    'hr': 'hr',  # Croatian
                    'sr': 'sr',  # Serbian
                    'mk': 'mk',  # Macedonian
                    'en': 'en',  # English
                    'es': 'es',  # Spanish
                    'fr': 'fr',  # French
                    'de': 'de',  # German
                    'it': 'it',  # Italian
                }
                return lang_map.get(lang, 'en')
        except (LangDetectException, Exception):
            pass
        return 'en'
    
    async def validate_whatsapp(self, number: str) -> Tuple[bool, str]:
        """Validate WhatsApp number format and check for duplicates"""
        # Clean the number
        cleaned = re.sub(r'[^\d+]', '', number)
        
        # Check format (must have country code)
        if not re.match(r'^\+\d{10,15}$', cleaned):
            return False, "needs_country_code"
        
        # Check for duplicates in database
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM farmers WHERE wa_phone_number = %s",
                        (cleaned,)
                    )
                    if cursor.fetchone():
                        return False, "already_registered"
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            # Continue anyway - don't block registration
        
        return True, "valid"
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password meets requirements"""
        if len(password) < 8:
            return False, "too_short"
        if password.isdigit():
            return False, "only_numbers"
        if password.isalpha():
            return False, "only_letters"
        return True, "valid"
    
    def is_complete(self, collected: Dict) -> bool:
        """Check if all required fields are collected and confirmed"""
        return all([
            collected.get("first_name"),
            collected.get("last_name"), 
            collected.get("whatsapp"),
            collected.get("password"),
            collected.get("password_confirmed", False)
        ])
    
    async def process_message(self, session_id: str, message: str) -> Dict:
        """Process user message with enhanced LLM conversation"""
        session = self.get_or_create_session(session_id)
        
        # Detect language
        detected_lang = self.detect_language(message)
        if session["language"] == "en" and detected_lang != "en":
            session["language"] = detected_lang
        
        # Add user message to history
        session["conversation_history"].append(f"User: {message}")
        
        # If already complete, redirect to main chat
        if session["complete"]:
            return {
                "response": self._get_completion_message(session["language"]),
                "registration_complete": True,
                "collected_data": session["collected"],
                "action": "redirect_to_chat"
            }
        
        # Check if we're waiting for password confirmation
        if session["awaiting_password_confirmation"]:
            return await self._handle_password_confirmation(session_id, session, message)
        
        # Build comprehensive LLM prompt
        prompt = self._build_registration_prompt(session, message)
        
        try:
            # Get LLM response
            llm_result = await self.chat_service.send_message(
                f"enhanced_reg_{session_id}",
                prompt,
                {"system_prompt_override": "You are AVA's registration assistant. Always respond in valid JSON format."}
            )
            
            response_text = llm_result.get("response", "")
            
            # Parse LLM response
            response_data = self._parse_llm_response(response_text)
            
            # Process extracted data
            await self._process_extracted_data(session, response_data)
            
            # Generate final response
            return await self._generate_response(session_id, session, response_data)
            
        except Exception as e:
            logger.error(f"Error in enhanced CAVA registration: {e}")
            return self._fallback_response(session, message)
    
    def _build_registration_prompt(self, session: Dict, message: str) -> str:
        """Build comprehensive prompt for LLM"""
        collected = session["collected"]
        lang = session["language"]
        
        # Language-specific examples
        lang_examples = {
            'bg': "Здравей, казвам се Иван Петров",
            'sl': "Pozdravljeni, sem Peter Novak", 
            'en': "Hi, I'm John Smith"
        }
        
        prompt = f"""You are AVA's registration assistant helping a farmer register. 

CRITICAL: First determine if the user wants to register! Common registration intents:
- "I want to register" / "Искам да се регистрирам" (Bulgarian) / "Želim se registrirati" (Slovenian)
- "Sign me up" / "Create account" / "New user"
- "How do I join?" / "Start registration"
- Providing their name unprompted often indicates registration intent

If user shows registration intent, help them register. If not, explain you can help them register.
        
Required fields to collect:
1. first_name - Their given/first name
2. last_name - Their family/surname  
3. whatsapp - WhatsApp number WITH country code (like +359, +386, +1, etc.)
4. password - Minimum 8 characters, mix of letters and numbers recommended

Currently collected:
- First name: {collected.get('first_name') or 'NOT PROVIDED'}
- Last name: {collected.get('last_name') or 'NOT PROVIDED'}
- WhatsApp: {collected.get('whatsapp') or 'NOT PROVIDED'}
- Password: {'PROVIDED' if collected.get('password') else 'NOT PROVIDED'}
- Password confirmed: {'YES' if collected.get('password_confirmed') else 'NO'}

User's detected language: {lang} ({lang_examples.get(lang, 'Hello, I am John')})

Recent conversation:
{chr(10).join(session['conversation_history'][-10:])}

User just said: "{message}"

CRITICAL RULES:
1. ALWAYS respond in the user's language ({lang})
2. Extract ANY registration data from their message
3. If they give multiple pieces of info at once (e.g., "I'm Peter Horvat, +38641348050"), extract ALL
4. For WhatsApp numbers, REQUIRE country code. If missing, ask for it
5. For passwords, after collecting initial password, ask for confirmation
6. If asked off-topic questions, politely redirect: "I'm here to help you register. We can discuss that after registration."
7. Be natural and conversational, not robotic
8. If WhatsApp already exists in our system, inform them
9. Validate password is at least 8 characters

Language-specific responses:
- Bulgarian (bg): Use Cyrillic, informal tone
- Slovenian (sl): Polite, use "vi" form initially  
- English (en): Friendly, professional

Return JSON:
{{
    "response": "Your response in {lang} language",
    "extracted": {{
        "first_name": "value if found or null",
        "last_name": "value if found or null", 
        "whatsapp": "value if found or null",
        "password": "value if found or null",
        "password_confirmation": "value if confirming password or null"
    }},
    "action": "continue|redirect|request_confirmation",
    "validation_needed": "whatsapp|password|none"
}}"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse JSON from LLM response"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        # Fallback structure
        return {
            "response": response_text,
            "extracted": {},
            "action": "continue",
            "validation_needed": "none"
        }
    
    async def _process_extracted_data(self, session: Dict, response_data: Dict):
        """Process and validate extracted data"""
        extracted = response_data.get("extracted", {})
        collected = session["collected"]
        
        # Update basic fields
        for field in ["first_name", "last_name"]:
            if extracted.get(field) and extracted[field] not in ["null", None]:
                collected[field] = extracted[field].strip()
        
        # Handle WhatsApp with validation
        if extracted.get("whatsapp") and extracted["whatsapp"] not in ["null", None]:
            number = extracted["whatsapp"].strip()
            is_valid, reason = await self.validate_whatsapp(number)
            
            if is_valid:
                collected["whatsapp"] = number
            else:
                # Store validation result for response generation
                session["whatsapp_validation"] = reason
        
        # Handle password
        if extracted.get("password") and extracted["password"] not in ["null", None]:
            password = extracted["password"].strip()
            is_valid, reason = self.validate_password(password)
            
            if is_valid:
                if not collected.get("password"):
                    # First time password entry
                    session["temp_password"] = password
                    session["awaiting_password_confirmation"] = True
                    response_data["action"] = "request_confirmation"
                else:
                    # This might be a new password, treat as change
                    session["temp_password"] = password
                    session["awaiting_password_confirmation"] = True
                    response_data["action"] = "request_confirmation"
            else:
                session["password_validation"] = reason
        
        # Handle password confirmation
        if extracted.get("password_confirmation") and session.get("temp_password"):
            if extracted["password_confirmation"] == session["temp_password"]:
                collected["password"] = session["temp_password"]
                collected["password_confirmed"] = True
                session["awaiting_password_confirmation"] = False
                session["temp_password"] = None
            else:
                session["password_mismatch"] = True
    
    async def _handle_password_confirmation(self, session_id: str, session: Dict, message: str) -> Dict:
        """Handle password confirmation step"""
        # Check if the message matches the temp password
        if message.strip() == session.get("temp_password", ""):
            session["collected"]["password"] = session["temp_password"]
            session["collected"]["password_confirmed"] = True
            session["awaiting_password_confirmation"] = False
            session["temp_password"] = None
            
            # Check if registration is now complete
            if self.is_complete(session["collected"]):
                return await self._complete_registration(session_id, session)
            else:
                # Continue collecting other fields
                return await self.process_message(session_id, "")
        else:
            # Password mismatch
            lang = session["language"]
            mismatch_messages = {
                'bg': "Паролите не съвпадат. Моля, въведете паролата отново:",
                'sl': "Gesli se ne ujemata. Prosim, vnesite geslo ponovno:",
                'en': "Passwords don't match. Please enter your password again:"
            }
            
            return {
                "response": mismatch_messages.get(lang, mismatch_messages['en']),
                "registration_complete": False,
                "action": "continue"
            }
    
    async def _generate_response(self, session_id: str, session: Dict, response_data: Dict) -> Dict:
        """Generate final response based on session state"""
        lang = session["language"]
        
        # Check for validation issues
        if session.get("whatsapp_validation") == "already_registered":
            session.pop("whatsapp_validation")
            return {
                "response": self._get_duplicate_message(lang),
                "registration_complete": False,
                "action": "continue"
            }
        
        if session.get("whatsapp_validation") == "needs_country_code":
            session.pop("whatsapp_validation")
            return {
                "response": self._get_country_code_message(lang),
                "registration_complete": False,
                "action": "continue"
            }
        
        if session.get("password_validation"):
            reason = session.pop("password_validation")
            return {
                "response": self._get_password_error_message(lang, reason),
                "registration_complete": False,
                "action": "continue"
            }
        
        # Check if complete
        if self.is_complete(session["collected"]):
            return await self._complete_registration(session_id, session)
        
        # Return LLM response
        return {
            "response": response_data.get("response", self._get_fallback_message(lang)),
            "registration_complete": False,
            "action": response_data.get("action", "continue")
        }
    
    async def _complete_registration(self, session_id: str, session: Dict) -> Dict:
        """Complete registration and create database account"""
        collected = session["collected"]
        
        try:
            # Create farmer account
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Hash the password
                    password_hash = pwd_context.hash(collected["password"])
                    
                    # Insert farmer
                    cursor.execute("""
                        INSERT INTO farmers (
                            manager_name, manager_last_name, wa_phone_number,
                            password_hash, farm_name, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        collected["first_name"],
                        collected["last_name"],
                        collected["whatsapp"],
                        password_hash,
                        f"{collected['first_name']}'s Farm",  # Default farm name
                        datetime.utcnow()
                    ))
                    
                    farmer_id = cursor.fetchone()[0]
                    conn.commit()
            
            # Mark session as complete
            session["complete"] = True
            session["farmer_id"] = farmer_id
            
            # Clear sensitive data
            session["collected"]["password"] = None
            session["temp_password"] = None
            
            lang = session["language"]
            return {
                "response": self._get_success_message(lang, collected["first_name"]),
                "registration_complete": True,
                "farmer_id": farmer_id,
                "action": "complete"
            }
            
        except Exception as e:
            logger.error(f"Failed to create farmer account: {e}")
            return {
                "response": self._get_error_message(session["language"]),
                "registration_complete": False,
                "action": "continue"
            }
    
    def _get_duplicate_message(self, lang: str) -> str:
        """Get duplicate WhatsApp message in user's language"""
        messages = {
            'bg': "Този WhatsApp номер вече е регистриран. Моля, използвайте друг номер или влезте в профила си.",
            'sl': "Ta WhatsApp številka je že registrirana. Prosim uporabite drugo številko ali se prijavite.",
            'en': "This WhatsApp number is already registered. Please use a different number or log in."
        }
        return messages.get(lang, messages['en'])
    
    def _get_country_code_message(self, lang: str) -> str:
        """Get country code request message"""
        messages = {
            'bg': "Моля, включете кода на държавата (например +359 за България)",
            'sl': "Prosim vključite kodo države (npr. +386 za Slovenijo)",
            'en': "Please include your country code (e.g., +1 for USA, +44 for UK)"
        }
        return messages.get(lang, messages['en'])
    
    def _get_password_error_message(self, lang: str, reason: str) -> str:
        """Get password error message"""
        if reason == "too_short":
            messages = {
                'bg': "Паролата трябва да е поне 8 символа. Моля, изберете по-дълга парола.",
                'sl': "Geslo mora imeti vsaj 8 znakov. Prosim izberite daljše geslo.",
                'en': "Password must be at least 8 characters. Please choose a longer password."
            }
        else:
            messages = {
                'bg': "Паролата трябва да съдържа букви и цифри. Моля, опитайте отново.",
                'sl': "Geslo mora vsebovati črke in številke. Prosim poskusite ponovno.",
                'en': "Password should contain both letters and numbers. Please try again."
            }
        return messages.get(lang, messages['en'])
    
    def _get_success_message(self, lang: str, name: str) -> str:
        """Get success message"""
        messages = {
            'bg': f"🎉 Поздравления, {name}! Регистрацията е завършена успешно. Добре дошли в AVA OLO! Сега можете да задавате въпроси за земеделието.",
            'sl': f"🎉 Čestitam, {name}! Registracija je uspešno zaključena. Dobrodošli v AVA OLO! Zdaj lahko postavljate vprašanja o kmetijstvu.",
            'en': f"🎉 Congratulations, {name}! Registration complete. Welcome to AVA OLO! You can now ask questions about farming."
        }
        return messages.get(lang, messages['en'])
    
    def _get_completion_message(self, lang: str) -> str:
        """Get already complete message"""
        messages = {
            'bg': "Вече сте регистрирани! Можете да задавате въпроси за земеделието.",
            'sl': "Že ste registrirani! Lahko postavljate vprašanja o kmetijstvu.",
            'en': "You're already registered! You can ask questions about farming."
        }
        return messages.get(lang, messages['en'])
    
    def _get_error_message(self, lang: str) -> str:
        """Get error message"""
        messages = {
            'bg': "Съжалявам, възникна грешка. Моля, опитайте отново.",
            'sl': "Oprostite, prišlo je do napake. Prosim poskusite ponovno.",
            'en': "Sorry, an error occurred. Please try again."
        }
        return messages.get(lang, messages['en'])
    
    def _get_fallback_message(self, lang: str) -> str:
        """Get fallback message"""
        messages = {
            'bg': "Здравейте! Аз съм AVA. Моля, споделете вашето име, за да започнем регистрацията.",
            'sl': "Pozdravljeni! Sem AVA. Prosim delite svoje ime, da začnemo registracijo.",
            'en': "Hello! I'm AVA. Please share your name to start registration."
        }
        return messages.get(lang, messages['en'])
    
    def _fallback_response(self, session: Dict, message: str) -> Dict:
        """Fallback response when LLM fails"""
        lang = session["language"]
        collected = session["collected"]
        
        if not collected.get("first_name"):
            response = self._get_fallback_message(lang)
        elif not collected.get("last_name"):
            messages = {
                'bg': f"Приятно ми е, {collected['first_name']}! Какво е вашето фамилно име?",
                'sl': f"Lepo vas spoznati, {collected['first_name']}! Kakšen je vaš priimek?",
                'en': f"Nice to meet you, {collected['first_name']}! What's your last name?"
            }
            response = messages.get(lang, messages['en'])
        elif not collected.get("whatsapp"):
            messages = {
                'bg': f"Благодаря, {collected['first_name']} {collected['last_name']}! Какъв е вашият WhatsApp номер (с код на държавата)?",
                'sl': f"Hvala, {collected['first_name']} {collected['last_name']}! Kakšna je vaša WhatsApp številka (s kodo države)?",
                'en': f"Thanks, {collected['first_name']} {collected['last_name']}! What's your WhatsApp number (with country code)?"
            }
            response = messages.get(lang, messages['en'])
        elif not collected.get("password"):
            messages = {
                'bg': "Отлично! Сега изберете парола (поне 8 символа):",
                'sl': "Odlično! Zdaj izberite geslo (vsaj 8 znakov):",
                'en': "Great! Now please choose a password (at least 8 characters):"
            }
            response = messages.get(lang, messages['en'])
        else:
            response = self._get_success_message(lang, collected['first_name'])
        
        return {
            "response": response,
            "registration_complete": False,
            "action": "continue"
        }
    
    async def _periodic_cleanup(self):
        """Clean up expired sessions every minute"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            await self.cleanup_expired_sessions()
    
    async def cleanup_expired_sessions(self):
        """Remove sessions older than 5 minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        expired = []
        
        for session_id, data in self.sessions.items():
            if data["last_activity"] < cutoff and not data["complete"]:
                expired.append(session_id)
        
        for session_id in expired:
            logger.info(f"Cleaning up expired session: {session_id}")
            del self.sessions[session_id]
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data for debugging"""
        if session_id in self.sessions:
            return {
                "collected": self.sessions[session_id]["collected"],
                "language": self.sessions[session_id]["language"],
                "complete": self.sessions[session_id]["complete"],
                "created_at": self.sessions[session_id]["created_at"],
                "last_activity": self.sessions[session_id]["last_activity"]
            }
        return None