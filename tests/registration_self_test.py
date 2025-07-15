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
        
        self.basic_test_cases = [
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
        
        for test_case in self.basic_test_cases:
            await self._run_test_case(test_case)
        
        return self._generate_test_report()
    
    async def run_stress_test(self):
        """Run all test scenarios including edge cases"""
        
        # Extended test cases for comprehensive testing
        extended_test_cases = [
            
            # Test Case 3: Two First Names + Last Name
            {
                "name": "Two First Names",
                "steps": [
                    {"input": "Ana Marija", "expect_contains": ["last name", "surname"]},
                    {"input": "Kovačević", "expect_contains": ["Ana Marija Kovačević", "WhatsApp", "phone"]},
                    {"input": "+385911234567", "expect_contains": ["password"]},
                    {"input": "password123", "expect_contains": ["confirm", "password123"]},
                    {"input": "password123", "expect_contains": ["farm", "called"]},
                    {"input": "Kovačević Farm", "expect_contains": ["Welcome", "Ana Marija"]}
                ]
            },
            
            # Test Case 4: Full Name Immediately  
            {
                "name": "Full Name Immediately",
                "steps": [
                    {"input": "Petar Jovanović", "expect_contains": ["Petar Jovanović", "WhatsApp", "phone"]},
                    {"input": "+381641234567", "expect_contains": ["password"]},
                    {"input": "Belgrade2024", "expect_contains": ["confirm", "Belgrade2024"]},
                    {"input": "Belgrade2024", "expect_contains": ["farm", "called"]},
                    {"input": "Jovanović Organic Farm", "expect_contains": ["Welcome", "Petar"]}
                ]
            },
            
            # Test Case 5: User Asks Question
            {
                "name": "User Asks Question",
                "steps": [
                    {"input": "What information do you need from me?", "expect_contains": ["name", "need your full name"]},
                    {"input": "Stefan Milosević", "expect_contains": ["Stefan Milosević", "WhatsApp"]},
                    {"input": "Why do you need my phone?", "expect_contains": ["WhatsApp", "contact", "help"]},
                    {"input": "+381642345678", "expect_contains": ["password"]},
                    {"input": "securepass", "expect_contains": ["confirm", "securepass"]},
                    {"input": "securepass", "expect_contains": ["farm"]},
                    {"input": "Green Valley", "expect_contains": ["Welcome", "Stefan"]}
                ]
            },
            
            # Test Case 6: Hyphenated Names
            {
                "name": "Hyphenated Names", 
                "steps": [
                    {"input": "Marie-Claire", "expect_contains": ["last name", "surname"]},
                    {"input": "Babić-Novak", "expect_contains": ["Marie-Claire Babić-Novak", "WhatsApp"]},
                    {"input": "+385923456789", "expect_contains": ["password"]},
                    {"input": "my-farm-2024", "expect_contains": ["confirm", "my-farm-2024"]},
                    {"input": "my-farm-2024", "expect_contains": ["farm"]},
                    {"input": "Babić-Novak Vineyards", "expect_contains": ["Welcome", "Marie-Claire"]}
                ]
            },
            
            # Test Case 7: Phone Without Country Code
            {
                "name": "Phone Without Country Code",
                "steps": [
                    {"input": "Nikola Petrov", "expect_contains": ["WhatsApp", "phone"]},
                    {"input": "0912345678", "expect_contains": ["country code", "+385"]},
                    {"input": "+385912345678", "expect_contains": ["password"]},
                    {"input": "nikola123", "expect_contains": ["confirm", "nikola123"]},
                    {"input": "nikola123", "expect_contains": ["farm"]},
                    {"input": "Petrov Grains", "expect_contains": ["Welcome", "Nikola"]}
                ]
            },
            
            # Test Case 8: Short Password 
            {
                "name": "Short Password Recovery",
                "steps": [
                    {"input": "Milica Stojanović", "expect_contains": ["WhatsApp", "phone"]},
                    {"input": "+381653456789", "expect_contains": ["password"]},
                    {"input": "123", "expect_contains": ["too short", "at least 6"]},
                    {"input": "milica2024", "expect_contains": ["confirm", "milica2024"]},
                    {"input": "milica2024", "expect_contains": ["farm"]},
                    {"input": "Sunny Farm", "expect_contains": ["Welcome", "Milica"]}
                ]
            },
            
            # Test Case 9: Password Confirmation Mismatch
            {
                "name": "Password Mismatch Recovery",
                "steps": [
                    {"input": "Branko Mitrović", "expect_contains": ["WhatsApp", "phone"]},
                    {"input": "+381664567890", "expect_contains": ["password"]},
                    {"input": "branko123", "expect_contains": ["confirm", "branko123"]},
                    {"input": "branko124", "expect_contains": ["don't match", "try again"]},
                    {"input": "branko123", "expect_contains": ["confirm", "branko123"]},
                    {"input": "branko123", "expect_contains": ["farm"]},
                    {"input": "Mitrović Livestock", "expect_contains": ["Welcome", "Branko"]}
                ]
            },
            
            # Test Case 10: Non-English Farm Name
            {
                "name": "Multilingual Farm Names",
                "steps": [
                    {"input": "Dragana Ilić", "expect_contains": ["WhatsApp", "phone"]},
                    {"input": "+381675678901", "expect_contains": ["password"]},
                    {"input": "dragana2024", "expect_contains": ["confirm", "dragana2024"]},
                    {"input": "dragana2024", "expect_contains": ["farm"]},
                    {"input": "Златна Долина", "expect_contains": ["Welcome", "Dragana", "Златна Долина"]},
                ]
            },
            
            # Test Case 11: Only First Name Given
            {
                "name": "Only First Name Confusion",
                "steps": [
                    {"input": "Aleksandar", "expect_contains": ["last name", "surname"]},
                    {"input": "I only have one name", "expect_contains": ["family name", "surname", "last name"]},
                    {"input": "Aleksandrović", "expect_contains": ["Aleksandar Aleksandrović", "WhatsApp"]},
                    {"input": "+381686789012", "expect_contains": ["password"]},
                    {"input": "aleksandar", "expect_contains": ["confirm", "aleksandar"]},
                    {"input": "aleksandar", "expect_contains": ["farm"]},
                    {"input": "Mountain Farm", "expect_contains": ["Welcome", "Aleksandar"]}
                ]
            },
            
            # Test Case 12: Special Characters in Names
            {
                "name": "Special Characters",
                "steps": [
                    {"input": "Željko Đorđević", "expect_contains": ["Željko Đorđević", "WhatsApp"]},
                    {"input": "+381697890123", "expect_contains": ["password"]},
                    {"input": "željko123", "expect_contains": ["confirm", "željko123"]},
                    {"input": "željko123", "expect_contains": ["farm"]},
                    {"input": "Đorđević Voće", "expect_contains": ["Welcome", "Željko", "Đorđević Voće"]}
                ]
            },
            
            # Test Case 13: Very Long Names
            {
                "name": "Long Names",
                "steps": [
                    {"input": "Anastasija Aleksandrovna", "expect_contains": ["last name", "surname"]},
                    {"input": "Konstantinović-Petrović", "expect_contains": ["Anastasija Aleksandrovna Konstantinović-Petrović", "WhatsApp"]},
                    {"input": "+381640123456", "expect_contains": ["password"]},
                    {"input": "anastasija2024", "expect_contains": ["confirm", "anastasija2024"]},
                    {"input": "anastasija2024", "expect_contains": ["farm"]},
                    {"input": "Konstantinović Family Estate", "expect_contains": ["Welcome", "Anastasija"]}
                ]
            },
            
            # Test Case 14: User Changes Mind
            {
                "name": "User Corrections",
                "steps": [
                    {"input": "Miloš", "expect_contains": ["last name", "surname"]},
                    {"input": "Wait, my full name is Miloš Radivojević", "expect_contains": ["Miloš Radivojević", "WhatsApp"]},
                    {"input": "+381651234567", "expect_contains": ["password"]},
                    {"input": "Actually, can I change my phone number?", "expect_contains": ["phone", "number"]},
                    {"input": "+381652345678", "expect_contains": ["password"]},
                    {"input": "milos123", "expect_contains": ["confirm", "milos123"]},
                    {"input": "milos123", "expect_contains": ["farm"]},
                    {"input": "Radivojević Farm", "expect_contains": ["Welcome", "Miloš"]}
                ]
            },
            
            # Test Case 15: Emoji and Special Cases
            {
                "name": "Edge Cases",
                "steps": [
                    {"input": "Marko 🚜", "expect_contains": ["last name", "surname"]},
                    {"input": "Farmović", "expect_contains": ["Marko", "WhatsApp"]},  # Should handle emoji gracefully
                    {"input": "+385641111111", "expect_contains": ["password"]},
                    {"input": "tractor@farm", "expect_contains": ["confirm", "tractor@farm"]},
                    {"input": "tractor@farm", "expect_contains": ["farm"]},
                    {"input": "🚜 Happy Farm 🌾", "expect_contains": ["Welcome", "Marko"]}
                ]
            }
        ]
        
        # Initialize basic test cases if not already done
        if not hasattr(self, 'basic_test_cases'):
            self.basic_test_cases = [
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
        
        all_test_cases = self.basic_test_cases + extended_test_cases
        
        print(f"🧪 Running {len(all_test_cases)} comprehensive test scenarios...")
        
        for i, test_case in enumerate(all_test_cases, 1):
            print(f"\n[{i}/{len(all_test_cases)}] {test_case['name']}")
            await self._run_test_case(test_case)
        
        return self._generate_detailed_report()
    
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
    
    def _generate_detailed_report(self):
        """Generate comprehensive test report"""
        
        passed_tests = [r for r in self.test_results if r.get('status') == 'PASSED']
        failed_tests = [r for r in self.test_results if r.get('status') in ['FAILED', 'ERROR']]
        
        print(f"\n" + "="*60)
        print(f"📊 COMPREHENSIVE TEST REPORT")
        print(f"="*60)
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        total_tests = len(passed_tests) + len(failed_tests)
        success_rate = len(passed_tests)/total_tests if total_tests > 0 else 0
        print(f"📈 SUCCESS RATE: {success_rate*100:.1f}%")
        
        if failed_tests:
            print(f"\n🚨 FAILED SCENARIOS:")
            for failure in failed_tests:
                print(f"  • {failure['test']}")
                print(f"    Step {failure['step']}: '{failure['input']}'")
                print(f"    Expected: {failure['expected']}")
                print(f"    Got: {failure['actual'][:100]}...")
                print()
        
        if passed_tests:
            print(f"✅ PASSED SCENARIOS:")
            for success in passed_tests:
                print(f"  • {success['test']}")
        
        # Categorize failure types
        failure_categories = {}
        for failure in failed_tests:
            category = self._categorize_failure(failure)
            failure_categories[category] = failure_categories.get(category, 0) + 1
        
        if failure_categories:
            print(f"\n🔍 FAILURE ANALYSIS:")
            for category, count in failure_categories.items():
                print(f"  • {category}: {count} failures")
        
        # Recommendation
        if success_rate >= 0.85:
            print(f"\n🎯 RECOMMENDATION: DEPLOY")
        else:
            print(f"\n⚠️  RECOMMENDATION: FIX_ISSUES")
        
        return {
            "total_tests": total_tests,
            "passed": len(passed_tests),
            "failed": len(failed_tests),
            "success_rate": success_rate,
            "failure_categories": failure_categories,
            "failures": failed_tests
        }
    
    def _categorize_failure(self, failure):
        """Categorize type of failure for analysis"""
        
        input_text = failure.get('input', '').lower()
        expected = str(failure.get('expected', [])).lower()
        
        if "name" in input_text or "name" in expected:
            return "Name Processing"
        elif "password" in expected:
            return "Password Handling" 
        elif "phone" in expected or "whatsapp" in expected:
            return "Phone Number Processing"
        elif "farm" in expected:
            return "Farm Name Processing"
        else:
            return "General Conversation Flow"

# CLI command: python -m tests.registration_self_test
if __name__ == "__main__":
    async def main():
        base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
        tester = RegistrationSelfTest(base_url)
        await tester.run_complete_flow_test()
    
    asyncio.run(main())