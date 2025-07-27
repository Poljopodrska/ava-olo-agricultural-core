#!/usr/bin/env python3
"""
CAVA Registration Engine - Intelligent registration using GPT-3.5
Handles natural conversation registration with data extraction and validation
Constitutional Amendment #15 compliant - 95%+ LLM intelligence
"""
import os
import logging
import json
import re
import bcrypt
import asyncio
import asyncpg
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Language detection
try:
    from langdetect import detect, LangDetectException
except ImportError:
    def detect(text):
        return 'en'
    class LangDetectException(Exception):
        pass

logger = logging.getLogger(__name__)

class CAVARegistrationEngine:
    """Intelligent registration engine using GPT-3.5 - Constitutional Amendment #15 compliant"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.sessions = {}  # Track registration sessions in memory
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
        
        logger.info("✅ CAVA Registration Engine initialized")
        logger.info(f"🔑 OpenAI API configured: {bool(self.api_key)}")
        logger.info(f"🗄️ Database configured: {self.db_config['host']}")
        
        # Test OpenAI connection if key available
        if self.api_key and not os.getenv("SKIP_OPENAI_TEST"):
            self._test_openai_connection()
    
    def _test_openai_connection(self):
        """Test OpenAI connection"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [{'role': 'user', 'content': 'test'}],
                'max_tokens': 5
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ OpenAI API connection verified")
                return True
            else:
                logger.warning(f"⚠️ OpenAI API test returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ OpenAI API test failed: {e}")
            return False
    
    async def process_registration_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process registration message with full CAVA intelligence"""
        
        # Get or create session
        session = self.sessions.get(session_id, {
            'first_name': None,
            'last_name': None,
            'wa_phone_number': None,
            'password': None,
            'password_confirmation': None,
            'language': None,
            'conversation_history': [],
            'created_at': datetime.utcnow().isoformat()
        })
        
        # Add user message to history
        session['conversation_history'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Build intelligent prompt for GPT-3.5
        system_prompt = self._build_registration_prompt(session)
        
        try:
            # Call OpenAI GPT-3.5
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    *[{'role': msg['role'], 'content': msg['content']} for msg in session['conversation_history']]
                ],
                'temperature': 0.7,
                'response_format': {'type': 'json_object'},
                'max_tokens': 500
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json()
                ai_content = ai_response['choices'][0]['message']['content']
                ai_data = json.loads(ai_content)
                
                # Update session with extracted data
                updated_fields = self._update_session_data(session, ai_data)
                
                # Add AI response to history
                session['conversation_history'].append({
                    'role': 'assistant',
                    'content': ai_data.get('response', 'I apologize, but I encountered an error. Please try again.'),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Check if registration complete
                registration_complete = ai_data.get('registration_complete', False) and self._is_complete(session)
                
                if registration_complete and not session.get('farmer_created'):
                    # Create farmer in database
                    farmer_id = await self._create_farmer(session)
                    if farmer_id:
                        session['farmer_id'] = farmer_id
                        session['farmer_created'] = True
                        session['completed_at'] = datetime.utcnow().isoformat()
                
                # Save session
                self.sessions[session_id] = session
                
                return {
                    'success': True,
                    'response': ai_data.get('response'),
                    'registration_complete': registration_complete,
                    'farmer_id': session.get('farmer_id'),
                    'collected_fields': self._get_collection_status(session),
                    'updated_fields': updated_fields,
                    'ai_connected': True,
                    'model_used': self.model,
                    'tokens_used': ai_response.get('usage', {}).get('total_tokens', 0)
                }
            else:
                return self._fallback_response(session, message)
                
        except Exception as e:
            logger.error(f"CAVA Registration Error: {e}")
            return self._fallback_response(session, message)
    
    def _build_registration_prompt(self, session: Dict[str, Any]) -> str:
        """Build intelligent registration prompt for GPT-3.5"""
        
        collected_summary = {
            'first_name': session.get('first_name'),
            'last_name': session.get('last_name'),
            'wa_phone_number': session.get('wa_phone_number'),
            'password': 'SET' if session.get('password') else None,
            'password_confirmed': session.get('password_confirmation') == session.get('password') if session.get('password') else False
        }
        
        return f"""You are CAVA, an intelligent agricultural assistant helping farmers register for AVA OLO.

Your job is to collect registration information through natural conversation and extract data from their messages.

REQUIRED REGISTRATION FIELDS:
- first_name: Their first/given name
- last_name: Their last/family name  
- wa_phone_number: WhatsApp phone number (with country code like +359, +386, etc.)
- password: A secure password (minimum 8 characters)
- password_confirmation: They must repeat the password to confirm it matches

CURRENT COLLECTED DATA: {json.dumps(collected_summary, indent=2)}

INSTRUCTIONS:
1. Analyze their message and extract ANY registration data you can find
2. Respond naturally in their language (detect from their message)
3. Guide them to provide the next missing piece of information
4. If they provide a password, ask them to repeat it for confirmation
5. When ALL fields are collected AND confirmed, mark registration as complete
6. Be conversational, friendly, and agricultural-focused
7. Handle any language (Bulgarian, English, Slovenian, etc.)

EXTRACTION RULES:
- Names can be in any format: "John Smith", "Петър", "My name is Maria", etc.
- Phone numbers: Look for +country_code followed by digits
- Passwords: Any mention of password, pass, парола, etc.
- Confirmations: When they repeat something after being asked to confirm

RESPONSE FORMAT (JSON):
{{
    "extracted_data": {{
        "first_name": "extracted_first_name_or_null",
        "last_name": "extracted_last_name_or_null", 
        "wa_phone_number": "extracted_phone_or_null",
        "password": "extracted_password_or_null",
        "password_confirmation": "extracted_confirmation_or_null"
    }},
    "response": "Your natural conversational response to the farmer",
    "registration_complete": false,
    "next_field_needed": "Description of what to ask for next",
    "language_detected": "detected_language"
}}

IMPORTANT: Only set registration_complete to true when ALL fields are collected AND password is confirmed!"""
    
    def _update_session_data(self, session: Dict[str, Any], ai_data: Dict[str, Any]) -> list:
        """Update session with extracted data and return list of updated fields"""
        updated_fields = []
        
        extracted = ai_data.get('extracted_data', {})
        
        for field in ['first_name', 'last_name', 'wa_phone_number', 'password']:
            if extracted.get(field) and not session.get(field):
                session[field] = extracted[field]
                updated_fields.append(field)
        
        # Handle password confirmation separately
        if extracted.get('password_confirmation'):
            session['password_confirmation'] = extracted['password_confirmation']
            updated_fields.append('password_confirmation')
        
        # Detect language
        if ai_data.get('language_detected'):
            session['language'] = ai_data['language_detected']
        
        return updated_fields
    
    def _is_complete(self, session: Dict[str, Any]) -> bool:
        """Check if all required fields are collected and confirmed"""
        return all([
            session.get('first_name'),
            session.get('last_name'),
            session.get('wa_phone_number'),
            session.get('password'),
            session.get('password_confirmation') == session.get('password')
        ])
    
    def _get_collection_status(self, session: Dict[str, Any]) -> Dict[str, bool]:
        """Get status of collected fields"""
        return {
            'first_name': bool(session.get('first_name')),
            'last_name': bool(session.get('last_name')),
            'wa_phone_number': bool(session.get('wa_phone_number')),
            'password': bool(session.get('password')),
            'password_confirmed': session.get('password_confirmation') == session.get('password') if session.get('password') else False
        }
    
    async def _create_farmer(self, session: Dict[str, Any]) -> Optional[int]:
        """Create farmer entry in database"""
        try:
            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(
                session['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Connect to database
            conn = await asyncpg.connect(**self.db_config)
            
            # Insert farmer
            farmer_id = await conn.fetchval("""
                INSERT INTO farmers (
                    first_name, last_name, wa_phone_number, 
                    password_hash, registration_date, country,
                    registration_method, ai_assisted
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, 
                session['first_name'],
                session['last_name'],
                session['wa_phone_number'],
                password_hash,
                datetime.utcnow(),
                self._detect_country(session['wa_phone_number']),
                'CAVA_REGISTRATION',
                True
            )
            
            await conn.close()
            return farmer_id
            
        except Exception as e:
            logger.error(f"Database error creating farmer: {e}")
            return None
    
    def _detect_country(self, phone_number: str) -> str:
        """Detect country from WhatsApp number prefix"""
        if phone_number.startswith('+359'):
            return 'Bulgaria'
        elif phone_number.startswith('+386'):
            return 'Slovenia'
        elif phone_number.startswith('+385'):
            return 'Croatia'
        elif phone_number.startswith('+381'):
            return 'Serbia'
        elif phone_number.startswith('+49'):
            return 'Germany'
        elif phone_number.startswith('+1'):
            return 'USA'
        else:
            return 'Unknown'
    
    def _fallback_response(self, session: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Fallback response when AI is unavailable"""
        
        # Simple field extraction without AI
        message_lower = message.lower()
        extracted_fields = []
        
        # Try to extract phone number
        import re
        phone_match = re.search(r'\+\d{1,4}\d{8,12}', message)
        if phone_match and not session.get('wa_phone_number'):
            session['wa_phone_number'] = phone_match.group()
            extracted_fields.append('wa_phone_number')
        
        # Determine what to ask for next
        if not session.get('first_name'):
            response = "Hello! I'm CAVA. To register, I need your first name. What should I call you?"
        elif not session.get('last_name'):
            response = f"Nice to meet you, {session['first_name']}! What's your last name?"
        elif not session.get('wa_phone_number'):
            response = "Great! Now I need your WhatsApp phone number (with country code, like +359...)."
        elif not session.get('password'):
            response = "Perfect! Please create a password for your account (minimum 8 characters)."
        elif not session.get('password_confirmation'):
            response = "Please type your password again to confirm it."
        elif session.get('password_confirmation') != session.get('password'):
            response = "The passwords don't match. Please type your password again."
        else:
            response = "Thank you! Your registration is complete. Welcome to AVA OLO!"
        
        self.sessions[session.get('session_id', 'fallback')] = session
        
        return {
            'success': True,
            'response': response,
            'registration_complete': self._is_complete(session),
            'collected_fields': self._get_collection_status(session),
            'ai_connected': False,
            'fallback_mode': True
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get registration session status"""
        session = self.sessions.get(session_id, {})
        
        return {
            'session_exists': bool(session),
            'fields_collected': self._get_collection_status(session),
            'completed': session.get('farmer_created', False),
            'farmer_id': session.get('farmer_id'),
            'conversation_length': len(session.get('conversation_history', [])),
            'language': session.get('language'),
            'created_at': session.get('created_at'),
            'completed_at': session.get('completed_at')
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear registration session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

# Singleton instance
_cava_engine = None

def get_cava_registration_engine() -> CAVARegistrationEngine:
    """Get or create CAVA registration engine instance"""
    global _cava_engine
    if _cava_engine is None:
        _cava_engine = CAVARegistrationEngine()
    return _cava_engine