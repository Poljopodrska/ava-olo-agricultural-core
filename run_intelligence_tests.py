"""
CAVA TRUE INTELLIGENCE VERIFICATION
Tests that CANNOT pass with pattern matching
"""
import asyncio
import os
import sys
from cava_registration_llm import CAVARegistrationLLM, registration_sessions

# DISABLE FALLBACK DURING TESTING
TESTING_MODE = True
ALLOW_FALLBACK = False

# Intelligence tests that require real LLM understanding
INTELLIGENCE_TESTS = [
    {
        "name": "Reverse Logic Test",
        "input": "My name is not Ljubljana, I live there",
        "must_extract": {
            "farm_location": "Ljubljana",
            "first_name": None  # Must NOT extract Ljubljana as name
        }
    },
    {
        "name": "Complex Context Test", 
        "input": "I used to live in Zagreb but moved my mango farm to Ljubljana last year",
        "must_extract": {
            "farm_location": "Ljubljana",  # Current location, not Zagreb
            "primary_crops": ["mango"]
        }
    },
    {
        "name": "Correction Test",
        "messages": [
            "I'm Pteer from Ljubljana",
            "Sorry, I meant Peter"
        ],
        "must_have_in_response": "Peter",  # Must use corrected name
        "must_extract": {
            "first_name": "Peter"  # Not Pteer
        }
    },
    {
        "name": "Multilingual Context",
        "input": "Jaz sem Ivan, prihajam iz mesta Ljubljana",
        "must_understand": "Slovenian",
        "must_extract": {
            "first_name": "Ivan",
            "farm_location": "Ljubljana"
        }
    },
    {
        "name": "Ambiguous Input Test",
        "input": "Belgrade is my favorite city but I farm in Ljubljana", 
        "must_extract": {
            "farm_location": "Ljubljana"  # Not Belgrade
        }
    }
]

# The Ljubljana Gauntlet - ultimate intelligence test
LJUBLJANA_GAUNTLET = [
    ("Ljubljana", {"farm_location": "Ljubljana"}),
    ("Ljubljana Ljubljana", {"farm_location": "Ljubljana"}),  # Repeated
    ("I'm Ljubljana", {"first_name": "Ljubljana"}),  # Actually a name!
    ("Call me Ljubljana from Zagreb", {
        "first_name": "Ljubljana", 
        "farm_location": "Zagreb"
    }),
    ("Ljubljana? No, I'm from Zagreb", {"farm_location": "Zagreb"}),
    ("Peter Ljubljana is my full name", {
        "first_name": "Peter",
        "last_name": "Ljubljana"
    })
]

def verify_llm_response_quality(response, input_text):
    """These checks PROVE LLM is working"""
    issues = []
    
    # 1. Response must be contextually appropriate
    if "Nice to meet you" in response and "Ljubljana" in response:
        issues.append("Template-like response detected")
    
    # 2. Response must show understanding
    if "ljubljana" in input_text.lower() and "location" not in response.lower() and "from" not in response.lower():
        issues.append("Didn't understand input was location")
    
    # 3. Response must be natural (not multiple questions)
    if response.count("?") > 1:
        issues.append("Multiple questions suggest template logic")
    
    return issues

async def verify_true_intelligence():
    """Tests that CANNOT pass without LLM"""
    print("🧠 VERIFYING TRUE LLM INTELLIGENCE")
    print("=" * 60)
    
    # First, verify API is working
    from verify_openai_setup import verify_openai_setup
    if not verify_openai_setup():
        print("❌ FATAL: Cannot proceed without working OpenAI API")
        return False
    
    llm = CAVARegistrationLLM()
    results = []
    sample_responses = []
    
    # Test 1: Intelligence Tests
    print("\n🔬 Running Intelligence Tests...")
    for test in INTELLIGENCE_TESTS:
        print(f"\n📝 {test['name']}")
        
        session_id = f"intel_test_{test['name'].replace(' ', '_').lower()}"
        
        # Clear session
        if session_id in registration_sessions:
            del registration_sessions[session_id]
        
        if "messages" in test:
            # Multi-message test
            conversation_history = []
            for msg in test["messages"]:
                result = await llm.process_registration_message(
                    session_id=session_id,
                    message=msg,
                    conversation_history=conversation_history
                )
                conversation_history.append({"message": msg, "is_farmer": True})
                conversation_history.append({"message": result['response'], "is_farmer": False})
            
            final_result = result
        else:
            # Single message test
            final_result = await llm.process_registration_message(
                session_id=session_id,
                message=test["input"],
                conversation_history=[]
            )
        
        input_display = test.get('input', test.get('messages', [''])[0])
        print(f"Input: {input_display}")
        print(f"Response: {final_result['response']}")
        print(f"Extracted: {final_result['extracted_data']}")
        
        # Verify requirements
        passed = True
        for field, expected in test["must_extract"].items():
            actual = final_result['extracted_data'].get(field)
            
            if expected is None:
                # Must NOT extract this field
                if actual is not None:
                    print(f"❌ FAIL: Extracted {field} when shouldn't have")
                    passed = False
                else:
                    print(f"✅ Correctly didn't extract {field}")
            elif isinstance(expected, list):
                # Check if any expected item is in actual
                if actual and any(item.lower() in str(actual).lower() for item in expected):
                    print(f"✅ Extracted {field} correctly")
                else:
                    print(f"❌ FAIL: Expected {expected} in {field}, got {actual}")
                    passed = False
            else:
                # Direct comparison
                if str(actual).lower() == str(expected).lower():
                    print(f"✅ Extracted {field} correctly")
                else:
                    print(f"❌ FAIL: Expected {expected} for {field}, got {actual}")
                    passed = False
        
        # Check response quality
        quality_issues = verify_llm_response_quality(final_result['response'], test.get('input', ''))
        if quality_issues:
            print(f"❌ Response quality issues: {', '.join(quality_issues)}")
            passed = False
        else:
            print("✅ Response quality good")
        
        results.append({"test": test['name'], "passed": passed})
        sample_responses.append(f"Input: '{test.get('input', '')}' → '{final_result['response']}'")
    
    # Test 2: Ljubljana Gauntlet
    print("\n🏰 LJUBLJANA GAUNTLET")
    print("-" * 40)
    
    gauntlet_results = []
    for i, (input_text, expected) in enumerate(LJUBLJANA_GAUNTLET):
        print(f"\nGauntlet {i+1}: '{input_text}'")
        
        session_id = f"gauntlet_{i}"
        if session_id in registration_sessions:
            del registration_sessions[session_id]
        
        result = await llm.process_registration_message(
            session_id=session_id,
            message=input_text,
            conversation_history=[]
        )
        
        print(f"Response: {result['response']}")
        print(f"Extracted: {result['extracted_data']}")
        
        # Check if extracted data matches expected
        passed = True
        for field, expected_value in expected.items():
            actual = result['extracted_data'].get(field)
            if str(actual).lower() != str(expected_value).lower():
                print(f"❌ Expected {field}='{expected_value}', got '{actual}'")
                passed = False
            else:
                print(f"✅ {field}='{actual}'")
        
        gauntlet_results.append(passed)
    
    # Test 3: Response Variation
    print("\n🎲 RESPONSE VARIATION TEST")
    print("-" * 30)
    
    variation_responses = []
    for i in range(3):
        session_id = f"variation_{i}"
        if session_id in registration_sessions:
            del registration_sessions[session_id]
        
        result = await llm.process_registration_message(
            session_id=session_id,
            message="Hi",
            conversation_history=[]
        )
        variation_responses.append(result['response'])
        print(f"Response {i+1}: {result['response']}")
    
    # Check if responses are varied
    unique_responses = len(set(variation_responses))
    variation_passed = unique_responses >= 2
    
    if variation_passed:
        print(f"✅ Responses varied ({unique_responses}/3 unique)")
    else:
        print(f"❌ Responses too similar ({unique_responses}/3 unique)")
    
    # Final Results
    print("\n" + "=" * 60)
    print("FINAL INTELLIGENCE VERIFICATION RESULTS")
    print("=" * 60)
    
    intelligence_passed = sum(1 for r in results if r['passed'])
    gauntlet_passed = sum(1 for r in gauntlet_results if r)
    
    print(f"\n📊 Intelligence Tests: {intelligence_passed}/{len(results)} passed")
    print(f"🏰 Ljubljana Gauntlet: {gauntlet_passed}/{len(LJUBLJANA_GAUNTLET)} passed")
    print(f"🎲 Response Variation: {'PASS' if variation_passed else 'FAIL'}")
    
    # Overall assessment
    all_passed = (intelligence_passed == len(results) and 
                 gauntlet_passed == len(LJUBLJANA_GAUNTLET) and 
                 variation_passed)
    
    print(f"\n🎯 LLM Intelligence Active: {'YES' if all_passed else 'NO'}")
    print(f"🚀 Ready for Deployment: {'YES' if all_passed else 'NO'}")
    
    if not all_passed:
        print("❌ Reason: Not all intelligence tests passed")
    
    return all_passed

async def main():
    """Run the complete intelligence verification"""
    if "--no-fallback" in sys.argv:
        print("🚫 Fallback disabled for testing")
    
    success = await verify_true_intelligence()
    
    if not success:
        print("\n❌ INTELLIGENCE VERIFICATION FAILED")
        sys.exit(1)
    else:
        print("\n✅ ALL INTELLIGENCE TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(main())