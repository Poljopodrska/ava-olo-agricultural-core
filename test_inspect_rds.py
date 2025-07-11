#!/usr/bin/env python3
"""
Test script for RDS inspection functionality
"""
import json
from inspect_rds import RDSInspector

def test_rds_inspection():
    """Test the RDS inspection functionality"""
    print("🔍 Testing RDS Database Inspector")
    print("=" * 50)
    
    try:
        # Initialize inspector
        inspector = RDSInspector()
        
        # Test 1: Get schema list
        print("\n📋 Test 1: Getting schema list...")
        schemas = inspector.get_schema_list()
        print(f"   Found {len(schemas)} schemas: {', '.join(schemas)}")
        
        # Test 2: Get tables in public schema
        print("\n📋 Test 2: Getting tables in 'public' schema...")
        tables = inspector.get_table_list('public')
        print(f"   Found {len(tables)} tables in public schema")
        if tables:
            print("   First 5 tables:")
            for table in tables[:5]:
                print(f"     - {table['name']} ({table['size']})")
        
        # Test 3: Quick inspection (limited)
        print("\n📋 Test 3: Running quick database inspection...")
        # For testing, we'll just check the structure without full inspection
        with inspector.get_session() as session:
            # Check if we can connect
            result = session.execute("SELECT version()").scalar()
            print(f"   PostgreSQL version: {result.split(',')[0]}")
            
            # Count schemas
            schema_count = session.execute("""
                SELECT COUNT(*) FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            """).scalar()
            print(f"   User schemas: {schema_count}")
            
            # Count tables in public
            table_count = session.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """).scalar()
            print(f"   Tables in public schema: {table_count}")
            
            # Check for non-public tables
            non_public_count = session.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast') 
                AND table_type = 'BASE TABLE'
            """).scalar()
            print(f"   Tables outside public schema: {non_public_count}")
        
        print("\n✅ All tests passed! The RDS inspector is working correctly.")
        print("\nℹ️  To run full inspection, use: python3 inspect_rds.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_rds_inspection()
    exit(0 if success else 1)