#!/usr/bin/env python3
"""
Test Simple Registration - Minimal code, maximum LLM
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class SimpleRegistrationTester:
    def __init__(self):
        self.results = []

    async def send_message(self, message: str, session_id: str) -> dict:
        """Send message to simple registration endpoint"""
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
                        return await response.json()
                    else:
                        text = await response.text()
                        return {"error": f"HTTP {response.status}: {text}"}
            except Exception as e:
                return {"error": str(e)}

    async def test_single_message_complete(self):
        """Test: Complete registration in one message"""
        print("\n🧪 Test 1: Single Message Complete Registration")
        
        session_id = "test-single-001"
        
        # Send everything at once
        response = await self.send_message(
            "Hi, I'm Peter Knaflic, my phone number is +38641348050", 
            session_id
        )
        
        print(f"Response: {response.get('response', 'ERROR')}")
        print(f"Collected: {response.get('collected_data', {})}")
        print(f"Complete: {response.get('completed', False)}")
        
        # Check if all data was extracted
        data = response.get('collected_data', {})
        has_first = bool(data.get('first_name'))
        has_last = bool(data.get('last_name'))
        has_phone = bool(data.get('whatsapp'))
        
        all_extracted = has_first and has_last and has_phone
        
        self.results.append(("Single Message Complete", all_extracted))
        return all_extracted

    async def test_multi_message_flow(self):
        """Test: Normal multi-message registration"""
        print("\n🧪 Test 2: Multi-Message Registration Flow")
        
        session_id = "test-multi-002"
        
        # Message 1: Greeting
        print("\n1. User: 'Hello'")
        response1 = await self.send_message("Hello", session_id)
        print(f"   Bot: {response1.get('response', 'ERROR')[:80]}...")
        
        # Message 2: Provide name
        print("\n2. User: 'I'm Ana Novak'")
        response2 = await self.send_message("I'm Ana Novak", session_id)
        print(f"   Bot: {response2.get('response', 'ERROR')[:80]}...")
        print(f"   Collected: {response2.get('collected_data', {})}")
        
        # Message 3: Provide phone
        print("\n3. User: 'My WhatsApp is 041234567'")
        response3 = await self.send_message("My WhatsApp is 041234567", session_id)
        print(f"   Bot: {response3.get('response', 'ERROR')[:80]}...")
        print(f"   Collected: {response3.get('collected_data', {})}")
        print(f"   Complete: {response3.get('completed', False)}")
        
        # Check final state
        data = response3.get('collected_data', {})
        is_complete = response3.get('completed', False)
        
        self.results.append(("Multi-Message Flow", is_complete))
        return is_complete

    async def test_no_repetition(self):
        """Test: System doesn't ask for data already provided"""
        print("\n🧪 Test 3: No Repetition Bug")
        
        session_id = "test-norep-003"
        
        # Provide phone first
        print("\n1. User: '+38651234567'")
        response1 = await self.send_message("+38651234567", session_id)
        print(f"   Bot: {response1.get('response', 'ERROR')}")
        
        # Check if bot asks for phone again
        asks_for_phone = any(word in response1.get('response', '').lower() 
                            for word in ['phone', 'whatsapp', 'number'])
        
        no_repetition = not asks_for_phone or 'already' in response1.get('response', '').lower()
        
        self.results.append(("No Repetition", no_repetition))
        return no_repetition

    async def test_partial_extraction(self):
        """Test: Extract what's available from partial info"""
        print("\n🧪 Test 4: Partial Information Extraction")
        
        session_id = "test-partial-004"
        
        # Send partial info
        print("\n1. User: 'I'm Maria, from Slovenia'")
        response = await self.send_message("I'm Maria, from Slovenia", session_id)
        print(f"   Bot: {response.get('response', 'ERROR')[:80]}...")
        print(f"   Collected: {response.get('collected_data', {})}")
        
        # Check if first name was extracted
        data = response.get('collected_data', {})
        extracted_first_name = bool(data.get('first_name'))
        
        self.results.append(("Partial Extraction", extracted_first_name))
        return extracted_first_name

    async def run_all_tests(self):
        """Run all simple registration tests"""
        print("=" * 60)
        print("🚀 SIMPLE REGISTRATION TESTS")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        
        # Check endpoint availability
        print("\n🔍 Checking endpoint availability...")
        test_response = await self.send_message("test", "test-check")
        if "error" in test_response and "404" in str(test_response['error']):
            print("⚠️  Endpoint not deployed yet")
            return
        
        # Run tests
        await self.test_single_message_complete()
        await self.test_multi_message_flow()
        await self.test_no_repetition()
        await self.test_partial_extraction()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
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
            print("🎉 ALL TESTS PASSED - SIMPLE REGISTRATION WORKING!")
        else:
            print("⚠️  Some tests failed - review implementation")

async def main():
    tester = SimpleRegistrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())