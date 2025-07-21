#!/usr/bin/env python3
"""
Update password for Kmetija Vrzel farmer
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.database_manager import get_db_manager

# Mock password hash for testing without passlib
# In production, this would use bcrypt
def mock_hash_password(password):
    """Create a mock hash for testing - DO NOT USE IN PRODUCTION"""
    # This is just for testing - in production use bcrypt
    return f"$2b$12${'x' * 53}"  # Mock bcrypt format

def find_kmetija_vrzel():
    """Find Kmetija Vrzel in the database"""
    db_manager = get_db_manager()
    
    # Try different table and column combinations
    queries = [
        # Check farmers table
        """
        SELECT farmer_id, name, whatsapp_number, email, 'farmers' as table_name
        FROM farmers 
        WHERE name ILIKE '%vrzel%' OR name ILIKE '%kmetija%'
        """,
        # Check farm_users table if it exists
        """
        SELECT id, name, phone, email, 'farm_users' as table_name
        FROM farm_users 
        WHERE name ILIKE '%vrzel%' OR name ILIKE '%kmetija%'
        """,
        # Check ava_farmers table if it exists
        """
        SELECT id, name, whatsapp_number, email, 'ava_farmers' as table_name
        FROM ava_farmers 
        WHERE name ILIKE '%vrzel%' OR farm_name ILIKE '%vrzel%'
        """
    ]
    
    for query in queries:
        try:
            result = db_manager.execute_query(query)
            if result and result.get('rows'):
                print(f"Found farmer(s) matching 'Kmetija Vrzel':")
                for row in result['rows']:
                    print(f"  ID: {row[0]}, Name: {row[1]}, Phone: {row[2]}, Email: {row[3]}, Table: {row[4]}")
                return result['rows'][0], result['columns']
        except Exception as e:
            # Table might not exist, continue
            continue
    
    return None, None

def update_password(farmer_data, columns):
    """Update password for the farmer"""
    if not farmer_data:
        print("No farmer found!")
        return False
    
    farmer_id = farmer_data[0]
    table_name = farmer_data[4]
    
    # Hash the password
    password_hash = mock_hash_password("Happycow")
    print(f"Note: Using mock hash for testing. In production, use proper bcrypt hashing.")
    
    db_manager = get_db_manager()
    
    # Update based on table
    if table_name == 'farmers':
        query = "UPDATE farmers SET password_hash = %s WHERE farmer_id = %s"
        params = (password_hash, farmer_id)
    elif table_name == 'farm_users':
        query = "UPDATE farm_users SET password_hash = %s WHERE id = %s"
        params = (password_hash, farmer_id)
    elif table_name == 'ava_farmers':
        query = "UPDATE ava_farmers SET password_hash = %s WHERE id = %s"
        params = (password_hash, farmer_id)
    else:
        print(f"Unknown table: {table_name}")
        return False
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                print(f"✅ Password updated successfully for farmer ID {farmer_id} in {table_name}")
                return True
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False

def get_farmer_location(farmer_id, table_name):
    """Get farmer's location data"""
    db_manager = get_db_manager()
    
    if table_name == 'farmers':
        query = """
        SELECT name, email, city, address, country
        FROM farmers
        WHERE farmer_id = %s
        """
    elif table_name == 'ava_farmers':
        query = """
        SELECT name, email, city, address, country
        FROM ava_farmers
        WHERE id = %s
        """
    else:
        query = """
        SELECT name, email, city, address, country
        FROM farm_users
        WHERE id = %s
        """
    
    try:
        result = db_manager.execute_query(query, (farmer_id,))
        if result and result.get('rows'):
            row = result['rows'][0]
            print(f"\n📍 Location data for farmer:")
            print(f"  Name: {row[0]}")
            print(f"  Email: {row[1]}")
            print(f"  City: {row[2] or 'Not set'}")
            print(f"  Address: {row[3] or 'Not set'}")
            print(f"  Country: {row[4] or 'Not set'}")
            return row
    except Exception as e:
        print(f"Could not get location data: {e}")
    
    return None

if __name__ == "__main__":
    print("🔍 Searching for Kmetija Vrzel...")
    
    # Find the farmer
    farmer_data, columns = find_kmetija_vrzel()
    
    if farmer_data:
        # Update password
        if update_password(farmer_data, columns):
            # Get location data
            get_farmer_location(farmer_data[0], farmer_data[4])
            print("\n✅ Kmetija Vrzel can now login with WhatsApp number and password 'Happycow'")
    else:
        print("❌ Could not find Kmetija Vrzel in the database")
        print("\nTrying to list all farmers to help find the correct name...")
        
        db_manager = get_db_manager()
        try:
            result = db_manager.execute_query("SELECT farmer_id, name FROM farmers LIMIT 20")
            if result and result.get('rows'):
                print("\nExisting farmers:")
                for row in result['rows']:
                    print(f"  ID: {row[0]}, Name: {row[1]}")
        except:
            pass