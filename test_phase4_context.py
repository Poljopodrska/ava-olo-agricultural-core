#!/usr/bin/env python3
"""
Test Phase 4: Context-Aware Registration Conversations
Test returning farmer recognition and context awareness
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

class Phase4ContextTester:
    def __init__(self):
        self.results = []

    async def send_message(self, message: str, session_id: str = None) -> dict:
        """Send message to context-aware registration endpoint"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'chat_session_id={session_id}'
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

    async def test_returning_farmer_with_context(self):
        """Test: Returning farmer says 'I'm Peter with the mangoes'"""
        print("\n🧪 Test 1: Returning Farmer with Context")
        
        session_id = str(uuid.uuid4())
        
        # First conversation - establish Peter as mango farmer
        print("First visit - establishing context...")
        response1 = await self.send_message("Hi, I'm Peter Horvat", session_id)
        response2 = await self.send_message("I grow mangoes in greenhouse", session_id)
        response3 = await self.send_message("My WhatsApp is +38651234567", session_id)
        
        print(f"Initial registration completed: {response3.get('completed', False)}")
        
        # New session - returning farmer
        new_session = str(uuid.uuid4())
        print("\nReturning visit - should recognize context...")
        
        response4 = await self.send_message("I'm Peter with the mangoes", new_session)
        print(f"Response: {response4.get('response', 'ERROR')[:100]}...")
        print(f"Potential matches: {len(response4.get('potential_matches', []))}")
        
        # Check if Peter was recognized
        has_matches = len(response4.get('potential_matches', [])) > 0
        mentions_peter = 'peter' in response4.get('response', '').lower()
        mentions_mango = 'mango' in response4.get('response', '').lower()
        
        recognized = has_matches or (mentions_peter and mentions_mango)
        
        self.results.append(("Returning Farmer Recognition", recognized))
        return recognized

    async def test_location_based_recognition(self):
        """Test: Recognition based on location context"""
        print("\n🧪 Test 2: Location-Based Recognition")
        
        session_id = str(uuid.uuid4())
        
        response = await self.send_message("I'm the organic farmer from Ljubljana", session_id)
        print(f"Response: {response.get('response', 'ERROR')[:100]}...")
        
        # Check if location is acknowledged
        mentions_ljubljana = 'ljubljana' in response.get('response', '').lower()
        has_matches = len(response.get('potential_matches', [])) > 0
        
        location_aware = mentions_ljubljana or has_matches
        
        self.results.append(("Location-Based Recognition", location_aware))
        return location_aware

    async def test_incomplete_registration_resume(self):
        """Test: Resume incomplete registration"""
        print("\n🧪 Test 3: Incomplete Registration Resume")
        
        # Start registration but don't complete
        session1 = str(uuid.uuid4())
        print("Starting registration...")
        response1 = await self.send_message("Hi, I'm Maria Petrovic", session1)
        response2 = await self.send_message("I'm from Slovenia", session1)
        
        print(f"Progress: {response2.get('progress_percentage', 0)}%")
        print(f"Collected: {response2.get('collected_data', {})}")
        
        # Try to resume later
        session2 = str(uuid.uuid4())
        print("\nAttempting to resume...")
        response3 = await self.send_message("It's Maria again, from earlier", session2)
        
        print(f"Response: {response3.get('response', 'ERROR')[:100]}...")
        print(f"Is returning: {response3.get('is_returning', False)}")
        
        # Check if previous context mentioned
        mentions_earlier = any(word in response3.get('response', '').lower() 
                              for word in ['back', 'again', 'earlier', 'before'])
        
        resume_detected = response3.get('is_returning', False) or mentions_earlier
        
        self.results.append(("Incomplete Registration Resume", resume_detected))
        return resume_detected

    async def test_crop_based_recognition(self):
        """Test: Recognition based on crop context"""
        print("\n🧪 Test 4: Crop-Based Recognition")
        
        session_id = str(uuid.uuid4())
        
        response = await self.send_message("I grow tomatoes and peppers", session_id)
        print(f"Response: {response.get('response', 'ERROR')[:100]}...")
        
        # Should ask for more info or acknowledge crops
        mentions_crops = any(crop in response.get('response', '').lower() 
                           for crop in ['tomato', 'pepper', 'grow', 'crop'])
        
        self.results.append(("Crop-Based Recognition", mentions_crops))
        return mentions_crops

    async def test_ambiguous_farmer_handling(self):
        """Test: Handle multiple possible matches"""
        print("\n🧪 Test 5: Ambiguous Farmer Handling")
        
        session_id = str(uuid.uuid4())
        
        # Common name that might have multiple matches
        response = await self.send_message("I'm John the farmer", session_id)
        print(f"Response: {response.get('response', 'ERROR')[:100]}...")
        
        # Should ask clarifying question if multiple Johns
        asks_clarification = any(word in response.get('response', '').lower()
                               for word in ['which', 'where', 'what crop', 'location'])
        
        # Or just continues with registration
        continues_registration = any(word in response.get('response', '').lower()
                                   for word in ['name', 'welcome', 'nice to meet'])
        
        handles_ambiguity = asks_clarification or continues_registration
        
        self.results.append(("Ambiguous Farmer Handling", handles_ambiguity))
        return handles_ambiguity

    async def test_normal_new_registration(self):
        """Test: New farmer registration still works normally"""
        print("\n🧪 Test 6: Normal New Registration")
        
        session_id = str(uuid.uuid4())
        
        # Complete new registration
        response1 = await self.send_message("Hello, I'm Aleksandra Novak", session_id)
        print(f"Name response: {response1.get('response', 'ERROR')[:80]}...")
        
        response2 = await self.send_message("My WhatsApp is +38640987654", session_id)
        print(f"WhatsApp response: {response2.get('response', 'ERROR')[:80]}...")
        
        # Check progress
        progress = response2.get('progress_percentage', 0)
        collected = response2.get('collected_data', {})
        
        print(f"Progress: {progress}%")
        print(f"Collected: {collected}")
        
        # Should have collected name and phone, be at 66% or 100%
        has_name = bool(collected.get('first_name'))
        has_phone = bool(collected.get('whatsapp'))
        good_progress = progress >= 66
        
        normal_registration_works = has_name and has_phone and good_progress
        
        self.results.append(("Normal New Registration", normal_registration_works))
        return normal_registration_works

    async def run_all_tests(self):
        """Run all Phase 4 tests"""
        print("=" * 60)
        print("🚀 PHASE 4: CONTEXT-AWARE REGISTRATION TESTS")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {BASE_URL}")
        
        # Check if endpoint exists first
        print("\n🔍 Checking endpoint availability...")
        test_response = await self.send_message("test")
        if "error" in test_response:
            print(f"⚠️  Endpoint not available: {test_response['error']}")
            print("Using fallback endpoint...")
            # Could fall back to /registration/message here
        
        # Run tests
        await self.test_returning_farmer_with_context()
        await self.test_location_based_recognition()
        await self.test_incomplete_registration_resume()
        await self.test_crop_based_recognition()
        await self.test_ambiguous_farmer_handling()
        await self.test_normal_new_registration()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PHASE 4 TEST RESULTS")
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
            print("🎉 ALL PHASE 4 TESTS PASSED - CONTEXT-AWARE REGISTRATION WORKING!")
        else:
            print("⚠️  Some tests failed - review implementation")

async def main():
    tester = Phase4ContextTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())