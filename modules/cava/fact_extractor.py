#!/usr/bin/env python3
"""
CAVA Fact Extractor Module
Extracts agricultural facts from conversations using GPT-3.5 Turbo
"""
import json
import logging
from typing import Dict, Any, Optional
from modules.chat.openai_key_manager import get_openai_client

logger = logging.getLogger(__name__)

class FactExtractor:
    """
    Extracts structured agricultural facts from farmer conversations
    Uses GPT-3.5 Turbo for cost-effective fact extraction
    """
    
    def __init__(self):
        self.client = None
        self.extraction_prompt = """
        Extract agricultural facts from this conversation.
        Return JSON with any of these if mentioned:
        - crops: [list of crop names mentioned]
        - chemicals_used: [list of pesticides/herbicides/fertilizers mentioned]
        - problems: [list of issues/diseases/pests mentioned]
        - dates: {planting: date, spraying: date, harvest: date, etc}
        - quantities: {fertilizer: amount, yield: amount, area: amount, etc}
        - field_names: [list of field names mentioned]
        - farming_practices: [organic, conventional, precision, etc]
        - equipment: [tractors, sprayers, harvesters mentioned]
        
        Message: {message}
        Previous context: {context}
        
        Return only valid JSON or empty {} if no facts found.
        Be specific and extract exact values when mentioned.
        """
        logger.info("FactExtractor initialized")
    
    async def extract_facts(self, message: str, context: str = "") -> Dict[str, Any]:
        """
        Use GPT-3.5 Turbo to extract farming facts from a message
        
        Args:
            message: The user's message to extract facts from
            context: Previous conversation context
            
        Returns:
            Dictionary of extracted facts
        """
        try:
            # Get OpenAI client
            if not self.client:
                self.client = get_openai_client()
            
            if not self.client:
                logger.error("OpenAI client not available for fact extraction")
                return {}
            
            # Prepare the prompt
            prompt = self.extraction_prompt.format(
                message=message,
                context=context[:500] if context else "No previous context"
            )
            
            # Call GPT-3.5 Turbo for fact extraction
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106",  # Latest GPT-3.5 model
                messages=[
                    {"role": "system", "content": "You are a precise agricultural data extractor. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=200    # Limit tokens for cost efficiency
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                facts = json.loads(content)
                logger.info(f"Extracted facts: {facts}")
                return facts
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from GPT-3.5 response: {content}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in fact extraction: {str(e)}")
            return {}
    
    def extract_facts_from_registration(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract facts from registration data (no LLM needed)
        
        Args:
            collected_data: Data collected during registration
            
        Returns:
            Dictionary of facts
        """
        facts = {}
        
        # Extract crop information
        if 'crops' in collected_data:
            facts['crops'] = collected_data['crops'] if isinstance(collected_data['crops'], list) else [collected_data['crops']]
        
        # Extract location information
        if 'city' in collected_data:
            facts['location'] = {
                'city': collected_data.get('city'),
                'country': collected_data.get('country')
            }
        
        # Extract farm information
        if 'farm_name' in collected_data:
            facts['farm_info'] = {
                'name': collected_data.get('farm_name'),
                'manager': f"{collected_data.get('first_name', '')} {collected_data.get('last_name', '')}"
            }
        
        # Extract field information if provided
        if 'field_names' in collected_data:
            facts['field_names'] = collected_data['field_names']
        
        return facts
    
    def identify_agricultural_intent(self, message: str) -> Optional[str]:
        """
        Quick intent identification without LLM
        Returns the type of agricultural query
        """
        message_lower = message.lower()
        
        # Define intent patterns
        intents = {
            'harvest_timing': ['when harvest', 'ready to harvest', 'harvest time', 'when to collect'],
            'pest_control': ['pest', 'disease', 'insect', 'spray', 'pesticide', 'fungicide'],
            'fertilizer': ['fertilizer', 'npk', 'nitrogen', 'phosphorus', 'potassium', 'nutrient'],
            'planting': ['plant', 'seed', 'sow', 'planting time', 'when to plant'],
            'weather': ['weather', 'rain', 'drought', 'temperature', 'forecast'],
            'yield': ['yield', 'production', 'how much', 'tons per hectare'],
            'organic': ['organic', 'bio', 'natural', 'chemical-free', 'certification'],
            'irrigation': ['water', 'irrigation', 'drip', 'sprinkler', 'watering'],
            'soil': ['soil', 'ph', 'analysis', 'test', 'quality'],
            'market': ['price', 'sell', 'market', 'buyer', 'export']
        }
        
        # Check for intent matches
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                logger.info(f"Identified intent: {intent}")
                return intent
        
        return None
    
    def extract_quantities(self, message: str) -> Dict[str, Any]:
        """
        Extract quantities and measurements from message
        """
        import re
        
        quantities = {}
        
        # Pattern for hectares/acres
        area_pattern = r'(\d+\.?\d*)\s*(hectare|ha|acre|m2|m²)'
        area_match = re.search(area_pattern, message, re.IGNORECASE)
        if area_match:
            quantities['area'] = {
                'value': float(area_match.group(1)),
                'unit': area_match.group(2).lower()
            }
        
        # Pattern for weight (kg, tons, etc)
        weight_pattern = r'(\d+\.?\d*)\s*(kg|kilogram|ton|tonne|g|gram|pound|lb)'
        weight_match = re.search(weight_pattern, message, re.IGNORECASE)
        if weight_match:
            quantities['weight'] = {
                'value': float(weight_match.group(1)),
                'unit': weight_match.group(2).lower()
            }
        
        # Pattern for liters/gallons
        volume_pattern = r'(\d+\.?\d*)\s*(liter|litre|l|gallon|gal|ml)'
        volume_match = re.search(volume_pattern, message, re.IGNORECASE)
        if volume_match:
            quantities['volume'] = {
                'value': float(volume_match.group(1)),
                'unit': volume_match.group(2).lower()
            }
        
        # Pattern for percentage
        percent_pattern = r'(\d+\.?\d*)\s*%'
        percent_match = re.search(percent_pattern, message)
        if percent_match:
            quantities['percentage'] = float(percent_match.group(1))
        
        return quantities
    
    def extract_dates(self, message: str) -> Dict[str, str]:
        """
        Extract date references from message
        """
        import re
        from datetime import datetime, timedelta
        
        dates = {}
        today = datetime.now()
        
        # Yesterday/today/tomorrow patterns
        if 'yesterday' in message.lower():
            dates['reference_date'] = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'today' in message.lower():
            dates['reference_date'] = today.strftime('%Y-%m-%d')
        elif 'tomorrow' in message.lower():
            dates['reference_date'] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # X days ago pattern
        days_ago_pattern = r'(\d+)\s*days?\s*ago'
        days_match = re.search(days_ago_pattern, message, re.IGNORECASE)
        if days_match:
            days = int(days_match.group(1))
            dates['days_ago'] = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Month patterns
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in message.lower():
                dates['month_mentioned'] = month_name
                break
        
        return dates