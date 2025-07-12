"""
Enhanced LLM Router with Country-Based Localization
Constitutional Amendment #13 Implementation

This enhanced router:
- Detects farmer's country from WhatsApp number
- Routes queries with country context
- Maintains information hierarchy
- Ensures constitutional compliance
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from enum import Enum
from dataclasses import dataclass
import os
from openai import OpenAI
import json
from datetime import datetime

from .country_detector import CountryDetector
from .localization_handler import LocalizationHandler, LocalizationContext, InformationItem
# Note: information_hierarchy will be in document-search module
# from ava_olo_document_search.core.information_hierarchy import InformationHierarchyManager, InformationQuery

# Temporary placeholder classes until proper integration
class InformationQuery:
    def __init__(self, query_text, context, required_relevance_levels=None):
        self.query_text = query_text
        self.context = context
        self.required_relevance_levels = required_relevance_levels or []

class InformationHierarchyManager:
    def query_information(self, query):
        # Placeholder implementation
        class Result:
            def __init__(self):
                self.farmer_items = []
                self.country_items = []
                self.global_items = []
                self.metadata = {"sources_used": []}
            def get_all_items_by_priority(self):
                return self.farmer_items + self.country_items + self.global_items
        return Result()

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of agricultural queries"""
    CROP_INFO = "crop_info"
    PEST_CONTROL = "pest_control"
    FERTILIZATION = "fertilization"
    WEATHER = "weather"
    MARKET_PRICES = "market_prices"
    REGULATIONS = "regulations"
    GENERAL = "general"


@dataclass
class RoutingDecision:
    """Routing decision with localization context"""
    query_type: QueryType
    requires_farmer_data: bool
    requires_country_data: bool
    requires_external_data: bool
    confidence: float
    reasoning: str
    suggested_sources: List[str]


class LocalizedLLMRouter:
    """
    Enhanced LLM Router that incorporates country-based localization
    Constitutional compliance: Pure LLM intelligence with country awareness
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4"
        self.country_detector = CountryDetector()
        self.localization_handler = LocalizationHandler()
        self.hierarchy_manager = InformationHierarchyManager()
    
    async def route_farmer_query(self, 
                               query: str, 
                               whatsapp_number: str,
                               farmer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Route farmer query with full localization context
        Main entry point for the enhanced router
        """
        # Step 1: Build localization context
        context = self.localization_handler.get_localization_context(
            whatsapp_number=whatsapp_number,
            farmer_id=farmer_id
        )
        
        logger.info(f"Query from {context.country_name} farmer in {context.preferred_language}")
        
        # Step 2: Detect query language and adapt if needed
        query_language = self.localization_handler.determine_language(context, query)
        if query_language != context.preferred_language:
            logger.info(f"Detected query in {query_language}, farmer prefers {context.preferred_language}")
        
        # Step 3: Analyze query intent with country context
        routing_decision = await self._analyze_query_with_context(query, context)
        
        # Step 4: Gather information from appropriate sources
        information_query = InformationQuery(
            query_text=query,
            context=context,
            required_relevance_levels=self._determine_required_levels(routing_decision)
        )
        
        information_result = self.hierarchy_manager.query_information(information_query)
        
        # Step 5: Synthesize localized response
        response = self.localization_handler.synthesize_response(
            query=query,
            context=context,
            information_items=information_result.get_all_items_by_priority()
        )
        
        # Step 6: Log for transparency
        self._log_routing_decision(context, routing_decision, information_result)
        
        return {
            "response": response,
            "context": {
                "country": context.country_code,
                "language": context.preferred_language,
                "farmer_id": context.farmer_id
            },
            "routing": {
                "query_type": routing_decision.query_type.value,
                "sources_used": information_result.metadata.get("sources_used", [])
            },
            "metadata": {
                "information_items": len(information_result.get_all_items_by_priority()),
                "response_language": query_language
            }
        }
    
    async def _analyze_query_with_context(self, 
                                        query: str, 
                                        context: LocalizationContext) -> RoutingDecision:
        """
        Analyze query intent with country context
        LLM-first approach with no hardcoded rules
        """
        try:
            # Build context-aware prompt
            system_prompt = f"""You are an agricultural query analyzer for AVA OLO.
            
Current context:
- Farmer from: {context.country_name} ({context.country_code})
- Language: {context.preferred_language}
- Agricultural zones: {', '.join(context.agricultural_zones) if context.agricultural_zones else 'Unknown'}

Analyze the query and return JSON with:
{{
    "query_type": "crop_info|pest_control|fertilization|weather|market_prices|regulations|general",
    "requires_farmer_data": true/false,
    "requires_country_data": true/false,
    "requires_external_data": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "suggested_sources": ["database", "rag", "external"]
}}

Consider the farmer's country context when determining data requirements."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return RoutingDecision(
                query_type=QueryType(analysis.get("query_type", "general")),
                requires_farmer_data=analysis.get("requires_farmer_data", False),
                requires_country_data=analysis.get("requires_country_data", True),
                requires_external_data=analysis.get("requires_external_data", False),
                confidence=analysis.get("confidence", 0.8),
                reasoning=analysis.get("reasoning", ""),
                suggested_sources=analysis.get("suggested_sources", ["database", "rag"])
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            # Fallback routing decision
            return RoutingDecision(
                query_type=QueryType.GENERAL,
                requires_farmer_data=True,
                requires_country_data=True,
                requires_external_data=False,
                confidence=0.5,
                reasoning="Fallback due to analysis error",
                suggested_sources=["database", "rag"]
            )
    
    def _determine_required_levels(self, decision: RoutingDecision) -> List[Any]:
        """Determine which information levels are needed based on routing decision"""
        from localization_handler import InformationRelevance
        
        levels = []
        
        if decision.requires_farmer_data:
            levels.append(InformationRelevance.FARMER_SPECIFIC)
        
        if decision.requires_country_data:
            levels.append(InformationRelevance.COUNTRY_SPECIFIC)
        
        if decision.requires_external_data:
            levels.append(InformationRelevance.GLOBAL)
        
        # Always include at least country and global as fallback
        if not levels:
            levels = [InformationRelevance.COUNTRY_SPECIFIC, InformationRelevance.GLOBAL]
        
        return levels
    
    def _log_routing_decision(self, 
                            context: LocalizationContext,
                            decision: RoutingDecision,
                            result: Any):
        """Log routing decision for transparency"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "farmer_id": context.farmer_id,
            "country": context.country_code,
            "language": context.preferred_language,
            "query_type": decision.query_type.value,
            "routing_confidence": decision.confidence,
            "sources_required": {
                "farmer": decision.requires_farmer_data,
                "country": decision.requires_country_data,
                "external": decision.requires_external_data
            },
            "items_found": {
                "farmer": len(result.farmer_items),
                "country": len(result.country_items),
                "global": len(result.global_items)
            }
        }
        
        logger.info(f"Routing decision: {json.dumps(log_entry)}")
    
    async def handle_seasonal_query(self, 
                                  query: str,
                                  context: LocalizationContext,
                                  crop: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle seasonal queries with country-specific context
        Example of specialized routing for time-sensitive queries
        """
        # Get seasonal context for the country
        seasonal_info = self.localization_handler.get_seasonal_context(context, crop)
        
        # Create information items with seasonal data
        seasonal_item = InformationItem(
            content=seasonal_info["seasonal_info"],
            relevance=InformationRelevance.COUNTRY_SPECIFIC,
            country_code=context.country_code,
            source_type="seasonal_analysis",
            metadata={"date": seasonal_info["date"].isoformat()}
        )
        
        # Regular information gathering
        info_query = InformationQuery(
            query_text=query,
            context=context
        )
        result = self.hierarchy_manager.query_information(info_query)
        
        # Add seasonal context
        result.country_items.insert(0, seasonal_item)
        
        # Synthesize response
        response = self.localization_handler.synthesize_response(
            query=query,
            context=context,
            information_items=result.get_all_items_by_priority()
        )
        
        return {
            "response": response,
            "seasonal_context": seasonal_info,
            "context": {
                "country": context.country_code,
                "season": seasonal_info.get("season", "unknown")
            }
        }
    
    async def handle_regulatory_query(self,
                                    query: str,
                                    context: LocalizationContext) -> Dict[str, Any]:
        """
        Handle regulatory queries with strict country-specific requirements
        Ensures farmers get accurate local regulations
        """
        # Regulatory queries MUST be country-specific
        routing = RoutingDecision(
            query_type=QueryType.REGULATIONS,
            requires_farmer_data=False,  # Regulations apply to all farmers
            requires_country_data=True,   # Must be country-specific
            requires_external_data=False, # Avoid external for legal accuracy
            confidence=0.95,
            reasoning="Regulatory information must be country-specific",
            suggested_sources=["database", "rag"]
        )
        
        # Query with country focus
        info_query = InformationQuery(
            query_text=query,
            context=context,
            required_relevance_levels=[
                InformationRelevance.COUNTRY_SPECIFIC
            ],
            max_items_per_level=10  # More items for comprehensive coverage
        )
        
        result = self.hierarchy_manager.query_information(info_query)
        
        # Synthesize with regulatory emphasis
        response = self.localization_handler.synthesize_response(
            query=query,
            context=context,
            information_items=result.get_all_items_by_priority()
        )
        
        return {
            "response": response,
            "regulatory_notice": f"This information applies to {context.country_name} regulations",
            "context": {
                "country": context.country_code,
                "regulatory_framework": True
            }
        }


# Integration with existing system
class LLMRouterAdapter:
    """
    Adapter to integrate enhanced router with existing AVA OLO modules
    Maintains backward compatibility while adding localization
    """
    
    def __init__(self):
        self.localized_router = LocalizedLLMRouter()
    
    async def process_message(self, 
                            message: str,
                            phone_number: str,
                            farmer_id: Optional[int] = None,
                            **kwargs) -> str:
        """
        Process message with localization
        Compatible with existing AVA OLO interfaces
        """
        result = await self.localized_router.route_farmer_query(
            query=message,
            whatsapp_number=phone_number,
            farmer_id=farmer_id
        )
        
        return result["response"]
    
    def get_context_for_farmer(self, phone_number: str) -> Dict[str, Any]:
        """Get localization context for a farmer"""
        context = self.localized_router.localization_handler.get_localization_context(phone_number)
        
        return {
            "country": context.country_code,
            "country_name": context.country_name,
            "language": context.preferred_language,
            "languages": context.languages,
            "timezone": context.timezone
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_bulgarian_mango():
        """Test Bulgarian mango farmer scenario"""
        router = LocalizedLLMRouter()
        
        # Bulgarian mango farmer query
        result = await router.route_farmer_query(
            query="Кога да бера манго?",  # When to harvest mango?
            whatsapp_number="+359123456789",
            farmer_id=123
        )
        
        print("Bulgarian Mango Test:")
        print(f"Response: {result['response']}")
        print(f"Country: {result['context']['country']}")
        print(f"Language: {result['context']['language']}")
        print(f"Query Type: {result['routing']['query_type']}")
    
    async def test_slovenian_prosaro():
        """Test Slovenian Prosaro scenario"""
        router = LocalizedLLMRouter()
        
        # Slovenian farmer query about Prosaro
        result = await router.route_farmer_query(
            query="Ali lahko uporabim Prosaro na paradižniku?",
            whatsapp_number="+386123456789",
            farmer_id=456
        )
        
        print("\nSlovenian Prosaro Test:")
        print(f"Response: {result['response']}")
        print(f"Sources Used: {result['routing']['sources_used']}")
    
    # Run tests
    asyncio.run(test_bulgarian_mango())
    asyncio.run(test_slovenian_prosaro())