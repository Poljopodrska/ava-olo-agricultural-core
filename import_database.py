#!/usr/bin/env python3
import psycopg2
import os
import sys

# RDS Connection Details
RDS_CONFIG = {
    'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
    'database': 'postgres',
    'user': 'postgres', 
    'password': '2hpzvrg_xP~qNbz1[_NppSK$e*O1',
    'port': 5432
}

def import_database_schema():
    print("🚀 Starting database import...")
    
    try:
        # Connect to RDS
        print("📡 Connecting to RDS...")
        conn = psycopg2.connect(**RDS_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to: {version[0]}")
        
        # Read SQL file
        print("📂 Reading SQL file...")
        with open('farmer_crm_aws_ready.sql', 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        print(f"📄 SQL file size: {len(sql_content)} characters")
        
        # Split SQL into individual statements to handle errors better
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            # Skip comments
            if line.strip().startswith('--'):
                continue
            
            current_statement.append(line)
            
            # End of statement
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                if statement and not statement.startswith('--'):
                    statements.append(statement)
                current_statement = []
        
        print(f"📋 Found {len(statements)} SQL statements to execute")
        
        # Execute statements one by one
        successful = 0
        failed = 0
        tables_created = []
        
        for i, statement in enumerate(statements):
            try:
                # Skip certain PostgreSQL-specific commands that might fail
                if any(skip in statement.upper() for skip in [
                    'SET STATEMENT_TIMEOUT',
                    'SET LOCK_TIMEOUT', 
                    'SELECT PG_CATALOG',
                    'SET CHECK_FUNCTION_BODIES',
                    'SET XMLOPTION',
                    'SET CLIENT_MIN_MESSAGES',
                    'SET ROW_SECURITY',
                    'SET DEFAULT_TABLE_ACCESS_METHOD',
                    'COMMENT ON SCHEMA'
                ]):
                    continue
                
                cursor.execute(statement)
                successful += 1
                
                # Track table creations
                if 'CREATE TABLE' in statement.upper():
                    # Extract table name
                    parts = statement.split()
                    for j, part in enumerate(parts):
                        if part.upper() == 'TABLE':
                            table_name = parts[j+1].strip('"').split('.')[-1]
                            tables_created.append(table_name)
                            print(f"  ✓ Created table: {table_name}")
                            break
                            
            except psycopg2.Error as e:
                failed += 1
                print(f"  ⚠️ Statement {i+1} failed: {str(e)[:100]}")
                # Continue with next statement
                continue
        
        print(f"\n📊 Execution summary:")
        print(f"  - Successful statements: {successful}")
        print(f"  - Failed statements: {failed}")
        print(f"  - Tables created: {len(tables_created)}")
        
        # Verify tables created
        print("\n🔍 Verifying tables in database...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 Database now contains {len(tables)} tables:")
        
        for table in tables[:10]:  # Show first 10
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table[0]} ({count} rows)")
        
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more tables")
        
        print("\n🎉 Database schema import completed!")
        print("🔗 Database ready at: farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except FileNotFoundError:
        print("❌ SQL file 'farmer_crm_aws_ready.sql' not found")
        print("📌 Make sure to upload the SQL file to the ECS environment first")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    success = import_database_schema()
    sys.exit(0 if success else 1)