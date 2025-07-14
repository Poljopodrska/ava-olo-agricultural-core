#!/usr/bin/env python3
"""
Simple Aurora connection test using psycopg2 (same as existing code)
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_manager import config

def test_connection():
    """Test Aurora connection using psycopg2 - same as monitoring dashboards"""
    print("🔍 Testing Aurora RDS Connection...")
    print(f"Host: {config.db_host}")
    print(f"Database: {config.db_name}")
    print(f"User: {config.db_user}")
    print(f"Port: {config.db_port}")
    
    connection = None
    
    # Strategy 1: Try with SSL required (AWS RDS default)
    if not connection:
        try:
            print("🔌 Attempting connection with SSL required...")
            connection = psycopg2.connect(
                host=config.db_host,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                port=config.db_port,
                connect_timeout=10,
                sslmode='require'
            )
            print("✅ Connected with SSL required")
        except psycopg2.OperationalError as ssl_error:
            print(f"   SSL required failed: {ssl_error}")
    
    # Strategy 2: Try with SSL preferred
    if not connection:
        try:
            print("🔌 Attempting connection with SSL preferred...")
            connection = psycopg2.connect(
                host=config.db_host,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                port=config.db_port,
                connect_timeout=10,
                sslmode='prefer'
            )
            print("✅ Connected with SSL preferred")
        except psycopg2.OperationalError as ssl_error:
            print(f"   SSL preferred failed: {ssl_error}")
    
    # Strategy 3: Try without SSL
    if not connection:
        try:
            print("🔌 Attempting connection without SSL...")
            connection = psycopg2.connect(
                host=config.db_host,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                port=config.db_port,
                connect_timeout=10,
                sslmode='disable'
            )
            print("✅ Connected without SSL")
        except Exception as e:
            print(f"❌ All connection attempts failed: {e}")
            return False
    
    if connection:
        try:
            # Test query
            cur = connection.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"PostgreSQL version: {version[0]}")
            
            # Check if farmers table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'farmers'
                );
            """)
            farmers_exists = cur.fetchone()[0]
            print(f"Farmers table exists: {farmers_exists}")
            
            # Check for authentication tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('farm_users', 'farm_activity_log')
            """)
            existing_auth_tables = cur.fetchall()
            if existing_auth_tables:
                print(f"⚠️  Existing auth tables: {[t[0] for t in existing_auth_tables]}")
            else:
                print("✅ No existing auth tables - safe to create")
            
            cur.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False

if __name__ == "__main__":
    test_connection()