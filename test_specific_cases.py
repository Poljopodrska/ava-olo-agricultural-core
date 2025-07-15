#!/usr/bin/env python3
"""
Test specific challenging cases to validate improvements
"""
import asyncio
import aiohttp
import json

async def test_specific_challenging_cases():
    """Test the most challenging cases that might fail"""
    
    print("🎯 Testing Specific Challenging Cases")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    challenging_cases = [
        {
            "name": "User Asks Question",
            "steps": [
                {"input": "What information do you need from me?", "expect": "name"},
                {"input": "Stefan Milosević", "expect": "phone"},
                {"input": "Why do you need my phone?", "expect": "WhatsApp"},
                {"input": "+381642345678", "expect": "password"},
                {"input": "securepass", "expect": "confirm"},
                {"input": "securepass", "expect": "farm"},
                {"input": "Green Valley", "expect": "Welcome"}
            ]
        },
        {
            "name": "Password Mismatch Recovery",
            "steps": [
                {"input": "Branko Mitrović", "expect": "phone"},
                {"input": "+381664567890", "expect": "password"},
                {"input": "branko123", "expect": "confirm"},
                {"input": "branko124", "expect": "don't match"},
                {"input": "branko123", "expect": "confirm"},
                {"input": "branko123", "expect": "farm"},
                {"input": "Mitrović Livestock", "expect": "Welcome"}
            ]
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in challenging_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            
            current_data = {}
            conversation_history = []
            last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
            
            success = True
            
            for i, step in enumerate(test_case['steps']):
                print(f"  Step {i+1}: '{step['input']}'")
                
                try:
                    response = await session.post(
                        f"{base_url}/api/v1/auth/chat-register",
                        json={
                            "user_input": step['input'],
                            "current_data": current_data,
                            "conversation_history": conversation_history,
                            "last_ava_message": last_ava_message
                        }
                    )
                    
                    if response.status == 200:
                        data = await response.json()
                        message = data.get('message', '').lower()
                        
                        if step['expect'].lower() in message:
                            print(f"    ✅ Found expected: '{step['expect']}'")
                            current_data = data.get('extracted_data', current_data)
                            conversation_history = data.get('conversation_history', conversation_history)
                            last_ava_message = data.get('last_ava_message', data.get('message', ''))
                        else:
                            print(f"    ❌ Expected '{step['expect']}' but got: {message[:100]}...")
                            success = False
                            break
                    else:
                        print(f"    ❌ HTTP {response.status}")
                        success = False
                        break
                        
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    success = False
                    break
            
            if success:
                print(f"  🎉 {test_case['name']} - PASSED!")
            else:
                print(f"  ❌ {test_case['name']} - FAILED!")

if __name__ == "__main__":
    asyncio.run(test_specific_challenging_cases())