"""
Simple test to verify registration doesn't loop
"""
import asyncio
from cava_registration_engine import CAVARegistrationEngine, registration_sessions

async def test_simple():
    engine = CAVARegistrationEngine()
    session_id = "test-simple-123"
    
    print("Test: Farmer says 'Peter'")
    
    # Direct call to fallback since CAVA isn't working
    result = await engine._fallback_registration(
        message="Peter",
        session_id=session_id,
        conversation_history=[]
    )
    
    print(f"Response: {result['response']}")
    print(f"Collected: {result.get('extracted_data', {})}")
    print(f"Session data: {registration_sessions.get(session_id, {}).get('collected_data', {})}")
    
    # Test second message
    print("\nTest: Farmer says 'Petrov'")
    result2 = await engine._fallback_registration(
        message="Petrov",
        session_id=session_id,
        conversation_history=[]
    )
    
    print(f"Response: {result2['response']}")
    print(f"Collected: {result2.get('extracted_data', {})}")
    print(f"Session data: {registration_sessions.get(session_id, {}).get('collected_data', {})}")

if __name__ == "__main__":
    asyncio.run(test_simple())
