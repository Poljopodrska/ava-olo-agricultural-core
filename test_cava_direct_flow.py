#!/usr/bin/env python3
"""
Test CAVA Direct GPT-4 Flow
Test the 7 critical scenarios for natural understanding
"""

import asyncio
import json
from cava_registration_llm import get_llm_registration_engine

# Critical test cases from specification
TEST_CASES = [
    ("Ljubljana", "Should understand it's a location"),
    ("How do you mean that?", "Should clarify previous question"),
    ("123", "Should ask for complete phone number"),
    ("My crocodile ate my tractor", "Should acknowledge and redirect"),
    ("Sisak, you know where that is?", "Should extract Sisak as location"),
    ("Peter Knaflič", "Should extract both names"),
    ("My name is not Ljubljana", "Should NOT extract Ljubljana as name")
]

async def test_direct_flow():
    """Test direct GPT-4 message flow"""
    print("🧪 TESTING CAVA DIRECT GPT-4 FLOW")
    print("=" * 60)
    
    engine = await get_llm_registration_engine()
    
    for i, (message, expected) in enumerate(TEST_CASES, 1):
        print(f"\n📝 Test {i}: {message}")
        print(f"Expected: {expected}")
        print("-" * 40)
        
        try:
            # Test with fresh session
            session_id = f"test_session_{i}"
            
            result = await engine.process_registration_message(
                message=message,
                session_id=session_id,
                conversation_history=[]
            )
            
            print(f"✅ Response: {result.get('response', '')}")
            print(f"📊 Extracted: {result.get('extracted_data', {})}")
            print(f"🎯 Complete: {result.get('registration_complete', False)}")
            
            # Specific validations
            if message == "Ljubljana":
                farm_location = result.get('extracted_data', {}).get('farm_location')
                if "ljubljana" in str(farm_location).lower():
                    print("✅ PASS: Ljubljana recognized as location")
                else:
                    print("❌ FAIL: Ljubljana not extracted as location")
                    
            elif message == "123":
                phone = result.get('extracted_data', {}).get('whatsapp_number')
                response = result.get('response', '')
                if not phone and ('complete' in response.lower() or 'country code' in response.lower()):
                    print("✅ PASS: Rejected incomplete phone number")
                else:
                    print("❌ FAIL: Should reject '123' as invalid phone")
                    
            elif message == "Peter Knaflič":
                data = result.get('extracted_data', {})
                first = data.get('first_name', '')
                last = data.get('last_name', '')
                if first and last:
                    print("✅ PASS: Both names extracted")
                else:
                    print("❌ FAIL: Should extract both first and last name")
                    
            elif message == "Sisak, you know where that is?":
                farm_location = result.get('extracted_data', {}).get('farm_location')
                if "sisak" in str(farm_location).lower():
                    print("✅ PASS: Sisak recognized as location")
                else:
                    print("❌ FAIL: Should extract Sisak as location")
                    
            elif message == "My name is not Ljubljana":
                first_name = result.get('extracted_data', {}).get('first_name')
                if not first_name or "ljubljana" not in str(first_name).lower():
                    print("✅ PASS: Ljubljana NOT extracted as name")
                else:
                    print("❌ FAIL: Should NOT extract Ljubljana as name")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 DIRECT FLOW TESTING COMPLETE")
    print("Review results above for natural understanding quality")

if __name__ == "__main__":
    asyncio.run(test_direct_flow())