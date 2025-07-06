"""Test connection to Windows PostgreSQL database"""
import asyncio
from core.database_operations import DatabaseOperations

async def main():
    db_ops = DatabaseOperations()
    
    # Test connection
    print("🔍 Testing connection to Windows PostgreSQL (farmer_crm database)...")
    success = await db_ops.test_windows_postgresql()
    
    if success:
        print("\n✅ Connection successful!")
        
        # Test getting farmers
        print("\n👥 Getting all farmers...")
        farmers = await db_ops.get_all_farmers()
        print(f"Found {len(farmers)} farmers:")
        for farmer in farmers[:5]:  # Show first 5
            print(f"  - {farmer['name']} ({farmer['farm_name']}) - {farmer['farm_type']}")
        
        # Test conversations
        print("\n💬 Checking conversations...")
        convs = await db_ops.get_conversations_for_approval()
        print(f"Unapproved: {len(convs['unapproved'])}, Approved: {len(convs['approved'])}")
        
        # Health check
        print("\n🏥 Running health check...")
        health = await db_ops.health_check()
        print(f"Health check: {'PASSED' if health else 'FAILED'}")
    else:
        print("\n❌ Connection failed!")

if __name__ == "__main__":
    asyncio.run(main())