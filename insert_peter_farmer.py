#!/usr/bin/env python3
"""
Insert Peter Knaflič farmer data into AWS database
"""

import os
import sys
import asyncio
import asyncpg
import bcrypt
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database_url_fixer import fix_database_url, get_database_components

async def insert_peter_data():
    """Insert Peter's farmer data into the AWS database"""
    
    # Peter's data
    FARMER_NAME = "Peter Knaflič"
    FARMER_PHONE = "+38641348050"
    FARMER_PASSWORD = "Viognier"
    FARM_NAME = "Knaflič Farm"
    LOCATION = "Pavšičeva 18, 1370 Logatec, Slovenia"
    FARM_SIZE = 28.0
    LATITUDE = 45.9144
    LONGITUDE = 14.2242
    
    FIELDS = {
        "Skirca": 1.0,
        "Kalce": 2.0,
        "Javornik": 25.0
    }
    
    print(f"🌾 Creating farmer account for: {FARMER_NAME}")
    print(f"📱 WhatsApp: {FARMER_PHONE}")
    print(f"🏡 Farm: {FARM_NAME}")
    print(f"📍 Location: {LOCATION}")
    
    # Get database URL and fix brackets
    database_url = os.environ.get('DATABASE_URL', '')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    # Fix brackets in password
    if '[' in database_url and ']' in database_url:
        # URL-encode brackets
        database_url = database_url.replace('[', '%5B').replace(']', '%5D')
        os.environ['DATABASE_URL'] = database_url
        print("✅ Fixed brackets in database URL")
    
    # Parse the fixed URL manually
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if not match:
        print("❌ Failed to parse database URL")
        return
    
    user, password, host, port, database = match.groups()
    # Decode the password
    password = password.replace('%5B', '[').replace('%5D', ']')
    
    try:
        # Connect to AWS database
        print("🔄 Connecting to AWS database...")
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        
        print("✅ Connected to AWS database")
        
        # Start transaction
        async with conn.transaction():
            # 1. Check if farmer already exists
            existing_farmer = await conn.fetchrow(
                "SELECT id, name FROM farmers WHERE wa_phone_number = $1",
                FARMER_PHONE
            )
            
            if existing_farmer:
                farmer_id = existing_farmer['id']
                print(f"ℹ️ Farmer already exists with ID: {farmer_id}")
                
                # Update farmer details
                await conn.execute("""
                    UPDATE farmers 
                    SET name = $1, location = $2, farm_size_hectares = $3, 
                        farm_name = $4, latitude = $5, longitude = $6,
                        last_message_at = $7
                    WHERE id = $8
                """, 
                    FARMER_NAME, LOCATION, FARM_SIZE, FARM_NAME,
                    LATITUDE, LONGITUDE, datetime.now(), farmer_id
                )
                print("✅ Updated farmer details")
            else:
                # 2. Create farmer record
                farmer_id = await conn.fetchval("""
                    INSERT INTO farmers (
                        name, wa_phone_number, location, 
                        farm_size_hectares, farm_name,
                        latitude, longitude,
                        created_at, last_message_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, 
                    FARMER_NAME, FARMER_PHONE, LOCATION,
                    FARM_SIZE, FARM_NAME,
                    LATITUDE, LONGITUDE,
                    datetime.now(), datetime.now()
                )
                
                print(f"✅ Created farmer with ID: {farmer_id}")
            
            # 3. Hash the password
            password_hash = bcrypt.hashpw(
                FARMER_PASSWORD.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # 4. Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM farm_users WHERE wa_phone_number = $1",
                FARMER_PHONE
            )
            
            if existing_user:
                print(f"ℹ️ User already exists, updating password...")
                
                await conn.execute("""
                    UPDATE farm_users 
                    SET password_hash = $1, user_name = $2, 
                        role = $3, is_active = $4
                    WHERE id = $5
                """, password_hash, FARMER_NAME, 'owner', True, existing_user['id'])
                
                print("✅ Updated user account and password")
            else:
                # 5. Create farm_user record
                user_id = await conn.fetchval("""
                    INSERT INTO farm_users (
                        farmer_id, wa_phone_number, password_hash,
                        user_name, role, is_active,
                        created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """,
                    farmer_id, FARMER_PHONE, password_hash,
                    FARMER_NAME, 'owner', True,
                    datetime.now()
                )
                
                print(f"✅ Created user with ID: {user_id}")
            
            # 6. Create fields
            print("\n📍 Creating/updating fields...")
            
            try:
                for field_name, size in FIELDS.items():
                    # Check if field already exists
                    existing_field = await conn.fetchrow(
                        "SELECT field_id FROM fields WHERE farmer_id = $1 AND field_name = $2",
                        farmer_id, field_name
                    )
                    
                    if existing_field:
                        # Update field size
                        await conn.execute("""
                            UPDATE fields 
                            SET size_hectares = $1, location = $2
                            WHERE field_id = $3
                        """, size, f"{field_name}, Logatec", existing_field['field_id'])
                        print(f"   ✅ Updated field '{field_name}' ({size} ha)")
                    else:
                        field_id = await conn.fetchval("""
                            INSERT INTO fields (
                                farmer_id, field_name, size_hectares,
                                location, created_at
                            ) VALUES ($1, $2, $3, $4, $5)
                            RETURNING field_id
                        """,
                            farmer_id, field_name, size,
                            f"{field_name}, Logatec", datetime.now()
                        )
                        print(f"   ✅ Created field '{field_name}' ({size} ha)")
            except Exception as e:
                print(f"   ⚠️ Note about fields: {e}")
        
        print("\n" + "="*50)
        print("🎉 SUCCESS! Peter can now log in with:")
        print(f"   📱 WhatsApp: {FARMER_PHONE}")
        print(f"   🔐 Password: {FARMER_PASSWORD}")
        print("\n🌐 Login at: https://3ksdvgdtad.us-east-1.awsapprunner.com/login")
        print("="*50)
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Inserting Peter Knaflič data into AWS database")
    print("=" * 50)
    
    # Check if bcrypt is installed
    try:
        import bcrypt
    except ImportError:
        print("📦 Installing bcrypt...")
        os.system("pip install bcrypt")
        import bcrypt
    
    asyncio.run(insert_peter_data())