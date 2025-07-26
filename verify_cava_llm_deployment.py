#!/usr/bin/env python3
"""
Verify CAVA LLM Deployment
Tests that the LLM engine is actually deployed and working
"""
import asyncio
import httpx
import json
from datetime import datetime

# Production URL
BASE_URL = "https://ava-olo-65365776.us-east-1.elb.amazonaws.com"

async def verify_cava_llm_deployment():
    """Verify CAVA LLM is deployed and working"""
    
    print("🔍 VERIFYING CAVA LLM DEPLOYMENT")
    print("=" * 50)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    checks = []
    
    # Check 1: Version endpoint shows new version
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/version", timeout=10)
            version_data = response.json()
            
            print("✅ Version Check:")
            print(f"   Version: {version_data.get('version', 'Unknown')}")
            print(f"   Build ID: {version_data.get('build_id', 'Unknown')}")
            
            # Check for v3.4.3 version
            version = version_data.get('version', '')
            if 'v3.4.3' in version and 'cava-llm' in version:
                print("   ✅ NEW VERSION DEPLOYED: v3.4.3-cava-llm")
                checks.append(True)
            else:
                print(f"   ❌ OLD VERSION: {version}")
                checks.append(False)
                
    except Exception as e:
        print(f"❌ Version check failed: {e}")
        checks.append(False)
    
    print()
    
    # Check 2: Debug endpoint shows OpenAI configured
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/v1/registration/debug", timeout=10)
            debug_data = response.json()
            
            print("✅ Debug Endpoint Check:")
            print(f"   OpenAI Key Set: {debug_data.get('openai_key_set', False)}")
            print(f"   Key Prefix: {debug_data.get('key_prefix', 'None')}")
            print(f"   CAVA Mode: {debug_data.get('cava_mode', 'Unknown')}")
            
            if debug_data.get('openai_key_set') and debug_data.get('cava_mode') == 'llm':
                print("   ✅ OpenAI API configured for LLM mode")
                checks.append(True)
            else:
                print("   ❌ OpenAI not configured or not in LLM mode")
                checks.append(False)
                
    except Exception as e:
        print(f"❌ Debug endpoint failed: {e}")
        checks.append(False)
    
    print()
    
    # Check 3: Test actual registration - "i want to register"
    try:
        async with httpx.AsyncClient() as client:
            test_payload = {
                "farmer_id": f"test_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "message": "i want to register",
                "language": "en"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/registration/cava",
                json=test_payload,
                timeout=20
            )
            
            print("✅ Registration Test: 'i want to register'")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response_text[:100]}...")
                
                # Check for hardcoded greetings (BAD)
                hardcoded_greetings = [
                    "👋 Hello! I'm CAVA",
                    "Welcome to AVA OLO!",
                    "Let's get you registered!"
                ]
                
                has_hardcoded = any(greeting in response_text for greeting in hardcoded_greetings)
                llm_used = result.get('llm_used', False)
                constitutional = result.get('constitutional_compliance', False)
                
                if has_hardcoded:
                    print("   ❌ HARDCODED RESPONSE DETECTED - LLM not working!")
                    checks.append(False)
                elif llm_used and constitutional:
                    print("   ✅ LLM RESPONSE - No hardcoded greeting detected")
                    print(f"   ✅ Constitutional compliance: {constitutional}")
                    checks.append(True)
                else:
                    print(f"   ⚠️  Unclear response - LLM used: {llm_used}, Constitutional: {constitutional}")
                    checks.append(False)
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Error: {response.text}")
                checks.append(False)
                
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        checks.append(False)
    
    print()
    
    # Check 4: Test Bulgarian registration
    try:
        async with httpx.AsyncClient() as client:
            test_payload = {
                "farmer_id": f"test_bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "message": "Искам да се регистрирам",
                "language": "bg"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/registration/cava",
                json=test_payload,
                timeout=20
            )
            
            print("✅ Bulgarian Test: 'Искам да се регистрирам'")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                print(f"   Response: {response_text[:100]}...")
                
                # Check if it's in Bulgarian or at least intelligent
                if any(c for c in response_text if ord(c) > 127):  # Non-ASCII chars
                    print("   ✅ Non-English response detected (likely Bulgarian)")
                    checks.append(True)
                elif "name" in response_text.lower() or "register" in response_text.lower():
                    print("   ✅ Intelligent English response to Bulgarian")
                    checks.append(True)
                else:
                    print("   ❌ Generic or hardcoded response")
                    checks.append(False)
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                checks.append(False)
                
    except Exception as e:
        print(f"❌ Bulgarian test failed: {e}")
        checks.append(False)
    
    print()
    print("=" * 50)
    print("DEPLOYMENT VERIFICATION SUMMARY:")
    print(f"   Total Checks: {len(checks)}")
    print(f"   Passed: {sum(checks)}")
    print(f"   Failed: {len(checks) - sum(checks)}")
    
    if all(checks):
        print("\n🎉 DEPLOYMENT VERIFIED: CAVA LLM is working!")
        print("✅ Version updated to v3.4.3")
        print("✅ OpenAI API configured")
        print("✅ Registration uses LLM responses")
        print("✅ No hardcoded greetings detected")
    else:
        print("\n❌ DEPLOYMENT ISSUES DETECTED:")
        if not checks[0]:
            print("   - Version not updated to v3.4.3")
        if not checks[1]:
            print("   - OpenAI API not configured")
        if not checks[2]:
            print("   - Registration still using hardcoded responses")
        if len(checks) > 3 and not checks[3]:
            print("   - Bulgarian registration not working")
    
    return all(checks)

if __name__ == "__main__":
    success = asyncio.run(verify_cava_llm_deployment())
    if success:
        print("\n🟢 CAVA LLM DEPLOYMENT SUCCESSFUL")
    else:
        print("\n🔴 CAVA LLM DEPLOYMENT FAILED")
    exit(0 if success else 1)