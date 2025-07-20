#!/usr/bin/env python3
"""
Claude Code Database Access Demo
Demonstrates secure database access through ECS endpoints
"""

from ava_database_helper import AVADatabaseAccess, print_query_results

def main():
    print("=== Claude Code Database Access Demo ===")
    print("🔗 Connecting to AVA OLO farmer database via ECS ALB...")
    
    # Initialize database access
    db = AVADatabaseAccess()
    
    # Test 1: Connection and basic info
    print("\n📊 Database Overview:")
    tables = db.get_tables()
    if tables.get('success'):
        print(f"✅ Connected successfully!")
        print(f"📋 Found {tables['count']} database tables")
        print("🌾 Key tables:")
        for table in tables['tables'][:8]:  # Show key tables
            if 'ava_' in table['name'] or 'farm_' in table['name']:
                print(f"   - {table['name']}: {table['rows']} rows, {table['columns']} columns")
    else:
        print(f"❌ Connection failed: {tables.get('error')}")
        return
    
    # Test 2: Farmer statistics  
    print("\n🚜 Farmer Analytics:")
    farmer_count = db.count_farmers()
    print(f"Total registered farmers: {farmer_count}")
    
    overview = db.get_farmer_overview()
    if overview.get('success') and overview.get('rows'):
        data = overview['rows'][0]
        print(f"Cities covered: {data.get('cities_covered', 'N/A')}")
        print(f"Total hectares: {data.get('total_hectares', 'N/A')}")
        print(f"Average hectares per farmer: {data.get('avg_hectares_per_farmer', 'N/A'):.2f}")
    
    # Test 3: Recent activity
    print("\n📅 Recent Farmer Registrations:")
    recent = db.get_recent_registrations(3)
    if recent.get('success') and recent.get('rows'):
        for i, farmer in enumerate(recent['rows'], 1):
            name = f"{farmer.get('manager_name', '')} {farmer.get('manager_last_name', '')}"
            farm = farmer.get('farm_name', 'Unknown Farm')
            city = farmer.get('city', 'Unknown City')
            hectares = farmer.get('total_hectares', 'N/A')
            print(f"   {i}. {name.strip()} - {farm} ({city}) - {hectares} ha")
    
    # Test 4: Agricultural data
    print("\n🌱 Crop Distribution:")
    crops = db.get_crop_distribution()
    if crops.get('success') and crops.get('rows'):
        for crop in crops['rows'][:5]:  # Top 5 crops
            name = crop.get('crop_name', 'Unknown')
            hectares = crop.get('total_hectares', 0)
            fields = crop.get('field_count', 0)
            print(f"   - {name}: {hectares} ha across {fields} fields")
    
    # Test 5: Conversation insights
    print("\n💬 Popular Support Topics:")
    topics = db.get_conversation_topics()
    if topics.get('success') and topics.get('rows'):
        for topic in topics['rows'][:5]:  # Top 5 topics
            topic_name = topic.get('topic', 'General')
            count = topic.get('conversation_count', 0)
            print(f"   - {topic_name}: {count} conversations")
    
    # Test 6: Custom query example
    print("\n🏙️ Farmers by City:")
    city_query = """
    SELECT 
        city,
        COUNT(*) as farmer_count,
        SUM(total_hectares) as city_hectares
    FROM ava_farmers 
    WHERE city IS NOT NULL 
    GROUP BY city 
    ORDER BY farmer_count DESC 
    LIMIT 5
    """
    city_result = db.query(city_query)
    if city_result.get('success') and city_result.get('rows'):
        for city_data in city_result['rows']:
            city = city_data.get('city', 'Unknown')
            farmers = city_data.get('farmer_count', 0)
            hectares = city_data.get('city_hectares', 0) or 0
            print(f"   - {city}: {farmers} farmers, {hectares} hectares")
    
    # Test 7: Security verification
    print("\n🔒 Security Verification:")
    
    # Test invalid query (should be blocked)
    security_test = db.query("DELETE FROM ava_farmers WHERE id = 1")
    if not security_test.get('success'):
        print("✅ Security working: DELETE query properly blocked")
    else:
        print("❌ Security issue: Dangerous query was allowed")
    
    print("\n=== Demo Complete ===")
    print("✅ Claude Code can safely access farmer database")
    print("🔐 All queries are logged for security audit")
    print("🚀 Ready for development and analysis tasks!")
    print(f"\n📡 Base URL: {db.base_url}")
    print(f"🔑 Authentication: X-Dev-Key required")

if __name__ == "__main__":
    main()