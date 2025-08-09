#!/usr/bin/env python3
"""
Debug script to check why Edi's fields aren't showing in FAVA
This can be run on the server or used to generate debug queries
"""
import os
import sys

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_debug_queries():
    """Generate SQL queries to debug Edi's context"""
    
    queries = []
    
    # 1. Find all Edis
    queries.append({
        "name": "Find all farmers named Edi",
        "sql": """
            SELECT id, manager_name, manager_last_name, wa_phone_number, phone, 
                   farm_name, city, country, created_at
            FROM farmers 
            WHERE LOWER(manager_name) LIKE '%edi%' 
               OR LOWER(manager_last_name) LIKE '%kante%'
            ORDER BY created_at DESC;
        """
    })
    
    # 2. Check fields for Edi Kante specifically
    queries.append({
        "name": "Get Edi Kante's fields",
        "sql": """
            SELECT f.*, fa.manager_name, fa.manager_last_name
            FROM fields f
            JOIN farmers fa ON f.farmer_id = fa.id
            WHERE LOWER(fa.manager_name) LIKE '%edi%' 
               AND LOWER(fa.manager_last_name) LIKE '%kante%';
        """
    })
    
    # 3. Check if phone number format is an issue
    queries.append({
        "name": "Check phone number formats",
        "sql": """
            SELECT id, manager_name, wa_phone_number, phone,
                   LENGTH(wa_phone_number) as wa_len,
                   LENGTH(phone) as phone_len
            FROM farmers 
            WHERE LOWER(manager_name) LIKE '%edi%'
            LIMIT 10;
        """
    })
    
    # 4. Check fields table structure
    queries.append({
        "name": "Fields table structure",
        "sql": """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'fields' 
            ORDER BY ordinal_position;
        """
    })
    
    # 5. Count fields per farmer
    queries.append({
        "name": "Count fields per farmer",
        "sql": """
            SELECT fa.id, fa.manager_name, fa.manager_last_name, 
                   COUNT(f.id) as field_count,
                   SUM(f.area_ha) as total_hectares
            FROM farmers fa
            LEFT JOIN fields f ON f.farmer_id = fa.id
            WHERE LOWER(fa.manager_name) LIKE '%edi%'
            GROUP BY fa.id, fa.manager_name, fa.manager_last_name
            ORDER BY field_count DESC;
        """
    })
    
    # 6. Check recent FAVA logs for Edi
    queries.append({
        "name": "Recent chat messages for Edi's phone",
        "sql": """
            SELECT session_id, role, content, timestamp
            FROM chat_messages
            WHERE session_id IN (
                SELECT wa_phone_number FROM farmers 
                WHERE LOWER(manager_name) LIKE '%edi%'
            )
            ORDER BY timestamp DESC
            LIMIT 20;
        """
    })
    
    # 7. Debug what FAVA sees
    queries.append({
        "name": "Simulate FAVA context query",
        "sql": """
            -- First get farmer ID for a phone number
            WITH farmer_lookup AS (
                SELECT id, manager_name, wa_phone_number
                FROM farmers 
                WHERE wa_phone_number = '+38651300564' -- Replace with actual number
                   OR phone = '+38651300564'
                LIMIT 1
            )
            SELECT 
                fl.id as farmer_id,
                fl.manager_name,
                fl.wa_phone_number,
                f.id as field_id,
                f.field_name,
                f.area_ha
            FROM farmer_lookup fl
            LEFT JOIN fields f ON f.farmer_id = fl.id;
        """
    })
    
    return queries

def print_debug_info():
    """Print debug information and queries"""
    print("=" * 80)
    print("EDI CONTEXT DEBUG QUERIES")
    print("=" * 80)
    print("\nRun these queries in the database to debug why Edi's fields aren't showing:\n")
    
    queries = generate_debug_queries()
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. {query['name']}")
        print("-" * 40)
        print(query['sql'])
        print()
    
    print("\n" + "=" * 80)
    print("DEBUGGING CHECKLIST")
    print("=" * 80)
    print("""
    1. ✓ Check if Edi exists in farmers table
    2. ✓ Check if Edi has fields in fields table
    3. ✓ Check if farmer_id foreign key is correct
    4. ✓ Check if WhatsApp phone number matches
    5. ✓ Check if FAVA is getting the correct farmer_id
    6. ✓ Check if context loading queries are working
    7. ✓ Check Redis connection (should fallback to DB)
    8. ✓ Check logs for errors
    """)
    
    print("\n" + "=" * 80)
    print("POSSIBLE ISSUES")
    print("=" * 80)
    print("""
    1. Phone number format mismatch (with/without +, spaces, etc.)
    2. farmer_id not being passed correctly to FAVA
    3. Database connection issues in production
    4. Fields table has different column names than expected
    5. FAVA context query is failing silently
    6. Language detection interfering with context loading
    """)

if __name__ == "__main__":
    print_debug_info()
    
    # Try to import and test locally if possible
    try:
        from modules.core.simple_db import execute_simple_query
        
        print("\n" + "=" * 80)
        print("ATTEMPTING LOCAL DATABASE TEST")
        print("=" * 80)
        
        # Try a simple query
        result = execute_simple_query(
            "SELECT COUNT(*) as farmer_count FROM farmers WHERE LOWER(manager_name) LIKE '%edi%'",
            ()
        )
        
        if result.get('success'):
            count = result['rows'][0][0] if result['rows'] else 0
            print(f"✅ Found {count} farmers named Edi in database")
        else:
            print(f"❌ Database query failed: {result.get('error')}")
            
    except Exception as e:
        print(f"⚠️  Cannot connect to database from local: {e}")
        print("\nPlease run these queries directly on the production database or check CloudWatch logs")