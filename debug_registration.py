#!/usr/bin/env python3
"""
Interactive registration debugging tool
"""
import asyncio
import aiohttp
import json

async def debug_registration_interactive():
    """Interactive debugging of registration system"""
    
    print("🔧 Interactive Registration Debugger")
    print("=" * 50)
    print("Type 'quit' to exit, 'reset' to start over")
    
    base_url = "http://localhost:8080"
    current_data = {}
    conversation_history = []
    last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
    
    print(f"\n🤖 AVA: {last_ava_message}")
    
    async with aiohttp.ClientSession() as session:
        while True:
            user_input = input("\n👨‍🌾 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'reset':
                current_data = {}
                conversation_history = []
                last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
                print(f"\n🔄 Reset! Starting over.")
                print(f"🤖 AVA: {last_ava_message}")
                continue
            elif user_input.lower() == 'debug':
                print(f"\n🔍 DEBUG INFO:")
                print(f"   Current Data: {json.dumps(current_data, indent=2)}")
                print(f"   Last AVA Message: {last_ava_message}")
                print(f"   Conversation History: {len(conversation_history)} entries")
                continue
            
            try:
                print(f"📡 Sending request...")
                
                response = await session.post(
                    f"{base_url}/api/v1/auth/chat-register",
                    json={
                        "user_input": user_input,
                        "current_data": current_data,
                        "conversation_history": conversation_history,
                        "last_ava_message": last_ava_message
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"🤖 AVA: {data.get('message', 'No response')}")
                    
                    # Show debug info
                    print(f"📊 Status: {data.get('status', 'unknown')}")
                    if data.get('extracted_data'):
                        print(f"📝 Extracted Data: {json.dumps(data['extracted_data'], indent=2)}")
                    
                    # Update state
                    current_data = data.get('extracted_data', current_data)
                    conversation_history = data.get('conversation_history', conversation_history)
                    last_ava_message = data.get('last_ava_message', data.get('message', ''))
                    
                    # Check if registration complete
                    if data.get('status') == 'COMPLETE':
                        print(f"🎉 Registration completed!")
                        if data.get('farmer_id'):
                            print(f"👤 Farmer ID: {data['farmer_id']}")
                        break
                    
                else:
                    print(f"❌ HTTP {response.status}: {await response.text()}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")

async def test_peter_case():
    """Test the specific Peter case that's failing"""
    
    print("🎯 Testing Peter Case Specifically")
    print("=" * 40)
    
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        print("Step 1: Send 'Peter'")
        
        response = await session.post(
            f"{base_url}/api/v1/auth/chat-register",
            json={
                "user_input": "Peter",
                "current_data": {},
                "conversation_history": [],
                "last_ava_message": "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
            }
        )
        
        if response.status == 200:
            data = await response.json()
            print(f"✅ Response: {data.get('message', '')}")
            print(f"📊 Status: {data.get('status', '')}")
            print(f"📝 Data: {json.dumps(data.get('extracted_data', {}), indent=2)}")
            
            # Check if it's asking for last name
            message = data.get('message', '').lower()
            if any(phrase in message for phrase in ['last name', 'surname', 'family name']):
                print("✅ CORRECT: Asking for last name")
            elif 'repeat' in message or 'try again' in message:
                print("❌ FAILED: Asking to repeat (this is the bug)")
            else:
                print("⚠️  UNCLEAR: Unexpected response")
        else:
            print(f"❌ HTTP {response.status}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'peter':
        asyncio.run(test_peter_case())
    else:
        asyncio.run(debug_registration_interactive())