"""
Test Pure LLM Natural Understanding
No pattern matching - only LLM intelligence
"""
import asyncio
from cava_registration_llm import CAVARegistrationLLM, registration_sessions

# These should pass through pure LLM intelligence
NATURAL_TESTS = [
    {
        "name": "Simple Location",
        "input": "I come from Ljubljana",
        "expected": {"farm_location": "Ljubljana"}
    },
    {
        "name": "Negative Context",
        "input": "My name is not Ljubljana",
        "expected": {"farm_location": None, "first_name": None}
    },
    {
        "name": "Name and Location",
        "input": "Call me Ljubljana from Zagreb",
        "expected": {
            "first_name": "Ljubljana",
            "farm_location": "Zagreb"
        }
    },
    {
        "name": "Complex Context",
        "input": "I used to live in Zagreb but moved my mango farm to Ljubljana last year",
        "expected": {
            "farm_location": "Ljubljana",
            "primary_crops": "mango"
        }
    },
    {
        "name": "Multilingual (Cyrillic)",
        "input": "Аз съм от София",  # Bulgarian: I am from Sofia
        "expected": {"farm_location": "Sofia"}
    },
    {
        "name": "Correction",
        "messages": [
            "I'm Pteer from Ljubljana",
            "Sorry, I meant Peter"
        ],
        "expected": {
            "first_name": "Peter",
            "farm_location": "Ljubljana"
        }
    }
]

async def test_pure_llm_understanding():
    """Test LLM understanding without ANY pattern matching"""
    print("🧠 TESTING PURE LLM NATURAL UNDERSTANDING")
    print("=" * 60)
    print("No pattern matching - only LLM intelligence")
    print()
    
    llm = CAVARegistrationLLM()
    results = []
    
    for test in NATURAL_TESTS:
        print(f"📝 {test['name']}")
        print("-" * 40)
        
        session_id = f"natural_test_{test['name'].replace(' ', '_').lower()}"
        
        # Clear session
        if session_id in registration_sessions:
            del registration_sessions[session_id]
        
        if "messages" in test:
            # Multi-message test
            conversation_history = []
            for msg in test["messages"]:
                print(f"Input: '{msg}'")
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
            print(f"Input: '{test['input']}'")
            final_result = await llm.process_registration_message(
                session_id=session_id,
                message=test["input"],
                conversation_history=[]
            )
        
        print(f"LLM Response: {final_result['response']}")
        print(f"LLM Extracted: {final_result['extracted_data']}")
        
        # Verify natural understanding
        passed = True
        for field, expected in test["expected"].items():
            actual = final_result['extracted_data'].get(field)
            
            if expected is None:
                # Should NOT extract this field
                if actual is not None:
                    print(f"❌ FAIL: Extracted {field}={actual} when should be None")
                    passed = False
                else:
                    print(f"✅ Correctly understood {field} should not be extracted")
            elif isinstance(expected, str):
                # Direct string comparison
                if str(actual).lower() == expected.lower():
                    print(f"✅ Correctly understood {field}='{actual}'")
                else:
                    print(f"❌ FAIL: Expected {field}='{expected}', got '{actual}'")
                    passed = False
            elif expected and actual:
                # Check if crops contain expected
                if expected.lower() in str(actual).lower():
                    print(f"✅ Correctly understood {field} contains '{expected}'")
                else:
                    print(f"❌ FAIL: Expected '{expected}' in {field}, got '{actual}'")
                    passed = False
            else:
                print(f"❌ FAIL: Expected {field}='{expected}', got '{actual}'")
                passed = False
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\nResult: {status}")
        print()
        
        results.append({"test": test['name'], "passed": passed})
    
    # Summary
    print("=" * 60)
    print("NATURAL UNDERSTANDING TEST RESULTS")
    print("=" * 60)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"\n📊 Results: {passed_count}/{total_count} tests passed")
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} - {result['test']}")
    
    print(f"\n🧠 LLM Natural Understanding: {'WORKING' if passed_count == total_count else 'NEEDS IMPROVEMENT'}")
    
    return passed_count == total_count

if __name__ == "__main__":
    asyncio.run(test_pure_llm_understanding())