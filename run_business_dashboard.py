#!/usr/bin/env python3
"""
Business Dashboard Launcher
Detects database schema and runs appropriate version
"""
import os
import psycopg2
from dotenv import load_dotenv
import subprocess
import sys

# Load environment variables
load_dotenv()

def check_database_schema():
    """Check which database schema we have"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', '5432')),
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        
        # Check if we have the agricultural schema (area_ha in fields)
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fields' 
            AND column_name IN ('area_ha', 'area_hectares')
        """)
        
        result = cursor.fetchone()
        
        if result:
            column_name = result[0]
            print(f"✅ Found fields table with column: {column_name}")
            
            # Check for field_crops table (agricultural schema)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'field_crops'
                )
            """)
            
            has_field_crops = cursor.fetchone()[0]
            
            conn.close()
            
            if column_name == 'area_ha' and has_field_crops:
                return 'agricultural'  # Use updated version
            else:
                return 'original'  # Use original version
        
        conn.close()
        return 'unknown'
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return 'unknown'

def main():
    """Main launcher"""
    print("🔍 Checking database schema...")
    
    schema_type = check_database_schema()
    
    if schema_type == 'agricultural':
        print("📊 Using updated business dashboard for agricultural schema")
        script = "business_dashboard_updated.py"
    elif schema_type == 'original':
        print("📊 Using original business dashboard")
        script = "business_dashboard.py"
    else:
        print("⚠️ Could not determine schema, defaulting to updated version")
        script = "business_dashboard_updated.py"
    
    # Run the appropriate dashboard
    print(f"🚀 Starting {script}...")
    try:
        subprocess.run([sys.executable, script])
    except KeyboardInterrupt:
        print("\n👋 Business dashboard stopped")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

if __name__ == "__main__":
    main()