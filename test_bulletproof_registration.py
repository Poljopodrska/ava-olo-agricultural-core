#!/usr/bin/env python3
"""
Test bulletproof password recognition with Serbian/Croatian names
"""
import asyncio
import aiohttp
import json

async def test_bulletproof_registration():
    """Test the bulletproof registration system with multilingual inputs"""
    base_url = "http://localhost:8080"
    
    print("🎯 Testing Bulletproof Password Recognition")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test Case 1: Serbian name with space password
        print("\n🔥 Test Case 1: Serbian name with city as password")
        print("-" * 40)
        
        context = {
            "current_data": {},
            "conversation_history": [],
            "last_ava_message": "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
        }
        
        # Name collection
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Marko Savić",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"User: Marko Savić")
        print(f"AVA: {data['message']}")
        context = {"current_data": data["extracted_data"], "conversation_history": data["conversation_history"], "last_ava_message": data["last_ava_message"]}
        
        # Phone collection
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "+381634567789",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: +381634567789")
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        context = {"current_data": data["extracted_data"], "conversation_history": data["conversation_history"], "last_ava_message": data["last_ava_message"]}
        
        # Password collection - THE KEY TEST
        print("\n🔐 PASSWORD TEST: 'Slavonski Brod' (14 characters with space)")
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Slavonski Brod",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"User: Slavonski Brod")
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        print(f"✅ Password accepted: {data['debug_info'].get('password_action') == 'collecting'}")
        context = {"current_data": data["extracted_data"], "conversation_history": data["conversation_history"], "last_ava_message": data["last_ava_message"]}
        
        # Password confirmation
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Slavonski Brod",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: Slavonski Brod")
        print(f"AVA: {data['message']}")
        print(f"Debug: {data.get('debug_info', {})}")
        print(f"✅ Password confirmed: {data['debug_info'].get('password_action') == 'confirmed'}")
        context = {"current_data": data["extracted_data"], "conversation_history": data["conversation_history"], "last_ava_message": data["last_ava_message"]}
        
        # Farm name - Serbian/Croatian
        print("\n🚜 FARM NAME TEST: 'Velika farma' (Serbian/Croatian)")
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Velika farma",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"User: Velika farma")
        print(f"AVA: {data['message']}")
        print(f"Status: {data['status']}")
        print(f"✅ Registration successful: {data.get('registration_successful', False)}")
        
        # Test Case 2: Edge cases
        print("\n\n🔧 Test Case 2: Edge Cases")
        print("-" * 40)
        
        # Short password test
        context = {
            "current_data": {"full_name": "Ana Novak", "wa_phone_number": "+385912345678"},
            "conversation_history": [],
            "last_ava_message": "Great! Now, could you please create a password? It should be at least 6 characters long."
        }
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "test",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"Testing short password 'test' (4 chars)")
        print(f"AVA: {data['message']}")
        print(f"✅ Correctly rejected: {'too short' in data['message'].lower()}")
        
        # Case-sensitive confirmation test
        print("\n📝 Testing case-sensitive confirmation")
        context = {
            "current_data": {"full_name": "Ana Novak", "wa_phone_number": "+385912345678", "temp_password_for_confirmation": "Zagreb123"},
            "conversation_history": [],
            "last_ava_message": "Thanks! Please confirm your password by typing 'Zagreb123' again:"
        }
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "zagreb123",  # Wrong case
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"User types: zagreb123 (wrong case)")
        print(f"AVA: {data['message']}")
        print(f"✅ Correctly rejected mismatch: {'match' in data['message'].lower()}")

if __name__ == "__main__":
    asyncio.run(test_bulletproof_registration())