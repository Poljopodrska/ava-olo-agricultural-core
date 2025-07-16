#!/usr/bin/env python3
"""Simple database connection test"""
import psycopg2
import os
from urllib.parse import quote_plus

print("=== Database Connection Test ===\n")

# Get connection details from environment or use defaults
db_host = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'farmer_crm')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', '')

print(f"Host: {db_host}")
print(f"Port: {db_port}")
print(f"Database: {db_name}")
print(f"User: {db_user}")
print(f"Password: {'*' * len(db_password) if db_password else 'NOT_SET'} ({len(db_password)} chars)")

if not db_password:
    print("\n❌ No password set in environment!")
    print("Set DB_PASSWORD environment variable and try again.")
    exit(1)

# Try direct connection
print("\n1. Testing direct psycopg2 connection...")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        sslmode='require'
    )
    print("✅ Direct connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Direct connection failed: {e}")

# Try URL-encoded connection string
print("\n2. Testing URL-encoded connection string...")
try:
    password_encoded = quote_plus(db_password)
    conn_string = f"postgresql://{db_user}:{password_encoded}@{db_host}:{db_port}/{db_name}?sslmode=require"
    print(f"Connection string: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}?sslmode=require")
    
    conn = psycopg2.connect(conn_string)
    print("✅ URL-encoded connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ URL-encoded connection failed: {e}")

print("\n=== Troubleshooting Tips ===")
print("1. Check RDS security group allows connections from your IP/service")
print("2. Verify the password is correct in AWS RDS")
print("3. Ensure RDS instance is publicly accessible if connecting from outside VPC")
print("4. Check if password contains special characters that need escaping")