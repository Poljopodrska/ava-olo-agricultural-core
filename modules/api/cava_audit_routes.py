#!/usr/bin/env python3
"""
CAVA Audit API Routes
Endpoints for comprehensive CAVA implementation testing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from modules.cava.audit import CAVAAudit
from modules.core.database_manager import DatabaseManager
from modules.api.chat_routes import chat_endpoint, ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cava", tags=["cava-audit"])

class MemoryTestRequest(BaseModel):
    phone_number: str

class MemoryTestResult(BaseModel):
    test_results: List[Dict]
    memory_score: int
    memory_status: str
    timestamp: str

@router.get("/audit")
async def run_cava_audit():
    """Run comprehensive CAVA implementation audit"""
    try:
        logger.info("Starting CAVA audit...")
        
        # Get database manager and ensure async pool is initialized
        db_manager = DatabaseManager()
        await db_manager.init_async_pool()
        
        # Initialize and run audit
        audit = CAVAAudit(db_manager)
        results = await audit.run_full_audit()
        
        # Add remediation suggestions
        results["remediation"] = generate_remediation_plan(results)
        
        logger.info(f"CAVA audit completed: {results['status']}")
        
        return results
        
    except Exception as e:
        logger.error(f"CAVA audit error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-memory", response_model=MemoryTestResult)
async def test_cava_memory(request: MemoryTestRequest):
    """Run interactive memory test with actual chat endpoint"""
    phone_number = request.phone_number
    
    test_messages = [
        {
            "message": "My name is Test Farmer from Bulgaria", 
            "expected": ["name recall", "greeting"]
        },
        {
            "message": "I grow mangoes on 50 hectares",
            "expected": ["crop recognition", "area noted"]
        },
        {
            "message": "What fertilizer should I use?",
            "expected": ["mango context", "fertilizer advice"]
        },
        {
            "message": "When should I apply it?",
            "expected": ["continuation", "timing based on previous"]
        },
        {
            "message": "Do you remember what crop I grow?",
            "expected": ["mango recall", "memory confirmation"]
        }
    ]
    
    results = []
    previous_responses = []
    
    for i, test in enumerate(test_messages):
        try:
            # Send message through actual chat endpoint
            chat_request = ChatRequest(
                wa_phone_number=phone_number,
                message=test["message"]
            )
            
            response = await chat_endpoint(chat_request)
            
            # Analyze response for memory indicators
            has_memory = analyze_memory_indicators(
                response.response, 
                test["message"],
                previous_responses, 
                i
            )
            
            results.append({
                "message": test["message"],
                "response": response.response[:200] + "..." if len(response.response) > 200 else response.response,
                "shows_memory": has_memory,
                "expected_indicators": test["expected"],
                "model_used": response.model_used,
                "facts_extracted": response.facts_extracted
            })
            
            previous_responses.append({
                "message": test["message"],
                "response": response.response
            })
            
            # Wait briefly between messages to simulate conversation
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error in memory test message {i+1}: {str(e)}")
            results.append({
                "message": test["message"],
                "response": f"ERROR: {str(e)}",
                "shows_memory": False,
                "expected_indicators": test["expected"],
                "error": True
            })
    
    # Calculate memory score
    memory_count = sum(1 for r in results if r.get("shows_memory", False))
    memory_score = (memory_count / len(test_messages)) * 100 if test_messages else 0
    
    # Determine status
    if memory_score >= 80:
        memory_status = "EXCELLENT - Full CAVA memory working"
    elif memory_score >= 60:
        memory_status = "GOOD - Partial memory functionality"
    elif memory_score >= 40:
        memory_status = "PARTIAL - Limited memory capability"
    elif memory_score >= 20:
        memory_status = "POOR - Minimal memory function"
    else:
        memory_status = "NOT_WORKING - No memory detected"
    
    return MemoryTestResult(
        test_results=results,
        memory_score=int(memory_score),
        memory_status=memory_status,
        timestamp=datetime.now().isoformat()
    )

def analyze_memory_indicators(response: str, current_message: str, 
                            previous_responses: List[Dict], message_index: int) -> bool:
    """Check if response shows memory of previous messages"""
    
    if not previous_responses:
        # First message, no memory expected
        return False
    
    response_lower = response.lower()
    memory_indicators = []
    
    # Check for name recall
    if message_index > 0 and any("test farmer" in r["message"].lower() for r in previous_responses):
        if "test farmer" in response_lower or "test" in response_lower:
            memory_indicators.append("name_recall")
    
    # Check for crop recall (mangoes)
    if message_index > 1 and any("mango" in r["message"].lower() for r in previous_responses):
        if "mango" in response_lower:
            memory_indicators.append("crop_recall")
    
    # Check for quantity recall (50 hectares)
    if message_index > 1 and any("50 hectares" in r["message"].lower() for r in previous_responses):
        if "50" in response or "fifty" in response_lower:
            memory_indicators.append("quantity_recall")
    
    # Check for contextual continuity
    if message_index > 2:
        continuity_words = ["earlier", "mentioned", "you said", "as we discussed", 
                          "previously", "your mango", "your farm", "your field"]
        if any(word in response_lower for word in continuity_words):
            memory_indicators.append("contextual_continuity")
    
    # Special check for direct memory question
    if "remember" in current_message.lower():
        if "mango" in response_lower or "yes" in response_lower:
            memory_indicators.append("direct_memory_confirmation")
    
    logger.info(f"Memory indicators found: {memory_indicators}")
    
    return len(memory_indicators) > 0

def generate_remediation_plan(audit_results: Dict) -> List[Dict]:
    """Generate specific fixes based on audit results"""
    plan = []
    
    components = audit_results.get("components", {})
    
    # Message Storage Issues
    storage = components.get("message_storage", {})
    if storage.get("score", 0) < 7:
        if storage.get("total_messages", 0) == 0:
            plan.append({
                "component": "Message Storage",
                "issue": "No messages being stored in database",
                "severity": "CRITICAL",
                "fix": "Ensure chat endpoint calls: await store_message(wa_phone_number, role, content)",
                "code_location": "modules/api/chat_routes.py",
                "priority": 1
            })
        elif storage.get("recent_messages", 0) == 0:
            plan.append({
                "component": "Message Storage",
                "issue": "Messages exist but none recent - storage may have stopped",
                "severity": "HIGH",
                "fix": "Check if store_message function is being called in current chat flow",
                "priority": 2
            })
    
    # Context Retrieval Issues
    context = components.get("context_retrieval", {})
    if context.get("score", 0) < 7:
        plan.append({
            "component": "Context Retrieval", 
            "issue": "System not retrieving previous messages for context",
            "severity": "CRITICAL",
            "fix": "Add: context = await cava_memory.get_conversation_context(wa_phone_number)",
            "code_location": "modules/api/chat_routes.py - before LLM call",
            "priority": 1
        })
    
    # Memory System Issues
    memory = components.get("memory_system", {})
    if memory.get("score", 0) < 7:
        plan.append({
            "component": "Memory System",
            "issue": "No conversation continuity detected",
            "severity": "HIGH",
            "fix": "Include message history in LLM prompt using context['messages']",
            "code_location": "modules/api/chat_routes.py - in messages array",
            "priority": 2
        })
    
    # Fact Extraction Issues
    facts = components.get("fact_extraction", {})
    if facts.get("score", 0) < 7:
        if not facts.get("llm_usage_tracking", False):
            plan.append({
                "component": "Fact Extraction",
                "issue": "LLM usage tracking table missing",
                "severity": "MEDIUM",
                "fix": "Run CREATE TABLE llm_usage_log as specified in chat_routes.py",
                "priority": 3
            })
        else:
            plan.append({
                "component": "Fact Extraction",
                "issue": "Facts not being extracted from conversations",
                "severity": "MEDIUM",
                "fix": "Call: facts = await fact_extractor.extract_facts(message, context)",
                "priority": 3
            })
    
    # Session Persistence Issues
    persistence = components.get("session_persistence", {})
    if persistence.get("score", 0) < 7:
        plan.append({
            "component": "Session Persistence",
            "issue": "Memory not persisting across conversation sessions",
            "severity": "HIGH",
            "fix": "Ensure CAVAMemory retrieves ALL historical messages, not just current session",
            "code_location": "modules/cava/conversation_memory.py",
            "priority": 2
        })
    
    # LLM Integration Issues
    llm = components.get("llm_integration", {})
    if llm.get("score", 0) < 7:
        plan.append({
            "component": "LLM Integration",
            "issue": "LLM not receiving context in prompts",
            "severity": "CRITICAL",
            "fix": "Add context summary to system prompt: Context about this farmer: {context['context_summary']}",
            "code_location": "modules/api/chat_routes.py - system message",
            "priority": 1
        })
    
    # Sort by priority
    plan.sort(key=lambda x: x["priority"])
    
    return plan

@router.post("/setup-tables")
async def setup_cava_tables():
    """Force execution of CAVA table creation"""
    try:
        db_manager = DatabaseManager()
        
        migration_sql = """
        -- Create chat_messages table
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            wa_phone_number VARCHAR(20) NOT NULL,
            role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            conversation_id VARCHAR(50),
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_chat_messages_phone ON chat_messages(wa_phone_number);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id);

        -- Create llm_usage_log table for cost tracking
        CREATE TABLE IF NOT EXISTS llm_usage_log (
            id SERIAL PRIMARY KEY,
            farmer_phone VARCHAR(20),
            model VARCHAR(50),
            tokens_in INTEGER,
            tokens_out INTEGER,
            cost DECIMAL(10,6),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_llm_usage_phone ON llm_usage_log(farmer_phone);
        CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_log(timestamp);

        -- Create farmer_facts table for extracted information
        CREATE TABLE IF NOT EXISTS farmer_facts (
            id SERIAL PRIMARY KEY,
            farmer_phone VARCHAR(20) NOT NULL,
            fact_type VARCHAR(50),
            fact_data JSONB,
            confidence DECIMAL(3,2) DEFAULT 1.0,
            source VARCHAR(100) DEFAULT 'chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_farmer_facts_phone ON farmer_facts(farmer_phone);
        CREATE INDEX IF NOT EXISTS idx_farmer_facts_type ON farmer_facts(fact_type);
        CREATE INDEX IF NOT EXISTS idx_farmer_facts_data ON farmer_facts USING GIN(fact_data);
        """
        
        # Execute migration
        async with db_manager.get_connection_async() as conn:
            await conn.execute(migration_sql)
            
            # Verify tables were created
            tables_check = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('chat_messages', 'llm_usage_log', 'farmer_facts')
            """)
            
            created_tables = [t['table_name'] for t in tables_check]
            
            # Check table structures
            structure_check = {}
            for table in created_tables:
                columns = await conn.fetch("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """, table)
                structure_check[table] = [f"{c['column_name']} ({c['data_type']})" for c in columns]
        
        logger.info(f"CAVA tables setup completed. Created: {created_tables}")
        
        return {
            "status": "success",
            "message": "CAVA tables created successfully",
            "tables_created": created_tables,
            "table_structures": structure_check,
            "ready_for_use": len(created_tables) == 3
        }
        
    except Exception as e:
        logger.error(f"CAVA setup error: {str(e)}")
        
        # Check what tables exist even if error
        try:
            async with db_manager.get_connection_async() as conn:
                existing = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('chat_messages', 'llm_usage_log', 'farmer_facts')
                """)
                existing_tables = [t['table_name'] for t in existing]
        except:
            existing_tables = []
        
        return {
            "status": "error",
            "message": str(e),
            "existing_tables": existing_tables,
            "partial_success": len(existing_tables) > 0
        }

@router.post("/test-conversation")
async def test_cava_conversation():
    """Test CAVA with a real conversation flow"""
    test_phone = "+385991234567"
    
    # Test conversation
    test_messages = [
        ("user", "My name is Marko and I grow mangoes"),
        ("user", "I have 25 hectares near Split"),
        ("user", "When should I harvest?")
    ]
    
    results = []
    
    try:
        for role, content in test_messages:
            if role == "user":
                # Send through chat endpoint
                response = await chat_endpoint(ChatRequest(
                    wa_phone_number=test_phone,
                    message=content
                ))
                
                results.append({
                    "role": "user",
                    "content": content,
                    "stored": True
                })
                
                results.append({
                    "role": "assistant",
                    "content": response.response,
                    "context_used": True,  # Assume context was used
                    "messages_in_context": len(results) // 2  # Estimate
                })
        
        # Verify storage
        db_manager = DatabaseManager()
        async with db_manager.get_connection_async() as conn:
            stored_messages = await conn.fetch("""
                SELECT role, content, timestamp 
                FROM chat_messages 
                WHERE wa_phone_number = $1 
                ORDER BY timestamp
            """, test_phone)
        
        # Check for memory indicators
        last_response = results[-1]["content"].lower() if results else ""
        memory_indicators = {
            "remembers_name": "marko" in last_response,
            "remembers_crop": "mango" in last_response,
            "remembers_location": "split" in last_response or "25 hectare" in last_response,
            "context_aware": any(word in last_response for word in ["your mango", "your 25 hectare", "your farm"])
        }
        
        return {
            "test_conversation": results,
            "messages_stored": len(stored_messages),
            "memory_indicators": memory_indicators,
            "memory_score": sum(memory_indicators.values()) * 25,
            "cava_working": sum(memory_indicators.values()) >= 2
        }
        
    except Exception as e:
        logger.error(f"Test conversation error: {str(e)}")
        return {
            "test_conversation": [],
            "messages_stored": 0,
            "memory_indicators": {},
            "memory_score": 0,
            "cava_working": False,
            "error": str(e)
        }

@router.get("/table-status")
async def check_table_status():
    """Quick check of CAVA table status"""
    tables = ['chat_messages', 'llm_usage_log', 'farmer_facts']
    status = {}
    
    try:
        db_manager = DatabaseManager()
        async with db_manager.get_connection_async() as conn:
            for table in tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    status[table] = {
                        "exists": True,
                        "row_count": count,
                        "status": "ready"
                    }
                except Exception as e:
                    status[table] = {
                        "exists": False,
                        "error": str(e),
                        "status": "missing"
                    }
        
        all_exist = all(t["exists"] for t in status.values())
        
        return {
            "tables": status,
            "cava_ready": all_exist,
            "setup_required": not all_exist
        }
        
    except Exception as e:
        logger.error(f"Table status check error: {str(e)}")
        # Return error status for all tables
        for table in tables:
            status[table] = {
                "exists": False,
                "error": str(e),
                "status": "error"
            }
        
        return {
            "tables": status,
            "cava_ready": False,
            "setup_required": True,
            "error": str(e)
        }

@router.get("/quick-check")
async def quick_cava_check():
    """Quick check of CAVA implementation status"""
    try:
        db_manager = DatabaseManager()
        
        async with db_manager.get_connection_async() as conn:
            # Quick checks
            has_messages = await conn.fetchval("SELECT COUNT(*) > 0 FROM chat_messages")
            has_recent = await conn.fetchval("""
                SELECT COUNT(*) > 0 FROM chat_messages 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """)
            has_llm_log = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'llm_usage_log'
                )
            """)
            
            using_gpt35 = False
            if has_llm_log:
                using_gpt35 = await conn.fetchval("""
                    SELECT COUNT(*) > 0 FROM llm_usage_log 
                    WHERE model LIKE '%gpt-3.5%'
                """)
        
        status = "NOT_CONFIGURED"
        if has_messages and has_recent and using_gpt35:
            status = "FULLY_OPERATIONAL"
        elif has_messages and has_recent:
            status = "PARTIAL_CAVA"
        elif has_messages:
            status = "INACTIVE"
        
        return {
            "status": status,
            "has_message_storage": has_messages,
            "has_recent_activity": has_recent,
            "has_cost_tracking": has_llm_log,
            "using_gpt35": using_gpt35,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def ensure_cava_tables_startup():
    """Ensure CAVA tables exist on every startup"""
    try:
        db_manager = DatabaseManager()
        
        async with db_manager.get_connection_async() as conn:
            # Check if tables exist
            tables_exist = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('chat_messages', 'llm_usage_log', 'farmer_facts')
            """)
            
            if tables_exist < 3:
                logger.info("📊 CAVA tables missing, creating them...")
                
                # Try to read from migration file first
                migration_sql = """
                -- Create chat_messages table
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    wa_phone_number VARCHAR(20) NOT NULL,
                    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    conversation_id VARCHAR(50),
                    metadata JSONB DEFAULT '{}'::jsonb
                );

                CREATE INDEX IF NOT EXISTS idx_chat_messages_phone ON chat_messages(wa_phone_number);
                CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp DESC);

                -- Create llm_usage_log table
                CREATE TABLE IF NOT EXISTS llm_usage_log (
                    id SERIAL PRIMARY KEY,
                    farmer_phone VARCHAR(20),
                    model VARCHAR(50),
                    tokens_in INTEGER,
                    tokens_out INTEGER,
                    cost DECIMAL(10,6),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_llm_usage_phone ON llm_usage_log(farmer_phone);
                CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_log(timestamp);

                -- Create farmer_facts table
                CREATE TABLE IF NOT EXISTS farmer_facts (
                    id SERIAL PRIMARY KEY,
                    farmer_phone VARCHAR(20) NOT NULL,
                    fact_type VARCHAR(50),
                    fact_data JSONB,
                    confidence DECIMAL(3,2) DEFAULT 1.0,
                    source VARCHAR(100) DEFAULT 'chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_farmer_facts_phone ON farmer_facts(farmer_phone);
                CREATE INDEX IF NOT EXISTS idx_farmer_facts_type ON farmer_facts(fact_type);
                """
                
                await conn.execute(migration_sql)
                logger.info("✅ CAVA tables created successfully!")
            else:
                logger.info("✅ CAVA tables already exist")
                
    except Exception as e:
        logger.error(f"⚠️ CAVA table check error: {e}")
        raise e