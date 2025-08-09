"""
Constitutional LLM-first query handler for database explorer
Following AVA OLO Constitution Principle 3: LLM Intelligence First
Enhanced with farming context intelligence and entity relationship understanding
"""
import os
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import inspect

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class LLMQueryHandler:
    """LLM-based SQL query generation with farming context intelligence"""
    
    def __init__(self, db_ops):
        self.db_ops = db_ops
        self.openai_client = None
        
        # Initialize OpenAI client if API key and module are available
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and OPENAI_AVAILABLE:
            openai.api_key = api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized for LLM-first query generation")
        elif not OPENAI_AVAILABLE:
            logger.warning("OpenAI module not installed - using fallback pattern matching")
        else:
            logger.warning("OPENAI_API_KEY not found - using fallback pattern matching")
    
    def _extract_person_names(self, query: str) -> List[str]:
        """Extract potential person names from query (capitalized words)"""
        # Pattern for potential names: Capitalized words, allowing for multi-word names
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        potential_names = re.findall(name_pattern, query)
        
        # Filter out common SQL/farming keywords that might be capitalized
        excluded_words = {'Select', 'From', 'Where', 'Join', 'Field', 'Fields', 'Crop', 'Crops', 'Task', 'Tasks'}
        return [name for name in potential_names if name not in excluded_words]
    
    def _detect_relationship_patterns(self, query: str) -> Tuple[str, str]:
        """Detect farming relationship patterns in query"""
        query_lower = query.lower()
        
        # Define relationship patterns
        patterns = {
            "farmer_to_fields": [
                r"fields?\s+of\s+", r"fields?\s+for\s+", r"fields?\s+belonging\s+to\s+",
                r"'s\s+fields?", r"owns?\s+which\s+fields?"
            ],
            "farmer_to_crops": [
                r"crops?\s+of\s+", r"crops?\s+for\s+", r"what\s+(?:is|are)\s+.*\s+growing",
                r"'s\s+crops?", r"plants?\s+grown\s+by"
            ],
            "farmer_to_tasks": [
                r"tasks?\s+by\s+", r"tasks?\s+for\s+", r"work\s+done\s+by",
                r"'s\s+tasks?", r"activities\s+of"
            ],
            "field_to_crops": [
                r"crops?\s+in\s+", r"planted\s+in\s+", r"growing\s+in\s+"
            ],
            "direct_farmer_search": [
                r"farmer\s+named\s+", r"farmer\s+called\s+", r"find\s+farmer\s+"
            ]
        }
        
        for relationship_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, query_lower):
                    return relationship_type, pattern
        
        return "unknown", ""
    
    def _preprocess_query(self, query: str, schema_context: str) -> Dict[str, Any]:
        """Analyze query for farming entities and relationships before LLM processing"""
        # Extract potential person names
        potential_names = self._extract_person_names(query)
        
        # Detect relationship patterns
        relationship_type, pattern_found = self._detect_relationship_patterns(query)
        
        # Analyze if query likely involves farmer lookup
        involves_farmer = (
            len(potential_names) > 0 or
            relationship_type in ["farmer_to_fields", "farmer_to_crops", "farmer_to_tasks", "direct_farmer_search"]
        )
        
        return {
            "original_query": query,
            "potential_farmer_names": potential_names,
            "relationship_type": relationship_type,
            "pattern_found": pattern_found,
            "involves_farmer_lookup": involves_farmer,
            "schema_context": schema_context
        }
    
    async def convert_natural_language_to_sql(self, description: str) -> Dict[str, Any]:
        """
        Convert natural language to SQL using enhanced LLM with farming context
        Falls back to pattern matching if LLM unavailable
        """
        try:
            # Get database schema
            schema_context = await self._get_schema_context()
            
            # Preprocess query to detect farming relationships
            preprocessed = self._preprocess_query(description, schema_context)
            
            if self.openai_client:
                # Enhanced LLM approach with farming intelligence
                result = await self._llm_generate_sql_enhanced(preprocessed)
                
                # Check if clarification is needed
                if result.get("needs_clarification"):
                    return result
                
                return result
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
    
    async def _llm_generate_sql_enhanced(self, preprocessed: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL using OpenAI GPT with enhanced farming context intelligence"""
        try:
            # Build enhanced prompt with farming relationship understanding
            enhanced_prompt = self._build_enhanced_prompt(preprocessed)
            
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a PostgreSQL expert for agricultural systems with deep understanding of farming entity relationships."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Check for ambiguity and need for clarification
            ambiguity_check = await self._check_ambiguity(
                preprocessed["original_query"], 
                sql_query,
                preprocessed
            )
            
            if ambiguity_check.get("needs_clarification"):
                return ambiguity_check
            
            # Validate it's a SELECT query
            if sql_query.upper().startswith("SELECT"):
                return {
                    "sql_query": sql_query,
                    "query_type": "llm_generated_enhanced",
                    "original_description": preprocessed["original_query"],
                    "llm_model": "gpt-4",
                    "farming_context_used": True,
                    "detected_relationship": preprocessed["relationship_type"],
                    "potential_farmers": preprocessed["potential_farmer_names"]
                }
            else:
                return {
                    "sql_query": f"-- LLM generated non-SELECT query: {sql_query}",
                    "query_type": "rejected",
                    "original_description": preprocessed["original_query"]
                }
                
        except Exception as e:
            logger.error(f"Enhanced LLM generation failed: {e}")
            # Fall back to basic LLM generation
            return await self._llm_generate_sql_basic(
                preprocessed["original_query"], 
                preprocessed["schema_context"]
            )
    
    def _build_enhanced_prompt(self, preprocessed: Dict[str, Any]) -> str:
        """Build enhanced prompt with farming context intelligence"""
        prompt = f"""You are an agricultural database expert. Generate PostgreSQL queries with deep understanding of farming relationships.

CRITICAL FARMING ENTITY RELATIONSHIPS:
- Farmers OWN fields (farmers.id → fields.farmer_id)
- Fields CONTAIN crops (fields.id → field_crops.field_id)
- Farmers PERFORM tasks (via fields: farmers.id → fields.farmer_id → tasks.field_id)
- Tasks happen ON fields (tasks.field_id → fields.id)

SEMANTIC INTERPRETATION RULES:
- "fields of [PersonName]" = Find farmer named PersonName, then list their fields
- "crops of [PersonName]" = Find farmer's fields, then crops in those fields
- "tasks by [PersonName]" = Find farmer's tasks through their fields
- "[PersonName]'s farm" = All data related to that farmer
- Person names in queries usually refer to farmers (manager_name or manager_last_name columns)

DATABASE SCHEMA:
{preprocessed['schema_context']}

QUERY ANALYSIS:
- Original Query: "{preprocessed['original_query']}"
- Detected Potential Farmer Names: {preprocessed['potential_farmer_names']}
- Detected Relationship Type: {preprocessed['relationship_type']}
- Likely Involves Farmer Lookup: {preprocessed['involves_farmer_lookup']}

IMPORTANT EXAMPLES:
- "list fields of Edi Kante" should generate:
  SELECT f.* FROM fields f 
  JOIN farmers farm ON f.farmer_id = farm.id 
  WHERE farm.manager_name ILIKE '%Edi%' 
  AND farm.manager_last_name ILIKE '%Kante%'
  
- "what are edi kante's fields" should generate:
  SELECT f.field_name, f.area_ha FROM fields f 
  JOIN farmers farm ON f.farmer_id = farm.id 
  WHERE farm.manager_name ILIKE '%edi%' 
  AND farm.manager_last_name ILIKE '%kante%'

- "show crops for Peter" should generate:
  SELECT fc.*, f.field_name FROM field_crops fc 
  JOIN fields f ON fc.field_id = f.id 
  JOIN farmers farm ON f.farmer_id = farm.id 
  WHERE farm.manager_name ILIKE '%Peter%'

CRITICAL RULES FOR NAME MATCHING:
1. NEVER use exact match (=) for person names - ALWAYS use ILIKE '%name%'
2. NEVER use lowercase exact match like = 'edi' - ALWAYS use ILIKE '%edi%'
3. Person names are CASE-INSENSITIVE - always use ILIKE, not =
4. Example: WHERE manager_name ILIKE '%edi%' NOT WHERE manager_name = 'edi'

ADDITIONAL RULES:
1. Only generate SELECT queries (no modifications)
2. When searching for person names, ALWAYS use ILIKE with % wildcards
3. Handle both English and Slovenian terms (kmet=farmer, polje=field, pridelek=crop)
4. Include appropriate JOINs when relationships are implied
5. Add ORDER BY and LIMIT where appropriate
6. Search in manager_name and manager_last_name columns for person names

Generate the SQL query (ONLY the query, no explanations):"""
        
        return prompt
    
    async def _llm_generate_sql_basic(self, description: str, schema_context: str) -> Dict[str, Any]:
        """Fallback to basic LLM SQL generation (original method)"""
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
    
    async def _check_ambiguity(self, query: str, sql: str, preprocessed: Dict) -> Dict[str, Any]:
        """Check if generated SQL might be ambiguous and need clarification"""
        try:
            # Quick heuristic checks before calling LLM
            query_lower = query.lower()
            sql_lower = sql.lower()
            
            # If we detected a person name and relationship but SQL doesn't have farmer join
            if (preprocessed["potential_farmer_names"] and 
                preprocessed["relationship_type"] in ["farmer_to_fields", "farmer_to_crops"] and
                "join farmers" not in sql_lower):
                
                # Use LLM to generate clarification
                clarification_prompt = f"""The user asked: "{query}"
                We detected they might be looking for a farmer named: {preprocessed['potential_farmer_names']}
                But the generated SQL searches in the wrong table.
                
                Generate a clarifying question to ask the user (be concise):"""
                
                response = await self.openai_client.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Generate helpful clarifying questions."},
                        {"role": "user", "content": clarification_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=100
                )
                
                return {
                    "needs_clarification": True,
                    "clarification_question": response.choices[0].message.content.strip(),
                    "query_type": "needs_clarification",
                    "original_description": query,
                    "suggestion": f"Did you mean to search for farmer '{' '.join(preprocessed['potential_farmer_names'])}' and their fields?"
                }
            
            return {"needs_clarification": False}
            
        except Exception as e:
            logger.error(f"Ambiguity check failed: {e}")
            # If ambiguity check fails, proceed with the query
            return {"needs_clarification": False}
    
    def _pattern_based_sql(self, description: str, schema_context: str) -> Dict[str, Any]:
        """Enhanced fallback pattern-based SQL generation when LLM unavailable"""
        description_lower = description.lower()
        
        # Preprocess to detect patterns
        preprocessed = self._preprocess_query(description, schema_context)
        
        # Handle specific patterns for farming relationships
        if "edi kante" in description_lower:
            if "field" in description_lower:
                # "list fields of Edi Kante" pattern
                sql_query = """
                SELECT f.id, f.field_name, f.area_ha, f.country,
                       fa.manager_name, fa.manager_last_name
                FROM fields f
                JOIN farmers fa ON f.farmer_id = fa.id
                WHERE (LOWER(fa.manager_name) LIKE '%edi%' 
                       OR LOWER(fa.manager_last_name) LIKE '%kante%')
                """
            else:
                # General search for Edi Kante
                sql_query = """
                SELECT * FROM farmers 
                WHERE LOWER(manager_name) LIKE '%edi%' 
                   OR LOWER(manager_last_name) LIKE '%kante%'
                """
        
        elif preprocessed["relationship_type"] == "farmer_to_fields" and preprocessed["potential_farmer_names"]:
            # Generic "fields of [Person]" pattern
            farmer_name = preprocessed["potential_farmer_names"][0]
            name_parts = farmer_name.split()
            where_conditions = []
            for part in name_parts:
                where_conditions.append(f"(LOWER(fa.manager_name) LIKE '%{part.lower()}%' OR LOWER(fa.manager_last_name) LIKE '%{part.lower()}%')")
            
            sql_query = f"""
            SELECT f.id, f.field_name, f.area_ha, f.country,
                   fa.manager_name, fa.manager_last_name
            FROM fields f
            JOIN farmers fa ON f.farmer_id = fa.id
            WHERE {' OR '.join(where_conditions)}
            """
        
        elif "how many farmers" in description_lower:
            sql_query = "SELECT COUNT(*) as total_farmers FROM farmers"
        
        elif "all farmers" in description_lower or "list farmers" in description_lower:
            sql_query = "SELECT * FROM farmers ORDER BY id DESC LIMIT 100"
        
        elif "all fields" in description_lower or "list fields" in description_lower:
            sql_query = """
            SELECT f.*, fa.manager_name, fa.manager_last_name
            FROM fields f
            LEFT JOIN farmers fa ON f.farmer_id = fa.id
            ORDER BY f.id DESC LIMIT 100
            """
        
        else:
            # Default fallback
            sql_query = "SELECT COUNT(*) as total_farmers FROM farmers"
        
        return {
            "sql_query": sql_query.strip(),
            "query_type": "pattern_fallback_enhanced",
            "original_description": description,
            "detected_relationship": preprocessed.get("relationship_type"),
            "potential_farmers": preprocessed.get("potential_farmer_names", [])
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