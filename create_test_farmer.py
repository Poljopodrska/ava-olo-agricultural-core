#!/usr/bin/env python3
"""
Create a test farmer user in the database
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

async def create_farmer_user():
    """Create a farmer and user in the database"""
    
    # ========================================
    # PETER KNAFLIČ FARM DATA
    # ========================================
    
    # Farmer data
    FARMER_NAME = "Peter Knaflič"
    FARMER_PHONE = "+38641234567"  # Please update with your actual WhatsApp number
    FARMER_PASSWORD = "ava2024"  # Please change this to your desired password
    FARM_NAME = "Knaflič Farm"
    LOCATION = "Pavšičeva 18, 1370 Logatec, Slovenia"
    
    # Farm details
    FARM_SIZE = 28.0  # Total: Skirca (1ha) + Kalce (2ha) + Javornik (25ha)
    LATITUDE = 45.9144  # Logatec coordinates
    LONGITUDE = 14.2242
    
    # Field information for reference
    FIELDS = {
        "Skirca": "1 ha",
        "Kalce": "2 ha", 
        "Javornik": "25 ha"
    }
    
    # ========================================
    
    print(f"🌾 Creating farmer account for: {FARMER_NAME}")
    print(f"📱 WhatsApp: {FARMER_PHONE}")
    print(f"🏡 Farm: {FARM_NAME}")
    print(f"📍 Location: {LOCATION}")
    
    # Fix database URL
    fix_database_url()
    components = get_database_components()
    
    if not components:
        print("❌ Failed to get database components")
        return
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=components['hostname'],
            port=components['port'],
            database=components['database'],
            user=components['username'],
            password=components['password']
        )
        
        print("✅ Connected to database")
        
        # Start transaction
        async with conn.transaction():
            # 1. First check if farmer already exists
            existing_farmer = await conn.fetchrow(
                "SELECT id FROM farmers WHERE wa_phone_number = $1",
                FARMER_PHONE
            )
            
            if existing_farmer:
                farmer_id = existing_farmer['id']
                print(f"ℹ️ Farmer already exists with ID: {farmer_id}")
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
            
            # 3. Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM farm_users WHERE wa_phone_number = $1",
                FARMER_PHONE
            )
            
            if existing_user:
                print(f"ℹ️ User already exists with ID: {existing_user['id']}")
                
                # Update password if user wants
                update_password = input("Do you want to update the password? (y/n): ")
                if update_password.lower() == 'y':
                    # Hash the new password
                    password_hash = bcrypt.hashpw(
                        FARMER_PASSWORD.encode('utf-8'), 
                        bcrypt.gensalt()
                    ).decode('utf-8')
                    
                    await conn.execute("""
                        UPDATE farm_users 
                        SET password_hash = $1 
                        WHERE id = $2
                    """, password_hash, existing_user['id'])
                    
                    print("✅ Password updated")
            else:
                # 4. Hash the password
                password_hash = bcrypt.hashpw(
                    FARMER_PASSWORD.encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
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
            
            # 6. Create fields for Peter
            print("\n📍 Creating fields...")
            
            # Check if fields table exists and create fields
            try:
                for field_name, size_str in FIELDS.items():
                    # Extract numeric size
                    size = float(size_str.split()[0])
                    
                    # Check if field already exists
                    existing_field = await conn.fetchrow(
                        "SELECT field_id FROM fields WHERE farmer_id = $1 AND field_name = $2",
                        farmer_id, field_name
                    )
                    
                    if existing_field:
                        print(f"   ℹ️ Field '{field_name}' already exists")
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
                print(f"   ⚠️ Could not create fields (table might not exist): {e}")
        
        print("\n🎉 Success! You can now log in with:")
        print(f"   WhatsApp: {FARMER_PHONE}")
        print(f"   Password: {FARMER_PASSWORD}")
        print("\n🌐 Go to: http://localhost:8000/login")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 AVA OLO - Create Test Farmer")
    print("=" * 50)
    
    # Check if bcrypt is installed
    try:
        import bcrypt
    except ImportError:
        print("❌ bcrypt not installed. Installing...")
        os.system("pip install bcrypt")
        import bcrypt
    
    asyncio.run(create_farmer_user())