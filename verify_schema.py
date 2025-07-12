#!/usr/bin/env python3
"""
Database Schema Verification Script
Constitutional LLM-first approach to discovering actual database structure
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_database_schema():
    """Discover actual database schema - Constitutional LLM-first approach"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'farmer_crm'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Check farmers table columns
        farmers_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'farmers'
        ORDER BY ordinal_position
        """
        
        print("=== FARMERS TABLE SCHEMA ===")
        cursor.execute(farmers_query)
        farmers_schema = cursor.fetchall()
        for row in farmers_schema:
            print(f"Column: {row[0]:<30} Type: {row[1]:<20} Nullable: {row[2]:<5} Default: {row[3]}")
        
        # Check fields table columns  
        fields_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'fields'
        ORDER BY ordinal_position
        """
        
        print("\n=== FIELDS TABLE SCHEMA ===")
        cursor.execute(fields_query)
        fields_schema = cursor.fetchall()
        for row in fields_schema:
            print(f"Column: {row[0]:<30} Type: {row[1]:<20} Nullable: {row[2]:<5} Default: {row[3]}")
        
        # Check conversations table columns
        conversations_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'conversations'
        ORDER BY ordinal_position
        """
        
        print("\n=== CONVERSATIONS TABLE SCHEMA ===")
        cursor.execute(conversations_query)
        conversations_schema = cursor.fetchall()
        for row in conversations_schema:
            print(f"Column: {row[0]:<30} Type: {row[1]:<20} Nullable: {row[2]:<5} Default: {row[3]}")
        
        # Check what tables exist
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        
        print("\n=== AVAILABLE TABLES ===")
        cursor.execute(tables_query)
        tables = cursor.fetchall()
        for table in tables:
            print(f"Table: {table[0]}")
        
        # Check for specific columns that might be causing issues
        print("\n=== CHECKING SPECIFIC COLUMNS ===")
        
        # Check if last_activity exists in farmers
        check_column_query = """
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = 'farmers' AND column_name = 'last_activity'
        """
        cursor.execute(check_column_query)
        has_last_activity = cursor.fetchone()[0] > 0
        print(f"farmers.last_activity exists: {has_last_activity}")
        
        # Check if pending_conversations exists in farmers
        check_column_query = """
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = 'farmers' AND column_name = 'pending_conversations'
        """
        cursor.execute(check_column_query)
        has_pending = cursor.fetchone()[0] > 0
        print(f"farmers.pending_conversations exists: {has_pending}")
        
        # Check if status exists in conversations
        check_column_query = """
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = 'conversations' AND column_name = 'status'
        """
        cursor.execute(check_column_query)
        has_conv_status = cursor.fetchone()[0] > 0
        print(f"conversations.status exists: {has_conv_status}")
        
        # Get sample data to understand structure
        print("\n=== SAMPLE DATA ===")
        cursor.execute("SELECT COUNT(*) FROM farmers")
        farmer_count = cursor.fetchone()[0]
        print(f"Total farmers: {farmer_count}")
        
        if farmer_count > 0:
            cursor.execute("SELECT * FROM farmers LIMIT 1")
            columns = [desc[0] for desc in cursor.description]
            print(f"\nFarmers table columns: {columns}")
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]
        print(f"\nTotal conversations: {conv_count}")
        
        if conv_count > 0:
            cursor.execute("SELECT * FROM conversations LIMIT 1")
            columns = [desc[0] for desc in cursor.description]
            print(f"\nConversations table columns: {columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error verifying schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 AVA OLO Database Schema Verification")
    print("=" * 60)
    verify_database_schema()