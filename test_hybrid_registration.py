#!/usr/bin/env python3
"""
Test hybrid LLM + coded password system
"""
import asyncio
import aiohttp
import json

async def test_hybrid_registration():
    """Test the hybrid registration system"""
    base_url = "http://localhost:8080"
    
    # Track conversation state
    conversation_history = []
    last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
    current_data = {}
    
    print("🤖 Testing Hybrid LLM + Coded Password System")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test sequence
        test_inputs = [
            ("Marko Horvat", "Name collection"),
            ("+385912345678", "Phone collection"),  
            ("Dobraguza", "Password collection"),
            ("Dobraguza", "Password confirmation"),
            ("Sunflower Farm", "Farm name collection")
        ]
        
        for user_input, description in test_inputs:
            print(f"\n📝 {description}")
            print(f"User: {user_input}")
            
            # Send request
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
            print(f"Handled by: {data.get('handled_by', 'unknown')}")
            
            if data.get('supervision_notes'):
                print(f"Supervision: {data['supervision_notes']}")
            
            # Update state
            if data.get('extracted_data'):
                current_data = data['extracted_data']
            conversation_history = data.get('conversation_history', conversation_history)
            last_ava_message = data.get('last_ava_message', data['message'])
            
            # Show current data
            print(f"Current data: {json.dumps(current_data, indent=2)}")
            
            # Check if complete
            if data.get('status') == 'COMPLETE':
                print("\n✅ Registration completed successfully!")
                print(f"Token: {data.get('token', 'No token')[:20]}...")
                break
        
        # Test password handling edge cases
        print("\n\n🔧 Testing Password Edge Cases")
        print("=" * 60)
        
        # Test 1: Short password
        print("\n1️⃣ Testing short password...")
        current_data = {"full_name": "Ana Novak", "wa_phone_number": "+385987654321"}
        last_ava_message = "Great! Now, could you please create a password? It should be at least 6 characters long."
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "abc",
                "current_data": current_data,
                "conversation_history": [],
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"User: abc")
        print(f"AVA: {data['message']}")
        print(f"Handled by: {data.get('handled_by')}")
        print(f"✅ Correctly rejected: {'too short' in data['message'].lower()}")
        
        # Test 2: Password mismatch
        print("\n2️⃣ Testing password mismatch...")
        current_data["temp_password"] = "ValidPassword123"
        last_ava_message = "Thanks! Please confirm your password by typing 'ValidPassword123' again:"
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "WrongPassword",
                "current_data": current_data,
                "conversation_history": [],
                "last_ava_message": last_ava_message
            }
        )
        
        data = await response.json()
        print(f"User: WrongPassword")
        print(f"AVA: {data['message']}")
        print(f"Handled by: {data.get('handled_by')}")
        print(f"✅ Correctly rejected: {'match' in data['message'].lower()}")

if __name__ == "__main__":
    asyncio.run(test_hybrid_registration())