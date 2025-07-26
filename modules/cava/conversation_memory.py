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
    
    async def get_conversation_context(self, wa_phone_number: str, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve recent messages and extracted facts for context
        
        Args:
            wa_phone_number: WhatsApp phone number
            limit: Number of recent messages to retrieve
            
        Returns:
            Dictionary with messages, farmer info, and context summary
        """
        try:
            messages = await self._get_recent_messages(wa_phone_number, limit)
            farmer = await self._get_farmer_info(wa_phone_number)
            context_summary = self._build_context_summary(messages, farmer)
            
            return {
                'messages': messages,
                'farmer': farmer,
                'context_summary': context_summary,
                'phone_number': wa_phone_number
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return {
                'messages': [],
                'farmer': None,
                'context_summary': '',
                'phone_number': wa_phone_number
            }
    
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
        
        # Check if this is a new conversation
        if not messages:
            summary_parts.append("New conversation - no previous messages")
        else:
            # Add time since last conversation
            if messages and messages[-1].get('timestamp'):
                last_msg_time = datetime.fromisoformat(messages[-1]['timestamp'])
                time_diff = datetime.now() - last_msg_time
                
                if time_diff > timedelta(days=7):
                    summary_parts.append(f"Returning after {time_diff.days} days")
                elif time_diff > timedelta(days=1):
                    summary_parts.append(f"Last conversation {time_diff.days} days ago")
        
        context_summary = " | ".join(summary_parts)
        logger.info(f"Built context summary: {context_summary}")
        
        return context_summary
    
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
    
    async def get_conversation_messages_for_llm(self, wa_phone_number: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get conversation messages formatted for LLM context
        Returns in the format expected by OpenAI chat completions API
        """
        messages = await self._get_recent_messages(wa_phone_number, limit)
        
        llm_messages = []
        for msg in messages:
            llm_messages.append({
                "role": msg['role'] if msg['role'] in ['user', 'assistant'] else 'user',
                "content": msg['content']
            })
        
        return llm_messages