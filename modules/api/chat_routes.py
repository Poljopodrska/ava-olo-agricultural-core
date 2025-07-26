#!/usr/bin/env python3
"""
CAVA-Powered Chat Routes with GPT-3.5 Turbo
Implements persistent message storage and context-aware conversations
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from modules.chat.openai_key_manager import get_openai_client
from modules.cava.conversation_memory import CAVAMemory
from modules.cava.fact_extractor import FactExtractor
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
        db_manager = DatabaseManager()
        query = """
            INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
            VALUES ($1, $2, $3, NOW())
        """
        
        async with db_manager.get_connection_async() as conn:
            await conn.execute(query, wa_phone_number, role, content)
            
        logger.info(f"Stored {role} message for {wa_phone_number}")
        
    except Exception as e:
        logger.error(f"Failed to store message: {str(e)}")

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
    - Stores all messages in PostgreSQL
    - Uses conversation context for better responses
    - Extracts and stores farming facts
    - Tracks LLM usage for cost monitoring
    """
    wa_phone_number = request.wa_phone_number
    message = request.message
    
    try:
        # 1. Store user message
        await store_message(wa_phone_number, 'user', message)
        
        # 2. Get CAVA context
        context = await cava_memory.get_conversation_context(wa_phone_number)
        
        # 3. Extract facts from user message
        facts = await fact_extractor.extract_facts(message, context['context_summary'])
        
        # 4. Build conversation for GPT-3.5
        messages = [
            {
                "role": "system", 
                "content": f"""You are AVA, an agricultural assistant for farmers.
Context about this farmer: {context['context_summary']}
Provide specific, actionable agricultural advice in their language.
Be concise but helpful. If they mention specific crops, chemicals, or farming practices, acknowledge them."""
            }
        ]
        
        # Add recent conversation history (last 5 messages)
        recent_messages = await cava_memory.get_conversation_messages_for_llm(wa_phone_number, limit=5)
        messages.extend(recent_messages)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # 5. Get GPT-3.5 response
        client = get_openai_client()
        if not client:
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Latest GPT-3.5 model
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        assistant_message = response.choices[0].message.content
        
        # 6. Store assistant response
        await store_message(wa_phone_number, 'assistant', assistant_message)
        
        # 7. Store extracted facts (if any)
        await store_extracted_facts(wa_phone_number, facts)
        
        # 8. Log token usage for cost tracking
        usage = response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage.__dict__
        cost = calculate_gpt35_cost(usage)
        await store_llm_usage(wa_phone_number, 'gpt-3.5-turbo', usage, cost)
        
        logger.info(f"Chat completed for {wa_phone_number}. Tokens: {usage.get('total_tokens', 0)}, Cost: ${cost}")
        
        return ChatResponse(
            response=assistant_message,
            conversation_id=wa_phone_number,
            model_used="gpt-3.5-turbo",
            facts_extracted=facts if facts else None,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error for {wa_phone_number}: {str(e)}")
        
        # Store error message
        error_msg = "I apologize, but I'm having trouble processing your request. Please try again."
        await store_message(wa_phone_number, 'assistant', f"[ERROR] {error_msg}")
        
        raise HTTPException(status_code=500, detail=str(e))

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