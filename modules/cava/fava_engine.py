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
        """Initialize FAVA with OpenAI connection and Welcome Package Manager"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.static_prompt = self._load_static_prompt()
        self.welcome_package_manager = None  # Will be initialized when needed
        
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
        Load farmer context using Welcome Package system (Redis-first, database fallback)
        OLD WAY: Multiple database queries for each message
        NEW WAY: Get from Redis welcome package (much faster)
        """
        
        logger.info(f"🎯 CONTEXT LOADING for farmer {farmer_id}")
        logger.info(f"  - Welcome package manager: {'AVAILABLE' if self.welcome_package_manager else 'NOT AVAILABLE'}")
        
        # Try to use welcome package manager if available
        if self.welcome_package_manager:
            try:
                logger.info(f"  - Attempting Redis fetch for farmer {farmer_id}")
                # Get welcome package from Redis (or auto-build if missing)
                welcome_package = self.welcome_package_manager.get_welcome_package(farmer_id)
                
                if welcome_package:
                    logger.info(f"  - Welcome package retrieved: {list(welcome_package.keys())}")
                    logger.info(f"  - Fields in package: {len(welcome_package.get('fields', []))}")
                    
                    # Log field details
                    for field in welcome_package.get('fields', [])[:3]:  # First 3 fields
                        logger.info(f"    - Field: {field}")
                    
                    # Transform welcome package into FAVA context format
                    context = self._transform_welcome_package_to_context(welcome_package)
                    logger.info(f"✅ SUCCESS: Loaded from Redis - {len(context.get('fields', []))} fields")
                    return context
                else:
                    logger.warning(f"  - Welcome package was empty/None")
            except Exception as e:
                logger.error(f"❌ REDIS FAILED for farmer {farmer_id}: {str(e)}", exc_info=True)
        
        # Fallback to original database loading if welcome package not available
        logger.info(f"Using database fallback for farmer {farmer_id}")
        context = {}
        
        # Load farmer details
        farmer_query = f"SELECT * FROM farmers WHERE id = {farmer_id}"
        farmer_result = await db_conn.fetchrow(farmer_query)
        context['farmer'] = dict(farmer_result) if farmer_result else {}
        logger.info(f"Farmer found: {farmer_result is not None}")
        
        # Load fields
        fields_query = f"SELECT * FROM fields WHERE farmer_id = {farmer_id}"
        logger.info(f"🔍 FAVA FIELDS QUERY: {fields_query}")
        fields_result = await db_conn.fetch(fields_query)
        context['fields'] = [dict(row) for row in fields_result]
        logger.info(f"📊 FAVA FIELDS RESULT: Found {len(context['fields'])} fields for farmer {farmer_id}")
        if context['fields']:
            for field in context['fields']:
                logger.info(f"  - Field: {field.get('field_name', 'unnamed')} ({field.get('area_ha', 0)} ha)")
        else:
            logger.warning(f"⚠️ NO FIELDS FOUND for farmer {farmer_id} - checking if farmer exists...")
            check_farmer = f"SELECT id, manager_name, manager_last_name FROM farmers WHERE id = {farmer_id}"
            farmer_check = await db_conn.fetchrow(check_farmer)
            if farmer_check:
                logger.info(f"✅ Farmer {farmer_id} EXISTS: {dict(farmer_check)}")
            else:
                logger.error(f"❌ Farmer {farmer_id} NOT FOUND in database!")
        
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
    
    def _transform_welcome_package_to_context(self, welcome_package: Dict) -> Dict:
        """
        Transform welcome package format into FAVA context format
        This is just data transformation, no LLM calls
        """
        context = {
            'farmer': welcome_package.get('farmer_info', {}),
            'fields': welcome_package.get('fields', []),
            'crops': welcome_package.get('all_crops', welcome_package.get('current_crops', [])),
            'recent_tasks': welcome_package.get('all_tasks', welcome_package.get('recent_tasks', [])),
            'recent_messages': [],  # Will be loaded separately if needed
            'total_hectares': welcome_package.get('total_hectares', 0),
            'total_fields': welcome_package.get('total_fields', 0),
            'context_source': 'welcome_package',
            'context_age': welcome_package.get('generated_at', '')
        }
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
- field_crops table: id (SERIAL), field_id (INT), crop_name (VARCHAR), variety (VARCHAR), start_date (DATE)
- field_activities table: id (SERIAL), field_id (INT), activity_type (VARCHAR), product_name (VARCHAR), activity_date (DATE), dose_amount (FLOAT), dose_unit (VARCHAR)
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
            # Handle both field names - crop_type (old) and crop (new)
            crop_name = crop.get('crop', crop.get('crop_type', crop.get('crop_name', '')))
            context_text += f"- Field {crop.get('field_name', 'unknown')}: {crop_name} - {crop.get('variety', '')} (planted {crop.get('planting_date', crop.get('start_date', 'unknown'))})\n"
        
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
                sql = parsed['sql_query'].replace(
                    '{farmer_id}', 
                    str(farmer_id)
                )
                
                # Clean up field names with quotes - if field_name has outer quotes, remove them
                # This handles cases like: field_name = '"Belouce"' -> 'Belouce'
                import re
                
                # Handle INSERT INTO fields with quoted field names
                # Example: VALUES (1, '"Belouce"', 3.2) -> VALUES (1, 'Belouce', 3.2)
                # Pattern matches: farmer_id, 'field_name_with_quotes', area_ha
                pattern = r"(VALUES\s*\([^,]+,\s*)'\"([^\"]+)\"'(\s*,)"
                sql = re.sub(pattern, r"\1'\2'\3", sql)
                
                # Also handle double single quotes
                pattern2 = r"(VALUES\s*\([^,]+,\s*)''([^']+)''(\s*,)"
                sql = re.sub(pattern2, r"\1'\2'\3", sql)
                
                # Log the SQL transformation for debugging
                if sql != parsed['sql_query'].replace('{farmer_id}', str(farmer_id)):
                    logger.info(f"FAVA SQL sanitized - removed quotes from field name")
                    logger.debug(f"Original: {parsed['sql_query']}")
                    logger.debug(f"Sanitized: {sql}")
                
                parsed['sql_query'] = sql
            
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
    
    def initialize_welcome_package_manager(self):
        """Initialize the Welcome Package Manager with Redis connection"""
        try:
            from ..core.redis_config import RedisConfig
            from ..core.welcome_package_manager import WelcomePackageManager
            from ..core.simple_db import execute_simple_query
            
            # Get Redis client
            redis_client = RedisConfig.get_redis_client()
            
            if redis_client:
                # Create a simple DB wrapper for the welcome package manager
                class SimpleDBOps:
                    def execute_query(self, query, params):
                        return execute_simple_query(query, params)
                
                db_ops = SimpleDBOps()
                self.welcome_package_manager = WelcomePackageManager(redis_client, db_ops)
                logger.info("Welcome Package Manager initialized with Redis")
            else:
                logger.warning("Redis not available - Welcome Package Manager disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize Welcome Package Manager: {e}")
            self.welcome_package_manager = None
    
    def refresh_welcome_package_after_data_change(self, farmer_id: int, fava_response: Dict):
        """
        Update welcome package after farmer data changes
        Called after successful database operations
        """
        if not self.welcome_package_manager:
            return
        
        try:
            action_type = fava_response.get('database_action')
            
            if action_type in ['INSERT', 'UPDATE', 'DELETE']:
                # Clear the package to force rebuild on next access
                self.welcome_package_manager.clear_package(farmer_id)
                logger.info(f"Welcome package cleared for farmer {farmer_id} after {action_type}")
                
                # Immediately rebuild to have fresh data ready
                self.welcome_package_manager.get_welcome_package(farmer_id)
                logger.info(f"Welcome package rebuilt for farmer {farmer_id}")
                
        except Exception as e:
            logger.error(f"Failed to refresh welcome package for farmer {farmer_id}: {e}")

# Singleton instance
_fava_engine = None

def get_fava_engine() -> FAVAEngine:
    """Get or create FAVA engine instance with Welcome Package support"""
    global _fava_engine
    if _fava_engine is None:
        _fava_engine = FAVAEngine()
        _fava_engine.initialize_welcome_package_manager()
        logger.info("FAVA Engine initialized - Pure LLM implementation with Redis Welcome Packages")
    return _fava_engine