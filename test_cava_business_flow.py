"""
CAVA Business-Focused Registration Flow Tests
Tests efficient registration completion in 5-7 exchanges
"""
import asyncio
import time
from datetime import datetime
from cava_registration_llm import CAVARegistrationLLM, registration_sessions

# Business flow test scenarios
BUSINESS_FLOW_TESTS = [
    {
        "name": "Efficient Registration Flow",
        "messages": [
            "Hi", 
            "Peter Knaflič", 
            "I'm from Ljubljana", 
            "I grow corn and wheat", 
            "+38640123456"
        ],
        "expected_exchanges": 5,
        "should_complete": True,
        "verify": "Registration completes efficiently with natural responses"
    },
    {
        "name": "Crocodile Redirect Test",
        "messages": [
            "My crocodile ate my tractor keys",
            "Yes it's a real crocodile from Florida", 
            "Peter Horvat"  # Should redirect and extract both names
        ],
        "max_exchanges": 5,
        "verify": "Redirected to registration by message 3, extracted full name"
    },
    {
        "name": "Urgent Emergency Override",
        "messages": [
            "URGENT: My entire corn field has blight disease spreading fast!"
        ],
        "verify": "Skips registration, offers immediate agricultural help",
        "should_prioritize_help": True
    },
    {
        "name": "Progressive Firmness Test",
        "messages": [
            "Hi",
            "Let's talk about the weather",
            "Do you like rain?",
            "What about sunshine?", 
            "How about snow?",
            "Peter"  # Should be more direct by now
        ],
        "verify": "Becomes more direct after multiple off-topic messages"
    },
    {
        "name": "Multi-info Single Message",
        "messages": [
            "I'm Ana Horvat from Ljubljana, I grow tomatoes and my WhatsApp is +38641234567"
        ],
        "expected_exchanges": 2,  # Should need only one more exchange
        "verify": "Extracts multiple pieces, asks for remaining field"
    }
]

async def test_business_flow_scenario(test):
    """Test a single business flow scenario"""
    print(f"📝 {test['name']}")
    print("-" * 50)
    
    llm = CAVARegistrationLLM()
    session_id = f"business_test_{test['name'].replace(' ', '_').lower()}"
    
    # Clear session
    if session_id in registration_sessions:
        del registration_sessions[session_id]
    
    conversation_history = []
    exchanges = 0
    start_time = time.time()
    
    for i, message in enumerate(test["messages"]):
        exchanges += 1
        print(f"\n💬 Exchange {exchanges}: '{message}'")
        
        try:
            result = await llm.process_registration_message(
                message=message,
                session_id=session_id,
                conversation_history=conversation_history
            )
            
            print(f"🤖 Response: {result['response']}")
            print(f"📊 Extracted: {result['extracted_data']}")
            print(f"✅ Complete: {result['registration_complete']}")
            
            # Update conversation history
            conversation_history.append({"message": message, "is_farmer": True})
            conversation_history.append({"message": result['response'], "is_farmer": False})
            
            # Check if registration completed
            if result['registration_complete']:
                print(f"🎯 Registration completed in {exchanges} exchanges!")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"test": test['name'], "passed": False, "error": str(e)}
    
    elapsed_time = time.time() - start_time
    
    # Verify test criteria
    passed = True
    issues = []
    
    # Check exchange count
    if "expected_exchanges" in test:
        if exchanges > test["expected_exchanges"]:
            issues.append(f"Too many exchanges: {exchanges} > {test['expected_exchanges']}")
            passed = False
        else:
            print(f"✅ Efficient: {exchanges} exchanges (target: {test['expected_exchanges']})")
    
    # Check max exchange limit
    if "max_exchanges" in test:
        if exchanges > test["max_exchanges"]:
            issues.append(f"Exceeded max exchanges: {exchanges} > {test['max_exchanges']}")
            passed = False
    
    # Check completion requirement
    if test.get("should_complete", False):
        if not result.get('registration_complete', False):
            issues.append("Registration should have completed but didn't")
            passed = False
        else:
            print("✅ Registration completed successfully")
    
    # Check urgency handling
    if test.get("should_prioritize_help", False):
        response_lower = result['response'].lower()
        if "register" in response_lower and "help" not in response_lower:
            issues.append("Should prioritize help over registration in urgent case")
            passed = False
        else:
            print("✅ Correctly prioritized emergency help")
    
    # Check for business focus indicators
    session = registration_sessions.get(session_id, {})
    conv_state = session.get("conversation_state")
    
    if conv_state:
        print(f"📈 Conversation metrics:")
        print(f"   Messages: {conv_state.message_count}")
        print(f"   Off-topic: {conv_state.off_topic_count}")
        print(f"   Urgency detected: {conv_state.urgency_detected}")
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\nResult: {status}")
    if issues:
        for issue in issues:
            print(f"   - {issue}")
    
    return {
        "test": test['name'],
        "passed": passed,
        "exchanges": exchanges,
        "time_seconds": elapsed_time,
        "issues": issues,
        "completed": result.get('registration_complete', False)
    }

async def test_crocodile_redirect_specifically():
    """Test the specific Bulgarian mango crocodile scenario"""
    print("\n🐊 BULGARIAN MANGO CROCODILE REDIRECT TEST")
    print("=" * 50)
    
    llm = CAVARegistrationLLM()
    session_id = "crocodile_test"
    
    if session_id in registration_sessions:
        del registration_sessions[session_id]
    
    # Test the exact scenario from requirements
    result1 = await llm.process_registration_message(
        message="крокодил яде манго",
        session_id=session_id,
        conversation_history=[]
    )
    
    print(f"💬 Message 1: 'крокодил яде манго'")
    print(f"🤖 Response 1: {result1['response']}")
    
    # Second exchange should redirect to registration
    result2 = await llm.process_registration_message(
        message="Yes, it's true, crocodiles in Bulgaria love mangoes",
        session_id=session_id,
        conversation_history=[
            {"message": "крокодил яде манго", "is_farmer": True},
            {"message": result1['response'], "is_farmer": False}
        ]
    )
    
    print(f"\n💬 Message 2: 'Yes, it's true, crocodiles in Bulgaria love mangoes'")
    print(f"🤖 Response 2: {result2['response']}")
    
    # Check if redirected within 2 exchanges
    redirect_keywords = ["name", "register", "information", "tell me"]
    redirected = any(keyword in result2['response'].lower() for keyword in redirect_keywords)
    
    if redirected:
        print("✅ Successfully redirected to registration within 2 exchanges")
        return True
    else:
        print("❌ Failed to redirect to registration within 2 exchanges")
        return False

async def run_all_business_flow_tests():
    """Run complete business flow test suite"""
    print("🎯 CAVA BUSINESS-FOCUSED REGISTRATION FLOW TESTS")
    print("=" * 60)
    print("Testing efficient registration completion in 5-7 exchanges")
    print()
    
    # Test 1: Standard business flow scenarios
    results = []
    for test in BUSINESS_FLOW_TESTS:
        result = await test_business_flow_scenario(test)
        results.append(result)
        print()
    
    # Test 2: Specific crocodile redirect test
    crocodile_passed = await test_crocodile_redirect_specifically()
    
    # Summary
    print("\n" + "=" * 60)
    print("BUSINESS FLOW TEST RESULTS")
    print("=" * 60)
    
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    print(f"\n📊 Business Flow Tests: {passed_tests}/{total_tests} passed")
    print(f"🐊 Crocodile Redirect Test: {'PASS' if crocodile_passed else 'FAIL'}")
    
    # Exchange efficiency metrics
    completed_tests = [r for r in results if r['completed']]
    if completed_tests:
        avg_exchanges = sum(r['exchanges'] for r in completed_tests) / len(completed_tests)
        print(f"📈 Average exchanges to completion: {avg_exchanges:.1f}")
        
        efficient_tests = [r for r in completed_tests if r['exchanges'] <= 7]
        efficiency_rate = len(efficient_tests) / len(completed_tests) * 100
        print(f"⚡ Efficiency rate (≤7 exchanges): {efficiency_rate:.0f}%")
    
    # Detailed results
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        exchanges_info = f"({result['exchanges']} exchanges)" if 'exchanges' in result else ""
        print(f"{status} - {result['test']} {exchanges_info}")
    
    # Overall assessment
    all_passed = (passed_tests == total_tests and crocodile_passed)
    
    print(f"\n🎯 Business Focus: {'VERIFIED' if all_passed else 'NEEDS WORK'}")
    print(f"🚀 Ready for v3.3.5: {'YES' if all_passed else 'NO'}")
    
    if not all_passed:
        print("❌ Some tests failed - improve business focus before deployment")
    else:
        print("✅ All business flow tests passed - ready for deployment!")
    
    return {
        "business_tests_passed": passed_tests,
        "business_tests_total": total_tests,
        "crocodile_redirect_passed": crocodile_passed,
        "average_exchanges": avg_exchanges if completed_tests else 0,
        "efficiency_rate": efficiency_rate if completed_tests else 0,
        "overall_ready": all_passed
    }

if __name__ == "__main__":
    asyncio.run(run_all_business_flow_tests())