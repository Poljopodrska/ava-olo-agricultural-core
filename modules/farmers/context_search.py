#!/usr/bin/env python3
"""
Farmer Context Search - Find existing farmers based on conversation clues
Supports flexible matching by name, location, crops, phone, etc.
"""
import re
import logging
from typing import Dict, List, Optional, Any
from modules.core.database_manager import get_db_manager

logger = logging.getLogger(__name__)

async def search_farmers_flexibly(criteria: Dict[str, Any]) -> List[Dict]:
    """
    Search farmers using multiple strategies
    Returns ranked list of potential matches
    """
    db_manager = get_db_manager()
    all_matches = []
    
    try:
        # Name-based search
        if criteria.get('names'):
            for name in criteria['names']:
                query = """
                SELECT 
                    farmer_id, first_name, last_name, whatsapp_number,
                    city, country, email, created_at,
                    'name_match' as match_type
                FROM farmers 
                WHERE (
                    LOWER(first_name) LIKE LOWER(%s) 
                    OR LOWER(last_name) LIKE LOWER(%s)
                    OR LOWER(first_name || ' ' || last_name) LIKE LOWER(%s)
                )
                AND is_active = true
                """
                name_pattern = f"%{name}%"
                results = await db_manager.execute_query(
                    query, 
                    (name_pattern, name_pattern, name_pattern)
                )
                if results:
                    all_matches.extend([{
                        'farmer_id': r[0],
                        'first_name': r[1],
                        'last_name': r[2],
                        'whatsapp_number': r[3],
                        'city': r[4],
                        'country': r[5],
                        'email': r[6],
                        'created_at': r[7],
                        'match_type': r[8],
                        'match_confidence': 0.8
                    } for r in results])
        
        # Location-based search
        if criteria.get('locations'):
            for location in criteria['locations']:
                query = """
                SELECT DISTINCT
                    f.farmer_id, f.first_name, f.last_name, f.whatsapp_number,
                    f.city, f.country, f.email, f.created_at,
                    'location_match' as match_type
                FROM farmers f
                LEFT JOIN fields fd ON f.farmer_id = fd.farmer_id
                WHERE (
                    LOWER(f.city) LIKE LOWER(%s)
                    OR LOWER(f.country) LIKE LOWER(%s)
                    OR LOWER(fd.name) LIKE LOWER(%s)
                    OR LOWER(fd.location) LIKE LOWER(%s)
                )
                AND f.is_active = true
                """
                location_pattern = f"%{location}%"
                results = await db_manager.execute_query(
                    query,
                    (location_pattern, location_pattern, location_pattern, location_pattern)
                )
                if results:
                    all_matches.extend([{
                        'farmer_id': r[0],
                        'first_name': r[1],
                        'last_name': r[2],
                        'whatsapp_number': r[3],
                        'city': r[4],
                        'country': r[5],
                        'email': r[6],
                        'created_at': r[7],
                        'match_type': r[8],
                        'match_confidence': 0.7
                    } for r in results])
        
        # Crop-based search
        if criteria.get('crops'):
            for crop in criteria['crops']:
                query = """
                SELECT DISTINCT
                    f.farmer_id, f.first_name, f.last_name, f.whatsapp_number,
                    f.city, f.country, f.email, f.created_at,
                    'crop_match' as match_type,
                    STRING_AGG(DISTINCT fd.crop, ', ') as crops
                FROM farmers f
                JOIN fields fd ON f.farmer_id = fd.farmer_id
                WHERE LOWER(fd.crop) LIKE LOWER(%s)
                AND f.is_active = true
                GROUP BY f.farmer_id, f.first_name, f.last_name, 
                         f.whatsapp_number, f.city, f.country, f.email, f.created_at
                """
                crop_pattern = f"%{crop}%"
                results = await db_manager.execute_query(query, (crop_pattern,))
                if results:
                    all_matches.extend([{
                        'farmer_id': r[0],
                        'first_name': r[1],
                        'last_name': r[2],
                        'whatsapp_number': r[3],
                        'city': r[4],
                        'country': r[5],
                        'email': r[6],
                        'created_at': r[7],
                        'match_type': r[8],
                        'crops': r[9],
                        'match_confidence': 0.6
                    } for r in results])
        
        # Phone partial match
        if criteria.get('phone_partial'):
            phone = criteria['phone_partial']
            # Remove non-digits for comparison
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) >= 4:
                query = """
                SELECT 
                    farmer_id, first_name, last_name, whatsapp_number,
                    city, country, email, created_at,
                    'phone_match' as match_type
                FROM farmers 
                WHERE REPLACE(REPLACE(REPLACE(whatsapp_number, '+', ''), '-', ''), ' ', '') 
                      LIKE %s
                AND is_active = true
                """
                phone_pattern = f"%{phone_digits}%"
                results = await db_manager.execute_query(query, (phone_pattern,))
                if results:
                    all_matches.extend([{
                        'farmer_id': r[0],
                        'first_name': r[1],
                        'last_name': r[2],
                        'whatsapp_number': r[3],
                        'city': r[4],
                        'country': r[5],
                        'email': r[6],
                        'created_at': r[7],
                        'match_type': r[8],
                        'match_confidence': 0.9
                    } for r in results])
        
        # Remove duplicates and rank by confidence
        unique_matches = {}
        for match in all_matches:
            farmer_id = match['farmer_id']
            if farmer_id not in unique_matches or match['match_confidence'] > unique_matches[farmer_id]['match_confidence']:
                unique_matches[farmer_id] = match
        
        # Sort by confidence
        ranked_matches = sorted(
            unique_matches.values(), 
            key=lambda x: x['match_confidence'], 
            reverse=True
        )
        
        logger.info(f"Found {len(ranked_matches)} potential farmer matches")
        return ranked_matches[:5]  # Return top 5 matches
        
    except Exception as e:
        logger.error(f"Error searching farmers: {e}")
        return []

async def extract_search_criteria_from_message(message: str, collected_data: Dict) -> Dict:
    """
    Extract identifying information from user message
    Uses simple pattern matching instead of LLM
    """
    criteria = {
        'names': [],
        'locations': [],
        'crops': [],
        'phone_partial': None
    }
    
    message_lower = message.lower()
    
    # Extract names - look for "I'm X" or "My name is X" patterns
    name_patterns = [
        r"i'm\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?",
        r"i am\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?",
        r"my name is\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?",
        r"it's\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?",
        r"this is\s+([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?",
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                criteria['names'].extend([m for m in match if m])
            else:
                criteria['names'].append(match)
    
    # Also check collected data
    if collected_data.get('first_name'):
        criteria['names'].append(collected_data['first_name'])
    if collected_data.get('last_name'):
        criteria['names'].append(collected_data['last_name'])
    
    # Extract locations - common cities in Slovenia/Bulgaria
    location_keywords = [
        'ljubljana', 'maribor', 'celje', 'kranj', 'velenje', 'novo mesto',
        'sofia', 'plovdiv', 'varna', 'burgas', 'ruse', 'stara zagora',
        'zagreb', 'split', 'rijeka', 'osijek',
    ]
    
    for location in location_keywords:
        if location in message_lower:
            criteria['locations'].append(location.title())
    
    # Extract from phrases like "from X" or "in X"
    location_patterns = [
        r"from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"near\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        criteria['locations'].extend(matches)
    
    # Extract crops
    crop_keywords = [
        'corn', 'wheat', 'barley', 'potato', 'tomato', 'pepper', 'cucumber',
        'apple', 'pear', 'plum', 'grape', 'strawberry', 'raspberry',
        'lettuce', 'cabbage', 'carrot', 'onion', 'garlic',
        'sunflower', 'soybean', 'rapeseed',
        'mango', 'mangoes', 'olive', 'olives',
        'organic', 'greenhouse', 'hydroponic'
    ]
    
    for crop in crop_keywords:
        if crop in message_lower:
            criteria['crops'].append(crop)
    
    # Extract phone numbers
    phone_pattern = r'(\+?\d{3,15})'
    phone_matches = re.findall(phone_pattern, message)
    if phone_matches:
        criteria['phone_partial'] = phone_matches[0]
    elif collected_data.get('whatsapp'):
        criteria['phone_partial'] = collected_data['whatsapp']
    
    # Clean up empty lists
    criteria = {k: v for k, v in criteria.items() if v}
    
    logger.info(f"Extracted search criteria: {criteria}")
    return criteria

async def get_farmer_details(farmer_id: int) -> Optional[Dict]:
    """Get detailed information about a specific farmer"""
    db_manager = get_db_manager()
    
    try:
        # Get farmer info
        farmer_query = """
        SELECT 
            farmer_id, first_name, last_name, whatsapp_number,
            city, country, email, created_at
        FROM farmers
        WHERE farmer_id = %s AND is_active = true
        """
        farmer_result = await db_manager.execute_query(farmer_query, (farmer_id,))
        
        if not farmer_result:
            return None
        
        farmer = farmer_result[0]
        farmer_data = {
            'farmer_id': farmer[0],
            'first_name': farmer[1],
            'last_name': farmer[2],
            'whatsapp_number': farmer[3],
            'city': farmer[4],
            'country': farmer[5],
            'email': farmer[6],
            'created_at': farmer[7],
            'fields': []
        }
        
        # Get fields info
        fields_query = """
        SELECT 
            field_id, name, hectares, crop, location,
            created_at
        FROM fields
        WHERE farmer_id = %s
        ORDER BY created_at DESC
        """
        fields_results = await db_manager.execute_query(fields_query, (farmer_id,))
        
        for field in fields_results:
            farmer_data['fields'].append({
                'field_id': field[0],
                'name': field[1],
                'hectares': float(field[2]) if field[2] else 0,
                'crop': field[3],
                'location': field[4],
                'created_at': field[5]
            })
        
        return farmer_data
        
    except Exception as e:
        logger.error(f"Error getting farmer details: {e}")
        return None

def format_farmer_matches(matches: List[Dict]) -> str:
    """Format farmer matches for LLM context"""
    if not matches:
        return "No existing farmers found matching the description."
    
    formatted = []
    for match in matches[:3]:  # Show top 3 matches
        farmer_info = f"- {match['first_name']} {match.get('last_name', '')}"
        
        if match.get('city'):
            farmer_info += f" from {match['city']}"
        
        if match.get('crops'):
            farmer_info += f" (grows {match['crops']})"
        elif match.get('match_type') == 'crop_match':
            farmer_info += f" (farmer with matching crops)"
        
        farmer_info += f" [confidence: {match['match_confidence']:.0%}]"
        formatted.append(farmer_info)
    
    return "\n".join(formatted)