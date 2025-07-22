#!/usr/bin/env python3
"""
Comprehensive LLM Test Suite for Registration
MUST PASS ALL TESTS BEFORE DEPLOYMENT
"""
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Tuple
import uuid

# Test configuration
BASE_URL = "http://localhost:8080"  # Local testing first
# BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"  # Production

class RegistrationLLMTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.results = []
        self.passed = 0
        self.failed = 0
        
    async def send_message(self, message: str) -> Dict:
        """Send message to registration chat endpoint"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'chat_session_id={self.session_id}'
            }
            
            try:
                async with session.post(
                    f"{BASE_URL}/api/v1/chat/registration/message",
                    json={"content": message},
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "response": f"Error: HTTP {response.status}",
                            "connected": False,
                            "error": True
                        }
            except Exception as e:
                return {
                    "response": f"Connection error: {str(e)}",
                    "connected": False,
                    "error": True
                }
    
    async def test_llm_not_hardcoded(self) -> List[Tuple[str, bool, str]]:
        """Test 1-10: Prove real LLM, not coded responses"""
        test_results = []
        
        # Test 1: Nonsense that can't be predicted
        print("\n🧪 Test 1: Purple elephant visa...")
        response1 = await self.send_message("My purple elephant needs a visa for Mars")
        result1 = (
            "sorry" not in response1['response'].lower() and 
            len(response1['response']) > 20 and
            response1.get('connected', False)
        )
        test_results.append(("Purple elephant visa", result1, response1['response'][:100]))
        
        # Test 2: Multiple languages mixed
        print("🧪 Test 2: Multi-language input...")
        response2 = await self.send_message("Bonjour, mein Name ist Петър, necesito ayuda με τα μήλα")
        result2 = (
            any(name in response2['response'] for name in ["Peter", "Петър", "name", "nombre"]) or
            "language" in response2['response'].lower()
        )
        test_results.append(("Multi-language", result2, response2['response'][:100]))
        
        # Test 3: Current events
        print("🧪 Test 3: Current events handling...")
        response3 = await self.send_message("What happened yesterday at exactly 3:47 PM in Ljubljana?")
        result3 = (
            "don't have specific information" in response3['response'] or 
            "real-time" in response3['response'] or
            "cannot" in response3['response'].lower()
        )
        test_results.append(("Current events", result3, response3['response'][:100]))
        
        # Test 4: Mathematical reasoning
        print("🧪 Test 4: Mathematical reasoning...")
        response4 = await self.send_message("If I plant 17 tomatoes in 3 rows, how many are left over?")
        result4 = (
            "2" in response4['response'] or 
            "two" in response4['response'].lower() or
            "remainder" in response4['response'].lower()
        )
        test_results.append(("Math reasoning", result4, response4['response'][:100]))
        
        # Test 5: Context switching
        print("🧪 Test 5: Context switching...")
        await self.send_message("My name is Peter")
        response5 = await self.send_message("Actually, let's talk about quantum physics instead")
        result5 = (
            "quantum" in response5['response'].lower() or 
            "registration" in response5['response'].lower() or
            "focus" in response5['response'].lower()
        )
        test_results.append(("Context switch", result5, response5['response'][:100]))
        
        # Test 6: Emotional intelligence
        print("🧪 Test 6: Emotional intelligence...")
        response6 = await self.send_message("I'm scared my crops will fail and I'll lose everything")
        result6 = (
            len(response6['response']) > 50 and
            any(word in response6['response'].lower() for word in ["understand", "help", "support", "sorry", "difficult"])
        )
        test_results.append(("Emotional response", result6, response6['response'][:100]))
        
        # Test 7: Nonsense words
        print("🧪 Test 7: Nonsense words...")
        response7 = await self.send_message("My flibbertigibbet is acting very kroompulent today")
        result7 = (
            "flibbertigibbet" in response7['response'] or 
            "don't understand" in response7['response'] or
            "clarify" in response7['response'].lower() or
            "mean" in response7['response'].lower()
        )
        test_results.append(("Nonsense words", result7, response7['response'][:100]))
        
        # Test 8: Complex reasoning
        print("🧪 Test 8: Complex reasoning...")
        response8 = await self.send_message("If rain makes crops grow, and growth needs sun, why do crops die in the desert?")
        result8 = len(response8['response']) > 100
        test_results.append(("Complex reasoning", result8, response8['response'][:100]))
        
        # Test 9: Rejection handling
        print("🧪 Test 9: Rejection handling...")
        response9 = await self.send_message("I refuse to give you any information")
        result9 = (
            "force" not in response9['response'].lower() and
            "must" not in response9['response'].lower()
        )
        test_results.append(("Rejection handling", result9, response9['response'][:100]))
        
        # Test 10: Time-sensitive
        print("🧪 Test 10: Time awareness...")
        response10 = await self.send_message("What time is it right now?")
        result10 = (
            "don't have access to current time" in response10['response'] or 
            "cannot tell time" in response10['response'] or
            "exact time" in response10['response'].lower()
        )
        test_results.append(("Time awareness", result10, response10['response'][:100]))
        
        return test_results
    
    async def test_registration_context_maintained(self) -> Tuple[str, bool, str]:
        """Test 11: Ensure registration purpose is maintained"""
        print("\n🧪 Test 11: Registration context...")
        
        # Start new session
        self.session_id = str(uuid.uuid4())
        
        await self.send_message("Let's discuss philosophy")
        response = await self.send_message("What about Socrates?")
        
        # Should eventually mention registration or needed info
        result = (
            any(word in response['response'].lower() for word in ["registration", "name", "whatsapp", "information", "help you", "get started"])
        )
        
        return ("Registration context", result, response['response'][:100])
    
    async def test_no_hardcoded_patterns(self) -> Tuple[str, bool, str]:
        """Test 12: Ensure no pattern matching"""
        print("\n🧪 Test 12: Varied responses...")
        
        # Start new session for each hello
        responses = []
        for i in range(5):
            self.session_id = str(uuid.uuid4())
            response = await self.send_message("Hello")
            responses.append(response['response'])
            await asyncio.sleep(1)  # Small delay between requests
        
        # All responses should be different (not hardcoded)
        unique_responses = len(set(responses))
        result = unique_responses >= 3  # At least 3 different responses out of 5
        
        return ("Varied responses", result, f"{unique_responses}/5 unique responses")
    
    async def test_llm_connectivity(self) -> Tuple[str, bool, str]:
        """Test 0: Basic connectivity test"""
        print("\n🧪 Test 0: LLM Connectivity...")
        
        response = await self.send_message("Hello, are you there?")
        result = (
            response.get('connected', False) and 
            len(response.get('response', '')) > 0 and
            'error' not in response
        )
        
        return ("LLM connectivity", result, response.get('response', 'No response')[:100])
    
    async def run_all_tests(self):
        """Run all tests and generate report"""
        print("=" * 60)
        print("🚀 COMPREHENSIVE LLM TEST SUITE FOR REGISTRATION")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        
        # Test 0: Connectivity
        test0 = await self.test_llm_connectivity()
        self.results.append(test0)
        
        # Tests 1-10: LLM behavior
        test_results = await self.test_llm_not_hardcoded()
        self.results.extend(test_results)
        
        # Test 11: Context
        test11 = await self.test_registration_context_maintained()
        self.results.append(test11)
        
        # Test 12: Variation
        test12 = await self.test_no_hardcoded_patterns()
        self.results.append(test12)
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test results report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        print("=" * 60)
        
        # Save to file
        with open("test_results.md", "w") as f:
            f.write("# LLM Registration Test Results\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Test Results\n\n")
            
            for i, (test_name, passed, response) in enumerate(self.results):
                status = "✅" if passed else "❌"
                print(f"{status} Test {i}: {test_name}")
                print(f"   Response: {response}")
                
                f.write(f"### Test {i}: {test_name}\n")
                f.write(f"- Status: {status} {'PASSED' if passed else 'FAILED'}\n")
                f.write(f"- Response: `{response}`\n\n")
                
                if passed:
                    self.passed += 1
                else:
                    self.failed += 1
        
        # Summary
        total = len(self.results)
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: {self.passed}/{total} tests passed ({pass_rate:.1f}%)")
        print("=" * 60)
        
        if self.failed > 0:
            print("\n⚠️  DEPLOYMENT BLOCKED - Not all tests passed!")
            print("Fix issues and run tests again.")
        else:
            print("\n✅ ALL TESTS PASSED - Ready for deployment!")
        
        # Update report
        with open("test_results.md", "a") as f:
            f.write(f"\n## Summary\n\n")
            f.write(f"- Total Tests: {total}\n")
            f.write(f"- Passed: {self.passed}\n")
            f.write(f"- Failed: {self.failed}\n")
            f.write(f"- Pass Rate: {pass_rate:.1f}%\n\n")
            
            if self.failed == 0:
                f.write("**✅ ALL TESTS PASSED - READY FOR DEPLOYMENT**\n")
            else:
                f.write("**❌ DEPLOYMENT BLOCKED - FIX FAILED TESTS**\n")

async def main():
    """Run the test suite"""
    tester = RegistrationLLMTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())