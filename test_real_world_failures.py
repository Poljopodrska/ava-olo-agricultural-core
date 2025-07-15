#!/usr/bin/env python3
"""
Real-world failure testing - catch the actual bugs
"""
import asyncio
import aiohttp
import json

async def test_real_world_failures():
    """Test the actual failures that occur in practice"""
    
    print("🚨 Testing Real-World Failures")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # These are the REAL cases that fail in practice
    critical_basic_cases = [
        {
            "name": "Single First Name - Peter",
            "steps": [
                {"input": "Peter", "expect_any": ["last name", "surname", "family name"], "must_not_contain": ["repeat", "try again", "error"]},
                {"input": "Johnson", "expect_any": ["Peter Johnson", "phone", "WhatsApp"], "must_not_contain": ["repeat", "try again", "error"]},
            ]
        },
        {
            "name": "Single First Name - Ana",
            "steps": [
                {"input": "Ana", "expect_any": ["last name", "surname", "family name"], "must_not_contain": ["repeat", "try again", "error"]},
                {"input": "Smith", "expect_any": ["Ana Smith", "phone", "WhatsApp"], "must_not_contain": ["repeat", "try again", "error"]},
            ]
        },
        {
            "name": "Single First Name - John",
            "steps": [
                {"input": "John", "expect_any": ["last name", "surname", "family name"], "must_not_contain": ["repeat", "try again", "error"]},
                {"input": "Doe", "expect_any": ["John Doe", "phone", "WhatsApp"], "must_not_contain": ["repeat", "try again", "error"]},
            ]
        },
        {
            "name": "JSON Parsing Test",
            "steps": [
                {"input": "TestUser", "expect_any": ["last name", "surname"], "must_not_contain": ["repeat", "try again", "error"]},
            ]
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        total_tests = 0
        passed_tests = 0
        
        for test_case in critical_basic_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            
            current_data = {}
            conversation_history = []
            last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
            
            case_passed = True
            
            for i, step in enumerate(test_case['steps']):
                total_tests += 1
                print(f"  Step {i+1}: '{step['input']}'")
                
                try:
                    response = await session.post(
                        f"{base_url}/api/v1/auth/chat-register",
                        json={
                            "user_input": step['input'],
                            "current_data": current_data,
                            "conversation_history": conversation_history,
                            "last_ava_message": last_ava_message
                        }
                    )
                    
                    if response.status == 200:
                        data = await response.json()
                        message = data.get('message', '').lower()
                        
                        print(f"    📝 AVA Response: {data.get('message', '')}")
                        
                        # Check if any expected content is found
                        expected_found = any(expected.lower() in message for expected in step['expect_any'])
                        
                        # Check if any forbidden content is found
                        forbidden_found = any(forbidden.lower() in message for forbidden in step.get('must_not_contain', []))
                        
                        if expected_found and not forbidden_found:
                            print(f"    ✅ PASSED - Found expected content, no forbidden content")
                            passed_tests += 1
                            current_data = data.get('extracted_data', current_data)
                            conversation_history = data.get('conversation_history', conversation_history)
                            last_ava_message = data.get('last_ava_message', data.get('message', ''))
                        else:
                            print(f"    ❌ FAILED")
                            print(f"       Expected any of: {step['expect_any']}")
                            print(f"       Must not contain: {step.get('must_not_contain', [])}")
                            print(f"       Expected found: {expected_found}")
                            print(f"       Forbidden found: {forbidden_found}")
                            case_passed = False
                            break
                    else:
                        print(f"    ❌ HTTP {response.status}: {await response.text()}")
                        case_passed = False
                        break
                        
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    case_passed = False
                    break
            
            if case_passed:
                print(f"  🎉 {test_case['name']} - PASSED!")
            else:
                print(f"  ❌ {test_case['name']} - FAILED!")
        
        print(f"\n📊 REAL-WORLD TEST RESULTS:")
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {passed_tests/total_tests:.1%}")
        
        if passed_tests < total_tests:
            print(f"🚨 CRITICAL: Basic functionality is broken!")
            print(f"🔧 These failures would block real users immediately")
        else:
            print(f"✅ All basic cases working correctly")

if __name__ == "__main__":
    asyncio.run(test_real_world_failures())