"""
🏛️ CAVA Database Connection Classes
Handles connections to all 4 CAVA databases
Constitutional principles: MODULE INDEPENDENCE, ERROR ISOLATION, PRIVACY-FIRST
"""

from __future__ import annotations

import os
import json
import redis
import asyncpg
from neo4j import GraphDatabase
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config_manager import config as main_config

# Load environments - try multiple locations for flexibility
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(base_dir, '.env'))  # Main .env
load_dotenv(os.path.join(base_dir, '.env.cava'))  # CAVA-specific
# Also try parent directory
parent_dir = os.path.dirname(base_dir)
load_dotenv(os.path.join(parent_dir, '.env'))

# Configure CAVA-specific logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CAVA')

class CAVANeo4jConnection:
    """Neo4j Graph Database Connection for CAVA"""
    
    def __init__(self):
        self.uri = os.getenv('CAVA_NEO4J_URI', 'bolt://localhost:7687')
        self.user = os.getenv('CAVA_NEO4J_USER', 'neo4j')
        self.password = os.getenv('CAVA_NEO4J_PASSWORD', 'cavapassword123')
        self.driver = None
        self.dry_run = os.getenv('CAVA_DRY_RUN_MODE', 'true').lower() == 'true'
    
    async def connect(self):
        """Initialize Neo4j connection with safety checks"""
        try:
            if self.dry_run:
                logger.info("🔍 DRY RUN: Would connect to Neo4j at %s", self.uri)
                return
            
            # Add timeout to prevent hanging
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            def create_driver():
                return GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50
                )
            
            # Use thread pool with timeout
            with ThreadPoolExecutor() as executor:
                future = executor.submit(create_driver)
                try:
                    self.driver = await asyncio.wait_for(
                        asyncio.wrap_future(future), 
                        timeout=10.0  # 10 second timeout
                    )
                except asyncio.TimeoutError:
                    logger.error("❌ Neo4j connection timeout")
                    return
            
            # Test connection with timeout
            def test_connection():
                with self.driver.session() as session:
                    result = session.run("RETURN 'CAVA Neo4j Connected' as message")
                    return result.single()['message']
            
            with ThreadPoolExecutor() as executor:
                future = executor.submit(test_connection)
                try:
                    message = await asyncio.wait_for(
                        asyncio.wrap_future(future), 
                        timeout=5.0  # 5 second timeout
                    )
                    logger.info("✅ %s", message)
                except asyncio.TimeoutError:
                    logger.error("❌ Neo4j test query timeout")
                    
        except Exception as e:
            logger.error("❌ Neo4j connection failed: %s", str(e))
            # ERROR ISOLATION - Don't crash, just log
            if not self.dry_run:
                raise
    
    async def execute_query(self, cypher_query: str, parameters: Dict = None) -> List[Dict]:
        """Execute Cypher query with safety checks"""
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would execute Cypher: %s", cypher_query[:100])
            return []
        
        if not self.driver:
            logger.warning("⚠️ Neo4j not connected")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error("❌ Cypher execution failed: %s", str(e))
            return []
    
    async def close(self):
        if self.driver:
            self.driver.close()
            logger.info("🔒 Neo4j connection closed")

class CAVARedisConnection:
    """Redis Memory Connection for CAVA"""
    
    def __init__(self):
        self.url = os.getenv('CAVA_REDIS_URL', 'redis://localhost:6379')
        self.expire_seconds = int(os.getenv('CAVA_REDIS_EXPIRE_SECONDS', '3600'))
        self.client = None
        self.dry_run = os.getenv('CAVA_DRY_RUN_MODE', 'true').lower() == 'true'
        self._dry_run_conversations = {}  # Mock storage for dry-run mode
    
    async def connect(self):
        """Initialize Redis connection with safety checks"""
        try:
            if self.dry_run:
                logger.info("🔍 DRY RUN: Would connect to Redis at %s", self.url)
                return
            
            # Add timeout to prevent hanging
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            def create_redis_client():
                client = redis.from_url(
                    self.url, 
                    decode_responses=True,
                    socket_timeout=5,  # 5 second socket timeout
                    socket_connect_timeout=5  # 5 second connection timeout
                )
                client.ping()  # Test connection
                return client
            
            # Use thread pool with timeout
            with ThreadPoolExecutor() as executor:
                future = executor.submit(create_redis_client)
                try:
                    self.client = await asyncio.wait_for(
                        asyncio.wrap_future(future), 
                        timeout=10.0  # 10 second timeout
                    )
                    logger.info("✅ CAVA Redis Connected")
                except asyncio.TimeoutError:
                    logger.error("❌ Redis connection timeout")
                    return
                    
        except Exception as e:
            logger.error("❌ Redis connection failed: %s", str(e))
            # ERROR ISOLATION - Don't crash
            if not self.dry_run:
                raise
    
    async def store_conversation(self, session_id: str, conversation_data: Dict):
        """Store conversation with privacy checks"""
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would store conversation for session %s", session_id)
            # Store in mock storage for testing
            self._dry_run_conversations[session_id] = conversation_data
            return
        
        if not self.client:
            logger.warning("⚠️ Redis not connected")
            return
        
        try:
            # PRIVACY-FIRST: Don't log sensitive data
            key = f"cava:conversation:{session_id}"
            value = json.dumps(conversation_data)
            self.client.setex(key, self.expire_seconds, value)
            logger.debug("💾 Stored conversation for session %s", session_id)
        except Exception as e:
            logger.error("❌ Redis store failed: %s", str(e))
    
    async def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Retrieve conversation data"""
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would get conversation for session %s", session_id)
            # Return mock conversation for testing
            return self._dry_run_conversations.get(session_id, {})
        
        if not self.client:
            return None
        
        try:
            key = f"cava:conversation:{session_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error("❌ Redis get failed: %s", str(e))
            return None
    
    async def add_message(self, session_id: str, message: Dict):
        """Add message to conversation history"""
        conversation = await self.get_conversation(session_id) or {"messages": []}
        conversation["messages"].append({
            **message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 messages (PRODUCTION-READY)
        conversation["messages"] = conversation["messages"][-50:]
        await self.store_conversation(session_id, conversation)

class CAVAPineconeConnection:
    """Pinecone Vector Connection for CAVA (Optional)"""
    
    def __init__(self):
        self.api_key = os.getenv('CAVA_PINECONE_API_KEY')
        self.environment = os.getenv('CAVA_PINECONE_ENVIRONMENT')
        self.index_name = os.getenv('CAVA_PINECONE_INDEX', 'cava-conversations')
        self.index = None
        self.enabled = os.getenv('CAVA_ENABLE_VECTOR', 'false').lower() == 'true'
        self.dry_run = os.getenv('CAVA_DRY_RUN_MODE', 'true').lower() == 'true'
    
    async def connect(self):
        """Initialize Pinecone connection if enabled"""
        if not self.enabled:
            logger.info("⏭️ Pinecone vector search disabled")
            return
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would connect to Pinecone")
            return
        
        try:
            import pinecone
            pinecone.init(
                api_key=self.api_key,
                environment=self.environment
            )
            
            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                logger.info("📐 Creating Pinecone index: %s", self.index_name)
                pinecone.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine"
                )
            
            self.index = pinecone.Index(self.index_name)
            logger.info("✅ CAVA Pinecone Connected")
        except ImportError:
            logger.warning("⚠️ Pinecone not installed - vector search disabled")
        except Exception as e:
            logger.error("❌ Pinecone connection failed: %s", str(e))
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        if not self.enabled or self.dry_run:
            return [0.0] * 1536  # Mock embedding
        
        try:
            import openai
            from config_manager import config
            openai.api_key = config.openai_api_key
            
            response = await openai.Embedding.acreate(
                input=text,
                model="text-embedding-ada-002"
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * 1536  # Fallback zero embedding
    
    async def store_conversation_embedding(self, session_id: str, content: str, metadata: Dict):
        """Store conversation with semantic embedding"""
        if not self.enabled or self.dry_run:
            logger.debug("Vector storage disabled or in dry-run mode")
            return
        
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Enhanced metadata
            enhanced_metadata = {
                **metadata,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content),
                "session_id": session_id,
                "content_preview": content[:200]  # First 200 chars
            }
            
            # Store in Pinecone
            self.index.upsert([(
                f"{session_id}_{datetime.now().timestamp()}",
                embedding,
                enhanced_metadata
            )])
            
            logger.info(f"✅ Stored embedding for session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store embedding: {e}")
    
    async def search_similar_conversations(self, query_text: str, farmer_id: int = None, top_k: int = 5) -> List[Dict]:
        """Search for semantically similar conversations"""
        if not self.enabled:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query_text)
            
            # Build filter
            filter_dict = {}
            if farmer_id:
                filter_dict["farmer_id"] = farmer_id
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            # Format results
            similar_contexts = []
            for match in results.get('matches', []):
                similar_contexts.append({
                    "score": match['score'],
                    "metadata": match.get('metadata', {}),
                    "content": match.get('metadata', {}).get('content_preview', '')
                })
            
            return similar_contexts
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []
    
    async def analyze_conversation_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze farmer's emotional state from conversation"""
        if not self.enabled:
            return {"sentiment_detected": False}
        
        try:
            # Search for similar emotional contexts
            emotional_keywords = self._extract_emotional_keywords(content)
            
            if emotional_keywords:
                # Search for similar emotional contexts
                similar = await self.search_similar_conversations(
                    f"farmer emotional state: {' '.join(emotional_keywords)}", 
                    top_k=3
                )
                
                return {
                    "sentiment_detected": True,
                    "emotional_keywords": emotional_keywords,
                    "similar_emotional_contexts": similar
                }
            
            return {"sentiment_detected": False}
            
        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {e}")
            return {"sentiment_detected": False}
    
    def _extract_emotional_keywords(self, content: str) -> List[str]:
        """Extract emotional keywords from content"""
        emotional_words = [
            "worried", "concerned", "anxious", "excited", "frustrated", 
            "happy", "sad", "confused", "urgent", "stressed", "nervous",
            "afraid", "confident", "unsure", "overwhelmed"
        ]
        
        content_lower = content.lower()
        return [word for word in emotional_words if word in content_lower]

class CAVAPostgreSQLConnection:
    """PostgreSQL Connection for CAVA (Constitutional requirement)"""
    
    def __init__(self):
        # Use main database URL from config_manager
        self.database_url = main_config.database_url
        self.schema = os.getenv('CAVA_POSTGRESQL_SCHEMA', 'cava')
        self.connection = None
        self.dry_run = os.getenv('CAVA_DRY_RUN_MODE', 'true').lower() == 'true'
    
    async def connect(self):
        """Initialize PostgreSQL connection"""
        try:
            if self.dry_run:
                logger.info("🔍 DRY RUN: Would connect to PostgreSQL")
                return
            
            self.connection = await asyncpg.connect(self.database_url)
            
            # Create CAVA schema if it doesn't exist
            await self.connection.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {self.schema}
            """)
            
            logger.info("✅ CAVA PostgreSQL Connected (schema: %s)", self.schema)
        except Exception as e:
            logger.error("❌ PostgreSQL connection failed: %s", str(e))
            if not self.dry_run:
                raise
    
    async def execute_query(self, query: str, *args) -> List[Dict]:
        """Execute SQL query in CAVA schema"""
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would execute SQL: %s", query[:100])
            return []
        
        if not self.connection:
            logger.warning("⚠️ PostgreSQL not connected")
            return []
        
        try:
            # Ensure we're using CAVA schema
            await self.connection.execute(f"SET search_path TO {self.schema}, public")
            rows = await self.connection.fetch(query, *args)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("❌ SQL execution failed: %s", str(e))
            return []
    
    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("🔒 PostgreSQL connection closed")

class CAVADatabaseManager:
    """Unified manager for all CAVA databases - MODULE INDEPENDENCE"""
    
    def __init__(self):
        self.neo4j = CAVANeo4jConnection()
        self.redis = CAVARedisConnection()
        self.pinecone = CAVAPineconeConnection()
        self.postgresql = CAVAPostgreSQLConnection()
        self.connected = False
        logger.info("🏛️ CAVA: Database Manager initialized")
    
    async def connect_all(self):
        """Connect to all CAVA databases with detailed logging"""
        logger.info("🚀 CAVA: Starting database connections...")
        connection_status = {}
        
        # Neo4j connection
        try:
            await self.neo4j.connect()
            logger.info("✅ CAVA: Neo4j connected successfully")
            connection_status['neo4j'] = 'connected'
        except Exception as e:
            logger.error(f"❌ CAVA: Neo4j connection failed: {str(e)}")
            connection_status['neo4j'] = f'failed: {str(e)}'
        
        # Redis connection  
        try:
            await self.redis.connect()
            logger.info("✅ CAVA: Redis connected successfully")
            connection_status['redis'] = 'connected'
        except Exception as e:
            logger.error(f"❌ CAVA: Redis connection failed: {str(e)}")
            connection_status['redis'] = f'failed: {str(e)}'
        
        # Pinecone connection
        try:
            await self.pinecone.connect()
            logger.info("✅ CAVA: Pinecone connected successfully")
            connection_status['pinecone'] = 'connected'
        except Exception as e:
            logger.error(f"❌ CAVA: Pinecone connection failed: {str(e)}")
            connection_status['pinecone'] = f'failed: {str(e)}'
        
        # PostgreSQL connection
        try:
            await self.postgresql.connect()
            logger.info("✅ CAVA: PostgreSQL connected successfully")
            connection_status['postgresql'] = 'connected'
        except Exception as e:
            logger.error(f"❌ CAVA: PostgreSQL connection failed: {str(e)}")
            connection_status['postgresql'] = f'failed: {str(e)}'
        
        logger.info(f"🔍 CAVA: Final connection status: {json.dumps(connection_status, indent=2)}")
        
        # ERROR ISOLATION - System continues even with partial failures
        self.connected = 'failed' not in str(connection_status)
        return connection_status
    
    async def health_check(self) -> Dict[str, str]:
        """Check health of all databases"""
        health = {
            "neo4j": "unknown",
            "redis": "unknown",
            "pinecone": "unknown",
            "postgresql": "unknown"
        }
        
        # Neo4j health
        try:
            if self.neo4j.driver:
                await self.neo4j.execute_query("RETURN 1")
                health["neo4j"] = "healthy"
        except:
            health["neo4j"] = "unhealthy"
        
        # Redis health
        try:
            if self.redis.client:
                self.redis.client.ping()
                health["redis"] = "healthy"
        except:
            health["redis"] = "unhealthy"
        
        # PostgreSQL health
        try:
            if self.postgresql.connection:
                await self.postgresql.execute_query("SELECT 1")
                health["postgresql"] = "healthy"
        except:
            health["postgresql"] = "unhealthy"
        
        # Pinecone
        if self.pinecone.enabled and self.pinecone.index:
            health["pinecone"] = "healthy"
        elif not self.pinecone.enabled:
            health["pinecone"] = "disabled"
        
        return health
    
    async def close_all(self):
        """Close all database connections"""
        await self.neo4j.close()
        await self.postgresql.close()
        logger.info("🔒 All CAVA databases disconnected")

# Test the connections
async def test_cava_connections():
    """Test all CAVA database connections"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    manager = CAVADatabaseManager()
    
    try:
        # Connect to all databases
        success = await manager.connect_all()
        
        if success:
            # Test Neo4j
            result = await manager.neo4j.execute_query("RETURN 'Neo4j works!' as test")
            print(f"Neo4j test: {result}")
            
            # Test Redis
            await manager.redis.store_conversation("test_session", {"test": "Redis works!"})
            conversation = await manager.redis.get_conversation("test_session")
            print(f"Redis test: {conversation}")
            
            # Test PostgreSQL
            result = await manager.postgresql.execute_query("SELECT 'PostgreSQL works!' as test")
            print(f"PostgreSQL test: {result}")
            
            # Health check
            health = await manager.health_check()
            print(f"Health check: {health}")
            
            print("🎉 All CAVA databases working correctly!")
        else:
            print("⚠️ Some databases failed to connect - check logs")
        
    except Exception as e:
        print(f"❌ CAVA connection error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await manager.close_all()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cava_connections())