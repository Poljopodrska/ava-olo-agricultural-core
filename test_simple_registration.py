#!/usr/bin/env python3
"""
Test ultra-simple registration with 'Alma' input
"""
import asyncio
import aiohttp
import json

async def test_simple_registration():
    """Test the simple registration system"""
    base_url = "http://localhost:8080"
    
    print("🎯 Testing Simple Registration")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test Case: Start with just "Alma"
        print("\n✨ Starting with just 'Alma'")
        print("-" * 40)
        
        context = {
            "current_data": {},
            "conversation_history": [],
            "last_ava_message": "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
        }
        
        # First name only
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Alma",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"User: Alma")
        print(f"AVA: {data['message']}")
        print(f"Status: {data['status']}")
        
        # Check if it asks for last name
        if "last name" in data['message'].lower():
            print("✅ Correctly asking for last name!")
        else:
            print("❌ Should ask for last name")
        
        # Continue with last name
        context = {"current_data": data["extracted_data"], "conversation_history": data.get("conversation_history", []), "last_ava_message": data.get("last_ava_message", data["message"])}
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Horvat",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: Horvat")
        print(f"AVA: {data['message']}")
        print(f"Extracted: {data['extracted_data']}")
        
        # Continue with phone
        context = {"current_data": data["extracted_data"], "conversation_history": data.get("conversation_history", []), "last_ava_message": data.get("last_ava_message", data["message"])}
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "+385912345678",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: +385912345678")
        print(f"AVA: {data['message']}")
        
        # Password
        context = {"current_data": data["extracted_data"], "conversation_history": data.get("conversation_history", []), "last_ava_message": data.get("last_ava_message", data["message"])}
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "testpass123",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: testpass123")
        print(f"AVA: {data['message']}")
        
        # Confirm password
        context = {"current_data": data["extracted_data"], "conversation_history": data.get("conversation_history", []), "last_ava_message": data.get("last_ava_message", data["message"])}
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "testpass123",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: testpass123")
        print(f"AVA: {data['message']}")
        
        # Farm name
        context = {"current_data": data["extracted_data"], "conversation_history": data.get("conversation_history", []), "last_ava_message": data.get("last_ava_message", data["message"])}
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Simple Test Farm",
                "current_data": context["current_data"],
                "conversation_history": context["conversation_history"],
                "last_ava_message": context["last_ava_message"]
            }
        )
        data = await response.json()
        print(f"\nUser: Simple Test Farm")
        print(f"AVA: {data['message']}")
        print(f"Status: {data['status']}")
        print(f"✅ Registration successful: {data.get('registration_successful', False)}")

if __name__ == "__main__":
    asyncio.run(test_simple_registration())