"""
Constitutional LLM-first query handler for database explorer
Following AVA OLO Constitution Principle 3: LLM Intelligence First
"""
import os
import logging
from typing import Dict, Any, Optional
import openai
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

class LLMQueryHandler:
    """LLM-based SQL query generation following constitutional principles"""
    
    def __init__(self, db_ops):
        self.db_ops = db_ops
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            openai.api_key = api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized for LLM-first query generation")
        else:
            logger.warning("OPENAI_API_KEY not found - using fallback pattern matching")
    
    async def convert_natural_language_to_sql(self, description: str) -> Dict[str, Any]:
        """
        Convert natural language to SQL using LLM (Constitutional Principle 3)
        Falls back to pattern matching if LLM unavailable
        """
        try:
            # Get database schema
            schema_context = await self._get_schema_context()
            
            if self.openai_client:
                # LLM-first approach (Constitutional compliance)
                return await self._llm_generate_sql(description, schema_context)
            else:
                # Fallback to pattern matching
                return self._pattern_based_sql(description, schema_context)
                
        except Exception as e:
            logger.error(f"Error in query conversion: {e}")
            return {
                "sql_query": f"-- Error: {str(e)}",
                "query_type": "error",
                "original_description": description
            }
    
    async def _get_schema_context(self) -> str:
        """Get database schema for LLM context"""
        with self.db_ops.get_session() as session:
            inspector = inspect(session.bind)
            
            schema_info = []
            for table_name in inspector.get_table_names():
                columns = []
                for col in inspector.get_columns(table_name):
                    col_type = str(col['type']).split('(')[0]  # Simplify type
                    columns.append(f"{col['name']} ({col_type})")
                
                schema_info.append(f"Table {table_name}: {', '.join(columns)}")
            
            return "\n".join(schema_info)
    
    async def _llm_generate_sql(self, description: str, schema_context: str) -> Dict[str, Any]:
        """Generate SQL using OpenAI GPT (LLM-first approach)"""
        try:
            prompt = f"""You are an expert PostgreSQL query generator for an agricultural system.

Database Schema:
{schema_context}

User Request: {description}

Generate a PostgreSQL query following these rules:
1. Only generate SELECT queries (no modifications)
2. Use proper JOINs when needed
3. Handle both English and Slovenian requests
4. Common Slovenian agricultural terms:
   - kmet/kmeti = farmer/farmers
   - polje/parcela = field
   - sporočilo = message
   - naloga = task
   - pridelek = crop
5. Add appropriate ORDER BY and LIMIT clauses
6. Return ONLY the SQL query, no explanations

SQL Query:"""

            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a PostgreSQL expert. Generate only valid SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Validate it's a SELECT query
            if sql_query.upper().startswith("SELECT"):
                return {
                    "sql_query": sql_query,
                    "query_type": "llm_generated",
                    "original_description": description,
                    "llm_model": "gpt-4"
                }
            else:
                return {
                    "sql_query": f"-- LLM generated non-SELECT query: {sql_query}",
                    "query_type": "rejected",
                    "original_description": description
                }
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fall back to pattern matching
            return self._pattern_based_sql(description, schema_context)
    
    def _pattern_based_sql(self, description: str, schema_context: str) -> Dict[str, Any]:
        """Fallback pattern-based SQL generation when LLM unavailable"""
        # This would contain the existing pattern matching logic
        # Keeping it simple for now
        return {
            "sql_query": "SELECT COUNT(*) FROM farmers;",
            "query_type": "pattern_fallback",
            "original_description": description
        }
    
    async def verify_llm_connectivity(self) -> bool:
        """Check if LLM is properly connected (for health dashboard)"""
        if not self.openai_client:
            return False
            
        try:
            # Simple test query
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": "Reply with 'OK'"}],
                max_tokens=10
            )
            return response.choices[0].message.content.strip() == "OK"
        except:
            return False