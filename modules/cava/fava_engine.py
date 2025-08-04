#!/usr/bin/env python3
"""
FAVA (Farmer-Aware Virtual Assistant) Engine
Pure LLM-based farmer context intelligence - NO business logic
99% GPT-3.5-turbo implementation with static prompt + dynamic context
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

class FAVAEngine:
    """
    FAVA Engine - Pure LLM implementation for farmer-aware intelligence
    NO business logic - ALL decisions made by GPT-3.5-turbo
    """
    
    def __init__(self):
        """Initialize FAVA with OpenAI connection"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.static_prompt = self._load_static_prompt()
        
    def _load_static_prompt(self) -> str:
        """Load the static FAVA prompt template"""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'fava_prompt.txt'
        )
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"FAVA prompt template not found at {prompt_path}")
            # Fallback to embedded prompt if file not found
            return """You are FAVA (Farmer-Aware Virtual Assistant).
CORE CAPABILITIES:
1. Remember everything about THIS specific farmer
2. Generate SQL queries when farmer wants to save data
3. Ask for confirmation when storage intent unclear
4. Give advice specific to HIS farm, location, crops

RESPONSE FORMAT (JSON):
{
  "response": "Your farmer-specific answer",
  "database_action": "INSERT/UPDATE/DELETE/null",
  "sql_query": "Generated SQL or null",
  "needs_confirmation": true/false,
  "confirmation_question": "Question to ask farmer or null",
  "context_used": ["list of context used"]
}"""
    
    async def process_farmer_message(
        self, 
        farmer_id: int, 
        message: str,
        db_connection: Any,
        language_code: str = 'en'
    ) -> Dict:
        """
        Process farmer message with pure LLM intelligence
        NO business logic - just prompt + context + LLM
        """
        # Step 1: Load farmer context (pure database queries)
        farmer_context = await self._load_farmer_context(farmer_id, db_connection)
        
        # Step 2: Build dynamic prompt (string concatenation ONLY)
        full_prompt = self._build_full_prompt(farmer_context, message, language_code)
        
        # Step 3: Single LLM call (NO business logic)
        llm_response = await self._call_llm(full_prompt)
        
        # Step 4: Parse LLM response (JSON parsing ONLY)
        return self._parse_llm_response(llm_response, farmer_id)
    
    async def _load_farmer_context(self, farmer_id: int, db_conn: Any) -> Dict:
        """
        Load ALL farmer context from database
        Pure queries - NO conditional logic
        """
        context = {}
        
        # Load farmer details
        farmer_query = f"SELECT * FROM farmers WHERE id = {farmer_id}"
        farmer_result = await db_conn.fetchrow(farmer_query)
        context['farmer'] = dict(farmer_result) if farmer_result else {}
        
        # Load fields
        fields_query = f"SELECT * FROM fields WHERE farmer_id = {farmer_id}"
        fields_result = await db_conn.fetch(fields_query)
        context['fields'] = [dict(row) for row in fields_result]
        
        # Load crops
        if context['fields']:
            field_ids = ','.join(str(f['id']) for f in context['fields'])
            crops_query = f"SELECT * FROM field_crops WHERE field_id IN ({field_ids})"
            crops_result = await db_conn.fetch(crops_query)
            context['crops'] = [dict(row) for row in crops_result]
        else:
            context['crops'] = []
        
        # Load recent tasks
        tasks_query = f"""
            SELECT t.* FROM tasks t
            JOIN fields f ON t.field_id = f.id
            WHERE f.farmer_id = {farmer_id}
            ORDER BY t.date_performed DESC
            LIMIT 10
        """
        tasks_result = await db_conn.fetch(tasks_query)
        context['recent_tasks'] = [dict(row) for row in tasks_result]
        
        # Load recent chat messages
        messages_query = f"""
            SELECT role, content, timestamp 
            FROM chat_messages 
            WHERE session_id LIKE '%{farmer_id}%'
            OR session_id IN (
                SELECT DISTINCT wa_phone_number 
                FROM farmers 
                WHERE id = {farmer_id}
            )
            ORDER BY timestamp DESC 
            LIMIT 10
        """
        messages_result = await db_conn.fetch(messages_query)
        context['recent_messages'] = [dict(row) for row in messages_result]
        
        return context
    
    def _build_full_prompt(self, farmer_context: Dict, message: str, language_code: str = 'en') -> str:
        """
        Build complete prompt with static template + dynamic context
        Pure string concatenation - NO logic
        """
        # Get language name from language service
        from modules.core.language_service import get_language_service
        language_service = get_language_service()
        language_name = language_service.get_language_name(language_code)
        
        # Replace language placeholders in prompt
        prompt_with_language = self.static_prompt.replace(
            '{farmer_language}', language_code
        ).replace(
            '{language_name}', language_name
        )
        # Format farmer context as readable text
        context_text = f"""
DATABASE SCHEMA FOR SQL GENERATION:
- fields table: id (SERIAL), farmer_id (INT), field_name (VARCHAR), area_ha (FLOAT)
- field_crops table: id (SERIAL), field_id (INT), crop_type (VARCHAR), variety (VARCHAR), planting_date (DATE)
- tasks table: id (SERIAL), field_id (INT), task_type (VARCHAR), date_performed (DATE)

CURRENT FARMER CONTEXT:

Farmer Details:
- Name: {farmer_context['farmer'].get('manager_name', '')} {farmer_context['farmer'].get('manager_last_name', '')}
- Location: {farmer_context['farmer'].get('city', '')}, {farmer_context['farmer'].get('country', '')}
- Farm: {farmer_context['farmer'].get('farm_name', 'Unknown Farm')}
- Phone: {farmer_context['farmer'].get('wa_phone_number', '')}
- Farmer ID: {farmer_context['farmer'].get('id', 0)}

Fields ({len(farmer_context['fields'])} total):
"""
        
        for field in farmer_context['fields']:
            context_text += f"- {field.get('field_name', 'Unknown')} (ID: {field.get('id', '?')}): {field.get('area_ha', 0)} hectares\n"
        
        context_text += f"\nCrops ({len(farmer_context['crops'])} active):\n"
        for crop in farmer_context['crops']:
            context_text += f"- {crop.get('crop_type', '')}: {crop.get('variety', '')} (planted {crop.get('planting_date', 'unknown')})\n"
        
        context_text += f"\nRecent Tasks:\n"
        for task in farmer_context['recent_tasks'][:5]:
            context_text += f"- {task.get('task_type', '')}: {task.get('date_performed', '')}\n"
        
        context_text += f"\nRecent Conversation:\n"
        for msg in farmer_context['recent_messages'][:5]:
            role = "Farmer" if msg.get('role') == 'user' else "FAVA"
            context_text += f"- {role}: {msg.get('content', '')[:100]}...\n"
        
        # Combine everything
        full_prompt = f"""{prompt_with_language}

{context_text}

FARMER MESSAGE: {message}

Generate FAVA response in JSON format:"""
        
        return full_prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call OpenAI GPT-3.5-turbo - pure API call
        NO business logic
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are FAVA, a farmer-aware assistant. Always respond with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,  # Low temperature for consistency
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    return '{"response": "Error connecting to AI", "database_action": null}'
                    
        except Exception as e:
            logger.error(f"FAVA LLM call failed: {str(e)}")
            return '{"response": "Error processing request", "database_action": null}'
    
    def _parse_llm_response(self, llm_response: str, farmer_id: int) -> Dict:
        """
        Parse LLM JSON response - pure JSON parsing
        NO business logic or validation
        """
        try:
            # Parse JSON from LLM
            parsed = json.loads(llm_response)
            
            # Replace farmer_id placeholder in SQL if present
            if parsed.get('sql_query'):
                parsed['sql_query'] = parsed['sql_query'].replace(
                    '{farmer_id}', 
                    str(farmer_id)
                )
            
            # Ensure all expected fields exist
            result = {
                'response': parsed.get('response', 'I understand your message.'),
                'database_action': parsed.get('database_action'),
                'sql_query': parsed.get('sql_query'),
                'needs_confirmation': parsed.get('needs_confirmation', False),
                'confirmation_question': parsed.get('confirmation_question'),
                'context_used': parsed.get('context_used', []),
                'success': True
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FAVA response: {e}")
            logger.error(f"Raw response: {llm_response}")
            
            # Return a safe fallback
            return {
                'response': llm_response if len(llm_response) < 500 else "I'm processing your message.",
                'database_action': None,
                'sql_query': None,
                'needs_confirmation': False,
                'confirmation_question': None,
                'context_used': [],
                'success': False,
                'error': 'JSON parsing failed'
            }

# Singleton instance
_fava_engine = None

def get_fava_engine() -> FAVAEngine:
    """Get or create FAVA engine instance"""
    global _fava_engine
    if _fava_engine is None:
        _fava_engine = FAVAEngine()
        logger.info("FAVA Engine initialized - Pure LLM implementation active")
    return _fava_engine