#!/usr/bin/env python3
"""
Test Constitutional Checklist Fix
Test the exact Peter scenario that was failing
"""
import asyncio
import aiohttp
import json

async def test_constitutional_peter_fix():
    """Test the exact failing scenario: Peter -> Knaflič -> re-asking bug"""
    
    print("🏛️ Testing Constitutional Checklist Fix")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    conversation_id = "constitutional-test-123"
    
    # The exact failing scenario from user feedback
    test_conversation = [
        {"input": "Peter", "should_ask_for": "last name", "should_not_reask": []},
        {"input": "Knaflič", "should_ask_for": "WhatsApp", "should_not_reask": ["name", "Peter"]},
        {"input": "+38641348550", "should_ask_for": "password", "should_not_reask": ["name", "phone", "WhatsApp"]},
        {"input": "testpass123", "should_ask_for": "confirm", "should_not_reask": ["name", "phone"]},
        {"input": "testpass123", "should_ask_for": "farm", "should_not_reask": ["name", "phone", "password"]},
        {"input": "Knaflič Farm", "should_ask_for": "complete", "should_not_reask": ["name", "phone", "password", "farm"]}
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🎯 Testing constitutional intelligence...")
        
        for i, step in enumerate(test_conversation, 1):
            print(f"\nStep {i}: User says '{step['input']}'")
            
            try:
                response = await session.post(
                    f"{base_url}/api/v1/auth/chat-register",
                    json={
                        "user_input": step['input'],
                        "conversation_id": conversation_id,
                        "current_data": {},
                        "conversation_history": [],
                        "last_ava_message": ""
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    ava_message = data.get('message', '').lower()
                    
                    print(f"  🤖 AVA: {data.get('message', '')}")
                    print(f"  📊 Data: {json.dumps(data.get('extracted_data', {}), indent=2)}")
                    
                    # Check that AVA asks for the right thing
                    should_ask = step['should_ask_for'].lower()
                    if should_ask in ava_message or (should_ask == "complete" and "welcome" in ava_message):
                        print(f"  ✅ Correctly asking for: {step['should_ask_for']}")
                    else:
                        print(f"  ❌ Expected to ask for '{step['should_ask_for']}' but got: {ava_message}")
                    
                    # Critical test: Check it's NOT re-asking for data it already has
                    re_asking_issues = []
                    for forbidden in step['should_not_reask']:
                        if forbidden.lower() in ava_message:
                            re_asking_issues.append(forbidden)
                    
                    if re_asking_issues:
                        print(f"  ❌ CONSTITUTIONAL VIOLATION: Re-asking for {re_asking_issues}")
                    else:
                        print(f"  ✅ Constitutional success: Not re-asking for collected data")
                    
                    # Check if registration complete
                    if data.get('status') == 'COMPLETE':
                        print(f"  🎉 Registration completed successfully!")
                        break
                        
                else:
                    print(f"  ❌ HTTP {response.status}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                break

async def test_checklist_display():
    """Test the constitutional checklist display"""
    
    print("\n🧠 Testing Constitutional Checklist Display")
    print("=" * 45)
    
    try:
        from registration_memory import RegistrationChatWithMemory
        from config_manager import config
        
        # Create memory instance
        memory_chat = RegistrationChatWithMemory(config.openai_api_key)
        
        print("Initial constitutional checklist:")
        print(memory_chat._create_checklist_display())
        
        # Simulate the Peter scenario
        print(f"\n--- After user says 'Peter' ---")
        # Don't set full_name yet - waiting for last name
        print(memory_chat._create_checklist_display())
        
        print(f"\n--- After completing name 'Peter Knaflič' ---")
        memory_chat.required_data["full_name"] = "Peter Knaflič"
        print(memory_chat._create_checklist_display())
        
        print(f"\n--- After getting phone number ---")
        memory_chat.required_data["wa_phone_number"] = "+38641348550"
        print(memory_chat._create_checklist_display())
        
        print(f"\nThis constitutional checklist prevents re-asking! 🏛️")
        
    except Exception as e:
        print(f"Demo error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Constitutional Registration Fix")
    asyncio.run(test_constitutional_peter_fix())
    asyncio.run(test_checklist_display())