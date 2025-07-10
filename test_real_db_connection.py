import asyncpg
import asyncio
import os

DB_HOST = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'farmer_crm')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '2hpzvrg_xP~qNbz1[_NppSK$e*O1')

async def test_real_database():
    try:
        # Connect to the real database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        print("✅ Successfully connected to farmer-crm-production!")
        
        # Get list of actual tables
        tables_query = """
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        print(f"\n📊 Found {len(tables)} tables in the database:")
        
        for table in tables:
            print(f"  - {table['table_name']} ({table['table_type']})")
        
        # Get sample data from first few tables
        for table in tables[:3]:  # Just first 3 tables
            table_name = table['table_name']
            try:
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count = await conn.fetchval(count_query)
                print(f"\n📋 Table '{table_name}' has {count} records")
                
                # Get column info
                columns_query = f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position;
                """
                columns = await conn.fetch(columns_query)
                print(f"   Columns: {', '.join([col['column_name'] for col in columns])}")
                
            except Exception as e:
                print(f"   Error accessing {table_name}: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Check environment variables and VPC connectivity")

if __name__ == "__main__":
    asyncio.run(test_real_database())