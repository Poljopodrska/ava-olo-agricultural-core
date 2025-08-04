#!/usr/bin/env python3
"""
Test WhatsApp Optimization for CAVA
Bulgarian Mango Farmer Test Scenario
"""
import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.cava.chat_engine import CAVAChatEngine
from modules.cava.conversation_optimizer import get_optimizer

async def test_bulgarian_mango_farmer():
    """Test CAVA with Bulgarian mango farmer scenario"""
    
    print("🥭 Bulgarian Mango Farmer WhatsApp Test")
    print("=" * 50)
    
    # Initialize CAVA engine
    engine = CAVAChatEngine()
    
    # Bulgarian mango farmer context
    farmer_context = {
        'farmer_name': 'Ivan Petrov',
        'location': 'Vipava Valley, Bulgaria',
        'weather': {
            'description': 'Sunny',
            'temperature': 18,
            'humidity': 65,
            'wind_speed': 3.2
        },
        'fields': [
            {'name': 'South Field', 'crop': 'Mango', 'hectares': 2.5},
            {'name': 'Valley Plot', 'crop': 'Grapes', 'hectares': 1.8}
        ]
    }
    
    # Test conversations
    test_messages = [
        "When should I water my mangoes?",
        "My mango leaves are turning yellow, what's wrong?",
        "Best fertilizer for mangoes in spring?",
        "How much water do mango trees need per week?",
        "Tell me everything about growing mangoes in cooler climates like Bulgaria"
    ]
    
    print(f"\n📱 Testing WhatsApp-style responses for {farmer_context['farmer_name']}")
    print(f"📍 Location: {farmer_context['location']}")
    print(f"🥭 Growing: Mangoes and Grapes")
    print("\n" + "=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n💬 Test {i}: {message}")
        print("-" * 40)
        
        # Get CAVA response
        result = await engine.chat(
            session_id="+359123456789",  # Bulgarian phone number
            message=message,
            farmer_context=farmer_context
        )
        
        if result.get("success"):
            response = result["response"]
            
            # Display optimization metrics
            print(f"✅ Response received:")
            print(f"📊 Metrics:")
            print(f"   - WhatsApp Optimized: {result.get('whatsapp_optimized', False)}")
            print(f"   - Message Count: {result.get('message_count', 1)}")
            print(f"   - Avg Length: {result.get('avg_message_length', 0):.0f} chars")
            print(f"   - Total Length: {len(response)} chars")
            print(f"\n📱 WhatsApp Response:")
            print("-" * 30)
            
            # Display as WhatsApp messages
            messages = response.split('\n\n')
            for msg in messages:
                print(f"[CAVA]: {msg}")
                if len(messages) > 1:
                    print()  # Space between multiple messages
            
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 50)
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Test the optimizer directly
    print("\n🔧 Direct Optimizer Test")
    print("=" * 50)
    
    optimizer = get_optimizer()
    
    # Test with a typical long response
    long_response = """Based on the current weather conditions in the Vipava Valley and considering that you're growing mangoes in a cooler climate than typical, I recommend implementing a comprehensive irrigation strategy. You should water your mango trees deeply but infrequently, approximately every 7-10 days during the growing season, ensuring the soil is moist to a depth of 2-3 feet. The amount of water needed varies with tree size and weather conditions, but mature trees typically require 30-50 gallons per watering. It's crucial to monitor soil moisture regularly and adjust watering based on rainfall and temperature. During fruit development, maintain consistent moisture levels to prevent fruit drop and ensure optimal fruit size and quality."""
    
    print("Original response length:", len(long_response), "chars")
    print("\nOptimizing for WhatsApp...")
    
    optimized = optimizer.optimize_response(long_response, {'farmer': 'Ivan', 'topic': 'irrigation'})
    
    print(f"\n📱 WhatsApp Optimized ({len(optimized)} messages):")
    print("-" * 30)
    for i, msg in enumerate(optimized, 1):
        print(f"Message {i} ({len(msg)} chars):")
        print(f"[CAVA]: {msg}")
        print()
    
    print("✅ WhatsApp Optimization Test Complete!")
    
    # Return test results
    return {
        "test_count": len(test_messages),
        "success": True,
        "farmer": farmer_context['farmer_name'],
        "optimization_working": len(optimized) > 1 or len(optimized[0]) < 200
    }

if __name__ == "__main__":
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set. Setting test key...")
        # You would set a real key here for testing
        print("❌ Cannot run test without API key")
        sys.exit(1)
    
    # Run the test
    result = asyncio.run(test_bulgarian_mango_farmer())
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   - Tests Run: {result['test_count']}")
    print(f"   - Success: {result['success']}")
    print(f"   - Farmer: {result['farmer']}")
    print(f"   - WhatsApp Optimization: {'✅ Working' if result['optimization_working'] else '❌ Not Working'}")
    print("=" * 50)