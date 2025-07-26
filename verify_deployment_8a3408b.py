#!/usr/bin/env python3
"""
Verify deployment of commit 8a3408b - Critical Constitutional Fix
"""
import httpx
import asyncio
import json
from datetime import datetime

async def verify_deployment():
    """Verify the critical fix is actually deployed"""
    
    # Production URL
    base_url = "https://ava-olo-agricultural-core.us-east-1.awsapprunner.com"
    
    print("🔍 DEPLOYMENT VERIFICATION - Commit 8a3408b")
    print("=" * 60)
    print(f"Target: {base_url}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    checks = []
    
    # Check 1: Version endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/version", timeout=10)
            version_data = response.json()
            print("✅ Version Check:")
            print(f"   Version: {version_data.get('version', 'Unknown')}")
            print(f"   Build ID: {version_data.get('build_id', 'Unknown')}")
            
            # Check if build ID contains commit hash
            build_id = version_data.get('build_id', '')
            if '8a3408b' in build_id:
                print("   ✅ Build ID contains commit hash 8a3408b")
                checks.append(True)
            else:
                print("   ❌ Build ID does NOT contain commit hash 8a3408b")
                checks.append(False)
    except Exception as e:
        print(f"❌ Version check failed: {e}")
        checks.append(False)
    
    print()
    
    # Check 2: Debug endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/registration/debug", timeout=10)
            debug_data = response.json()
            print("✅ Debug Endpoint Check:")
            print(f"   OpenAI Key Set: {debug_data.get('openai_key_set', False)}")
            print(f"   Key Prefix: {debug_data.get('key_prefix', 'None')}")
            print(f"   CAVA Mode: {debug_data.get('cava_mode', 'Unknown')}")
            
            if debug_data.get('openai_key_set'):
                print("   ✅ OpenAI API key is configured")
                checks.append(True)
            else:
                print("   ❌ OpenAI API key is NOT configured")
                checks.append(False)
    except Exception as e:
        print(f"❌ Debug endpoint not found (indicates old code): {e}")
        checks.append(False)
    
    print()
    
    # Check 3: Test registration intent
    try:
        async with httpx.AsyncClient() as client:
            test_payload = {
                "farmer_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "message": "I want to register",
                "language": "en"
            }
            
            response = await client.post(
                f"{base_url}/api/v1/registration/cava",
                json=test_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                print("✅ Registration Test:")
                print(f"   Response: {response_text[:100]}...")
                
                # Check for hardcoded greetings (BAD)
                hardcoded_greetings = [
                    "👋 Hello! I'm CAVA",
                    "Welcome to AVA OLO!",
                    "Let's get you registered!"
                ]
                
                if any(greeting in response_text for greeting in hardcoded_greetings):
                    print("   ❌ HARDCODED RESPONSE DETECTED - Old code still running!")
                    checks.append(False)
                else:
                    print("   ✅ LLM-generated response (no hardcoded greeting)")
                    checks.append(True)
            else:
                print(f"❌ Registration test failed: {response.status_code}")
                checks.append(False)
    except Exception as e:
        print(f"❌ Registration test error: {e}")
        checks.append(False)
    
    print()
    print("=" * 60)
    print("DEPLOYMENT VERIFICATION SUMMARY:")
    print(f"   Total Checks: {len(checks)}")
    print(f"   Passed: {sum(checks)}")
    print(f"   Failed: {len(checks) - sum(checks)}")
    
    if all(checks):
        print("\n✅ DEPLOYMENT VERIFIED: Commit 8a3408b is live!")
    else:
        print("\n❌ DEPLOYMENT FAILED: Old code still running")
        print("\nRequired Actions:")
        print("1. Check AWS App Runner deployment status")
        print("2. Verify environment variables are set")
        print("3. Force new deployment if needed")
    
    return all(checks)

if __name__ == "__main__":
    result = asyncio.run(verify_deployment())
    exit(0 if result else 1)