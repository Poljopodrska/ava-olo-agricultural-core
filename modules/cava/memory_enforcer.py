"""
CAVA Memory Enforcer - Ensures LLM responses demonstrate memory explicitly
"""
import re
from typing import Dict, List, Set
import json
from datetime import datetime

class MemoryEnforcer:
    """Ensures LLM responses demonstrate memory explicitly"""
    
    @staticmethod
    def extract_critical_facts(context: Dict) -> Dict:
        """Extract facts that MUST be mentioned in responses"""
        critical_facts = {
            "farmer_name": None,
            "location": None,
            "crops": [],
            "quantities": {},
            "problems": [],
            "unusual_aspects": [],
            "conversation_history_summary": []
        }
        
        # Extract from farmer data
        if context.get('farmer'):
            farmer = context['farmer']
            if farmer.get('manager_name'):
                critical_facts['farmer_name'] = farmer['manager_name']
            if farmer.get('city'):
                critical_facts['location'] = {
                    'city': farmer['city'],
                    'country': farmer.get('country', 'Croatia')
                }
            if farmer.get('total_hectares'):
                critical_facts['quantities']['total_hectares'] = farmer['total_hectares']
            if farmer.get('crops'):
                critical_facts['crops'] = [c for c in farmer['crops'] if c]
        
        # Extract from messages
        all_messages = context.get('messages', [])
        for msg in all_messages:
            if msg['role'] == 'user':
                content = msg['content'].lower()
                
                # Extract quantities
                quantities = re.findall(r'(\d+)\s*(hectare|ha|ton|kg)', content)
                for qty, unit in quantities:
                    critical_facts['quantities'][f"{qty}_{unit}"] = f"{qty} {unit}"
                
                # Extract unusual combinations
                if 'mango' in content and any(loc in content for loc in ['bulgaria', 'croatian', 'serbian']):
                    critical_facts['unusual_aspects'].append("tropical fruit in temperate climate")
                
                # Extract names
                name_patterns = [
                    r"i'm\s+(\w+)",
                    r"i am\s+(\w+)",
                    r"my name is\s+(\w+)",
                    r"call me\s+(\w+)"
                ]
                for pattern in name_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match and not critical_facts['farmer_name']:
                        critical_facts['farmer_name'] = match.group(1).capitalize()
        
        # Build conversation summary
        if len(all_messages) > 2:
            critical_facts['conversation_history_summary'] = [
                f"We've exchanged {len(all_messages)} messages",
                f"You first contacted me on {all_messages[0].get('timestamp', datetime.now()).strftime('%B %d') if all_messages else ''}"
            ]
        
        return critical_facts
    
    @staticmethod
    def create_memory_demonstration_prompt(critical_facts: Dict, user_message: str) -> str:
        """Create a prompt that FORCES memory demonstration"""
        
        prompt = f"""You are AVA, an agricultural assistant with PERFECT MEMORY. You MUST demonstrate that you remember EVERYTHING about this farmer.

CRITICAL MEMORY FACTS YOU MUST USE:
"""
        
        if critical_facts['farmer_name']:
            prompt += f"- Farmer's name: {critical_facts['farmer_name']} (USE THEIR NAME!)\n"
        
        if critical_facts['location']:
            prompt += f"- Location: {critical_facts['location']['city']}, {critical_facts['location']['country']} (MENTION THIS!)\n"
        
        if critical_facts['crops']:
            prompt += f"- Crops: {', '.join(critical_facts['crops'])} (REFERENCE THEIR SPECIFIC CROPS!)\n"
        
        if critical_facts['quantities']:
            for key, value in critical_facts['quantities'].items():
                prompt += f"- Quantity: {value} (MENTION EXACT NUMBERS!)\n"
        
        if critical_facts['unusual_aspects']:
            prompt += f"- Unusual aspects: {', '.join(critical_facts['unusual_aspects'])} (ACKNOWLEDGE HOW UNIQUE THIS IS!)\n"
        
        prompt += f"""
MANDATORY RESPONSE RULES:
1. Start with their name if known
2. Reference their specific location
3. Mention their exact crop and quantities
4. If it's an unusual scenario (like mangoes in Bulgaria), acknowledge it
5. Show you remember previous conversations
6. Be specific, not generic
7. NEVER ask for information you already know

Current farmer message: "{user_message}"

Now respond in a way that PROVES you remember everything about them. Make it impossible for them to think you forgot anything!"""
        
        return prompt
    
    @staticmethod
    def verify_memory_demonstration(response: str, critical_facts: Dict) -> Dict:
        """Verify that response actually demonstrates memory"""
        verification = {
            "mentions_name": False,
            "mentions_location": False,
            "mentions_crop": False,
            "mentions_quantity": False,
            "acknowledges_unusual": False,
            "shows_history": False,
            "score": 0
        }
        
        response_lower = response.lower()
        
        # Check name
        if critical_facts['farmer_name']:
            verification['mentions_name'] = critical_facts['farmer_name'].lower() in response_lower
        
        # Check location
        if critical_facts['location']:
            verification['mentions_location'] = (
                critical_facts['location']['city'].lower() in response_lower or
                critical_facts['location']['country'].lower() in response_lower
            )
        
        # Check crops
        if critical_facts['crops']:
            verification['mentions_crop'] = any(
                crop.lower() in response_lower for crop in critical_facts['crops']
            )
        
        # Check quantities
        if critical_facts['quantities']:
            verification['mentions_quantity'] = any(
                str(qty.split('_')[0]) in response for qty in critical_facts['quantities']
            )
        
        # Check unusual acknowledgment
        unusual_keywords = ['unusual', 'unique', 'interesting', 'special', 'rare', 'tropical', 'surprising']
        verification['acknowledges_unusual'] = any(
            keyword in response_lower for keyword in unusual_keywords
        )
        
        # Check history reference
        history_keywords = ['last time', 'mentioned', 'told me', 'remember', 'as you said', 'your']
        verification['shows_history'] = any(
            keyword in response_lower for keyword in history_keywords
        )
        
        # Calculate score
        verification['score'] = sum([
            verification['mentions_name'] * 20,
            verification['mentions_location'] * 20,
            verification['mentions_crop'] * 20,
            verification['mentions_quantity'] * 15,
            verification['acknowledges_unusual'] * 15,
            verification['shows_history'] * 10
        ])
        
        return verification