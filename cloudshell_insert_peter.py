#!/usr/bin/env python3
"""
AWS CloudShell script to insert Peter's data
Handles the database password with brackets properly
"""

import psycopg2
import os

def insert_peter_data():
    # Database connection details
    RDS_ENDPOINT = "farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
    RDS_PORT = "5432"
    RDS_DATABASE = "farmer_crm"
    RDS_USER = "postgres"
    RDS_PASSWORD = "2hpzvrg_xP~qNbz1[_NppSK$e*O1"  # Password with brackets
    
    print("🌾 Inserting Peter Knaflič data into RDS")
    print("=" * 50)
    
    try:
        # Connect to database
        print("🔄 Connecting to RDS...")
        conn = psycopg2.connect(
            host=RDS_ENDPOINT,
            port=RDS_PORT,
            database=RDS_DATABASE,
            user=RDS_USER,
            password=RDS_PASSWORD
        )
        cur = conn.cursor()
        print("✅ Connected to database")
        
        # 1. Insert/update farmer
        print("\n📋 Creating farmer record...")
        cur.execute("""
            INSERT INTO farmers (
                name, wa_phone_number, location, 
                farm_size_hectares, farm_name,
                latitude, longitude,
                created_at, last_message_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            ) 
            ON CONFLICT (wa_phone_number) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                location = EXCLUDED.location,
                farm_size_hectares = EXCLUDED.farm_size_hectares,
                farm_name = EXCLUDED.farm_name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                last_message_at = NOW()
            RETURNING id
        """, (
            'Peter Knaflič',
            '+38641348050',
            'Pavšičeva 18, 1370 Logatec, Slovenia',
            28.0,
            'Knaflič Farm',
            45.9144,
            14.2242
        ))
        
        farmer_id = cur.fetchone()[0]
        print(f"✅ Farmer created/updated with ID: {farmer_id}")
        
        # 2. Insert/update user account
        print("\n🔐 Creating user account...")
        cur.execute("""
            INSERT INTO farm_users (
                farmer_id, wa_phone_number, password_hash,
                user_name, role, is_active, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (wa_phone_number) 
            DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                user_name = EXCLUDED.user_name,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active
        """, (
            farmer_id,
            '+38641348050',
            '$2b$12$KxwgM8Gh2I5NGDKpEOLFXuXE7jV1B5YzH.xVxxfAU8kYvzxf5.Wjy',  # bcrypt hash of 'Viognier'
            'Peter Knaflič',
            'owner',
            True
        ))
        print("✅ User account created/updated")
        
        # 3. Create fields
        print("\n📍 Creating fields...")
        fields = [
            ('Skirca', 1.0, 'Skirca, Logatec'),
            ('Kalce', 2.0, 'Kalce, Logatec'),
            ('Javornik', 25.0, 'Javornik, Logatec')
        ]
        
        for field_name, size, location in fields:
            cur.execute("""
                INSERT INTO fields (
                    farmer_id, field_name, size_hectares,
                    location, created_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (farmer_id, field_name) 
                DO UPDATE SET 
                    size_hectares = EXCLUDED.size_hectares,
                    location = EXCLUDED.location
            """, (farmer_id, field_name, size, location))
            print(f"   ✅ Created field '{field_name}' ({size} ha)")
        
        # Commit changes
        conn.commit()
        
        # Verify
        print("\n🔍 Verifying data...")
        cur.execute("""
            SELECT 
                f.id, f.name, f.wa_phone_number, f.farm_name,
                fu.user_name, fu.role
            FROM farmers f
            JOIN farm_users fu ON f.id = fu.farmer_id
            WHERE f.wa_phone_number = %s
        """, ('+38641348050',))
        
        result = cur.fetchone()
        if result:
            print(f"✅ Verified: {result[1]} - {result[2]}")
            print(f"   Farm: {result[3]}")
            print(f"   Role: {result[5]}")
        
        print("\n" + "="*50)
        print("🎉 SUCCESS! Peter can now login:")
        print("   URL: https://3ksdvgdtad.us-east-1.awsapprunner.com/login")
        print("   WhatsApp: +38641348050")
        print("   Password: Viognier")
        print("="*50)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    insert_peter_data()