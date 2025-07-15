#!/usr/bin/env python3
"""
🏛️ Constitutional Amendment #15: Zero-Code Conversation Engine
Universal conversation handler - LLM generates ALL intelligence
Constitutional Amendment #15 compliant
"""
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .universal_execution_engine import UniversalExecutionEngine

logger = logging.getLogger(__name__)

class ZeroCodeConversationEngine:
    """
    🏛️ Universal conversation handler - LLM generates ALL intelligence
    Constitutional Amendment #15 compliant: "If the LLM can write it, don't code it"
    
    Handles:
    - Registration conversations (Peter → Knaflič)
    - Farming questions (watermelon location, Bulgarian mango harvest)
    - Mixed conversations (questions + new information)
    - ANY crop, ANY country, ANY farming scenario
    """
    
    def __init__(self, session_id: str, database_url: str, redis_url: str, openai_api_key: str):
        self.session_id = session_id
        self.executor = UniversalExecutionEngine(database_url, redis_url, openai_api_key)
        self.conversation_state = "active"
        self.farmer_id = None
    
    async def initialize(self):
        """Initialize the conversation engine"""
        await self.executor.initialize()
        logger.info(f"🏛️ Zero-Code Conversation Engine initialized for session {self.session_id}")
    
    async def chat(self, farmer_message: str) -> Dict[str, Any]:
        """
        🧠 Handle ANY farmer message with zero custom coding
        LLM generates all necessary intelligence
        Constitutional Amendment #15: Universal conversation processing
        """
        
        try:
            # Step 1: Get conversation context
            conversation_history = await self.executor.get_conversation_context(self.session_id)
            farmer_context = await self.executor.get_farmer_context(self.session_id, self.farmer_id)
            
            # Step 2: LLM analyzes what to do with this message
            analysis = await self.executor.llm_generator.analyze_message_intent(
                farmer_message, conversation_history
            )
            
            # Step 3: Execute whatever LLM decided to store
            storage_results = []
            if analysis.get("storage_needed"):
                storage_ops = await self.executor.llm_generator.generate_storage_instructions(
                    farmer_message, farmer_context
                )
                if storage_ops:
                    storage_results = await self.executor.execute_llm_storage(storage_ops, farmer_context)
            
            # Step 4: Execute whatever LLM decided to query
            query_results = []
            if analysis.get("query_needed"):
                query = await self.executor.llm_generator.generate_database_query(
                    farmer_message, farmer_context, self.executor.get_database_schema()
                )
                query_results = await self.executor.execute_llm_query(query, farmer_context)
            
            # Step 5: LLM generates the response
            response = await self.executor.llm_generator.generate_response_logic(
                farmer_message, query_results, farmer_context
            )
            
            # Step 6: Store conversation
            await self.executor.store_conversation_memory(
                self.session_id, farmer_message, response, {
                    "analysis": analysis,
                    "storage_results": storage_results,
                    "query_results": query_results
                }
            )
            
            # Step 7: Check if this is registration completion
            registration_status = await self._check_registration_completion(
                farmer_message, response, conversation_history
            )
            
            return {
                "message": response,
                "session_id": self.session_id,
                "llm_generated": True,  # Everything was LLM-generated!
                "amendment_15_compliance": True,
                "analysis": analysis,
                "storage_results": storage_results,
                "query_results": query_results,
                "registration_status": registration_status,
                "farmer_context": farmer_context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Zero-code conversation failed: {str(e)}")
            
            # Even error handling is LLM-generated
            error_response = await self.executor.llm_generator.handle_query_error(
                farmer_message, str(e)
            )
            
            return {
                "message": error_response,
                "session_id": self.session_id,
                "llm_generated": True,
                "amendment_15_compliance": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_registration_completion(self, farmer_message: str, response: str, conversation_history: List[Dict]) -> Dict:
        """
        🧠 LLM determines if registration is complete
        Amendment #15: Universal registration intelligence
        """
        
        try:
            # Let LLM determine registration status
            registration_prompt = f"""
🏛️ Constitutional Amendment #15: Registration Intelligence

Analyze if farmer registration is complete based on this conversation.

RECENT MESSAGE: "{farmer_message}"
AVA RESPONSE: "{response}"
CONVERSATION: {json.dumps(conversation_history[-10:], indent=2)}

REGISTRATION REQUIREMENTS:
- full_name (first and last name)
- phone_number (WhatsApp format)
- password (confirmed)
- farm_name

Return JSON:
{{
  "registration_complete": true/false,
  "collected_data": {{
    "full_name": "extracted name or null",
    "phone_number": "extracted phone or null",
    "password": "extracted password or null",
    "farm_name": "extracted farm name or null"
  }},
  "next_needed": "what's still needed or null"
}}
"""
            
            registration_analysis = await self.executor.llm_generator.llm.apredict_messages([
                {"role": "user", "content": registration_prompt}
            ])
            
            analysis_content = registration_analysis.content.strip()
            
            # Parse JSON response
            if analysis_content.startswith('```json'):
                analysis_content = analysis_content[7:]
            if analysis_content.endswith('```'):
                analysis_content = analysis_content[:-3]
            
            registration_status = json.loads(analysis_content)
            
            # If registration is complete, create farmer account
            if registration_status.get("registration_complete"):
                farmer_data = registration_status.get("collected_data", {})
                if all(farmer_data.values()):  # All fields have values
                    farmer_id = await self._create_farmer_account(farmer_data)
                    registration_status["farmer_id"] = farmer_id
                    self.farmer_id = farmer_id
            
            return registration_status
            
        except Exception as e:
            logger.error(f"❌ Registration analysis failed: {str(e)}")
            return {"registration_complete": False, "error": str(e)}
    
    async def _create_farmer_account(self, farmer_data: Dict) -> Optional[int]:
        """
        🧠 Create farmer account when registration is complete
        Amendment #15: Universal account creation
        """
        
        try:
            # Generate SQL for farmer creation
            create_farmer_sql = """
            INSERT INTO farmers (name, phone, farm_name, country, language, registration_date)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """
            
            # Detect country from phone number (LLM could do this too)
            country = "Unknown"
            if farmer_data.get("phone_number", "").startswith("+385"):
                country = "Croatia"
            elif farmer_data.get("phone_number", "").startswith("+359"):
                country = "Bulgaria"
            
            async with self.executor._db_pool.acquire() as conn:
                farmer_id = await conn.fetchval(
                    create_farmer_sql,
                    farmer_data["full_name"],
                    farmer_data["phone_number"],
                    farmer_data["farm_name"],
                    country,
                    "en",  # Default language
                    datetime.now()
                )
            
            logger.info(f"🏛️ Created farmer account {farmer_id} for {farmer_data['full_name']}")
            return farmer_id
            
        except Exception as e:
            logger.error(f"❌ Farmer account creation failed: {str(e)}")
            return None
    
    async def handle_mixed_conversation(self, farmer_message: str) -> Dict[str, Any]:
        """
        🧠 Handle mixed conversations (registration + farming questions)
        Amendment #15: Universal conversation intelligence
        """
        
        # The main chat() method already handles mixed conversations
        # LLM intelligence determines what parts are registration vs farming
        return await self.chat(farmer_message)
    
    async def get_conversation_summary(self) -> Dict[str, Any]:
        """
        📊 Get conversation summary for monitoring
        Amendment #15: Universal conversation analytics
        """
        
        try:
            conversation_history = await self.executor.get_conversation_context(self.session_id, 50)
            
            # Let LLM analyze conversation patterns
            summary_prompt = f"""
🏛️ Constitutional Amendment #15: Conversation Analytics

Analyze this conversation for insights.

CONVERSATION: {json.dumps(conversation_history, indent=2)}

Return JSON summary:
{{
  "message_count": 0,
  "conversation_type": "registration|farming|mixed",
  "crops_mentioned": ["watermelon", "mango"],
  "fields_mentioned": ["north", "south"],
  "activities_discussed": ["planting", "harvesting", "pesticides"],
  "farmer_needs": ["field location", "harvest timing"],
  "completion_status": "ongoing|registration_complete|farming_active"
}}
"""
            
            summary_response = await self.executor.llm_generator.llm.apredict_messages([
                {"role": "user", "content": summary_prompt}
            ])
            
            summary_content = summary_response.content.strip()
            
            if summary_content.startswith('```json'):
                summary_content = summary_content[7:]
            if summary_content.endswith('```'):
                summary_content = summary_content[:-3]
            
            summary = json.loads(summary_content)
            summary["session_id"] = self.session_id
            summary["farmer_id"] = self.farmer_id
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Conversation summary failed: {str(e)}")
            return {
                "session_id": self.session_id,
                "error": str(e),
                "message_count": len(conversation_history) if 'conversation_history' in locals() else 0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        🔍 Health check for zero-code conversation engine
        Amendment #15: System health monitoring
        """
        
        engine_health = {
            "session_id": self.session_id,
            "conversation_state": self.conversation_state,
            "farmer_id": self.farmer_id,
            "amendment_15_compliance": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check executor health
        executor_health = await self.executor.health_check()
        engine_health.update(executor_health)
        
        return engine_health
    
    async def cleanup(self):
        """Cleanup conversation engine"""
        try:
            await self.executor.cleanup()
            logger.info(f"🏛️ Zero-Code Conversation Engine cleaned up for session {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")