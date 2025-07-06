"""
LLM Router - Pure routing intelligence for AVA OLO
Mango in Bulgaria compliant: No hardcoded patterns, pure LLM intelligence
"""
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries the system can handle"""
    FIELD_MANAGEMENT = "field_management"
    CROP_INFO = "crop_info"
    PEST_CONTROL = "pest_control"
    FERTILIZATION = "fertilization"
    WEATHER = "weather"
    GENERAL_FARMING = "general_farming"
    UNKNOWN = "unknown"

class DataSource(Enum):
    """Available data sources"""
    DATABASE = "database"
    KNOWLEDGE_BASE = "knowledge_base"
    EXTERNAL_SEARCH = "external_search"
    COMBINED = "combined"

class LLMRouter:
    """
    Pure LLM-based router - no hardcoded patterns
    Routes queries to appropriate handlers based on LLM intelligence
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4"
        
    async def route_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route query using pure LLM intelligence
        
        Args:
            query: User query in any language
            context: Additional context (farmer_id, location, etc.)
            
        Returns:
            Routing decision with confidence and reasoning
        """
        try:
            # Build routing prompt - let LLM understand the query naturally
            routing_prompt = self._build_routing_prompt(query, context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": routing_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistent routing
            )
            
            routing_decision = json.loads(response.choices[0].message.content)
            
            # Log routing decision for monitoring
            logger.info(f"Routing decision: {routing_decision}")
            
            return {
                "query": query,
                "query_type": routing_decision.get("query_type", QueryType.UNKNOWN.value),
                "data_sources": routing_decision.get("data_sources", [DataSource.KNOWLEDGE_BASE.value]),
                "confidence": routing_decision.get("confidence", 0.5),
                "reasoning": routing_decision.get("reasoning", ""),
                "entities": routing_decision.get("entities", {}),
                "language": routing_decision.get("language", "hr"),
                "requires_followup": routing_decision.get("requires_followup", False)
            }
            
        except Exception as e:
            logger.error(f"Routing error: {str(e)}")
            # Fallback routing decision
            return {
                "query": query,
                "query_type": QueryType.GENERAL_FARMING.value,
                "data_sources": [DataSource.KNOWLEDGE_BASE.value],
                "confidence": 0.3,
                "reasoning": f"Routing error: {str(e)}",
                "entities": {},
                "language": "hr",
                "requires_followup": True
            }
    
    def _build_routing_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build intelligent routing prompt"""
        
        context_info = ""
        if context:
            if context.get("farmer_id"):
                context_info += f"\nFarmer ID: {context['farmer_id']}"
            if context.get("location"):
                context_info += f"\nLocation: {context['location']}"
            if context.get("recent_topics"):
                context_info += f"\nRecent topics: {', '.join(context['recent_topics'])}"
        
        return f"""You are an agricultural query router for AVA OLO system.
Analyze the query and determine:
1. Query type (field_management, crop_info, pest_control, fertilization, weather, general_farming)
2. Required data sources (database, knowledge_base, external_search, combined)
3. Extracted entities (fields, crops, chemicals, dates, quantities)
4. Language detection
5. Confidence level (0-1)

Context:{context_info}

Query types:
- field_management: Creating, updating, listing fields
- crop_info: Information about crops, varieties, cultivation
- pest_control: Pesticides, diseases, pests, PHI (karenca)
- fertilization: Fertilizers, nutrients, application
- weather: Weather data, forecasts, conditions
- general_farming: General agricultural advice

Data sources:
- database: Farmer's own data (fields, crops, history)
- knowledge_base: Agricultural knowledge, FIS documents, best practices
- external_search: Current information, prices, news
- combined: Multiple sources needed

Return JSON:
{{
    "query_type": "string",
    "data_sources": ["string"],
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "entities": {{
        "field": "optional",
        "crop": "optional", 
        "chemical": "optional",
        "quantity": "optional",
        "date": "optional"
    }},
    "language": "detected language code",
    "requires_followup": boolean
}}"""

    async def refine_routing(self, 
                           initial_routing: Dict[str, Any], 
                           feedback: str) -> Dict[str, Any]:
        """
        Refine routing based on feedback
        Used when initial routing needs adjustment
        """
        refinement_prompt = f"""
Previous routing decision:
{json.dumps(initial_routing, indent=2)}

Feedback: {feedback}

Please refine the routing decision based on this feedback.
Return updated JSON with same structure.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are refining a routing decision based on feedback."},
                    {"role": "user", "content": refinement_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            refined_routing = json.loads(response.choices[0].message.content)
            refined_routing["refined"] = True
            
            return refined_routing
            
        except Exception as e:
            logger.error(f"Refinement error: {str(e)}")
            initial_routing["refinement_error"] = str(e)
            return initial_routing

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics for monitoring"""
        # This would connect to monitoring system
        # For now, return placeholder
        return {
            "total_routes": 0,
            "route_distribution": {},
            "average_confidence": 0.0,
            "error_rate": 0.0
        }