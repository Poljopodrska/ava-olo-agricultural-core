"""
Localization Handler - Constitutional Principle #13 Implementation
Handles country-specific localization with LLM intelligence

This module maintains constitutional compliance:
- LLM-first approach for all localization decisions
- No hardcoded country-specific logic
- Privacy-first information hierarchy
"""

from typing import Dict, List, Optional, Tuple, Any
import logging
from enum import Enum
from dataclasses import dataclass
from openai import OpenAI
import os
from datetime import datetime
import json

from .country_detector import CountryDetector

logger = logging.getLogger(__name__)


class InformationRelevance(Enum):
    """Information relevance hierarchy as per Constitutional Amendment #13"""
    FARMER_SPECIFIC = "FARMER"      # Highest priority - individual farmer data
    COUNTRY_SPECIFIC = "COUNTRY"    # Medium priority - country-level knowledge
    GLOBAL = "GLOBAL"              # Lowest priority - universal knowledge


@dataclass
class LocalizationContext:
    """Context for localization decisions"""
    whatsapp_number: str
    country_code: str
    country_name: str
    languages: List[str]
    farmer_id: Optional[int] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    agricultural_zones: Optional[List[str]] = None


@dataclass
class InformationItem:
    """Represents a piece of information with its relevance level"""
    content: str
    relevance: InformationRelevance
    farmer_id: Optional[int] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    source_type: str = "unknown"
    metadata: Optional[Dict] = None


class LocalizationHandler:
    """
    Handles intelligent localization based on farmer's country
    Constitutional compliance: Pure LLM intelligence, no hardcoded logic
    """
    
    def __init__(self):
        self.country_detector = CountryDetector()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4"
        
    def get_localization_context(self, whatsapp_number: str, farmer_id: Optional[int] = None) -> LocalizationContext:
        """
        Build complete localization context from WhatsApp number
        """
        # Get country information
        country_info = self.country_detector.get_country_info(whatsapp_number)
        
        # Use LLM to determine additional context
        additional_context = self._llm_determine_context(country_info)
        
        return LocalizationContext(
            whatsapp_number=whatsapp_number,
            country_code=country_info['country_code'],
            country_name=country_info['country_name'],
            languages=country_info['languages'],
            farmer_id=farmer_id,
            preferred_language=country_info['languages'][0] if country_info['languages'] else 'en',
            timezone=additional_context.get('timezone'),
            agricultural_zones=additional_context.get('agricultural_zones', [])
        )
    
    def _llm_determine_context(self, country_info: Dict) -> Dict:
        """
        Use LLM to determine additional context like timezone and agricultural zones
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an agricultural localization expert. 
                        Given a country, provide timezone and major agricultural zones.
                        Return JSON format: {"timezone": "UTC+X", "agricultural_zones": ["zone1", "zone2"]}"""
                    },
                    {
                        "role": "user",
                        "content": f"Country: {country_info['country_name']} ({country_info['country_code']})"
                    }
                ],
                temperature=0
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Failed to determine additional context: {e}")
            return {}
    
    def synthesize_response(self, 
                          query: str,
                          context: LocalizationContext,
                          information_items: List[InformationItem]) -> str:
        """
        Synthesize a localized response using the information hierarchy
        Constitutional compliance: LLM handles all synthesis, no hardcoded rules
        """
        # Sort information by relevance priority
        farmer_info = [item for item in information_items if item.relevance == InformationRelevance.FARMER_SPECIFIC]
        country_info = [item for item in information_items if item.relevance == InformationRelevance.COUNTRY_SPECIFIC]
        global_info = [item for item in information_items if item.relevance == InformationRelevance.GLOBAL]
        
        # Build context for LLM
        system_prompt = self._build_synthesis_prompt(context)
        user_prompt = self._build_information_prompt(query, farmer_info, country_info, global_info)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to synthesize response: {e}")
            return self._fallback_response(context)
    
    def _build_synthesis_prompt(self, context: LocalizationContext) -> str:
        """Build system prompt for response synthesis"""
        return f"""You are AVA OLO, an agricultural assistant helping farmers.
        
Current farmer context:
- Country: {context.country_name} ({context.country_code})
- Language: {context.preferred_language}
- Agricultural zones: {', '.join(context.agricultural_zones) if context.agricultural_zones else 'Unknown'}

Instructions:
1. Respond in {context.preferred_language} language
2. Use measurements and terms familiar in {context.country_name}
3. Consider local agricultural practices and regulations
4. Prioritize farmer-specific information, then country-specific, then global
5. Be professional but friendly, focused on practical agricultural advice
6. If timezone-sensitive information, consider {context.timezone if context.timezone else 'local time'}
"""
    
    def _build_information_prompt(self, 
                                query: str,
                                farmer_info: List[InformationItem],
                                country_info: List[InformationItem],
                                global_info: List[InformationItem]) -> str:
        """Build user prompt with hierarchical information"""
        prompt_parts = [f"Farmer's question: {query}\n\n"]
        
        if farmer_info:
            prompt_parts.append("FARMER-SPECIFIC INFORMATION (highest priority):")
            for item in farmer_info:
                prompt_parts.append(f"- {item.content}")
            prompt_parts.append("")
        
        if country_info:
            prompt_parts.append(f"COUNTRY-SPECIFIC INFORMATION (for this farmer's country):")
            for item in country_info:
                prompt_parts.append(f"- {item.content}")
            prompt_parts.append("")
        
        if global_info:
            prompt_parts.append("GENERAL AGRICULTURAL INFORMATION (use if needed):")
            for item in global_info:
                prompt_parts.append(f"- {item.content}")
            prompt_parts.append("")
        
        prompt_parts.append("Synthesize a helpful response using the above information, prioritizing farmer-specific and country-specific details.")
        
        return "\n".join(prompt_parts)
    
    def _fallback_response(self, context: LocalizationContext) -> str:
        """Fallback response maintaining constitutional compliance"""
        # Even fallback uses LLM, not hardcoded responses
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a polite message in {context.preferred_language} saying the system is temporarily unable to process the request."
                    },
                    {
                        "role": "user",
                        "content": "Create message"
                    }
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except:
            # Ultimate fallback - still not hardcoded per country
            return "System temporarily unavailable. Please try again."
    
    def determine_language(self, context: LocalizationContext, message: str) -> str:
        """
        Intelligently determine the best language for response
        Can detect language from farmer's message and adapt
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Detect the language of the message and determine best response language.
                        Farmer is from {context.country_name} where languages are: {', '.join(context.languages)}.
                        Return only the ISO 639-1 language code (e.g., 'en', 'es', 'bg')."""
                    },
                    {
                        "role": "user",
                        "content": f"Message: {message}"
                    }
                ],
                temperature=0
            )
            
            detected_language = response.choices[0].message.content.strip().lower()
            
            # Validate it's a reasonable language code
            if len(detected_language) == 2:
                return detected_language
            else:
                return context.preferred_language
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return context.preferred_language
    
    def localize_measurement(self, value: float, unit: str, context: LocalizationContext) -> str:
        """
        Localize measurements based on country preferences
        Constitutional compliance: LLM determines appropriate units
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Convert measurement to appropriate unit for {context.country_name}. Return only the converted value with unit."
                    },
                    {
                        "role": "user",
                        "content": f"{value} {unit}"
                    }
                ],
                temperature=0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Measurement localization failed: {e}")
            return f"{value} {unit}"
    
    def get_seasonal_context(self, context: LocalizationContext, crop: Optional[str] = None) -> Dict[str, Any]:
        """
        Get seasonal agricultural context for the farmer's location
        """
        current_date = datetime.now()
        
        try:
            prompt = f"""For {context.country_name} on {current_date.strftime('%B %d')}:
            1. What season is it?
            2. What are typical agricultural activities?
            """
            
            if crop:
                prompt += f"\n3. Specific considerations for {crop}?"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an agricultural expert. Provide brief, practical seasonal information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )
            
            return {
                "date": current_date,
                "seasonal_info": response.choices[0].message.content,
                "country": context.country_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get seasonal context: {e}")
            return {
                "date": current_date,
                "seasonal_info": None,
                "country": context.country_name
            }


# Example usage
if __name__ == "__main__":
    handler = LocalizationHandler()
    
    # Test Bulgarian mango farmer
    bulgarian_number = "+359123456789"
    context = handler.get_localization_context(bulgarian_number, farmer_id=123)
    
    print(f"Context for {bulgarian_number}:")
    print(f"  Country: {context.country_name} ({context.country_code})")
    print(f"  Languages: {context.languages}")
    print(f"  Preferred: {context.preferred_language}")
    
    # Test information synthesis
    test_items = [
        InformationItem(
            content="Your mango field #3 showed signs of fruit fly last week",
            relevance=InformationRelevance.FARMER_SPECIFIC,
            farmer_id=123
        ),
        InformationItem(
            content="In Bulgaria, mango cultivation requires greenhouse protection due to climate",
            relevance=InformationRelevance.COUNTRY_SPECIFIC,
            country_code="BG"
        ),
        InformationItem(
            content="Mango trees typically need 24-27°C for optimal growth",
            relevance=InformationRelevance.GLOBAL
        )
    ]
    
    response = handler.synthesize_response(
        query="When should I harvest my mangoes?",
        context=context,
        information_items=test_items
    )
    
    print(f"\nSynthesized response: {response}")