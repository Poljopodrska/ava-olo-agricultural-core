#!/usr/bin/env python3
"""
Test Bulgarian Registration Intent
Verify that LLM correctly handles Bulgarian registration requests
"""
import asyncio
import httpx
import json
import os
from datetime import datetime

async def test_bulgarian_registration():
    """Test registration with Bulgarian intent"""
    
    # Set up API endpoint
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Bulgarian Registration Intent")
    print("=" * 50)
    
    # Test 1: Check debug endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/registration/debug")
            debug_info = response.json()
            print("📊 Debug Info:")
            print(f"   OpenAI Key Set: {debug_info['openai_key_set']}")
            print(f"   Key Prefix: {debug_info['key_prefix']}")
            print(f"   CAVA Mode: {debug_info['cava_mode']}")
            print()
    except Exception as e:
        print(f"❌ Could not reach debug endpoint: {e}")
        return
    
    # Test 2: Send Bulgarian registration intent
    session_id = f"test_bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    test_messages = [
        "Искам да се регистрирам",  # "I want to register" in Bulgarian
        "Казвам се Иван Петров",     # "My name is Ivan Petrov"
        "+359888123456",             # Bulgarian phone number
        "mypassword123"              # Password
    ]
    
    print("🗣️ Testing Registration Flow:")
    print(f"   Session ID: {session_id}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"Step {i}: Sending '{message}'")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/api/v1/registration/cava",
                    json={
                        "farmer_id": session_id,
                        "message": message,
                        "language": "bg"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Response: {result.get('response', 'No response')}")
                    
                    # Check if LLM was used
                    if "collected_data" in result:
                        print(f"📋 Collected: {result['collected_data']}")
                    
                    if result.get("registration_complete"):
                        print("🎉 Registration Complete!")
                        break
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
            
            print()
            await asyncio.sleep(1)  # Small delay between messages
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            break
    
    # Test 3: Verify LLM was actually used
    print("\n🔍 Checking server logs for LLM usage...")
    print("   Look for: '🏛️ CONSTITUTIONAL LLM CALL' in logs")
    print("   Look for: '✅ LLM RESPONSE' in logs")
    
    print("\n✅ Test complete! Check server logs to verify LLM usage.")

if __name__ == "__main__":
    # Load environment if needed
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Loading .env.production...")
        try:
            from dotenv import load_dotenv
            load_dotenv(".env.production")
        except:
            pass
    
    asyncio.run(test_bulgarian_registration())