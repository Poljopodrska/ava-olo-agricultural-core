#!/usr/bin/env python3
"""
Test conversational context awareness in registration
"""
import asyncio
import aiohttp
import json

async def test_registration_conversation():
    """Test registration with conversational context"""
    base_url = "http://localhost:8080"
    
    # Track conversation state
    conversation_history = []
    last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
    current_data = {}
    
    print("🔍 Testing Conversational Context Registration")
    print("=" * 50)
    
    # Test case 1: Name collection
    print("\n1️⃣ Testing name collection...")
    user_input = "Lidija"
    
    async with aiohttp.ClientSession() as session:
        # First interaction - first name only
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": user_input,
                "current_data": current_data,
                "conversation_history": conversation_history,
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"User: {user_input}")
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        
        # Update state
        current_data = data.get('extracted_data', {})
        conversation_history = data.get('conversation_history', [])
        last_ava_message = data.get('last_ava_message', '')
        
        # Second interaction - last name
        user_input = "Bačić"
        print(f"\nUser: {user_input}")
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": user_input,
                "current_data": current_data,
                "conversation_history": conversation_history,
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        print(f"Current data: {data.get('extracted_data', {})}")
        
        # Update state
        current_data = data.get('extracted_data', {})
        conversation_history = data.get('conversation_history', [])
        last_ava_message = data.get('last_ava_message', '')
        
        # Test case 2: Phone number
        print("\n2️⃣ Testing phone number collection...")
        user_input = "+385992530806"
        print(f"User: {user_input}")
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": user_input,
                "current_data": current_data,
                "conversation_history": conversation_history,
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        
        # Update state
        current_data = data.get('extracted_data', {})
        conversation_history = data.get('conversation_history', [])
        last_ava_message = data.get('last_ava_message', '')
        
        # Test case 3: Password collection - THE KEY TEST
        print("\n3️⃣ Testing password collection (critical test)...")
        user_input = "Dobraguza"
        print(f"User: {user_input}")
        print(f"Last AVA message was: '{last_ava_message}'")
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": user_input,
                "current_data": current_data,
                "conversation_history": conversation_history,
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        print(f"✅ Password accepted: {'password' in data.get('extracted_data', {}) and data['extracted_data']['password'] == 'Dobraguza'}")
        
        # Update state
        current_data = data.get('extracted_data', {})
        conversation_history = data.get('conversation_history', [])
        last_ava_message = data.get('last_ava_message', '')
        
        # Test case 4: Farm name
        print("\n4️⃣ Testing farm name collection...")
        user_input = "Sunflower Haven"
        print(f"User: {user_input}")
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": user_input,
                "current_data": current_data,
                "conversation_history": conversation_history,
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"AVA: {data['message']}")
        print(f"Status: {data.get('status')}")
        print(f"Registration successful: {data.get('registration_successful', False)}")
        
        if data.get('status') == 'COMPLETE':
            print("\n✅ Registration completed successfully!")
            print(f"Final data: {json.dumps(data.get('extracted_data', {}), indent=2)}")
        else:
            print("\n❌ Registration did not complete")

if __name__ == "__main__":
    asyncio.run(test_registration_conversation())