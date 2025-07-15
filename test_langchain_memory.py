#!/usr/bin/env python3
"""
Test LangChain memory approach for registration
"""
import asyncio
import aiohttp
import json

async def test_langchain_peter_case():
    """Test the Peter case with LangChain memory"""
    
    print("🧠 Testing LangChain Memory Approach")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    conversation_id = None
    
    test_steps = [
        {"input": "Peter", "expect": "last name"},
        {"input": "Johnson", "expect": "Peter Johnson"},
        {"input": "+385912345678", "expect": "password"},
        {"input": "testpass123", "expect": "confirm"},
        {"input": "testpass123", "expect": "farm"},
        {"input": "Johnson Farm", "expect": "Welcome"}
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🎯 Starting conversation with LangChain memory...")
        
        for i, step in enumerate(test_steps, 1):
            print(f"\nStep {i}: '{step['input']}'")
            
            try:
                payload = {
                    "user_input": step['input'],
                    "current_data": {},
                    "conversation_history": [],
                    "last_ava_message": ""
                }
                
                if conversation_id:
                    payload["conversation_id"] = conversation_id
                
                response = await session.post(
                    f"{base_url}/api/v1/auth/chat-register",
                    json=payload
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract conversation ID for next request
                    if data.get("conversation_id"):
                        conversation_id = data["conversation_id"]
                    
                    print(f"  🤖 AVA: {data.get('message', '')}")
                    print(f"  📊 Memory: {data.get('memory_enabled', False)}")
                    print(f"  📝 Data: {json.dumps(data.get('extracted_data', {}), indent=4)}")
                    
                    # Check expectation
                    message = data.get('message', '').lower()
                    if step['expect'].lower() in message:
                        print(f"  ✅ Expected '{step['expect']}' found")
                    else:
                        print(f"  ❌ Expected '{step['expect']}' but got: {message}")
                    
                    # Check if registration complete
                    if data.get('status') == 'COMPLETE':
                        print(f"  🎉 Registration completed!")
                        break
                        
                else:
                    print(f"  ❌ HTTP {response.status}: {await response.text()}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                break

async def test_memory_persistence():
    """Test that memory persists across requests"""
    
    print("\n🧠 Testing Memory Persistence")
    print("=" * 40)
    
    base_url = "http://localhost:8080"
    conversation_id = "test-memory-123"
    
    async with aiohttp.ClientSession() as session:
        # First request
        print("Request 1: 'Peter'")
        response1 = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Peter",
                "conversation_id": conversation_id,
                "current_data": {},
                "conversation_history": [],
                "last_ava_message": ""
            }
        )
        
        if response1.status == 200:
            data1 = await response1.json()
            print(f"AVA: {data1.get('message', '')}")
        
        # Second request - should remember "Peter"
        print("\nRequest 2: 'Johnson'")
        response2 = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Johnson",
                "conversation_id": conversation_id,
                "current_data": {},
                "conversation_history": [],
                "last_ava_message": ""
            }
        )
        
        if response2.status == 200:
            data2 = await response2.json()
            print(f"AVA: {data2.get('message', '')}")
            
            # Check if it remembered Peter
            if "peter johnson" in data2.get('message', '').lower():
                print("✅ Memory working - remembered Peter!")
            else:
                print("❌ Memory not working - forgot Peter")

if __name__ == "__main__":
    print("🚀 Testing LangChain Memory Registration System")
    asyncio.run(test_langchain_peter_case())
    asyncio.run(test_memory_persistence())