"""
Test CAVA Registration Fix
Verify no more infinite loops
"""

import asyncio
from cava_registration_engine import CAVARegistrationEngine

async def test_registration_loop_fix():
    """Test that registration doesn't loop on same question"""
    engine = CAVARegistrationEngine()
    session_id = "test-loop-fix-123"
    
    print("Testing Registration Loop Fix...")
    print("=" * 50)
    
    # Test 1: Farmer says "Peter" - should get last name question
    print("\n📝 Test 1: Farmer types 'Peter'")
    
    # First interaction - empty message to get welcome
    result1 = await engine.process_registration_message(
        message="",
        session_id=session_id,
        conversation_history=[]
    )
    print(f"AVA: {result1['response']}")
    
    # Farmer responds with first name
    history = [
        {"message": result1['response'], "is_farmer": False},
        {"message": "Peter", "is_farmer": True}
    ]
    
    result2 = await engine.process_registration_message(
        message="Peter",
        session_id=session_id,
        conversation_history=history
    )
    
    print(f"Farmer: Peter")
    print(f"AVA: {result2['response']}")
    print(f"✅ Collected data: {result2.get('extracted_data', {})}")
    
    # Verify it's not asking for first name again
    if "first name" in result2['response'].lower() and "peter" not in result2['response'].lower():
        print("❌ FAIL: Still asking for first name!")
    else:
        print("✅ PASS: Moved to next question!")
    
    # Test 2: Continue with last name
    print("\n📝 Test 2: Farmer types 'Petrov'")
    
    history.extend([
        {"message": result2['response'], "is_farmer": False},
        {"message": "Petrov", "is_farmer": True}
    ])
    
    result3 = await engine.process_registration_message(
        message="Petrov",
        session_id=session_id,
        conversation_history=history
    )
    
    print(f"Farmer: Petrov")
    print(f"AVA: {result3['response']}")
    print(f"✅ Collected data: {result3.get('extracted_data', {})}")
    
    # Verify progression
    if "whatsapp" in result3['response'].lower() or "phone" in result3['response'].lower():
        print("✅ PASS: Progressed to phone number!")
    else:
        print("❌ FAIL: Not progressing correctly")
    
    # Test 3: Complete registration flow
    print("\n📝 Test 3: Complete registration")
    
    # Add phone
    history.extend([
        {"message": result3['response'], "is_farmer": False},
        {"message": "+359123456789", "is_farmer": True}
    ])
    
    result4 = await engine.process_registration_message(
        message="+359123456789",
        session_id=session_id,
        conversation_history=history
    )
    print(f"Phone added. AVA: {result4['response'][:50]}...")
    
    # Add location
    history.extend([
        {"message": result4['response'], "is_farmer": False},
        {"message": "Bulgaria", "is_farmer": True}
    ])
    
    result5 = await engine.process_registration_message(
        message="Bulgaria",
        session_id=session_id,
        conversation_history=history
    )
    print(f"Location added. AVA: {result5['response'][:50]}...")
    
    # Add crops
    history.extend([
        {"message": result5['response'], "is_farmer": False},
        {"message": "mangoes", "is_farmer": True}
    ])
    
    result6 = await engine.process_registration_message(
        message="mangoes",
        session_id=session_id,
        conversation_history=history
    )
    
    print(f"Crops added. Registration complete: {result6.get('registration_complete', False)}")
    print(f"Final data: {result6.get('extracted_data', {})}")
    
    if result6.get('registration_complete'):
        print("\n✅ SUCCESS: Registration completed without loops!")
    else:
        print("\n❌ FAIL: Registration not completed")

if __name__ == "__main__":
    asyncio.run(test_registration_loop_fix())