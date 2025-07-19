"""
Quick test for Ljubljana recognition
"""
import asyncio
from cava_registration_llm import CAVARegistrationLLM, registration_sessions

async def test_ljubljana():
    engine = CAVARegistrationLLM()
    
    print("Testing Ljubljana Recognition in Fallback Mode")
    print("=" * 50)
    
    # Test 1: Just "Ljubljana"
    print("\nTest 1: Farmer says 'Ljubljana'")
    result1 = await engine._simple_fallback(
        message="Ljubljana",
        session_id="test_ljubljana_1",
        conversation_history=[]
    )
    
    print(f"Response: {result1['response']}")
    print(f"Extracted: {result1['extracted_data']}")
    
    if result1['extracted_data'].get('farm_location') == 'Ljubljana':
        print("✅ SUCCESS: Ljubljana recognized as location!")
    else:
        print("❌ FAIL: Ljubljana not recognized as location")
    
    # Test 2: "I'm from Ljubljana"
    print("\n\nTest 2: Farmer says 'I'm from Ljubljana'")
    result2 = await engine._simple_fallback(
        message="I'm from Ljubljana",
        session_id="test_ljubljana_2",
        conversation_history=[]
    )
    
    print(f"Response: {result2['response']}")
    print(f"Extracted: {result2['extracted_data']}")
    
    # Test 3: "Peter" should be name, not location
    print("\n\nTest 3: Farmer says 'Peter'")
    result3 = await engine._simple_fallback(
        message="Peter",
        session_id="test_ljubljana_3",
        conversation_history=[]
    )
    
    print(f"Response: {result3['response']}")
    print(f"Extracted: {result3['extracted_data']}")
    
    if result3['extracted_data'].get('first_name') == 'Peter':
        print("✅ SUCCESS: Peter recognized as name!")
    else:
        print("❌ FAIL: Peter not recognized as name")

if __name__ == "__main__":
    asyncio.run(test_ljubljana())