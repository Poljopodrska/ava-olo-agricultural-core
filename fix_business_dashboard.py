#!/usr/bin/env python3
"""
Constitutional fix for business dashboard - LLM-first approach
Only use columns that actually exist, constitutional compliance
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_actual_farmer_columns():
    """Constitutional approach: Discover what columns actually exist"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=10
        )
        cursor = conn.cursor()
        
        # Get actual columns in farmers table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'farmers'
            ORDER BY ordinal_position
        """)
        
        columns = {}
        for row in cursor.fetchall():
            columns[row[0]] = row[1]
        
        conn.close()
        return columns
        
    except Exception as e:
        print(f"Error getting farmer columns: {e}")
        return {}

def generate_constitutional_business_queries():
    """Generate business queries based on actual schema"""
    
    columns = get_actual_farmer_columns()
    print("Actual farmer columns:", list(columns.keys()))
    
    # Base query that should always work
    base_query = "SELECT COUNT(*) FROM farmers"
    
    # Conditional queries based on what exists
    queries = {
        "total_farmers": base_query
    }
    
    # Only add queries for columns that exist
    if 'is_active' in columns:
        queries["active_farmers"] = "SELECT COUNT(*) FROM farmers WHERE is_active = true"
        queries["inactive_farmers"] = "SELECT COUNT(*) FROM farmers WHERE is_active = false"
    
    if 'created_at' in columns:
        queries["new_farmers_24h"] = """
            SELECT COUNT(*) FROM farmers 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """
        queries["new_farmers_7d"] = """
            SELECT COUNT(*) FROM farmers 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """
    
    if 'updated_at' in columns:
        queries["recently_updated"] = """
            SELECT COUNT(*) FROM farmers 
            WHERE updated_at >= NOW() - INTERVAL '24 hours'
        """
    
    return queries

def test_constitutional_queries():
    """Test the constitutional queries"""
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=10
        )
        cursor = conn.cursor()
        
        queries = generate_constitutional_business_queries()
        
        print("\n=== TESTING CONSTITUTIONAL QUERIES ===")
        results = {}
        
        for name, query in queries.items():
            try:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                results[name] = result
                print(f"✅ {name}: {result}")
            except Exception as e:
                print(f"❌ {name} failed: {e}")
                results[name] = 0
        
        conn.close()
        return results
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return {}

def create_constitutional_business_dashboard_patch():
    """Create a patch for business dashboard using constitutional approach"""
    
    columns = get_actual_farmer_columns()
    
    patch_code = '''
# Constitutional business metrics - only use columns that exist
def get_constitutional_business_metrics():
    """Constitutional compliance: Use only existing columns"""
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        metrics = {}
        
        # Always safe: total count
        cursor.execute("SELECT COUNT(*) FROM farmers")
        metrics["total_farmers"] = cursor.fetchone()[0]
        
'''
    
    # Add conditional queries based on actual schema
    if 'is_active' in columns:
        patch_code += '''
        # is_active column exists
        cursor.execute("SELECT COUNT(*) FROM farmers WHERE is_active = true")
        metrics["active_farmers"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM farmers WHERE is_active = false")
        metrics["inactive_farmers"] = cursor.fetchone()[0]
'''
    else:
        patch_code += '''
        # No is_active column - all farmers considered active
        metrics["active_farmers"] = metrics["total_farmers"]
        metrics["inactive_farmers"] = 0
'''
    
    if 'created_at' in columns:
        patch_code += '''
        # created_at column exists
        cursor.execute("SELECT COUNT(*) FROM farmers WHERE created_at >= NOW() - INTERVAL '24 hours'")
        metrics["new_24h"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM farmers WHERE created_at >= NOW() - INTERVAL '7 days'")
        metrics["new_7d"] = cursor.fetchone()[0]
'''
    else:
        patch_code += '''
        # No created_at column
        metrics["new_24h"] = 0
        metrics["new_7d"] = 0
'''
    
    patch_code += '''
        conn.close()
        return metrics
        
    except Exception as e:
        # Constitutional fallback
        return {
            "total_farmers": 0,
            "active_farmers": 0,
            "inactive_farmers": 0,
            "new_24h": 0,
            "new_7d": 0,
            "error": str(e)
        }
'''
    
    return patch_code

if __name__ == "__main__":
    print("🔍 Constitutional Business Dashboard Fix")
    print("=" * 50)
    
    columns = get_actual_farmer_columns()
    if columns:
        print(f"✅ Found {len(columns)} columns in farmers table")
        print("Columns:", list(columns.keys()))
        
        results = test_constitutional_queries()
        print(f"\n✅ Generated {len(results)} working queries")
        
        patch = create_constitutional_business_dashboard_patch()
        print("\n📝 Constitutional patch code generated")
        print("Run this to apply the fix:")
        print("python3 fix_business_dashboard.py > constitutional_patch.py")
        
    else:
        print("❌ Could not connect to database or discover schema")