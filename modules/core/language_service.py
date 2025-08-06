#!/usr/bin/env python3
"""
Multi-Language Intelligence Service
Handles IP-based detection, WhatsApp country mapping, and language persistence
"""
import logging
import re
from typing import Optional, Dict, Tuple
import httpx
import json

logger = logging.getLogger(__name__)

class LanguageService:
    """
    Intelligent language detection and management service
    """
    
    # WhatsApp country code to language mapping
    COUNTRY_CODE_TO_LANGUAGE = {
        # Balkans
        '+386': 'sl',  # Slovenia → Slovenian
        '+385': 'hr',  # Croatia → Croatian  
        '+359': 'bg',  # Bulgaria → Bulgarian
        '+381': 'sr',  # Serbia → Serbian
        '+389': 'mk',  # North Macedonia → Macedonian
        '+387': 'bs',  # Bosnia → Bosnian
        '+382': 'me',  # Montenegro → Montenegrin
        '+383': 'sq',  # Kosovo → Albanian
        
        # Central Europe
        '+43': 'de',   # Austria → German
        '+49': 'de',   # Germany → German
        '+41': 'de',   # Switzerland → German (primary)
        '+420': 'cs',  # Czech Republic → Czech
        '+421': 'sk',  # Slovakia → Slovak
        '+36': 'hu',   # Hungary → Hungarian
        '+48': 'pl',   # Poland → Polish
        
        # Southern Europe
        '+39': 'it',   # Italy → Italian
        '+34': 'es',   # Spain → Spanish
        '+351': 'pt',  # Portugal → Portuguese
        '+30': 'el',   # Greece → Greek
        '+33': 'fr',   # France → French
        
        # English-speaking
        '+1': 'en',    # USA/Canada → English
        '+44': 'en',   # UK → English
        '+353': 'en',  # Ireland → English
        '+61': 'en',   # Australia → English
        '+64': 'en',   # New Zealand → English
        '+91': 'en',   # India → English (primary business)
        
        # Other European
        '+31': 'nl',   # Netherlands → Dutch
        '+32': 'nl',   # Belgium → Dutch/French
        '+45': 'da',   # Denmark → Danish
        '+46': 'sv',   # Sweden → Swedish
        '+47': 'no',   # Norway → Norwegian
        '+358': 'fi',  # Finland → Finnish
        '+372': 'et',  # Estonia → Estonian
        '+371': 'lv',  # Latvia → Latvian
        '+370': 'lt',  # Lithuania → Lithuanian
        '+40': 'ro',   # Romania → Romanian
        '+90': 'tr',   # Turkey → Turkish
        '+380': 'uk',  # Ukraine → Ukrainian
        '+7': 'ru',    # Russia → Russian
        '+375': 'be',  # Belarus → Belarusian
    }
    
    # IP country to language mapping
    COUNTRY_TO_LANGUAGE = {
        # Primary mappings
        'SI': 'sl',  # Slovenia
        'HR': 'hr',  # Croatia
        'BG': 'bg',  # Bulgaria
        'AT': 'de',  # Austria
        'DE': 'de',  # Germany
        'CH': 'de',  # Switzerland
        'IT': 'it',  # Italy
        'ES': 'es',  # Spain
        'FR': 'fr',  # France
        'GB': 'en',  # United Kingdom
        'US': 'en',  # United States
        'CA': 'en',  # Canada
        'AU': 'en',  # Australia
        'NZ': 'en',  # New Zealand
        'IN': 'en',  # India
        'RS': 'sr',  # Serbia
        'BA': 'bs',  # Bosnia
        'ME': 'me',  # Montenegro
        'MK': 'mk',  # North Macedonia
        'AL': 'sq',  # Albania
        'XK': 'sq',  # Kosovo
        'CZ': 'cs',  # Czech Republic
        'SK': 'sk',  # Slovakia
        'HU': 'hu',  # Hungary
        'PL': 'pl',  # Poland
        'RO': 'ro',  # Romania
        'GR': 'el',  # Greece
        'PT': 'pt',  # Portugal
        'NL': 'nl',  # Netherlands
        'BE': 'nl',  # Belgium
        'DK': 'da',  # Denmark
        'SE': 'sv',  # Sweden
        'NO': 'no',  # Norway
        'FI': 'fi',  # Finland
        'EE': 'et',  # Estonia
        'LV': 'lv',  # Latvia
        'LT': 'lt',  # Lithuania
        'TR': 'tr',  # Turkey
        'UA': 'uk',  # Ukraine
        'RU': 'ru',  # Russia
        'BY': 'be',  # Belarus
    }
    
    # Language code to full name mapping
    LANGUAGE_NAMES = {
        'en': 'English',
        'sl': 'Slovenian',
        'hr': 'Croatian',
        'bg': 'Bulgarian',
        'sr': 'Serbian',
        'bs': 'Bosnian',
        'me': 'Montenegrin',
        'mk': 'Macedonian',
        'sq': 'Albanian',
        'de': 'German',
        'it': 'Italian',
        'es': 'Spanish',
        'fr': 'French',
        'pt': 'Portuguese',
        'el': 'Greek',
        'cs': 'Czech',
        'sk': 'Slovak',
        'hu': 'Hungarian',
        'pl': 'Polish',
        'ro': 'Romanian',
        'nl': 'Dutch',
        'da': 'Danish',
        'sv': 'Swedish',
        'no': 'Norwegian',
        'fi': 'Finnish',
        'et': 'Estonian',
        'lv': 'Latvian',
        'lt': 'Lithuanian',
        'tr': 'Turkish',
        'uk': 'Ukrainian',
        'ru': 'Russian',
        'be': 'Belarusian',
    }
    
    def __init__(self):
        """Initialize language service"""
        self.default_language = 'en'
        
    async def detect_language_from_ip(self, ip_address: str) -> str:
        """
        Detect language from IP address using geolocation
        Falls back to English if detection fails
        """
        try:
            # Skip localhost/private IPs
            if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.'):
                logger.info(f"Private IP {ip_address}, defaulting to English")
                return self.default_language
            
            # Use ip-api.com for free geolocation (no API key needed)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip_address}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        country_code = data.get('countryCode', '')
                        detected_language = self.COUNTRY_TO_LANGUAGE.get(
                            country_code, 
                            self.default_language
                        )
                        
                        logger.info(f"IP {ip_address} → Country {country_code} → Language {detected_language}")
                        return detected_language
                        
        except Exception as e:
            logger.warning(f"IP geolocation failed for {ip_address}: {e}")
        
        return self.default_language
    
    def detect_language_from_whatsapp(self, whatsapp_number: str) -> str:
        """
        Detect language from WhatsApp number country code
        """
        # Clean the number - keep only digits and +
        clean_number = re.sub(r'[^\d+]', '', whatsapp_number)
        
        # Ensure it starts with + (required format)
        if not clean_number.startswith('+'):
            clean_number = '+' + clean_number
        
        # Try to match country codes (longest match first)
        for length in [4, 3, 2, 1]:  # Some country codes are up to 4 digits
            country_code = clean_number[:length+1]  # +1 for the + sign
            if country_code in self.COUNTRY_CODE_TO_LANGUAGE:
                detected_language = self.COUNTRY_CODE_TO_LANGUAGE[country_code]
                logger.info(f"WhatsApp {whatsapp_number} → Country code {country_code} → Language {detected_language}")
                return detected_language
        
        logger.warning(f"Unknown country code for {whatsapp_number}, defaulting to English")
        return self.default_language
    
    async def get_farmer_language(self, farmer_id: int, db_connection) -> str:
        """
        Get stored language preference from database
        Falls back to English if not set
        """
        try:
            result = await db_connection.fetchrow(
                "SELECT language_preference FROM farmers WHERE id = $1",
                farmer_id
            )
            
            if result and result['language_preference']:
                return result['language_preference']
                
        except Exception as e:
            logger.error(f"Error fetching language preference for farmer {farmer_id}: {e}")
        
        return self.default_language
    
    async def update_farmer_language(self, farmer_id: int, new_language: str, db_connection) -> bool:
        """
        Update language preference in database
        """
        try:
            # Validate language code
            if new_language not in self.LANGUAGE_NAMES:
                logger.warning(f"Invalid language code: {new_language}")
                return False
            
            await db_connection.execute(
                "UPDATE farmers SET language_preference = $1 WHERE id = $2",
                new_language, farmer_id
            )
            
            logger.info(f"Updated farmer {farmer_id} language preference to {new_language}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating language preference for farmer {farmer_id}: {e}")
            return False
    
    def get_language_name(self, language_code: str) -> str:
        """Get full language name from code"""
        return self.LANGUAGE_NAMES.get(language_code, 'English')
    
    def detect_language_change_request(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if farmer is requesting a language change
        Returns (is_change_request, requested_language_code)
        """
        message_lower = message.lower()
        
        # Language change patterns
        change_patterns = [
            r'speak\s+(\w+)',
            r'talk\s+in\s+(\w+)',
            r'switch\s+to\s+(\w+)',
            r'change\s+to\s+(\w+)',
            r'can\s+you\s+speak\s+(\w+)',
            r'please\s+speak\s+(\w+)',
            r'use\s+(\w+)\s+language',
            r'говори\s+(\w+)',  # Bulgarian: speak
            r'govori\s+(\w+)',  # Croatian/Serbian: speak
            r'parla\s+(\w+)',   # Italian: speak
            r'habla\s+(\w+)',   # Spanish: speak
            r'sprich\s+(\w+)',  # German: speak
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, message_lower)
            if match:
                requested_language_name = match.group(1).lower()
                
                # Map language names to codes
                for code, name in self.LANGUAGE_NAMES.items():
                    if requested_language_name in name.lower():
                        logger.info(f"Language change detected: {requested_language_name} → {code}")
                        return True, code
                
                # Check for direct language codes
                if requested_language_name in self.LANGUAGE_NAMES:
                    return True, requested_language_name
        
        return False, None
    
    def get_whatsapp_country_from_number(self, whatsapp_number: str) -> Optional[str]:
        """Get country name from WhatsApp number"""
        clean_number = re.sub(r'[^\d+]', '', whatsapp_number)
        if not clean_number.startswith('+'):
            clean_number = '+' + clean_number
        
        # Country code to country name mapping
        COUNTRY_NAMES = {
            '+386': 'Slovenia',
            '+385': 'Croatia',
            '+359': 'Bulgaria',
            '+43': 'Austria',
            '+39': 'Italy',
            '+1': 'USA/Canada',
            '+44': 'United Kingdom',
            # Add more as needed
        }
        
        for length in [4, 3, 2, 1]:
            country_code = clean_number[:length+1]
            if country_code in COUNTRY_NAMES:
                return COUNTRY_NAMES[country_code]
        
        return None

# Singleton instance
_language_service = None

def get_language_service() -> LanguageService:
    """Get or create language service instance"""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
        logger.info("Language Service initialized")
    return _language_service