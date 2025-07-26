#!/usr/bin/env python3
"""
Verify Deployment Success - Check if v3.5.0 reached production
"""
import requests
import time
import json

def check_deployment():
    """Check if the new version is deployed"""
    try:
        # Check version endpoint
        response = requests.get("https://ava-olo-65365776.us-east-1.elb.amazonaws.com/version", timeout=10)
        data = response.json()
        current_version = data.get('version', 'unknown')
        
        print(f"🔍 Current Version: {current_version}")
        
        # Check if it's v3.5.0
        if "v3.5.0" in current_version:
            print("✅ SUCCESS: v3.5.0 deployed successfully!")
            
            # Test registration endpoint
            test_registration()
            return True
        else:
            print(f"⏳ Still waiting... Current: {current_version}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking version: {e}")
        return False

def test_registration():
    """Test if registration now uses LLM"""
    try:
        print("\n🧪 Testing Registration LLM...")
        
        # Test the registration endpoint
        response = requests.post(
            "https://ava-olo-65365776.us-east-1.elb.amazonaws.com/api/v1/registration/cava",
            json={
                "message": "I want to register",
                "farmer_id": "test123",
                "language": "en"
            },
            timeout=15
        )
        
        data = response.json()
        response_text = data.get('response', '')
        
        print(f"📝 Registration Response: {response_text[:100]}...")
        
        # Check if it's intelligent (not hardcoded)
        hardcoded_phrases = ["👋 Hello! I'm CAVA", "What's your name?"]
        is_intelligent = not any(phrase in response_text for phrase in hardcoded_phrases)
        
        if is_intelligent and len(response_text) > 10:
            print("✅ REGISTRATION SUCCESS: Getting intelligent LLM responses!")
            print("🥭 MANGO TEST: Bulgarian mango farmer will now get intelligent registration!")
        else:
            print("❌ REGISTRATION ISSUE: Still getting hardcoded responses")
            
    except Exception as e:
        print(f"❌ Registration test error: {e}")

if __name__ == "__main__":
    print("🚀 Deployment Verification Script")
    print("=" * 50)
    
    max_attempts = 10
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"\n📊 Attempt {attempt}/{max_attempts}")
        
        if check_deployment():
            print("\n🎉 DEPLOYMENT VERIFICATION COMPLETE!")
            break
        
        if attempt < max_attempts:
            print("⏱️  Waiting 30 seconds before next check...")
            time.sleep(30)
        
        attempt += 1
    
    if attempt > max_attempts:
        print("\n⚠️  Max attempts reached. Deployment may still be in progress.")
        print("Check GitHub Actions: https://github.com/your-repo/actions")