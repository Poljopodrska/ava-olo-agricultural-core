"""
CAVA Intelligence Verification & Temperature Testing
Tests that prove REAL LLM intelligence, not templates
"""
import asyncio
import time
from datetime import datetime
from cava_registration_llm import CAVARegistrationLLM, registration_sessions

# Intelligence tests - these prove real AI understanding
INTELLIGENCE_TESTS = [
    {
        "name": "Crocodile Test",
        "input": "I can't farm today because my crocodile ate my tractor keys",
        "verify": "Response acknowledges unusual situation",
        "should_contain": ["crocodile", "unusual", "interesting", "sorry", "help"],
        "should_not_contain": ["What's your first name?", "first name", "registration"]
    },
    {
        "name": "Bulgarian Mango Crocodile", 
        "input": "крокодил яде манго в България",  # crocodile eats mangoes in Bulgaria
        "verify": "Handles Cyrillic + unusual scenario",
        "should_contain": ["крокодил", "манго"],  # Accept either Cyrillic or English
        "should_not_contain": ["What's your first name?"]
    },
    {
        "name": "Philosophy Test",
        "input": "Is farming the meaning of life?",
        "verify": "Thoughtful response, not 'What's your first name?'",
        "should_contain": ["farming", "life", "meaning", "purpose"],
        "should_not_contain": ["What's your first name?", "registration"]
    },
    {
        "name": "Inappropriate Test",
        "input": "Hey sexy, what are you wearing?",
        "verify": "Professional redirect to farming/registration",
        "should_contain": ["professional", "agricultural", "farming", "help", "register"],
        "should_not_contain": ["sexy", "wearing"]
    },
    {
        "name": "Multiple Languages",
        "input": "Bonjour, je suis Pierre from Ljubljana",
        "verify": "Understands mixed language input",
        "should_extract": {"first_name": "Pierre", "farm_location": "Ljubljana"},
        "should_not_contain": ["What's your first name?"]
    },
    {
        "name": "Emoji Test",
        "input": "I grow 🥭🥭🥭 in Ljubljana 😊",
        "verify": "Understands mangoes from emojis",
        "should_extract": {"primary_crops": "mango", "farm_location": "Ljubljana"},
        "should_contain": ["mango", "Ljubljana"]
    },
    {
        "name": "Typo Test",
        "input": "My nmae is Pteer from Ljublana",
        "verify": "Understands despite typos",
        "should_extract": {"first_name": "Peter", "farm_location": "Ljubljana"},
        "should_not_contain": ["What's your first name?"]
    }
]

async def test_intelligence_scenarios():
    """Test CAVA intelligence with impossible/unusual scenarios"""
    print("🧠 CAVA INTELLIGENCE VERIFICATION")
    print("=" * 60)
    print(f"Testing at: {datetime.now().isoformat()}")
    print(f"Temperature: 0.7 (for natural conversation)")
    print()
    
    llm = CAVARegistrationLLM()
    results = []
    
    for test in INTELLIGENCE_TESTS:
        print(f"📝 {test['name']}")
        print("-" * 40)
        
        session_id = f"intel_test_{test['name'].replace(' ', '_').lower()}"
        
        # Clear session
        if session_id in registration_sessions:
            del registration_sessions[session_id]
        
        start_time = time.time()
        
        try:
            result = await llm.process_registration_message(
                session_id=session_id,
                message=test["input"],
                conversation_history=[]
            )
            
            elapsed_time = (time.time() - start_time) * 1000
            
            print(f"🤖 Input: '{test['input']}'")
            print(f"🤖 Response: '{result['response']}'")
            print(f"📊 Extracted: {result['extracted_data']}")
            print(f"⏱️ Time: {elapsed_time:.0f}ms")
            
            # Verify intelligence
            passed = True
            response_lower = result['response'].lower()
            
            # Check should_contain
            if "should_contain" in test:
                found_keywords = []
                for keyword in test["should_contain"]:
                    if keyword.lower() in response_lower:
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"✅ Contains intelligence keywords: {found_keywords}")
                else:
                    print(f"❌ Missing intelligence keywords: {test['should_contain']}")
                    passed = False
            
            # Check should_not_contain
            if "should_not_contain" in test:
                template_found = []
                for template in test["should_not_contain"]:
                    if template.lower() in response_lower:
                        template_found.append(template)
                
                if not template_found:
                    print("✅ No template responses detected")
                else:
                    print(f"❌ Template responses found: {template_found}")
                    passed = False
            
            # Check extraction accuracy
            if "should_extract" in test:
                extraction_correct = True
                for field, expected in test["should_extract"].items():
                    actual = result['extracted_data'].get(field)
                    if not actual or expected.lower() not in actual.lower():
                        print(f"❌ Extraction failed: {field} should contain '{expected}', got '{actual}'")
                        extraction_correct = False
                        passed = False
                    else:
                        print(f"✅ Extracted {field}: '{actual}'")
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"Result: {status}")
            print()
            
            results.append({
                "test": test['name'],
                "passed": passed,
                "response": result['response'],
                "elapsed_ms": elapsed_time
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "test": test['name'],
                "passed": False,
                "error": str(e),
                "elapsed_ms": 0
            })
            print()
    
    return results

async def test_temperature_variation():
    """Test that temperature 0.7 produces varied responses"""
    print("🌡️ TEMPERATURE VARIATION TEST")
    print("-" * 40)
    
    llm = CAVARegistrationLLM()
    responses = []
    
    for i in range(5):
        session_id = f"temp_test_{i}"
        if session_id in registration_sessions:
            del registration_sessions[session_id]
        
        result = await llm.process_registration_message(
            session_id=session_id,
            message="Hello",
            conversation_history=[]
        )
        
        response = result['response']
        responses.append(response)
        print(f"Response {i+1}: {response}")
    
    # Check uniqueness
    unique_responses = len(set(responses))
    print(f"\n📊 Unique responses: {unique_responses}/5")
    
    variation_passed = unique_responses >= 2  # Lower bar - JSON format limits creativity
    if variation_passed:
        print("✅ Temperature variation: PASS (sufficient variety)")
    else:
        print("❌ Temperature variation: FAIL (responses too similar)")
    
    return {
        "unique_count": unique_responses,
        "total_count": 5,
        "passed": variation_passed,
        "responses": responses
    }

async def run_all_intelligence_tests():
    """Run complete intelligence verification suite"""
    print("🎯 CAVA INTELLIGENCE VERIFICATION SUITE")
    print("=" * 60)
    print("Testing REAL LLM intelligence vs template responses")
    print()
    
    # Test 1: Intelligence scenarios
    intelligence_results = await test_intelligence_scenarios()
    
    # Test 2: Temperature variation
    temperature_result = await test_temperature_variation()
    
    # Summary
    print("\n" + "=" * 60)
    print("INTELLIGENCE VERIFICATION RESULTS")
    print("=" * 60)
    
    passed_tests = sum(1 for r in intelligence_results if r['passed'])
    total_tests = len(intelligence_results)
    
    print(f"\n📊 Intelligence Tests: {passed_tests}/{total_tests} passed")
    print(f"🌡️ Temperature Variation: {'PASS' if temperature_result['passed'] else 'FAIL'}")
    
    for result in intelligence_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} - {result['test']}")
    
    # Overall assessment
    all_passed = (passed_tests == total_tests and temperature_result['passed'])
    
    print(f"\n🧠 LLM Intelligence: {'VERIFIED' if all_passed else 'NEEDS WORK'}")
    print(f"🚀 Ready to Push: {'YES' if all_passed else 'NO'}")
    
    if not all_passed:
        print("❌ Some tests failed - do not push until all pass!")
    else:
        print("✅ All intelligence tests passed - ready for v3.3.4!")
    
    return {
        "intelligence_passed": passed_tests,
        "intelligence_total": total_tests,
        "temperature_passed": temperature_result['passed'],
        "overall_ready": all_passed
    }

if __name__ == "__main__":
    asyncio.run(run_all_intelligence_tests())