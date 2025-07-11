#!/usr/bin/env python3
"""
Migrate database structure from local Windows PostgreSQL to AWS RDS
Only copies the schema (tables, columns, constraints) - not the data
"""
import subprocess
import os
from datetime import datetime

# Source database (Windows local)
SOURCE_DB = {
    "host": "localhost",
    "port": "5432",
    "database": "farmer_crm",
    "user": "postgres",
    "password": "password"
}

# Target database (AWS RDS)
TARGET_DB = {
    "host": "farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com",
    "port": "5432",
    "database": "postgres",
    "user": "postgres",
    "password": "2hpzvrg_xP~qNbz1[_NppSK$e*O1"
}

def main():
    print("🚀 Database Structure Migration Tool")
    print("=" * 50)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    schema_file = f"farmer_crm_schema_{timestamp}.sql"
    
    print(f"\n1️⃣ Exporting schema from local database...")
    
    # Export only the schema (no data) from Windows PostgreSQL
    export_cmd = [
        "pg_dump",
        "-h", SOURCE_DB["host"],
        "-p", SOURCE_DB["port"],
        "-U", SOURCE_DB["user"],
        "-d", SOURCE_DB["database"],
        "--schema-only",  # Only structure, no data
        "--no-owner",     # Don't include ownership
        "--no-privileges", # Don't include privileges
        "-f", schema_file
    ]
    
    # Set password for source
    env = os.environ.copy()
    env["PGPASSWORD"] = SOURCE_DB["password"]
    
    try:
        result = subprocess.run(export_cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Schema exported successfully to {schema_file}")
            
            # Show what tables were found
            with open(schema_file, 'r') as f:
                content = f.read()
                tables = [line.split()[2] for line in content.split('\n') if line.startswith('CREATE TABLE')]
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables[:10]:  # Show first 10
                    print(f"   - {table}")
                if len(tables) > 10:
                    print(f"   ... and {len(tables) - 10} more")
        else:
            print(f"❌ Export failed: {result.stderr}")
            return
    except Exception as e:
        print(f"❌ Error during export: {e}")
        return
    
    print(f"\n2️⃣ Ready to import to AWS RDS")
    print(f"   Target: {TARGET_DB['host']}")
    print(f"   Database: {TARGET_DB['database']}")
    
    # Note: Direct import to RDS won't work from local machine due to VPC
    print("\n⚠️  Cannot directly import from local machine to RDS (VPC restrictions)")
    print("\n📌 Next steps:")
    print(f"1. The schema has been saved to: {schema_file}")
    print("2. You can either:")
    print("   a) Use AWS RDS Query Editor in AWS Console to run the SQL")
    print("   b) Use a bastion host or EC2 instance within the VPC")
    print("   c) Temporarily make RDS publicly accessible (not recommended)")
    print("\n💡 For option (a), copy the contents of the SQL file and paste in RDS Query Editor")
    
    # Create a simplified version for easy copy-paste
    simple_file = f"farmer_crm_tables_simple_{timestamp}.sql"
    print(f"\n3️⃣ Creating simplified SQL file for easy import: {simple_file}")
    
    with open(schema_file, 'r') as f:
        content = f.read()
    
    # Extract only CREATE TABLE statements
    lines = content.split('\n')
    create_statements = []
    in_create = False
    current_statement = []
    
    for line in lines:
        if line.strip().startswith('CREATE TABLE'):
            in_create = True
            current_statement = [line]
        elif in_create:
            current_statement.append(line)
            if line.strip().endswith(';'):
                create_statements.append('\n'.join(current_statement))
                in_create = False
                current_statement = []
    
    with open(simple_file, 'w') as f:
        f.write("-- Farmer CRM Database Tables\n")
        f.write("-- Generated from Windows PostgreSQL\n")
        f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write('\n\n'.join(create_statements))
    
    print(f"✅ Simplified SQL file created: {simple_file}")
    print("\n🎯 Quick start:")
    print("1. Open AWS RDS Query Editor")
    print("2. Connect to your RDS instance")
    print(f"3. Copy and paste the contents of {simple_file}")
    print("4. Execute the SQL")
    
if __name__ == "__main__":
    main()