#!/usr/bin/env python3
"""
Phone Number Country Detector
Detects country based on WhatsApp phone number prefix
"""

def detect_country_from_phone(phone_number: str) -> str:
    """
    Detect country from phone number prefix
    Returns country name based on international dialing code
    """
    if not phone_number:
        return ""
    
    # Clean the phone number (remove +, spaces, etc)
    phone = phone_number.strip().replace("+", "").replace(" ", "").replace("-", "")
    
    # Country codes mapping (most common European and agricultural countries)
    country_codes = {
        "386": "Slovenia",
        "385": "Croatia", 
        "381": "Serbia",
        "387": "Bosnia and Herzegovina",
        "389": "North Macedonia",
        "383": "Kosovo",
        "382": "Montenegro",
        "359": "Bulgaria",
        "40": "Romania",
        "36": "Hungary",
        "43": "Austria",
        "39": "Italy",
        "33": "France",
        "34": "Spain",
        "351": "Portugal",
        "49": "Germany",
        "41": "Switzerland",
        "32": "Belgium",
        "31": "Netherlands",
        "48": "Poland",
        "420": "Czech Republic",
        "421": "Slovakia",
        "30": "Greece",
        "90": "Turkey",
        "44": "United Kingdom",
        "353": "Ireland",
        "45": "Denmark",
        "46": "Sweden",
        "47": "Norway",
        "358": "Finland",
        "372": "Estonia",
        "371": "Latvia",
        "370": "Lithuania",
        "380": "Ukraine",
        "375": "Belarus",
        "7": "Russia",
        "1": "United States/Canada",
        "91": "India",
        "86": "China",
        "81": "Japan",
        "82": "South Korea",
        "61": "Australia",
        "64": "New Zealand",
        "27": "South Africa",
        "254": "Kenya",
        "255": "Tanzania",
        "256": "Uganda",
        "234": "Nigeria",
        "20": "Egypt",
        "212": "Morocco",
        "216": "Tunisia",
        "213": "Algeria",
        "55": "Brazil",
        "54": "Argentina",
        "52": "Mexico",
        "57": "Colombia",
        "56": "Chile",
        "51": "Peru",
        "593": "Ecuador"
    }
    
    # Check for country code matches (longest prefix first)
    for length in [3, 2, 1]:
        prefix = phone[:length]
        if prefix in country_codes:
            return country_codes[prefix]
    
    # Default to empty if no match found
    return ""

def get_country_phone_format(country: str) -> dict:
    """
    Get phone number format hints for a country
    Returns dict with format info
    """
    formats = {
        "Slovenia": {
            "code": "+386",
            "format": "+386 XX XXX XX XX",
            "example": "+386 40 123 45 67"
        },
        "Bulgaria": {
            "code": "+359",
            "format": "+359 XXX XXX XXX",
            "example": "+359 888 123 456"
        },
        "Croatia": {
            "code": "+385",
            "format": "+385 XX XXX XXXX",
            "example": "+385 91 234 5678"
        },
        "Serbia": {
            "code": "+381",
            "format": "+381 XX XXX XXXX",
            "example": "+381 60 123 4567"
        }
    }
    
    return formats.get(country, {
        "code": "",
        "format": "International format",
        "example": "+XX XXX XXX XXXX"
    })

def validate_phone_for_country(phone_number: str, country: str) -> bool:
    """
    Validate if phone number matches expected country
    """
    detected_country = detect_country_from_phone(phone_number)
    return detected_country.lower() == country.lower() if detected_country else False