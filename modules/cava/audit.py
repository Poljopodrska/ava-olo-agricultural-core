#!/usr/bin/env python3
"""
CAVA Implementation Audit & Diagnostic Tool
Comprehensive checks for memory system implementation status
"""
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CAVAAudit:
    """Comprehensive audit tool for CAVA implementation"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.test_phone = "+359887654321"  # Bulgarian test number
        
    async def run_full_audit(self) -> Dict:
        """Run comprehensive CAVA implementation audit"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "score": 0,
            "status": "NOT_IMPLEMENTED",
            "details": {},
            "test_phone": self.test_phone
        }
        
        # Component checks
        logger.info("Starting CAVA audit...")
        
        results["components"]["message_storage"] = await self.check_message_storage()
        results["components"]["context_retrieval"] = await self.check_context_retrieval()
        results["components"]["memory_system"] = await self.check_memory_system()
        results["components"]["fact_extraction"] = await self.check_fact_extraction()
        results["components"]["session_persistence"] = await self.check_session_persistence()
        results["components"]["llm_integration"] = await self.check_llm_integration()
        
        # Calculate score
        results["score"] = sum(c.get("score", 0) for c in results["components"].values())
        results["max_score"] = len(results["components"]) * 10
        results["percentage"] = (results["score"] / results["max_score"]) * 100 if results["max_score"] > 0 else 0
        
        # Determine status
        if results["score"] < 10:
            results["status"] = "NOT_IMPLEMENTED"
        elif results["score"] < 25:
            results["status"] = "PARTIAL_IMPLEMENTATION"
        elif results["score"] < 40:
            results["status"] = "BASIC_CAVA"
        else:
            results["status"] = "FULL_CAVA"
            
        logger.info(f"CAVA audit completed: {results['status']} ({results['score']}/{results['max_score']})")
        
        return results
    
    async def check_message_storage(self) -> Dict:
        """Check if messages are being stored in database"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                # Check table exists
                table_check = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'chat_messages'
                    )
                """)
                
                if not table_check:
                    return {
                        "score": 0,
                        "status": "FAILED",
                        "error": "chat_messages table does not exist"
                    }
                
                # Check message count
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM chat_messages"
                )
                
                # Check recent messages
                recent = await conn.fetchval("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                """)
                
                # Check structure
                columns = await conn.fetch("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'chat_messages'
                """)
                
                required_columns = ['wa_phone_number', 'role', 'content', 'timestamp']
                has_columns = all(
                    any(col['column_name'] == req for col in columns) 
                    for req in required_columns
                )
                
                score = 0
                if has_columns:
                    score += 3
                if count > 0:
                    score += 3
                if recent > 0:
                    score += 4
                    
                return {
                    "score": score,
                    "status": "PASS" if score >= 7 else "PARTIAL" if score >= 4 else "FAIL",
                    "total_messages": count,
                    "recent_messages": recent,
                    "has_required_columns": has_columns,
                    "columns": [col['column_name'] for col in columns]
                }
                
        except Exception as e:
            logger.error(f"Error checking message storage: {e}")
            return {
                "score": 0,
                "status": "ERROR",
                "error": str(e)
            }
    
    async def check_context_retrieval(self) -> Dict:
        """Check if system retrieves conversation context"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                # Look for conversations with multiple messages
                multi_message_convos = await conn.fetchval("""
                    SELECT COUNT(DISTINCT wa_phone_number) 
                    FROM chat_messages 
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY wa_phone_number 
                    HAVING COUNT(*) > 2
                """)
                
                # Check for conversations showing continuity
                context_patterns = await conn.fetch("""
                    WITH conversation_pairs AS (
                        SELECT 
                            wa_phone_number,
                            role,
                            content,
                            LAG(content) OVER (PARTITION BY wa_phone_number ORDER BY timestamp) as prev_content,
                            timestamp
                        FROM chat_messages
                        WHERE timestamp > NOW() - INTERVAL '7 days'
                    )
                    SELECT COUNT(*) as continuity_count
                    FROM conversation_pairs
                    WHERE role = 'assistant' 
                    AND prev_content IS NOT NULL
                    AND (
                        content LIKE '%mentioned%' OR
                        content LIKE '%earlier%' OR
                        content LIKE '%you said%' OR
                        content LIKE '%your%' OR
                        length(content) > 50
                    )
                """)
                
                continuity_count = context_patterns[0]['continuity_count'] if context_patterns else 0
                
                score = 0
                if multi_message_convos and multi_message_convos > 0:
                    score += 5
                if continuity_count > 0:
                    score += 5
                
                return {
                    "score": min(score, 10),
                    "status": "PASS" if score >= 7 else "PARTIAL" if score >= 4 else "FAIL",
                    "conversations_with_multiple_messages": multi_message_convos or 0,
                    "responses_showing_context": continuity_count
                }
                
        except Exception as e:
            logger.error(f"Error checking context retrieval: {e}")
            return {"score": 0, "status": "ERROR", "error": str(e)}
    
    async def check_memory_system(self) -> Dict:
        """Test if system remembers information across messages"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                # Check for conversation continuity patterns
                memory_test = await conn.fetch("""
                    WITH numbered_messages AS (
                        SELECT 
                            wa_phone_number,
                            content,
                            role,
                            timestamp,
                            ROW_NUMBER() OVER (PARTITION BY wa_phone_number ORDER BY timestamp) as msg_number
                        FROM chat_messages
                        WHERE timestamp > NOW() - INTERVAL '7 days'
                    ),
                    conversation_analysis AS (
                        SELECT 
                            m1.wa_phone_number,
                            m1.content as user_msg,
                            m2.content as assistant_response,
                            m1.msg_number
                        FROM numbered_messages m1
                        JOIN numbered_messages m2 ON 
                            m1.wa_phone_number = m2.wa_phone_number AND
                            m2.msg_number = m1.msg_number + 1 AND
                            m1.role = 'user' AND
                            m2.role = 'assistant'
                    )
                    SELECT 
                        wa_phone_number,
                        COUNT(*) as exchange_count,
                        MAX(msg_number) as max_exchange
                    FROM conversation_analysis
                    GROUP BY wa_phone_number
                    HAVING COUNT(*) > 1
                """)
                
                # Check if we have the CAVA memory module
                cava_memory_exists = await conn.fetchval("""
                    SELECT COUNT(*) > 0
                    FROM chat_messages
                    WHERE content LIKE '%context%' OR content LIKE '%remember%'
                """)
                
                has_memory = len(memory_test) > 0
                shows_cava = cava_memory_exists
                
                score = 0
                if has_memory:
                    score += 5
                if shows_cava:
                    score += 5
                
                return {
                    "score": score,
                    "status": "PASS" if score >= 7 else "PARTIAL" if score >= 4 else "FAIL",
                    "conversations_with_memory": len(memory_test),
                    "shows_context_awareness": shows_cava,
                    "sample_conversations": memory_test[:3] if memory_test else []
                }
                
        except Exception as e:
            logger.error(f"Error checking memory system: {e}")
            return {"score": 0, "status": "ERROR", "error": str(e)}
    
    async def check_fact_extraction(self) -> Dict:
        """Check if system extracts and stores facts"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                # Check for agricultural terms in messages
                ag_terms = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM chat_messages 
                    WHERE (
                        content ILIKE '%crop%' OR 
                        content ILIKE '%harvest%' OR 
                        content ILIKE '%plant%' OR
                        content ILIKE '%fertilizer%' OR
                        content ILIKE '%hectare%' OR
                        content ILIKE '%mango%' OR
                        content ILIKE '%corn%' OR
                        content ILIKE '%wheat%'
                    )
                    AND timestamp > NOW() - INTERVAL '7 days'
                """)
                
                # Check if llm_usage_log exists and has GPT-3.5 entries
                llm_usage_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'llm_usage_log'
                    )
                """)
                
                gpt35_usage = 0
                if llm_usage_exists:
                    gpt35_usage = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM llm_usage_log 
                        WHERE model LIKE '%gpt-3.5%'
                    """)
                
                score = 0
                if ag_terms > 0:
                    score += 5
                if gpt35_usage > 0:
                    score += 5
                
                return {
                    "score": min(score, 10),
                    "status": "PASS" if score >= 7 else "PARTIAL" if score >= 4 else "FAIL",
                    "agricultural_terms_found": ag_terms,
                    "llm_usage_tracking": llm_usage_exists,
                    "gpt35_usage_count": gpt35_usage
                }
                
        except Exception as e:
            logger.error(f"Error checking fact extraction: {e}")
            return {"score": 0, "status": "ERROR", "error": str(e)}
    
    async def check_session_persistence(self) -> Dict:
        """Check if memory persists across sessions"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                # Check for farmers with multiple conversation days
                persistent_sessions = await conn.fetch("""
                    WITH daily_conversations AS (
                        SELECT 
                            wa_phone_number,
                            DATE(timestamp) as conversation_date,
                            COUNT(*) as messages_that_day
                        FROM chat_messages
                        WHERE timestamp > NOW() - INTERVAL '30 days'
                        GROUP BY wa_phone_number, DATE(timestamp)
                    )
                    SELECT 
                        wa_phone_number,
                        COUNT(DISTINCT conversation_date) as conversation_days,
                        SUM(messages_that_day) as total_messages,
                        MAX(conversation_date) - MIN(conversation_date) as day_span
                    FROM daily_conversations
                    GROUP BY wa_phone_number
                    HAVING COUNT(DISTINCT conversation_date) > 1
                    ORDER BY conversation_days DESC
                    LIMIT 10
                """)
                
                # Check for time gaps showing session resumption
                session_gaps = await conn.fetchval("""
                    WITH time_gaps AS (
                        SELECT 
                            wa_phone_number,
                            timestamp,
                            LAG(timestamp) OVER (PARTITION BY wa_phone_number ORDER BY timestamp) as prev_timestamp
                        FROM chat_messages
                    )
                    SELECT COUNT(DISTINCT wa_phone_number)
                    FROM time_gaps
                    WHERE prev_timestamp IS NOT NULL
                    AND timestamp - prev_timestamp > INTERVAL '1 hour'
                """)
                
                score = min(len(persistent_sessions) * 2, 10)
                
                return {
                    "score": score,
                    "status": "PASS" if score >= 7 else "PARTIAL" if score >= 4 else "FAIL",
                    "farmers_with_persistent_sessions": len(persistent_sessions),
                    "farmers_resuming_after_gap": session_gaps or 0,
                    "examples": [{
                        "phone": p['wa_phone_number'],
                        "days": p['conversation_days'],
                        "messages": p['total_messages'],
                        "span_days": p['day_span'].days if p['day_span'] else 0
                    } for p in persistent_sessions[:3]]
                }
                
        except Exception as e:
            logger.error(f"Error checking session persistence: {e}")
            return {"score": 0, "status": "ERROR", "error": str(e)}
    
    async def check_llm_integration(self) -> Dict:
        """Check if LLM receives context in prompts"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                # Check for CAVA-style responses
                context_aware_responses = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM chat_messages 
                    WHERE role = 'assistant'
                    AND (
                        content LIKE '%you mentioned%' OR
                        content LIKE '%you said%' OR
                        content LIKE '%earlier%' OR
                        content LIKE '%last time%' OR
                        content LIKE '%previously%' OR
                        content LIKE '%As we discussed%'
                    )
                    AND timestamp > NOW() - INTERVAL '7 days'
                """)
                
                # Check for personalized responses
                personalized = await conn.fetchval("""
                    SELECT COUNT(DISTINCT wa_phone_number)
                    FROM chat_messages
                    WHERE role = 'assistant'
                    AND content ~ '\\y(your|Your)\\y.*\\y(farm|field|crop|mango|corn|wheat)\\y'
                    AND timestamp > NOW() - INTERVAL '7 days'
                """)
                
                score = 0
                if context_aware_responses > 0:
                    score += 5
                if personalized > 0:
                    score += 5
                
                return {
                    "score": score,
                    "status": "PASS" if score >= 7 else "PARTIAL" if score >= 4 else "FAIL",
                    "context_aware_responses": context_aware_responses,
                    "personalized_responses": personalized
                }
                
        except Exception as e:
            logger.error(f"Error checking LLM integration: {e}")
            return {"score": 0, "status": "ERROR", "error": str(e)}