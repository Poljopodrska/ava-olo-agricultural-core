#!/usr/bin/env python3
"""
Test Repetition Bug Fix
Test the exact scenario where system asks for already provided info
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class RepetitionBugTester:
    def __init__(self):
        self.results = []
        self.session_id = str(uuid.uuid4())

    async def send_message(self, message: str) -> dict:
        """Send message to context-aware registration endpoint"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'chat_session_id={self.session_id}'
            }
            
            try:
                async with session.post(
                    f"{BASE_URL}/api/v1/chat/registration/context",
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

    async def test_peter_knaflic_scenario(self):
        """Test the exact scenario that Peter Knaflič reported"""
        print("\n🧪 Testing Peter Knaflič Repetition Bug")
        print("=" * 60)
        
        # Step 1: User expresses uncertainty
        print("\n1. User: 'Not sure I want this...'")
        response1 = await self.send_message("Not sure I want this...")
        print(f"   AVA: {response1.get('response', 'ERROR')}")
        print(f"   Collected: {response1.get('collected_data', {})}")
        
        # Step 2: User asks to provide phone
        print("\n2. User: 'Can I provide you with my phone number?'")
        response2 = await self.send_message("Can I provide you with my phone number?")
        print(f"   AVA: {response2.get('response', 'ERROR')}")
        print(f"   Collected: {response2.get('collected_data', {})}")
        
        # Step 3: User provides phone number
        print("\n3. User: '+38641348050'")
        response3 = await self.send_message("+38641348050")
        print(f"   AVA: {response3.get('response', 'ERROR')}")
        print(f"   Collected: {response3.get('collected_data', {})}")
        
        # CHECK: Did it ask for phone again?
        asks_for_phone_again = any(word in response3.get('response', '').lower() 
                                  for word in ['whatsapp', 'phone', 'number', 'contact'])
        
        if asks_for_phone_again:
            print("\n❌ BUG DETECTED: System asked for phone number again!")
            self.results.append(("No Phone Repetition", False))
        else:
            print("\n✅ GOOD: System did not ask for phone again")
            self.results.append(("No Phone Repetition", True))
        
        # Step 4: User provides full name
        print("\n4. User: 'Peter Knaflič'")
        response4 = await self.send_message("Peter Knaflič")
        print(f"   AVA: {response4.get('response', 'ERROR')}")
        print(f"   Collected: {response4.get('collected_data', {})}")
        print(f"   Completed: {response4.get('completed', False)}")
        
        # Final checks
        final_data = response4.get('collected_data', {})
        
        # Check if all data was collected
        has_phone = final_data.get('whatsapp') == '+38641348050'
        has_first_name = final_data.get('first_name') in ['Peter', 'peter']
        has_last_name = final_data.get('last_name') in ['Knaflič', 'Knaflic', 'knaflic']
        is_complete = response4.get('completed', False)
        
        print("\n📊 Final Status:")
        print(f"   Phone collected: {'✅' if has_phone else '❌'} {final_data.get('whatsapp', 'None')}")
        print(f"   First name collected: {'✅' if has_first_name else '❌'} {final_data.get('first_name', 'None')}")
        print(f"   Last name collected: {'✅' if has_last_name else '❌'} {final_data.get('last_name', 'None')}")
        print(f"   Registration complete: {'✅' if is_complete else '❌'}")
        
        # Test passes if no repetition and all data collected
        test_passed = not asks_for_phone_again and has_phone and has_first_name and has_last_name
        
        self.results.append(("Complete Registration", test_passed))
        
        return test_passed

    async def test_immediate_extraction(self):
        """Test that extraction happens immediately"""
        print("\n🧪 Testing Immediate Extraction")
        print("=" * 60)
        
        new_session = str(uuid.uuid4())
        self.session_id = new_session
        
        # Send phone number
        print("\n1. Sending just phone number: '041348050'")
        response = await self.send_message("041348050")
        
        collected = response.get('collected_data', {})
        phone_collected = bool(collected.get('whatsapp'))
        
        print(f"   Collected immediately: {collected}")
        print(f"   Phone extracted: {'✅' if phone_collected else '❌'}")
        
        self.results.append(("Immediate Phone Extraction", phone_collected))
        
        # Send name
        print("\n2. Sending name: 'Ana Novak'")
        response2 = await self.send_message("Ana Novak")
        
        collected2 = response2.get('collected_data', {})
        name_collected = bool(collected2.get('first_name')) and bool(collected2.get('last_name'))
        
        print(f"   Collected: {collected2}")
        print(f"   Name extracted: {'✅' if name_collected else '❌'}")
        
        self.results.append(("Immediate Name Extraction", name_collected))

    async def run_all_tests(self):
        """Run all repetition bug tests"""
        print("=" * 60)
        print("🚀 REPETITION BUG FIX TESTS")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        
        # Run tests
        await self.test_peter_knaflic_scenario()
        await self.test_immediate_extraction()
        
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
            print("🎉 ALL TESTS PASSED - REPETITION BUG FIXED!")
        else:
            print("⚠️  Some tests failed - bug not fully fixed")

async def main():
    tester = RepetitionBugTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())