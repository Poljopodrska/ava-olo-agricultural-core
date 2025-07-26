#!/usr/bin/env python3
"""
Verify Comprehensive Prompt Deployment
Checks if v3.5.4+ with comprehensive prompt is actually deployed
"""
import requests
import json
import time
from datetime import datetime

def check_debug_endpoint():
    """Check the debug endpoint to see what prompt is being used"""
    try:
        print("🔍 Checking debug endpoint...")
        response = requests.get(
            "https://ava-olo-65365776.us-east-1.elb.amazonaws.com/api/v1/registration/debug-prompt",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug endpoint accessible")
            print(f"📊 Version: {data.get('code_version', 'Unknown')}")
            print(f"📏 Prompt length: {data.get('prompt_length', 0)} chars")
            print(f"🎯 Prompt type: {data.get('prompt_type', 'Unknown')}")
            print(f"🧠 Has comprehensive prompt: {data.get('contains_comprehensive', False)}")
            
            # Check indicators
            indicators = data.get('prompt_indicators', {})
            print("\n📋 Prompt Indicators:")
            for key, value in indicators.items():
                status = "✅" if value else "❌"
                print(f"  {status} {key}: {value}")
            
            # Check test scenario
            scenario = data.get('test_scenario', {})
            print("\n🧪 Test Scenario (Peter → Knaflič):")
            print(f"  Last bot message: {scenario.get('last_bot_message')}")
            print(f"  User response: {scenario.get('user_response')}")
            print(f"  Detected as: {scenario.get('detected_question_type')}")
            print(f"  Expected type: {scenario.get('expected_data_type')}")
            print(f"  Interpretation: {scenario.get('interpretation')}")
            
            return data
        else:
            print(f"❌ Debug endpoint returned {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking debug endpoint: {e}")
        return None

def test_registration_flow():
    """Test actual registration flow with Knaflič"""
    try:
        print("\n\n🧪 Testing Registration Flow...")
        
        # Create session
        session_id = f"test_{int(time.time())}"
        
        # Step 1: Start registration
        print("\n1️⃣ Starting registration...")
        response = requests.post(
            "https://ava-olo-65365776.us-east-1.elb.amazonaws.com/api/v1/registration/cava",
            json={
                "message": "I want to register",
                "farmer_id": session_id,
                "language": "en"
            },
            timeout=15
        )
        
        data = response.json()
        print(f"Response: {data.get('response', '')[:100]}...")
        debug = data.get('debug', {})
        print(f"Version: {debug.get('version', 'Unknown')}")
        print(f"Prompt type: {debug.get('prompt_type', 'Unknown')}")
        
        # Step 2: Provide first name
        print("\n2️⃣ Providing first name 'Peter'...")
        response = requests.post(
            "https://ava-olo-65365776.us-east-1.elb.amazonaws.com/api/v1/registration/cava",
            json={
                "message": "Peter",
                "farmer_id": session_id,
                "language": "en"
            },
            timeout=15
        )
        
        data = response.json()
        print(f"Response: {data.get('response', '')[:100]}...")
        print(f"Collected data: {data.get('collected_data', {})}")
        debug = data.get('debug', {})
        print(f"Last question was: {debug.get('last_question_was')}")
        print(f"Detected as: {debug.get('detected_as')}")
        
        # Step 3: Provide last name - THE CRITICAL TEST
        print("\n3️⃣ 🚨 CRITICAL TEST: Providing last name 'Knaflič'...")
        response = requests.post(
            "https://ava-olo-65365776.us-east-1.elb.amazonaws.com/api/v1/registration/cava",
            json={
                "message": "Knaflič",
                "farmer_id": session_id,
                "language": "en"
            },
            timeout=15
        )
        
        data = response.json()
        llm_response = data.get('response', '')
        print(f"LLM Response: {llm_response}")
        
        collected = data.get('collected_data', {})
        print(f"\n📊 Collected Data:")
        print(f"  First name: {collected.get('first_name', 'NOT COLLECTED')}")
        print(f"  Last name: {collected.get('last_name', 'NOT COLLECTED')}")
        
        # Check if Knaflič was correctly identified as last name
        if collected.get('last_name') == 'Knaflič':
            print("\n✅ SUCCESS: 'Knaflič' correctly identified as LAST NAME!")
            print("🥭 MANGO TEST PASSED!")
        else:
            print("\n❌ FAILURE: 'Knaflič' was NOT identified as last name")
            print(f"❌ It was interpreted as: {collected}")
            
        # Check debug info
        debug = data.get('debug', {})
        print(f"\n🔍 Debug Info:")
        print(f"  Has comprehensive prompt: {debug.get('has_comprehensive_prompt')}")
        print(f"  Prompt length: {debug.get('prompt_length')}")
        print(f"  Last question type: {debug.get('last_question_was')}")
        
        return collected.get('last_name') == 'Knaflič'
        
    except Exception as e:
        print(f"❌ Error testing registration: {e}")
        return False

def check_version_endpoint():
    """Check the version endpoint"""
    try:
        print("\n\n📊 Checking Version Endpoint...")
        response = requests.get(
            "https://ava-olo-65365776.us-east-1.elb.amazonaws.com/version",
            timeout=10
        )
        
        data = response.json()
        version = data.get('version', 'Unknown')
        print(f"Current version: {version}")
        
        # Check if it's v3.5.4 or higher
        if "v3.5.4" in version or "v3.5.5" in version:
            print("✅ Version v3.5.4+ is deployed")
        else:
            print(f"⚠️ Unexpected version: {version}")
            
        return version
        
    except Exception as e:
        print(f"❌ Error checking version: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Comprehensive Prompt Deployment Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check debug endpoint
    debug_data = check_debug_endpoint()
    
    # Check version
    version = check_version_endpoint()
    
    # Test registration flow
    registration_success = test_registration_flow()
    
    # Summary
    print("\n\n📋 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 60)
    
    if debug_data and debug_data.get('contains_comprehensive'):
        print("✅ Debug endpoint shows COMPREHENSIVE prompt")
    else:
        print("❌ Debug endpoint shows OLD prompt")
        
    if version and ("v3.5.4" in version or "v3.5.5" in version):
        print("✅ Version v3.5.4+ deployed")
    else:
        print("❌ Old version still running")
        
    if registration_success:
        print("✅ Registration correctly handles 'Knaflič' as last name")
    else:
        print("❌ Registration FAILS the Knaflič test")
        
    print("\n🎯 FINAL VERDICT:")
    if debug_data and debug_data.get('contains_comprehensive') and registration_success:
        print("✅ COMPREHENSIVE PROMPT IS DEPLOYED AND WORKING!")
    else:
        print("❌ DEPLOYMENT ISSUE - Comprehensive prompt not active")
        print("\n💡 Possible causes:")
        print("  1. ECS task still running old container")
        print("  2. CloudFront/CDN caching old responses")
        print("  3. Multiple tasks running different versions")
        print("  4. Code not properly built into Docker image")