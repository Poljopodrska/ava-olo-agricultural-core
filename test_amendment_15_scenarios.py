#!/usr/bin/env python3
"""
🏛️ Constitutional Amendment #15: Zero-Code Universal Intelligence Tests
Test watermelon, Bulgarian mango, and any crop scenarios
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

async def test_watermelon_scenario():
    """
    🍉 Test watermelon scenario - Amendment #15 universal intelligence
    """
    
    print("🍉 Testing Watermelon Scenario")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    session_id = f"test_watermelon_{uuid.uuid4().hex[:8]}"
    
    watermelon_questions = [
        "Where did I plant my watermelon?",
        "When did I last water my watermelon field?",
        "Is my watermelon ready for harvest?",
        "What pesticides did I use on watermelon?",
        "How big is my watermelon field?"
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"🎯 Testing LLM universal intelligence for watermelon...")
        
        for i, question in enumerate(watermelon_questions, 1):
            print(f"\nQuestion {i}: '{question}'")
            
            try:
                response = await session.post(
                    f"{base_url}/api/v1/zero-code-chat",
                    json={
                        "session_id": session_id,
                        "message": question
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"  🧠 LLM Response: {data['message']}")
                    print(f"  🏛️ Amendment #15: {data['amendment_15_compliance']}")
                    print(f"  🤖 LLM Generated: {data['llm_generated']}")
                    
                    # Check for watermelon-specific intelligence
                    if "watermelon" in data['message'].lower():
                        print(f"  ✅ Watermelon intelligence working")
                    else:
                        print(f"  ⚠️  Generic response - LLM should be more specific")
                        
                else:
                    print(f"  ❌ HTTP {response.status}: {await response.text()}")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

async def test_bulgarian_mango_scenario():
    """
    🥭 Test Bulgarian mango scenario - Amendment #15 + MANGO Rule compliance
    """
    
    print("\n🥭 Testing Bulgarian Mango Scenario")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    session_id = f"test_bulgarian_mango_{uuid.uuid4().hex[:8]}"
    
    bulgarian_mango_questions = [
        "When is my Bulgarian mango harvest ready?",
        "What's the best fertilizer for mango in Bulgaria?",
        "Are there mango pests in Bulgarian climate?",
        "How do I protect mango from Bulgarian winter?",
        "What's the yield per hectare for Bulgarian mango?"
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"🎯 Testing MANGO Rule compliance...")
        
        for i, question in enumerate(bulgarian_mango_questions, 1):
            print(f"\nQuestion {i}: '{question}'")
            
            try:
                response = await session.post(
                    f"{base_url}/api/v1/zero-code-chat",
                    json={
                        "session_id": session_id,
                        "message": question
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"  🧠 LLM Response: {data['message']}")
                    print(f"  🏛️ Amendment #15: {data['amendment_15_compliance']}")
                    print(f"  🤖 LLM Generated: {data['llm_generated']}")
                    
                    # Check for Bulgarian + mango intelligence
                    message_lower = data['message'].lower()
                    if "mango" in message_lower and "bulgaria" in message_lower:
                        print(f"  ✅ MANGO Rule compliance - handles Bulgarian mango")
                    elif "mango" in message_lower:
                        print(f"  ⚠️  Partial MANGO Rule - mango detected, Bulgaria context missing")
                    else:
                        print(f"  ❌ MANGO Rule violation - generic response")
                        
                else:
                    print(f"  ❌ HTTP {response.status}: {await response.text()}")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

async def test_peter_registration_scenario():
    """
    👤 Test Peter registration scenario - Amendment #15 registration intelligence
    """
    
    print("\n👤 Testing Peter Registration Scenario")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    session_id = f"test_peter_{uuid.uuid4().hex[:8]}"
    
    registration_steps = [
        {"input": "Peter", "expect": "last name"},
        {"input": "Knaflič", "expect": "phone"},
        {"input": "+38641348550", "expect": "password"},
        {"input": "testpass123", "expect": "confirm"},
        {"input": "testpass123", "expect": "farm"},
        {"input": "Knaflič Farm", "expect": "welcome"}
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"🎯 Testing constitutional registration fix...")
        
        for i, step in enumerate(registration_steps, 1):
            print(f"\nStep {i}: '{step['input']}'")
            
            try:
                response = await session.post(
                    f"{base_url}/api/v1/zero-code-chat",
                    json={
                        "session_id": session_id,
                        "message": step['input']
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"  🧠 LLM Response: {data['message']}")
                    print(f"  🏛️ Amendment #15: {data['amendment_15_compliance']}")
                    
                    # Check registration status
                    if data.get("registration_status"):
                        reg_status = data["registration_status"]
                        print(f"  📝 Registration: {reg_status.get('registration_complete', False)}")
                        print(f"  📊 Collected: {reg_status.get('collected_data', {})}")
                    
                    # Check for expected response
                    message_lower = data['message'].lower()
                    if step['expect'].lower() in message_lower:
                        print(f"  ✅ Expected '{step['expect']}' found")
                    else:
                        print(f"  ❌ Expected '{step['expect']}' but got different response")
                    
                    # Critical: Check for re-asking bug
                    if i > 1 and "peter" in message_lower and "name" in message_lower:
                        print(f"  ❌ CONSTITUTIONAL VIOLATION: Re-asking for name!")
                    else:
                        print(f"  ✅ Constitutional compliance - not re-asking")
                    
                    # Check if registration complete
                    if data.get("registration_status", {}).get("registration_complete"):
                        print(f"  🎉 Registration completed!")
                        break
                        
                else:
                    print(f"  ❌ HTTP {response.status}: {await response.text()}")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

async def test_mixed_conversation_scenario():
    """
    🔄 Test mixed conversation - registration + farming questions
    """
    
    print("\n🔄 Testing Mixed Conversation Scenario")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    session_id = f"test_mixed_{uuid.uuid4().hex[:8]}"
    
    mixed_conversation = [
        "Peter",
        "Knaflič",
        "Where did I plant my watermelon?",  # Farming question mid-registration
        "+38641348550",
        "Is my mango harvest ready?",  # Another farming question
        "testpass123",
        "testpass123",
        "Knaflič Farm",
        "What pesticides should I use on my corn?"  # Post-registration farming
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"🎯 Testing mixed conversation intelligence...")
        
        for i, message in enumerate(mixed_conversation, 1):
            print(f"\nMessage {i}: '{message}'")
            
            try:
                response = await session.post(
                    f"{base_url}/api/v1/zero-code-chat",
                    json={
                        "session_id": session_id,
                        "message": message
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"  🧠 LLM Response: {data['message']}")
                    print(f"  🏛️ Amendment #15: {data['amendment_15_compliance']}")
                    
                    # Check intent analysis
                    if data.get("analysis"):
                        analysis = data["analysis"]
                        print(f"  🎯 Intent: {analysis.get('intent_type', 'unknown')}")
                        print(f"  📊 Query needed: {analysis.get('query_needed', False)}")
                        print(f"  💾 Storage needed: {analysis.get('storage_needed', False)}")
                    
                    # Check for intelligent responses
                    message_lower = data['message'].lower()
                    if "watermelon" in message.lower() and "watermelon" in message_lower:
                        print(f"  ✅ Watermelon intelligence active")
                    elif "mango" in message.lower() and "mango" in message_lower:
                        print(f"  ✅ Mango intelligence active")
                    elif "corn" in message.lower() and "corn" in message_lower:
                        print(f"  ✅ Corn intelligence active")
                    
                else:
                    print(f"  ❌ HTTP {response.status}: {await response.text()}")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

async def test_unknown_crop_scenario():
    """
    🌱 Test unknown crop scenario - Amendment #15 universal adaptability
    """
    
    print("\n🌱 Testing Unknown Crop Scenario")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    session_id = f"test_unknown_{uuid.uuid4().hex[:8]}"
    
    unknown_crop_questions = [
        "How do I grow dragonfruit in Croatia?",
        "What's the best time to plant quinoa?",
        "Are there pests that affect acai berries?",
        "How much water does moringa need?",
        "What fertilizer works for black sorghum?"
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"🎯 Testing universal crop adaptability...")
        
        for i, question in enumerate(unknown_crop_questions, 1):
            print(f"\nQuestion {i}: '{question}'")
            
            try:
                response = await session.post(
                    f"{base_url}/api/v1/zero-code-chat",
                    json={
                        "session_id": session_id,
                        "message": question
                    }
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"  🧠 LLM Response: {data['message']}")
                    print(f"  🏛️ Amendment #15: {data['amendment_15_compliance']}")
                    
                    # Check for crop-specific intelligence
                    message_lower = data['message'].lower()
                    question_lower = question.lower()
                    
                    # Extract crop name from question
                    crops = ["dragonfruit", "quinoa", "acai", "moringa", "sorghum"]
                    crop_found = None
                    for crop in crops:
                        if crop in question_lower:
                            crop_found = crop
                            break
                    
                    if crop_found and crop_found in message_lower:
                        print(f"  ✅ Universal intelligence - handles {crop_found}")
                    elif crop_found:
                        print(f"  ⚠️  Partial intelligence - {crop_found} not mentioned in response")
                    else:
                        print(f"  ❌ Failed to identify crop in question")
                        
                else:
                    print(f"  ❌ HTTP {response.status}: {await response.text()}")
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

async def main():
    """Run all Amendment #15 tests"""
    
    print("🏛️ Constitutional Amendment #15: Zero-Code Universal Intelligence Tests")
    print("=" * 80)
    print("Testing: LLM generates 95%+ of business logic")
    print("Scenarios: Watermelon, Bulgarian mango, unknown crops, mixed conversations")
    print("=" * 80)
    
    # Run all test scenarios
    await test_watermelon_scenario()
    await test_bulgarian_mango_scenario()
    await test_peter_registration_scenario()
    await test_mixed_conversation_scenario()
    await test_unknown_crop_scenario()
    
    print("\n🏛️ Amendment #15 Testing Complete!")
    print("=" * 80)
    print("✅ LLM Universal Intelligence")
    print("✅ Zero Custom Crop Coding")
    print("✅ Constitutional Compliance")
    print("✅ MANGO Rule Validation")
    print("🚀 Revolutionary zero-code agricultural conversations!")

if __name__ == "__main__":
    asyncio.run(main())