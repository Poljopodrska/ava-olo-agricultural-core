"""
Check what tables exist in the AWS RDS database
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '2hpzvrg_xP~qNbz1[_NppSK$e*O1')

print(f"Connecting to AWS RDS database...")
print(f"Host: {DB_HOST}")
print(f"Database: {DB_NAME}")
print(f"User: {DB_USER}")

try:
    # Connect to the database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Get all tables in the public schema
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    
    if tables:
        print(f"\n✅ Successfully connected! Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
    else:
        print("\n⚠️  No tables found in the database!")
        print("\nChecking all schemas:")
        cursor.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name;
        """)
        all_tables = cursor.fetchall()
        for schema, table in all_tables:
            print(f"  - {schema}.{table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error connecting to database: {e}")
    print("\nThis might be because:")
    print("1. You're connecting from local machine (not within AWS VPC)")
    print("2. The database credentials are incorrect")
    print("3. The database needs to be accessed through AWS App Runner")