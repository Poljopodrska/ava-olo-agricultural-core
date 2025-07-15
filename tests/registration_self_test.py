#!/usr/bin/env python3
"""
Automated self-testing for registration flow
"""
import asyncio
import aiohttp
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RegistrationSelfTest:
    """Automated self-testing for registration flow"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
    
    async def run_complete_flow_test(self):
        """Test complete registration flow"""
        
        test_cases = [
            # Test Case 1: Standard flow
            {
                "name": "Standard Registration",
                "steps": [
                    {"input": "Alma", "expect_contains": ["last name", "surname"]},
                    {"input": "Udovčić", "expect_contains": ["WhatsApp", "phone"]},
                    {"input": "+385912345678", "expect_contains": ["password"]},
                    {"input": "mojafarma123", "expect_contains": ["confirm", "again"]},
                    {"input": "mojafarma123", "expect_contains": ["farm", "called"]},
                    {"input": "Udovčić Farm", "expect_contains": ["Welcome", "ready"]}
                ]
            },
            
            # Test Case 2: Password with spaces
            {
                "name": "Password With Spaces",
                "steps": [
                    {"input": "Marko Horvat", "expect_contains": ["WhatsApp", "phone"]},
                    {"input": "+385987654321", "expect_contains": ["password"]},
                    {"input": "Slavonski Brod", "expect_contains": ["confirm", "Slavonski Brod"]},
                    {"input": "Slavonski Brod", "expect_contains": ["farm", "called"]},
                    {"input": "Velika farma", "expect_contains": ["Welcome", "ready"]}
                ]
            }
        ]
        
        for test_case in test_cases:
            await self._run_test_case(test_case)
        
        return self._generate_test_report()
    
    async def _run_test_case(self, test_case):
        """Run a single test case"""
        
        print(f"\n🧪 Testing: {test_case['name']}")
        current_data = {}
        conversation_history = []
        last_ava_message = "Hi! I'm AVA, your agricultural assistant. What's your full name? (first and last name)"
        
        for i, step in enumerate(test_case['steps']):
            print(f"  Step {i+1}: '{step['input']}'")
            
            try:
                # Send request
                response = await self._send_request(step['input'], current_data, conversation_history, last_ava_message)
                
                # Check expectations
                success = self._check_expectations(response, step['expect_contains'])
                
                if success:
                    print(f"    ✅ Expected content found")
                    current_data = response.get('extracted_data', current_data)
                    conversation_history = response.get('conversation_history', conversation_history)
                    last_ava_message = response.get('last_ava_message', response.get('message', ''))
                    
                    # Check if registration completed
                    if response.get('status') == 'COMPLETE':
                        print(f"    🎉 Registration completed!")
                        
                else:
                    print(f"    ❌ FAILED - Expected: {step['expect_contains']}")
                    print(f"    📝 Got: {response.get('message', 'No response')}")
                    self.test_results.append({
                        "test": test_case['name'],
                        "step": i+1,
                        "input": step['input'],
                        "expected": step['expect_contains'],
                        "actual": response.get('message', ''),
                        "status": "FAILED"
                    })
                    break
                    
            except Exception as e:
                print(f"    ❌ ERROR - {str(e)}")
                self.test_results.append({
                    "test": test_case['name'],
                    "step": i+1,
                    "input": step['input'],
                    "expected": step['expect_contains'],
                    "actual": f"Error: {str(e)}",
                    "status": "ERROR"
                })
                break
        else:
            print(f"  🎉 {test_case['name']} - ALL STEPS PASSED!")
            self.test_results.append({
                "test": test_case['name'],
                "status": "PASSED"
            })
    
    async def _send_request(self, user_input, current_data, conversation_history, last_ava_message):
        """Send request to registration endpoint"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/auth/chat-register",
                json={
                    "user_input": user_input,
                    "current_data": current_data,
                    "conversation_history": conversation_history,
                    "last_ava_message": last_ava_message
                }
            ) as response:
                return await response.json()
    
    def _check_expectations(self, response, expect_contains):
        """Check if response contains expected content"""
        
        message = response.get('message', '').lower()
        return any(expected.lower() in message for expected in expect_contains)
    
    def _generate_test_report(self):
        """Generate test report"""
        
        passed = len([r for r in self.test_results if r.get('status') == 'PASSED'])
        total = len([r for r in self.test_results if 'status' in r])
        
        print(f"\n📊 TEST REPORT:")
        print(f"✅ Passed: {passed}/{total}")
        
        failures = [r for r in self.test_results if r.get('status') in ['FAILED', 'ERROR']]
        if failures:
            print(f"❌ Failures:")
            for failure in failures:
                print(f"  - {failure['test']} Step {failure['step']}: '{failure['input']}'")
                print(f"    Expected: {failure['expected']}")
                print(f"    Got: {failure['actual']}")
        
        return {
            "passed": passed,
            "total": total,
            "success_rate": passed/total if total > 0 else 0,
            "failures": failures
        }

# CLI command: python -m tests.registration_self_test
if __name__ == "__main__":
    async def main():
        base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
        tester = RegistrationSelfTest(base_url)
        await tester.run_complete_flow_test()
    
    asyncio.run(main())