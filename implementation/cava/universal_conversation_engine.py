"""
🏛️ CAVA Universal Conversation Engine
Constitutional Amendment #15: 95%+ LLM-generated logic
Handles ANY farmer conversation through LLM intelligence
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from implementation.cava.database_connections import CAVADatabaseManager
from implementation.cava.llm_query_generator import CAVALLMQueryGenerator
from implementation.cava.error_handling import (
    CAVAFailoverManager, 
    CAVAErrorRecovery, 
    create_cava_error_handler,
    retry_with_backoff
)
from implementation.cava.performance_optimization import (
    CAVAPerformanceOptimizer,
    CAVAResponseCache,
    CAVAParallelProcessor,
    integrate_performance_optimization
)
from config_manager import config as main_config

logger = logging.getLogger(__name__)

class CAVAUniversalConversationEngine:
    """
    Universal conversation engine combining all CAVA components
    Constitutional principles: LLM-FIRST, MANGO RULE, FARMER-CENTRIC
    """
    
    def __init__(self):
        self.db_manager = CAVADatabaseManager()
        self.llm_generator = CAVALLMQueryGenerator()
        self.dry_run = os.getenv('CAVA_DRY_RUN_MODE', 'true').lower() == 'true'
        self.session_timeout = int(os.getenv('CAVA_SESSION_TIMEOUT', '3600'))
        
        # Enhancement 2: Production-grade error handling
        self.failover_manager, self.error_recovery = create_cava_error_handler()
        
        # Enhancement 3: Performance optimization
        self.performance_optimizer = CAVAPerformanceOptimizer()
        self.response_cache = CAVAResponseCache()
        self.parallel_processor = CAVAParallelProcessor()
        
        logger.info("🏛️ CAVA Universal Engine initialized (dry_run: %s)", self.dry_run)
    
    async def initialize(self):
        """Initialize all CAVA components"""
        logger.info("🚀 Initializing CAVA Universal Engine...")
        
        # Connect to all databases
        success = await self.db_manager.connect_all()
        if not success and not self.dry_run:
            logger.error("❌ Failed to connect to all databases")
            raise RuntimeError("CAVA initialization failed")
        
        logger.info("✅ CAVA Universal Engine ready!")
        return success
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5)
    async def _get_conversation_with_retry(self, session_id: str) -> Optional[Dict]:
        """Get conversation with retry logic"""
        return await self.db_manager.redis.get_conversation(session_id)
    
    @CAVAPerformanceOptimizer().track_performance("handle_farmer_message")
    async def handle_farmer_message(
        self,
        farmer_id: int,
        message: str,
        session_id: Optional[str] = None,
        channel: str = "telegram"
    ) -> Dict[str, Any]:
        """
        Universal handler for ANY farmer message
        Works for registration, farming questions, ANY crop, ANY country
        """
        try:
            # Generate or retrieve session
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info("📝 New session: %s", session_id)
            
            # Get conversation context from Redis with failover
            conversation = await self.failover_manager.execute_with_failover(
                "redis",
                self._get_conversation_with_retry,
                session_id
            ) or {
                "session_id": session_id,
                "farmer_id": farmer_id,
                "channel": channel,
                "started_at": datetime.now().isoformat(),
                "messages": [],
                "registration_state": {},
                "conversation_type": None
            }
            
            # Add incoming message to history
            await self.db_manager.redis.add_message(session_id, {
                "role": "farmer",
                "content": message,
                "channel": channel
            })
            
            # Check cache first for performance
            cache_context = {
                "farmer_id": farmer_id,
                "conversation_type": conversation.get("conversation_type")
            }
            
            # LLM analyzes the message with failover and caching (Amendment #15)
            analysis, was_cached = await self.response_cache.get_or_compute(
                farmer_id=farmer_id,
                message=message,
                context=cache_context,
                compute_func=lambda: self.failover_manager.execute_with_failover(
                    "openai",
                    self.llm_generator.analyze_farmer_message,
                    message, 
                    {
                        "farmer_id": farmer_id,
                        "recent_messages": conversation.get("messages", [])[-5:],
                        "registration_state": conversation.get("registration_state", {})
                    }
                )
            )
            
            if was_cached:
                logger.debug("🚀 Using cached analysis for faster response")
            
            logger.info("🧠 LLM Analysis: intent=%s, type=%s", 
                       analysis.get("intent"), analysis.get("conversation_type"))
            
            # Route based on LLM analysis
            response = await self._route_conversation(
                farmer_id, message, analysis, conversation, session_id
            )
            
            # Store response in conversation
            await self.db_manager.redis.add_message(session_id, {
                "role": "ava",
                "content": response["message"],
                "analysis": analysis
            })
            
            # Log to PostgreSQL for constitutional compliance
            await self._log_to_postgresql(session_id, farmer_id, message, response, analysis)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": response["message"],
                "conversation_type": analysis.get("conversation_type"),
                "analysis": analysis,
                "requires_action": response.get("requires_action", False)
            }
            
        except Exception as e:
            logger.error("❌ Error handling message: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "I'm having trouble understanding. Could you please try again?"
            }
    
    async def _route_conversation(
        self,
        farmer_id: int,
        message: str,
        analysis: Dict,
        conversation: Dict,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Route conversation based on LLM analysis
        Supports registration, farming questions, mixed conversations
        """
        intent = analysis.get("intent", "general_chat")
        conversation_type = analysis.get("conversation_type", "farming")
        
        # Registration flow
        if intent == "registration" or not await self._is_farmer_registered(farmer_id):
            return await self._handle_registration(
                farmer_id, message, analysis, conversation, session_id
            )
        
        # Farming questions - use graph database
        elif intent in ["farming_question", "field_info", "harvest_timing", "product_application"]:
            return await self._handle_farming_question(
                farmer_id, message, analysis, session_id
            )
        
        # General chat or unknown
        else:
            return await self._handle_general_chat(
                farmer_id, message, analysis
            )
    
    async def _handle_registration(
        self,
        farmer_id: int,
        message: str,
        analysis: Dict,
        conversation: Dict,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Handle registration flow using LLM extraction
        Solves the Peter → Knaflič re-asking problem
        """
        registration_state = conversation.get("registration_state", {})
        
        # LLM extracts registration data
        extracted_data = await self.llm_generator.extract_registration_data(
            message, registration_state
        )
        
        # Update registration state
        for field in extracted_data.get("updates_made", []):
            if field in extracted_data:
                registration_state[field] = extracted_data[field]
        
        # Check what's still missing
        required_fields = ["full_name", "phone_number", "password"]
        missing_fields = [f for f in required_fields if not registration_state.get(f)]
        
        if not missing_fields:
            # Registration complete - store in databases
            success = await self._complete_registration(farmer_id, registration_state)
            
            if success:
                # Store in Neo4j graph
                await self._store_farmer_in_graph(farmer_id, registration_state)
                
                return {
                    "message": f"✅ Registration complete! Welcome {registration_state['full_name']}! You can now ask me about farming, tell me about your fields, or ask when to harvest your crops.",
                    "registration_complete": True
                }
            else:
                return {
                    "message": "There was an issue completing your registration. Please try again.",
                    "error": True
                }
        
        else:
            # Ask for next missing field
            next_field = missing_fields[0]
            
            if next_field == "full_name":
                prompt = "👋 Welcome to AVA! What's your name?"
            elif next_field == "phone_number":
                prompt = f"Thanks {registration_state.get('first_name', '')}! What's your phone number (with country code)?"
            elif next_field == "password":
                prompt = "Almost done! Please create a password for your account:"
            else:
                prompt = f"Please provide your {next_field}:"
            
            # Update conversation state
            conversation["registration_state"] = registration_state
            await self.db_manager.redis.store_conversation(session_id, conversation)
            
            return {
                "message": prompt,
                "registration_in_progress": True,
                "missing_fields": missing_fields
            }
    
    async def _handle_farming_question(
        self,
        farmer_id: int,
        message: str,
        analysis: Dict,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Handle farming questions using graph database and LLM
        Works for watermelon, Bulgarian mango, dragonfruit, ANY crop
        Enhanced with vector intelligence for semantic understanding
        """
        # Enhancement 1 & 3: Parallel semantic retrieval for performance
        if self.db_manager.pinecone.enabled:
            # Execute semantic operations in parallel
            parallel_ops = [
                ("similar_contexts", lambda: self.db_manager.pinecone.search_similar_conversations(
                    query_text=message,
                    farmer_id=farmer_id,
                    top_k=3
                )),
                ("sentiment_analysis", lambda: self.db_manager.pinecone.analyze_conversation_sentiment(message))
            ]
            
            results = await self.parallel_processor.execute_parallel(parallel_ops)
            similar_contexts = results.get("similar_contexts", [])
            sentiment_analysis = results.get("sentiment_analysis", {})
            
            # If farmer seems worried/stressed, adjust response tone
            if sentiment_analysis.get("sentiment_detected"):
                analysis["emotional_state"] = sentiment_analysis
                logger.info("🎭 Detected emotional state: %s", 
                           sentiment_analysis.get("emotional_keywords", []))
        else:
            similar_contexts = []
            sentiment_analysis = {}
        
        # Check if we need to store information first
        if analysis.get("actions_needed", {}).get("store_in_graph"):
            # LLM generates storage query
            storage_query = await self.llm_generator.generate_graph_storage_query(
                analysis, farmer_id
            )
            
            if storage_query:
                # Extract parameters from entities
                params = self._extract_query_parameters(analysis, farmer_id)
                
                # Execute storage
                await self.db_manager.neo4j.execute_query(storage_query, params)
                logger.info("💾 Stored farming data in graph")
                
                # Store conversation embedding for future semantic search
                if self.db_manager.pinecone.enabled:
                    await self.db_manager.pinecone.store_conversation_embedding(
                        session_id=session_id,
                        content=message,
                        metadata={
                            "farmer_id": farmer_id,
                            "conversation_type": "farming_info_storage",
                            "entities": analysis.get("entities", {}),
                            "crop": analysis.get("entities", {}).get("crops", ["unknown"])[0]
                        }
                    )
        
        # Generate query to answer the question
        if analysis.get("actions_needed", {}).get("query_graph"):
            query = await self.llm_generator.generate_graph_query(
                message, farmer_id, {"session_id": session_id}
            )
            
            if query:
                # Execute query
                params = {"farmer_id": farmer_id}
                graph_data = await self.db_manager.neo4j.execute_query(query, params)
                
                # Enhanced response generation with context
                response = await self.llm_generator.generate_response_from_data(
                    message, 
                    graph_data, 
                    {
                        **analysis,
                        "similar_contexts": similar_contexts,
                        "emotional_state": sentiment_analysis
                    }
                )
                
                # Store this Q&A for future semantic search
                if self.db_manager.pinecone.enabled:
                    await self.db_manager.pinecone.store_conversation_embedding(
                        session_id=session_id,
                        content=f"Q: {message}\nA: {response}",
                        metadata={
                            "farmer_id": farmer_id,
                            "conversation_type": "farming_qa",
                            "intent": analysis.get("intent"),
                            "helpful": True
                        }
                    )
                
                return {"message": response}
        
        # Default farming response
        return {
            "message": "I'm here to help with your farming questions. Could you tell me more about what you need?"
        }
    
    async def _handle_general_chat(
        self,
        farmer_id: int,
        message: str,
        analysis: Dict
    ) -> Dict[str, Any]:
        """Handle general conversation"""
        # Simple responses for now
        responses = {
            "greeting": "Hello! How can I help you with your farming today?",
            "thanks": "You're welcome! Let me know if you need anything else.",
            "goodbye": "Goodbye! Feel free to ask me about your crops anytime!",
            "default": "I'm here to help with farming. You can ask about your fields, when to harvest, or what products you've applied."
        }
        
        # Detect simple intents
        lower_msg = message.lower()
        if any(word in lower_msg for word in ["hello", "hi", "hey"]):
            return {"message": responses["greeting"]}
        elif any(word in lower_msg for word in ["thanks", "thank you"]):
            return {"message": responses["thanks"]}
        elif any(word in lower_msg for word in ["bye", "goodbye"]):
            return {"message": responses["goodbye"]}
        else:
            return {"message": responses["default"]}
    
    async def _is_farmer_registered(self, farmer_id: int) -> bool:
        """Check if farmer is registered"""
        try:
            # Check PostgreSQL for registration
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM farmers 
                    WHERE telegram_id = $1 OR whatsapp_id = $1
                )
            """
            result = await self.db_manager.postgresql.execute_query(query, farmer_id)
            return result[0]["exists"] if result else False
        except:
            # In dry-run or error, assume registered
            return self.dry_run
    
    async def _complete_registration(self, farmer_id: int, registration_data: Dict) -> bool:
        """Complete farmer registration in PostgreSQL"""
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would complete registration for farmer %s", farmer_id)
            return True
        
        try:
            # Store in PostgreSQL
            query = """
                INSERT INTO farmers (telegram_id, full_name, phone_number, password, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (telegram_id) 
                DO UPDATE SET 
                    full_name = EXCLUDED.full_name,
                    phone_number = EXCLUDED.phone_number,
                    updated_at = NOW()
            """
            
            await self.db_manager.postgresql.execute_query(
                query,
                farmer_id,
                registration_data.get("full_name"),
                registration_data.get("phone_number"),
                registration_data.get("password")  # Should be hashed in production
            )
            
            logger.info("✅ Farmer %s registered successfully", farmer_id)
            return True
        except Exception as e:
            logger.error("❌ Registration failed: %s", str(e))
            return False
    
    async def _store_farmer_in_graph(self, farmer_id: int, registration_data: Dict):
        """Store farmer node in Neo4j graph"""
        query = """
        MERGE (f:Farmer {id: $farmer_id})
        SET f.name = $name,
            f.phone = $phone,
            f.registered_at = datetime(),
            f.country = $country
        """
        
        params = {
            "farmer_id": farmer_id,
            "name": registration_data.get("full_name"),
            "phone": registration_data.get("phone_number"),
            "country": registration_data.get("country_detected", "Unknown")
        }
        
        await self.db_manager.neo4j.execute_query(query, params)
        logger.info("📊 Farmer stored in graph database")
    
    async def _log_to_postgresql(
        self,
        session_id: str,
        farmer_id: int,
        message: str,
        response: Dict,
        analysis: Dict
    ):
        """Log conversation to PostgreSQL for constitutional compliance"""
        if self.dry_run:
            return
        
        try:
            query = """
                INSERT INTO cava.conversation_sessions 
                (session_id, farmer_id, conversation_type, total_messages, last_message_at)
                VALUES ($1, $2, $3, 1, NOW())
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    total_messages = cava.conversation_sessions.total_messages + 1,
                    last_message_at = NOW()
            """
            
            await self.db_manager.postgresql.execute_query(
                query,
                session_id,
                farmer_id,
                analysis.get("conversation_type", "unknown")
            )
            
            # Log intelligence analysis
            intel_query = """
                INSERT INTO cava.intelligence_log
                (session_id, message_type, llm_analysis, llm_response, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """
            
            await self.db_manager.postgresql.execute_query(
                intel_query,
                session_id,
                analysis.get("intent", "unknown"),
                json.dumps(analysis),
                response.get("message", "")
            )
            
        except Exception as e:
            logger.error("❌ PostgreSQL logging failed: %s", str(e))
    
    def _extract_query_parameters(self, analysis: Dict, farmer_id: int) -> Dict:
        """Extract parameters for database queries from LLM analysis"""
        entities = analysis.get("entities", {})
        
        params = {"farmer_id": farmer_id}
        
        # Add extracted entities as parameters
        if entities.get("fields"):
            params["field_name"] = entities["fields"][0]
        
        if entities.get("crops"):
            params["crop_type"] = entities["crops"][0]
        
        if entities.get("products"):
            params["product_name"] = entities["products"][0]
        
        if entities.get("dates"):
            params["date"] = entities["dates"][0]
        
        return params
    
    async def get_conversation_history(self, session_id: str) -> Optional[Dict]:
        """Get full conversation history"""
        return await self.db_manager.redis.get_conversation(session_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all CAVA components"""
        db_health = await self.db_manager.health_check()
        
        return {
            "status": "healthy" if all(v == "healthy" or v == "disabled" for v in db_health.values()) else "degraded",
            "databases": db_health,
            "llm_configured": bool(self.llm_generator.api_key),
            "dry_run_mode": self.dry_run
        }
    
    async def close(self):
        """Clean shutdown of all connections"""
        await self.db_manager.close_all()
        logger.info("🔒 CAVA Universal Engine shut down")

# Test the universal engine
async def test_universal_engine():
    """Test CAVA Universal Conversation Engine"""
    logging.basicConfig(level=logging.INFO)
    
    engine = CAVAUniversalConversationEngine()
    
    try:
        # Initialize
        await engine.initialize()
        
        # Test 1: Registration flow (Peter Knaflič scenario)
        print("\n🧪 Test 1: Registration Flow")
        
        # First message - just name
        response1 = await engine.handle_farmer_message(
            farmer_id=12345,
            message="Peter Knaflič"
        )
        print(f"Response 1: {response1['message']}")
        session_id = response1["session_id"]
        
        # Second message - phone
        response2 = await engine.handle_farmer_message(
            farmer_id=12345,
            message="+385912345678",
            session_id=session_id
        )
        print(f"Response 2: {response2['message']}")
        
        # Third message - password
        response3 = await engine.handle_farmer_message(
            farmer_id=12345,
            message="mypassword123",
            session_id=session_id
        )
        print(f"Response 3: {response3['message']}")
        
        # Test 2: Watermelon question
        print("\n🧪 Test 2: Watermelon Question")
        response4 = await engine.handle_farmer_message(
            farmer_id=12345,
            message="I planted watermelon in my north field last week"
        )
        print(f"Response 4: {response4['message']}")
        
        response5 = await engine.handle_farmer_message(
            farmer_id=12345,
            message="Where is my watermelon?"
        )
        print(f"Response 5: {response5['message']}")
        
        # Test 3: Bulgarian mango (MANGO RULE)
        print("\n🧪 Test 3: Bulgarian Mango")
        response6 = await engine.handle_farmer_message(
            farmer_id=67890,
            message="When can I harvest my Bulgarian mangoes?"
        )
        print(f"Response 6: {response6['message']}")
        
        # Health check
        health = await engine.health_check()
        print(f"\n🏥 Health Check: {json.dumps(health, indent=2)}")
        
    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(test_universal_engine())