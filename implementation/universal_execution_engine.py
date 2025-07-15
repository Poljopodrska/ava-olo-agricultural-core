#!/usr/bin/env python3
"""
🏛️ Constitutional Amendment #15: Universal Execution Engine
Executes whatever the LLM generates
Minimal code - maximum LLM intelligence
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncpg
import redis.asyncio as redis

from .llm_query_generator import LLMQueryGenerator

logger = logging.getLogger(__name__)

class UniversalExecutionEngine:
    """
    Executes whatever the LLM generates
    Constitutional Amendment #15 compliant - minimal code, maximum LLM intelligence
    """
    
    def __init__(self, database_url: str, redis_url: str, openai_api_key: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.llm_generator = LLMQueryGenerator(openai_api_key)
        self._db_pool = None
        self._redis_client = None
    
    async def initialize(self):
        """Initialize database and Redis connections"""
        try:
            # Initialize PostgreSQL connection pool
            self._db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            
            # Initialize Redis client
            self._redis_client = redis.from_url(self.redis_url)
            
            logger.info("🏛️ Universal Execution Engine initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize execution engine: {str(e)}")
            raise
    
    async def execute_llm_query(self, llm_generated_sql: str, farmer_context: Dict) -> List[Dict]:
        """
        🧠 Execute whatever SQL query LLM generated
        Amendment #15: Universal execution for ANY farming question
        """
        
        try:
            if not self._db_pool:
                await self.initialize()
            
            async with self._db_pool.acquire() as conn:
                # Execute LLM-generated query
                rows = await conn.fetch(llm_generated_sql)
                
                # Convert rows to dictionaries
                results = []
                for row in rows:
                    results.append(dict(row))
                
                logger.info(f"🧠 Executed LLM query, got {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"❌ LLM query execution failed: {str(e)}")
            
            # Let LLM handle the error
            error_response = await self.llm_generator.handle_query_error(
                llm_generated_sql, str(e)
            )
            
            return [{"error": error_response}]
    
    async def execute_llm_storage(self, llm_generated_operations: List[Dict], farmer_context: Dict) -> List[Dict]:
        """
        🧠 Execute whatever storage operations LLM decided
        Amendment #15: Universal storage for ANY farming data
        """
        
        results = []
        
        try:
            if not self._db_pool:
                await self.initialize()
            
            async with self._db_pool.acquire() as conn:
                async with conn.transaction():
                    
                    for operation in llm_generated_operations:
                        try:
                            if operation["type"] == "INSERT":
                                await conn.execute(
                                    operation["sql"],
                                    *operation.get("values", [])
                                )
                                results.append({
                                    "operation": operation["type"],
                                    "table": operation.get("table", "unknown"),
                                    "status": "success"
                                })
                                
                            elif operation["type"] == "UPDATE":
                                await conn.execute(
                                    operation["sql"],
                                    *operation.get("values", [])
                                )
                                results.append({
                                    "operation": operation["type"],
                                    "table": operation.get("table", "unknown"),
                                    "status": "success"
                                })
                                
                        except Exception as e:
                            logger.error(f"❌ Storage operation failed: {str(e)}")
                            results.append({
                                "operation": operation["type"],
                                "table": operation.get("table", "unknown"),
                                "status": "error",
                                "error": str(e)
                            })
            
            logger.info(f"🧠 Executed {len(llm_generated_operations)} LLM storage operations")
            return results
            
        except Exception as e:
            logger.error(f"❌ LLM storage execution failed: {str(e)}")
            return [{"error": f"Storage execution failed: {str(e)}"}]
    
    async def store_conversation_memory(self, session_id: str, message: str, response: str, context: Dict = None):
        """
        💾 Simple conversation storage - LLM doesn't need to generate this
        Amendment #15: Minimal universal functionality
        """
        
        try:
            if not self._redis_client:
                await self.initialize()
            
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "response": response,
                "context": context or {}
            }
            
            # Store in Redis list
            await self._redis_client.lpush(
                f"conversation:{session_id}",
                json.dumps(conversation_entry)
            )
            
            # Keep only last 50 messages
            await self._redis_client.ltrim(f"conversation:{session_id}", 0, 49)
            
            logger.info(f"💾 Stored conversation for session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Conversation storage failed: {str(e)}")
    
    async def get_conversation_context(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        💾 Get recent conversation for LLM context
        Amendment #15: Minimal universal functionality
        """
        
        try:
            if not self._redis_client:
                await self.initialize()
            
            # Get recent messages from Redis
            messages = await self._redis_client.lrange(f"conversation:{session_id}", 0, limit - 1)
            
            conversation_history = []
            for msg in messages:
                try:
                    conversation_entry = json.loads(msg)
                    conversation_history.append(conversation_entry)
                except json.JSONDecodeError:
                    continue
            
            # Reverse to get chronological order
            conversation_history.reverse()
            
            logger.info(f"💾 Retrieved {len(conversation_history)} conversation entries for session {session_id}")
            return conversation_history
            
        except Exception as e:
            logger.error(f"❌ Conversation retrieval failed: {str(e)}")
            return []
    
    async def get_farmer_context(self, session_id: str, farmer_id: Optional[int] = None) -> Dict:
        """
        🧠 Get farmer context for LLM processing
        Amendment #15: Universal context retrieval
        """
        
        try:
            if not self._db_pool:
                await self.initialize()
            
            context = {
                "session_id": session_id,
                "farmer_id": farmer_id,
                "fields": [],
                "recent_activities": []
            }
            
            if farmer_id:
                async with self._db_pool.acquire() as conn:
                    # Get farmer's fields
                    fields = await conn.fetch(
                        "SELECT field_name, crop_type, area_ha FROM fields WHERE farmer_id = $1",
                        farmer_id
                    )
                    context["fields"] = [dict(field) for field in fields]
                    
                    # Get recent activities
                    activities = await conn.fetch(
                        """
                        SELECT activity_type, field_name, product_name, application_date, notes
                        FROM applications 
                        WHERE farmer_id = $1 
                        ORDER BY application_date DESC 
                        LIMIT 10
                        """,
                        farmer_id
                    )
                    context["recent_activities"] = [dict(activity) for activity in activities]
            
            logger.info(f"🧠 Retrieved farmer context for session {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"❌ Farmer context retrieval failed: {str(e)}")
            return {"session_id": session_id, "error": str(e)}
    
    def get_database_schema(self) -> str:
        """
        📋 Provide LLM with database schema for query generation
        Amendment #15: Schema awareness for universal intelligence
        """
        
        return """
🏛️ Constitutional Amendment #15: Database Schema for LLM Intelligence

FARMERS TABLE:
- id (primary key)
- name (varchar)
- phone (varchar) 
- farm_name (varchar)
- country (varchar)
- language (varchar)
- registration_date (timestamp)

FIELDS TABLE:
- id (primary key)
- farmer_id (foreign key)
- field_name (varchar)
- crop_type (varchar)
- area_ha (decimal)
- plant_date (date)
- harvest_date (date)

APPLICATIONS TABLE:
- id (primary key)
- farmer_id (foreign key)
- field_name (varchar)
- product_name (varchar)
- activity_type (varchar) -- 'pesticide', 'fertilizer', 'irrigation', etc.
- application_date (timestamp)
- amount (decimal)
- notes (text)

OBSERVATIONS TABLE:
- id (primary key)
- farmer_id (foreign key)
- field_name (varchar)
- observation_date (timestamp)
- observation_type (varchar) -- 'pest', 'disease', 'growth', etc.
- description (text)
- severity (varchar)

CONSTITUTIONAL REQUIREMENTS:
- Supports ANY crop (watermelon, Bulgarian mango, unknown crops)
- Works for ANY country/language
- Handles partial data gracefully
- Scalable for international farming operations
"""
    
    async def cleanup(self):
        """Cleanup connections"""
        try:
            if self._db_pool:
                await self._db_pool.close()
            if self._redis_client:
                await self._redis_client.close()
            logger.info("🏛️ Universal Execution Engine cleaned up")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")
    
    async def health_check(self) -> Dict:
        """
        🔍 Health check for universal execution engine
        Amendment #15: System health monitoring
        """
        
        health_status = {
            "status": "healthy",
            "database": "unknown",
            "redis": "unknown",
            "llm_generator": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check database
            if self._db_pool:
                async with self._db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                health_status["database"] = "healthy"
            else:
                health_status["database"] = "not_initialized"
            
            # Check Redis
            if self._redis_client:
                await self._redis_client.ping()
                health_status["redis"] = "healthy"
            else:
                health_status["redis"] = "not_initialized"
            
            # Check LLM generator
            if self.llm_generator:
                health_status["llm_generator"] = "healthy"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status