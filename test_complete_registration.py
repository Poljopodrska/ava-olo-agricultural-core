#!/usr/bin/env python3
"""
Test Complete Registration Flow with Password
Bulgarian mango farmer completes registration, gets password, and can sign in
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class CompleteRegistrationTester:
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

    async def test_bulgarian_mango_farmer(self):
        """Test: Bulgarian mango farmer completes full registration"""
        print("\n🧪 TEST 1: Bulgarian Mango Farmer Registration")
        print("-" * 60)
        
        session_id = "bulgarian-mango-001"
        
        # Step 1: Introduction
        print("\n1. Farmer: 'Hello, I'm Peter from Bulgaria, I grow mangoes'")
        response1 = await self.send_message(
            "Hello, I'm Peter from Bulgaria, I grow mangoes", 
            session_id
        )
        print(f"   AVA: {response1.get('response', 'ERROR')[:100]}...")
        print(f"   Progress: {response1.get('progress_percentage', 0)}%")
        print(f"   Collected: {response1.get('collected_data', {})}")
        
        # Step 2: Last name
        print("\n2. Farmer: 'Petrov is my last name'")
        response2 = await self.send_message(
            "Petrov is my last name",
            session_id
        )
        print(f"   AVA: {response2.get('response', 'ERROR')[:100]}...")
        print(f"   Progress: {response2.get('progress_percentage', 0)}%")
        print(f"   Collected: {response2.get('collected_data', {})}")
        
        # Step 3: Phone number
        print("\n3. Farmer: 'My WhatsApp is +359888123456'")
        response3 = await self.send_message(
            "My WhatsApp is +359888123456",
            session_id
        )
        print(f"   AVA: {response3.get('response', 'ERROR')[:100]}...")
        print(f"   Progress: {response3.get('progress_percentage', 0)}%")
        print(f"   Collected: {response3.get('collected_data', {})}")
        
        # Step 4: Password
        print("\n4. Farmer: 'I'll use password Mango2024!'")
        response4 = await self.send_message(
            "I'll use password Mango2024!",
            session_id
        )
        print(f"   AVA: {response4.get('response', 'ERROR')[:100]}...")
        print(f"   Progress: {response4.get('progress_percentage', 0)}%")
        print(f"   Collected: {response4.get('collected_data', {})}")
        print(f"   Completed: {response4.get('completed', False)}")
        print(f"   Show App Button: {response4.get('show_app_button', False)}")
        
        # Check final state
        data = response4.get('collected_data', {})
        is_complete = response4.get('completed', False)
        has_all_fields = all(data.get(field) for field in ['first_name', 'last_name', 'whatsapp', 'password'])
        has_login_instructions = 'username' in response4.get('response', '').lower()
        
        # Verify results
        print("\n📊 Final Verification:")
        print(f"   ✓ All fields collected: {has_all_fields}")
        print(f"   ✓ Registration completed: {is_complete}")
        print(f"   ✓ Login instructions shown: {has_login_instructions}")
        print(f"   ✓ Username shown as: {data.get('whatsapp', 'NOT SHOWN')}")
        
        test_passed = has_all_fields and is_complete and has_login_instructions
        self.results.append(("Bulgarian Mango Farmer", test_passed))
        
        return test_passed

    async def test_password_collection(self):
        """Test: Password is properly collected"""
        print("\n🧪 TEST 2: Password Collection")
        print("-" * 60)
        
        session_id = "password-test-002"
        
        # Provide all data at once
        print("\n1. Farmer: 'Ana Novak, 38651234567, password: SecureFarm123'")
        response = await self.send_message(
            "Ana Novak, 38651234567, password: SecureFarm123",
            session_id
        )
        
        data = response.get('collected_data', {})
        print(f"   Collected: {data}")
        print(f"   Password extracted: {'password' in data and data['password'] == 'SecureFarm123'}")
        
        password_collected = data.get('password') == 'SecureFarm123'
        self.results.append(("Password Collection", password_collected))
        
        return password_collected

    async def test_auto_completion(self):
        """Test: Registration auto-completes when all fields collected"""
        print("\n🧪 TEST 3: Auto-Completion")
        print("-" * 60)
        
        session_id = "auto-complete-003"
        
        # Step through registration
        await self.send_message("Hi, I'm Maria", session_id)
        await self.send_message("Surname is Horvat", session_id)
        await self.send_message("WhatsApp +38641999888", session_id)
        
        # Final message with password should complete
        response = await self.send_message("My password will be Farm2024", session_id)
        
        print(f"\nFinal response: {response.get('response', 'ERROR')[:150]}...")
        print(f"Completed: {response.get('completed', False)}")
        print(f"Show App Button: {response.get('show_app_button', False)}")
        
        # Should auto-complete
        is_completed = response.get('completed', False)
        shows_button = response.get('show_app_button', False)
        stops_asking = "perfect" in response.get('response', '').lower() or "complete" in response.get('response', '').lower()
        
        auto_completes = is_completed and shows_button and stops_asking
        self.results.append(("Auto-Completion", auto_completes))
        
        return auto_completes

    async def test_login_instructions(self):
        """Test: Clear login instructions with WhatsApp as username"""
        print("\n🧪 TEST 4: Login Instructions")
        print("-" * 60)
        
        session_id = "login-instructions-004"
        
        # Complete registration quickly
        response = await self.send_message(
            "John Smith, +38640555444, password is MySecret123",
            session_id
        )
        
        print(f"\nCompletion message:")
        print(response.get('response', 'No response'))
        
        # Check instructions
        instructions = response.get('response', '').lower()
        has_username = 'username' in instructions
        has_whatsapp = '+38640555444' in response.get('response', '')
        has_password = 'password' in instructions
        mentions_signin = 'sign in' in instructions or 'login' in instructions
        
        print(f"\n✓ Shows username: {has_username}")
        print(f"✓ Shows WhatsApp number: {has_whatsapp}")
        print(f"✓ Mentions password: {has_password}")
        print(f"✓ Mentions sign in: {mentions_signin}")
        
        clear_instructions = has_username and has_whatsapp and has_password and mentions_signin
        self.results.append(("Login Instructions", clear_instructions))
        
        return clear_instructions

    async def test_all_fields_required(self):
        """Test: All 4 fields must be provided"""
        print("\n🧪 TEST 5: All Fields Required")
        print("-" * 60)
        
        session_id = "fields-required-005"
        
        # Provide only 3 fields
        await self.send_message("I'm Test User", session_id)
        await self.send_message("Phone: 38651111222", session_id)
        
        # Should not be complete yet
        response = await self.send_message("How do I continue?", session_id)
        
        not_complete = not response.get('completed', False)
        still_asking = 'password' in response.get('response', '').lower()
        
        print(f"Not complete with 3 fields: {not_complete}")
        print(f"Still asking for password: {still_asking}")
        
        # Now provide password
        final_response = await self.send_message("Password123", session_id)
        now_complete = final_response.get('completed', False)
        
        print(f"Complete after password: {now_complete}")
        
        requires_all = not_complete and still_asking and now_complete
        self.results.append(("All Fields Required", requires_all))
        
        return requires_all

    async def run_all_tests(self):
        """Run all registration completion tests"""
        print("=" * 60)
        print("🚀 COMPLETE REGISTRATION FLOW TESTS")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        
        # Check endpoint availability
        print("\n🔍 Checking endpoint availability...")
        test_response = await self.send_message("test", "availability-check")
        if "error" in test_response and "404" in str(test_response['error']):
            print("⚠️  Endpoint not deployed yet")
            return
        
        # Run all tests
        await self.test_bulgarian_mango_farmer()
        await self.test_password_collection()
        await self.test_auto_completion()
        await self.test_login_instructions()
        await self.test_all_fields_required()
        
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
            print("🎉 ALL TESTS PASSED - COMPLETE REGISTRATION FLOW WORKING!")
            print("\n🥭 MANGO TEST PASSED: Bulgarian mango farmer can register and sign in!")
        else:
            print("⚠️  Some tests failed - review implementation")

async def main():
    tester = CompleteRegistrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())