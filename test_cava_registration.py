"""
Test CAVA Registration Engine
Verify natural conversation flow
"""

import asyncio
from cava_registration_engine import CAVARegistrationEngine

async def test_natural_registration():
    """Test various natural registration patterns"""
    engine = CAVARegistrationEngine()
    session_id = "test-session-123"
    
    print("Testing CAVA Registration Engine...")
    print("=" * 50)
    
    # Test 1: Complete info in one message
    print("\nTest 1: Complete info in one message")
    result = await engine.process_registration_message(
        message="Hi, I'm Peter Petrov from Bulgaria, my number is +359123456789",
        session_id=session_id,
        conversation_history=[]
    )
    print(f"Response: {result['response']}")
    print(f"Extracted data: {result.get('extracted_data', {})}")
    print(f"Missing fields: {result.get('missing_fields', [])}")
    
    # Test 2: Partial info
    print("\n\nTest 2: Partial info")
    result = await engine.process_registration_message(
        message="I'm Maria",
        session_id=session_id + "-2",
        conversation_history=[]
    )
    print(f"Response: {result['response']}")
    print(f"Missing fields: {result.get('missing_fields', [])}")
    
    # Test 3: Natural conversation flow
    print("\n\nTest 3: Natural conversation flow")
    history = []
    
    # First message
    result = await engine.process_registration_message(
        message="Hello, I need help with my mango farm",
        session_id=session_id + "-3",
        conversation_history=history
    )
    print(f"AVA: {result['response']}")
    
    history.append({"message": "Hello, I need help with my mango farm", "is_farmer": True})
    history.append({"message": result['response'], "is_farmer": False})
    
    # Second message
    result = await engine.process_registration_message(
        message="I'm Ivan from Plovdiv",
        session_id=session_id + "-3",
        conversation_history=history
    )
    print(f"Farmer: I'm Ivan from Plovdiv")
    print(f"AVA: {result['response']}")
    
    # Test 4: Different language/style
    print("\n\nTest 4: Minimal responses")
    result = await engine.process_registration_message(
        message="John",
        session_id=session_id + "-4",
        conversation_history=[]
    )
    print(f"Farmer: John")
    print(f"AVA: {result['response']}")

if __name__ == "__main__":
    asyncio.run(test_natural_registration())