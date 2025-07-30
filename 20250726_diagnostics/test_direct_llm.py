#!/usr/bin/env python3
"""
Test Direct LLM Implementation
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

async def test_direct_llm():
    """Test the direct LLM implementation"""
    print("🧪 Testing Direct LLM v3.4.5")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Check status
        print("1️⃣ Checking chat status...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/chat/status")
            status = response.json()
            print(f"   OpenAI configured: {status.get('openai_configured')}")
            print(f"   Test mode: {status.get('test_mode')}")
            print(f"   Key length: {status.get('key_length')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # 2. Test quick endpoint
        print("2️⃣ Testing quick LLM endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/chat/test")
            result = response.json()
            print(f"   Test: {result.get('test')}")
            print(f"   Response: {result.get('response', result.get('error'))}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # 3. Test varied responses
        test_messages = [
            "What is 2+2?",
            "Tell me about mangoes",
            "How's the weather?",
            "Hello there!"
        ]
        
        print("3️⃣ Testing varied responses...")
        for msg in test_messages:
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"message": msg, "farmer_id": "test"}
                )
                result = response.json()
                llm_response = result.get('response', 'ERROR')
                print(f"   Q: {msg}")
                print(f"   A: {llm_response[:80]}...")
                print(f"   LLM: {result.get('llm_test', False)}")
                print()
            except Exception as e:
                print(f"   ❌ Error with '{msg}': {e}")
        
        # 4. Test dashboard endpoint
        print("4️⃣ Testing dashboard endpoint /message...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/chat/message",
                json={"content": "Is the LLM working?"}
            )
            result = response.json()
            print(f"   Response: {result.get('response', 'ERROR')[:80]}...")
            print(f"   Model: {result.get('model')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    await test_direct_llm()
    print()
    print("✅ Direct LLM test complete!")
    print("If you see varied, intelligent responses above, the LLM is working!")

if __name__ == "__main__":
    asyncio.run(main())