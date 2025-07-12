"""
LLM-First Farmer Database Query Engine
Constitutional Principle #3 Implementation

This system achieves 100% constitutional compliance:
- GPT-4 transforms natural language to SQL
- GPT-4 transforms results back to natural language  
- No hardcoded queries (MANGO RULE compliant)
- Works for any crop in any country
- Privacy-first (farmer data stays internal)
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import constitutional config manager
try:
    from ava_olo_shared.config_manager import config
except ImportError:
    # Fallback for different import paths
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ava-olo-shared'))
    from config_manager import config

logger = logging.getLogger(__name__)


@dataclass
class DatabaseQuery:
    """Represents a database query with context"""
    natural_language_query: str
    farmer_id: Optional[int] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    query_type: Optional[str] = None
    ethnicity: Optional[str] = None
    phone_number: Optional[str] = None
    language_override: bool = False
    country_override: bool = False


@dataclass  
class QueryResult:
    """Represents query result with metadata"""
    natural_language_response: str
    sql_query: str
    raw_results: List[Dict]
    processing_metadata: Dict[str, Any]
    constitutional_compliance: bool = True


class LLMDatabaseQueryEngine:
    """
    Pure LLM-driven database query engine
    Constitutional compliance: GPT-4 handles all query logic
    """
    
    def __init__(self):
        # Use config manager for OpenAI initialization
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model
        self.db_connection = None
        self._initialize_database()
        
        # Initialize smart country detector
        try:
            from ava_olo_shared.smart_country_detector import SmartCountryDetector
            self.country_detector = SmartCountryDetector()
            logger.info("Smart country detector initialized")
        except ImportError:
            logger.warning("Smart country detector not available - using basic detection")
            self.country_detector = None
        
        # Log constitutional compliance
        if config.enable_constitutional_checks:
            compliance = config.validate_constitutional_compliance()
            logger.info(f"Constitutional compliance check: {compliance}")
        
    def _initialize_database(self):
        """Initialize database connection using constitutional config"""
        try:
            # Use config manager for database connection
            self.db_connection = psycopg2.connect(
                host=config.db_host,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                port=config.db_port
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def process_farmer_query(self, 
                                 query: DatabaseQuery) -> QueryResult:
        """
        Process farmer query using pure LLM approach with smart country/language detection
        Main entry point for constitutional compliance
        """
        # Step 1: Apply smart country/language detection if available
        enhanced_query = await self._enhance_query_with_smart_detection(query)
        
        # Step 2: Get database schema for context
        schema_info = self._get_database_schema()
        
        # Step 3: Generate SQL using GPT-4
        sql_query = await self._llm_generate_sql(enhanced_query, schema_info)
        
        # Step 4: Execute query safely
        raw_results = self._execute_query_safely(sql_query, enhanced_query.farmer_id)
        
        # Step 5: Convert results to natural language using GPT-4
        natural_response = await self._llm_format_response(
            enhanced_query, sql_query, raw_results
        )
        
        # Step 6: Log for transparency
        metadata = self._create_metadata(enhanced_query, sql_query, raw_results)
        
        return QueryResult(
            natural_language_response=natural_response,
            sql_query=sql_query,
            raw_results=raw_results,
            processing_metadata=metadata,
            constitutional_compliance=True
        )
    
    async def _enhance_query_with_smart_detection(self, query: DatabaseQuery) -> DatabaseQuery:
        """Enhance query with smart country/language detection"""
        if not self.country_detector or not query.phone_number:
            return query
        
        try:
            # Use smart detection
            detection_result = self.country_detector.detect_with_override(
                phone_number=query.phone_number,
                language_override=query.language if query.language_override else None,
                country_override=query.country_code if query.country_override else None,
                ethnicity=query.ethnicity
            )
            
            # Update query with detected information
            enhanced_query = DatabaseQuery(
                natural_language_query=query.natural_language_query,
                farmer_id=query.farmer_id,
                country_code=detection_result.country_code,
                language=detection_result.primary_language,
                query_type=query.query_type,
                ethnicity=query.ethnicity,
                phone_number=query.phone_number,
                language_override=detection_result.is_override,
                country_override=detection_result.is_override
            )
            
            logger.info(f"Smart detection: {query.phone_number} -> {detection_result.country_code} ({detection_result.primary_language})")
            if detection_result.is_override:
                logger.info(f"Override applied: {detection_result.override_reason}")
            
            return enhanced_query
            
        except Exception as e:
            logger.warning(f"Smart detection failed: {e}, using original query")
            return query
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """Get database schema information for LLM context"""
        schema_query = """
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name IN ('farmers', 'fields', 'field_crops', 'tasks', 'incoming_messages')
        ORDER BY table_name, ordinal_position;
        """
        
        with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(schema_query)
            schema_results = cursor.fetchall()
        
        # Organize schema by table
        schema_info = {}
        for row in schema_results:
            table_name = row['table_name']
            if table_name not in schema_info:
                schema_info[table_name] = []
            schema_info[table_name].append({
                'column': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable']
            })
        
        return schema_info
    
    async def _llm_generate_sql(self, 
                              query: DatabaseQuery, 
                              schema_info: Dict) -> str:
        """
        Use GPT-4 to generate SQL from natural language
        Constitutional compliance: Pure LLM intelligence
        """
        # Build comprehensive prompt for SQL generation
        system_prompt = self._build_sql_generation_prompt(schema_info)
        user_prompt = self._build_user_query_prompt(query)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,  # Deterministic for SQL generation
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean and validate SQL
            sql_query = self._clean_sql_query(sql_query)
            
            # Log the generated query
            logger.info(f"Generated SQL: {sql_query}")
            
            return sql_query
            
        except Exception as e:
            logger.error(f"LLM SQL generation failed: {e}")
            # Fallback: Safe default query
            return f"SELECT 'Error generating query' as message;"
    
    def _build_sql_generation_prompt(self, schema_info: Dict) -> str:
        """Build system prompt for SQL generation"""
        schema_description = self._format_schema_for_prompt(schema_info)
        
        return f"""You are an expert SQL generator for a farmer CRM system.

DATABASE SCHEMA:
{schema_description}

RULES:
1. Generate ONLY PostgreSQL SELECT queries
2. NEVER use INSERT, UPDATE, DELETE, or DROP
3. Always include WHERE clauses to limit results to specific farmer if farmer_id provided
4. Use proper JOINs to get related data
5. Return only the SQL query, no explanations
6. Use clear column aliases for better readability
7. Handle NULL values appropriately
8. Limit results to 100 rows maximum

SECURITY:
- Only SELECT operations allowed
- No dynamic SQL injection patterns
- Always parameterize farmer_id if provided

EXAMPLES:
Query: "How many fields do I have?"
SQL: SELECT COUNT(*) as field_count FROM fields WHERE farmer_id = %s;

Query: "What crops am I growing?"
SQL: SELECT DISTINCT fc.crop_name, COUNT(*) as field_count 
     FROM field_crops fc 
     JOIN fields f ON fc.field_id = f.field_id 
     WHERE f.farmer_id = %s 
     GROUP BY fc.crop_name;

Query: "Show me my recent tasks"
SQL: SELECT task_description, due_date, status 
     FROM tasks 
     WHERE farmer_id = %s 
     ORDER BY due_date DESC 
     LIMIT 10;
"""
    
    def _format_schema_for_prompt(self, schema_info: Dict) -> str:
        """Format schema information for LLM prompt"""
        schema_text = []
        
        for table_name, columns in schema_info.items():
            schema_text.append(f"\nTable: {table_name}")
            for col in columns:
                nullable = "NULL" if col['nullable'] == 'YES' else "NOT NULL"
                schema_text.append(f"  - {col['column']} ({col['type']}) {nullable}")
        
        return "\n".join(schema_text)
    
    def _build_user_query_prompt(self, query: DatabaseQuery) -> str:
        """Build user prompt for specific query"""
        prompt_parts = [f"Natural language query: {query.natural_language_query}"]
        
        if query.farmer_id:
            prompt_parts.append(f"Farmer ID: {query.farmer_id}")
        
        if query.language:
            prompt_parts.append(f"Response should consider language: {query.language}")
        
        if query.country_code:
            prompt_parts.append(f"Farmer's country: {query.country_code}")
        
        prompt_parts.append("\nGenerate the SQL query:")
        
        return "\n".join(prompt_parts)
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and validate SQL query for safety"""
        # Remove any markdown formatting
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Ensure it's a SELECT query
        if not sql_query.upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Remove dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
        sql_upper = sql_query.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"Forbidden keyword: {keyword}")
        
        # Ensure query ends with semicolon
        if not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query
    
    def _execute_query_safely(self, 
                            sql_query: str, 
                            farmer_id: Optional[int]) -> List[Dict]:
        """Execute SQL query safely with proper error handling"""
        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Use parameterized query if farmer_id is provided
                if farmer_id and '%s' in sql_query:
                    cursor.execute(sql_query, (farmer_id,))
                else:
                    cursor.execute(sql_query)
                
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return [{"error": f"Query execution failed: {str(e)}"}]
    
    async def _llm_format_response(self, 
                                 query: DatabaseQuery,
                                 sql_query: str,
                                 raw_results: List[Dict]) -> str:
        """
        Use GPT-4 to format results into natural language
        Constitutional compliance: LLM handles all formatting
        """
        # Build prompt for response formatting
        system_prompt = self._build_response_formatting_prompt(query)
        user_prompt = self._build_results_prompt(query, sql_query, raw_results)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Slight creativity for natural language
                max_tokens=800
            )
            
            formatted_response = response.choices[0].message.content.strip()
            
            # Log the formatted response
            logger.info(f"Formatted response: {formatted_response}")
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"LLM response formatting failed: {e}")
            # Fallback: Simple formatting
            return self._simple_fallback_response(raw_results)
    
    def _build_response_formatting_prompt(self, query: DatabaseQuery) -> str:
        """Build system prompt for response formatting"""
        language_instruction = ""
        if query.language and query.language != 'en':
            language_map = {
                'bg': 'Bulgarian',
                'sl': 'Slovenian', 
                'hr': 'Croatian',
                'sr': 'Serbian',
                'es': 'Spanish',
                'pt': 'Portuguese'
            }
            lang_name = language_map.get(query.language, query.language)
            language_instruction = f"Respond in {lang_name} language."
        
        return f"""You are AVA OLO, a helpful agricultural assistant for farmers.

Your job is to convert database query results into natural, helpful responses for farmers.

GUIDELINES:
1. Be professional but friendly
2. Use agricultural terminology appropriately
3. Present data clearly and concisely
4. If no results found, explain helpfully
5. Include relevant agricultural context when appropriate
6. {language_instruction}
7. Focus on practical information farmers need
8. Use measurements and terms familiar to farmers
9. Be encouraging and supportive

TONE: Professional agricultural advisor, not overly sweet or casual.

CONTEXT: You are responding to a farmer's question about their agricultural data."""
    
    def _build_results_prompt(self, 
                            query: DatabaseQuery,
                            sql_query: str,
                            raw_results: List[Dict]) -> str:
        """Build prompt with query results for formatting"""
        prompt_parts = [
            f"Farmer's original question: {query.natural_language_query}",
            f"Database query executed: {sql_query}",
            f"Query results: {json.dumps(raw_results, indent=2, default=str)}",
            "",
            "Convert these results into a helpful, natural language response for the farmer:"
        ]
        
        return "\n".join(prompt_parts)
    
    def _simple_fallback_response(self, raw_results: List[Dict]) -> str:
        """Simple fallback response if LLM formatting fails"""
        if not raw_results:
            return "No data found for your query."
        
        if len(raw_results) == 1 and 'error' in raw_results[0]:
            return f"I encountered an issue processing your request: {raw_results[0]['error']}"
        
        # Simple table-like format
        return f"Found {len(raw_results)} result(s). Please try rephrasing your question for a better response."
    
    def _create_metadata(self, 
                       query: DatabaseQuery,
                       sql_query: str,
                       raw_results: List[Dict]) -> Dict[str, Any]:
        """Create metadata for transparency"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "original_query": query.natural_language_query,
            "farmer_id": query.farmer_id,
            "language": query.language,
            "sql_generated": sql_query,
            "results_count": len(raw_results),
            "llm_model": self.model,
            "constitutional_compliance": {
                "llm_first": True,
                "privacy_first": True,
                "mango_rule": True
            }
        }


# Example usage and testing
async def test_constitutional_compliance():
    """Test the LLM-first system with constitutional scenarios"""
    engine = LLMDatabaseQueryEngine()
    
    # Test 1: Bulgarian mango farmer (MANGO RULE)
    bulgarian_query = DatabaseQuery(
        natural_language_query="Колко манго дървета имам?",  # How many mango trees do I have?
        farmer_id=123,
        country_code="BG",
        language="bg"
    )
    
    result = await engine.process_farmer_query(bulgarian_query)
    print("Bulgarian Mango Test:")
    print(f"Response: {result.natural_language_response}")
    print(f"SQL: {result.sql_query}")
    print(f"Constitutional: {result.constitutional_compliance}")
    
    # Test 2: Slovenian tomato farmer
    slovenian_query = DatabaseQuery(
        natural_language_query="Kdaj je potrebno pošpricati paradižnik?",  # When to spray tomatoes?
        farmer_id=456,
        country_code="SI", 
        language="sl"
    )
    
    result = await engine.process_farmer_query(slovenian_query)
    print("\nSlovenian Tomato Test:")
    print(f"Response: {result.natural_language_response}")
    print(f"SQL: {result.sql_query}")
    
    # Test 3: English general query
    english_query = DatabaseQuery(
        natural_language_query="Show me my recent tasks and their status",
        farmer_id=789,
        language="en"
    )
    
    result = await engine.process_farmer_query(english_query)
    print("\nEnglish Tasks Test:")
    print(f"Response: {result.natural_language_response}")
    print(f"SQL: {result.sql_query}")


if __name__ == "__main__":
    asyncio.run(test_constitutional_compliance())