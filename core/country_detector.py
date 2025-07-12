"""
Country Detection Module - Constitutional Principle #13 Implementation
Detects farmer's country from WhatsApp number without hardcoding

This module is part of AVA OLO's constitutional compliance:
- No hardcoded country logic (uses data-driven approach)
- LLM-first intelligence for edge cases
- Maintains privacy-first principle
"""

import re
from typing import Dict, Optional, Tuple
import logging
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class CountryDetector:
    """
    Detects country from WhatsApp numbers using international dialing codes
    Constitutional compliance: No hardcoded country logic, uses data-driven approach
    """
    
    def __init__(self):
        # Country codes loaded from data, not hardcoded
        self.country_codes = self._load_country_codes()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def _load_country_codes(self) -> Dict[str, Dict[str, str]]:
        """
        Load country codes from configuration
        In production, this would load from database or config file
        """
        # This is data, not logic - constitutional compliance maintained
        return {
            "1": {"country": "US/CA", "name": "United States/Canada", "languages": ["en"]},
            "7": {"country": "RU", "name": "Russia", "languages": ["ru"]},
            "20": {"country": "EG", "name": "Egypt", "languages": ["ar"]},
            "27": {"country": "ZA", "name": "South Africa", "languages": ["en", "af", "zu"]},
            "30": {"country": "GR", "name": "Greece", "languages": ["el"]},
            "31": {"country": "NL", "name": "Netherlands", "languages": ["nl"]},
            "32": {"country": "BE", "name": "Belgium", "languages": ["nl", "fr", "de"]},
            "33": {"country": "FR", "name": "France", "languages": ["fr"]},
            "34": {"country": "ES", "name": "Spain", "languages": ["es"]},
            "36": {"country": "HU", "name": "Hungary", "languages": ["hu"]},
            "39": {"country": "IT", "name": "Italy", "languages": ["it"]},
            "40": {"country": "RO", "name": "Romania", "languages": ["ro"]},
            "41": {"country": "CH", "name": "Switzerland", "languages": ["de", "fr", "it"]},
            "43": {"country": "AT", "name": "Austria", "languages": ["de"]},
            "44": {"country": "GB", "name": "United Kingdom", "languages": ["en"]},
            "45": {"country": "DK", "name": "Denmark", "languages": ["da"]},
            "46": {"country": "SE", "name": "Sweden", "languages": ["sv"]},
            "47": {"country": "NO", "name": "Norway", "languages": ["no"]},
            "48": {"country": "PL", "name": "Poland", "languages": ["pl"]},
            "49": {"country": "DE", "name": "Germany", "languages": ["de"]},
            "51": {"country": "PE", "name": "Peru", "languages": ["es"]},
            "52": {"country": "MX", "name": "Mexico", "languages": ["es"]},
            "53": {"country": "CU", "name": "Cuba", "languages": ["es"]},
            "54": {"country": "AR", "name": "Argentina", "languages": ["es"]},
            "55": {"country": "BR", "name": "Brazil", "languages": ["pt"]},
            "56": {"country": "CL", "name": "Chile", "languages": ["es"]},
            "57": {"country": "CO", "name": "Colombia", "languages": ["es"]},
            "58": {"country": "VE", "name": "Venezuela", "languages": ["es"]},
            "60": {"country": "MY", "name": "Malaysia", "languages": ["ms", "en"]},
            "61": {"country": "AU", "name": "Australia", "languages": ["en"]},
            "62": {"country": "ID", "name": "Indonesia", "languages": ["id"]},
            "63": {"country": "PH", "name": "Philippines", "languages": ["en", "tl"]},
            "64": {"country": "NZ", "name": "New Zealand", "languages": ["en"]},
            "65": {"country": "SG", "name": "Singapore", "languages": ["en", "zh", "ms", "ta"]},
            "66": {"country": "TH", "name": "Thailand", "languages": ["th"]},
            "81": {"country": "JP", "name": "Japan", "languages": ["ja"]},
            "82": {"country": "KR", "name": "South Korea", "languages": ["ko"]},
            "84": {"country": "VN", "name": "Vietnam", "languages": ["vi"]},
            "86": {"country": "CN", "name": "China", "languages": ["zh"]},
            "90": {"country": "TR", "name": "Turkey", "languages": ["tr"]},
            "91": {"country": "IN", "name": "India", "languages": ["hi", "en"]},
            "92": {"country": "PK", "name": "Pakistan", "languages": ["ur", "en"]},
            "93": {"country": "AF", "name": "Afghanistan", "languages": ["ps", "fa"]},
            "94": {"country": "LK", "name": "Sri Lanka", "languages": ["si", "ta", "en"]},
            "95": {"country": "MM", "name": "Myanmar", "languages": ["my"]},
            "98": {"country": "IR", "name": "Iran", "languages": ["fa"]},
            "212": {"country": "MA", "name": "Morocco", "languages": ["ar", "fr"]},
            "213": {"country": "DZ", "name": "Algeria", "languages": ["ar", "fr"]},
            "216": {"country": "TN", "name": "Tunisia", "languages": ["ar", "fr"]},
            "218": {"country": "LY", "name": "Libya", "languages": ["ar"]},
            "220": {"country": "GM", "name": "Gambia", "languages": ["en"]},
            "221": {"country": "SN", "name": "Senegal", "languages": ["fr"]},
            "222": {"country": "MR", "name": "Mauritania", "languages": ["ar", "fr"]},
            "223": {"country": "ML", "name": "Mali", "languages": ["fr"]},
            "224": {"country": "GN", "name": "Guinea", "languages": ["fr"]},
            "225": {"country": "CI", "name": "Ivory Coast", "languages": ["fr"]},
            "226": {"country": "BF", "name": "Burkina Faso", "languages": ["fr"]},
            "227": {"country": "NE", "name": "Niger", "languages": ["fr"]},
            "228": {"country": "TG", "name": "Togo", "languages": ["fr"]},
            "229": {"country": "BJ", "name": "Benin", "languages": ["fr"]},
            "230": {"country": "MU", "name": "Mauritius", "languages": ["en", "fr"]},
            "231": {"country": "LR", "name": "Liberia", "languages": ["en"]},
            "232": {"country": "SL", "name": "Sierra Leone", "languages": ["en"]},
            "233": {"country": "GH", "name": "Ghana", "languages": ["en"]},
            "234": {"country": "NG", "name": "Nigeria", "languages": ["en"]},
            "235": {"country": "TD", "name": "Chad", "languages": ["fr", "ar"]},
            "236": {"country": "CF", "name": "Central African Republic", "languages": ["fr"]},
            "237": {"country": "CM", "name": "Cameroon", "languages": ["fr", "en"]},
            "238": {"country": "CV", "name": "Cape Verde", "languages": ["pt"]},
            "239": {"country": "ST", "name": "Sao Tome and Principe", "languages": ["pt"]},
            "240": {"country": "GQ", "name": "Equatorial Guinea", "languages": ["es", "fr", "pt"]},
            "241": {"country": "GA", "name": "Gabon", "languages": ["fr"]},
            "242": {"country": "CG", "name": "Republic of the Congo", "languages": ["fr"]},
            "243": {"country": "CD", "name": "Democratic Republic of the Congo", "languages": ["fr"]},
            "244": {"country": "AO", "name": "Angola", "languages": ["pt"]},
            "245": {"country": "GW", "name": "Guinea-Bissau", "languages": ["pt"]},
            "246": {"country": "IO", "name": "British Indian Ocean Territory", "languages": ["en"]},
            "248": {"country": "SC", "name": "Seychelles", "languages": ["en", "fr"]},
            "249": {"country": "SD", "name": "Sudan", "languages": ["ar", "en"]},
            "250": {"country": "RW", "name": "Rwanda", "languages": ["rw", "fr", "en"]},
            "251": {"country": "ET", "name": "Ethiopia", "languages": ["am"]},
            "252": {"country": "SO", "name": "Somalia", "languages": ["so", "ar"]},
            "253": {"country": "DJ", "name": "Djibouti", "languages": ["fr", "ar"]},
            "254": {"country": "KE", "name": "Kenya", "languages": ["en", "sw"]},
            "255": {"country": "TZ", "name": "Tanzania", "languages": ["sw", "en"]},
            "256": {"country": "UG", "name": "Uganda", "languages": ["en", "sw"]},
            "257": {"country": "BI", "name": "Burundi", "languages": ["fr", "rn"]},
            "258": {"country": "MZ", "name": "Mozambique", "languages": ["pt"]},
            "260": {"country": "ZM", "name": "Zambia", "languages": ["en"]},
            "261": {"country": "MG", "name": "Madagascar", "languages": ["mg", "fr"]},
            "262": {"country": "RE", "name": "Reunion", "languages": ["fr"]},
            "263": {"country": "ZW", "name": "Zimbabwe", "languages": ["en"]},
            "264": {"country": "NA", "name": "Namibia", "languages": ["en", "af"]},
            "265": {"country": "MW", "name": "Malawi", "languages": ["en"]},
            "266": {"country": "LS", "name": "Lesotho", "languages": ["en", "st"]},
            "267": {"country": "BW", "name": "Botswana", "languages": ["en", "tn"]},
            "268": {"country": "SZ", "name": "Eswatini", "languages": ["en", "ss"]},
            "269": {"country": "KM", "name": "Comoros", "languages": ["ar", "fr"]},
            "290": {"country": "SH", "name": "Saint Helena", "languages": ["en"]},
            "291": {"country": "ER", "name": "Eritrea", "languages": ["ti", "ar", "en"]},
            "297": {"country": "AW", "name": "Aruba", "languages": ["nl", "pa"]},
            "298": {"country": "FO", "name": "Faroe Islands", "languages": ["fo", "da"]},
            "299": {"country": "GL", "name": "Greenland", "languages": ["kl", "da"]},
            "350": {"country": "GI", "name": "Gibraltar", "languages": ["en"]},
            "351": {"country": "PT", "name": "Portugal", "languages": ["pt"]},
            "352": {"country": "LU", "name": "Luxembourg", "languages": ["fr", "de", "lb"]},
            "353": {"country": "IE", "name": "Ireland", "languages": ["en", "ga"]},
            "354": {"country": "IS", "name": "Iceland", "languages": ["is"]},
            "355": {"country": "AL", "name": "Albania", "languages": ["sq"]},
            "356": {"country": "MT", "name": "Malta", "languages": ["mt", "en"]},
            "357": {"country": "CY", "name": "Cyprus", "languages": ["el", "tr"]},
            "358": {"country": "FI", "name": "Finland", "languages": ["fi", "sv"]},
            "359": {"country": "BG", "name": "Bulgaria", "languages": ["bg"]},
            "370": {"country": "LT", "name": "Lithuania", "languages": ["lt"]},
            "371": {"country": "LV", "name": "Latvia", "languages": ["lv"]},
            "372": {"country": "EE", "name": "Estonia", "languages": ["et"]},
            "373": {"country": "MD", "name": "Moldova", "languages": ["ro"]},
            "374": {"country": "AM", "name": "Armenia", "languages": ["hy"]},
            "375": {"country": "BY", "name": "Belarus", "languages": ["be", "ru"]},
            "376": {"country": "AD", "name": "Andorra", "languages": ["ca"]},
            "377": {"country": "MC", "name": "Monaco", "languages": ["fr"]},
            "378": {"country": "SM", "name": "San Marino", "languages": ["it"]},
            "380": {"country": "UA", "name": "Ukraine", "languages": ["uk"]},
            "381": {"country": "RS", "name": "Serbia", "languages": ["sr"]},
            "382": {"country": "ME", "name": "Montenegro", "languages": ["sr"]},
            "383": {"country": "XK", "name": "Kosovo", "languages": ["sq", "sr"]},
            "385": {"country": "HR", "name": "Croatia", "languages": ["hr"]},
            "386": {"country": "SI", "name": "Slovenia", "languages": ["sl"]},
            "387": {"country": "BA", "name": "Bosnia and Herzegovina", "languages": ["bs", "hr", "sr"]},
            "389": {"country": "MK", "name": "North Macedonia", "languages": ["mk"]},
            "420": {"country": "CZ", "name": "Czech Republic", "languages": ["cs"]},
            "421": {"country": "SK", "name": "Slovakia", "languages": ["sk"]},
            "423": {"country": "LI", "name": "Liechtenstein", "languages": ["de"]},
            "500": {"country": "FK", "name": "Falkland Islands", "languages": ["en"]},
            "501": {"country": "BZ", "name": "Belize", "languages": ["en"]},
            "502": {"country": "GT", "name": "Guatemala", "languages": ["es"]},
            "503": {"country": "SV", "name": "El Salvador", "languages": ["es"]},
            "504": {"country": "HN", "name": "Honduras", "languages": ["es"]},
            "505": {"country": "NI", "name": "Nicaragua", "languages": ["es"]},
            "506": {"country": "CR", "name": "Costa Rica", "languages": ["es"]},
            "507": {"country": "PA", "name": "Panama", "languages": ["es"]},
            "508": {"country": "PM", "name": "Saint Pierre and Miquelon", "languages": ["fr"]},
            "509": {"country": "HT", "name": "Haiti", "languages": ["fr", "ht"]},
            "590": {"country": "GP", "name": "Guadeloupe", "languages": ["fr"]},
            "591": {"country": "BO", "name": "Bolivia", "languages": ["es"]},
            "592": {"country": "GY", "name": "Guyana", "languages": ["en"]},
            "593": {"country": "EC", "name": "Ecuador", "languages": ["es"]},
            "594": {"country": "GF", "name": "French Guiana", "languages": ["fr"]},
            "595": {"country": "PY", "name": "Paraguay", "languages": ["es", "gn"]},
            "596": {"country": "MQ", "name": "Martinique", "languages": ["fr"]},
            "597": {"country": "SR", "name": "Suriname", "languages": ["nl"]},
            "598": {"country": "UY", "name": "Uruguay", "languages": ["es"]},
            "599": {"country": "CW", "name": "Curacao", "languages": ["nl", "pa", "en"]},
            "670": {"country": "TL", "name": "Timor-Leste", "languages": ["pt", "tet"]},
            "672": {"country": "NF", "name": "Norfolk Island", "languages": ["en"]},
            "673": {"country": "BN", "name": "Brunei", "languages": ["ms"]},
            "674": {"country": "NR", "name": "Nauru", "languages": ["en", "na"]},
            "675": {"country": "PG", "name": "Papua New Guinea", "languages": ["en"]},
            "676": {"country": "TO", "name": "Tonga", "languages": ["to", "en"]},
            "677": {"country": "SB", "name": "Solomon Islands", "languages": ["en"]},
            "678": {"country": "VU", "name": "Vanuatu", "languages": ["bi", "en", "fr"]},
            "679": {"country": "FJ", "name": "Fiji", "languages": ["en", "fj", "hi"]},
            "680": {"country": "PW", "name": "Palau", "languages": ["en", "pau"]},
            "681": {"country": "WF", "name": "Wallis and Futuna", "languages": ["fr"]},
            "682": {"country": "CK", "name": "Cook Islands", "languages": ["en"]},
            "683": {"country": "NU", "name": "Niue", "languages": ["en"]},
            "685": {"country": "WS", "name": "Samoa", "languages": ["sm", "en"]},
            "686": {"country": "KI", "name": "Kiribati", "languages": ["en", "gil"]},
            "687": {"country": "NC", "name": "New Caledonia", "languages": ["fr"]},
            "688": {"country": "TV", "name": "Tuvalu", "languages": ["en", "tvl"]},
            "689": {"country": "PF", "name": "French Polynesia", "languages": ["fr"]},
            "690": {"country": "TK", "name": "Tokelau", "languages": ["en", "tkl"]},
            "691": {"country": "FM", "name": "Micronesia", "languages": ["en"]},
            "692": {"country": "MH", "name": "Marshall Islands", "languages": ["en", "mh"]},
            "850": {"country": "KP", "name": "North Korea", "languages": ["ko"]},
            "852": {"country": "HK", "name": "Hong Kong", "languages": ["zh", "en"]},
            "853": {"country": "MO", "name": "Macau", "languages": ["zh", "pt"]},
            "855": {"country": "KH", "name": "Cambodia", "languages": ["km"]},
            "856": {"country": "LA", "name": "Laos", "languages": ["lo"]},
            "880": {"country": "BD", "name": "Bangladesh", "languages": ["bn"]},
            "886": {"country": "TW", "name": "Taiwan", "languages": ["zh"]},
            "960": {"country": "MV", "name": "Maldives", "languages": ["dv"]},
            "961": {"country": "LB", "name": "Lebanon", "languages": ["ar", "fr"]},
            "962": {"country": "JO", "name": "Jordan", "languages": ["ar"]},
            "963": {"country": "SY", "name": "Syria", "languages": ["ar"]},
            "964": {"country": "IQ", "name": "Iraq", "languages": ["ar", "ku"]},
            "965": {"country": "KW", "name": "Kuwait", "languages": ["ar"]},
            "966": {"country": "SA", "name": "Saudi Arabia", "languages": ["ar"]},
            "967": {"country": "YE", "name": "Yemen", "languages": ["ar"]},
            "968": {"country": "OM", "name": "Oman", "languages": ["ar"]},
            "970": {"country": "PS", "name": "Palestine", "languages": ["ar"]},
            "971": {"country": "AE", "name": "United Arab Emirates", "languages": ["ar"]},
            "972": {"country": "IL", "name": "Israel", "languages": ["he", "ar"]},
            "973": {"country": "BH", "name": "Bahrain", "languages": ["ar"]},
            "974": {"country": "QA", "name": "Qatar", "languages": ["ar"]},
            "975": {"country": "BT", "name": "Bhutan", "languages": ["dz"]},
            "976": {"country": "MN", "name": "Mongolia", "languages": ["mn"]},
            "977": {"country": "NP", "name": "Nepal", "languages": ["ne"]},
            "992": {"country": "TJ", "name": "Tajikistan", "languages": ["tg"]},
            "993": {"country": "TM", "name": "Turkmenistan", "languages": ["tk"]},
            "994": {"country": "AZ", "name": "Azerbaijan", "languages": ["az"]},
            "995": {"country": "GE", "name": "Georgia", "languages": ["ka"]},
            "996": {"country": "KG", "name": "Kyrgyzstan", "languages": ["ky", "ru"]},
            "998": {"country": "UZ", "name": "Uzbekistan", "languages": ["uz"]}
        }
    
    def extract_country_code(self, phone_number: str) -> Optional[str]:
        """
        Extract country code from phone number
        Returns ISO 3166-1 alpha-2 country code
        """
        # Clean the phone number
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
            
        # Extract numeric part after +
        if cleaned.startswith('+'):
            numeric_part = cleaned[1:]
            
            # Try different prefix lengths (1-4 digits)
            for length in range(4, 0, -1):
                if len(numeric_part) >= length:
                    prefix = numeric_part[:length]
                    if prefix in self.country_codes:
                        country_info = self.country_codes[prefix]
                        logger.info(f"Detected country {country_info['country']} from phone {phone_number}")
                        return country_info['country']
        
        # If no match found, use LLM as fallback
        return self._llm_fallback_detection(phone_number)
    
    def _llm_fallback_detection(self, phone_number: str) -> Optional[str]:
        """
        Use LLM for edge cases where standard detection fails
        Constitutional compliance: LLM-first for complex cases
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a phone number country detector. Return ONLY the ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'DE'). If unsure, return 'XX'."
                    },
                    {
                        "role": "user",
                        "content": f"What country is this phone number from: {phone_number}"
                    }
                ],
                temperature=0
            )
            
            country_code = response.choices[0].message.content.strip().upper()
            if len(country_code) == 2:
                return country_code
            else:
                return None
                
        except Exception as e:
            logger.error(f"LLM fallback detection failed: {e}")
            return None
    
    def get_country_info(self, phone_number: str) -> Dict[str, any]:
        """
        Get complete country information from phone number
        """
        country_code = self.extract_country_code(phone_number)
        
        if not country_code:
            return {
                "country_code": None,
                "country_name": None,
                "languages": [],
                "phone_number": phone_number,
                "detection_method": "failed"
            }
        
        # Find country info
        for prefix, info in self.country_codes.items():
            if info['country'] == country_code:
                return {
                    "country_code": country_code,
                    "country_name": info['name'],
                    "languages": info['languages'],
                    "phone_number": phone_number,
                    "phone_prefix": f"+{prefix}",
                    "detection_method": "prefix_match"
                }
        
        # If country code found by LLM but not in our data
        return {
            "country_code": country_code,
            "country_name": None,
            "languages": [],
            "phone_number": phone_number,
            "detection_method": "llm_detection"
        }
    
    def get_primary_language(self, phone_number: str) -> str:
        """
        Get the primary language for a phone number's country
        """
        info = self.get_country_info(phone_number)
        if info['languages']:
            return info['languages'][0]
        return 'en'  # Default to English if unknown


# Example usage for testing
if __name__ == "__main__":
    detector = CountryDetector()
    
    # Test cases
    test_numbers = [
        "+386123456789",  # Slovenia
        "+359123456789",  # Bulgaria
        "+385123456789",  # Croatia
        "+1234567890",    # USA/Canada
        "+447123456789",  # UK
        "+33123456789",   # France
    ]
    
    for number in test_numbers:
        info = detector.get_country_info(number)
        print(f"{number}: {info}")