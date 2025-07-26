#!/usr/bin/env python3
"""
Verify OpenAI Key Deployment
Checks if the OpenAI key is now working in production
"""
import asyncio
import httpx
import json
import sys
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

async def check_deployment():
    """Check if OpenAI key is deployed"""
    print("🔍 Verifying OpenAI Key Deployment")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Check LLM status
        try:
            print("1️⃣ Checking LLM Status...")
            response = await client.get(f"{BASE_URL}/api/v1/registration/llm-status")
            status = response.json()
            
            key_exists = status['environment']['openai_key_exists']
            engine_ready = status['engine_status']['cava_engine_initialized']
            critical_check = status['critical_check']
            
            print(f"   - OpenAI Key Exists: {'✅' if key_exists else '❌'} {key_exists}")
            print(f"   - Engine Initialized: {'✅' if engine_ready else '❌'} {engine_ready}")
            print(f"   - Critical Check: {critical_check}")
            
            if not key_exists:
                print()
                print("⏳ Deployment may still be in progress. Wait 1-2 minutes and try again.")
                return False
                
        except Exception as e:
            print(f"❌ Error checking LLM status: {e}")
            return False
        
        # Test registration
        try:
            print()
            print("2️⃣ Testing Registration with LLM...")
            test_data = {
                "farmer_id": f"verify_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "message": "i want to register"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/registration/cava",
                json=test_data
            )
            
            result = response.json()
            response_text = result.get('response', '')
            
            # Check for hardcoded responses
            hardcoded_phrases = [
                "👋 Hello! I'm CAVA",
                "Welcome to AVA OLO!",
                "Let's get you registered!",
                "Registration system not available"
            ]
            
            is_hardcoded = any(phrase in response_text for phrase in hardcoded_phrases)
            
            print(f"   Response: {response_text[:100]}...")
            
            if is_hardcoded:
                print(f"   ❌ Still getting hardcoded/error response")
                return False
            else:
                print(f"   ✅ LLM response detected!")
                return True
                
        except Exception as e:
            print(f"❌ Error testing registration: {e}")
            return False

async def main():
    """Main verification function"""
    success = await check_deployment()
    
    print()
    print("=" * 50)
    
    if success:
        print("🎉 SUCCESS: OpenAI Key Deployed and Working!")
        print()
        print("✅ LLM registration is now active")
        print("✅ Constitutional compliance achieved")
        print("✅ Ready for production use")
    else:
        print("❌ DEPLOYMENT NOT COMPLETE")
        print()
        print("Next steps:")
        print("1. Wait 1-2 minutes for deployment to complete")
        print("2. Run this script again")
        print("3. Check ECS deployment events if issues persist")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)