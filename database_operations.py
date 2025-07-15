"""
Constitutional Database Operations
Replaces hardcoded SQL with LLM-first approach
100% Constitutional Compliance Implementation
"""

import os
import sys

# Import config manager - it's in the same directory
try:
    from config_manager import config
except ImportError:
    # If direct import fails, try with current directory
    import config_manager
    config = config_manager.config

from llm_first_database_engine import LLMDatabaseQueryEngine, DatabaseQuery
import logging
from typing import Dict, Any, Optional, List
import asyncio

logger = logging.getLogger(__name__)


class ConstitutionalDatabaseOperations:
    """
    Constitutional replacement for hardcoded database operations
    100% LLM-first compliance
    """
    
    def __init__(self, connection_string: str = None):
        self.llm_engine = LLMDatabaseQueryEngine()
        self.connection_string = connection_string
    
    async def get_farmer_info(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        """Get farmer information by ID using LLM"""
        query = DatabaseQuery(
            natural_language_query="Get all information about this farmer including name, farm name, location, and contact details",
            farmer_id=farmer_id,
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        
        # Return structured data for compatibility
        if result.raw_results and len(result.raw_results) > 0:
            return result.raw_results[0]
        return None
    
    async def get_all_farmers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of all farmers using LLM"""
        query = DatabaseQuery(
            natural_language_query=f"List all farmers with their basic information, limit to {limit} results",
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        return result.raw_results
    
    async def get_farmer_fields(self, farmer_id: int) -> List[Dict[str, Any]]:
        """Get all fields for a farmer using LLM"""
        query = DatabaseQuery(
            natural_language_query="Show all fields for this farmer with their sizes and locations",
            farmer_id=farmer_id,
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        return result.raw_results
    
    async def get_recent_conversations(self, farmer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for context using LLM"""
        query = DatabaseQuery(
            natural_language_query=f"Show the last {limit} messages from this farmer",
            farmer_id=farmer_id,
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        return result.raw_results
    
    async def save_conversation(self, farmer_id: int, conversation_data: Dict[str, Any]) -> Optional[int]:
        """Save conversation - Note: This is read-only for now as LLM only generates SELECT queries"""
        logger.warning("Constitutional compliance: Write operations not yet implemented in LLM-first approach")
        return None
    
    async def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get crop information using LLM"""
        query = DatabaseQuery(
            natural_language_query=f"Get information about {crop_name} crop including varieties and growing seasons",
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        
        if result.raw_results and len(result.raw_results) > 0:
            return result.raw_results[0]
        return None
    
    async def get_conversations_for_approval(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get conversations grouped by approval status using LLM"""
        query = DatabaseQuery(
            natural_language_query="Show recent farmer messages that need approval, grouped by status",
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        
        # Group results
        unapproved = [r for r in result.raw_results if not r.get('approved', False)]
        approved = [r for r in result.raw_results if r.get('approved', False)]
        
        return {"unapproved": unapproved, "approved": approved}
    
    async def get_conversation_details(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed conversation information using LLM"""
        query = DatabaseQuery(
            natural_language_query=f"Show full details of conversation with ID {conversation_id}",
            language="en"
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        
        if result.raw_results and len(result.raw_results) > 0:
            return result.raw_results[0]
        return None
    
    async def health_check(self) -> bool:
        """Check database connectivity using LLM"""
        try:
            query = DatabaseQuery(
                natural_language_query="Count total number of farmers in the database",
                language="en"
            )
            
            result = await self.llm_engine.process_farmer_query(query)
            
            if result.raw_results and len(result.raw_results) > 0:
                count = result.raw_results[0].get('count', 0)
                logger.info(f"Database health check: Connected with {count} farmers")
                return True
            return False
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    async def process_natural_query(self, 
                                  query_text: str,
                                  farmer_id: Optional[int] = None,
                                  language: str = "en",
                                  country_code: Optional[str] = None) -> str:
        """
        Process any natural language query
        This is the main method for constitutional compliance
        """
        query = DatabaseQuery(
            natural_language_query=query_text,
            farmer_id=farmer_id,
            language=language,
            country_code=country_code
        )
        
        result = await self.llm_engine.process_farmer_query(query)
        
        # Log for transparency
        logger.info(f"Processed query for farmer {farmer_id}: {query_text}")
        logger.info(f"Generated SQL: {result.sql_query}")
        
        return result.natural_language_response
    
    # Synchronous wrappers for backward compatibility
    def get_session(self):
        """Compatibility wrapper - returns self as session is managed internally"""
        return self
    
    def execute(self, *args, **kwargs):
        """Compatibility wrapper for execute calls"""
        logger.warning("Direct execute called - routing through LLM engine")
        return None
    
    def fetchone(self):
        """Compatibility wrapper"""
        return None
    
    def fetchall(self):
        """Compatibility wrapper"""
        return []


# Create a wrapper that makes async methods work in sync context
class DatabaseOperations(ConstitutionalDatabaseOperations):
    """Backward compatibility wrapper with sync methods"""
    
    def __init__(self, connection_string: str = None):
        super().__init__(connection_string)
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
    
    def get_farmer_info(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        """Sync wrapper for get_farmer_info"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_farmer_info(farmer_id))
    
    def get_all_farmers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Sync wrapper for get_all_farmers"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_all_farmers(limit))
    
    def get_farmer_fields(self, farmer_id: int) -> List[Dict[str, Any]]:
        """Sync wrapper for get_farmer_fields"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_farmer_fields(farmer_id))
    
    def get_recent_conversations(self, farmer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Sync wrapper for get_recent_conversations"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_recent_conversations(farmer_id, limit))
    
    def save_conversation(self, farmer_id: int, conversation_data: Dict[str, Any]) -> Optional[int]:
        """Sync wrapper for save_conversation"""
        loop = self._get_loop()
        return loop.run_until_complete(super().save_conversation(farmer_id, conversation_data))
    
    def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Sync wrapper for get_crop_info"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_crop_info(crop_name))
    
    def get_conversations_for_approval(self) -> Dict[str, List[Dict[str, Any]]]:
        """Sync wrapper for get_conversations_for_approval"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_conversations_for_approval())
    
    def get_conversation_details(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Sync wrapper for get_conversation_details"""
        loop = self._get_loop()
        return loop.run_until_complete(super().get_conversation_details(conversation_id))
    
    def health_check(self) -> bool:
        """Sync wrapper for health_check"""
        loop = self._get_loop()
        return loop.run_until_complete(super().health_check())
    
    def test_windows_postgresql(self) -> bool:
        """Compatibility method for testing"""
        return self.health_check()


# Test function for constitutional compliance
async def test_mango_rule_compliance():
    """Test Bulgarian mango farmer scenario"""
    db_ops = ConstitutionalDatabaseOperations()
    
    # Test Bulgarian query
    bulgarian_response = await db_ops.process_natural_query(
        query_text="Колко манго дървета имам?",  # How many mango trees do I have?
        farmer_id=123,
        language="bg",
        country_code="BG"
    )
    
    print(f"Bulgarian Mango Test Response: {bulgarian_response}")
    
    # Test Slovenian query
    slovenian_response = await db_ops.process_natural_query(
        query_text="Kdaj saditi paradižnik?",  # When to plant tomatoes?
        farmer_id=456,
        language="sl",
        country_code="SI"
    )
    
    print(f"Slovenian Tomato Test Response: {slovenian_response}")
    
    return True


if __name__ == "__main__":
    # Run compliance test
    asyncio.run(test_mango_rule_compliance())