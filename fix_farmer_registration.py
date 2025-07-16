#!/usr/bin/env python3
"""
Fix farmer registration to use the SAME working database connection as database dashboard
"""

# The WORKING connection method from get_constitutional_db_connection
WORKING_CONNECTION_CODE = '''
# This is the EXACT working connection from main.py database dashboard
import psycopg2
import os
from contextlib import contextmanager

@contextmanager
def get_working_db_connection():
    """Use the EXACT same connection method as the working database dashboard"""
    connection = None
    
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        print(f"DEBUG: Attempting connection to {host}:{port}/{database} as {user}")
        
        # Strategy 1: Try with SSL required (AWS RDS default)
        if not connection:
            try:
                connection = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='require'
                )
                print("DEBUG: Connected with SSL required")
            except psycopg2.OperationalError as ssl_error:
                print(f"DEBUG: SSL required failed: {ssl_error}")
        
        # Strategy 2: Try with SSL preferred
        if not connection:
            try:
                connection = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='prefer'
                )
                print("DEBUG: Connected with SSL preferred")
            except psycopg2.OperationalError as ssl_pref_error:
                print(f"DEBUG: SSL preferred failed: {ssl_pref_error}")
        
        # Strategy 3: Try connecting to postgres database instead
        if not connection:
            try:
                connection = psycopg2.connect(
                    host=host,
                    database='postgres',  # Try postgres database
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='require'
                )
                print("DEBUG: Connected to postgres database instead")
            except psycopg2.OperationalError as postgres_error:
                print(f"DEBUG: Postgres database connection failed: {postgres_error}")
        
        if connection:
            yield connection
        else:
            yield None
            
    except Exception as e:
        print(f"DEBUG: Connection error: {e}")
        yield None
    finally:
        if connection:
            connection.close()
'''

print("=" * 80)
print("FARMER REGISTRATION DATABASE FIX")
print("=" * 80)

print("\n1. The working database dashboard uses direct psycopg2 connection with:")
print("   - Individual parameters (host, user, password, etc.)")
print("   - Multiple SSL strategies")
print("   - Fallback to 'postgres' database")
print("   - NO URL construction")

print("\n2. The failing farmer registration uses:")
print("   - DATABASE_URL construction")
print("   - SQLAlchemy engine")
print("   - URL encoding for password")

print("\n3. FIX: Update DatabaseOperations to use the working method")

print("\n4. The issue is likely:")
print("   - Password encoding in URL vs direct connection")
print("   - SSL mode handling")
print("   - Database name differences")

print("\n5. To fix farmer registration:")
print("   - Replace the SQLAlchemy connection in DatabaseOperations")
print("   - Use the exact psycopg2 connection method from main.py")
print("   - This is proven to work in the same environment")

print("\n" + "=" * 80)
print("IMPLEMENTATION:")
print("=" * 80)

print(WORKING_CONNECTION_CODE)