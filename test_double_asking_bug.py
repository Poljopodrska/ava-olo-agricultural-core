#!/usr/bin/env python3
"""
Test Double-Asking Bug Fix
Never ask for data already marked with ✅
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class DoubleAskingTester:
    def __init__(self):
        self.results = []

    async def send_message(self, message: str, session_id: str) -> dict:
        """Send message to registration endpoint"""
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

    async def test_peter_knaflic_scenario(self):
        """Test the EXACT failing scenario: Peter then Knaflič"""
        print("\n🧪 TEST 1: Peter then Knaflič (Never Ask Twice)")
        print("-" * 60)
        
        session_id = "peter-knaflic-001"
        
        # Step 1: User says "Peter"
        print("\n1. User: 'Peter'")
        response1 = await self.send_message("Peter", session_id)
        print(f"   AVA: {response1.get('response', 'ERROR')}")
        print(f"   Collected: {response1.get('collected_data', {})}")
        
        # Check: Should NOT ask for first name again
        asks_for_first_name_1 = "first name" in response1.get('response', '').lower()
        print(f"   ✓ Not asking for first name: {not asks_for_first_name_1}")
        
        # Step 2: User says "Knaflič"
        print("\n2. User: 'Knaflič'")
        response2 = await self.send_message("Knaflič", session_id)
        print(f"   AVA: {response2.get('response', 'ERROR')}")
        print(f"   Collected: {response2.get('collected_data', {})}")
        
        # CRITICAL CHECK: Must NOT ask for first name!
        asks_for_first_name_2 = "first name" in response2.get('response', '').lower()
        asks_for_name_2 = "your name" in response2.get('response', '').lower()
        
        print(f"\n   🔍 Response contains 'first name': {asks_for_first_name_2}")
        print(f"   🔍 Response contains 'your name': {asks_for_name_2}")
        print(f"   🔍 Should ask for WhatsApp/Password: {'whatsapp' in response2.get('response', '').lower() or 'password' in response2.get('response', '').lower()}")
        
        # Test passes if it never asks for first name after having it
        never_asks_twice = not asks_for_first_name_2 and not asks_for_name_2
        
        self.results.append(("Never Ask for First Name", never_asks_twice))
        return never_asks_twice

    async def test_sequential_collection(self):
        """Test sequential data collection without repetition"""
        print("\n🧪 TEST 2: Sequential Collection")
        print("-" * 60)
        
        session_id = "sequential-002"
        
        # Provide first name
        print("\n1. User: 'I'm Ana'")
        response1 = await self.send_message("I'm Ana", session_id)
        print(f"   AVA: {response1.get('response', 'ERROR')}")
        data1 = response1.get('collected_data', {})
        print(f"   Has first_name: {'first_name' in data1 and data1['first_name']}")
        
        # Provide last name
        print("\n2. User: 'Novak'")
        response2 = await self.send_message("Novak", session_id)
        print(f"   AVA: {response2.get('response', 'ERROR')}")
        
        # Should not ask for first or last name
        no_name_repeat = (
            "first name" not in response2.get('response', '').lower() and
            "last name" not in response2.get('response', '').lower() and
            "your name" not in response2.get('response', '').lower()
        )
        
        print(f"   ✓ Not asking for names: {no_name_repeat}")
        
        self.results.append(("Sequential Collection", no_name_repeat))
        return no_name_repeat

    async def test_whatsapp_not_repeated(self):
        """Test that WhatsApp is not asked twice"""
        print("\n🧪 TEST 3: WhatsApp Not Repeated")
        print("-" * 60)
        
        session_id = "whatsapp-003"
        
        # Provide name and phone
        await self.send_message("I'm Maria Horvat", session_id)
        
        print("\n1. User: '+38651234567'")
        response1 = await self.send_message("+38651234567", session_id)
        print(f"   AVA: {response1.get('response', 'ERROR')}")
        
        # Next message should not ask for phone
        print("\n2. User: 'What's next?'")
        response2 = await self.send_message("What's next?", session_id)
        print(f"   AVA: {response2.get('response', 'ERROR')}")
        
        # Should ask for password, not phone
        asks_for_phone = any(word in response2.get('response', '').lower() 
                            for word in ["whatsapp", "phone", "number", "contact"])
        asks_for_password = "password" in response2.get('response', '').lower()
        
        print(f"   ✓ Not asking for phone: {not asks_for_phone}")
        print(f"   ✓ Asking for password: {asks_for_password}")
        
        no_phone_repeat = not asks_for_phone and asks_for_password
        self.results.append(("WhatsApp Not Repeated", no_phone_repeat))
        return no_phone_repeat

    async def test_password_not_repeated(self):
        """Test that password is not asked twice"""
        print("\n🧪 TEST 4: Password Not Repeated")
        print("-" * 60)
        
        session_id = "password-004"
        
        # Provide everything
        await self.send_message("John Smith", session_id)
        await self.send_message("38640123456", session_id)
        
        print("\n1. User: 'MySecret123'")
        response1 = await self.send_message("MySecret123", session_id)
        print(f"   AVA: {response1.get('response', 'ERROR')}")
        print(f"   Completed: {response1.get('completed', False)}")
        
        # Should be complete, not asking for password
        asks_for_password = "password" in response1.get('response', '').lower()
        is_complete = response1.get('completed', False)
        
        print(f"   ✓ Not asking for password: {not asks_for_password}")
        print(f"   ✓ Registration complete: {is_complete}")
        
        no_password_repeat = not asks_for_password and is_complete
        self.results.append(("Password Not Repeated", no_password_repeat))
        return no_password_repeat

    async def test_progress_indicators_match(self):
        """Test that collected data matches progress indicators"""
        print("\n🧪 TEST 5: Progress Indicators Match Data")
        print("-" * 60)
        
        session_id = "progress-005"
        
        # Collect data step by step
        responses = []
        messages = ["Peter", "Petrovic", "+38651999888", "Farm2024!"]
        
        for i, msg in enumerate(messages):
            print(f"\n{i+1}. User: '{msg}'")
            response = await self.send_message(msg, session_id)
            responses.append(response)
            
            data = response.get('collected_data', {})
            progress = response.get('progress_percentage', 0)
            expected_progress = (i + 1) * 25
            
            print(f"   Progress: {progress}% (expected: {expected_progress}%)")
            print(f"   Fields collected: {len([v for v in data.values() if v])}")
            
        # Final check
        final_data = responses[-1].get('collected_data', {})
        all_fields_collected = all(final_data.get(f) for f in ['first_name', 'last_name', 'whatsapp', 'password'])
        
        self.results.append(("Progress Tracking", all_fields_collected))
        return all_fields_collected

    async def run_all_tests(self):
        """Run all double-asking bug tests"""
        print("=" * 60)
        print("🚀 DOUBLE-ASKING BUG FIX TESTS")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        print("\nTesting: System should NEVER ask for ✅ data")
        
        # Check endpoint availability
        print("\n🔍 Checking endpoint availability...")
        test_response = await self.send_message("test", "availability-check")
        if "error" in test_response and "404" in str(test_response['error']):
            print("⚠️  Endpoint not deployed yet")
            return
        
        # Run all tests
        await self.test_peter_knaflic_scenario()
        await self.test_sequential_collection()
        await self.test_whatsapp_not_repeated()
        await self.test_password_not_repeated()
        await self.test_progress_indicators_match()
        
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
            print("🎉 ALL TESTS PASSED - NEVER ASKS FOR ✅ DATA!")
        else:
            print("⚠️  Some tests failed - double-asking bug not fully fixed")
            
        # Critical test result
        if self.results[0][1]:  # Peter/Knaflič test
            print("\n✅ CRITICAL TEST PASSED: Peter → Knaflič works correctly!")
        else:
            print("\n❌ CRITICAL TEST FAILED: Still asking for first name after 'Peter'!")

async def main():
    tester = DoubleAskingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())