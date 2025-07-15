#!/usr/bin/env python3
"""
🏛️ Constitutional Amendment #15: LLM Query Generator
LLM generates ALL database queries, business logic, and responses
Zero custom coding - pure LLM intelligence
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

logger = logging.getLogger(__name__)

class LLMQueryGenerator:
    """
    LLM generates ALL database queries, business logic, and responses
    Constitutional Amendment #15 compliant - zero custom coding
    """
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0.1,
            openai_api_key=openai_api_key
        )
    
    async def generate_database_query(self, farmer_question: str, farmer_context: Dict, db_schema: str) -> str:
        """
        🧠 LLM writes SQL queries for ANY farming question
        Amendment #15: Universal intelligence handles watermelon, Bulgarian mango, any crop
        """
        
        constitutional_prompt = f"""
🏛️ Constitutional Amendment #15: LLM-Generated Intelligence

You are AVA's universal database intelligence. Generate a SQL query for ANY farming question.

FARMER QUESTION: "{farmer_question}"
FARMER CONTEXT: {json.dumps(farmer_context, indent=2)}

DATABASE SCHEMA:
{db_schema}

CONSTITUTIONAL REQUIREMENTS:
- Handle ANY crop (watermelon, Bulgarian mango, unknown crops)
- Work for ANY country/language context
- Generate appropriate SQL for the farmer's specific question
- Use farmer's actual field names and data from context

EXAMPLES OF UNIVERSAL INTELLIGENCE:
- "Where's my watermelon?" → Query fields table for watermelon plantings
- "Harvest ready?" → Query applications + PHI data for harvest timing
- "Bulgarian mango pesticides?" → Query treatments for mango in Bulgaria
- "Field north problems?" → Query applications/observations for field 'north'

Generate only the SQL query, nothing else.
If farmer context is missing, generate a query that would work when context is available.
"""
        
        try:
            response = await self.llm.apredict_messages([
                HumanMessage(content=constitutional_prompt)
            ])
            
            query = response.content.strip()
            
            # Remove any markdown formatting
            if query.startswith('```sql'):
                query = query[6:]
            if query.endswith('```'):
                query = query[:-3]
            
            logger.info(f"🧠 LLM generated query for '{farmer_question}': {query}")
            return query.strip()
            
        except Exception as e:
            logger.error(f"❌ LLM query generation failed: {str(e)}")
            return "SELECT 'LLM query generation failed' as error;"
    
    async def generate_response_logic(self, question: str, raw_data: List[Dict], farmer_context: Dict) -> str:
        """
        🧠 LLM converts raw database results to farmer-friendly responses
        Amendment #15: Universal intelligence for ANY agricultural scenario
        """
        
        constitutional_prompt = f"""
🏛️ Constitutional Amendment #15: LLM-Generated Intelligence

You are AVA's universal response intelligence. Convert database results to farmer-friendly responses.

FARMER QUESTION: "{question}"
FARMER CONTEXT: {json.dumps(farmer_context, indent=2)}
DATABASE RESULTS: {json.dumps(raw_data, indent=2)}

CONSTITUTIONAL REQUIREMENTS:
- Work for ANY crop, ANY country, ANY farming question
- Reference actual field names and dates from results
- Be conversational but professional (agricultural tone)
- Handle empty results gracefully
- Adapt to farmer's language context

UNIVERSAL INTELLIGENCE EXAMPLES:
- Watermelon location: "Your watermelon is in the north field, planted on March 15th"
- Bulgarian mango harvest: "Your mango in field 'south' will be ready in 14 days"
- Pesticide question: "You last applied Prosaro to your corn on June 10th"
- Empty results: "I don't see any [crop] data in your records yet"

Generate a helpful, conversational response based on the database results.
"""
        
        try:
            response = await self.llm.apredict_messages([
                HumanMessage(content=constitutional_prompt)
            ])
            
            farmer_response = response.content.strip()
            logger.info(f"🧠 LLM generated response for '{question}': {farmer_response[:100]}...")
            
            return farmer_response
            
        except Exception as e:
            logger.error(f"❌ LLM response generation failed: {str(e)}")
            return "I'm having trouble processing that question right now. Could you try rephrasing it?"
    
    async def generate_storage_instructions(self, farmer_message: str, farmer_context: Dict) -> List[Dict]:
        """
        🧠 LLM decides what farming facts to store and how
        Amendment #15: Universal intelligence extracts data from ANY conversation
        """
        
        constitutional_prompt = f"""
🏛️ Constitutional Amendment #15: LLM-Generated Intelligence

You are AVA's universal storage intelligence. Extract farming facts that should be stored.

FARMER MESSAGE: "{farmer_message}"
FARMER CONTEXT: {json.dumps(farmer_context, indent=2)}

CONSTITUTIONAL REQUIREMENTS:
- Extract ANY farming information (crops, fields, applications, observations)
- Work for ANY crop, ANY country, ANY farming practice
- Generate appropriate SQL INSERT/UPDATE statements
- Handle partial information gracefully

UNIVERSAL INTELLIGENCE EXAMPLES:
- "I planted watermelon in north field" → INSERT into plantings
- "Applied Prosaro to corn yesterday" → INSERT into applications
- "Bulgarian mango harvest ready" → UPDATE harvest_status
- "Field south has aphids" → INSERT into observations

Return JSON with SQL operations needed:
{{
  "operations": [
    {{
      "type": "INSERT",
      "table": "plantings",
      "sql": "INSERT INTO plantings (farmer_id, field_name, crop_type, plant_date) VALUES (?, ?, ?, ?)",
      "values": [123, "north", "watermelon", "2024-03-15"]
    }}
  ]
}}

Return empty array if no farming facts to store.
"""
        
        try:
            response = await self.llm.apredict_messages([
                HumanMessage(content=constitutional_prompt)
            ])
            
            storage_instructions = response.content.strip()
            
            # Parse JSON response
            if storage_instructions.startswith('```json'):
                storage_instructions = storage_instructions[7:]
            if storage_instructions.endswith('```'):
                storage_instructions = storage_instructions[:-3]
            
            operations = json.loads(storage_instructions)
            
            logger.info(f"🧠 LLM generated {len(operations.get('operations', []))} storage operations")
            return operations.get('operations', [])
            
        except Exception as e:
            logger.error(f"❌ LLM storage generation failed: {str(e)}")
            return []
    
    async def analyze_message_intent(self, farmer_message: str, conversation_history: List[Dict]) -> Dict:
        """
        🧠 LLM analyzes what to do with farmer's message
        Amendment #15: Universal intelligence determines query/storage needs
        """
        
        constitutional_prompt = f"""
🏛️ Constitutional Amendment #15: LLM-Generated Intelligence

You are AVA's universal intent intelligence. Analyze what this farmer message requires.

FARMER MESSAGE: "{farmer_message}"
CONVERSATION HISTORY: {json.dumps(conversation_history[-5:], indent=2)}

CONSTITUTIONAL REQUIREMENTS:
- Determine if database query needed (questions about existing data)
- Determine if storage needed (new farming information shared)
- Work for ANY crop, ANY country, ANY farming scenario
- Handle mixed conversations (questions + new info)

UNIVERSAL INTELLIGENCE EXAMPLES:
- "Where's my watermelon?" → query_needed: true, storage_needed: false
- "I planted corn yesterday" → query_needed: false, storage_needed: true
- "Applied Prosaro to my mango field" → query_needed: false, storage_needed: true
- "When did I last spray?" → query_needed: true, storage_needed: false

Return JSON analysis:
{{
  "query_needed": true/false,
  "storage_needed": true/false,
  "intent_type": "question|information|greeting|mixed",
  "confidence": 0.9
}}
"""
        
        try:
            response = await self.llm.apredict_messages([
                HumanMessage(content=constitutional_prompt)
            ])
            
            analysis = response.content.strip()
            
            # Parse JSON response
            if analysis.startswith('```json'):
                analysis = analysis[7:]
            if analysis.endswith('```'):
                analysis = analysis[:-3]
            
            intent_analysis = json.loads(analysis)
            
            logger.info(f"🧠 LLM analyzed intent: {intent_analysis}")
            return intent_analysis
            
        except Exception as e:
            logger.error(f"❌ LLM intent analysis failed: {str(e)}")
            return {
                "query_needed": True,
                "storage_needed": False,
                "intent_type": "question",
                "confidence": 0.5
            }
    
    async def handle_query_error(self, failed_query: str, error_message: str) -> str:
        """
        🧠 LLM handles database query errors intelligently
        Amendment #15: Universal error recovery
        """
        
        constitutional_prompt = f"""
🏛️ Constitutional Amendment #15: LLM-Generated Intelligence

You are AVA's universal error recovery intelligence. Handle this database query error.

FAILED QUERY: {failed_query}
ERROR MESSAGE: {error_message}

CONSTITUTIONAL REQUIREMENTS:
- Generate a farmer-friendly error response
- Don't expose technical details
- Suggest alternative approaches
- Work for ANY farming scenario

Generate a helpful response that acknowledges the issue without technical jargon.
"""
        
        try:
            response = await self.llm.apredict_messages([
                HumanMessage(content=constitutional_prompt)
            ])
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"❌ LLM error handling failed: {str(e)}")
            return "I'm having trouble accessing that information right now. Could you try asking in a different way?"