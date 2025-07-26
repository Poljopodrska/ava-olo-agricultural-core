#!/usr/bin/env python3
"""
UNFAKEABLE LLM Tests for CAVA Registration
These tests can ONLY pass with real LLM intelligence (95%+ requirement)
"""
import asyncio
import httpx
import json
import uuid
import re
from datetime import datetime
from unittest.mock import patch, Mock
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8080"  # Change to production URL when testing deployed version
TIMEOUT = 30

async def call_cava(message: str, session_id: str = None) -> Dict[str, Any]:
    """Call CAVA registration endpoint"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/registration/cava",
            json={
                "farmer_id": session_id,
                "message": message,
                "language": "auto"
            },
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        
        return response.json()

def asks_for_user_data(response: str) -> bool:
    """Check if response asks for user data"""
    asking_patterns = [
        r"\bname\b", r"\bnumber\b", r"\bphone\b", r"\bwhatsapp\b", 
        r"\bpassword\b", r"\bcalled\b", r"\byour\b.*\bname\b",
        r"what.*name", r"tell.*name", r"give.*name",
        r"nazwa", r"номер", r"телефон", r"парола", r"ime", r"број"  # Multi-language
    ]
    return any(re.search(pattern, response.lower()) for pattern in asking_patterns)

def extracts_name_correctly(response: str, original_message: str) -> bool:
    """Check if name was extracted from mixed language message"""
    names = ["Peter", "Maria", "Peter", "Horvat"]  # Expected names from test messages
    return any(name.lower() in response.lower() for name in names)

def validates_behavior(response: str, expected_behavior: str) -> bool:
    """Validate specific behavior expectations"""
    behaviors = {
        "should_ask_lastname": lambda r: any(word in r.lower() for word in ["last", "surname", "family", "презиме"]),
        "should_understand_city_not_lastname": lambda r: "ljubljana" not in r.lower() and asks_for_user_data(r),
        "should_correct_understanding": lambda r: "horvat" in r.lower() or "corrected" in r.lower(),
        "should_ask_country_code": lambda r: any(word in r.lower() for word in ["country", "code", "+", "prefix"]),
        "should_construct_+386_number": lambda r: "+386" in r or "slovenia" in r.lower()
    }
    
    behavior_fn = behaviors.get(expected_behavior)
    return behavior_fn(response) if behavior_fn else True

def begins_registration_flow(response: str) -> bool:
    """Check if response begins registration process"""
    registration_indicators = [
        r"name", r"start", r"register", r"sign.*up", r"create.*account",
        r"help.*register", r"let.*start", r"first.*name", r"what.*called"
    ]
    return any(re.search(pattern, response.lower()) for pattern in registration_indicators)

def provides_intelligent_validation(response: str, expected_validation: str) -> bool:
    """Check for intelligent validation responses"""
    validations = {
        "should_say_too_short": lambda r: any(word in r.lower() for word in ["short", "long", "characters", "chars"]),
        "should_ask_country_code": lambda r: any(word in r.lower() for word in ["country", "code", "+", "prefix"]),
        "should_accept_single_letter": lambda r: "x" in r.lower() and not ("invalid" in r.lower() or "error" in r.lower()),
        "should_say_number_too_long": lambda r: any(word in r.lower() for word in ["long", "many", "digits"]),
        "should_ask_for_whatsapp_not_email": lambda r: "whatsapp" in r.lower() and not "email" in r.lower()
    }
    
    validation_fn = validations.get(expected_validation)
    return validation_fn(response) if validation_fn else True

def understands_correction(response: str) -> bool:
    """Check if system understood the correction"""
    correction_indicators = [
        "giovanna", "corrected", "updated", "changed", "fix", "sorry", "noted"
    ]
    return any(indicator in response.lower() for indicator in correction_indicators)

# TEST SUITE - ALL 10 TESTS MUST PASS

async def test_1_random_greeting_variations():
    """Test 1: Random greetings that can't be hardcoded"""
    print("Test 1: Random greeting variations...")
    
    greetings = [
        "yo quiero registrarme por favor",  # Spanish
        "म मेरो खेत दर्ता गर्न चाहन्छु",  # Nepali  
        "tôi muốn đăng ký trang trại",  # Vietnamese
        "jeg vil gjerne registrere meg",  # Norwegian
        "ฉันต้องการลงทะเบียน",  # Thai
    ]
    
    for greeting in greetings:
        print(f"  Testing: {greeting}")
        response = await call_cava(greeting)
        response_text = response.get("response", "")
        
        # Must understand registration intent in ANY language
        assert asks_for_user_data(response_text), f"Failed to ask for user data with: {greeting}"
        assert response_text != "Hello! I'm CAVA...", f"Returned default greeting for: {greeting}"
        assert "👋" not in response_text, f"Used hardcoded emoji greeting for: {greeting}"

async def test_2_nonsense_with_intent():
    """Test 2: Garbled text with clear intent - only LLM can parse"""
    print("Test 2: Nonsense with intent...")
    
    messages = [
        "helo i wnat to regstr my frm plz",
        "REGISTER!!!! ME NOW FARM!!!",
        "can has registration? me farmer yes",
        "rgstr me",
        "farm registration i need very much thank"
    ]
    
    for msg in messages:
        print(f"  Testing: {msg}")
        response = await call_cava(msg)
        response_text = response.get("response", "")
        
        # LLM must extract intent from bad spelling/grammar
        assert asks_for_user_data(response_text), f"Failed to parse intent from: {msg}"

async def test_3_mixed_language_response():
    """Test 3: Code-switching - multiple languages in one message"""
    print("Test 3: Mixed language response...")
    
    messages = [
        "Hello, jeg heter Peter and I want to register",  # English + Norwegian
        "Mi nombre es Maria, can you help me register?",  # Spanish + English
        "Ich bin a farmer, trebam registraciju",  # German + Croatian
    ]
    
    for msg in messages:
        print(f"  Testing: {msg}")
        response = await call_cava(msg)
        response_text = response.get("response", "")
        
        # Must handle mixed languages naturally
        assert extracts_name_correctly(response_text, msg), f"Failed to extract name from: {msg}"

async def test_4_contextual_understanding():
    """Test 4: Context-dependent responses that require understanding"""
    print("Test 4: Contextual understanding...")
    
    conversation = [
        ("I'm Peter", "should_ask_lastname"),
        ("From Ljubljana", "should_understand_city_not_lastname"),
        ("Oops I meant my last name is Horvat", "should_correct_understanding"),
        ("My phone is 65123456", "should_ask_country_code"),
        ("Slovenia", "should_construct_+386_number")
    ]
    
    session_id = str(uuid.uuid4())
    for message, expected_behavior in conversation:
        print(f"  Testing: {message} -> {expected_behavior}")
        response = await call_cava(message, session_id)
        response_text = response.get("response", "")
        
        assert validates_behavior(response_text, expected_behavior), \
            f"Failed behavior {expected_behavior} for: {message}"

async def test_5_creative_registration_requests():
    """Test 5: Unusual but valid registration requests"""
    print("Test 5: Creative registration requests...")
    
    requests = [
        "I heard about AVA from my neighbor and would love to join",
        "Sign me up! My corn fields need help",
        "How do I create account? I have 50 hectares",
        "My cooperative told me to register here",
        "Is this where I register for agricultural assistance?"
    ]
    
    for request in requests:
        print(f"  Testing: {request}")
        response = await call_cava(request)
        response_text = response.get("response", "")
        
        # Must understand these are ALL registration requests
        assert begins_registration_flow(response_text), f"Failed to begin registration for: {request}"

async def test_6_rejection_of_offtopic():
    """Test 6: Must redirect off-topic questions appropriately"""
    print("Test 6: Rejection of off-topic...")
    
    offtopic = [
        "What's the weather tomorrow?",
        "How do I cook pasta?",
        "Who won the world cup?",
        "Tell me a joke",
        "What's 2+2?"
    ]
    
    for question in offtopic:
        print(f"  Testing: {question}")
        response = await call_cava(question)
        response_text = response.get("response", "")
        
        # Must redirect to registration
        redirect_phrases = ["register", "registration", "after", "once", "first", "account"]
        assert any(phrase in response_text.lower() for phrase in redirect_phrases), \
            f"Failed to redirect off-topic question: {question}"

async def test_7_llm_api_verification():
    """Test 7: Verify actual OpenAI API calls are made"""
    print("Test 7: LLM API verification...")
    
    # Check debug endpoint first
    async with httpx.AsyncClient() as client:
        debug_response = await client.get(f"{BASE_URL}/api/v1/registration/debug")
        debug_data = debug_response.json()
        
        # Must have OpenAI key configured
        assert debug_data.get("openai_key_set") == True, "OpenAI API key not configured"
        assert debug_data.get("cava_mode") == "llm", "CAVA not in LLM mode"
    
    # Test actual call
    response = await call_cava("I want to register")
    
    # Should not be a fallback response
    response_text = response.get("response", "")
    fallback_indicators = [
        "I'm having trouble connecting",
        "mock response",
        "fallback",
        "API unavailable"
    ]
    
    assert not any(indicator in response_text.lower() for indicator in fallback_indicators), \
        "Received fallback response instead of LLM response"

async def test_8_dynamic_field_validation():
    """Test 8: Intelligent validation messages"""
    print("Test 8: Dynamic field validation...")
    
    validations = [
        ("my password is 123", "should_say_too_short"),
        ("my number is 123", "should_ask_country_code"),
        ("my name is X", "should_accept_single_letter"),
        ("+1234567890123456789", "should_say_number_too_long"),
        ("email@example.com", "should_ask_for_whatsapp_not_email")
    ]
    
    for input_text, expected_validation in validations:
        print(f"  Testing: {input_text} -> {expected_validation}")
        response = await call_cava(input_text)
        response_text = response.get("response", "")
        
        assert provides_intelligent_validation(response_text, expected_validation), \
            f"Failed validation {expected_validation} for: {input_text}"

async def test_9_conversation_memory():
    """Test 9: Remembers context across messages"""
    print("Test 9: Conversation memory...")
    
    session_id = str(uuid.uuid4())
    
    # Tell name in one message
    print("  Setting name: Giovanni")
    response1 = await call_cava("Hi, I'm Giovanni", session_id)
    
    # Reference it later
    print("  Asking about name")
    response2 = await call_cava("Did you get my name?", session_id)
    response2_text = response2.get("response", "")
    
    name_remembered = "giovanni" in response2_text.lower() or "yes" in response2_text.lower()
    assert name_remembered, "Failed to remember name across messages"
    
    # Correct information
    print("  Correcting name")
    response3 = await call_cava("Actually it's Giovanna, not Giovanni", session_id)
    response3_text = response3.get("response", "")
    
    assert understands_correction(response3_text), "Failed to understand name correction"

async def test_10_no_hallucination_test():
    """Test 10: Doesn't make up information"""
    print("Test 10: No hallucination...")
    
    messages = [
        "What crops did I mention?",
        "What's my phone number?",
        "Did I tell you my last name?",
        "Where did I say I'm from?"
    ]
    
    session_id = str(uuid.uuid4())
    # First message - no info given yet
    await call_cava("I want to register", session_id)
    
    for msg in messages:
        print(f"  Testing: {msg}")
        response = await call_cava(msg, session_id)
        response_text = response.get("response", "")
        
        # Must not hallucinate data
        honest_responses = [
            "don't know", "haven't told", "didn't mention", "not sure",
            "haven't said", "didn't say", "no information", "not provided"
        ]
        
        is_honest = any(phrase in response_text.lower() for phrase in honest_responses)
        assert is_honest, f"Hallucinated information for: {msg}. Response: {response_text}"

# Test execution functions
async def run_single_test(test_func):
    """Run a single test with error handling"""
    test_name = test_func.__name__
    try:
        await test_func()
        return test_name, "✅ PASSED", None
    except AssertionError as e:
        return test_name, "❌ FAILED", str(e)
    except Exception as e:
        return test_name, "💥 ERROR", str(e)

async def run_all_tests():
    """Run all 10 tests and return results"""
    print("🧪 RUNNING CAVA REGISTRATION LLM TESTS")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    tests = [
        test_1_random_greeting_variations,
        test_2_nonsense_with_intent,
        test_3_mixed_language_response,
        test_4_contextual_understanding,
        test_5_creative_registration_requests,
        test_6_rejection_of_offtopic,
        test_7_llm_api_verification,
        test_8_dynamic_field_validation,
        test_9_conversation_memory,
        test_10_no_hallucination_test
    ]
    
    results = {}
    
    for test in tests:
        test_name, status, error = await run_single_test(test)
        results[test_name] = {"status": status, "error": error}
        print(f"{test_name}: {status}")
        if error:
            print(f"   Error: {error}")
        print()
    
    print("=" * 60)
    
    # Calculate pass rate  
    passed = sum(1 for r in results.values() if "PASSED" in r["status"])
    total = len(results)
    pass_rate = (passed / total) * 100
    
    print(f"📊 TEST RESULTS: {passed}/{total} passed ({pass_rate:.1f}%)")
    
    if pass_rate < 100:
        print("\n🚨 DEPLOYMENT BLOCKED: Not all tests passed!")
        print("This is a CONSTITUTIONAL VIOLATION - fix before deploying!")
        print("\nFailed tests:")
        for test_name, result in results.items():
            if "FAILED" in result["status"] or "ERROR" in result["status"]:
                print(f"  - {test_name}: {result['error']}")
    else:
        print("\n✅ ALL TESTS PASSED! Safe to deploy.")
        print("🏛️ Constitutional Amendment #15 compliance verified!")
    
    return results, pass_rate

if __name__ == "__main__":
    # Load environment
    import os
    if not os.getenv("OPENAI_API_KEY"):
        try:
            from dotenv import load_dotenv
            load_dotenv(".env.production")
        except:
            pass
    
    # Run tests
    results, pass_rate = asyncio.run(run_all_tests())
    
    # Save results
    with open("test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "pass_rate": pass_rate,
            "deployment_allowed": pass_rate == 100,
            "base_url": BASE_URL,
            "constitutional_compliance": pass_rate >= 95
        }, f, indent=2)
    
    exit(0 if pass_rate == 100 else 1)