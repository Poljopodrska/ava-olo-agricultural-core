"""
🏛️ CAVA LLM Query Generator
Constitutional Amendment #15 compliance - LLM generates ALL queries
Zero custom coding for specific farming scenarios
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config_manager import config as main_config

logger = logging.getLogger(__name__)

class CAVALLMQueryGenerator:
    """
    LLM generates ALL database queries for CAVA
    Constitutional principles: LLM-FIRST, MANGO RULE, PRIVACY-FIRST
    """
    
    def __init__(self):
        self.api_key = main_config.openai_api_key
        self.model = os.getenv('CAVA_LLM_MODEL', 'gpt-4')
        self.temperature = 0.1  # Low temperature for consistent query generation
        self.dry_run = os.getenv('CAVA_DRY_RUN_MODE', 'true').lower() == 'true'
        
        # Initialize OpenAI client
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("⚠️ OpenAI API key not configured")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_farmer_message(self, message: str, conversation_context: Dict) -> Dict:
        """
        LLM analyzes farmer message and determines what actions needed
        Works for ANY crop, ANY country (MANGO RULE)
        """
        prompt = f"""
You are analyzing a farmer's message in the CAVA conversation system.
Constitutional requirements: Must work for ANY crop in ANY country.

FARMER MESSAGE: "{message}"
CONVERSATION CONTEXT: {json.dumps(conversation_context, indent=2)}

Analyze this message and return JSON with:
{{
    "intent": "registration|farming_question|product_application|harvest_timing|field_info|general_chat",
    "entities": {{
        "farmer_name": "extracted name or null",
        "fields": ["field names mentioned"],
        "products": ["product names mentioned"], 
        "crops": ["crop types mentioned - watermelon, mango, dragonfruit, etc."],
        "dates": ["dates mentioned in YYYY-MM-DD format"],
        "locations": ["locations/countries mentioned"]
    }},
    "actions_needed": {{
        "store_in_graph": true/false,
        "query_graph": true/false,
        "search_vector": true/false,
        "update_memory": true/false,
        "check_harvest_timing": true/false
    }},
    "conversation_type": "registration|farming|mixed",
    "language_detected": "en|es|bg|hr|sl|etc",
    "confidence": 0.0-1.0
}}

Focus on farming relationships and extracting actionable information.
Support ALL crops including exotic ones (dragonfruit, quinoa, acai, etc).
Return only valid JSON.
"""
        
        # Define fallback response for registration
        fallback_response = {
            "intent": "registration",
            "entities": {
                "farmer_name": message if len(message.split()) <= 3 else None  # Simple name detection
            },
            "actions_needed": {"update_memory": True},
            "conversation_type": "registration",
            "confidence": 0.5
        }
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would analyze message with LLM")
            # Return mock analysis for testing
            return {
                "intent": "farming_question" if "?" in message else "general_chat",
                "entities": {
                    "crops": ["watermelon"] if "watermelon" in message.lower() else [],
                    "fields": ["north field"] if "north" in message.lower() else []
                },
                "actions_needed": {
                    "query_graph": "?" in message,
                    "store_in_graph": "plant" in message.lower() or "applied" in message.lower()
                },
                "conversation_type": "farming",
                "confidence": 0.9
            }
        
        try:
            if not self.client:
                logger.error("❌ OpenAI client not initialized - API key missing?")
                return fallback_response
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a farming analysis expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.debug(f"LLM analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {str(e)}")
            return {
                "intent": "general_chat",
                "entities": {},
                "actions_needed": {},
                "error": str(e)
            }
    
    async def generate_graph_storage_query(self, analysis: Dict, farmer_id: int) -> Optional[str]:
        """
        LLM generates Cypher query to store farming relationships
        Universal support for ANY crop or farming practice
        """
        if not analysis.get("actions_needed", {}).get("store_in_graph"):
            return None
        
        entities = analysis.get("entities", {})
        
        prompt = f"""
Generate a Cypher query to store farming information in Neo4j graph.

ANALYSIS: {json.dumps(analysis, indent=2)}
FARMER_ID: {farmer_id}

Graph Schema:
- (Farmer {{id, name, phone, farm_name, country, language}})
- (Field {{id, name, area_ha, location, soil_type}})
- (Product {{name, type, active_ingredient, pre_harvest_days}})
- (Application {{date, amount, method, weather_conditions}})
- (Crop {{id, type, variety, planting_date, expected_harvest}})

Relationships:
- (Farmer)-[:OWNS]->(Field)
- (Field)-[:PLANTED_WITH]->(Crop)
- (Field)-[:TREATED_WITH]->(Application)
- (Application)-[:USED_PRODUCT]->(Product)
- (Crop)-[:SUITABLE_FOR_CLIMATE]->(Country)

Requirements:
1. Use MERGE to avoid duplicates
2. Handle ANY crop type (watermelon, mango, dragonfruit, quinoa, etc.)
3. Support ANY country/location
4. Use parameters like $farmer_id, $field_name, etc.
5. Add timestamps where appropriate

Generate Cypher query that stores the extracted information.
Return only the Cypher query, nothing else.
"""
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would generate storage query with LLM")
            return """
            MATCH (f:Farmer {id: $farmer_id})
            MERGE (field:Field {name: $field_name, farmer_id: $farmer_id})
            MERGE (crop:Crop {type: $crop_type, field_id: field.id})
            MERGE (f)-[:OWNS]->(field)
            MERGE (field)-[:PLANTED_WITH]->(crop)
            SET crop.planting_date = date()
            """
        
        try:
            if not self.client:
                logger.error("❌ OpenAI client not initialized - API key missing?")
                return fallback_response
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Neo4j Cypher expert. Generate valid Cypher queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            cypher = response.choices[0].message.content.strip()
            # Remove markdown formatting if present
            if cypher.startswith("```"):
                cypher = cypher.split("```")[1].replace("cypher", "").strip()
            
            logger.debug(f"Generated storage Cypher: {cypher[:100]}...")
            return cypher
            
        except Exception as e:
            logger.error(f"❌ Storage query generation failed: {str(e)}")
            return None
    
    async def generate_graph_query(self, question: str, farmer_id: int, conversation_context: Dict) -> Optional[str]:
        """
        LLM generates Cypher query to answer farmer questions
        Works for watermelon, Bulgarian mango, dragonfruit, ANY crop
        """
        prompt = f"""
Generate a Cypher query to answer the farmer's question using Neo4j graph.

FARMER QUESTION: "{question}"
FARMER_ID: {farmer_id}
CONTEXT: {json.dumps(conversation_context, indent=2)}

Graph Schema:
- (Farmer {{id, name, phone, farm_name, country}})
- (Field {{id, name, area_ha, crop_type, location}})
- (Product {{name, type, pre_harvest_days}})
- (Application {{date, amount, method}})
- (Crop {{id, type, variety, planting_date, expected_harvest}})

Common query patterns:
1. "Where is my [crop]?" → Find fields with specific crop
2. "When can I harvest?" → Check planting date + crop maturity time
3. "What did I apply?" → Find applications for fields
4. "Is it ready?" → Calculate harvest timing based on applications

Generate a Cypher query that:
- Answers the specific question
- Works for ANY crop type (not just common ones)
- Uses $farmer_id parameter
- Returns relevant data

Return only the Cypher query, nothing else.
"""
        
        if self.dry_run:
            logger.info(f"🔍 DRY RUN: Would generate query for: {question}")
            return """
            MATCH (f:Farmer {id: $farmer_id})-[:OWNS]->(field:Field)
            OPTIONAL MATCH (field)-[:PLANTED_WITH]->(crop:Crop)
            RETURN field.name as field_name, crop.type as crop_type, crop.planting_date as planted_date
            """
        
        try:
            if not self.client:
                logger.error("❌ OpenAI client not initialized - API key missing?")
                return fallback_response
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Neo4j Cypher expert for farming queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            cypher = response.choices[0].message.content.strip()
            if cypher.startswith("```"):
                cypher = cypher.split("```")[1].replace("cypher", "").strip()
            
            logger.debug(f"Generated query Cypher: {cypher[:100]}...")
            return cypher
            
        except Exception as e:
            logger.error(f"❌ Query generation failed: {str(e)}")
            return None
    
    async def generate_response_from_data(self, question: str, graph_data: List[Dict], analysis: Dict) -> str:
        """
        LLM generates farmer-friendly response from raw graph data
        Supports ALL crops and farming scenarios
        """
        prompt = f"""
You are AVA, a constitutional agricultural assistant. Generate a helpful response.

FARMER QUESTION: "{question}"
GRAPH DATA: {json.dumps(graph_data, indent=2)}
MESSAGE ANALYSIS: {json.dumps(analysis, indent=2)}

Constitutional requirements:
1. Work for ANY crop in ANY country (MANGO RULE)
2. Be conversational and helpful (FARMER-CENTRIC)
3. Reference specific field names, dates, and products from the data
4. Give actionable agricultural advice
5. If no data found, ask clarifying questions
6. Support exotic crops (dragonfruit, quinoa, Bulgarian mango, etc.)

Generate a natural farmer response that:
- Directly answers their question
- Uses their exact field/crop names
- Provides practical advice
- Maintains professional agricultural tone
"""
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would generate response with LLM")
            if graph_data:
                return f"I found information about your fields: {graph_data[0].get('field_name', 'your field')}. How can I help you further?"
            else:
                return "I don't have any information about that yet. Could you tell me more about what you've planted?"
        
        try:
            if not self.client:
                logger.error("❌ OpenAI client not initialized - API key missing?")
                return fallback_response
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are AVA, a helpful agricultural assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Slightly higher for more natural responses
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Response generation failed: {str(e)}")
            return "I'm having trouble processing that right now. Could you try asking in a different way?"
    
    async def extract_registration_data(self, message: str, current_state: Dict) -> Dict:
        """
        LLM extracts registration information from farmer messages
        Handles names from ANY country/culture
        """
        prompt = f"""
Extract registration information from farmer message.

MESSAGE: "{message}"
CURRENT STATE: {json.dumps(current_state, indent=2)}

Requirements:
1. Handle names from ANY culture (Croatian, Bulgarian, Hindi, Chinese, etc.)
2. Detect phone numbers with ANY country code
3. Only extract NEW information not already in current state
4. Handle hyphenated names, multiple surnames, etc.

Extract and return JSON:
{{
    "first_name": "extracted first name or null",
    "last_name": "extracted last name or null", 
    "full_name": "combined name if both available",
    "phone_number": "phone with country code or null",
    "farm_name": "farm name or null",
    "password": "password if provided or null",
    "country_detected": "country from phone code or null",
    "updates_made": ["list of fields that were updated"]
}}

Return only valid JSON.
"""
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would extract registration data with LLM")
            # Smarter mock extraction for testing
            mock_data = {"updates_made": []}
            
            # Extract name if not present
            if not current_state.get("full_name"):
                # Check if message looks like a name (2+ words, all alphabetic)
                words = [w for w in message.split() if w.replace("-", "").isalpha()]
                if len(words) >= 2:
                    mock_data["full_name"] = " ".join(words)
                    mock_data["first_name"] = words[0]
                    mock_data["last_name"] = " ".join(words[1:])
                    mock_data["updates_made"].extend(["full_name", "first_name", "last_name"])
                elif len(words) == 1 and not current_state.get("first_name"):
                    mock_data["first_name"] = words[0]
                    mock_data["updates_made"].append("first_name")
            
            # Extract phone if not present
            if not current_state.get("phone_number") and ("+" in message or any(c.isdigit() for c in message)):
                # Simple phone detection
                if message.startswith("+") and len(message) > 10:
                    mock_data["phone_number"] = message.strip()
                    mock_data["updates_made"].append("phone_number")
                    # Detect country from phone prefix
                    if message.startswith("+385"):
                        mock_data["country_detected"] = "Croatia"
                    elif message.startswith("+359"):
                        mock_data["country_detected"] = "Bulgaria"
            
            # Extract password if not present
            if not current_state.get("password") and current_state.get("phone_number"):
                # If we have name and phone, any other text might be password
                if len(message) >= 6 and not message.startswith("+"):
                    mock_data["password"] = message
                    mock_data["updates_made"].append("password")
                
            return mock_data
        
        # Define fallback extraction when OpenAI not available
        fallback_extraction = {"updates_made": []}
        
        # Simple extraction logic
        if not current_state.get("full_name"):
            words = message.strip().split()
            if len(words) >= 2 and all(w.replace("-", "").replace("č", "c").replace("ć", "c").isalpha() for w in words):
                fallback_extraction["full_name"] = message.strip()
                fallback_extraction["first_name"] = words[0]
                fallback_extraction["last_name"] = " ".join(words[1:])
                fallback_extraction["updates_made"] = ["full_name", "first_name", "last_name"]
            elif len(words) == 1 and words[0].replace("-", "").isalpha():
                fallback_extraction["first_name"] = words[0]
                fallback_extraction["updates_made"] = ["first_name"]
        elif not current_state.get("phone_number") and message.startswith("+"):
            fallback_extraction["phone_number"] = message.strip()
            fallback_extraction["updates_made"] = ["phone_number"]
        elif not current_state.get("password") and len(message) >= 6:
            fallback_extraction["password"] = message
            fallback_extraction["updates_made"] = ["password"]
            
        try:
            if not self.client:
                logger.error("❌ OpenAI client not initialized - Using fallback extraction")
                return fallback_extraction
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a registration data extractor. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"❌ Registration extraction failed: {str(e)}")
            return {"error": str(e), "updates_made": []}
    
    async def generate_sql_query(self, question: str, farmer_id: int, context: Dict) -> Optional[str]:
        """
        LLM generates PostgreSQL queries for CAVA schema
        """
        prompt = f"""
Generate a PostgreSQL query for the CAVA schema.

QUESTION: "{question}"
FARMER_ID: {farmer_id}
CONTEXT: {json.dumps(context, indent=2)}

CAVA Schema (schema: cava):
- conversation_sessions (id, session_id, farmer_id, conversation_type, total_messages)
- intelligence_log (id, session_id, message_type, llm_analysis, database_queries)
- performance_metrics (metric_date, avg_response_time_ms, error_count)

Generate SQL that answers the question.
Use cava schema prefix (e.g., cava.conversation_sessions).
Return only the SQL query.
"""
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would generate SQL with LLM")
            return "SELECT * FROM cava.conversation_sessions WHERE farmer_id = $1 ORDER BY created_at DESC LIMIT 10"
        
        try:
            if not self.client:
                logger.error("❌ OpenAI client not initialized - API key missing?")
                return fallback_response
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ SQL generation failed: {str(e)}")
            return None

# Test the LLM query generator
async def test_llm_query_generator():
    """Test LLM query generation capabilities"""
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    generator = CAVALLMQueryGenerator()
    
    # Test 1: Watermelon question
    print("\n🍉 Test 1: Watermelon Question")
    analysis = await generator.analyze_farmer_message(
        "Where did I plant my watermelon?",
        {"farmer_id": 123, "recent_topics": ["planting", "fields"]}
    )
    print(f"Analysis: {json.dumps(analysis, indent=2)}")
    
    query = await generator.generate_graph_query(
        "Where did I plant my watermelon?",
        123,
        {"recent_topics": ["planting"]}
    )
    print(f"Generated Query: {query}")
    
    # Test 2: Bulgarian mango (MANGO RULE test)
    print("\n🥭 Test 2: Bulgarian Mango Farmer")
    analysis = await generator.analyze_farmer_message(
        "When can I harvest my Bulgarian mangoes?",
        {"farmer_id": 456, "location": "Bulgaria"}
    )
    print(f"Analysis: {json.dumps(analysis, indent=2)}")
    
    # Test 3: Registration
    print("\n📝 Test 3: Registration Data")
    reg_data = await generator.extract_registration_data(
        "My name is Peter Knaflič",
        {"first_name": None, "last_name": None}
    )
    print(f"Registration: {json.dumps(reg_data, indent=2)}")
    
    # Test 4: Product application
    print("\n💊 Test 4: Product Application")
    analysis = await generator.analyze_farmer_message(
        "I applied Roundup to north field yesterday",
        {"farmer_id": 123}
    )
    print(f"Analysis: {json.dumps(analysis, indent=2)}")
    
    storage_query = await generator.generate_graph_storage_query(analysis, 123)
    print(f"Storage Query: {storage_query}")
    
    print("\n✅ LLM Query Generator Tests Complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_llm_query_generator())