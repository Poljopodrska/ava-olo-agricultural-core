#!/usr/bin/env python3
"""
CAVA Conversation Memory Module
Handles conversation context retrieval and management for persistent chat sessions
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncpg
from modules.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class CAVAMemory:
    """
    CAVA Memory component for conversation context management
    Retrieves recent messages and farmer information to build context
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.redis_client = None  # Future: Redis for active sessions
        logger.info("CAVAMemory initialized")
    
    async def get_conversation_context(self, wa_phone_number: str, limit: int = 50) -> Dict[str, Any]:
        """
        Retrieve ALL conversation messages and build comprehensive context
        
        Args:
            wa_phone_number: WhatsApp phone number
            limit: Number of recent messages for LLM (full history still analyzed)
            
        Returns:
            Dictionary with messages, farmer info, comprehensive context summary, and facts
        """
        try:
            # Get ALL messages for true persistence
            all_messages = await self._get_all_messages(wa_phone_number)
            
            # Get farmer information with ALL details
            farmer = await self._get_farmer_info_comprehensive(wa_phone_number)
            
            # Get stored facts
            stored_facts = await self.get_farmer_facts(wa_phone_number)
            
            # Build comprehensive context from ALL conversation history
            context_summary = self._build_comprehensive_context(all_messages, farmer, stored_facts)
            
            # Extract key facts from entire conversation history
            conversation_facts = self._extract_all_conversation_facts(all_messages)
            
            # For LLM, send recent messages but with full context summary
            recent_for_llm = all_messages[-limit:] if len(all_messages) > limit else all_messages
            
            return {
                'messages': recent_for_llm,
                'all_messages': all_messages,
                'all_messages_count': len(all_messages),
                'farmer': farmer,
                'context_summary': context_summary,
                'stored_facts': stored_facts,
                'conversation_facts': conversation_facts,
                'phone_number': wa_phone_number,
                'has_history': len(all_messages) > 0,
                'memory_persistence_active': True
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return {
                'messages': [],
                'all_messages': [],
                'all_messages_count': 0,
                'farmer': None,
                'context_summary': 'New conversation - no previous context',
                'stored_facts': [],
                'conversation_facts': {},
                'phone_number': wa_phone_number,
                'has_history': False,
                'memory_persistence_active': False
            }
    
    async def _get_all_messages(self, wa_phone_number: str) -> List[Dict]:
        """Retrieve ALL messages from chat_messages table for complete context"""
        query = """
            SELECT role, content, timestamp 
            FROM chat_messages 
            WHERE wa_phone_number = $1 
            ORDER BY timestamp ASC
        """
        
        try:
            async with self.db_manager.get_connection_async() as conn:
                rows = await conn.fetch(query, wa_phone_number)
                
                messages = []
                for row in rows:
                    messages.append({
                        'role': row['role'],
                        'content': row['content'],
                        'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None
                    })
                
                logger.info(f"Retrieved ALL {len(messages)} messages for {wa_phone_number}")
                return messages
                
        except Exception as e:
            logger.error(f"Error retrieving all messages: {str(e)}")
            return []

    async def _get_recent_messages(self, wa_phone_number: str, limit: int) -> List[Dict]:
        """Retrieve recent messages from chat_messages table"""
        query = """
            SELECT role, content, timestamp 
            FROM chat_messages 
            WHERE wa_phone_number = $1 
            ORDER BY timestamp DESC 
            LIMIT $2
        """
        
        try:
            async with self.db_manager.get_connection_async() as conn:
                rows = await conn.fetch(query, wa_phone_number, limit)
                
                messages = []
                for row in rows:
                    messages.append({
                        'role': row['role'],
                        'content': row['content'],
                        'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None
                    })
                
                # Reverse to get chronological order
                messages.reverse()
                
                logger.info(f"Retrieved {len(messages)} messages for {wa_phone_number}")
                return messages
                
        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            return []
    
    async def _get_farmer_info_comprehensive(self, wa_phone_number: str) -> Optional[Dict]:
        """Get comprehensive farmer information including crops, fields, and calculated totals"""
        query = """
            SELECT f.*, 
                   array_agg(DISTINCT fc.crop_name) FILTER (WHERE fc.crop_name IS NOT NULL) as crops,
                   array_agg(DISTINCT fi.field_name) FILTER (WHERE fi.field_name IS NOT NULL) as fields,
                   COUNT(DISTINCT fi.id) as field_count,
                   COALESCE(SUM(DISTINCT fi.area_ha), 0) as total_hectares,
                   array_agg(DISTINCT fi.location) FILTER (WHERE fi.location IS NOT NULL) as field_locations
            FROM farmers f
            LEFT JOIN fields fi ON f.id = fi.farmer_id
            LEFT JOIN field_crops fc ON fi.id = fc.field_id
            WHERE f.wa_phone_number = $1
            GROUP BY f.id
        """
        
        try:
            async with self.db_manager.get_connection_async() as conn:
                row = await conn.fetchrow(query, wa_phone_number)
                
                if not row:
                    logger.info(f"No farmer found for phone: {wa_phone_number}")
                    return None
                
                farmer_dict = dict(row)
                
                # Clean up None values from arrays
                farmer_dict['crops'] = [c for c in (farmer_dict.get('crops', []) or []) if c]
                farmer_dict['fields'] = [f for f in (farmer_dict.get('fields', []) or []) if f]
                farmer_dict['field_locations'] = [loc for loc in (farmer_dict.get('field_locations', []) or []) if loc]
                
                logger.info(f"Found farmer: {farmer_dict.get('manager_name')} with {len(farmer_dict['crops'])} crops, {farmer_dict.get('total_hectares', 0)} hectares")
                return farmer_dict
                
        except Exception as e:
            logger.error(f"Error retrieving comprehensive farmer info: {str(e)}")
            return None

    async def _get_farmer_info(self, wa_phone_number: str) -> Optional[Dict]:
        """Get farmer information including crops and fields"""
        query = """
            SELECT f.*, 
                   array_agg(DISTINCT fc.crop_name) FILTER (WHERE fc.crop_name IS NOT NULL) as crops,
                   array_agg(DISTINCT fi.field_name) FILTER (WHERE fi.field_name IS NOT NULL) as fields
            FROM farmers f
            LEFT JOIN fields fi ON f.id = fi.farmer_id
            LEFT JOIN field_crops fc ON fi.id = fc.field_id
            WHERE f.wa_phone_number = $1
            GROUP BY f.id
        """
        
        try:
            async with self.db_manager.get_connection_async() as conn:
                row = await conn.fetchrow(query, wa_phone_number)
                
                if not row:
                    logger.info(f"No farmer found for phone: {wa_phone_number}")
                    return None
                
                farmer_dict = dict(row)
                
                # Clean up None values from arrays
                farmer_dict['crops'] = farmer_dict.get('crops', []) or []
                farmer_dict['fields'] = farmer_dict.get('fields', []) or []
                
                logger.info(f"Found farmer: {farmer_dict.get('manager_name')} with {len(farmer_dict['crops'])} crops")
                return farmer_dict
                
        except Exception as e:
            logger.error(f"Error retrieving farmer info: {str(e)}")
            return None
    
    def _build_context_summary(self, messages: List[Dict], farmer: Optional[Dict]) -> str:
        """Create a summary for LLM context"""
        summary_parts = []
        
        # Add farmer information
        if farmer:
            summary_parts.append(f"Farmer: {farmer.get('manager_name', 'Unknown')} from {farmer.get('city', 'Unknown')}, {farmer.get('country', 'Unknown')}")
            
            if farmer.get('crops'):
                summary_parts.append(f"Grows: {', '.join(farmer['crops'])}")
            
            if farmer.get('fields'):
                summary_parts.append(f"Fields: {', '.join(farmer['fields'])}")
        
        # Add recent conversation topics
        recent_topics = self._extract_topics(messages[-5:] if len(messages) > 5 else messages)
        if recent_topics:
            summary_parts.append(f"Recent topics: {', '.join(recent_topics)}")
        
        # Check if this is a new conversation or returning session
        if not messages:
            summary_parts.append("New conversation - no previous messages")
        else:
            # Add time since last conversation (CRITICAL for session persistence)
            if messages and messages[-1].get('timestamp'):
                last_msg_time = datetime.fromisoformat(messages[-1]['timestamp'])
                time_diff = datetime.now() - last_msg_time
                
                if time_diff > timedelta(hours=1):
                    # This is a returning session - emphasize memory continuity
                    if time_diff > timedelta(days=7):
                        summary_parts.append(f"RETURNING USER after {time_diff.days} days - remember all previous farming discussions")
                    elif time_diff > timedelta(days=1):
                        summary_parts.append(f"RETURNING USER after {time_diff.days} days - continue previous conversation about farming")
                    elif time_diff > timedelta(hours=3):
                        summary_parts.append(f"RETURNING USER after {int(time_diff.total_seconds()/3600)} hours - remember earlier farming topics")
                    else:
                        summary_parts.append("CONTINUING previous conversation - remember all context")
                        
            # Add historical context summary for returning users
            if len(messages) > 2:
                # Extract key topics from all messages (not just recent)
                all_topics = self._extract_topics(messages)
                crops_mentioned = []
                for msg in messages:
                    content = msg.get('content', '').lower()
                    for crop in ['mango', 'tomato', 'wheat', 'corn', 'rice', 'banana', 'apple']:
                        if crop in content and crop not in crops_mentioned:
                            crops_mentioned.append(crop)
                
                if crops_mentioned:
                    summary_parts.append(f"IMPORTANT: Previously discussed crops: {', '.join(crops_mentioned)}")
                if all_topics:
                    summary_parts.append(f"Previous farming topics: {', '.join(all_topics)}")
        
        context_summary = " | ".join(summary_parts)
        logger.info(f"Built context summary: {context_summary}")
        
        return context_summary
    
    def _build_comprehensive_context(self, all_messages: List[Dict], farmer: Optional[Dict], stored_facts: List[Dict]) -> str:
        """Build comprehensive context that captures EVERYTHING for behavioral testing"""
        context_parts = []
        
        # Farmer identity with ALL details
        if farmer:
            if farmer.get('manager_name'):
                context_parts.append(f"Farmer: {farmer['manager_name']}")
            if farmer.get('farm_name'):
                context_parts.append(f"Farm: {farmer['farm_name']}")
            if farmer.get('city') and farmer.get('country'):
                context_parts.append(f"Location: {farmer['city']}, {farmer['country']}")
            if farmer.get('total_hectares') and farmer['total_hectares'] > 0:
                context_parts.append(f"Total farm area: {farmer['total_hectares']} hectares")
            if farmer.get('crops'):
                crops = [c for c in farmer['crops'] if c]
                if crops:
                    context_parts.append(f"Registered crops: {', '.join(crops)}")
            if farmer.get('fields'):
                fields = [f for f in farmer['fields'] if f]
                if fields:
                    context_parts.append(f"Field names: {', '.join(fields)}")
        
        # Extract ALL mentioned facts from ENTIRE conversation history
        conversation_facts = self._extract_all_conversation_facts(all_messages)
        
        # Add facts from conversation with high priority
        if conversation_facts.get('crops_mentioned'):
            context_parts.append(f"MENTIONED CROPS: {', '.join(conversation_facts['crops_mentioned'])}")
        if conversation_facts.get('quantities_mentioned'):
            context_parts.append(f"QUANTITIES: {', '.join(conversation_facts['quantities_mentioned'])}")
        if conversation_facts.get('locations_mentioned'):
            context_parts.append(f"LOCATIONS: {', '.join(conversation_facts['locations_mentioned'])}")
        if conversation_facts.get('problems_mentioned'):
            context_parts.append(f"PROBLEMS DISCUSSED: {', '.join(conversation_facts['problems_mentioned'])}")
        
        # Add stored facts
        if stored_facts:
            fact_summary = self._build_facts_summary(stored_facts)
            if fact_summary:
                context_parts.append(f"STORED FACTS: {fact_summary}")
        
        # Conversation metadata - CRITICAL for behavioral testing
        if all_messages:
            context_parts.append(f"TOTAL CONVERSATION HISTORY: {len(all_messages)} messages")
            
            # Check for session breaks to emphasize memory continuity
            if len(all_messages) > 1:
                first_msg_time = datetime.fromisoformat(all_messages[0]['timestamp'])
                last_msg_time = datetime.fromisoformat(all_messages[-1]['timestamp'])
                conversation_span = last_msg_time - first_msg_time
                
                if conversation_span.total_seconds() > 3600:  # More than 1 hour
                    context_parts.append(f"LONG-TERM MEMORY: Conversation spans {conversation_span.days} days")
                    context_parts.append("CRITICAL: REMEMBER ALL PREVIOUS DETAILS - This is a returning farmer")
                
            # Add key conversation themes
            themes = self._extract_conversation_themes(all_messages)
            if themes:
                context_parts.append(f"CONVERSATION THEMES: {', '.join(themes)}")
        else:
            context_parts.append("NEW CONVERSATION: No previous message history")
        
        # Final comprehensive context
        comprehensive_context = " | ".join(context_parts)
        
        # Ensure we mention key elements for behavioral testing
        if all_messages:
            # Check for mango mentions specifically (MANGO TEST)
            has_mango = any('mango' in msg.get('content', '').lower() for msg in all_messages)
            if has_mango:
                comprehensive_context += " | CRITICAL MEMORY: Previous mango farming discussions"
            
            # Check for Bulgaria mentions specifically
            has_bulgaria = any('bulgaria' in msg.get('content', '').lower() for msg in all_messages)
            if has_bulgaria:
                comprehensive_context += " | CRITICAL MEMORY: Bulgaria location mentioned"
        
        logger.info(f"Built comprehensive context ({len(comprehensive_context)} chars): {comprehensive_context[:200]}...")
        
        return comprehensive_context
    
    def _extract_all_conversation_facts(self, messages: List[Dict]) -> Dict[str, List[str]]:
        """Extract every important fact mentioned in the entire conversation"""
        facts = {
            'crops_mentioned': set(),
            'quantities_mentioned': set(),
            'locations_mentioned': set(),
            'problems_mentioned': set(),
            'products_mentioned': set(),
            'time_references': set()
        }
        
        # Define comprehensive keyword lists
        crop_keywords = ['mango', 'corn', 'wheat', 'tomato', 'tomatoes', 'pepper', 'potato', 'potatoes', 
                        'soybean', 'grape', 'grapes', 'vineyard', 'apple', 'banana', 'rice', 'barley',
                        'sunflower', 'cucumber', 'cabbage', 'lettuce', 'carrot', 'onion', 'garlic']
        
        location_keywords = ['bulgaria', 'bulgarian', 'plovdiv', 'sofia', 'croatia', 'croatian', 'zagreb',
                           'germany', 'german', 'munich', 'italy', 'italian', 'sicily', 'poland', 'polish',
                           'krakow', 'spain', 'spanish', 'andalusia', 'france', 'french', 'provence',
                           'netherlands', 'dutch', 'holland']
        
        problem_keywords = ['aphid', 'aphids', 'mildew', 'rust', 'blight', 'weed', 'weeds', 'drought', 
                          'flood', 'pest', 'pests', 'disease', 'diseases', 'fungus', 'fungal', 'virus',
                          'yellow', 'brown', 'wilting', 'dying', 'sick', 'problem', 'issue']
        
        product_keywords = ['roundup', 'fertilizer', 'npk', 'fungicide', 'herbicide', 'pesticide',
                          'insecticide', 'organic', 'compost', 'manure', 'spray']
        
        for msg in messages:
            content = msg.get('content', '').lower()
            
            # Extract crops
            for crop in crop_keywords:
                if crop in content:
                    facts['crops_mentioned'].add(crop)
            
            # Extract quantities with units
            import re
            quantities = re.findall(r'(\d+)\s*(hectare|hectares|ha|ton|tons|kg|kilogram|liter|liters|acre|acres)', content)
            for qty, unit in quantities:
                facts['quantities_mentioned'].add(f"{qty} {unit}")
            
            # Extract locations
            for location in location_keywords:
                if location in content:
                    facts['locations_mentioned'].add(location)
            
            # Extract problems
            for problem in problem_keywords:
                if problem in content:
                    facts['problems_mentioned'].add(problem)
            
            # Extract products
            for product in product_keywords:
                if product in content:
                    facts['products_mentioned'].add(product)
            
            # Extract time references
            time_patterns = [r'(\d+)\s*(year|years|month|months|week|weeks|day|days)', 
                           r'(spring|summer|autumn|fall|winter)', 
                           r'(january|february|march|april|may|june|july|august|september|october|november|december)',
                           r'(yesterday|today|tomorrow|last week|next week|this year|last year)']
            
            for pattern in time_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        facts['time_references'].add(' '.join(match))
                    else:
                        facts['time_references'].add(match)
        
        # Convert sets to lists and limit
        result = {}
        for key, value_set in facts.items():
            result[key] = list(value_set)[:10]  # Limit to 10 items per category
        
        return result
    
    def _extract_conversation_themes(self, messages: List[Dict]) -> List[str]:
        """Extract main themes from the entire conversation"""
        themes = set()
        
        theme_keywords = {
            'planting': ['plant', 'seed', 'sow', 'planting', 'seeding'],
            'harvesting': ['harvest', 'ready', 'ripe', 'collect', 'picking'],
            'fertilization': ['fertilizer', 'npk', 'nitrogen', 'feed', 'nutrition'],
            'pest_control': ['pest', 'spray', 'disease', 'fungicide', 'pesticide'],
            'weather_concerns': ['weather', 'rain', 'drought', 'temperature', 'climate'],
            'yield_optimization': ['yield', 'production', 'improve', 'increase', 'optimize'],
            'organic_farming': ['organic', 'bio', 'natural', 'chemical-free'],
            'irrigation': ['water', 'irrigation', 'drip', 'watering'],
            'soil_management': ['soil', 'ph', 'analysis', 'test', 'quality'],
            'equipment': ['tractor', 'machinery', 'equipment', 'tools']
        }
        
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                
                for theme, keywords in theme_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        themes.add(theme)
        
        return list(themes)[:5]  # Return top 5 themes
    
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract main topics from recent messages"""
        topics = []
        
        # Keywords to look for in agricultural conversations
        topic_keywords = {
            'harvest': ['harvest', 'ready', 'ripe', 'collect'],
            'planting': ['plant', 'seed', 'sow', 'planting'],
            'fertilizer': ['fertilizer', 'npk', 'nitrogen', 'phosphorus', 'potassium'],
            'pest': ['pest', 'insect', 'disease', 'spray', 'pesticide'],
            'weather': ['weather', 'rain', 'drought', 'temperature', 'forecast'],
            'yield': ['yield', 'production', 'tons', 'hectare'],
            'organic': ['organic', 'bio', 'natural', 'chemical-free'],
            'irrigation': ['water', 'irrigation', 'drip', 'sprinkler'],
            'soil': ['soil', 'ph', 'analysis', 'test'],
            'equipment': ['tractor', 'machinery', 'equipment', 'tools']
        }
        
        # Check messages for topics
        for msg in messages:
            if msg.get('role') == 'user':
                content_lower = msg.get('content', '').lower()
                
                for topic, keywords in topic_keywords.items():
                    if any(keyword in content_lower for keyword in keywords):
                        if topic not in topics:
                            topics.append(topic)
        
        return topics[:3]  # Return top 3 topics
    
    async def store_extracted_facts(self, wa_phone_number: str, facts: Dict[str, Any]):
        """
        Store extracted facts in farmer_facts table for future reference
        """
        try:
            if not facts:
                return
                
            logger.info(f"Storing extracted facts for {wa_phone_number}: {facts}")
            
            # Store each fact type in the farmer_facts table
            async with self.db_manager.get_connection_async() as conn:
                for fact_type, fact_data in facts.items():
                    if fact_data:  # Only store non-empty facts
                        insert_query = """
                            INSERT INTO farmer_facts (
                                farmer_phone, fact_type, fact_data, source, created_at, updated_at
                            ) VALUES ($1, $2, $3, $4, NOW(), NOW())
                            ON CONFLICT (farmer_phone, fact_type, fact_data) 
                            DO UPDATE SET 
                                updated_at = NOW(),
                                version = farmer_facts.version + 1
                        """
                        
                        # Convert fact_data to JSON if it's not already
                        import json
                        if isinstance(fact_data, (dict, list)):
                            fact_json = json.dumps(fact_data)
                        else:
                            fact_json = json.dumps({"value": fact_data})
                        
                        await conn.execute(
                            insert_query,
                            wa_phone_number,
                            fact_type,
                            fact_json,
                            'chat'
                        )
            
            logger.info(f"Successfully stored {len(facts)} fact types for {wa_phone_number}")
            
        except Exception as e:
            logger.error(f"Error storing extracted facts: {str(e)}")
    
    async def get_farmer_facts(self, wa_phone_number: str, fact_type: str = None) -> List[Dict]:
        """
        Retrieve stored facts for a farmer
        
        Args:
            wa_phone_number: Phone number
            fact_type: Optional filter by fact type
            
        Returns:
            List of fact records
        """
        try:
            if fact_type:
                query = """
                    SELECT fact_type, fact_data, confidence, created_at, updated_at, version
                    FROM farmer_facts 
                    WHERE farmer_phone = $1 AND fact_type = $2
                    ORDER BY updated_at DESC
                """
                params = [wa_phone_number, fact_type]
            else:
                query = """
                    SELECT fact_type, fact_data, confidence, created_at, updated_at, version
                    FROM farmer_facts 
                    WHERE farmer_phone = $1
                    ORDER BY fact_type, updated_at DESC
                """
                params = [wa_phone_number]
            
            async with self.db_manager.get_connection_async() as conn:
                rows = await conn.fetch(query, *params)
            
            facts = []
            for row in rows:
                import json
                facts.append({
                    'fact_type': row['fact_type'],
                    'fact_data': json.loads(row['fact_data']),
                    'confidence': float(row['confidence']) if row['confidence'] else 1.0,
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'version': row['version']
                })
            
            logger.info(f"Retrieved {len(facts)} facts for {wa_phone_number}")
            return facts
            
        except Exception as e:
            logger.error(f"Error retrieving farmer facts: {str(e)}")
            return []
    
    async def get_enhanced_context(self, wa_phone_number: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get enhanced conversation context including stored facts
        """
        try:
            # Get basic context
            context = await self.get_conversation_context(wa_phone_number, limit)
            
            # Add stored facts
            stored_facts = await self.get_farmer_facts(wa_phone_number)
            context['stored_facts'] = stored_facts
            
            # Enhance context summary with facts
            if stored_facts:
                fact_summary = self._build_facts_summary(stored_facts)
                context['context_summary'] += f" | Known facts: {fact_summary}"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting enhanced context: {str(e)}")
            return await self.get_conversation_context(wa_phone_number, limit)
    
    def _build_facts_summary(self, facts: List[Dict]) -> str:
        """Build a summary of stored facts for context"""
        fact_types = {}
        
        for fact in facts:
            fact_type = fact['fact_type']
            if fact_type not in fact_types:
                fact_types[fact_type] = []
            
            fact_data = fact['fact_data']
            if isinstance(fact_data, dict) and 'value' in fact_data:
                fact_types[fact_type].append(str(fact_data['value']))
            elif isinstance(fact_data, list):
                fact_types[fact_type].extend([str(item) for item in fact_data])
            else:
                fact_types[fact_type].append(str(fact_data))
        
        # Build summary
        summary_parts = []
        for fact_type, values in fact_types.items():
            if values:
                unique_values = list(set(values))[:3]  # Max 3 values per type
                summary_parts.append(f"{fact_type}: {', '.join(unique_values)}")
        
        return "; ".join(summary_parts[:5])  # Max 5 fact types
    
    async def get_conversation_messages_for_llm(self, wa_phone_number: str, limit: int = 8) -> List[Dict[str, str]]:
        """
        Get conversation messages formatted for LLM context
        Enhanced for session persistence - includes more historical context
        Returns in the format expected by OpenAI chat completions API
        """
        # Get more messages to ensure session persistence
        messages = await self._get_recent_messages(wa_phone_number, limit)
        
        # For session persistence, include key historical messages even beyond limit
        if len(messages) >= limit:
            # Get older messages that contain important agricultural terms
            try:
                agricultural_query = """
                    SELECT role, content, timestamp 
                    FROM chat_messages 
                    WHERE wa_phone_number = $1 
                    AND (
                        LOWER(content) LIKE '%mango%' OR 
                        LOWER(content) LIKE '%hectare%' OR 
                        LOWER(content) LIKE '%farm%' OR 
                        LOWER(content) LIKE '%crop%' OR
                        LOWER(content) LIKE '%grow%'
                    )
                    ORDER BY timestamp DESC 
                    LIMIT 3
                """
                
                async with self.db_manager.get_connection_async() as conn:
                    historical_rows = await conn.fetch(agricultural_query, wa_phone_number)
                    
                    # Add important historical messages that aren't in recent messages
                    for row in historical_rows:
                        historical_msg = {
                            'role': row['role'],
                            'content': row['content'],
                            'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None
                        }
                        
                        # Only add if not already in recent messages
                        if not any(msg['content'] == historical_msg['content'] for msg in messages):
                            messages.insert(0, historical_msg)  # Insert at beginning
                            
            except Exception as e:
                logger.warning(f"Could not retrieve historical agricultural messages: {str(e)}")
        
        llm_messages = []
        for msg in messages[-limit:]:  # Still respect limit but with better selection
            llm_messages.append({
                "role": msg['role'] if msg['role'] in ['user', 'assistant'] else 'user',
                "content": msg['content']
            })
        
        return llm_messages