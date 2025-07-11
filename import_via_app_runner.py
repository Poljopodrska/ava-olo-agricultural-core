#!/usr/bin/env python3
"""
Import database schema to AWS RDS via App Runner
This script can be run from App Runner which has VPC access
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def import_schema():
    # Read the SQL file
    with open('farmer_crm_aws_ready.sql', 'r') as f:
        sql_content = f.read()
    
    # Connect to AWS RDS
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    
    # Split SQL into individual statements
    statements = []
    current = []
    
    for line in sql_content.split('\n'):
        if line.strip().startswith('--'):
            continue
        if line.strip():
            current.append(line)
        if line.strip().endswith(';') and not any(keyword in ' '.join(current).upper() for keyword in ['CREATE OR REPLACE FUNCTION', 'CREATE FUNCTION']):
            if current:
                statements.append(' '.join(current))
                current = []
    
    # Execute each statement
    success_count = 0
    error_count = 0
    
    with engine.connect() as conn:
        for i, stmt in enumerate(statements):
            try:
                if stmt.strip() and not stmt.strip().startswith('--'):
                    conn.execute(text(stmt))
                    conn.commit()
                    success_count += 1
                    if 'CREATE TABLE' in stmt:
                        table_name = stmt.split('CREATE TABLE')[1].split('(')[0].strip().strip('"')
                        print(f"✅ Created table: {table_name}")
            except Exception as e:
                error_count += 1
                print(f"❌ Error on statement {i}: {str(e)[:100]}")
                conn.rollback()
    
    print(f"\n📊 Import complete: {success_count} successful, {error_count} errors")
    
    # List final tables
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = result.fetchall()
        print(f"\n📋 Tables in database ({len(tables)} total):")
        for table in tables:
            print(f"   - {table[0]}")

if __name__ == "__main__":
    import_schema()