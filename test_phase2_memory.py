#!/usr/bin/env python3
"""
Test Phase 2: Memory & State Tracking for Registration
Bulgarian mango farmer conversation test
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class Phase2Tester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.results = []

    async def send_message(self, message: str) -> dict:
        """Send message to registration memory endpoint"""
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
                        return {"error": f"HTTP {response.status}"}
            except Exception as e:
                return {"error": str(e)}

    async def test_memory_persistence(self):
        """Test if conversation memory persists across messages"""
        print("\n🧪 Test 1: Memory Persistence")
        
        # First message - introduce as Peter
        response1 = await self.send_message("Hello, I'm Peter from Bulgaria")
        print(f"Response 1: {response1.get('response', 'ERROR')[:100]}...")
        
        # Second message - should remember the name
        response2 = await self.send_message("What did I tell you my name was?")
        print(f"Response 2: {response2.get('response', 'ERROR')[:100]}...")
        
        # Check if Peter is mentioned in response
        mentions_peter = "Peter" in response2.get('response', '') or "peter" in response2.get('response', '').lower()
        
        self.results.append(("Memory Persistence", mentions_peter))
        return mentions_peter

    async def test_state_tracking(self):
        """Test if registration state is tracked correctly"""
        print("\n🧪 Test 2: State Tracking")
        
        # Provide first name
        response1 = await self.send_message("My first name is Georgi")
        print(f"First name collection: {response1.get('collected_data', {})}")
        
        # Provide last name
        response2 = await self.send_message("My surname is Dimitrov")
        print(f"After surname: {response2.get('collected_data', {})}")
        
        # Provide WhatsApp
        response3 = await self.send_message("My WhatsApp is +359888123456")
        print(f"After WhatsApp: {response3.get('collected_data', {})}")
        
        # Check if all fields are collected
        final_data = response3.get('collected_data', {})
        has_all_fields = (
            final_data.get('first_name') and
            final_data.get('last_name') and  
            final_data.get('whatsapp')
        )
        
        print(f"Completion status: {response3.get('completed', False)}")
        print(f"Progress: {response3.get('progress_percentage', 0)}%")
        
        self.results.append(("State Tracking", has_all_fields))
        return has_all_fields

    async def test_progress_tracking(self):
        """Test if progress percentage increases correctly"""
        print("\n🧪 Test 3: Progress Tracking")
        
        # Start fresh session for this test
        self.session_id = str(uuid.uuid4())
        
        # Initial message should be 0%
        response1 = await self.send_message("Hi there")
        progress1 = response1.get('progress_percentage', 0)
        
        # Add first name - should be ~33%
        response2 = await self.send_message("I'm Maria")
        progress2 = response2.get('progress_percentage', 0)
        
        # Add last name - should be ~66%
        response3 = await self.send_message("Petrov is my family name")
        progress3 = response3.get('progress_percentage', 0)
        
        # Add WhatsApp - should be 100%
        response4 = await self.send_message("My WhatsApp number is +359123456789")
        progress4 = response4.get('progress_percentage', 0)
        
        print(f"Progress tracking: {progress1}% → {progress2}% → {progress3}% → {progress4}%")
        
        # Progress should increase
        progress_increases = progress1 < progress2 < progress3 < progress4
        
        self.results.append(("Progress Tracking", progress_increases))
        return progress_increases

    async def test_bulgarian_mango_farmer(self):
        """Test the Bulgarian mango farmer conversation scenario"""
        print("\n🧪 Test 4: Bulgarian Mango Farmer Conversation")
        
        # Start fresh session for Bulgarian farmer
        self.session_id = str(uuid.uuid4())
        
        conversation = [
            "Здравейте! I'm a mango farmer from Bulgaria",
            "My name is Ivan",
            "Actually, I grow mangoes in greenhouse",
            "Ivanov is my family name",
            "I have problems with my mango trees",
            "My phone number is +359887654321",
            "Can you remember what fruit I grow?"
        ]
        
        responses = []
        for message in conversation:
            response = await self.send_message(message)
            responses.append(response)
            print(f"Message: {message}")
            print(f"Response: {response.get('response', 'ERROR')[:80]}...")
            print(f"Collected: {response.get('collected_data', {})}")
            print(f"Progress: {response.get('progress_percentage', 0)}%")
            print("---")
        
        # Check final state
        final_response = responses[-1]
        
        # Should remember conversation details
        final_text = final_response.get('response', '').lower()
        remembers_fruit = 'mango' in final_text
        
        # Should have collected all data
        final_data = final_response.get('collected_data', {})
        has_ivan = final_data.get('first_name') == 'Ivan'
        has_ivanov = final_data.get('last_name') == 'Ivanov'
        has_phone = final_data.get('whatsapp') == '+359887654321'
        
        all_collected = has_ivan and has_ivanov and has_phone
        
        print(f"Memory test - remembers mango: {remembers_fruit}")
        print(f"Data collection - all fields: {all_collected}")
        
        self.results.append(("Bulgarian Mango Farmer", remembers_fruit and all_collected))
        return remembers_fruit and all_collected

    async def test_completion_detection(self):
        """Test if completion is detected correctly"""
        print("\n🧪 Test 5: Completion Detection")
        
        # Start fresh session
        self.session_id = str(uuid.uuid4())
        
        # Provide all info at once
        response = await self.send_message(
            "Hi, I'm Stefan Petković from Serbia, my WhatsApp is +381123456789"
        )
        
        print(f"One-shot registration:")
        print(f"Collected: {response.get('collected_data', {})}")
        print(f"Completed: {response.get('completed', False)}")
        print(f"Progress: {response.get('progress_percentage', 0)}%")
        
        is_complete = response.get('completed', False)
        is_100_percent = response.get('progress_percentage', 0) == 100
        
        completion_works = is_complete and is_100_percent
        
        self.results.append(("Completion Detection", completion_works))
        return completion_works

    async def run_all_tests(self):
        """Run all Phase 2 tests"""
        print("=" * 60)
        print("🚀 PHASE 2: MEMORY & STATE TRACKING TESTS")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        
        # Run tests
        await self.test_memory_persistence()
        await self.test_state_tracking() 
        await self.test_progress_tracking()
        await self.test_bulgarian_mango_farmer()
        await self.test_completion_detection()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PHASE 2 TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        for test_name, result in self.results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nSUMMARY: {passed}/{total} tests passed ({pass_rate:.1f}%)")
        
        if passed == total:
            print("🎉 ALL PHASE 2 TESTS PASSED - MEMORY & STATE TRACKING WORKING!")
        else:
            print("⚠️  Some tests failed - review implementation")

async def main():
    tester = Phase2Tester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())