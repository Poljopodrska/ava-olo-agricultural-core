"""
🏛️ CAVA Universal Conversation Engine
Constitutional Amendment #15: 95%+ LLM-generated logic
Handles ANY farmer conversation through LLM intelligence
"""

from __future__ import annotations

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

logger = logging.getLogger('CAVA')

class CAVAUniversalConversationEngine:
    """
    Universal conversation engine combining all CAVA components
    Constitutional principles: LLM-FIRST, MANGO RULE, FARMER-CENTRIC
    """
    
    def __init__(self):
        logger.info("🧠 CAVA: Universal Conversation Engine starting...")
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
        
        logger.info(f"🔍 CAVA: Configuration - dry_run: {self.dry_run}")
        logger.info("🏛️ CAVA: Universal Conversation Engine initialized")
    
    async def initialize(self):
        """Initialize with comprehensive logging"""
        logger.info("🚀 CAVA: Starting initialization process...")
        
        try:
            connection_status = await self.db_manager.connect_all()
            logger.info(f"🔍 CAVA: Database connections: {connection_status}")
            
            # Check environment variables
            env_vars = {
                'CAVA_DRY_RUN_MODE': os.getenv('CAVA_DRY_RUN_MODE'),
                'CAVA_ENABLE_GRAPH': os.getenv('CAVA_ENABLE_GRAPH'),
                'CAVA_ENABLE_MEMORY': os.getenv('CAVA_ENABLE_MEMORY'),
                'CAVA_REDIS_URL': os.getenv('CAVA_REDIS_URL', 'NOT_SET'),
                'CAVA_NEO4J_URI': os.getenv('CAVA_NEO4J_URI', 'NOT_SET')
            }
            logger.info(f"🔍 CAVA: Environment variables: {json.dumps(env_vars, indent=2)}")
            
            logger.info("✅ CAVA: Initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ CAVA: Initialization failed: {str(e)}")
            return False
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5)
    async def _get_conversation_with_retry(self, session_id: str) -> Optional[Dict]:
        """Get conversation with retry logic"""
        return await self.db_manager.redis.get_conversation(session_id)
    
    async def handle_farmer_message(
        self,
        farmer_id: int,
        message: str,
        session_id: Optional[str] = None,
        channel: str = "telegram"
    ) -> Dict[str, Any]:
        """Enhanced message handler with detailed logging"""
        
        logger.info(f"📨 CAVA: Handling message from farmer {farmer_id}")
        logger.info(f"🔍 CAVA: Message: '{message}' | Session: {session_id} | Channel: {channel}")
        
        try:
            # Generate or retrieve session
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info(f"🆔 CAVA: Generated new session: {session_id}")
            
            # Get conversation context from Redis
            logger.info("💾 CAVA: Retrieving conversation context from Redis...")
            conversation = await self.failover_manager.execute_with_failover(
                "redis",
                self._get_conversation_with_retry,
                session_id
            )
            
            if conversation:
                logger.info(f"📚 CAVA: Found existing conversation with {len(conversation.get('messages', []))} messages")
                logger.info(f"🔍 CAVA: Conversation state: {json.dumps(conversation.get('registration_state', {}), indent=2)}")
            else:
                logger.info("🆕 CAVA: No existing conversation found, starting fresh")
                conversation = {
                    "session_id": session_id,
                    "farmer_id": farmer_id,
                    "channel": channel,
                    "started_at": datetime.now().isoformat(),
                    "messages": [],
                    "registration_state": {},
                    "conversation_type": None
                }
            
            # Add incoming message to history
            logger.info("💬 CAVA: Adding message to conversation history...")
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
            
            # LLM analyzes the message
            logger.info("🧠 CAVA: Starting LLM analysis...")
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
            
            logger.info(f"🧠 CAVA: LLM Analysis complete:")
            logger.info(f"   Intent: {analysis.get('intent')}")
            logger.info(f"   Conversation Type: {analysis.get('conversation_type')}")
            logger.info(f"   Entities: {analysis.get('entities', {})}")
            logger.info(f"   Actions Needed: {analysis.get('actions_needed', {})}")
            
            # Route conversation
            logger.info("🔀 CAVA: Routing conversation based on analysis...")
            response = await self._route_conversation(
                farmer_id, message, analysis, conversation, session_id
            )
            
            logger.info(f"💭 CAVA: Generated response: '{response.get('message', 'NO_MESSAGE')}'")
            
            # Store response
            await self.db_manager.redis.add_message(session_id, {
                "role": "ava",
                "content": response["message"],
                "analysis": analysis
            })
            
            # Log to PostgreSQL for constitutional compliance
            await self._log_to_postgresql(session_id, farmer_id, message, response, analysis)
            
            logger.info("✅ CAVA: Message handling complete!")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": response["message"],
                "conversation_type": analysis.get("conversation_type"),
                "analysis": analysis,
                "cava_powered": True,
                "debug_info": {
                    "farmer_id": farmer_id,
                    "session_id": session_id,
                    "message_processed": True,
                    "llm_analysis_success": True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ CAVA: Error handling message: {str(e)}")
            logger.error(f"❌ CAVA: Error details: {type(e).__name__}")
            import traceback
            logger.error(f"❌ CAVA: Traceback: {traceback.format_exc()}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "I'm having technical difficulties but I'm still here to help. Could you try again?",
                "debug_info": {
                    "farmer_id": farmer_id,
                    "session_id": session_id,
                    "error_type": type(e).__name__,
                    "cava_attempted": True
                }
            }
    
    async def _route_conversation(
        self,
        farmer_id: int,
        message: str,
        analysis: Dict,
        conversation: Dict,
        session_id: str
    ) -> Dict[str, Any]:
        """Enhanced routing with detailed logging"""
        
        intent = analysis.get("intent", "unknown")
        conversation_type = analysis.get("conversation_type", "unknown")
        
        logger.info(f"🔀 CAVA: Routing - Intent: {intent}, Type: {conversation_type}")
        
        # Check if farmer is registered
        is_registered = await self._is_farmer_registered(farmer_id)
        logger.info(f"👤 CAVA: Farmer {farmer_id} registration status: {is_registered}")
        
        if intent == "registration" or not is_registered:
            logger.info("📝 CAVA: Handling as REGISTRATION conversation")
            return await self._handle_registration(
                farmer_id, message, analysis, conversation, session_id
            )
        elif intent in ["farming_question", "field_info", "harvest_timing", "product_application"]:
            logger.info("🌾 CAVA: Handling as FARMING conversation")
            return await self._handle_farming_question(
                farmer_id, message, analysis, session_id
            )
        else:
            logger.info("💬 CAVA: Handling as GENERAL CHAT")
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
        """Enhanced registration handler with detailed logging"""
        
        logger.info("📝 CAVA: Starting registration handling...")
        
        registration_state = conversation.get("registration_state", {})
        logger.info(f"📋 CAVA: Current registration state: {json.dumps(registration_state, indent=2)}")
        
        # LLM extracts registration data
        logger.info("🧠 CAVA: Extracting registration data with LLM...")
        extracted_data = await self.llm_generator.extract_registration_data(
            message, registration_state
        )
        logger.info(f"📊 CAVA: Extracted data: {json.dumps(extracted_data, indent=2)}")
        
        # Update registration state
        for field in extracted_data.get("updates_made", []):
            if field in extracted_data:
                old_value = registration_state.get(field)
                registration_state[field] = extracted_data[field]
                logger.info(f"📝 CAVA: Updated {field}: '{old_value}' → '{extracted_data[field]}'")
        
        # Check what's still missing
        required_fields = ["full_name", "phone_number", "password"]
        missing_fields = [f for f in required_fields if not registration_state.get(f)]
        
        logger.info(f"✅ CAVA: Required fields status:")
        for field in required_fields:
            status = "✅" if registration_state.get(field) else "❌"
            logger.info(f"   {status} {field}: {registration_state.get(field, 'MISSING')}")
        
        logger.info(f"📋 CAVA: Missing fields: {missing_fields}")
        
        if not missing_fields:
            logger.info("🎉 CAVA: Registration complete! Storing farmer data...")
            success = await self._complete_registration(farmer_id, registration_state)
            
            if success:
                await self._store_farmer_in_graph(farmer_id, registration_state)
                logger.info("✅ CAVA: Registration successfully completed!")
                
                return {
                    "message": f"✅ Registration complete! Welcome {registration_state['full_name']}! You can now ask me about farming, tell me about your fields, or ask when to harvest your crops.",
                    "registration_complete": True,
                    "debug_info": {"registration_successful": True}
                }
            else:
                logger.error("❌ CAVA: Registration completion failed")
                return {
                    "message": "There was an issue completing your registration. Please try again.",
                    "error": True
                }
        else:
            # Generate next question
            next_field = missing_fields[0]
            logger.info(f"❓ CAVA: Asking for next field: {next_field}")
            
            # Generate response with LLM
            response = await self._generate_registration_response(
                registration_state, missing_fields, message
            )
            
            # Update conversation state
            conversation["registration_state"] = registration_state
            await self.db_manager.redis.store_conversation(session_id, conversation)
            
            logger.info(f"💭 CAVA: Generated registration response: '{response}'")
            
            return {
                "message": response,
                "registration_in_progress": True,
                "missing_fields": missing_fields,
                "debug_info": {
                    "next_field_needed": next_field,
                    "fields_collected": len(required_fields) - len(missing_fields),
                    "total_fields": len(required_fields)
                }
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
    
    async def _generate_registration_response(self, current_state: Dict, missing_fields: List[str], last_message: str) -> str:
        """Generate registration response with logging"""
        
        logger.info("🧠 CAVA: Generating registration response with LLM...")
        
        prompt = f"""
You are AVA helping a farmer register. Generate the next question.

CURRENT STATE: {json.dumps(current_state, indent=2)}
MISSING FIELDS: {missing_fields}
FARMER JUST SAID: "{last_message}"

CRITICAL RULES:
1. Thank them for what they just provided
2. Ask for the NEXT missing field only
3. NEVER re-ask for information you already have
4. Be conversational and friendly
5. Use their name if you have it

Generate response:
"""
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            generated_response = response.choices[0].message.content.strip()
            logger.info(f"🧠 CAVA: LLM generated response: '{generated_response}'")
            return generated_response
            
        except Exception as e:
            logger.error(f"❌ CAVA: LLM response generation failed: {str(e)}")
            # Fallback response
            next_field = missing_fields[0] if missing_fields else "information"
            return f"Thanks! Could you please provide your {next_field.replace('_', ' ')}?"
    
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