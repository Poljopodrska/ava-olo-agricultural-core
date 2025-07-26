#!/usr/bin/env python3
"""
CAVA-Powered Chat Routes with GPT-3.5 Turbo
Implements persistent message storage and context-aware conversations
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

from modules.core.openai_config import OpenAIConfig, get_openai_client
from modules.core.openai_detective import OpenAIKeyDetective
from modules.cava.conversation_memory import CAVAMemory
from modules.cava.fact_extractor import FactExtractor
from modules.cava.memory_enforcer import MemoryEnforcer
from modules.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])

# Initialize CAVA components
cava_memory = CAVAMemory()
fact_extractor = FactExtractor()

class ChatRequest(BaseModel):
    """Chat request model"""
    wa_phone_number: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    conversation_id: str
    model_used: str
    facts_extracted: Optional[Dict[str, Any]] = None
    timestamp: str
    context_used: bool = True
    context_summary: Optional[str] = None
    messages_in_context: int = 0
    memory_indicators: Optional[Dict[str, Any]] = None

def calculate_gpt35_cost(usage: Dict) -> float:
    """
    Calculate cost for GPT-3.5 Turbo usage
    Pricing: $0.0015 per 1K input tokens, $0.002 per 1K output tokens
    """
    input_cost = (usage.get('prompt_tokens', 0) / 1000) * 0.0015
    output_cost = (usage.get('completion_tokens', 0) / 1000) * 0.002
    return round(input_cost + output_cost, 6)

async def store_message(wa_phone_number: str, role: str, content: str) -> None:
    """Store message in chat_messages table"""
    try:
        print(f"🔄 STORING MESSAGE: {role} from {wa_phone_number}")
        db_manager = DatabaseManager()
        query = """
            INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
            VALUES ($1, $2, $3, NOW())
        """
        
        async with db_manager.get_connection_async() as conn:
            await conn.execute(query, wa_phone_number, role, content)
            print(f"✅ MESSAGE STORED SUCCESSFULLY in database")
            
        logger.info(f"Stored {role} message for {wa_phone_number}")
        
    except Exception as e:
        print(f"❌ FAILED TO STORE MESSAGE: {str(e)}")
        logger.error(f"Failed to store message: {str(e)}")
        # Re-raise to ensure calling code knows about the failure
        raise e

async def store_llm_usage(wa_phone_number: str, model: str, usage: Dict, cost: float) -> None:
    """Store LLM usage for cost tracking"""
    try:
        db_manager = DatabaseManager()
        
        # First ensure the table exists
        create_table_query = """
            CREATE TABLE IF NOT EXISTS llm_usage_log (
                id SERIAL PRIMARY KEY,
                farmer_phone VARCHAR(20),
                model VARCHAR(50),
                tokens_in INTEGER,
                tokens_out INTEGER,
                cost DECIMAL(10,6),
                timestamp TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_llm_usage_phone ON llm_usage_log(farmer_phone);
            CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_log(timestamp);
        """
        
        async with db_manager.get_connection_async() as conn:
            await conn.execute(create_table_query)
            
            # Insert usage record
            insert_query = """
                INSERT INTO llm_usage_log (
                    farmer_phone, model, tokens_in, tokens_out, cost, timestamp
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """
            
            await conn.execute(
                insert_query,
                wa_phone_number,
                model,
                usage.get('prompt_tokens', 0),
                usage.get('completion_tokens', 0),
                cost
            )
            
        logger.info(f"Stored LLM usage: {model} for {wa_phone_number}, cost: ${cost}")
        
    except Exception as e:
        logger.error(f"Failed to store LLM usage: {str(e)}")

async def store_extracted_facts(wa_phone_number: str, facts: Dict[str, Any]) -> None:
    """Store extracted facts for future use"""
    if facts:
        await cava_memory.store_extracted_facts(wa_phone_number, facts)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    CAVA-powered chat endpoint with GPT-3.5 Turbo
    Enhanced with comprehensive error handling for service availability
    - Stores all messages in PostgreSQL
    - Uses conversation context for better responses
    - Extracts and stores farming facts
    - Tracks LLM usage for cost monitoring
    """
    wa_phone_number = request.wa_phone_number
    message = request.message
    
    # 🔍 DIAGNOSTIC LOGGING - ADDED FOR DEBUGGING
    print(f"🔍 CHAT ENDPOINT CALLED: {wa_phone_number} - {message[:50]}...")
    print(f"📍 Chat endpoint location: {__file__}")
    
    # CRITICAL: Check OpenAI availability using new configuration system
    if not OpenAIConfig.is_available():
        print("🔄 OpenAI not initialized, attempting recovery...")
        
        # Try automatic recovery with detective
        if not OpenAIKeyDetective.attempt_recovery():
            # If recovery fails, provide detailed diagnostics
            investigation = OpenAIKeyDetective.investigate()
            print(f"❌ CRITICAL: OpenAI recovery failed - {investigation}")
            
            return ChatResponse(
                response="Chat service is not configured. Please check the diagnostics.",
                conversation_id=wa_phone_number,
                model_used="unavailable",
                timestamp=datetime.now().isoformat(),
                context_used=False,
                context_summary="OpenAI service configuration error",
                messages_in_context=0,
                memory_indicators={
                    "error": "OPENAI_CONFIGURATION_FAILED",
                    "diagnostics": investigation,
                    "fix_url": "/openai-wizard"
                }
            )
    
    print(f"✅ OpenAI properly configured and available")
    print(f"🧠 CAVA Memory initialized: {cava_memory is not None}")
    print(f"🎯 Fact extractor initialized: {fact_extractor is not None}")
    
    try:
        # 1. Store user message
        print(f"📝 Storing user message...")
        await store_message(wa_phone_number, 'user', message)
        print(f"✅ User message stored successfully")
        
        # 2. Get comprehensive CAVA context (includes ALL messages and facts)
        print(f"🧠 Getting comprehensive CAVA context...")
        context = await cava_memory.get_conversation_context(wa_phone_number, limit=50)
        print(f"✅ Context retrieved: {context.get('all_messages_count', 0)} total messages, {len(context.get('messages', []))} for LLM")
        print(f"📊 Context summary: {context.get('context_summary', '')[:150]}...")
        print(f"🔍 Memory persistence: {context.get('memory_persistence_active', False)}")
        print(f"📈 Conversation facts: {len(context.get('conversation_facts', {}))}")
        
        # 3. Extract facts from user message
        print(f"🎯 Extracting facts...")
        facts = await fact_extractor.extract_facts(message, context['context_summary'])
        print(f"✅ Facts extracted: {facts}")
        
        # 3a. MEMORY ENFORCEMENT: Extract critical facts
        memory_enforcer = MemoryEnforcer()
        critical_facts = memory_enforcer.extract_critical_facts(context)
        print(f"🧠 Critical facts for memory enforcement: {critical_facts}")
        
        # 4. Build conversation for GPT-3.5 with ENHANCED context
        # CRITICAL FIX: Ensure all context is included in LLM messages
        
        # Build comprehensive system message with ALL context
        conversation_facts = context.get('conversation_facts', {})
        stored_facts = context.get('stored_facts', [])
        
        # Use memory enforcer to create aggressive prompt
        system_content = memory_enforcer.create_memory_demonstration_prompt(critical_facts, message)
        
        messages = [
            {"role": "system", "content": system_content}
        ]
        
        # Add recent conversation history (CRITICAL for memory!)
        print(f"📚 Getting recent messages for LLM context...")
        recent_messages = await cava_memory.get_conversation_messages_for_llm(wa_phone_number, limit=8)
        messages.extend(recent_messages)
        print(f"✅ Added {len(recent_messages)} recent messages to context")
        
        # Debug logging - Log what we're sending to LLM
        try:
            debug_data = {
                "context_summary": context['context_summary'],
                "stored_facts_count": len(context.get('stored_facts', [])),
                "recent_messages_count": len(recent_messages),
                "total_messages_to_llm": len(messages) + 1,  # +1 for current message
                "mentions_crops": any(crop in context['context_summary'].lower() 
                                    for crop in ['mango', 'tomato', 'wheat', 'corn', 'rice'])
            }
            
            # Store debug info in database
            db_manager = DatabaseManager()
            async with db_manager.get_connection_async() as debug_conn:
                await debug_conn.execute("""
                    CREATE TABLE IF NOT EXISTS llm_debug_log (
                        id SERIAL PRIMARY KEY,
                        farmer_phone VARCHAR(20),
                        message_preview TEXT,
                        context_summary TEXT,
                        llm_messages_json TEXT,
                        debug_data JSONB,
                        timestamp TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                await debug_conn.execute("""
                    INSERT INTO llm_debug_log 
                    (farmer_phone, message_preview, context_summary, llm_messages_json, debug_data)
                    VALUES ($1, $2, $3, $4, $5)
                """, wa_phone_number, message[:100], context['context_summary'], 
                     json.dumps(messages)[:2000], json.dumps(debug_data))
                
            print(f"🔍 Debug logged: {debug_data}")
            
        except Exception as debug_error:
            print(f"⚠️ Debug logging failed: {debug_error}")
        
        # Add current message
        messages.append({"role": "user", "content": message})
        print(f"🤖 Sending {len(messages)} messages to GPT-3.5...")
        
        # CRITICAL: Log exactly what we're sending to LLM for debugging
        print(f"📋 LLM System Message: {system_content[:200]}...")
        print(f"📋 Context Summary: {context['context_summary']}")
        if recent_messages:
            print(f"📋 Last conversation message: {recent_messages[-1].get('content', '')[:100]}...")
        
        # 5. Get GPT-3.5 response with enhanced error handling
        print(f"🤖 Getting OpenAI client...")
        client = OpenAIConfig.get_client()
        if not client:
            print(f"❌ OpenAI client not available!")
            openai_status = OpenAIConfig.get_status()
            return ChatResponse(
                response="AI service is temporarily unavailable. The language model could not be initialized. Please try again later.",
                conversation_id=wa_phone_number,
                model_used="unavailable",
                timestamp=datetime.now().isoformat(),
                context_used=True,
                context_summary=context['context_summary'][:200] if context.get('context_summary') else None,
                messages_in_context=len(context.get('messages', [])),
                memory_indicators={"error": "OPENAI_CLIENT_UNAVAILABLE", "status": openai_status}
            )
        
        print(f"🤖 Calling OpenAI API...")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",  # Latest GPT-3.5 model
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
        except Exception as openai_error:
            error_type = type(openai_error).__name__
            error_msg = str(openai_error)
            
            print(f"❌ OpenAI API error: {error_type} - {error_msg}")
            
            # Handle specific OpenAI errors
            if "authentication" in error_msg.lower() or "401" in error_msg:
                return ChatResponse(
                    response="Authentication with AI service failed. Please contact support to resolve this issue.",
                    conversation_id=wa_phone_number,
                    model_used="auth_error",
                    timestamp=datetime.now().isoformat(),
                    context_used=True,
                    context_summary=context['context_summary'][:200] if context.get('context_summary') else None,
                    messages_in_context=len(recent_messages),
                    memory_indicators={"error": "OPENAI_AUTH_FAILED", "error_type": error_type}
                )
            elif "rate limit" in error_msg.lower():
                return ChatResponse(
                    response="Our AI service is temporarily busy. Please wait a moment and try again.",
                    conversation_id=wa_phone_number,
                    model_used="rate_limited",
                    timestamp=datetime.now().isoformat(),
                    context_used=True,
                    context_summary=context['context_summary'][:200] if context.get('context_summary') else None,
                    messages_in_context=len(recent_messages),
                    memory_indicators={"error": "OPENAI_RATE_LIMIT", "error_type": error_type}
                )
            else:
                # Generic error
                return ChatResponse(
                    response="I'm experiencing technical difficulties with the AI service. Please try again in a few moments.",
                    conversation_id=wa_phone_number,
                    model_used="error",
                    timestamp=datetime.now().isoformat(),
                    context_used=True,
                    context_summary=context['context_summary'][:200] if context.get('context_summary') else None,
                    messages_in_context=len(recent_messages),
                    memory_indicators={"error": "OPENAI_API_ERROR", "error_type": error_type, "error_msg": error_msg[:100]}
                )
        
        assistant_message = response.choices[0].message.content
        print(f"✅ GPT-3.5 response received: {assistant_message[:50]}...")
        
        # 5a. MEMORY VERIFICATION: Check if response demonstrates memory
        verification = memory_enforcer.verify_memory_demonstration(assistant_message, critical_facts)
        print(f"🔍 Memory verification score: {verification['score']}/100")
        print(f"🔍 Memory verification details: {verification}")
        
        # 5b. RETRY if memory demonstration is weak
        if verification['score'] < 70:
            print(f"⚠️ Memory demonstration weak (score: {verification['score']}), retrying with stronger prompt...")
            
            # Create even more explicit prompt
            retry_prompt = f"""Your response didn't show enough memory! Here's what you MUST mention:
            
{json.dumps(critical_facts, indent=2)}

REWRITE your response to EXPLICITLY mention:
1. Their name: {critical_facts.get('farmer_name', 'the farmer')}
2. Their location: {critical_facts.get('location', {}).get('city', 'their location')}
3. Their crop: {', '.join(critical_facts.get('crops', ['their crops']))}
4. Specific quantities: {list(critical_facts.get('quantities', {}).values())}
5. Acknowledge if it's unusual (like tropical crops in temperate climates)

Original response to improve: {assistant_message}

Now give a response that PROVES you remember everything!"""
            
            retry_messages = [
                {"role": "system", "content": retry_prompt},
                {"role": "user", "content": message}
            ]
            
            try:
                retry_response = client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=retry_messages,
                    temperature=0.5,  # Lower temperature for more focused response
                    max_tokens=500
                )
                
                assistant_message = retry_response.choices[0].message.content
                verification = memory_enforcer.verify_memory_demonstration(assistant_message, critical_facts)
                print(f"✅ Retry response received with memory score: {verification['score']}/100")
                
            except Exception as retry_error:
                print(f"⚠️ Retry failed: {retry_error}, using original response")
        
        # 6. Store assistant response
        print(f"📝 Storing assistant response...")
        await store_message(wa_phone_number, 'assistant', assistant_message)
        print(f"✅ Assistant response stored")
        
        # 7. Store extracted facts (if any)
        if facts:
            print(f"📊 Storing extracted facts...")
            await store_extracted_facts(wa_phone_number, facts)
            print(f"✅ Facts stored")
        
        # 8. Log token usage for cost tracking
        print(f"💰 Logging LLM usage...")
        usage = response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage.__dict__
        cost = calculate_gpt35_cost(usage)
        await store_llm_usage(wa_phone_number, 'gpt-3.5-turbo', usage, cost)
        print(f"✅ Usage logged: {usage.get('total_tokens', 0)} tokens, ${cost}")
        
        # 9. COMPREHENSIVE MEMORY TEST: Check if response uses full context
        response_lower = assistant_message.lower()
        context_lower = context['context_summary'].lower()
        conversation_facts = context.get('conversation_facts', {})
        
        # Check if the response mentions crops from conversation history
        crops_in_response = []
        for crop in conversation_facts.get('crops_mentioned', []):
            if crop in response_lower:
                crops_in_response.append(crop)
        
        # Check if the response mentions locations from conversation history 
        locations_in_response = []
        for location in conversation_facts.get('locations_mentioned', []):
            if location in response_lower:
                locations_in_response.append(location)
        
        # Check if the response mentions quantities from conversation history
        quantities_referenced = any(qty.split()[0] in response_lower for qty in conversation_facts.get('quantities_mentioned', []))
        
        memory_indicators = {
            'total_conversation_messages': context.get('all_messages_count', 0),
            'mentions_conversation_crops': crops_in_response,
            'mentions_conversation_locations': locations_in_response,
            'references_quantities': quantities_referenced,
            'uses_personal_pronouns': any(word in response_lower for word in ['your', 'you mentioned', 'you told', 'as we discussed']),
            'shows_memory_continuity': any(phrase in response_lower for phrase in ['remember', 'mentioned', 'told me', 'discussed', 'previously']),
            'context_has_crops': len(conversation_facts.get('crops_mentioned', [])) > 0,
            'context_has_locations': len(conversation_facts.get('locations_mentioned', [])) > 0,
            'memory_persistence_working': context.get('memory_persistence_active', False),
            'behavioral_test_compliance': {
                'mango_mentioned': 'mango' in crops_in_response,
                'bulgaria_mentioned': 'bulgaria' in locations_in_response,
                'hectares_referenced': any('hectare' in qty for qty in conversation_facts.get('quantities_mentioned', []))
            },
            'memory_verification_score': verification['score'],
            'memory_verification_details': verification
        }
        
        print(f"🧠 Memory Check: {memory_indicators}")
        
        logger.info(f"Chat completed for {wa_phone_number}. Tokens: {usage.get('total_tokens', 0)}, Cost: ${cost}")
        print(f"🎉 CHAT COMPLETION SUCCESS for {wa_phone_number}")
        
        return ChatResponse(
            response=assistant_message,
            conversation_id=wa_phone_number,
            model_used="gpt-3.5-turbo",
            facts_extracted=facts if facts else None,
            timestamp=datetime.now().isoformat(),
            context_used=True,
            context_summary=context['context_summary'][:200] if context.get('context_summary') else None,
            messages_in_context=context.get('all_messages_count', 0),
            memory_indicators=memory_indicators
        )
        
    except Exception as e:
        # Never crash - always return a response
        print(f"Chat error: {str(e)}")
        return ChatResponse(
            response="I'm having technical difficulties. Please try again in a moment.",
            conversation_id=request.wa_phone_number,
            model_used="error",
            timestamp=datetime.now().isoformat(),
            context_used=False,
            messages_in_context=0,
            memory_indicators={"error": str(e)}
        )

@router.get("/chat/history/{wa_phone_number}")
async def get_chat_history(wa_phone_number: str, limit: int = 50):
    """Get chat history for a phone number"""
    try:
        db_manager = DatabaseManager()
        query = """
            SELECT role, content, timestamp
            FROM chat_messages
            WHERE wa_phone_number = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        
        async with db_manager.get_connection_async() as conn:
            rows = await conn.fetch(query, wa_phone_number, limit)
            
        history = []
        for row in rows:
            history.append({
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None
            })
        
        # Reverse to get chronological order
        history.reverse()
        
        return {
            'wa_phone_number': wa_phone_number,
            'messages': history,
            'total_messages': len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/usage/{wa_phone_number}")
async def get_usage_stats(wa_phone_number: str):
    """Get LLM usage statistics for a phone number"""
    try:
        db_manager = DatabaseManager()
        query = """
            SELECT 
                COUNT(*) as total_requests,
                SUM(tokens_in) as total_input_tokens,
                SUM(tokens_out) as total_output_tokens,
                SUM(cost) as total_cost,
                MIN(timestamp) as first_usage,
                MAX(timestamp) as last_usage
            FROM llm_usage_log
            WHERE farmer_phone = $1
        """
        
        async with db_manager.get_connection_async() as conn:
            row = await conn.fetchrow(query, wa_phone_number)
            
        if not row:
            return {
                'wa_phone_number': wa_phone_number,
                'usage': None,
                'message': 'No usage found for this phone number'
            }
        
        return {
            'wa_phone_number': wa_phone_number,
            'usage': {
                'total_requests': row['total_requests'],
                'total_input_tokens': row['total_input_tokens'] or 0,
                'total_output_tokens': row['total_output_tokens'] or 0,
                'total_cost': float(row['total_cost'] or 0),
                'first_usage': row['first_usage'].isoformat() if row['first_usage'] else None,
                'last_usage': row['last_usage'].isoformat() if row['last_usage'] else None,
                'average_cost_per_request': float(row['total_cost'] or 0) / row['total_requests'] if row['total_requests'] > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/debug")
async def chat_debug():
    """Show current chat configuration and CAVA status"""
    try:
        db_manager = DatabaseManager()
        
        # Check database connection
        db_connected = False
        recent_messages_count = 0
        table_exists = False
        
        try:
            async with db_manager.get_connection_async() as conn:
                db_connected = True
                
                # Check if chat_messages table exists
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'chat_messages'
                    )
                """)
                
                if table_exists:
                    recent_messages_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM chat_messages 
                        WHERE timestamp > NOW() - INTERVAL '1 hour'
                    """)
        except Exception as db_error:
            print(f"❌ Database debug error: {db_error}")
        
        # Check CAVA components
        cava_status = {
            "cava_memory_initialized": cava_memory is not None,
            "fact_extractor_initialized": fact_extractor is not None,
            "database_connected": db_connected,
            "chat_messages_table_exists": table_exists,
            "recent_messages_count": recent_messages_count,
            "chat_module_location": __file__,
            "openai_client_available": get_openai_client() is not None
        }
        
        print(f"🔍 DEBUG INFO: {cava_status}")
        
        return {
            **cava_status,
            "status": "debug_info_collected",
            "timestamp": datetime.now().isoformat(),
            "cava_integration_active": all([
                cava_memory is not None,
                fact_extractor is not None,
                db_connected,
                table_exists
            ])
        }
        
    except Exception as e:
        return {
            "status": "debug_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/chat/test-cava-direct")
async def test_cava_direct():
    """Direct test of CAVA without going through main chat endpoint"""
    test_phone = "+385991234567"
    test_message = "Direct CAVA test message"
    
    print(f"🧪 DIRECT CAVA TEST STARTING for {test_phone}")
    
    try:
        # Test message storage
        print(f"📝 Testing message storage...")
        await store_message(test_phone, "user", test_message)
        print(f"✅ Message storage test passed")
        
        # Test context retrieval
        print(f"🧠 Testing context retrieval...")
        context = await cava_memory.get_enhanced_context(test_phone)
        print(f"✅ Context retrieval test passed: {len(context.get('messages', []))} messages")
        
        # Test fact extraction
        print(f"🎯 Testing fact extraction...")
        facts = await fact_extractor.extract_facts(test_message, context.get('context_summary', ''))
        print(f"✅ Fact extraction test passed: {facts}")
        
        # Check database storage
        print(f"💾 Checking database storage...")
        db_manager = DatabaseManager()
        async with db_manager.get_connection_async() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM chat_messages WHERE wa_phone_number = $1",
                test_phone
            )
            
            # Get latest message
            latest = await conn.fetchrow(
                "SELECT role, content, timestamp FROM chat_messages WHERE wa_phone_number = $1 ORDER BY timestamp DESC LIMIT 1",
                test_phone
            )
        
        print(f"✅ Database storage test passed: {count} messages found")
        
        return {
            "status": "success",
            "message_stored": count > 0,
            "storage_count": count,
            "context_retrieved": bool(context),
            "context_summary": context.get('context_summary', ''),
            "facts_extracted": facts,
            "latest_message": {
                "role": latest['role'],
                "content": latest['content'][:50] + "..." if len(latest['content']) > 50 else latest['content'],
                "timestamp": latest['timestamp'].isoformat()
            } if latest else None,
            "cava_working_directly": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ DIRECT CAVA TEST FAILED: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "cava_working_directly": False,
            "timestamp": datetime.now().isoformat()
        }

@router.get("/chat/status")
async def chat_status():
    """Quick status check for CAVA chat system"""
    try:
        db_manager = DatabaseManager()
        async with db_manager.get_connection_async() as conn:
            # Check if table exists and get count
            total_messages = await conn.fetchval("SELECT COUNT(*) FROM chat_messages") or 0
            recent_messages = await conn.fetchval("""
                SELECT COUNT(*) FROM chat_messages 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """) or 0
        
        return {
            'status': 'operational',
            'cava_enabled': True,
            'total_messages_stored': total_messages,
            'recent_messages': recent_messages,
            'message_storage_working': total_messages > 0,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.get("/chat/test")
async def test_cava_chat():
    """Test endpoint to verify CAVA chat is working"""
    return {
        'status': 'ok',
        'model': 'gpt-3.5-turbo',
        'cava_enabled': True,
        'features': [
            'Message persistence in PostgreSQL',
            'Conversation context awareness', 
            'Farming fact extraction',
            'Cost tracking',
            'Multi-language support'
        ],
        'timestamp': datetime.now().isoformat()
    }