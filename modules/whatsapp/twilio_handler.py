#!/usr/bin/env python3
"""
Twilio WhatsApp Handler for AVA OLO
Handles incoming WhatsApp messages via Twilio and processes them through CAVA
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from modules.cava.natural_registration import NaturalRegistrationFlow
from modules.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PhoneNumberCountryDetector:
    """Detects country from phone number prefix"""
    
    COUNTRY_CODES = {
        '+359': 'Bulgaria',     # Bulgarian mango farmers
        '+386': 'Slovenia', 
        '+385': 'Croatia',
        '+387': 'Bosnia and Herzegovina',
        '+381': 'Serbia',
        '+389': 'North Macedonia',
        '+382': 'Montenegro',
        '+36': 'Hungary',
        '+43': 'Austria',
        '+49': 'Germany',
        '+39': 'Italy',
        '+33': 'France',
        '+34': 'Spain',
        '+1': 'United States',
        '+44': 'United Kingdom',
    }
    
    LANGUAGE_MAP = {
        'Bulgaria': 'bg',
        'Slovenia': 'sl', 
        'Croatia': 'hr',
        'Bosnia and Herzegovina': 'bs',
        'Serbia': 'sr',
        'North Macedonia': 'mk',
        'Montenegro': 'me',
        'Hungary': 'hu',
        'Austria': 'de',
        'Germany': 'de',
        'Italy': 'it',
        'France': 'fr',
        'Spain': 'es',
        'United States': 'en',
        'United Kingdom': 'en',
    }
    
    @classmethod
    def detect_country_and_language(cls, phone_number: str) -> Tuple[str, str]:
        """
        Detect country and language from phone number
        Returns (country, language_code)
        """
        # Clean the phone number
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        
        # Try to match country codes (longest first)
        for code in sorted(cls.COUNTRY_CODES.keys(), key=len, reverse=True):
            if phone.startswith(code):
                country = cls.COUNTRY_CODES[code]
                language = cls.LANGUAGE_MAP.get(country, 'en')
                logger.info(f"Detected country: {country}, language: {language} from phone: {phone}")
                return country, language
        
        # Default to English if no match
        logger.warning(f"Could not detect country from phone number: {phone}, defaulting to English")
        return 'Unknown', 'en'

class TwilioWhatsAppHandler:
    """Main handler for Twilio WhatsApp integration"""
    
    def __init__(self):
        # Twilio configuration
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')  # whatsapp:+1234567890
        
        if not all([self.account_sid, self.auth_token, self.twilio_whatsapp_number]):
            logger.error("Missing Twilio configuration. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER")
            raise ValueError("Twilio configuration incomplete")
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        # Initialize CAVA registration engine
        self.natural_registration = NaturalRegistrationFlow()
        
        # Database connection
        self.db_manager = DatabaseManager()
        
        logger.info(f"TwilioWhatsAppHandler initialized with number: {self.twilio_whatsapp_number}")
    
    async def handle_incoming_message(self, from_number: str, body: str, message_sid: str = None) -> str:
        """
        Handle incoming WhatsApp message from Twilio webhook
        
        Args:
            from_number: WhatsApp number (format: whatsapp:+1234567890)
            body: Message text
            message_sid: Twilio message SID
            
        Returns:
            Response message to send back via Twilio
        """
        try:
            logger.info(f"=== WHATSAPP MESSAGE RECEIVED ===")
            logger.info(f"From: {from_number}")
            logger.info(f"Body: {body}")
            logger.info(f"Message SID: {message_sid}")
            
            # Extract phone number (remove whatsapp: prefix)
            phone_number = from_number.replace('whatsapp:', '') if from_number.startswith('whatsapp:') else from_number
            
            # Detect country and language from phone number
            country, language = PhoneNumberCountryDetector.detect_country_and_language(phone_number)
            
            # Store incoming message in database
            self.store_message_sync(phone_number, body, 'incoming', message_sid, country, language)
            
            # Process message through CAVA registration
            # Use phone number as session_id for WhatsApp conversations
            session_id = phone_number
            
            # Add language context to the session
            session = self.natural_registration.get_or_create_session(session_id)
            session['language'] = language
            session['country'] = country
            session['wa_phone_number'] = phone_number
            
            # Process the message
            result = await self.natural_registration.process_message(session_id, body)
            
            response_text = result.get('response', 'Hello! I am AVA, your agricultural assistant. How can I help you today?')
            
            # Store outgoing response in database
            self.store_message_sync(phone_number, response_text, 'outgoing', None, country, language)
            
            # If registration is complete, create farmer account
            if result.get('registration_complete') and 'collected_data' in result:
                await self.handle_registration_completion(result['collected_data'], phone_number, country)
            
            logger.info(f"Response prepared: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {str(e)}")
            error_response = "I'm sorry, I encountered an error. Please try again later."
            
            # Store error response
            try:
                self.store_message_sync(phone_number, error_response, 'outgoing', None, 'Unknown', 'en')
            except:
                pass
            
            return error_response
    
    def store_message_sync(self, phone_number: str, message: str, direction: str, 
                          message_sid: str = None, country: str = 'Unknown', 
                          language: str = 'en'):
        """
        Store WhatsApp message in chat_messages table
        
        Args:
            phone_number: WhatsApp phone number
            message: Message content
            direction: 'incoming' or 'outgoing'
            message_sid: Twilio message SID
            country: Detected country
            language: Detected language
        """
        try:
            # First, ensure chat_messages table exists with wa_phone_number column
            self.ensure_chat_messages_table_sync()
            
            insert_query = """
                INSERT INTO chat_messages (
                    wa_phone_number, message_content, direction, 
                    message_sid, country, language, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                phone_number,
                message,
                direction,
                message_sid,
                country,
                language,
                datetime.utcnow()
            )
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(insert_query, values)
                    conn.commit()
            
            logger.info(f"Stored {direction} message from {phone_number} in database")
            
        except Exception as e:
            logger.error(f"Failed to store message in database: {str(e)}")
    
    def ensure_chat_messages_table_sync(self):
        """Ensure chat_messages table exists with all required columns"""
        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    wa_phone_number VARCHAR(20),
                    message_content TEXT,
                    direction VARCHAR(10),
                    message_sid VARCHAR(100),
                    country VARCHAR(50),
                    language VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(100),
                    farmer_id INTEGER
                );
                
                -- Add indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_chat_messages_phone ON chat_messages(wa_phone_number);
                CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
            """
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_table_query)
                    conn.commit()
            
            logger.info("Ensured chat_messages table exists with required columns")
            
        except Exception as e:
            logger.error(f"Failed to create chat_messages table: {str(e)}")
    
    async def handle_registration_completion(self, collected_data: Dict, phone_number: str, country: str):
        """Handle completed registration by creating farmer account"""
        try:
            logger.info(f"=== REGISTRATION COMPLETED FOR {phone_number} ===")
            logger.info(f"Collected data: {collected_data}")
            
            # Import create_farmer_account here to avoid circular imports
            from modules.auth.routes import create_farmer_account
            
            # Prepare farmer data for account creation
            farmer_data = {
                "farm_name": collected_data.get("farm_name", f"Farm - {collected_data.get('first_name', 'Unknown')}"),
                "manager_name": collected_data.get("first_name", ""),
                "manager_last_name": collected_data.get("last_name", ""),
                "wa_phone_number": phone_number,
                "phone": phone_number,  # Use same number for both fields
                "email": collected_data.get("email", ""),
                "city": collected_data.get("city", ""),
                "country": country,
                "password": collected_data.get("password", "default123"),  # Generate or ask for password
                "fields": []  # Can be added later through the system
            }
            
            # Create the farmer account
            result = await create_farmer_account(farmer_data)
            
            if result.get('success'):
                logger.info(f"✅ Created farmer account for {phone_number}: ID {result.get('farmer_id')}")
                
                # Send confirmation message
                confirmation = f"🎉 Welcome to AVA OLO! Your account has been created successfully. You can now ask me questions about farming, get advice, and manage your agricultural activities. How can I help you today?"
                
                # Send confirmation via WhatsApp
                await self.send_whatsapp_message(phone_number, confirmation)
                
            else:
                logger.error(f"❌ Failed to create farmer account: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error handling registration completion: {str(e)}")
    
    async def send_whatsapp_message(self, to_number: str, message: str) -> bool:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to_number: WhatsApp number (with or without whatsapp: prefix)
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure number has whatsapp: prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message_instance = self.client.messages.create(
                body=message,
                from_=self.twilio_whatsapp_number,
                to=to_number
            )
            
            logger.info(f"Sent WhatsApp message to {to_number}: {message_instance.sid}")
            
            # Store the outgoing message
            phone_only = to_number.replace('whatsapp:', '')
            country, language = PhoneNumberCountryDetector.detect_country_and_language(phone_only)
            self.store_message_sync(phone_only, message, 'outgoing', message_instance.sid, country, language)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {str(e)}")
            return False
    
    def create_twiml_response(self, message: str) -> str:
        """
        Create TwiML response for Twilio webhook
        
        Args:
            message: Response message
            
        Returns:
            TwiML XML string
        """
        response = MessagingResponse()
        response.message(message)
        
        twiml_str = str(response)
        logger.info(f"Created TwiML response: {twiml_str}")
        
        return twiml_str
    
    def get_conversation_history_sync(self, phone_number: str, limit: int = 50) -> list:
        """Get conversation history for a phone number"""
        try:
            query = """
                SELECT message_content, direction, created_at, country, language
                FROM chat_messages 
                WHERE wa_phone_number = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (phone_number, limit))
                    results = cursor.fetchall()
            
            history = []
            for row in results:
                history.append({
                    'message': row[0],
                    'direction': row[1],
                    'timestamp': row[2],
                    'country': row[3],
                    'language': row[4]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []

# Singleton instance
_whatsapp_handler = None

def get_whatsapp_handler() -> TwilioWhatsAppHandler:
    """Get singleton WhatsApp handler instance"""
    global _whatsapp_handler
    if _whatsapp_handler is None:
        _whatsapp_handler = TwilioWhatsAppHandler()
    return _whatsapp_handler