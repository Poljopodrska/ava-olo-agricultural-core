#!/usr/bin/env python3
"""
Test FAVA (Farmer-Aware Virtual Assistant) with Bulgarian Mango Farmer
Demonstrates farmer-specific context awareness vs generic advice
"""
import asyncio
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.cava.fava_engine import get_fava_engine
from modules.core.database_manager import DatabaseManager

async def test_bulgarian_mango_farmer_fava():
    """Test FAVA with Bulgarian mango farmer scenario"""
    
    print("🥭 FAVA Bulgarian Mango Farmer Test")
    print("=" * 50)
    print("Testing farmer-aware intelligence vs generic advice")
    print()
    
    # Initialize FAVA engine
    fava = get_fava_engine()
    db_manager = DatabaseManager()
    
    # Test scenarios for Bulgarian mango farmer
    test_scenarios = [
        {
            "message": "How are my mangoes doing?",
            "expected": "Response should mention HIS specific mango fields, size, location"
        },
        {
            "message": "I planted new Alphonso mangoes in greenhouse yesterday",
            "expected": "Should detect intent to save data and generate INSERT SQL"
        },
        {
            "message": "Should I water today?",
            "expected": "Should give advice based on HIS location (Vipava/Bulgaria) and HIS crops"
        },
        {
            "message": "My greenhouse is 500 square meters",
            "expected": "Should ask for confirmation to update database"
        },
        {
            "message": "What pest problems should I watch for?",
            "expected": "Should mention pests specific to mangoes in Bulgarian climate"
        }
    ]
    
    # Simulate Bulgarian mango farmer (needs to exist in database)
    # For testing, we'll use a mock farmer ID
    farmer_id = 46  # Peter's ID from the conversation
    
    print(f"🧑‍🌾 Testing with Farmer ID: {farmer_id}")
    print()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}: {scenario['message']}")
        print(f"Expected: {scenario['expected']}")
        print("-" * 40)
        
        try:
            async with db_manager.get_connection_async() as conn:
                # Process through FAVA
                result = await fava.process_farmer_message(
                    farmer_id=farmer_id,
                    message=scenario['message'],
                    db_connection=conn
                )
                
                print("FAVA Response:")
                print(f"  Message: {result.get('response', 'No response')}")
                
                if result.get('database_action'):
                    print(f"  Database Action: {result['database_action']}")
                    
                if result.get('sql_query'):
                    print(f"  SQL Query: {result['sql_query'][:100]}...")
                    
                if result.get('needs_confirmation'):
                    print(f"  Needs Confirmation: {result['confirmation_question']}")
                    
                if result.get('context_used'):
                    print(f"  Context Used: {', '.join(result['context_used'])}")
                    
                print()
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()
    
    # Test pure LLM decision making
    print("\n" + "=" * 50)
    print("🤖 Testing Pure LLM Intelligence (No Business Logic)")
    print("=" * 50)
    
    # Complex scenario requiring LLM intelligence
    complex_message = "I noticed some yellowing on the lower leaves of my mangoes in the south greenhouse, it's been 5 days since I last watered"
    
    print(f"Complex Message: {complex_message}")
    print()
    
    try:
        async with db_manager.get_connection_async() as conn:
            result = await fava.process_farmer_message(
                farmer_id=farmer_id,
                message=complex_message,
                db_connection=conn
            )
            
            print("FAVA Analysis:")
            print(f"Response: {result.get('response', 'No response')}")
            print()
            print("Key Points:")
            print("✅ Should mention HIS south greenhouse specifically")
            print("✅ Should relate to HIS mango variety")
            print("✅ Should consider Vipava/Bulgarian climate")
            print("✅ Should reference the 5-day watering gap")
            print()
            
            # Check if response is farmer-specific
            response_lower = result.get('response', '').lower()
            is_specific = any([
                'south' in response_lower,
                'your' in response_lower,
                'vipava' in response_lower,
                '5 day' in response_lower or 'five day' in response_lower
            ])
            
            if is_specific:
                print("✅ PASS: Response is farmer-specific!")
            else:
                print("❌ FAIL: Response appears generic")
                
    except Exception as e:
        print(f"❌ Error in complex test: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 FAVA Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("FAVA requires OpenAI API access")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_bulgarian_mango_farmer_fava())