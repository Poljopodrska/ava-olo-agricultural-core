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
        
        # Get database manager
        db_manager = DatabaseManager()
        
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