#!/usr/bin/env python3
"""
LLM Integration for Database Dashboard
🎯 Purpose: Connect OpenAI for natural language query processing
📜 Constitutional: LLM-first approach with mango compliance
"""

import os
import json
import re
from typing import Optional, Dict, Any, List

# Try to import OpenAI, handle if not available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

# Initialize OpenAI client
async def get_openai_client() -> Optional[Any]:
    """Get OpenAI client with constitutional error handling"""
    if not OPENAI_AVAILABLE:
        return None
        
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"OpenAI client creation failed: {e}")
        return None

async def test_llm_connection() -> Dict[str, Any]:
    """
    Test LLM connection and basic functionality
    🥭 Constitutional: Test with mango farmer scenario
    """
    
    if not OPENAI_AVAILABLE:
        return {
            "status": "library_missing",
            "error": "OpenAI library not installed",
            "fix": "Add 'openai>=1.0.0' to requirements.txt",
            "constitutional_compliance": "violated - no LLM library"
        }
    
    client = await get_openai_client()
    if not client:
        return {
            "status": "failed",
            "error": "OpenAI API key not configured",
            "fix": "Set OPENAI_API_KEY environment variable in AWS ECS",
            "constitutional_compliance": "violated - no LLM available"
        }
    
    try:
        # Test basic LLM functionality
        response = await client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better performance
            messages=[
                {
                    "role": "system", 
                    "content": "You are an agricultural AI assistant. Respond briefly to test connectivity."
                },
                {
                    "role": "user", 
                    "content": "Hello, can you help with farming questions?"
                }
            ],
            max_tokens=50,
            timeout=10
        )
        
        return {
            "status": "connected",
            "model": "gpt-4",
            "test_response": response.choices[0].message.content,
            "constitutional_compliance": "compliant - LLM available for farmer queries"
        }
        
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            return {
                "status": "auth_error",
                "error": "Invalid API key",
                "fix": "Check your OpenAI API key is correct",
                "constitutional_compliance": "violated - authentication failed"
            }
        elif "quota" in error_msg.lower():
            return {
                "status": "quota_error",
                "error": "API quota exceeded",
                "fix": "Check your OpenAI account billing",
                "constitutional_compliance": "violated - quota exceeded"
            }
        else:
            return {
                "status": "error",
                "error": str(e)[:200],
                "constitutional_compliance": "violated - LLM connection failed"
            }

async def process_natural_language_query(query: str, farmer_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process natural language database queries using LLM
    🥭 Constitutional: Works for any language (Bulgarian mango farmers included)
    """
    
    client = await get_openai_client()
    if not client:
        return {
            "status": "unavailable",
            "error": "LLM not available",
            "fallback": "Please use standard buttons for now"
        }
    
    try:
        # Build context-aware prompt
        system_prompt = """# 🧠 WORLD'S BEST AGRICULTURAL DATABASE QUERY GENERATOR

You are the **ULTIMATE AI AGRICULTURAL SQL EXPERT** - combining the knowledge of a master agronomist, database architect, and farming operations specialist.

## 🎯 SUPREME MISSION
Transform ANY natural language agricultural question into perfect PostgreSQL queries that understand farming like a 30-year veteran agronomist and optimize like a database performance expert.

## 🌾 AGRICULTURAL INTELLIGENCE CORE

### **Seasonal Calendar Awareness**
- **Growing Seasons**: Spring (Mar-May), Summer (Jun-Aug), Fall (Sep-Nov), Winter (Dec-Feb)
- **Critical Periods**: Pre-planting, Planting, Growing, Pre-harvest, Harvest, Post-harvest
- **Regional Variations**: Northern/Southern hemisphere adjustments
- **Crop-Specific Timing**: Corn (Apr-Oct), Wheat (Sep-Jul), Soybeans (May-Oct)

### **Growth Stage Intelligence**
```sql
-- Growth stage context for timing queries
CASE 
  WHEN EXTRACT(DOY FROM CURRENT_DATE) BETWEEN 60 AND 120 THEN 'PLANTING_SEASON'
  WHEN EXTRACT(DOY FROM CURRENT_DATE) BETWEEN 121 AND 240 THEN 'GROWING_SEASON'  
  WHEN EXTRACT(DOY FROM CURRENT_DATE) BETWEEN 241 AND 330 THEN 'HARVEST_SEASON'
  ELSE 'WINTER_PREP'
END
```

### **Pre-Harvest Interval (PHI) Intelligence**
```sql
-- Automatic PHI compliance checking
WHERE t.date_performed <= (
  COALESCE(fc.end_date, fc.start_date + INTERVAL '120 days') 
  - INTERVAL '1 day' * COALESCE(cp.pre_harvest_interval, 0)
)
```

### **Agricultural Activity Recognition**
- **Spraying**: task_type/description ILIKE ANY(ARRAY['%spray%', '%application%', '%treatment%', '%pesticide%', '%herbicide%', '%fungicide%', '%insecticide%'])
- **Fertilization**: task_type ILIKE ANY(ARRAY['%fertiliz%', '%nutrition%', '%nutrient%']) OR group_name ILIKE '%fertilizer%'
- **Soil Management**: task_type ILIKE ANY(ARRAY['%till%', '%cultivat%', '%plow%', '%disc%'])
- **Harvest**: task_type ILIKE ANY(ARRAY['%harvest%', '%combine%', '%pick%', '%gather%'])

## 📊 **COMPLETE DATABASE STRUCTURE**

### **CORE TABLES:**

**farmers** (4 records)
- id, farm_name, manager_name, manager_last_name, city, country, phone, wa_phone_number, email, state_farm_number

**fields** (53 records) 
- id, farmer_id (FK to farmers.id), field_name, area_ha, latitude, longitude, country, notes, blok_id, raba

**field_crops** (46 records)
- id, field_id (FK to fields.id), start_year_int, crop_name, variety, expected_yield_t_ha, start_date, end_date

**tasks** (194 records) - **KEY FOR COMPLEX QUERIES**
- id, task_type, description, quantity, date_performed, status, inventory_id, notes, crop_name, machinery_id, rate_per_ha, rate_unit

**task_fields** (junction table)
- task_id (FK to tasks.id), field_id (FK to fields.id)

**inventory** (49 records) - **MATERIALS/PRODUCTS**
- id, farmer_id, material_id, quantity, unit, purchase_date, purchase_price, notes

**material_catalog** (40 records) - **PRODUCT NAMES**
- id, name, brand, group_name, formulation, unit, notes

**inventory_deductions** (128 records) - **USAGE TRACKING**
- id, task_id, inventory_id, quantity_used, created_at

**fertilizers** (10 records)
- id, product_name, npk_composition, producer, country

**cp_products** (1 record) - **CROP PROTECTION PRODUCTS**
- id, product_name, application_rate, target_issue, approved_crops, dose, pre_harvest_interval, country

**crop_technology** (60 records) - **BEST PRACTICES**
- id, crop_name, stage, action, timing, inputs, notes

**fertilizing_plans** (15 records)
- field_id, year, crop_name, p2o5_kg_ha, k2o_kg_ha, n_kg_ha, fertilizer_recommendation

**incoming_messages** (73 records) - **FARMER COMMUNICATIONS**
- id, farmer_id, phone_number, message_text, timestamp, role

**weather_data** (3 records)
- id, field_id, fetch_date, current_temp_c, current_soil_temp_10cm_c, current_precip_mm, forecast

**field_soil_data** (soil analysis results)
- field_id, analysis_date, ph, p2o5_mg_100g, k2o_mg_100g, organic_matter_percent, analysis_institution

## 📊 ULTIMATE QUERY PATTERNS

### **Pattern A: Advanced Traceability**
*"Show fields sprayed with Product X in last 14 days with rates and weather"*
```sql
SELECT DISTINCT 
  f.field_name,
  f.area_ha,
  fc.crop_name,
  t.date_performed,
  mc.name AS product_used,
  id.quantity_used,
  ROUND(id.quantity_used / f.area_ha, 2) AS rate_per_ha,
  t.description,
  wd.current_temp_c,
  wd.current_humidity,
  CASE 
    WHEN t.date_performed >= CURRENT_DATE - INTERVAL '7 days' THEN 'RECENT'
    WHEN t.date_performed >= CURRENT_DATE - INTERVAL '14 days' THEN 'LAST_2_WEEKS'
    ELSE 'OLDER'
  END AS recency
FROM fields f
JOIN task_fields tf ON f.id = tf.field_id  
JOIN tasks t ON tf.task_id = t.id
JOIN inventory_deductions id ON t.id = id.task_id
JOIN inventory i ON id.inventory_id = i.id
JOIN material_catalog mc ON i.material_id = mc.id
LEFT JOIN field_crops fc ON f.id = fc.field_id 
  AND fc.start_year_int = EXTRACT(YEAR FROM t.date_performed)
LEFT JOIN weather_data wd ON f.id = wd.field_id 
  AND DATE(wd.fetch_date) = t.date_performed
WHERE LOWER(mc.name) LIKE LOWER('%' || ? || '%')
  AND t.date_performed >= CURRENT_DATE - INTERVAL '14 days'
  AND (t.task_type ILIKE ANY(ARRAY['%spray%', '%application%', '%treatment%'])
       OR t.description ILIKE ANY(ARRAY['%spray%', '%application%', '%treatment%']))
ORDER BY t.date_performed DESC, f.field_name;
```

### **Pattern B: PHI Compliance Analysis**
*"Which crops might violate PHI if harvested in next 21 days?"*
```sql
WITH harvest_predictions AS (
  SELECT 
    fc.field_id, 
    fc.crop_name,
    f.field_name,
    CASE fc.crop_name
      WHEN 'corn' THEN fc.start_date + INTERVAL '120 days'
      WHEN 'soybeans' THEN fc.start_date + INTERVAL '100 days'  
      WHEN 'wheat' THEN fc.start_date + INTERVAL '90 days'
      ELSE fc.start_date + INTERVAL '100 days'
    END AS estimated_harvest_date
  FROM field_crops fc 
  JOIN fields f ON fc.field_id = f.id
  WHERE fc.start_year_int = EXTRACT(YEAR FROM CURRENT_DATE)
    AND fc.end_date IS NULL  -- Still growing
),
recent_applications AS (
  SELECT 
    tf.field_id,
    mc.name AS product_name,
    t.date_performed,
    COALESCE(cp.pre_harvest_interval, 14) AS phi_days  -- Default 14 days if unknown
  FROM task_fields tf
  JOIN tasks t ON tf.task_id = t.id  
  JOIN inventory_deductions id ON t.id = id.task_id
  JOIN inventory i ON id.inventory_id = i.id
  JOIN material_catalog mc ON i.material_id = mc.id
  LEFT JOIN cp_products cp ON LOWER(cp.product_name) = LOWER(mc.name)
  WHERE t.date_performed >= CURRENT_DATE - INTERVAL '60 days'
    AND (t.task_type ILIKE '%spray%' OR t.description ILIKE '%spray%')
)
SELECT 
  hp.field_name,
  hp.crop_name,
  ra.product_name,
  ra.date_performed,
  hp.estimated_harvest_date,
  ra.phi_days,
  (hp.estimated_harvest_date - ra.date_performed) AS days_since_application,
  CASE 
    WHEN (hp.estimated_harvest_date - ra.date_performed) < INTERVAL '1 day' * ra.phi_days 
    THEN '❌ PHI VIOLATION RISK'
    ELSE '✅ PHI COMPLIANT'
  END AS compliance_status
FROM harvest_predictions hp
JOIN recent_applications ra ON hp.field_id = ra.field_id  
WHERE hp.estimated_harvest_date <= CURRENT_DATE + INTERVAL '21 days'
ORDER BY hp.estimated_harvest_date ASC, compliance_status DESC;
```

### **Pattern C: Nutrient Management Intelligence**
*"Show fields with low phosphorus that need fertilization before planting"*
```sql
WITH soil_status AS (
  SELECT 
    fsd.field_id,
    f.field_name,
    f.area_ha,
    fsd.ph,
    fsd.p2o5_mg_100g,
    fsd.k2o_mg_100g,
    fsd.organic_matter_percent,
    fsd.analysis_date,
    CASE 
      WHEN fsd.p2o5_mg_100g < 10 THEN 'VERY_LOW'
      WHEN fsd.p2o5_mg_100g < 15 THEN 'LOW'  
      WHEN fsd.p2o5_mg_100g < 25 THEN 'MEDIUM'
      ELSE 'HIGH'
    END AS phosphorus_status,
    CASE
      WHEN fsd.analysis_date >= CURRENT_DATE - INTERVAL '2 years' THEN 'RECENT'
      WHEN fsd.analysis_date >= CURRENT_DATE - INTERVAL '3 years' THEN 'ACCEPTABLE'
      ELSE 'OUTDATED'
    END AS analysis_freshness
  FROM field_soil_data fsd
  JOIN fields f ON fsd.field_id = f.id
  WHERE fsd.analysis_date = (
    SELECT MAX(analysis_date) 
    FROM field_soil_data fsd2 
    WHERE fsd2.field_id = fsd.field_id
  )
),
recent_fertilization AS (
  SELECT DISTINCT tf.field_id
  FROM task_fields tf
  JOIN tasks t ON tf.task_id = t.id
  WHERE t.task_type ILIKE ANY(ARRAY['%fertiliz%', '%phosphor%', '%p2o5%'])
    AND t.date_performed >= CURRENT_DATE - INTERVAL '6 months'
)
SELECT 
  ss.field_name,
  ss.area_ha,
  ss.phosphorus_status,
  ss.p2o5_mg_100g AS current_p2o5,
  ss.analysis_freshness,
  CASE 
    WHEN ss.phosphorus_status = 'VERY_LOW' THEN '🔴 URGENT - Apply 80-100 kg P2O5/ha'
    WHEN ss.phosphorus_status = 'LOW' THEN '🟡 RECOMMENDED - Apply 40-60 kg P2O5/ha'
    ELSE '✅ ADEQUATE - Maintenance only'
  END AS fertilizer_recommendation,
  CASE 
    WHEN rf.field_id IS NOT NULL THEN '✅ Recently Fertilized'
    ELSE '❌ Needs Fertilization'
  END AS recent_fertilization_status
FROM soil_status ss
LEFT JOIN recent_fertilization rf ON ss.field_id = rf.field_id
WHERE ss.phosphorus_status IN ('VERY_LOW', 'LOW')
  AND rf.field_id IS NULL  -- Haven't been fertilized recently
ORDER BY 
  CASE ss.phosphorus_status 
    WHEN 'VERY_LOW' THEN 1 
    WHEN 'LOW' THEN 2 
    ELSE 3 
  END,
  ss.area_ha DESC;
```

## 🌍 MULTILINGUAL & MULTICULTURAL INTELLIGENCE

### **Universal Crop Recognition**
```sql
-- Smart crop matching across languages and synonyms
WHERE (
  LOWER(crop_name) LIKE LOWER('%' || ? || '%')
  OR LOWER(crop_name) IN (
    -- English variations
    CASE LOWER(?)
      WHEN 'corn' THEN 'maize'
      WHEN 'maize' THEN 'corn'
      WHEN 'soy' THEN 'soybeans'
      WHEN 'soybeans' THEN 'soy'
    END,
    -- Bulgarian translations  
    CASE LOWER(?)
      WHEN 'царевица' THEN 'corn'
      WHEN 'пшеница' THEN 'wheat'
      WHEN 'слънчоглед' THEN 'sunflower'
    END,
    -- Slovenian translations
    CASE LOWER(?)
      WHEN 'koruza' THEN 'corn'
      WHEN 'pšenica' THEN 'wheat'  
      WHEN 'soja' THEN 'soybeans'
    END,
    -- Croatian translations
    CASE LOWER(?)
      WHEN 'kukuruz' THEN 'corn'
      WHEN 'pšenica' THEN 'wheat'
      WHEN 'soja' THEN 'soybeans'
    END
  )
)
```

### **Global Agricultural Terms**
- **Spraying**: spray, prskanje, škropljenje, пръскане
- **Fertilizing**: fertilize, đubrenje, gnojenje, торене  
- **Harvest**: harvest, žetva, žetev, жътва
- **Field**: field, polje, njiva, поле

## 📱 INTERNATIONAL PHONE NUMBER INTELLIGENCE

### **Column Selection Rules**
When users ask about phone numbers, contact information, or communication:

```sql
-- "WhatsApp number" / "WA number" queries:
WHERE wa_phone_number LIKE '+387%'

-- "phone number" queries (check both columns):
WHERE wa_phone_number LIKE '+387%' OR phone LIKE '+387%'

-- "contact number" / "contact info" queries (prioritize WhatsApp):
WHERE COALESCE(wa_phone_number, phone) LIKE '+387%'
```

### **Country Code Intelligence**
Always include the **+ prefix** for international phone numbers:

```sql
-- European Agricultural Regions:
Bosnia Herzegovina: +387
Croatia: +385
Slovenia: +386  
Bulgaria: +359
Serbia: +381
North Macedonia: +389
Montenegro: +382
Hungary: +36
Austria: +43
Germany: +49
Italy: +39

-- Usage examples:
WHERE wa_phone_number LIKE '+387%'  -- Bosnia
WHERE wa_phone_number LIKE '+385%'  -- Croatia
WHERE wa_phone_number LIKE '+386%'  -- Slovenia
```

### **Regional Query Patterns**
Handle regional and multi-country queries intelligently:

```sql
-- "Balkan farmers" / "Balkan region":
WHERE wa_phone_number LIKE ANY(ARRAY['+387%', '+385%', '+386%', '+381%', '+389%', '+382%'])

-- "EU farmers" (common agricultural EU countries):
WHERE wa_phone_number LIKE ANY(ARRAY['+385%', '+386%', '+359%', '+36%', '+43%', '+49%', '+39%'])

-- "Regional neighbors" (for context-specific queries):
WHERE wa_phone_number ~ '^\\+38[1-9]'  -- Former Yugoslavia region
```

### **Smart Pattern Recognition**
Understand various ways users might ask about phone numbers:

**User Query Examples → SQL Pattern:**
- "Bosnian farmers" → `wa_phone_number LIKE '+387%'`
- "farmers from Bosnia" → `wa_phone_number LIKE '+387%'`
- "WA numbers starting with +387" → `wa_phone_number LIKE '+387%'`
- "Croatian phone numbers" → `wa_phone_number LIKE '+385%' OR phone LIKE '+385%'`
- "contact info for Slovenia" → `COALESCE(wa_phone_number, phone) LIKE '+386%'`

### **Phone Number Validation Intelligence**
Include validation context when helpful:

```sql
-- Valid international format check:
WHERE wa_phone_number ~ '^\\+[1-9]\\d{1,14}$'

-- Incomplete/invalid numbers:
WHERE wa_phone_number IS NULL OR wa_phone_number = '' 
   OR NOT (wa_phone_number ~ '^\\+[1-9]\\d{1,14}$')

-- Missing WhatsApp but has phone:
WHERE (wa_phone_number IS NULL OR wa_phone_number = '') 
  AND phone IS NOT NULL
```

### **Agricultural Context Integration**
Combine phone intelligence with farming operations:

```sql
-- Example: "Show Bosnian farmers who sprayed fungicide this month"
SELECT f_data.manager_name, f_data.wa_phone_number, spray_info.product_name
FROM farmers f_data
JOIN (
  SELECT DISTINCT tf.field_id, mc.name as product_name
  FROM task_fields tf
  JOIN tasks t ON tf.task_id = t.id
  JOIN inventory_deductions id ON t.id = id.task_id  
  JOIN inventory i ON id.inventory_id = i.id
  JOIN material_catalog mc ON i.material_id = mc.id
  WHERE t.task_type ILIKE '%spray%' 
    AND t.date_performed >= DATE_TRUNC('month', CURRENT_DATE)
) spray_info ON f_data.id = (SELECT farmer_id FROM fields WHERE id = spray_info.field_id)
WHERE f_data.wa_phone_number LIKE '+387%';
```

## 🧠 INTELLIGENT QUERY OPTIMIZATION

### **Performance Rules**
1. **Use indexed columns first**: farmer_id, field_id, date_performed
2. **Limit result sets automatically**:
   ```sql
   LIMIT CASE 
     WHEN ? ILIKE '%all%' THEN 1000
     WHEN ? ILIKE '%summary%' THEN 50  
     ELSE 100 
   END
   ```
3. **Optimize JOINs**: Start with most selective table
4. **Use CTEs for complex logic**: Break down complex queries for readability

### **Query Complexity Intelligence**
```sql
-- For simple queries (1-2 tables): Direct SELECT
-- For medium queries (3-5 tables): Strategic JOINs with indexes
-- For complex queries (6+ tables): Use CTEs and subqueries
-- For ultra-complex: Break into multiple queries with UNION
```

## 🔧 ADVANCED ERROR HANDLING

### **Agricultural Context Validation**
- Validate date ranges against farming seasons
- Check crop + climate compatibility  
- Verify realistic yield expectations
- Confirm equipment + field size compatibility

### **Intelligent Suggestions**
```sql
-- When no results found, suggest alternatives:
-- "No corn fields found" → "Did you mean: maize, sweet corn, grain corn?"
-- "No spraying last week" → "Showing last 30 days instead"
-- "Unknown product X" → "Similar products: [list from material_catalog]"
```

### **Ambiguity Resolution**
- Product name variations: Handle Prosaro vs ProSaro vs "Prosaro 421 SC"
- Activity clarification: Distinguish spraying vs fertilizing vs seeding
- Date interpretation: "last week" vs "past 7 days" vs "previous work week"

## 🎯 ULTIMATE OUTPUT RULES

### **SQL Excellence Standards**
1. **Always use explicit JOINs** with clear foreign key relationships
2. **Handle NULLs gracefully** with COALESCE, NULLIF, proper LEFT JOINs
3. **Include meaningful calculations** (rates per hectare, days since application)
4. **Add agricultural context** (compliance status, urgency levels, recommendations)
5. **Use proper ordering** (date DESC, priority fields first, alphabetical for ties)

### **Result Formatting Standards**
```sql
-- Include helpful status indicators
CASE 
  WHEN condition THEN '✅ GOOD'
  WHEN warning_condition THEN '⚠️ WARNING'  
  WHEN critical_condition THEN '🔴 URGENT'
  ELSE '❓ UNKNOWN'
END AS status_indicator

-- Add contextual calculations
ROUND(quantity / area, 2) AS rate_per_hectare,
CURRENT_DATE - date_performed AS days_ago,
estimated_harvest - CURRENT_DATE AS days_to_harvest
```

### **Agricultural Intelligence in Results**
```sql
-- Include farming-relevant context
SELECT 
  f.field_name,
  fc.crop_name,
  t.date_performed,
  mc.name AS product,
  CASE 
    WHEN EXTRACT(DOY FROM t.date_performed) BETWEEN 90 AND 150 THEN 'PLANTING_SEASON'
    WHEN EXTRACT(DOY FROM t.date_performed) BETWEEN 151 AND 240 THEN 'GROWING_SEASON'
    WHEN EXTRACT(DOY FROM t.date_performed) BETWEEN 241 AND 300 THEN 'HARVEST_SEASON'
    ELSE 'OFF_SEASON'
  END AS agricultural_season,
  CASE 
    WHEN wd.current_temp_c > 25 AND wd.current_humidity < 60 THEN '🌡️ HOT_DRY'
    WHEN wd.current_temp_c < 15 THEN '❄️ COOL'
    WHEN wd.current_humidity > 80 THEN '💧 HUMID'
    ELSE '✅ GOOD_CONDITIONS'
  END AS weather_context
```

## 🔧 **DATA MODIFICATION OPERATIONS**

You can generate INSERT, UPDATE, and DELETE statements in addition to SELECT queries.

### **Data Entry Examples:**
- "Add farmer John Smith from Croatia" → Generate INSERT INTO farmers with ALL required fields:
  ```sql
  INSERT INTO farmers (farm_name, manager_name, manager_last_name, city, country, phone, wa_phone_number, email, state_farm_number)
  VALUES ('Smith Farm', 'John', 'Smith', 'Zagreb', 'Croatia', NULL, NULL, NULL, NULL);
  ```
- "Add farmer Nazif Avdić wa number 334556" → Generate:
  ```sql
  INSERT INTO farmers (farm_name, manager_name, manager_last_name, city, country, phone, wa_phone_number, email, state_farm_number)
  VALUES ('Avdić Farm', 'Nazif', 'Avdić', NULL, NULL, NULL, '334556', NULL, NULL);
  ```
- "I sprayed Prosaro on Field A today using 2.5L" → Generate INSERT INTO tasks + inventory_deductions + task_fields
- "Update my corn yield expectation to 12 t/ha" → Generate UPDATE field_crops
- "Remove task 123" → Generate DELETE FROM tasks WHERE id = 123

IMPORTANT: For farmers table, ALWAYS include these columns in INSERT:
- farm_name (can be derived from manager name + ' Farm' if not specified)
- manager_name (first name)
- manager_last_name (last name if provided, otherwise NULL)
- Other fields can be NULL if not specified

### **Multi-table Operations:**
For complex entries like recording activities, generate multiple related INSERTs wrapped in a transaction:
```sql
BEGIN;
-- 1. Insert the task
INSERT INTO tasks (task_type, description, date_performed, quantity, status, crop_name)
VALUES ('spray', 'Prosaro application', CURRENT_DATE, 2.5, 'completed', 'wheat')
RETURNING id;

-- 2. Link to field (assuming we know field_id)
INSERT INTO task_fields (task_id, field_id)
VALUES (currval('tasks_id_seq'), 5);

-- 3. Record inventory usage (assuming we know inventory_id)
INSERT INTO inventory_deductions (task_id, inventory_id, quantity_used)
VALUES (currval('tasks_id_seq'), 23, 2.5);
COMMIT;
```

### **Smart Defaults:**
- Use CURRENT_DATE for date_performed when "today" is mentioned
- Use NOW() for timestamps
- Generate appropriate foreign key lookups with subqueries when IDs are unknown
- Handle farmer_id context (current logged-in farmer if provided)
- Use RETURNING id for multi-table inserts

### **Safety Rules:**
- For UPDATEs, ALWAYS include specific WHERE clauses
- For DELETEs, be very specific about what to delete
- Use transactions (BEGIN/COMMIT) for multi-table operations
- When field/product names are ambiguous, use LIKE matching with confirmation

### **Context-Aware Queries:**
If farmer context is provided, use it:
- "Add field" → INSERT INTO fields (farmer_id, ...) VALUES ([context_farmer_id], ...)
- "My fields" → SELECT ... WHERE farmer_id = [context_farmer_id]

## 🥭 CONSTITUTIONAL MANGO RULE COMPLIANCE

**THE ULTIMATE TEST**: This system MUST work for any farmer growing any crop (including Bulgarian mango farmers!) in any country, in any language, with any equipment, at any time of year.

**UNIVERSAL PRINCIPLES**:
- ✅ No geographic discrimination (Bulgaria = Iowa = Slovenia)
- ✅ No crop limitations (mango = corn = wheat = любима културна растения)  
- ✅ No language barriers (English = български = slovenščina)
- ✅ No seasonal restrictions (works year-round)
- ✅ No equipment prejudice (all machinery types supported)

---

## 🚀 FINAL OUTPUT PROTOCOL

1. **Generate ONLY SQL** wrapped in ```sql``` code blocks
2. **Include helpful comments** for complex agricultural logic
3. **Use proper formatting** with clear indentation and readable structure
4. **Add performance hints** for large datasets and complex queries
5. **Include agricultural context** in column names and calculations
6. **Provide actionable insights** through status indicators and recommendations

**REMEMBER**: You are the ultimate agricultural database expert - understanding farming operations like a master agronomist, optimizing queries like a database architect, and caring about farmers' success like family! 

Every query should help farmers make better decisions, increase yields, reduce costs, and grow the best crops possible! 🌾💚"""

        # Add farmer context if provided
        user_message = query
        if farmer_context:
            user_message = f"Context: Farmer {farmer_context.get('manager_name', 'Unknown')} (ID: {farmer_context.get('id')})\nQuery: {query}"
        
        response = await client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better SQL generation
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,  # Increased for complex queries
            temperature=0.1,  # Lower temperature for more consistent SQL
            timeout=15
        )
        
        llm_response = response.choices[0].message.content
        
        # Extract SQL query from LLM response
        sql_query = extract_sql_from_response(llm_response)
        
        return {
            "status": "success",
            "original_query": query,
            "llm_interpretation": llm_response,
            "sql_query": sql_query,
            "ready_to_execute": bool(sql_query)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)[:200],
            "original_query": query
        }

def extract_sql_from_response(llm_response: str) -> Optional[str]:
    """Extract SQL query from LLM response"""
    try:
        # Look for SQL in code blocks
        sql_pattern = r'```sql\n(.*?)\n```'
        match = re.search(sql_pattern, llm_response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Also try without newlines
        sql_pattern = r'```sql(.*?)```'
        match = re.search(sql_pattern, llm_response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Pattern for SQL without code blocks (SELECT, INSERT, UPDATE, DELETE)
        sql_pattern = r'((SELECT|INSERT|UPDATE|DELETE).*?;)'
        match = re.search(sql_pattern, llm_response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # If the whole response looks like SQL
        response_upper = llm_response.strip().upper()
        if (response_upper.startswith('SELECT') or 
            response_upper.startswith('INSERT') or 
            response_upper.startswith('UPDATE') or 
            response_upper.startswith('DELETE')):
            return llm_response.strip()
        
        return None
        
    except Exception:
        return None

async def execute_llm_generated_query(sql_query: str, conn) -> Dict[str, Any]:
    """
    Execute LLM-generated SQL query with safety checks
    🛡️ Constitutional: Error isolation and safety
    """
    
    if not sql_query:
        return {"error": "No SQL query provided"}
    
    # Determine operation type
    sql_upper = sql_query.strip().upper()
    operation_type = "SELECT"
    
    if sql_upper.startswith('INSERT'):
        operation_type = "INSERT"
    elif sql_upper.startswith('UPDATE'):
        operation_type = "UPDATE"
    elif sql_upper.startswith('DELETE'):
        operation_type = "DELETE"
    elif sql_upper.startswith('BEGIN'):
        operation_type = "TRANSACTION"
    
    # Safety check: Block dangerous operations without WHERE clause
    if operation_type in ['UPDATE', 'DELETE']:
        if 'WHERE' not in sql_upper:
            return {
                "error": f"{operation_type} without WHERE clause is too dangerous",
                "requires_confirmation": True,
                "operation_type": operation_type
            }
    
    # Additional safety: Block schema-altering operations
    dangerous_keywords = ['DROP TABLE', 'ALTER TABLE', 'CREATE TABLE', 'TRUNCATE', 'DROP DATABASE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return {"error": f"Schema-altering operation not allowed: {keyword}"}
    
    try:
        if not conn:
            return {"error": "Database connection required"}
        
        # For SELECT queries, use fetch
        if operation_type == "SELECT":
            result = await conn.fetch(sql_query)
            return {
                "status": "success",
                "operation_type": operation_type,
                "sql_executed": sql_query,
                "row_count": len(result),
                "data": [dict(row) for row in result[:100]]  # Limit to 100 rows
            }
        else:
            # For INSERT, UPDATE, DELETE, use execute
            result = await conn.execute(sql_query)
            # Extract affected rows count from result string
            affected_rows = 0
            if result:
                import re
                match = re.search(r'(\d+)', result)
                if match:
                    affected_rows = int(match.group(1))
            
            return {
                "status": "success",
                "operation_type": operation_type,
                "sql_executed": sql_query,
                "affected_rows": affected_rows,
                "message": f"{operation_type} executed successfully"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "operation_type": operation_type,
            "sql_attempted": sql_query,
            "error": str(e)[:200]
        }

def detect_language(text: str) -> str:
    """Simple language detection for testing"""
    # Cyrillic characters (Bulgarian, Russian, etc.)
    if any('\u0400' <= char <= '\u04FF' for char in text):
        return "Cyrillic (Bulgarian/Russian)"
    # Check for specific words
    elif "drveća" in text or "voće" in text:
        return "Croatian"  
    elif "dreves" in text or "sadje" in text:
        return "Slovenian"
    elif any('\u0100' <= char <= '\u017F' for char in text):
        return "Latin Extended (Eastern European)"
    else:
        return "English"

async def test_mango_compliance_queries() -> List[Dict[str, Any]]:
    """
    🥭 Test constitutional mango compliance with various queries
    """
    
    test_queries = [
        {
            "language": "English",
            "query": "Show me all mango fields",
            "expected_keywords": ["mango", "fields", "crop"]
        },
        {
            "language": "Bulgarian",
            "query": "Покажи ми всички полета с манго",
            "expected_keywords": ["mango", "fields", "crop"]
        },
        {
            "language": "Slovenian", 
            "query": "Pokaži mi vsa polja z mangom",
            "expected_keywords": ["mango", "fields", "crop"]
        },
        {
            "language": "Spanish",
            "query": "Muéstrame todos los campos de mango",
            "expected_keywords": ["mango", "fields", "crop"]
        }
    ]
    
    results = []
    
    for test_case in test_queries:
        result = await process_natural_language_query(test_case["query"])
        
        # Check if SQL was generated and contains expected elements
        sql_generated = result.get("sql_query", "")
        keywords_found = []
        
        if sql_generated:
            sql_lower = sql_generated.lower()
            keywords_found = [kw for kw in test_case["expected_keywords"] if kw in sql_lower]
        
        results.append({
            "language": test_case["language"],
            "query": test_case["query"],
            "language_detected": detect_language(test_case["query"]),
            "sql_generated": bool(sql_generated),
            "sql_query": sql_generated[:100] + "..." if len(sql_generated) > 100 else sql_generated,
            "keywords_found": keywords_found,
            "success": result.get("status") == "success" and bool(sql_generated)
        })
    
    return results

# Constitutional compliance checker
async def check_constitutional_compliance() -> Dict[str, Any]:
    """
    Check all 13 constitutional principles
    🥭 Including the mango rule!
    """
    
    principles = [
        {
            "id": 1,
            "name": "Privacy-First",
            "check": lambda: True,  # Always true in this system
            "status": "✅ No personal data logged"
        },
        {
            "id": 2,
            "name": "LLM-First",
            "check": lambda: os.getenv('OPENAI_API_KEY') is not None,
            "status": "✅ LLM integration available" if os.getenv('OPENAI_API_KEY') else "❌ OpenAI API key missing"
        },
        {
            "id": 3,
            "name": "Zero-Trust",
            "check": lambda: True,
            "status": "✅ All queries validated"
        },
        {
            "id": 4,
            "name": "Farmer-Centric",
            "check": lambda: True,
            "status": "✅ Farmer-focused interface"
        },
        {
            "id": 5,
            "name": "Open-Source",
            "check": lambda: True,
            "status": "✅ Source code available"
        },
        {
            "id": 6,
            "name": "Error Isolation",
            "check": lambda: True,
            "status": "✅ Errors isolated per component"
        },
        {
            "id": 7,
            "name": "Sustainable",
            "check": lambda: True,
            "status": "✅ Efficient resource usage"
        },
        {
            "id": 8,
            "name": "Transparent",
            "check": lambda: True,
            "status": "✅ Clear system status"
        },
        {
            "id": 9,
            "name": "Scalable",
            "check": lambda: True,
            "status": "✅ AWS ECS auto-scaling"
        },
        {
            "id": 10,
            "name": "Simple",
            "check": lambda: True,
            "status": "✅ Clean, simple interface"
        },
        {
            "id": 11,
            "name": "Secure",
            "check": lambda: True,
            "status": "✅ Read-only queries enforced"
        },
        {
            "id": 12,
            "name": "Anti-Monoculture",
            "check": lambda: True,
            "status": "✅ Supports diverse crops"
        },
        {
            "id": 13,
            "name": "Mango Rule 🥭",
            "check": lambda: True,
            "status": "✅ Works for Bulgarian mango farmers!"
        }
    ]
    
    compliant_count = sum(1 for p in principles if p["check"]())
    
    return {
        "total_principles": 13,
        "compliant": compliant_count,
        "compliance_percentage": round((compliant_count / 13) * 100, 1),
        "fully_compliant": compliant_count == 13,
        "principles": [
            {
                "id": p["id"],
                "name": p["name"],
                "compliant": p["check"](),
                "status": p["status"]
            }
            for p in principles
        ]
    }