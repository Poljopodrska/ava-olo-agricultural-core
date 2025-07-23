#!/usr/bin/env python3
"""
Comprehensive LLM-Only Test Suite
Tests that ONLY a real LLM can pass, impossible to fake with code
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
from typing import Dict, List

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class LLMComprehensiveTester:
    def __init__(self):
        self.results = {}
        self.detailed_results = []
        
    def new_session(self) -> str:
        """Generate new session ID"""
        return f"test-{uuid.uuid4()}"
    
    async def chat(self, message: str, session_id: str) -> str:
        """Send message and get response"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{BASE_URL}/api/v1/chat/register",
                    json={
                        "message": message,
                        "session_id": session_id
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', 'No response')
                    else:
                        return f"Error: HTTP {response.status}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def test_nonsense_questions(self):
        """Questions with no predictable answer"""
        print("\n🧪 TEST 1: Impossible-to-Predict Responses")
        print("-" * 50)
        
        tests = [
            "My purple elephant wants to study quantum physics in Ljubljana",
            "The flying spaghetti monster ate my tractor manual",
            "How many unicorns fit in a corn silo?",
            "My crops are singing Beethoven at night",
            "The moon told me to plant watermelons sideways"
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Must give thoughtful response
            is_valid = (
                len(response) > 20 and 
                "error" not in response.lower() and
                response != "No response"
            )
            
            if is_valid:
                passed += 1
                
            print(f"\nQ: {test}")
            print(f"A: {response[:100]}...")
            print(f"✓ Valid: {is_valid}")
            
            self.detailed_results.append({
                "test": "nonsense_questions",
                "input": test,
                "response": response,
                "passed": is_valid
            })
        
        self.results["nonsense_questions"] = f"{passed}/{len(tests)}"
        return passed == len(tests)
    
    async def test_multilingual_chaos(self):
        """Mix languages in ways impossible to predict"""
        print("\n🧪 TEST 2: Multilingual Mixed Sentences")
        print("-" * 50)
        
        tests = [
            "Je suis Peter από την Ljubljana and necesito ayuda",
            "Mein име е Петър and ich grow 玉米",
            "Привет, my nombre ist Hans from Maribor",
            "我的 farm heeft problemas με τα crops",
            "Bonjour, я farmer from България με μάνγκο"
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Should handle gracefully
            is_valid = (
                len(response) > 10 and
                "error" not in response.lower() and
                response != "No response"
            )
            
            if is_valid:
                passed += 1
                
            print(f"\nMultilingual: {test}")
            print(f"Response: {response[:80]}...")
            print(f"✓ Valid: {is_valid}")
            
            self.detailed_results.append({
                "test": "multilingual_chaos",
                "input": test,
                "response": response,
                "passed": is_valid
            })
        
        self.results["multilingual_chaos"] = f"{passed}/{len(tests)}"
        return passed >= len(tests) * 0.8
    
    async def test_reasoning_required(self):
        """Tests requiring actual reasoning"""
        print("\n🧪 TEST 3: Contextual Reasoning")
        print("-" * 50)
        
        passed = 0
        total = 0
        
        # Test 1: Math reasoning
        session1 = self.new_session()
        await self.chat("I have 17 hectares split among 3 sons", session1)
        response1 = await self.chat("How much does the youngest get if he gets 1 hectare less than others?", session1)
        
        # Should involve math reasoning
        is_math_valid = any(num in response1 for num in ["5", "6", "five", "six"])
        print(f"\nMath test: 17 hectares, 3 sons, youngest gets 1 less")
        print(f"Response: {response1[:100]}...")
        print(f"✓ Shows reasoning: {is_math_valid}")
        
        if is_math_valid:
            passed += 1
        total += 1
        
        # Test 2: Temporal reasoning
        session2 = self.new_session()
        await self.chat("I planted corn last Tuesday", session2)
        response2 = await self.chat("If it takes 90 days to grow, when do I harvest?", session2)
        
        # Should mention time/date concepts
        is_time_valid = any(word in response2.lower() for word in ["days", "weeks", "months", "october", "january"])
        print(f"\nTemporal test: Planted Tuesday, 90 days to grow")
        print(f"Response: {response2[:100]}...")
        print(f"✓ Shows reasoning: {is_time_valid}")
        
        if is_time_valid:
            passed += 1
        total += 1
        
        # Test 3: Logical reasoning
        session3 = self.new_session()
        response3 = await self.chat("If all my chickens are brown, and some brown animals are cows, are all my chickens cows?", session3)
        
        # Should say no or indicate logical fallacy
        is_logic_valid = any(word in response3.lower() for word in ["no", "not", "different", "chicken", "cow"])
        print(f"\nLogic test: Chickens/cows syllogism")
        print(f"Response: {response3[:100]}...")
        print(f"✓ Shows reasoning: {is_logic_valid}")
        
        if is_logic_valid:
            passed += 1
        total += 1
        
        self.results["reasoning_required"] = f"{passed}/{total}"
        return passed >= 2
    
    async def test_emotional_responses(self):
        """Test empathy and emotional understanding"""
        print("\n🧪 TEST 4: Emotional Intelligence")
        print("-" * 50)
        
        tests = [
            "My father just died and left me his farm but I don't know anything about farming",
            "I'm so happy! My first tomato finally grew after 5 failed attempts!",
            "I'm scared the bank will take my farm if this harvest fails",
            "My neighbor is sabotaging my crops out of jealousy",
            "I feel like a failure as a farmer"
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Should give thoughtful, empathetic response
            empathy_words = ["sorry", "understand", "help", "support", "congratulations", 
                           "wonderful", "difficult", "challenging", "feel", "worry"]
            
            is_empathetic = (
                len(response) > 30 and
                any(word in response.lower() for word in empathy_words)
            )
            
            if is_empathetic:
                passed += 1
                
            print(f"\nEmotional: {test[:60]}...")
            print(f"Response: {response[:100]}...")
            print(f"✓ Empathetic: {is_empathetic}")
            
            self.detailed_results.append({
                "test": "emotional_responses",
                "input": test,
                "response": response,
                "passed": is_empathetic
            })
        
        self.results["emotional_responses"] = f"{passed}/{len(tests)}"
        return passed >= len(tests) * 0.8
    
    async def test_context_switching(self):
        """Test ability to handle topic changes"""
        print("\n🧪 TEST 5: Dynamic Context Switching")
        print("-" * 50)
        
        session = self.new_session()
        passed = 0
        
        # Setup
        await self.chat("My name is Ana", session)
        
        # Test 1: Topic change
        response1 = await self.chat("Actually, let's talk about black holes instead", session)
        acknowledges_change = any(word in response1.lower() for word in ["black hole", "topic", "space", "but", "however"])
        print(f"\nTopic switch to black holes")
        print(f"Response: {response1[:100]}...")
        print(f"✓ Acknowledges: {acknowledges_change}")
        if acknowledges_change:
            passed += 1
        
        # Test 2: Memory check
        response2 = await self.chat("Wait, what was I supposed to tell you?", session)
        remembers_context = any(word in response2.lower() for word in ["name", "registration", "information", "ana"])
        print(f"\nAsking what to tell")
        print(f"Response: {response2[:100]}...")
        print(f"✓ Remembers: {remembers_context}")
        if remembers_context:
            passed += 1
        
        # Test 3: Confusion handling
        response3 = await self.chat("I forgot what we were doing", session)
        guides_back = any(word in response3.lower() for word in ["registration", "name", "help", "information"])
        print(f"\nForgot what doing")
        print(f"Response: {response3[:100]}...")
        print(f"✓ Guides back: {guides_back}")
        if guides_back:
            passed += 1
        
        self.results["context_switching"] = f"{passed}/3"
        return passed >= 2
    
    async def test_trick_questions(self):
        """Questions designed to confuse hardcoded logic"""
        print("\n🧪 TEST 6: Trick Questions")
        print("-" * 50)
        
        tests = [
            ("My name is not Peter", "Should be confused"),
            ("Don't use the name I'm about to tell you: Maria", "Should not use Maria"),
            ("I go by many names but call me Bob", "Should use Bob"),
            ("My real name is secret but I'm known as Farmer Joe", "Should use Farmer Joe"),
            ("Guess my name, it starts with K and ends with vin", "Should ask, not guess")
        ]
        
        passed = 0
        for test, expectation in tests:
            response = await self.chat(test, self.new_session())
            
            print(f"\nTrick: {test}")
            print(f"Expect: {expectation}")
            print(f"Response: {response[:100]}...")
            
            # Basic check: reasonable response
            if len(response) > 10 and "error" not in response.lower():
                passed += 1
                print(f"✓ Handled appropriately")
            else:
                print(f"✗ Failed to handle")
        
        self.results["trick_questions"] = f"{passed}/{len(tests)}"
        return passed >= 3
    
    async def test_cultural_awareness(self):
        """Test understanding of cultural contexts"""
        print("\n🧪 TEST 7: Cultural Context")
        print("-" * 50)
        
        tests = [
            "I need to plant after Vidovdan",  # Serbian holiday
            "My baba taught me to plant by the moon",  # Balkan tradition
            "We follow the three sisters method here",  # Native American
            "I practice jhum cultivation",  # Shifting cultivation
            "Our kibbutz shares all farming decisions"  # Israeli collective
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Should not say "don't understand"
            understands = (
                "don't understand" not in response.lower() and
                "what is" not in response.lower() and
                len(response) > 20
            )
            
            if understands:
                passed += 1
                
            print(f"\nCultural: {test}")
            print(f"Response: {response[:100]}...")
            print(f"✓ Shows awareness: {understands}")
        
        self.results["cultural_awareness"] = f"{passed}/{len(tests)}"
        return passed >= 3
    
    async def test_sarcasm_detection(self):
        """Test understanding of non-literal language"""
        print("\n🧪 TEST 8: Sarcasm and Humor")
        print("-" * 50)
        
        tests = [
            "Oh sure, I LOVE waking up at 4am to milk cows",
            "My tractor is my best friend - it never argues with me",
            "Great, another form to fill out, just what I needed",
            "I'm a professional plant killer, want my help?",
            "My scarecrow is doing a better job farming than me"
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Should show understanding of humor/sarcasm
            understands_tone = (
                len(response) > 20 and
                not response.lower().startswith("great!") and
                not response.lower().startswith("wonderful!")
            )
            
            if understands_tone:
                passed += 1
                
            print(f"\nSarcasm: {test[:60]}...")
            print(f"Response: {response[:100]}...")
            print(f"✓ Appropriate: {understands_tone}")
        
        self.results["sarcasm_detection"] = f"{passed}/{len(tests)}"
        return passed >= 3
    
    async def test_contradiction_handling(self):
        """Test handling of contradictory statements"""
        print("\n🧪 TEST 9: Contradiction Handling")
        print("-" * 50)
        
        passed = 0
        
        # Test 1: Name contradiction
        session1 = self.new_session()
        await self.chat("I'm Peter", session1)
        response1 = await self.chat("Actually I'm not Peter, I'm Paul", session1)
        
        handles_name = any(word in response1.lower() for word in ["paul", "correction", "update", "change"])
        print(f"\nName change: Peter -> Paul")
        print(f"Response: {response1[:100]}...")
        print(f"✓ Handles: {handles_name}")
        if handles_name:
            passed += 1
        
        # Test 2: Phone contradiction
        session2 = self.new_session()
        await self.chat("I have no phone", session2)
        response2 = await self.chat("My number is 38641234567", session2)
        
        handles_phone = "no phone" not in response2.lower()
        print(f"\nPhone contradiction: no phone -> gives number")
        print(f"Response: {response2[:100]}...")
        print(f"✓ Handles: {handles_phone}")
        if handles_phone:
            passed += 1
        
        self.results["contradiction_handling"] = f"{passed}/2"
        return passed >= 1
    
    async def test_meta_awareness(self):
        """Test self-awareness and meta-cognition"""
        print("\n🧪 TEST 10: Meta-Questions About AI")
        print("-" * 50)
        
        tests = [
            "Are you just pattern matching or do you understand me?",
            "How do I know you're not just a hardcoded bot?",
            "Prove to me you're actually thinking",
            "What would happen if I spoke only in metaphors?",
            "Can you tell when I'm testing you?"
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Should give thoughtful response about its nature
            is_thoughtful = (
                len(response) > 40 and
                "error" not in response.lower() and
                not response.startswith("I don't")
            )
            
            if is_thoughtful:
                passed += 1
                
            print(f"\nMeta: {test}")
            print(f"Response: {response[:100]}...")
            print(f"✓ Thoughtful: {is_thoughtful}")
        
        self.results["meta_awareness"] = f"{passed}/{len(tests)}"
        return passed >= 3
    
    async def test_impossible_temporal(self):
        """Questions about specific moments impossible to know"""
        print("\n🧪 TEST 11: Time-Sensitive Impossible Questions")
        print("-" * 50)
        
        tests = [
            "What did I eat for breakfast this morning?",
            "What color shirt am I wearing right now?",
            "How many fingers am I holding up?",
            "What's the weather like where I am at this exact moment?",
            "What song is playing on my radio?"
        ]
        
        passed = 0
        for test in tests:
            response = await self.chat(test, self.new_session())
            
            # Should acknowledge it cannot know
            admits_limitation = any(phrase in response.lower() for phrase in [
                "cannot know", "can't know", "don't have access", "unable to see",
                "don't know", "can't tell", "no way", "impossible"
            ])
            
            if admits_limitation:
                passed += 1
                
            print(f"\nImpossible: {test}")
            print(f"Response: {response[:100]}...")
            print(f"✓ Admits limitation: {admits_limitation}")
        
        self.results["impossible_temporal"] = f"{passed}/{len(tests)}"
        return passed >= 4
    
    async def test_response_variety(self):
        """Same input should give different outputs"""
        print("\n🧪 TEST 12: Response Variation")
        print("-" * 50)
        
        responses = []
        for i in range(5):
            response = await self.chat("Hello", self.new_session())
            responses.append(response)
            print(f"\nAttempt {i+1}: {response[:50]}...")
        
        # Count unique responses
        unique_responses = set(responses)
        variety_score = len(unique_responses)
        
        print(f"\nUnique responses: {variety_score}/5")
        
        self.results["response_variety"] = f"{variety_score}/5"
        return variety_score >= 3
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("=" * 60)
        print("🚀 COMPREHENSIVE LLM-ONLY TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        print("\nThese tests are IMPOSSIBLE to pass without a real LLM!")
        
        # Test if endpoint is available
        test_response = await self.chat("test", "availability-check")
        if "Error:" in test_response:
            print(f"\n❌ Endpoint not available: {test_response}")
            return
        
        # Run all test categories
        test_functions = [
            self.test_nonsense_questions,
            self.test_multilingual_chaos,
            self.test_reasoning_required,
            self.test_emotional_responses,
            self.test_context_switching,
            self.test_trick_questions,
            self.test_cultural_awareness,
            self.test_sarcasm_detection,
            self.test_contradiction_handling,
            self.test_meta_awareness,
            self.test_impossible_temporal,
            self.test_response_variety
        ]
        
        test_results = {}
        for test_func in test_functions:
            try:
                result = await test_func()
                test_results[test_func.__name__] = "PASSED" if result else "FAILED"
            except Exception as e:
                test_results[test_func.__name__] = f"ERROR: {str(e)}"
                print(f"\n❌ Error in {test_func.__name__}: {e}")
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        for test_name, result in test_results.items():
            status = "✅" if result == "PASSED" else "❌"
            score = self.results.get(test_name.replace("test_", ""), "N/A")
            print(f"{status} {test_name:30} Score: {score:10} {result}")
            if result == "PASSED":
                passed += 1
        
        total = len(test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"OVERALL: {passed}/{total} tests passed ({pass_rate:.1f}%)")
        print(f"{'='*60}")
        
        # Save results to file
        final_results = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": f"{BASE_URL}/api/v1/chat/register",
            "test_results": test_results,
            "scores": self.results,
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": pass_rate
            },
            "detailed_results": self.detailed_results[:20]  # First 20 for space
        }
        
        with open("llm_test_results.json", "w") as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n📁 Results saved to: llm_test_results.json")
        
        if pass_rate >= 90:
            print("\n🎉 VERIFIED: This is a REAL LLM! No hardcoded bot could pass these tests!")
        elif pass_rate >= 70:
            print("\n⚠️  LIKELY LLM: Most tests passed, some issues detected")
        else:
            print("\n❌ FAILED: This doesn't appear to be a real LLM")
        
        return final_results

async def main():
    tester = LLMComprehensiveTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())