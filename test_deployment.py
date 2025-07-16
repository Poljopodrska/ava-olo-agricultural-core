#!/usr/bin/env python3
"""Test deployment configuration"""
import os
import psycopg2
import urllib.parse
from sqlalchemy import create_engine, text

def test_environment():
    """Test environment variables"""
    print("=== Environment Variables ===")
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT', 'GOOGLE_MAPS_API_KEY']
    
    for var in env_vars:
        value = os.getenv(var)
        if var == 'DB_PASSWORD' and value:
            print(f"{var}: SET ({len(value)} chars)")
        elif var == 'GOOGLE_MAPS_API_KEY' and value:
            print(f"{var}: {value[:10]}...{value[-5:]}")
        else:
            print(f"{var}: {value if value else 'NOT SET'}")
    
    return all(os.getenv(var) for var in env_vars)

def test_database_connection():
    """Test database connection"""
    print("\n=== Database Connection Test ===")
    
    # Get credentials
    db_host = os.getenv('DB_HOST', '').strip().replace(' ', '')
    db_name = os.getenv('DB_NAME', 'farmer_crm')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_port = os.getenv('DB_PORT', '5432')
    
    # Test direct psycopg2 connection
    print("\n1. Testing direct psycopg2 connection...")
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
            sslmode='require'
        )
        print("✅ Direct psycopg2 connection: SUCCESS")
        
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM farmers")
        count = cur.fetchone()[0]
        print(f"   Found {count} farmers in database")
        
        conn.close()
    except Exception as e:
        print(f"❌ Direct psycopg2 connection: FAILED")
        print(f"   Error: {e}")
        return False
    
    # Test SQLAlchemy connection with URL encoding
    print("\n2. Testing SQLAlchemy connection...")
    try:
        db_password_encoded = urllib.parse.quote(db_password, safe='')
        database_url = f"postgresql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}"
        
        print(f"   URL preview: {database_url[:40]}...{database_url[-20:]}")
        
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 30
            }
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM farmers"))
            count = result.scalar()
            print("✅ SQLAlchemy connection: SUCCESS")
            print(f"   Found {count} farmers in database")
            
    except Exception as e:
        print(f"❌ SQLAlchemy connection: FAILED")
        print(f"   Error: {e}")
        return False
    
    return True

def test_google_maps():
    """Test Google Maps configuration"""
    print("\n=== Google Maps Configuration ===")
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if api_key and len(api_key) > 10:
        print(f"✅ API Key present: {api_key[:10]}...{api_key[-5:]}")
        print(f"   Length: {len(api_key)} chars")
        return True
    else:
        print("❌ API Key missing or invalid")
        return False

def main():
    """Run all tests"""
    print("AVA OLO Deployment Configuration Test")
    print("=" * 50)
    
    env_ok = test_environment()
    db_ok = test_database_connection()
    maps_ok = test_google_maps()
    
    print("\n=== Summary ===")
    print(f"Environment: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Database: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Google Maps: {'✅ PASS' if maps_ok else '❌ FAIL'}")
    
    if all([env_ok, db_ok, maps_ok]):
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())