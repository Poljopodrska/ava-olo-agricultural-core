"""
Test CAVA LLM with mock OpenAI responses
Simulates what would happen with real OpenAI API
"""
import asyncio
import json
from unittest.mock import patch, MagicMock
from cava_registration_llm import CAVARegistrationLLM, registration_sessions

# Mock OpenAI responses for each test case
MOCK_RESPONSES = {
    "Ljubljana": {
        "response": "I see you're from Ljubljana! That's a beautiful city in Slovenia. What's your name?",
        "extracted_data": {
            "first_name": None,
            "last_name": None,
            "whatsapp_number": None,
            "farm_location": "Ljubljana",
            "primary_crops": None
        },
        "language_detected": "en",
        "confidence": {
            "location_vs_name": 0.95
        }
    },
    "I'm from Ljubljana": {
        "response": "Great, you're farming in Ljubljana! What's your first name?",
        "extracted_data": {
            "first_name": None,
            "last_name": None,
            "whatsapp_number": None,
            "farm_location": "Ljubljana",
            "primary_crops": None
        },
        "language_detected": "en"
    },
    "My name is Peter": {
        "response": "Nice to meet you, Peter! What's your last name?",
        "extracted_data": {
            "first_name": "Peter",
            "last_name": None,
            "whatsapp_number": None,
            "farm_location": "Ljubljana",  # Remembers from previous message
            "primary_crops": None
        },
        "language_detected": "en"
    },
    "Hi, I'm Peter Horvat from Ljubljana": {
        "response": "Welcome Peter Horvat from Ljubljana! What crops do you grow on your farm?",
        "extracted_data": {
            "first_name": "Peter",
            "last_name": "Horvat",
            "whatsapp_number": None,
            "farm_location": "Ljubljana",
            "primary_crops": None
        },
        "language_detected": "en"
    },
    "I grow mangoes and corn": {
        "response": "Mangoes and corn - interesting combination! What's your WhatsApp number so we can stay in touch?",
        "extracted_data": {
            "first_name": "Peter",
            "last_name": "Horvat",
            "whatsapp_number": None,
            "farm_location": "Ljubljana",
            "primary_crops": "mangoes, corn"
        },
        "language_detected": "en"
    },
    "Jaz sem Janez": {
        "response": "Pozdravljeni Janez! Kakšen je vaš priimek?",  # Hello Janez! What's your last name?
        "extracted_data": {
            "first_name": "Janez",
            "last_name": None,
            "whatsapp_number": None,
            "farm_location": None,
            "primary_crops": None
        },
        "language_detected": "sl"
    }
}

def create_mock_openai_response(message_content):
    """Create a mock OpenAI response based on the message"""
    
    # Find the best matching mock response
    for key, response in MOCK_RESPONSES.items():
        if key.lower() in message_content.lower() or message_content.lower() in key.lower():
            return MagicMock(
                choices=[MagicMock(
                    message=MagicMock(
                        content=json.dumps(response)
                    )
                )]
            )
    
    # Default response if no match
    return MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content=json.dumps({
                    "response": "Could you tell me more about yourself and your farm?",
                    "extracted_data": {},
                    "language_detected": "en"
                })
            )
        )]
    )

async def test_with_mock():
    """Test CAVA with mocked OpenAI responses"""
    
    print("Testing CAVA LLM with Mock OpenAI")
    print("=" * 60)
    
    # Patch OpenAI
    with patch('openai.ChatCompletion.create') as mock_create:
        # Configure mock to return appropriate responses
        mock_create.side_effect = lambda **kwargs: create_mock_openai_response(
            kwargs['messages'][-1]['content']
        )
        
        # Also mock the API key check
        with patch('os.getenv', return_value='mock-api-key'):
            
            engine = CAVARegistrationLLM()
            
            # Test 1: Ljubljana recognition
            print("\n🧪 Test 1: City Recognition")
            print("-" * 40)
            
            result = await engine.process_registration_message(
                message="Ljubljana",
                session_id="test_city",
                conversation_history=[]
            )
            
            print(f"Farmer: Ljubljana")
            print(f"AVA: {result['response']}")
            print(f"Extracted location: {result['extracted_data'].get('farm_location')}")
            
            if result['extracted_data'].get('farm_location') == 'Ljubljana':
                print("✅ PASS: Ljubljana recognized as city!")
            else:
                print("❌ FAIL: Ljubljana not recognized")
            
            # Test 2: Natural conversation
            print("\n\n🧪 Test 2: Natural Conversation Flow")
            print("-" * 40)
            
            messages = [
                "Hi, I'm Peter Horvat from Ljubljana",
                "I grow mangoes and corn"
            ]
            
            session_id = "test_natural"
            conversation_history = []
            
            for msg in messages:
                result = await engine.process_registration_message(
                    message=msg,
                    session_id=session_id,
                    conversation_history=conversation_history
                )
                
                print(f"\nFarmer: {msg}")
                print(f"AVA: {result['response']}")
                print(f"Collected so far: {json.dumps(result['extracted_data'], indent=2)}")
                
                # Update conversation history
                conversation_history.append({"message": msg, "is_farmer": True})
                conversation_history.append({"message": result['response'], "is_farmer": False})
            
            # Verify final data
            final_data = result['extracted_data']
            expected = {
                "first_name": "Peter",
                "last_name": "Horvat",
                "farm_location": "Ljubljana",
                "primary_crops": "mangoes, corn"
            }
            
            print("\n📊 Verification:")
            all_correct = True
            for field, expected_value in expected.items():
                actual = final_data.get(field)
                if actual == expected_value:
                    print(f"✅ {field}: {actual}")
                else:
                    print(f"❌ {field}: expected '{expected_value}', got '{actual}'")
                    all_correct = False
            
            if all_correct:
                print("\n✅ Natural conversation test PASSED!")
            else:
                print("\n❌ Natural conversation test FAILED!")
            
            # Test 3: Language detection
            print("\n\n🧪 Test 3: Slovenian Language")
            print("-" * 40)
            
            result = await engine.process_registration_message(
                message="Jaz sem Janez",
                session_id="test_slovenian",
                conversation_history=[]
            )
            
            print(f"Farmer: Jaz sem Janez")
            print(f"AVA: {result['response']}")
            print(f"Language detected: {result.get('language_detected', 'unknown')}")
            print(f"Extracted name: {result['extracted_data'].get('first_name')}")
            
            if result['extracted_data'].get('first_name') == 'Janez':
                print("✅ PASS: Slovenian name extracted!")
            else:
                print("❌ FAIL: Slovenian not understood")

if __name__ == "__main__":
    asyncio.run(test_with_mock())